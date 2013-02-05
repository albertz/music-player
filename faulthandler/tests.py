from __future__ import with_statement
from contextlib import contextmanager
import datetime
import faulthandler
import os
import re
import signal
import subprocess
import sys
import tempfile
import unittest

try:
    import threading
    HAVE_THREADS = True
except ImportError:
    HAVE_THREADS = False

TIMEOUT = 1

Py_REF_DEBUG = hasattr(sys, 'gettotalrefcount')

try:
    skipIf = unittest.skipIf
except AttributeError:
    import functools
    def skipIf(test, reason):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                if not test:
                    return func(*args, **kw)
                else:
                    print("skip %s: %s" % (func.__name__, reason))
            return wrapper
        return decorator

try:
    from resource import setrlimit, RLIMIT_CORE, error as resource_error
except ImportError:
    prepare_subprocess = None
else:
    def prepare_subprocess():
        # don't create core file
        try:
            setrlimit(RLIMIT_CORE, (0, 0))
        except (ValueError, resource_error):
            pass

def expected_traceback(lineno1, lineno2, header, count=1):
    regex = header
    regex += '  File "<string>", line %s in func\n' % lineno1
    regex += '  File "<string>", line %s in <module>' % lineno2
    if count != 1:
        regex = (regex + '\n') * (count - 1) + regex
    return '^' + regex + '$'

@contextmanager
def temporary_filename():
   filename = tempfile.mktemp()
   try:
       yield filename
   finally:
       try:
           os.unlink(filename)
       except OSError:
           pass

