#!/usr/bin/env python3
"""Automated tests for Testing Site AI Generator & Hardened Sandbox Engine."""

import json
import pathlib
import subprocess
import sys
import time
import urllib.request
import unittest

BASE_DIR = pathlib.Path(__file__).parent.resolve()
SERVER_PY = BASE_DIR / "server.py"
PROBLEMS_DIR = BASE_DIR / "problems"


class TestTestingSiteGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start server in background
        cls.proc = subprocess.Popen([sys.executable, str(SERVER_PY)])
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        if cls.proc:
            cls.proc.terminate()
            cls.proc.wait()

    def test_01_config_api(self):
        with urllib.request.urlopen("http://localhost:5500/api/config") as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read().decode())
            self.assertIn("base_url", data)
            self.assertIn("model", data)

    def test_02_two_stage_self_validation(self):
        from server import execute_code

        sample_in = "4\n1 2 3 4\n"
        ref_py = (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "if data:\n"
            "    nums = [int(x) for x in data[1:]]\n"
            "    print(sum(nums))\n"
        )

        res = execute_code(ref_py, "python", sample_in)
        self.assertEqual(res["returncode"], 0)
        self.assertEqual(res["stdout"].strip(), "10")

    def test_03_sandbox_blocks_python_attack(self):
        payload = json.dumps({
            "problem_id": 1,
            "code": "import os\nos.system('calc')",
            "language": "python"
        }).encode()
        req = urllib.request.Request(
            "http://localhost:5500/api/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read().decode())
            self.assertEqual(data["status"], "Security Violation")
            self.assertIn("SANDBOX SECURITY ERROR", data["stderr"])

    def test_04_sandbox_blocks_cpp_attack(self):
        payload = json.dumps({
            "problem_id": 1,
            "code": "#include <windows.h>\nint main(){ return 0; }",
            "language": "cpp"
        }).encode()
        req = urllib.request.Request(
            "http://localhost:5500/api/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read().decode())
            self.assertEqual(data["status"], "Security Violation")
            self.assertIn("Host Windows API <windows.h>", data["stderr"])

    def test_05_cpp_bracket_problem_run_and_submit(self):
        cpp_code = """#include <iostream>
#include <stack>
#include <string>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        string s;
        cin >> s;
        stack<char> st;
        bool ok = true;
        for (char c : s) {
            if (c == '(' || c == '{' || c == '[') {
                st.push(c);
            } else {
                if (st.empty()) { ok = false; break; }
                char top = st.top();
                st.pop();
                if ((c == ')' && top != '(') ||
                    (c == '}' && top != '{') ||
                    (c == ']' && top != '[')) {
                    ok = false;
                    break;
                }
            }
        }
        if (ok && st.empty()) cout << "YES\\n";
        else cout << "NO\\n";
    }
    return 0;
}"""

        # 1. Run against sample
        payload = json.dumps({
            "problem_id": 2,
            "code": cpp_code,
            "language": "cpp"
        }).encode()
        req = urllib.request.Request(
            "http://localhost:5500/api/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read().decode())
            self.assertEqual(data["status"], "Passed")
            self.assertTrue(data["passed"])
            self.assertEqual(data["stdout"].strip(), "YES\nNO\nYES")

        # 2. Submit for grading
        req_sub = urllib.request.Request(
            "http://localhost:5500/api/submit",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_sub) as r:
            self.assertEqual(r.status, 200)
            sub_data = json.loads(r.read().decode())
            self.assertEqual(sub_data["verdict"], "Accepted")
            self.assertEqual(sub_data["passed_count"], sub_data["total_count"])


if __name__ == "__main__":
    unittest.main()
