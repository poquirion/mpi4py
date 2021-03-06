import sys
try:
    import threading as _threading
    _HAS_THREADING = True
except ImportError:
    import dummy_threading as _threading
    _HAS_THREADING = False

Thread = _threading.Thread
try:
    current_thread = _threading.current_thread # Py 3.X
except AttributeError:
    current_thread = _threading.currentThread  # Py 2.X

import mpi4py.rc
mpi4py.rc.thread_level = 'multiple'
from mpi4py import MPI
import mpiunittest as unittest


class TestMPIThreads(unittest.TestCase):

    REQUIRED = MPI.THREAD_SERIALIZED

    def testThreadLevels(self):
        levels = [MPI.THREAD_SINGLE,
                  MPI.THREAD_FUNNELED,
                  MPI.THREAD_SERIALIZED,
                  MPI.THREAD_MULTIPLE]
        if None in levels: return
        for i in range(len(levels)-1):
            self.assertTrue(levels[i] < levels[i+1])
        try:
            provided = MPI.Query_thread()
            self.assertTrue(provided in levels)
        except NotImplementedError:
            pass

    def testIsThreadMain(self, main=True):
        try:
            flag = MPI.Is_thread_main()
        except NotImplementedError:
            return
        self.assertEqual(flag, main)
        if _VERBOSE:
            thread = current_thread()
            name = thread.getName()
            log = lambda m: sys.stderr.write(m+'\n')
            log("%s: MPI.Is_thread_main() -> %s" % (name, flag))

    def testIsThreadMainInThread(self):
        try:
            provided = MPI.Query_thread()
        except NotImplementedError:
            return
        if provided < self.REQUIRED:
            return
        T = []
        for i in range(5):
            t = Thread(target=self.testIsThreadMain,
                       args = (not _HAS_THREADING,))
            T.append(t)
        if provided == MPI.THREAD_SERIALIZED:
            for t in T:
                t.start()
                t.join()
        elif provided == MPI.THREAD_MULTIPLE:
            for t in T:
                t.start()
            for t in T:
                t.join()


if hasattr(sys, 'pypy_version_info'):
    if (sys.version_info[0] == 3 and
        sys.pypy_version_info[0] < 5):
        del TestMPIThreads.testIsThreadMainInThread

name, version = MPI.get_vendor()
if name == 'Open MPI':
    TestMPIThreads.REQUIRED = MPI.THREAD_MULTIPLE
if name == 'LAM/MPI':
    TestMPIThreads.REQUIRED = MPI.THREAD_MULTIPLE


_VERBOSE = False
#_VERBOSE = True
if __name__ == '__main__':
    if '-v' in sys.argv:
        _VERBOSE = True
    unittest.main()
