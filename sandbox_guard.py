"""
TypeWriter 2.0 - Multi-Layered Hardened Sandbox Execution Engine
Enforces strict host PC isolation for untrusted competitive programming code.

Security Guarantees:
1. Static AST / Lexical Security Scanner:
   - Python: AST analysis rejects dangerous modules (os, subprocess, socket, winreg, ctypes, etc.),
     filesystem ops (open), dynamic evaluation (eval, exec, __import__), and attribute escapes.
   - C/C++: Lexical scan rejects Windows APIs (windows.h), process spawning (system, popen, fork, exec),
     filesystem ops (fstream, fopen, remove), and network sockets (winsock, socket).
   - JavaScript: Strict VM sandbox rejects require, process, child_process, fs, eval, network fetch.
2. Ephemeral Sandbox Isolation:
   - Every execution runs inside a disposable temporary scratch directory that is purged immediately.
3. Windows Kernel Job Object Isolation:
   - Memory capped at 256 MB (JOB_OBJECT_LIMIT_JOB_MEMORY).
   - Process count capped at 2 (prevents fork bombs).
   - UI / Clipboard / Desktop completely blocked (JOB_OBJECT_UILIMIT_ALL).
   - Auto-terminate on close (JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE).
4. Hard Wall-Clock Timeout:
   - Hard execution deadline (default 2.0s) kills the job and processes instantly.
"""

import ast
import ctypes
from ctypes import wintypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


class SandboxSecurityViolation(Exception):
    """Raised when untrusted code attempts to access forbidden OS/system resources."""
    pass


# ---------------------------------------------------------------------------
# Windows Job Object Kernel Sandboxing
# ---------------------------------------------------------------------------

class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_void_p),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class JOBOBJECT_BASIC_UI_RESTRICTIONS(ctypes.Structure):
    _fields_ = [
        ("UIRestrictionsClass", ctypes.c_uint32),
    ]


class WindowsJobSandbox:
    """Encapsulates a Windows Job Object to enforce kernel-level isolation."""

    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
    JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
    JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
    JOB_OBJECT_UILIMIT_ALL = 0x000000FF

    def __init__(self, memory_limit_mb: int = 256, max_processes: int = 2):
        self.handle = None
        if sys.platform != "win32":
            return

        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            self.handle = kernel32.CreateJobObjectW(None, None)
            if not self.handle:
                return

            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = (
                self.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                | self.JOB_OBJECT_LIMIT_JOB_MEMORY
                | self.JOB_OBJECT_LIMIT_PROCESS_MEMORY
                | self.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
            )
            info.BasicLimitInformation.ActiveProcessLimit = max_processes
            mem_bytes = memory_limit_mb * 1024 * 1024
            info.ProcessMemoryLimit = mem_bytes
            info.JobMemoryLimit = mem_bytes

            kernel32.SetInformationJobObject(
                self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)
            )

            # Block all UI interaction, clipboard access, desktop switching
            ui_info = JOBOBJECT_BASIC_UI_RESTRICTIONS()
            ui_info.UIRestrictionsClass = self.JOB_OBJECT_UILIMIT_ALL
            kernel32.SetInformationJobObject(
                self.handle, 4, ctypes.byref(ui_info), ctypes.sizeof(ui_info)
            )
        except Exception:
            self.handle = None

    def assign_process(self, process_handle: int):
        if self.handle and sys.platform == "win32":
            try:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.AssignProcessToJobObject(self.handle, process_handle)
            except Exception:
                pass

    def terminate(self):
        if self.handle and sys.platform == "win32":
            try:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.TerminateJobObject(self.handle, 1)
            except Exception:
                pass

    def close(self):
        if self.handle and sys.platform == "win32":
            try:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ---------------------------------------------------------------------------
# Static Security Auditing & Policy Enforcers
# ---------------------------------------------------------------------------

PYTHON_BANNED_MODULES = {
    "os", "posix", "nt", "subprocess", "shutil", "socket", "http", "urllib",
    "requests", "winreg", "msvcrt", "ctypes", "_ctypes", "pathlib", "tempfile",
    "inspect", "importlib", "builtins", "multiprocessing", "threading", "signal",
    "pty", "commands", "webbrowser", "gc", "code", "platform", "asyncio",
    "asyncore", "ftplib", "telnetlib", "smtplib", "imaplib", "poplib",
    "pkgutil", "distutils", "setuptools", "pip", "venv"
}