class FaultHandlerTests(unittest.TestCase):
    def get_output(self, code, filename=None):
        """
        Run the specified code in Python (in a new child process) and read the
        output from the standard error or from a file (if filename is set).
        Return the output lines as a list.

        Strip the reference count from the standard error for Python debug
        build, and replace "Current thread 0x00007f8d8fbd9700" by "Current
        thread XXX".
        """
        options = {}
        if prepare_subprocess:
            options['preexec_fn'] = prepare_subprocess
        process = subprocess.Popen(
            [sys.executable, '-c', code],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **options)
        stdout, stderr = process.communicate()
        exitcode = process.wait()
        output = stdout.decode('ascii', 'backslashreplace')
        output = re.sub(r"\[\d+ refs\]\r?\n?$", "", output)
        if filename:
            self.assertEqual(output, '')
            with open(filename, "rb") as fp:
                output = fp.read()
            output = output.decode('ascii', 'backslashreplace')
        output = re.sub('Current thread 0x[0-9a-f]+',
                        'Current thread XXX',
                        output)
        return output.splitlines(), exitcode

    def check_fatal_error(self, code, line_number, name_regex,
                          filename=None, all_threads=True, other_regex=None):
        """
        Check that the fault handler for fatal errors is enabled and check the
        traceback from the child process output.

        Raise an error if the output doesn't match the expected format.
        """
        if all_threads:
            header = r'Current thread XXX'
        else:
            header = r'Traceback \(most recent call first\)'
        regex = """
^Fatal Python error: %s

%s:
  File "<string>", line %s in <module>$
""".strip()
        regex = regex % (name_regex, header, line_number)
        if other_regex:
            regex += '|' + other_regex
        output, exitcode = self.get_output(code, filename)
        output = '\n'.join(output)
        self.assertRegex(output, regex)
        self.assertNotEqual(exitcode, 0)

    def test_read_null(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._read_null()
""".strip(),
            3,
            '(?:Segmentation fault|Bus error)')

    def test_sigsegv(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._sigsegv()
""".strip(),
            3,
            'Segmentation fault')

    def test_sigabrt(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._sigabrt()
""".strip(),
            3,
            'Aborted')

    @skipIf(sys.platform == 'win32',
            "SIGFPE cannot be caught on Windows")
    def test_sigfpe(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._sigfpe()
""".strip(),
            3,
            'Floating point exception')

    @skipIf(not hasattr(faulthandler, '_sigbus'),
            "need faulthandler._sigbus()")
    def test_sigbus(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._sigbus()
""".strip(),
            3,
            'Bus error')

    @skipIf(not hasattr(faulthandler, '_sigill'),
            "need faulthandler._sigill()")
    def test_sigill(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._sigill()
""".strip(),
            3,
            'Illegal instruction')

    def test_fatal_error(self):
        if sys.version_info >= (2, 6):
            arg = "b'xyz'"
        else:
            arg = "'xyz'"
        message = "xyz\nFatal Python error: Aborted"
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._fatal_error(%s)
""".strip() % (arg,),
            3,
            message)

    @skipIf(not hasattr(faulthandler, '_stack_overflow'),
            'need faulthandler._stack_overflow()')
    def test_stack_overflow(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._stack_overflow()
""".strip(),
            3,
            '(?:Segmentation fault|Bus error)',
            other_regex='unable to raise a stack overflow')

    def test_gil_released(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable()
faulthandler._read_null(True)
""".strip(),
            3,
            '(?:Segmentation fault|Bus error)')

    def test_enable_file(self):
        with temporary_filename() as filename:
            self.check_fatal_error("""
import faulthandler
output = open(%r, 'wb')
faulthandler.enable(output)
faulthandler._read_null()
""".strip() % (filename,),
                4,
                '(?:Segmentation fault|Bus error)',
                filename=filename)

    def test_enable_single_thread(self):
        self.check_fatal_error("""
import faulthandler
faulthandler.enable(all_threads=False)
faulthandler._read_null()
""".strip(),
            3,
            '(?:Segmentation fault|Bus error)',
            all_threads=False)

    def test_disable(self):
        code = """
import faulthandler
faulthandler.enable()
faulthandler.disable()
faulthandler._read_null()
""".strip()
        not_expected = 'Fatal Python error'
        stderr, exitcode = self.get_output(code)
        stder = '\n'.join(stderr)
        self.assertTrue(not_expected not in stderr,
                     "%r is present in %r" % (not_expected, stderr))
        self.assertNotEqual(exitcode, 0)

    def test_is_enabled(self):
        was_enabled = faulthandler.is_enabled()
        try:
            faulthandler.enable()
            self.assertTrue(faulthandler.is_enabled())
            faulthandler.disable()
            self.assertFalse(faulthandler.is_enabled())
        finally:
            if was_enabled:
                faulthandler.enable()
            else:
                faulthandler.disable()

    def check_dump_traceback(self, filename):
        """
        Explicitly call dump_traceback() function and check its output.
        Raise an error if the output doesn't match the expected format.
        """
        code = """
from __future__ import with_statement
import faulthandler

def funcB():
    if %s:
        with open(%s, "wb") as fp:
            faulthandler.dump_traceback(fp)
    else:
        faulthandler.dump_traceback()

def funcA():
    funcB()

funcA()
""".strip()
        code = code % (bool(filename), repr(filename))
        if filename:
            lineno = 7
        else:
            lineno = 9
        expected = [
            'Current thread XXX:',
            '  File "<string>", line %s in funcB' % lineno,
            '  File "<string>", line 12 in funcA',
            '  File "<string>", line 14 in <module>'
        ]
        trace, exitcode = self.get_output(code, filename)
        self.assertEqual(trace, expected)
        self.assertEqual(exitcode, 0)

    def test_dump_traceback(self):
        self.check_dump_traceback(None)

    def test_dump_traceback_file(self):
        with temporary_filename() as filename:
            self.check_dump_traceback(filename)

    @skipIf(not HAVE_THREADS, 'need threads')
    def check_dump_traceback_threads(self, filename):
        """
        Call explicitly dump_traceback(all_threads=True) and check the output.
        Raise an error if the output doesn't match the expected format.
        """
        code = """
from __future__ import with_statement
import faulthandler
from threading import Thread, Event
import time

def dump():
    if %s:
        with open(%s, "wb") as fp:
            faulthandler.dump_traceback(fp, all_threads=True)
    else:
        faulthandler.dump_traceback(all_threads=True)

class Waiter(Thread):
    # avoid blocking if the main thread raises an exception.
    daemon = True

    def __init__(self):
        Thread.__init__(self)
        self.running = Event()
        self.stop = Event()

    def run(self):
        self.running.set()
        self.stop.wait()

waiter = Waiter()
waiter.start()
waiter.running.wait()
dump()
waiter.stop.set()
waiter.join()
""".strip()
        code = code % (bool(filename), repr(filename))
        output, exitcode = self.get_output(code, filename)
        output = '\n'.join(output)
        if filename:
            lineno = 9
        else:
            lineno = 11
        regex = """
^Thread 0x[0-9a-f]+:
(?:  File ".*threading.py", line [0-9]+ in [_a-z]+
){1,3}  File "<string>", line 24 in run
  File ".*threading.py", line [0-9]+ in _?_bootstrap_inner
  File ".*threading.py", line [0-9]+ in _?_bootstrap

Current thread XXX:
  File "<string>", line %s in dump
  File "<string>", line 29 in <module>$
""".strip()
        regex = regex % (lineno,)
        self.assertRegex(output, regex)
        self.assertEqual(exitcode, 0)

    def test_dump_traceback_threads(self):
        self.check_dump_traceback_threads(None)

    def test_dump_traceback_threads_file(self):
        with temporary_filename() as filename:
            self.check_dump_traceback_threads(filename)

    def _check_dump_traceback_later(self, repeat, cancel, filename):
        """
        Check how many times the traceback is written in timeout x 2.5 seconds,
        or timeout x 3.5 seconds if cancel is True: 1, 2 or 3 times depending
        on repeat and cancel options.

        Raise an error if the output doesn't match the expect format.
        """
        timeout_str = str(datetime.timedelta(seconds=TIMEOUT))
        code = """
import faulthandler
import time

def func(repeat, cancel, timeout):
    if cancel:
        faulthandler.cancel_dump_traceback_later()
    for loop in range(2):
        time.sleep(timeout * 1.25)
    faulthandler.cancel_dump_traceback_later()

timeout = %s
repeat = %s
cancel = %s
if %s:
    file = open(%s, "wb")
else:
    file = None
faulthandler.dump_traceback_later(timeout,
    repeat=repeat, file=file)
func(repeat, cancel, timeout)
if file is not None:
    file.close()
""".strip()
        code = code % (TIMEOUT, repeat, cancel,
                       bool(filename), repr(filename))
        trace, exitcode = self.get_output(code, filename)
        trace = '\n'.join(trace)

        if not cancel:
            if repeat:
                count = 2
            else:
                count = 1
            header = r'Timeout \(%s\)!\nCurrent thread XXX:\n' % timeout_str
            regex = expected_traceback(8, 20, header, count=count)
            self.assertRegex(trace, regex)
        else:
            self.assertEqual(trace, '')
        self.assertEqual(exitcode, 0)

    @skipIf(not hasattr(faulthandler, 'dump_traceback_later'),
            'need faulthandler.dump_traceback_later()')
    def check_dump_traceback_later(self, repeat=False, cancel=False,
                                  file=False):
        if file:
            with temporary_filename() as filename:
                self._check_dump_traceback_later(repeat, cancel, filename)
        else:
            self._check_dump_traceback_later(repeat, cancel, None)

    def test_dump_traceback_later(self):
        self.check_dump_traceback_later()

    def test_dump_traceback_later_repeat(self):
        self.check_dump_traceback_later(repeat=True)

    def test_dump_traceback_later_cancel(self):
        self.check_dump_traceback_later(cancel=True)

    def test_dump_traceback_later_file(self):
        self.check_dump_traceback_later(file=True)

    @skipIf(not hasattr(faulthandler, "register"),
            "need faulthandler.register")
    def check_register(self, filename=False, all_threads=False,
                       unregister=False, chain=False):
        """
        Register a handler displaying the traceback on a user signal. Raise the
        signal and check the written traceback.

        If chain is True, check that the previous signal handler is called.

        Raise an error if the output doesn't match the expected format.
        """
        signum = signal.SIGUSR1
        code = """
import faulthandler
import os
import signal
import sys

def func(signum):
    os.kill(os.getpid(), signum)

def handler(signum, frame):
    handler.called = True
handler.called = False

exitcode = 0
signum = %s
filename = %s
unregister = %s
all_threads = %s
chain = %s
if bool(filename):
    file = open(filename, "wb")
else:
    file = None
if chain:
    signal.signal(signum, handler)
faulthandler.register(signum, file=file,
                      all_threads=all_threads, chain=chain)
if unregister:
    faulthandler.unregister(signum)
func(signum)
if chain and not handler.called:
    if file is not None:
        output = file
    else:
        output = sys.stderr
    output.write("Error: signal handler not called!\\n")
    exitcode = 1
if file is not None:
    file.close()
sys.exit(exitcode)
""".strip()
        code = code % (
            signum,
            repr(filename),
            unregister,
            all_threads,
            chain,
        )
        trace, exitcode = self.get_output(code, filename)
        trace = '\n'.join(trace)
        if not unregister:
            if all_threads:
                regex = 'Current thread XXX:\n'
            else:
                regex = 'Traceback \(most recent call first\):\n'
            regex = expected_traceback(7, 29, regex)
            self.assertRegex(trace, regex)
        else:
            self.assertEqual(trace, '')
        if unregister:
            self.assertNotEqual(exitcode, 0)
        else:
            self.assertEqual(exitcode, 0)

    def test_register(self):
        self.check_register()

    def test_unregister(self):
        self.check_register(unregister=True)

    def test_register_file(self):
        with temporary_filename() as filename:
            self.check_register(filename=filename)

    def test_register_threads(self):
        self.check_register(all_threads=True)

    def test_register_chain(self):
        self.check_register(chain=True)

    if not hasattr(unittest.TestCase, 'assertRegex'):
        # Copy/paste from Python 3.3: just replace (str, bytes) by str
        def assertRegex(self, text, expected_regex, msg=None):
            """Fail the test unless the text matches the regular expression."""
            if isinstance(expected_regex, str):
                assert expected_regex, "expected_regex must not be empty."
                expected_regex = re.compile(expected_regex)
            if not expected_regex.search(text):
                msg = msg or "Regex didn't match"
                msg = '%s: %r not found in %r' % (msg, expected_regex.pattern, text)
                raise self.failureException(msg)


if __name__ == "__main__":
    unittest.main()
