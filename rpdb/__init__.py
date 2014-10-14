"""Remote Python Debugger (pdb wrapper)."""

__author__ = "Bertrand Janin <b@janin.com>"
__version__ = "0.1.5"

import pdb
import socket
import sys
import traceback


class Rpdb(pdb.Pdb):

    def __init__(self, addr="127.0.0.1", port=4444):
        """Initialize the socket and initialize pdb."""

        # Backup stdin and stdout before replacing them by the socket handle
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin

        # Open a 'reusable' socket to let the webapp reload on the same port
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.skt.bind((addr, port))
        self.skt.listen(1)

        # Writes to stdout are forbidden in mod_wsgi environments
        try:
            sys.stderr.write("pdb is running on %s:%d\n" % self.skt.getsockname())
        except IOError:
            pass

        (clientsocket, address) = self.skt.accept()
        handle = clientsocket.makefile('rw')
        pdb.Pdb.__init__(self, completekey='tab', stdin=handle, stdout=handle)
        sys.stdout = sys.stdin = handle

    def shutdown(self):
        """Revert stdin and stdout, close the socket."""
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        self.skt.close()

    def do_continue(self, arg):
        """Clean-up and do underlying continue."""
        try:
            return pdb.Pdb.do_continue(self, arg)
        finally:
            self.shutdown()

    do_c = do_cont = do_continue

    def do_quit(self, arg):
        """Clean-up and do underlying quit."""
        try:
            return pdb.Pdb.do_quit(self, arg)
        finally:
            self.shutdown()

    do_q = do_exit = do_quit

    def do_EOF(self, arg):
        """Clean-up and do underlying EOF."""
        try:
            return pdb.Pdb.do_EOF(self, arg)
        finally:
            self.shutdown()



def set_trace(addr="127.0.0.1", port=4444):
    """Wrapper function to keep the same import x; x.set_trace() interface.

    We catch all the possible exceptions from pdb and cleanup.

    """
    debugger = Rpdb(addr=addr, port=port)
    try:
        debugger.set_trace(sys._getframe().f_back)
    except Exception:
        traceback.print_exc()