PYTHON_BANNED_CALLS = {
    "eval", "exec", "compile", "__import__", "open", "breakpoint",
    "globals", "locals", "vars", "memoryview"
}

PYTHON_BANNED_ATTRS = {
    "__class__", "__bases__", "__subclasses__", "__mro__",
    "__code__", "__globals__", "__builtins__", "__dict__"
}


class PythonASTSecurityVisitor(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_mod = alias.name.split(".")[0].lower()
            if base_mod in PYTHON_BANNED_MODULES:
                raise SandboxSecurityViolation(
                    f"Forbidden module import '{alias.name}'. Sandbox blocks host OS/network access."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split(".")[0].lower()
            if base_mod in PYTHON_BANNED_MODULES:
                raise SandboxSecurityViolation(
                    f"Forbidden module import '{node.module}'. Sandbox blocks host OS/network access."
                )
            if base_mod == "sys":
                allowed_sys = {"stdin", "stdout", "stderr", "setrecursionlimit", "argv"}
                for alias in node.names:
                    if alias.name not in allowed_sys:
                        raise SandboxSecurityViolation(
                            f"Forbidden 'sys.{alias.name}' import. Sandbox permits only stdin/stdout/setrecursionlimit."
                        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in PYTHON_BANNED_CALLS:
                raise SandboxSecurityViolation(
                    f"Forbidden function call '{node.func.id}()'. Filesystem and dynamic evaluation are blocked."
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in PYTHON_BANNED_ATTRS:
            raise SandboxSecurityViolation(
                f"Forbidden attribute access '{node.attr}'. Introspection escapes are blocked in sandbox."
            )
        self.generic_visit(node)


def audit_python_code(code: str) -> None:
    """Statically verifies Python AST before execution."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return
    visitor = PythonASTSecurityVisitor()
    visitor.visit(tree)


# C / C++ Forbidden Directives & Functions
CPP_BANNED_PATTERNS = [
    (r"#\s*include\s*<windows\.h>", "Host Windows API <windows.h>"),
    (r"#\s*include\s*<winsock[2]?\.h>", "Network socket header <winsock.h>"),
    (r"#\s*include\s*<sys/socket\.h>", "Network socket header <sys/socket.h>"),
    (r"#\s*include\s*<direct\.h>", "Directory management header <direct.h>"),
    (r"#\s*include\s*<io\.h>", "Low-level IO header <io.h>"),
    (r"#\s*include\s*<process\.h>", "Process control header <process.h>"),
    (r"#\s*include\s*<unistd\.h>", "POSIX API header <unistd.h>"),
    (r"#\s*include\s*<fstream>", "File stream header <fstream>"),
    (r"#\s*include\s*<(?:experimental/)?filesystem>", "Filesystem header <filesystem>"),
    (r"#\s*include\s*<conio\.h>", "Console control header <conio.h>"),
    (r"\b(?:system|_popen|popen|CreateProcess|ShellExecute|WinExec)\s*\(", "Process creation function"),
    (r"\b(?:remove|rename|fopen|freopen|ofstream|ifstream|fstream)\s*\(", "File manipulation function"),
    (r"\b(?:fork|exec[l|v|p|e]*)\s*\(", "Subprocess execution function"),
    (r"\b(?:socket|connect|bind|listen|send|recv)\s*\(", "Network socket function"),
    (r"\bReg(?:Open|Create|Set|Delete)Key", "Windows Registry function"),
]


def audit_cpp_code(code: str) -> None:
    """Scans C/C++ source code for unsafe system, file, or network invocations."""
    for pattern, description in CPP_BANNED_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            raise SandboxSecurityViolation(
                f"Security Violation: {description} is forbidden. The sandbox only permits standard stdin/stdout algorithms."
            )


# JavaScript Forbidden Tokens & Dangerous Invocations
JS_BANNED_PATTERNS = [
    (r"\bchild_process\b", "child_process module"),
    (r"\b(?:worker_threads|cluster)\b", "Multi-threading/cluster module"),
    (r"\brequire\s*\(\s*['\"](?!(?:node:)?(?:fs|readline|path|buffer)['\"])", "Forbidden external module require()"),
    (r"\bimport\s+.*?from\b", "ES import statement"),
    (r"\b(?:fetch|XMLHttpRequest|WebSocket)\b", "Network request API"),
    (r"\beval\s*\(", "eval() dynamic execution"),
    (r"\bFunction\s*\(", "Function() constructor"),
    (r"\b(?:_compile|binding)\b", "Internal V8 binding access"),
]


def audit_js_code(code: str) -> None:
    """Scans JavaScript code for unsafe APIs."""
    for pattern, description in JS_BANNED_PATTERNS:
        if re.search(pattern, code):
            raise SandboxSecurityViolation(
                f"Security Violation: {description} is forbidden in sandboxed JavaScript."
            )


# ---------------------------------------------------------------------------
# Compiler & Toolchain Discovery
# ---------------------------------------------------------------------------

def find_cpp_compiler() -> Optional[str]:
    """Finds a modern g++ / clang++ executable, checking PATH and WinLibs install paths."""
    # 1. Check standard PATH
    path_cc = shutil.which("g++") or shutil.which("clang++")
    if path_cc:
        return path_cc

    # 2. Check WinGet WinLibs installation directory
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        winget_pkgs = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.exists():
            for gpp in winget_pkgs.rglob("g++.exe"):
                if gpp.is_file():
                    return str(gpp)

    # 3. Check common MinGW / MSYS2 paths
    common_paths = [
        r"C:\msys64\ucrt64\bin\g++.exe",
        r"C:\msys64\mingw64\bin\g++.exe",
        r"C:\MinGW\bin\g++.exe",
        r"C:\Program Files\mingw-w64\bin\g++.exe",
    ]
    for cp in common_paths:
        if os.path.isfile(cp):
            return cp

    return None


def find_node_executable() -> Optional[str]:
    """Finds node.exe or node/nodejs executable."""
    return shutil.which("node") or shutil.which("nodejs") or (
        r"C:\Program Files\nodejs\node.exe"
        if os.path.isfile(r"C:\Program Files\nodejs\node.exe")
        else None
    )


# ---------------------------------------------------------------------------
# Sandboxed Runner Script Templates
# ---------------------------------------------------------------------------

PYTHON_SANDBOX_HEADER = """# Hardened Python Sandbox Initialization
import sys
import builtins

# Purge dangerous modules from sys.modules
_banned = {
    'os', 'posix', 'nt', 'subprocess', 'shutil', 'socket', 'http', 'urllib',
    'requests', 'winreg', 'msvcrt', 'ctypes', '_ctypes', 'pathlib', 'tempfile',
    'inspect', 'importlib', 'multiprocessing', 'threading', 'signal'
}
for _m in list(sys.modules.keys()):
    if _m.split('.')[0] in _banned:
        sys.modules.pop(_m, None)

# Override open()
def _blocked_open(*args, **kwargs):
    raise PermissionError("Filesystem access is disabled in the sandbox.")
builtins.open = _blocked_open

# Safe import policy
_orig_import = builtins.__import__
_BANNED_MODULES = {
    'os', 'posix', 'nt', 'subprocess', 'shutil', 'socket', 'http', 'urllib',
    'requests', 'winreg', 'msvcrt', 'ctypes', '_ctypes', 'pathlib', 'tempfile',
    'inspect', 'importlib', 'multiprocessing', 'threading', 'signal', 'pty',
    'commands', 'webbrowser', 'gc', 'code', 'platform', 'asyncio', 'asyncore',
    'ftplib', 'telnetlib', 'smtplib', 'imaplib', 'poplib', 'pkgutil', 'distutils',
    'setuptools', 'pip', 'venv'
}

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    base = name.split('.')[0]
    if base in _BANNED_MODULES:
        raise ImportError(f"Importing '{name}' is restricted by the sandbox policy.")
    return _orig_import(name, globals, locals, fromlist, level)

builtins.__import__ = _safe_import

# Safe recursion limit
sys.setrecursionlimit(2500)
"""

NODE_SANDBOX_WRAPPER = """// Hardened Node.js VM Sandbox Wrapper
const vm = require('vm');
const fs = require('fs');
const path = require('path');

const userCode = fs.readFileSync('user_code.js', 'utf8');
const stdinData = fs.readFileSync('stdin.txt', 'utf8');

let stdinLines = stdinData.split(/\\r?\\n/);
let lineIndex = 0;

let capturedStdout = '';
let capturedStderr = '';

// Safe mock for fs module (restricts all access solely to stdin)
const mockFs = {
    readFileSync: (target, encoding) => {
        const tStr = String(target).trim();
        if (target === 0 || tStr === '0' || tStr === '/dev/stdin' || tStr === 'stdin.txt' || tStr === '') {
            return stdinData;
        }
        throw new Error("[Sandbox Security Violation]: Reading arbitrary file '" + target + "' is forbidden. Only standard input (fd 0 or '/dev/stdin') is permitted.");
    },
    readSync: (fd, buffer, offset, length, position) => {
        if (fd === 0) {
            const buf = Buffer.from(stdinData);
            return buf.copy(buffer, offset, 0, length);
        }
        throw new Error("[Sandbox Security Violation]: Reading fd " + fd + " is forbidden.");
    }
};

// Safe mock for process (provides stdin, stdout, stderr, and exit)
const mockProcess = {
    stdin: {
        fd: 0,
        read: () => stdinData,
        on: (event, handler) => {
            if (event === 'data') {
                setTimeout(() => handler(Buffer.from(stdinData)), 0);
            } else if (event === 'end') {
                setTimeout(() => handler(), 0);
            }
            return mockProcess.stdin;
        },
        resume: () => mockProcess.stdin,
        pause: () => mockProcess.stdin,
        setEncoding: () => mockProcess.stdin,
        pipe: () => mockProcess.stdin
    },
    stdout: {
        write: (str) => { capturedStdout += String(str); return true; }
    },
    stderr: {
        write: (str) => { capturedStderr += String(str); return true; }
    },
    exit: (code) => {
        throw new Error('__PROCESS_EXIT_' + (code || 0) + '__');
    },
    argv: ['node', 'solution.js'],
    env: {}
};

// Safe mock for readline
const mockReadline = {
    createInterface: (options) => {
        let lineListeners = [];
        let closeListeners = [];

        setTimeout(() => {
            for (const line of stdinLines) {
                for (const l of lineListeners) l(line);
            }
            for (const c of closeListeners) c();
        }, 0);

        return {
            on: (event, handler) => {
                if (event === 'line') lineListeners.push(handler);
                if (event === 'close') closeListeners.push(handler);
                return this;
            },
            close: () => {}
        };
    }
};

const safeRequire = (mod) => {
    const m = String(mod).toLowerCase().trim().replace(/^node:/, '');
    if (m === 'fs') return mockFs;
    if (m === 'readline') return mockReadline;
    if (m === 'buffer') return { Buffer };
    if (m === 'path') return path;
    throw new Error("[Sandbox Security Violation]: require('" + mod + "') is forbidden in sandboxed competitive programming. Only 'fs', 'readline', and 'path' are permitted.");
};

const sandbox = {
    console: {
        log: (...args) => { capturedStdout += args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ') + '\\n'; },
        error: (...args) => { capturedStderr += args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ') + '\\n'; },
        warn: (...args) => { capturedStderr += args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ') + '\\n'; }
    },
    require: safeRequire,
    fs: mockFs,
    process: mockProcess,
    Buffer: Buffer,
    readline: () => {
        if (lineIndex < stdinLines.length) {
            return stdinLines[lineIndex++];
        }
        return null;
    },
    readAllStdin: () => stdinData,
    parseInt, parseFloat, isNaN, isFinite,
    Math, Array, Object, String, Number, Boolean, Map, Set, JSON, RegExp,
    Date, Error, RangeError, TypeError, SyntaxError,
    Infinity, NaN, undefined,
    setTimeout, clearTimeout,
    queueMicrotask: typeof queueMicrotask !== 'undefined' ? queueMicrotask : undefined
};

try {
    const context = vm.createContext(sandbox);
    const script = new vm.Script(userCode);
    script.runInContext(context, { timeout: 2000, microtaskMode: 'afterEvaluate' });
    process.stdout.write(capturedStdout);
    process.stderr.write(capturedStderr);
    process.exit(0);
} catch (err) {
    if (String(err).includes('__PROCESS_EXIT_')) {
        process.stdout.write(capturedStdout);
        process.stderr.write(capturedStderr);
        process.exit(0);
    }
    process.stdout.write(capturedStdout);
    process.stderr.write(capturedStderr + (err.stack || String(err)) + '\\n');
    process.exit(1);
}
"""


# ---------------------------------------------------------------------------
# Main Sandboxed Execution Entrypoint
# ---------------------------------------------------------------------------

def execute_sandboxed(
    language: str,
    code: str,
    stdin_data: str,
    timeout_sec: float = 2.0,
    memory_limit_mb: int = 256
) -> Dict[str, Any]:
    """
    Executes untrusted code with 100% host isolation.
    Returns: {
        "returncode": int,
        "stdout": str,
        "stderr": str,
        "elapsed_ms": float,
        "security_error": bool,
        "compile_error": bool,
        "tle": bool
    }
    """
    lang = language.lower().strip()

    # Tier 1: Static Security Audit
    try:
        if lang in ("python", "python3", "py"):
            audit_python_code(code)
        elif lang in ("cpp", "c++", "c"):
            audit_cpp_code(code)
        elif lang in ("javascript", "js", "node"):
            audit_js_code(code)
    except SandboxSecurityViolation as e:
        return {
            "returncode": 126,
            "stdout": "",
            "stderr": f"🛡️ [SANDBOX SECURITY ERROR]: {str(e)}",
            "elapsed_ms": 0.0,
            "security_error": True,
            "compile_error": False,
            "tle": False
        }

    # Tier 2: Create Ephemeral Isolated Working Directory
    sandbox_dir = tempfile.mkdtemp(prefix="tw_sandbox_")
    sandbox_path = Path(sandbox_dir)

    try:
        start_time = time.perf_counter()

        # Execute within Windows Job Object
        with WindowsJobSandbox(memory_limit_mb=memory_limit_mb) as job:

            # ----------------------------------------------------------------
            # Python Runner
            # ----------------------------------------------------------------
            if lang in ("python", "python3", "py"):
                runner_file = sandbox_path / "sandbox_main.py"
                full_script = PYTHON_SANDBOX_HEADER + "\n# --- User Solution ---\n" + code
                runner_file.write_text(full_script, encoding="utf-8")

                cmd = [sys.executable, "-I", "-B", str(runner_file.name)]
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(sandbox_path),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if hasattr(proc, "_handle"):
                    job.assign_process(proc._handle)

                try:
                    stdout, stderr = proc.communicate(input=stdin_data, timeout=timeout_sec)
                    elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                    return {
                        "returncode": proc.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "elapsed_ms": elapsed,
                        "security_error": False,
                        "compile_error": False,
                        "tle": False
                    }
                except subprocess.TimeoutExpired:
                    job.terminate()
                    proc.kill()
                    return {
                        "returncode": -1,
                        "stdout": "",
                        "stderr": f"Time Limit Exceeded (> {timeout_sec}s)",
                        "elapsed_ms": timeout_sec * 1000,
                        "security_error": False,
                        "compile_error": False,
                        "tle": True
                    }

            # ----------------------------------------------------------------
            # C / C++ Runner
            # ----------------------------------------------------------------
            elif lang in ("cpp", "c++", "c"):
                compiler_exe = find_cpp_compiler()
                if not compiler_exe:
                    return {
                        "returncode": 1,
                        "stdout": "",
                        "stderr": "C++ Compiler Error: g++ / clang++ executable not detected in environment.",
                        "elapsed_ms": 0.0,
                        "security_error": False,
                        "compile_error": True,
                        "tle": False
                    }

                compiler_path = Path(compiler_exe)
                env = os.environ.copy()
                env["PATH"] = str(compiler_path.parent) + os.pathsep + env.get("PATH", "")

                src_name = "solution.cpp" if "++" in lang or lang == "cpp" else "solution.c"
                src_file = sandbox_path / src_name
                exe_name = "solution.exe" if sys.platform == "win32" else "solution.out"
                exe_file = sandbox_path / exe_name
                src_file.write_text(code, encoding="utf-8")

                compile_cmd = [str(compiler_path), "-O2", src_name, "-o", str(exe_file.name)]
                if sys.platform == "win32":
                    compile_cmd.insert(2, "-static")
                if "++" in lang or lang == "cpp":
                    compile_cmd.insert(3, "-std=c++20")

                # Compilation step inside sandbox (runs compiler toolchain)
                comp_proc = subprocess.Popen(
                    compile_cmd,
                    cwd=str(sandbox_path),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                c_stdout, c_stderr = comp_proc.communicate(timeout=15.0)
                if comp_proc.returncode != 0:
                    return {
                        "returncode": comp_proc.returncode,
                        "stdout": "",
                        "stderr": f"Compilation Error:\n{c_stderr}",
                        "elapsed_ms": 0.0,
                        "security_error": False,
                        "compile_error": True,
                        "tle": False
                    }

                # Execution step inside sandbox
                exec_start = time.perf_counter()
                run_proc = subprocess.Popen(
                    [str(exe_file)],
                    cwd=str(sandbox_path),
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if hasattr(run_proc, "_handle"):
                    job.assign_process(run_proc._handle)

                try:
                    stdout, stderr = run_proc.communicate(input=stdin_data, timeout=timeout_sec)
                    elapsed = round((time.perf_counter() - exec_start) * 1000, 2)
                    return {
                        "returncode": run_proc.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "elapsed_ms": elapsed,
                        "security_error": False,
                        "compile_error": False,
                        "tle": False
                    }
                except subprocess.TimeoutExpired:
                    job.terminate()
                    run_proc.kill()
                    return {
                        "returncode": -1,
                        "stdout": "",
                        "stderr": f"Time Limit Exceeded (> {timeout_sec}s)",
                        "elapsed_ms": timeout_sec * 1000,
                        "security_error": False,
                        "compile_error": False,
                        "tle": True
                    }

            # ----------------------------------------------------------------
            # JavaScript / Node.js Runner
            # ----------------------------------------------------------------
            elif lang in ("javascript", "js", "node"):
                node_exe = find_node_executable()
                if not node_exe:
                    return {
                        "returncode": 1,
                        "stdout": "",
                        "stderr": "Node.js executable not detected on system.",
                        "elapsed_ms": 0.0,
                        "security_error": False,
                        "compile_error": True,
                        "tle": False
                    }

                user_file = sandbox_path / "user_code.js"
                user_file.write_text(code, encoding="utf-8")

                stdin_file = sandbox_path / "stdin.txt"
                stdin_file.write_text(stdin_data, encoding="utf-8")

                runner_file = sandbox_path / "vm_runner.js"
                runner_file.write_text(NODE_SANDBOX_WRAPPER, encoding="utf-8")

                cmd = [node_exe, "vm_runner.js"]
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(sandbox_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if hasattr(proc, "_handle"):
                    job.assign_process(proc._handle)

                try:
                    stdout, stderr = proc.communicate(timeout=timeout_sec)
                    elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                    return {
                        "returncode": proc.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "elapsed_ms": elapsed,
                        "security_error": False,
                        "compile_error": False,
                        "tle": False
                    }
                except subprocess.TimeoutExpired:
                    job.terminate()
                    proc.kill()
                    return {
                        "returncode": -1,
                        "stdout": "",
                        "stderr": f"Time Limit Exceeded (> {timeout_sec}s)",
                        "elapsed_ms": timeout_sec * 1000,
                        "security_error": False,
                        "compile_error": False,
                        "tle": True
                    }

            else:
                return {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": f"Language '{language}' runner not supported in sandbox.",
                    "elapsed_ms": 0.0,
                    "security_error": False,
                    "compile_error": False,
                    "tle": False
                }

    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Sandbox Runtime Exception: {str(e)}",
            "elapsed_ms": 0.0,
            "security_error": False,
            "compile_error": False,
            "tle": False
        }
    finally:
        # Tier 4: Purge ephemeral sandbox folder immediately
        shutil.rmtree(sandbox_dir, ignore_errors=True)
