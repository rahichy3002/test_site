#!/usr/bin/env python3
"""Standalone Local Judge Server and Mock Exam Platform for Progsity.

Runs locally on Python standard library without external pip dependencies.
Provides:
  - Exact Progsity exam interface with dark UI
  - Real-time code execution judge (Python, Node.js, C++, C, Java)
  - Pre-validated 20-problem exam bank with language-locked IDE modes
  - Proctoring, watermark simulation, and stealth event auditor
"""

import http.server
import json
import os
import pathlib
import socketserver
import sys
import urllib.parse

# Import hardened sandbox execution engine
import sandbox_guard

PORT = int(os.environ.get("PORT", 5500))
BASE_DIR = pathlib.Path(__file__).parent.resolve()
PROBLEMS_DIR = BASE_DIR / "problems"
STATIC_DIR = BASE_DIR / "static"


def execute_code(code: str, language: str, stdin_data: str, timeout_sec: float = 2.0) -> dict:
    """Execute code strictly inside the hardened Windows kernel sandbox."""
    return sandbox_guard.execute_sandboxed(
        language=language,
        code=code,
        stdin_data=stdin_data,
        timeout_sec=timeout_sec,
        memory_limit_mb=256
    )





class ProgsityMockHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/problems":
            self.send_json(self.get_problems_list())
            return

        if path.startswith("/api/problem/"):
            prob_id = path.replace("/api/problem/", "").strip()
            prob_file = PROBLEMS_DIR / f"{prob_id}.json"
            if prob_file.exists():
                data = json.loads(prob_file.read_text(encoding="utf-8"))
                self.send_json(data)
            else:
                self.send_error(404, "Problem Not Found")
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_error(400, "Invalid JSON body")
            return

        if path == "/api/run":
            res = self.handle_run_sample(req_data)
            self.send_json(res)
            return

        if path == "/api/submit":
            res = self.handle_submit_grading(req_data)
            self.send_json(res)
            return

        self.send_error(404, "Not Found")

    def get_problems_list(self):
        probs = []
        files = sorted([p for p in PROBLEMS_DIR.glob("*.json") if p.stem.isdigit()], key=lambda x: int(x.stem))
        for p in files:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                probs.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "index": data.get("problem_index", ""),
                })
            except Exception:
                pass
        return probs

    def handle_run_sample(self, req: dict):
        prob_id = req.get("problem_id", 1)
        code = req.get("code", "")
        language = req.get("language", "cpp")
        custom_input = req.get("custom_input", None)

        prob_file = PROBLEMS_DIR / f"{prob_id}.json"
        if not prob_file.exists():
            return {"status": "Error", "message": "Problem not found"}

        prob_data = json.loads(prob_file.read_text(encoding="utf-8"))
        test_in = custom_input if custom_input is not None else prob_data.get("sample_input", "")
        expected_out = prob_data.get("sample_output", "").strip()

        exec_res = execute_code(code, language, test_in)
        stdout = exec_res["stdout"].rstrip()
        stderr = exec_res["stderr"].rstrip()

        passed = (stdout == expected_out) if custom_input is None else None

        if exec_res.get("security_error"):
            status = "Security Violation"
            passed = False
        elif exec_res.get("compile_error"):
            status = "Compilation Error"
            passed = False
        elif exec_res.get("tle"):
            status = "Time Limit Exceeded"
            passed = False
        else:
            status = "Passed" if passed is True else ("Failed" if passed is False else "Finished")

        return {
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "expected": expected_out,
            "elapsed_ms": exec_res.get("elapsed_ms", 0),
            "passed": passed,
        }

    def handle_submit_grading(self, req: dict):
        prob_id = req.get("problem_id", 1)
        code = req.get("code", "")
        language = req.get("language", "cpp")

        prob_file = PROBLEMS_DIR / f"{prob_id}.json"
        if not prob_file.exists():
            return {"status": "Error", "message": "Problem not found"}

        prob_data = json.loads(prob_file.read_text(encoding="utf-8"))
        tests = []
        tests.append({
            "input": prob_data.get("sample_input", ""),
            "expected_output": prob_data.get("sample_output", "").strip(),
        })
        tests.extend(prob_data.get("hidden_tests", []))

        results = []
        all_passed = True
        total_time = 0

        for idx, t in enumerate(tests, 1):
            exec_res = execute_code(code, language, t["input"])
            stdout = exec_res["stdout"].rstrip()
            expected = t["expected_output"].rstrip()

            if exec_res.get("security_error"):
                verdict = "Security Violation"
                all_passed = False
            elif exec_res.get("tle"):
                verdict = "Time Limit Exceeded"
                all_passed = False
            elif exec_res.get("compile_error"):
                verdict = "Compilation Error"
                all_passed = False
            elif exec_res["returncode"] != 0:
                verdict = "Runtime Error"
                all_passed = False
            elif stdout == expected:
                verdict = "Accepted"
            else:
                verdict = "Wrong Answer"
                all_passed = False

            total_time += exec_res.get("elapsed_ms", 0)
            results.append({
                "test": idx,
                "verdict": verdict,
                "elapsed_ms": exec_res.get("elapsed_ms", 0),
                "stderr": exec_res.get("stderr", ""),
            })

            if not all_passed and verdict in ("Compilation Error", "Time Limit Exceeded", "Security Violation"):
                break

        overall = "Accepted" if all_passed else results[-1]["verdict"]
        return {
            "verdict": overall,
            "passed_count": sum(1 for r in results if r["verdict"] == "Accepted"),
            "total_count": len(tests),
            "total_time_ms": round(total_time, 2),
            "test_results": results,
        }

    def send_json(self, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def update_problem_indices():
    """Ensure all problem files have accurate 'X / Total' indices."""
    files = sorted([p for p in PROBLEMS_DIR.glob("*.json") if p.stem.isdigit()], key=lambda x: int(x.stem))
    total = len(files)
    for idx, f in enumerate(files, 1):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            d["problem_index"] = f"{idx} / {total}"
            f.write_text(json.dumps(d, indent=2), encoding="utf-8")
        except Exception:
            pass


def main():
    os.chdir(str(BASE_DIR))
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    update_problem_indices()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ProgsityMockHandler) as httpd:
        print("=" * 65)
        print("  PROGSITY SECURED EXAM MOCK PLATFORM & JUDGE SERVER")
        print("=" * 65)
        print(f"  URL:             http://localhost:{PORT}")
        print(f"  Problems Loaded: {len(list(PROBLEMS_DIR.glob('*.json')))}")
        print("  Press Ctrl+C to stop server.")
        print("=" * 65 + "\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    main()
