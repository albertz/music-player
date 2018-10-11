
# Copyright (c) 2016, Albert Zeyer, www.az2000.de
# All rights reserved.
# file created 2011-04-15


# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
https://github.com/albertz/py_better_exchook

This is a simple replacement for the standard Python exception handler (sys.excepthook).
In addition to what the standard handler does, it also prints all referenced variables
(no matter if local, global or builtin) of the code line of each stack frame.
See below for some examples and some example output.

See these functions:

- better_exchook
- format_tb / print_tb
- iter_traceback
- get_current_frame
- dump_all_thread_tracebacks
- install
- replace_traceback_format_tb

Although there might be a few more useful functions, thus we export all of them.

Also see the demo/tests at the end.
"""

from __future__ import print_function

import sys
import os
import os.path
import threading
import keyword
import inspect
try:
    from traceback import StackSummary, FrameSummary
except ImportError:
    class _Dummy:
        pass
    StackSummary = FrameSummary = _Dummy

# noinspection PySetFunctionToLiteral,SpellCheckingInspection
pykeywords = set(keyword.kwlist) | set(["None", "True", "False"])

_cur_pwd = os.getcwd()
_threading_main_thread = threading.main_thread() if hasattr(threading, "main_thread") else None

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    unicode
except NameError:  # Python3
    unicode = str   # Python 3 compatibility

try:
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    raw_input
except NameError:  # Python3
    raw_input = input


def parse_py_statement(line):
    state = 0
    curtoken = ""
    spaces = " \t\n"
    ops = ".,;:+-*/%&!=|(){}[]^<>"
    i = 0
    def _escape_char(c):
        if c == "n": return "\n"
        elif c == "t": return "\t"
        else: return c
    while i < len(line):
        c = line[i]
        i += 1
        if state == 0:
            if c in spaces: pass
            elif c in ops: yield ("op", c)
            elif c == "#": state = 6
            elif c == "\"": state = 1
            elif c == "'": state = 2
            else:
                curtoken = c
                state = 3
        elif state == 1: # string via "
            if c == "\\": state = 4
            elif c == "\"":
                yield ("str", curtoken)
                curtoken = ""
                state = 0
            else: curtoken += c
        elif state == 2: # string via '
            if c == "\\": state = 5
            elif c == "'":
                yield ("str", curtoken)
                curtoken = ""
                state = 0
            else: curtoken += c
        elif state == 3: # identifier
            if c in spaces + ops + "#\"'":
                yield ("id", curtoken)
                curtoken = ""
                state = 0
                i -= 1
            else: curtoken += c
        elif state == 4: # escape in "
            curtoken += _escape_char(c)
            state = 1
        elif state == 5: # escape in '
            curtoken += _escape_char(c)
            state = 2
        elif state == 6: # comment
            curtoken += c
    if state == 3: yield ("id", curtoken)
    elif state == 6: yield ("comment", curtoken)


def parse_py_statements(source_code):
    for line in source_code.splitlines():
        for t in parse_py_statement(line):
            yield t


def grep_full_py_identifiers(tokens):
    global pykeywords
    tokens = list(tokens)
    i = 0
    while i < len(tokens):
        tokentype, token = tokens[i]
        i += 1
        if tokentype != "id": continue
        while i+1 < len(tokens) and tokens[i] == ("op", ".") and tokens[i+1][0] == "id":
            token += "." + tokens[i+1][1]
            i += 2
        if token == "": continue
        if token in pykeywords: continue
        if token[0] in ".0123456789": continue
        yield token


def set_linecache(filename, source):
    import linecache
    linecache.cache[filename] = None, None, [line+'\n' for line in source.splitlines()], filename


def simple_debug_shell(globals, locals):
    try: import readline
    except ImportError: pass # ignore
    COMPILE_STRING_FN = "<simple_debug_shell input>"
    while True:
        try:
            s = raw_input("> ")
        except (KeyboardInterrupt, EOFError):
            print("breaked debug shell: " + sys.exc_info()[0].__name__)
            break
        if s.strip() == "": continue
        try:
            c = compile(s, COMPILE_STRING_FN, "single")
        except Exception as e:
            print("%s : %s in %r" % (e.__class__.__name__, str(e), s))
        else:
            set_linecache(COMPILE_STRING_FN, s)
            try:
                ret = eval(c, globals, locals)
            except (KeyboardInterrupt, SystemExit):
                print("debug shell exit: " + sys.exc_info()[0].__name__)
                break
            except Exception:
                print("Error executing %r" % s)
                better_exchook(*sys.exc_info(), autodebugshell=False)
            else:
                try:
                    if ret is not None: print(ret)
                except Exception:
                    print("Error printing return value of %r" % s)
                    better_exchook(*sys.exc_info(), autodebugshell=False)


def debug_shell(user_ns, user_global_ns, traceback=None, execWrapper=None):
    ipshell = None
    try:
        import IPython
        have_ipython = True
    except ImportError:
        have_ipython = False
    if not ipshell and traceback and have_ipython:
        try:
            from IPython.core.debugger import Pdb
            from IPython.terminal.debugger import TerminalPdb
            from IPython.terminal.ipapp import TerminalIPythonApp
            ipapp = TerminalIPythonApp.instance()
            ipapp.interact = False  # Avoid output (banner, prints)
            ipapp.initialize(argv=[])
            def_colors = ipapp.shell.colors
            pdb_obj = TerminalPdb(def_colors)
            pdb_obj.botframe = None  # not sure. exception otherwise at quit
            ipshell = lambda: pdb_obj.interaction(None, traceback=traceback)
        except Exception:
            print("IPython Pdb exception:")
            better_exchook(*sys.exc_info(), autodebugshell=False)
    if not ipshell and have_ipython:
        try:
            import IPython
            import IPython.terminal.embed
            class DummyMod(object): pass
            module = DummyMod()
            module.__dict__ = user_global_ns
            module.__name__ = "_DummyMod"
            if "__name__" not in user_ns:
                user_ns = user_ns.copy()
                user_ns["__name__"] = "_DummyUserNsMod"
            ipshell = IPython.terminal.embed.InteractiveShellEmbed.instance(
                user_ns=user_ns, user_module=module)
        except Exception:
            print("IPython not available:")
            better_exchook(*sys.exc_info(), autodebugshell=False)
        else:
            if execWrapper:
                old = ipshell.run_code
                ipshell.run_code = lambda code: execWrapper(lambda: old(code))
    if ipshell:
        ipshell()
    else:
        print("Use simple debug shell:")
        if traceback:
            import pdb
            pdb.post_mortem(traceback)
        else:
            simple_debug_shell(user_global_ns, user_ns)


def output_limit():
    return 300


def pp_extra_info(obj, depthlimit = 3):
    s = []
    if hasattr(obj, "__len__"):
        try:
            if type(obj) in (str,unicode,list,tuple,dict) and len(obj) <= 5:
                pass # don't print len in this case
            else:
                s += ["len = " + str(obj.__len__())]
        except Exception: pass
    if depthlimit > 0 and hasattr(obj, "__getitem__"):
        try:
            if type(obj) in (str,unicode):
                pass # doesn't make sense to get subitems here
            else:
                subobj = obj.__getitem__(0)
                extra_info = pp_extra_info(subobj, depthlimit - 1)
                if extra_info != "":
                    s += ["_[0]: {" + extra_info + "}"]
        except Exception: pass
    return ", ".join(s)


def pretty_print(obj):
    s = repr(obj)
    limit = output_limit()
    if len(s) > limit:
        s = s[:limit - 3] + "..."
    extra_info = pp_extra_info(obj)
    if extra_info != "": s += ", " + extra_info
    return s


def fallback_findfile(filename):
    mods = [m for m in sys.modules.values() if m and hasattr(m, "__file__") and filename in m.__file__]
    if len(mods) == 0:
        return None
    altfn = mods[0].__file__
    if altfn[-4:-1] == ".py": altfn = altfn[:-1] # *.pyc or whatever
    if not os.path.exists(altfn) and altfn.startswith("./"):
        # Maybe current dir changed.
        altfn2 = _cur_pwd + altfn[1:]
        if os.path.exists(altfn2):
            return altfn2
        # Try dirs of some other mods.
        for m in ["__main__", "better_exchook"]:
            if hasattr(sys.modules.get(m), "__file__"):
                altfn2 = os.path.dirname(sys.modules[m].__file__) + altfn[1:]
                if os.path.exists(altfn2):
                    return altfn2
    return altfn


def is_source_code_missing_open_brackets(source_code):
    open_brackets = "[{("
    close_brackets = "]})"
    last_close_bracket = [-1]  # stack
    counters = [0] * len(open_brackets)
    # Go in reverse order through the tokens.
    # Thus, we first should see the closing brackets, and then the matching opening brackets.
    for t_type, t_content in reversed(list(parse_py_statements(source_code))):
        if t_type != "op": continue  # we are from now on only interested in ops (including brackets)
        if t_content in open_brackets:
            idx = open_brackets.index(t_content)
            if last_close_bracket[-1] == idx:  # ignore if we haven't seen the closing one
                counters[idx] -= 1
                del last_close_bracket[-1]
        elif t_content in close_brackets:
            idx = close_brackets.index(t_content)
            counters[idx] += 1
            last_close_bracket += [idx]
    return not all([c == 0 for c in counters])


def get_source_code(filename, lineno, module_globals):
    import linecache
    linecache.checkcache(filename)
    source_code = linecache.getline(filename, lineno, module_globals)
    # In case of a multi-line statement, lineno is usually the last line.
    # We are checking for missing open brackets and add earlier code lines.
    while is_source_code_missing_open_brackets(source_code):
        if lineno <= 0: break
        lineno -= 1
        source_code = "".join([linecache.getline(filename, lineno, module_globals), source_code])
    return source_code


def str_visible_len(s):
    """
    :param str s:
    :return: len without escape chars
    :rtype: int
    """
    import re
    # via: https://github.com/chalk/ansi-regex/blob/master/index.js
    s = re.sub("[\x1b\x9b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-PRZcf-nqry=><]", "", s)
    return len(s)


def add_indent_lines(prefix, s):
    if not s: return prefix
    prefix_len = str_visible_len(prefix)
    lines = s.splitlines(True)
    return "".join([prefix + lines[0]] + [" " * prefix_len + l for l in lines[1:]])


def get_indent_prefix(s):
    return s[:len(s) - len(s.lstrip())]


def get_same_indent_prefix(lines):
    if not lines: return ""
    prefix = get_indent_prefix(lines[0])
    if not prefix: return ""
    if all([l.startswith(prefix) for l in lines]):
        return prefix
    return None


def remove_indent_lines(s):
    if not s: return ""
    lines = s.splitlines(True)
    prefix = get_same_indent_prefix(lines)
    if prefix is None:  # not in expected format. just lstrip all lines
        return "".join([l.lstrip() for l in lines])
    return "".join([l[len(prefix):] for l in lines])


def replace_tab_indent(s, replace="    "):
    prefix = get_indent_prefix(s)
    return prefix.replace("\t", replace) + s[len(prefix):]


def replace_tab_indents(s, replace="    "):
    lines = s.splitlines(True)
    return "".join([replace_tab_indent(l, replace) for l in lines])


def to_bool(s, fallback=None):
    """
    :param str s: str to be converted to bool, e.g. "1", "0", "true", "false"
    :param T fallback: if s is not recognized as a bool
    :return: boolean value, or fallback
    :rtype: bool|T
    """
    if not s:
        return fallback
    s = s.lower()
    if s in ["1", "true", "yes", "y"]:
        return True
    if s in ["0", "false", "no", "n"]:
        return False
    return fallback


class Color:
    ColorIdxTable = {k: i for (i, k) in enumerate([
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"])}

    @classmethod
    def get_global_color_enabled(cls):
        return to_bool(os.environ.get("CLICOLOR", ""), fallback=True)

    def __init__(self, enable=None):
        """
        :param bool|None enable:
        """
        if enable is None:
            enable = self.get_global_color_enabled()
        self.enable = enable

    def color(self, s, color=None, bold=False):
        """
        :param str s:
        :param str|None color: e.g. "blue"
        :param bool bold:
        :return: s optionally wrapped with ansi escape codes
        :rtype: str
        """
        if not self.enable:
            return s
        code_seq = []
        if color:
            code_seq += [30 + self.ColorIdxTable[color]]  # foreground color
        if bold:
            code_seq += [1]
        if not code_seq:
            return s
        start = "\x1b[%sm" % ";".join(map(str, code_seq))
        end = "\x1b[0m"
        return start + s + end

    def __call__(self, *args, **kwargs):
        return self.color(*args, **kwargs)

    def py_syntax_highlight(self, s):
        if not self.enable:
            return s
        state = 0
        spaces = " \t\n"
        ops = ".,;:+-*/%&!=|(){}[]^<>"
        i = 0
        curtoken = ""
        color_args = {0: {}, len(s): {}}  # type: dict[int,dict[str]] # i -> color kwargs
        def finish_identifier():
            if curtoken in pykeywords:
                color_args[max([k for k in color_args.keys() if k < i])] = {"color": "blue"}
        while i < len(s):
            c = s[i]
            i += 1
            if c == "\n":
                if state == 3: finish_identifier()
                color_args[i] = {}; state = 0
            elif state == 0:
                if c in spaces: pass
                elif c in ops: color_args[i - 1] = {"color": "blue"}; color_args[i] = {}
                elif c == "#": color_args[i - 1] = {"color": "white"}; state = 6
                elif c == '"': color_args[i - 1] = {"color": "cyan"}; state = 1
                elif c == "'": color_args[i - 1] = {"color": "cyan"}; state = 2
                else:
                    curtoken = c
                    color_args[i - 1] = {}
                    state = 3
            elif state == 1:  # string via "
                if c == "\\": state = 4
                elif c == "\"":
                    color_args[i] = {}
                    state = 0
            elif state == 2:  # string via '
                if c == "\\": state = 5
                elif c == "'":
                    color_args[i] = {}
                    state = 0
            elif state == 3:  # identifier
                if c in spaces + ops + "#\"'":
                    finish_identifier()
                    color_args[i] = {}
                    state = 0
                    i -= 1
                else:
                    curtoken += c
            elif state == 4:  # escape in "
                state = 1
            elif state == 5:  # escape in '
                state = 2
            elif state == 6:  # comment
                pass
        if state == 3: finish_identifier()
        out = ""
        i = 0
        while i < len(s):
            j = min([k for k in color_args.keys() if k > i])
            out += self.color(s[i:j], **color_args[i])
            i = j
        return out


def is_at_exit():
    """
    Some heuristics to figure out whether this is called at a stage where the Python interpreter is shutting down.

    :return: whether the Python interpreter is currently in the process of shutting down
    :rtype: bool
    """
    if _threading_main_thread is not None:
        if not hasattr(threading, "main_thread"):
            return True
        if threading.main_thread() != _threading_main_thread:
            return True
        if not _threading_main_thread.is_alive():
            return True
    return False


def format_tb(tb=None, limit=None, allLocals=None, allGlobals=None, withTitle=False, with_color=None, with_vars=None):
    """
    :param types.TracebackType|types.FrameType|StackSummary tb: traceback. if None, will use sys._getframe
    :param int|None limit: limit the traceback to this number of frames. by default, will look at sys.tracebacklimit
    :param dict[str]|None allLocals: if set, will update it with all locals from all frames
    :param dict[str]|None allGlobals: if set, will update it with all globals from all frames
    :param bool withTitle:
    :param bool|None with_color: output with ANSI escape codes for color
    :param bool with_vars: will print var content which are referenced in the source code line. by default enabled.
    :return: list of strings (line-based)
    :rtype: list[str]
    """
    color = Color(enable=with_color)
    out = []
    def output(s1, s2=None, **kwargs):
        if kwargs:
            s1 = color(s1, **kwargs)
        if s2 is not None:
            s1 = add_indent_lines(s1, s2)
        out.append(s1 + "\n")
    def format_filename(s):
        base = os.path.basename(s)
        return (
            color('"' + s[:-len(base)], "cyan") +
            color(base, "cyan", bold=True) +
            color('"', "cyan"))
    def format_py_obj(obj):
        return color.py_syntax_highlight(pretty_print(obj))
    if tb is None:
        try:
            tb = get_current_frame()
            assert tb
        except Exception:
            output(color("format_tb: tb is None and sys._getframe() failed", "red", bold=True))
            return out
    def isstacksummary(_tb):
        return isinstance(_tb, StackSummary)
    isframe = inspect.isframe
    if withTitle:
        if isframe(tb) or isstacksummary(tb):
            output(color('Traceback (most recent call first):', "blue"))
        else:  # expect traceback-object (or compatible)
            output(color('Traceback (most recent call last):', "blue"))
    if with_vars is None and is_at_exit():
        # Better to not show __repr__ of some vars, as this might lead to crashes
        # when native extensions are involved.
        with_vars = False
        if withTitle:
            output("(Exclude vars because we are exiting.)")
    if with_vars is None:
        if any([f.f_code.co_name == "__del__" for f in iter_traceback()]):
            # __del__ is usually called via the Python garbage collector (GC).
            # This can happen and very random / non-deterministic places.
            # There are cases where it is not safe to access some of the vars on the stack
            # because they might be in a non-well-defined state, thus calling their __repr__ is not safe.
            # See e.g. this bug:
            # https://github.com/tensorflow/tensorflow/issues/22770
            with_vars = False
            if withTitle:
                output("(Exclude vars because we are on a GC stack.)")
    if with_vars is None:
        with_vars = True
    try:
        if limit is None:
            if hasattr(sys, 'tracebacklimit'):
                limit = sys.tracebacklimit
        n = 0
        _tb = tb
        class NotFound(Exception):
            pass
        def _resolve_identifier(namespace, id):
            if id[0] not in namespace:
                raise NotFound()
            obj = namespace[id[0]]
            for part in id[1:]:
                obj = getattr(obj, part)
            return obj
        def _try_set(old, prefix, func):
            if old is not None: return old
            try: return add_indent_lines(prefix, func())
            except NotFound: return old
            except Exception as e:
                return prefix + "!" + e.__class__.__name__ + ": " + str(e)
        while _tb is not None and (limit is None or n < limit):
            if isframe(_tb):
                f = _tb
            elif isstacksummary(_tb):
                if isinstance(_tb[0], ExtendedFrameSummary):
                    f = _tb[0].tb_frame
                else:
                    f = DummyFrame.from_frame_summary(_tb[0])
            else:
                f = _tb.tb_frame
            if allLocals is not None: allLocals.update(f.f_locals)
            if allGlobals is not None: allGlobals.update(f.f_globals)
            if hasattr(_tb, "tb_lineno"): lineno = _tb.tb_lineno
            elif isstacksummary(_tb): lineno = _tb[0].lineno
            else: lineno = f.f_lineno
            co = f.f_code
            filename = co.co_filename
            name = co.co_name
            output("".join([
                '  ',
                color("File ", "blue", bold=True), format_filename(filename), ", ",
                color("line ", "blue"), color("%d" % lineno, "magenta"), ", ",
                color("in ", "blue"), name]))
            if not os.path.isfile(filename):
                altfn = fallback_findfile(filename)
                if altfn:
                    output(color("    -- couldn't find file, trying this instead: ", "blue") +
                           format_filename(altfn))
                    filename = altfn
            source_code = get_source_code(filename, lineno, f.f_globals)
            if source_code:
                source_code = remove_indent_lines(replace_tab_indents(source_code)).rstrip()
                output("    line: ", color.py_syntax_highlight(source_code), color="blue")
                if not with_vars:
                    pass
                elif isinstance(f, DummyFrame) and not f.have_vars_available:
                    pass
                else:
                    output(color('    locals:', "blue"))
                    alreadyPrintedLocals = set()
                    for tokenstr in grep_full_py_identifiers(parse_py_statement(source_code)):
                        splittedtoken = tuple(tokenstr.split("."))
                        for token in [splittedtoken[0:i] for i in range(1, len(splittedtoken) + 1)]:
                            if token in alreadyPrintedLocals: continue
                            tokenvalue = None
                            tokenvalue = _try_set(tokenvalue, color("<local> ", "blue"), lambda: format_py_obj(_resolve_identifier(f.f_locals, token)))
                            tokenvalue = _try_set(tokenvalue, color("<global> ", "blue"), lambda: format_py_obj(_resolve_identifier(f.f_globals, token)))
                            tokenvalue = _try_set(tokenvalue, color("<builtin> ", "blue"), lambda: format_py_obj(_resolve_identifier(f.f_builtins, token)))
                            tokenvalue = tokenvalue or color("<not found>", "blue")
                            prefix = '      %s ' % color(".", "blue", bold=True).join(token) + color("= ", "blue", bold=True)
                            output(prefix, tokenvalue)
                            alreadyPrintedLocals.add(token)
                    if len(alreadyPrintedLocals) == 0:
                        output(color("       no locals", "blue"))
            else:
                output(color('    -- code not available --', "blue"))
            if isframe(_tb):
                _tb = _tb.f_back
            elif isstacksummary(_tb):
                _tb = StackSummary.from_list(_tb[1:])
                if not _tb:
                    _tb = None
            else:
                _tb = _tb.tb_next
            n += 1

    except Exception as e:
        output(color("ERROR: cannot get more detailed exception info because:", "red", bold=True))
        import traceback
        for l in traceback.format_exc().split("\n"):
            output("   " + l)

    return out


def print_tb(tb, file=None, **kwargs):
    if file is None:
        file = sys.stderr
    for l in format_tb(tb=tb, **kwargs):
        file.write(l)
    file.flush()


def better_exchook(etype, value, tb, debugshell=False, autodebugshell=True, file=None, with_color=None):
    """
    Replacement for sys.excepthook.

    :param etype: exception type
    :param value: exception value
    :param tb: traceback
    :param bool debugshell: spawn a debug shell at the context of the exception
    :param bool autodebugshell: if env DEBUG is an integer != 0, it will spawn a debug shell
    :param file: the output stream where we will print the traceback and exception information
    :param bool|None with_color: whether to use ANSI escape codes for colored output
    """
    if file is None:
        file = sys.stderr
    def output(ln): file.write(ln + "\n")
    color = Color(enable=with_color)
    output(color("EXCEPTION", "red", bold=True))
    allLocals,allGlobals = {},{}
    if tb is not None:
        print_tb(tb, allLocals=allLocals, allGlobals=allGlobals, file=file, withTitle=True, with_color=color.enable)
    else:
        output(color("better_exchook: traceback unknown", "red"))

    import types
    def _some_str(value):
        try: return str(value)
        except Exception: return '<unprintable %s object>' % type(value).__name__
    def _format_final_exc_line(etype, value):
        valuestr = _some_str(value)
        if value is None or not valuestr:
            line = color("%s" % etype, "red")
        else:
            line = color("%s" % etype, "red") + ": %s" % (valuestr,)
        return line
    if (isinstance(etype, BaseException) or
        (hasattr(types, "InstanceType") and isinstance(etype, types.InstanceType)) or
        etype is None or type(etype) is str):
        output(_format_final_exc_line(etype, value))
    else:
        output(_format_final_exc_line(etype.__name__, value))

    if autodebugshell:
        try: debugshell = int(os.environ["DEBUG"]) != 0
        except Exception: pass
    if debugshell:
        output("---------- DEBUG SHELL -----------")
        debug_shell(user_ns=allLocals, user_global_ns=allGlobals, traceback=tb)
    file.flush()


def dump_all_thread_tracebacks(exclude_thread_ids=None, file=None):
    """
    Prints the traceback of all threads.

    :param set[int]|list[int]|None exclude_thread_ids: threads to exclude
    :param file: output stream
    """
    if exclude_thread_ids is None:
        exclude_thread_ids = []
    if not file:
        file = sys.stdout
    import threading

    if hasattr(sys, "_current_frames"):
        print("", file=file)
        threads = {t.ident: t for t in threading.enumerate()}
        for tid, stack in sys._current_frames().items():
            if tid in exclude_thread_ids: continue
            # This is a bug in earlier Python versions.
            # http://bugs.python.org/issue17094
            # Note that this leaves out all threads not created via the threading module.
            if tid not in threads: continue
            tags = []
            thread = threads.get(tid)
            if thread:
                assert isinstance(thread, threading.Thread)
                if thread is threading.currentThread():
                    tags += ["current"]
                if isinstance(thread, threading._MainThread):
                    tags += ["main"]
                tags += [str(thread)]
            else:
                tags += ["unknown with id %i" % tid]
            print("Thread %s:" % ", ".join(tags), file=file)
            print_tb(stack, file=file)
            print("", file=file)
        print("That were all threads.", file=file)
    else:
        print("Does not have sys._current_frames, cannot get thread tracebacks.", file=file)


def get_current_frame():
    """
    :return: current frame object (excluding this function call)
    :rtype: types.FrameType

    Uses sys._getframe if available, otherwise some trickery with sys.exc_info and a dummy exception.
    """
    if hasattr(sys, "_getframe"):
        return sys._getframe(1)
    try:
        raise ZeroDivisionError
    except ZeroDivisionError:
        return sys.exc_info()[2].tb_frame.f_back


def iter_traceback(tb=None, enforce_most_recent_call_first=False):
    """
    Iterates a traceback of various formats:
      - traceback (types.TracebackType)
      - frame object (types.FrameType)
      - stack summary (traceback.StackSummary)

    :param types.TracebackType|types.FrameType|StackSummary|None tb: traceback. if None, will use sys._getframe
    :param bool enforce_most_recent_call_first:
        Frame or stack summery: most recent call first (top of the stack is the first entry in the result)
        Traceback: most recent call last
        If True, and we get traceback, will unroll and reverse, such that we have always the most recent call first.
    :return: yields the frames (types.FrameType)
    :rtype: list[types.FrameType|DummyFrame]
    """
    if tb is None:
        tb = get_current_frame()

    def is_stack_summary(_tb):
        return isinstance(_tb, StackSummary)

    is_frame = inspect.isframe
    is_traceback = inspect.istraceback
    assert is_traceback(tb) or is_frame(tb) or is_stack_summary(tb)
    # Frame or stack summery: most recent call first
    # Traceback: most recent call last
    if is_traceback(tb) and enforce_most_recent_call_first:
        frames = list(iter_traceback(tb))
        for frame in frames[::-1]:
            yield frame
        return

    _tb = tb
    while _tb is not None:
        if is_frame(_tb):
            frame = _tb
        elif is_stack_summary(_tb):
            if isinstance(_tb[0], ExtendedFrameSummary):
                frame = _tb[0].tb_frame
            else:
                frame = DummyFrame.from_frame_summary(_tb[0])
        else:
            frame = _tb.tb_frame
        yield frame
        if is_frame(_tb):
            _tb = _tb.f_back
        elif is_stack_summary(_tb):
            _tb = StackSummary.from_list(_tb[1:])
            if not _tb:
                _tb = None
        else:
            _tb = _tb.tb_next


class ExtendedFrameSummary(FrameSummary):
    def __init__(self, frame, **kwargs):
        super(ExtendedFrameSummary, self).__init__(**kwargs)
        self.tb_frame = frame


class DummyFrame:
    """
    This class has the same attributes as a code and a frame object
    and is intended to be used as a dummy replacement.
    """

    @classmethod
    def from_frame_summary(cls, f):
        """
        :param FrameSummary f:
        :rtype: DummyFrame
        """
        return cls(filename=f.filename, lineno=f.lineno, name=f.name, f_locals=f.locals)

    def __init__(self, filename, lineno, name, f_locals=None, f_globals=None, f_builtins=None):
        self.lineno = lineno
        self.tb_lineno = lineno
        self.f_lineno = lineno
        self.f_code = self
        self.filename = filename
        self.co_filename = filename
        self.name = name
        self.co_name = name
        self.f_locals = f_locals or {}
        self.f_globals = f_globals or {}
        self.f_builtins = f_builtins or {}
        self.have_vars_available = (f_locals is not None or f_globals is not None or f_builtins is not None)


def _StackSummary_extract(frame_gen, limit=None, lookup_lines=True, capture_locals=False):
    """Create a StackSummary from a traceback or stack object.
    Very simplified copy of the original StackSummary.extract().
    We want always to capture locals, that is why we overwrite it.
    Additionally, we also capture the frame.
    This is a bit hacky and also not like this is originally intended (to not keep refs).

    :param frame_gen: A generator that yields (frame, lineno) tuples to
        include in the stack.
    :param limit: None to include all frames or the number of frames to
        include.
    :param lookup_lines: If True, lookup lines for each frame immediately,
        otherwise lookup is deferred until the frame is rendered.
    :param capture_locals: If True, the local variables from each frame will
        be captured as object representations into the FrameSummary.
    """
    result = StackSummary()
    for f, lineno in frame_gen:
        co = f.f_code
        filename = co.co_filename
        name = co.co_name
        result.append(ExtendedFrameSummary(
            frame=f, filename=filename, lineno=lineno, name=name, lookup_line=False))
    return result


def install():
    """
    Replaces sys.excepthook by our better_exchook.
    """
    sys.excepthook = better_exchook


def replace_traceback_format_tb():
    """
    Replaces these functions from the traceback module by our own:

    - traceback.format_tb
    - traceback.StackSummary.format
    - traceback.StackSummary.extract

    Note that this kind of monkey patching might not be safe under all circumstances
    and is not officially supported by Python.
    """
    import traceback
    traceback.format_tb = format_tb
    if hasattr(traceback, "StackSummary"):
        traceback.StackSummary.format = format_tb
        traceback.StackSummary.extract = _StackSummary_extract


# ------------------------------------------------
# Test/demo code starts here.

def test_is_source_code_missing_open_brackets():
    assert is_source_code_missing_open_brackets("a") is False
    assert is_source_code_missing_open_brackets("a)") is True
    assert is_source_code_missing_open_brackets("fn()") is False
    assert is_source_code_missing_open_brackets("fn().b()") is False
    assert is_source_code_missing_open_brackets("fn().b()[0]") is False
    assert is_source_code_missing_open_brackets("fn({a[0]: 'b'}).b()[0]") is False
    assert is_source_code_missing_open_brackets("a[0]: 'b'}).b()[0]") is True


def test_add_indent_lines():
    assert add_indent_lines("foo ", " bar") == "foo  bar"
    assert add_indent_lines("foo ", " bar\n baz") == "foo  bar\n     baz"


def test_get_same_indent_prefix():
    assert get_same_indent_prefix(["a", "b"]) == ""
    assert get_same_indent_prefix([" a"]) == " "
    assert get_same_indent_prefix([" a", "  b"]) == " "


def test_remove_indent_lines():
    assert remove_indent_lines(" a\n  b") == "a\n b"
    assert remove_indent_lines("  a\n b") == "a\nb"
    assert remove_indent_lines("\ta\n\t b") == "a\n b"


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        for k, v in sorted(globals().items()):
            if not k.startswith("test_"): continue
            print("running: %s()" % k)
            v()
        print("ok.")
        sys.exit()

    elif sys.argv[1:] == ["debug_shell"]:
        debug_shell(locals(), globals())
        sys.exit()

    elif sys.argv[1:] == ["debug_shell_exception"]:
        try:
            raise Exception("demo exception")
        except Exception:
            better_exchook(*sys.exc_info(), debugshell=True)
        sys.exit()

    elif sys.argv[1:]:
        print("Usage: %s (test|...)" % sys.argv[0])
        sys.exit(1)

    # some examples
    # this code produces this output: https://gist.github.com/922622

    try:
        x = {1:2, "a":"b"}
        def f():
            y = "foo"
            # noinspection PyUnresolvedReferences,PyStatementEffect
            x, 42, sys.stdin.__class__, sys.exc_info, y, z
        f()
    except Exception:
        better_exchook(*sys.exc_info())

    try:
        f = lambda x: None
        # noinspection PyUnresolvedReferences,PyUnboundLocalVariable,PyArgumentList
        f(x, y)
    except Exception:
        better_exchook(*sys.exc_info())

    try:
        # noinspection PyArgumentList
        (lambda x: None)(__name__,
                         42)  # multiline
    except Exception:
        better_exchook(*sys.exc_info())

    try:
        class Obj:
            def __repr__(self):
                return (
                    "<Obj multi-\n" +
                    "     line repr>")
        obj = Obj()
        assert not obj
    except Exception:
        better_exchook(*sys.exc_info())

    # use this to overwrite the global exception handler
    sys.excepthook = better_exchook
    # and fail
    # noinspection PyUnresolvedReferences
    finalfail(sys)
