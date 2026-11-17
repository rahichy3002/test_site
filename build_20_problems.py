"""
Builds and self-validates 20 comprehensive competitive programming exam tasks
distributed across C++, Python, JavaScript, and C.
"""

import json
import pathlib
import sys

# Ensure sandbox_guard can be imported
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sandbox_guard

PROBLEMS_DIR = pathlib.Path(__file__).parent / "problems"

LANG_MAP = {
    "cpp": "C++ (C++20)",
    "python": "Python 3 (Python 3.12)",
    "javascript": "JavaScript (Node.js 20)",
    "c": "C (C17)",
}

RAW_PROBLEMS = [
    # -------------------------------------------------------------------------
    # Problem 1: C++ - Kenji's CSV Parser
    # -------------------------------------------------------------------------
    {
        "id": 1,
        "title": "Kenji's CSV Parser",
        "lang": "cpp",
        "statement": "<p>Kenji is building a robust CSV data importer for his financial analytics engine. In standard CSV, fields are separated by commas. However, if a field contains commas or quotes, the entire field is surrounded by double quotes. Inside a quoted field, a literal quote is represented by two consecutive double quotes (<code>\"\"</code>).</p><p>Given <code>N</code> lines of CSV records, parse each record into its individual fields and output the number of fields followed by each field enclosed in brackets <code>[...]</code>.</p>",
        "input_format": "The first line contains an integer N (1 <= N <= 100). The next N lines each contain a single CSV line string.",
        "output_format": "For each record, output the count of fields followed by each field enclosed in brackets [field].",
        "constraints": "1 <= N <= 100\n1 <= length of each line <= 1000",
        "sample_input": "2\napple,banana,cherry\n\"She said, \"\"hello!\"\"\",123,\"foo,bar\"",
        "hidden_inputs": [
            "1\n\"\",single,\"two,parts\",end",
            "2\nsimple\na,,b"
        ],
        "ref_code": """#include <iostream>
#include <string>
#include <vector>
using namespace std;

void parseLine(const string& line) {
    vector<string> fields;
    string cur = "";
    bool inQuotes = false;
    for (size_t i = 0; i < line.length(); ++i) {
        char c = line[i];
        if (inQuotes) {
            if (c == '"' && i + 1 < line.length() && line[i+1] == '"') {
                cur += '"';
                ++i;
            } else if (c == '"') {
                inQuotes = false;
            } else {
                cur += c;
            }
        } else {
            if (c == '"') {
                inQuotes = true;
            } else if (c == ',') {
                fields.push_back(cur);
                cur = "";
            } else {
                cur += c;
            }
        }
    }
    fields.push_back(cur);
    cout << fields.size();
    for (const auto& f : fields) cout << " [" << f << "]";
    cout << "\\n";
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int n;
    if (cin >> n) {
        string dummy;
        getline(cin, dummy);
        while (n--) {
            string line;
            getline(cin, line);
            parseLine(line);
        }
    }
    return 0;
}""",
        "templates": {
            "cpp": "#include <iostream>\n#include <string>\n#include <vector>\nusing namespace std;\n\nint main() {\n    ios_base::sync_with_stdio(false);\n    cin.tie(NULL);\n    // Your CSV parser code here\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 2: C++ - Valid Bracket Sequence
    # -------------------------------------------------------------------------
    {
        "id": 2,
        "title": "Valid Bracket Sequence",
        "lang": "cpp",
        "statement": "<p>You are given a string containing parentheses, brackets, and braces: <code>'('</code>, <code>')'</code>, <code>'{'</code>, <code>'}'</code>, <code>'['</code>, and <code>']'</code>. Determine if the input string is valid.</p><p>An input string is valid if open brackets are closed by the same type of brackets in the correct order, and every close bracket has a matching open bracket.</p>",
        "input_format": "The first line contains an integer T, the number of test cases. The next T lines each contain a single bracket sequence string.",
        "output_format": "For each testcase, print 'YES' if valid or 'NO' otherwise.",
        "constraints": "1 <= T <= 100\n1 <= length of string <= 10^5",
        "sample_input": "3\n{[()]}\n{[(])}\n{{[[(())]]}}",
        "hidden_inputs": [
            "4\n(\n]\n({[]})\n()[]{}",
            "2\n((((\n))))"
        ],
        "ref_code": """#include <iostream>
#include <stack>
#include <string>
using namespace std;

bool isValid(const string& s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '{' || c == '[') {
            st.push(c);
        } else {
            if (st.empty()) return false;
            char top = st.top();
            st.pop();
            if ((c == ')' && top != '(') ||
                (c == '}' && top != '{') ||
                (c == ']' && top != '[')) return false;
        }
    }
    return st.empty();
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int t;
    if (cin >> t) {
        while (t--) {
            string s;
            cin >> s;
            cout << (isValid(s) ? "YES\\n" : "NO\\n");
        }
    }
    return 0;
}""",
        "templates": {
            "cpp": "#include <iostream>\n#include <string>\n#include <stack>\nusing namespace std;\n\nint main() {\n    ios_base::sync_with_stdio(false);\n    cin.tie(NULL);\n    // Your code here\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 3: Python - Balanced Subarray Sum
    # -------------------------------------------------------------------------
    {
        "id": 3,
        "title": "Balanced Subarray Sum",
        "lang": "python",
        "statement": "<p>Given an array of integers, find the length of the longest contiguous subarray such that the sum of its elements is equal to the number of elements in that subarray. For example, in <code>[2, 2]</code>, the sum is 4 and length is 2 (not equal). But in <code>[1, 1, 1]</code> sum is 3 and length is 3 (equal).</p>",
        "input_format": "The first line contains an integer N (1 <= N <= 10^5). The second line contains N integers A[1], A[2], ..., A[N].",
        "output_format": "Output a single integer representing the maximum length of such a subarray. If none exists, output 0.",
        "constraints": "1 <= N <= 10^5\n-10^9 <= A[i] <= 10^9",
        "sample_input": "5\n1 2 3 2 2",
        "hidden_inputs": [
            "1\n1",
            "6\n2 0 2 0 1 1"
        ],
        "ref_code": """import sys

def main():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    arr = [int(x) for x in input_data[1:n+1]]
    
    # sum(A[i..j]) == (j - i + 1) <=> sum(A[k] - 1 for k in i..j) == 0
    prefix_map = {0: -1}
    curr = 0
    max_len = 0
    for idx, val in enumerate(arr):
        curr += (val - 1)
        if curr in prefix_map:
            max_len = max(max_len, idx - prefix_map[curr])
        else:
            prefix_map[curr] = idx
    print(max_len)

if __name__ == '__main__':
    main()""",
        "templates": {
            "python": "import sys\n\ndef main():\n    data = sys.stdin.read().split()\n    # Write your solution here\n\nif __name__ == '__main__':\n    main()\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 4: JavaScript - Log Severity Aggregator
    # -------------------------------------------------------------------------
    {
        "id": 4,
        "title": "Log Severity Aggregator",
        "lang": "javascript",
        "statement": "<p>A cloud server generates structured log lines in the format: <code>[TIMESTAMP] [SEVERITY] MESSAGE</code>. Severity levels are <code>INFO</code>, <code>WARN</code>, <code>ERROR</code>, and <code>FATAL</code>.</p><p>Parse the logs and output the total count for each severity level in the exact format: <code>INFO: X, WARN: Y, ERROR: Z, FATAL: W</code>.</p>",
        "input_format": "The first line contains an integer N. The next N lines each contain a log line.",
        "output_format": "Output a single line: INFO: X, WARN: Y, ERROR: Z, FATAL: W",
        "constraints": "1 <= N <= 1000",
        "sample_input": "4\n[2026-11-17 10:00:01] [INFO] Server started\n[2026-11-17 10:00:02] [WARN] Memory high\n[2026-11-17 10:00:03] [ERROR] Connection timeout\n[2026-11-17 10:00:04] [INFO] Client disconnected",
        "hidden_inputs": [
            "2\n[10:00] [FATAL] System crash\n[10:01] [FATAL] Rebooting",
            "1\n[00:00] [WARN] Test"
        ],
        "ref_code": """let n = parseInt(readline());
let counts = { INFO: 0, WARN: 0, ERROR: 0, FATAL: 0 };
for (let i = 0; i < n; i++) {
    let line = readline();
    if (!line) continue;
    let match = line.match(/\\[(INFO|WARN|ERROR|FATAL)\\]/);
    if (match && counts.hasOwnProperty(match[1])) {
        counts[match[1]]++;
    }
}
console.log(`INFO: ${counts.INFO}, WARN: ${counts.WARN}, ERROR: ${counts.ERROR}, FATAL: ${counts.FATAL}`);""",
        "templates": {
            "javascript": "function main() {\n    let n = parseInt(readline());\n    // Write your solution here\n}\nmain();\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 5: C - Hexadecimal Byte Aligner
    # -------------------------------------------------------------------------
    {
        "id": 5,
        "title": "Hexadecimal Byte Aligner",
        "lang": "c",
        "statement": "<p>Given an array of 32-bit unsigned integers, pack each integer into big-endian byte order and output each byte as an uppercase 2-digit hexadecimal number separated by spaces. If the number of bytes is not a multiple of 4, pad with zeros.</p>",
        "input_format": "The first line contains an integer N. The next line contains N unsigned 32-bit integers.",
        "output_format": "Print each byte in big-endian order as uppercase 2-digit hex (e.g. 0A 1B FF) separated by spaces.",
        "constraints": "1 <= N <= 100\n0 <= A[i] <= 4294967295",
        "sample_input": "2\n305419896 1",
        "hidden_inputs": [
            "1\n0",
            "3\n255 65535 16777215"
        ],
        "ref_code": """#include <stdio.h>
#include <stdint.h>

int main() {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int first = 1;
    for (int i = 0; i < n; ++i) {
        uint32_t val;
        scanf("%u", &val);
        uint8_t bytes[4];
        bytes[0] = (val >> 24) & 0xFF;
        bytes[1] = (val >> 16) & 0xFF;
        bytes[2] = (val >> 8) & 0xFF;
        bytes[3] = val & 0xFF;
        for (int j = 0; j < 4; ++j) {
            if (!first) printf(" ");
            printf("%02X", bytes[j]);
            first = 0;
        }
    }
    printf("\\n");
    return 0;
}""",
        "templates": {
            "c": "#include <stdio.h>\n#include <stdint.h>\n\nint main() {\n    // Write your C solution here\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 6: Python - Min-Cost Flight Itinerary
    # -------------------------------------------------------------------------
    {
        "id": 6,
        "title": "Min-Cost Flight Itinerary",
        "lang": "python",
        "statement": "<p>You are given a directed graph of <code>N</code> airports labeled <code>1</code> to <code>N</code> connected by <code>M</code> one-way flights. Each flight has a cost <code>W</code>. Find the minimum cost to travel from airport <code>1</code> to airport <code>N</code>. If airport <code>N</code> is unreachable, output <code>-1</code>.</p>",
        "input_format": "First line: N M (number of airports and flights). Next M lines: u v w (flight from u to v with cost w).",
        "output_format": "Print the minimum flight cost from 1 to N, or -1 if unreachable.",
        "constraints": "2 <= N <= 1000\n1 <= M <= 5000\n1 <= w <= 10^6",
        "sample_input": "4 4\n1 2 100\n2 4 200\n1 3 50\n3 4 100",
        "hidden_inputs": [
            "3 1\n1 2 10",
            "3 3\n1 2 5\n2 3 5\n1 3 8"
        ],
        "ref_code": """import sys
import heapq

def main():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    m = int(input_data[1])
    adj = [[] for _ in range(n + 1)]
    idx = 2
    for _ in range(m):
        u = int(input_data[idx])
        v = int(input_data[idx+1])
        w = int(input_data[idx+2])
        adj[u].append((v, w))
        idx += 3

    dist = [float('inf')] * (n + 1)
    dist[1] = 0
    pq = [(0, 1)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == n:
            break
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))

    print(dist[n] if dist[n] != float('inf') else -1)

if __name__ == '__main__':
    main()""",
        "templates": {
            "python": "import sys\nimport heapq\n\ndef main():\n    # Implement Dijkstra algorithm\n    pass\n\nif __name__ == '__main__':\n    main()\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 7: C++ - Anagram Grouping & Canonical Sorting
    # -------------------------------------------------------------------------
    {
        "id": 7,
        "title": "Anagram Grouping & Canonical Sorting",
        "lang": "cpp",
        "statement": "<p>Given an array of <code>N</code> lowercase strings, group the anagrams together. Sort each group lexicographically, and then sort all groups by the first word in each group. Output each group on a new line separated by spaces.</p>",
        "input_format": "The first line contains N. The next line contains N space-separated strings.",
        "output_format": "Print each group of anagrams on a new line.",
        "constraints": "1 <= N <= 1000\n1 <= length of each word <= 50",
        "sample_input": "6\neat tea tan ate nat bat",
        "hidden_inputs": [
            "1\nsolo",
            "4\na b a b"
        ],
        "ref_code": """#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <map>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int n;
    if (!(cin >> n)) return 0;
    map<string, vector<string>> groups;
    for (int i = 0; i < n; ++i) {
        string s;
        cin >> s;
        string key = s;
        sort(key.begin(), key.end());
        groups[key].push_back(s);
    }
    vector<vector<string>> result;
    for (auto& p : groups) {
        sort(p.second.begin(), p.second.end());
        result.push_back(p.second);
    }
    sort(result.begin(), result.end(), [](const vector<string>& a, const vector<string>& b) {
        return a[0] < b[0];
    });
    for (const auto& group : result) {
        for (size_t i = 0; i < group.size(); ++i) {
            if (i > 0) cout << " ";
            cout << group[i];
        }
        cout << "\\n";
    }
    return 0;
}""",
        "templates": {
            "cpp": "#include <iostream>\n#include <vector>\n#include <string>\n#include <map>\nusing namespace std;\n\nint main() {\n    // Group anagrams\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 8: C - Run-Length Token Encoder
    # -------------------------------------------------------------------------
    {
        "id": 8,
        "title": "Run-Length Token Encoder",
        "lang": "c",
        "statement": "<p>Implement Run-Length Encoding (RLE) on a sequence of uppercase characters. For consecutive runs of identical characters, output the character followed by the count (e.g. <code>AAABBBCC</code> becomes <code>A3B3C2</code>). Single characters should still include count 1 (e.g. <code>A1</code>).</p>",
        "input_format": "A single line containing an uppercase string S.",
        "output_format": "The run-length encoded string.",
        "constraints": "1 <= length of S <= 1000",
        "sample_input": "AABBBCCCCD",
        "hidden_inputs": [
            "Z",
            "ABCDE"
        ],
        "ref_code": """#include <stdio.h>
#include <string.h>

int main() {
    char s[1005];
    if (scanf("%s", s) != 1) return 0;
    int len = strlen(s);
    if (len == 0) return 0;
    int count = 1;
    for (int i = 1; i < len; ++i) {
        if (s[i] == s[i-1]) {
            count++;
        } else {
            printf("%c%d", s[i-1], count);
            count = 1;
        }
    }
    printf("%c%d\\n", s[len-1], count);
    return 0;
}""",
        "templates": {
            "c": "#include <stdio.h>\n#include <string.h>\n\nint main() {\n    // Encode RLE\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 9: JavaScript - Sliding Window Max-Min Ratio
    # -------------------------------------------------------------------------
    {
        "id": 9,
        "title": "Sliding Window Max-Min Difference",
        "lang": "javascript",
        "statement": "<p>Given an array of <code>N</code> positive integers and a window size <code>K</code>, slide the window across the array from left to right. For each window of size <code>K</code>, compute <code>max(window) - min(window)</code> and print the results separated by spaces.</p>",
        "input_format": "First line: N K. Second line: N positive integers.",
        "output_format": "Print N - K + 1 space-separated integers representing the difference for each window.",
        "constraints": "1 <= K <= N <= 1000\n1 <= A[i] <= 10^6",
        "sample_input": "7 3\n10 5 2 7 8 7 12",
        "hidden_inputs": [
            "3 1\n5 10 15",
            "4 4\n1 2 3 4"
        ],
        "ref_code": """let parts = readAllStdin().trim().split(/\\s+/);
if (parts.length >= 2) {
    let n = parseInt(parts[0]);
    let k = parseInt(parts[1]);
    let arr = [];
    for (let i = 0; i < n; i++) arr.push(parseInt(parts[2 + i]));
    
    let res = [];
    for (let i = 0; i <= n - k; i++) {
        let minVal = arr[i];
        let maxVal = arr[i];
        for (let j = 1; j < k; j++) {
            let v = arr[i + j];
            if (v < minVal) minVal = v;
            if (v > maxVal) maxVal = v;
        }
        res.push(maxVal - minVal);
    }
    console.log(res.join(" "));
}""",
        "templates": {
            "javascript": "function main() {\n    // Sliding window calculation\n}\nmain();\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 10: Python - Matrix Spiral Transposition
    # -------------------------------------------------------------------------
    {
        "id": 10,
        "title": "Matrix Spiral Transposition",
        "lang": "python",
        "statement": "<p>Given an <code>R x C</code> matrix of integers, traverse the elements in clockwise spiral order starting from top-left. Output the spiral sequence on a single line separated by spaces.</p>",
        "input_format": "First line: R C. Next R lines: C integers each.",
        "output_format": "A single line containing the spiral traversal elements separated by spaces.",
        "constraints": "1 <= R, C <= 100",
        "sample_input": "3 3\n1 2 3\n4 5 6\n7 8 9",
        "hidden_inputs": [
            "1 4\n10 20 30 40",
            "3 1\n5\n6\n7"
        ],
        "ref_code": """import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    r, c = int(data[0]), int(data[1])
    grid = []
    idx = 2
    for _ in range(r):
        grid.append([int(x) for x in data[idx:idx+c]])
        idx += c

    res = []
    top, bottom, left, right = 0, r - 1, 0, c - 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            res.append(grid[top][j])
        top += 1
        for i in range(top, bottom + 1):
            res.append(grid[i][right])
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                res.append(grid[bottom][j])
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                res.append(grid[i][left])
            left += 1

    print(" ".join(str(x) for x in res))

if __name__ == '__main__':
    main()""",
        "templates": {
            "python": "import sys\n\ndef main():\n    # Spiral matrix\n    pass\n\nif __name__ == '__main__':\n    main()\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 11: C++ - Next Greater Element Circular
    # -------------------------------------------------------------------------
    {
        "id": 11,
        "title": "Next Greater Element Circular",
        "lang": "cpp",
        "statement": "<p>Given a circular integer array <code>A</code> of size <code>N</code>, find the next greater number for every element. If no greater number exists, output <code>-1</code> for that number.</p>",
        "input_format": "First line: N. Second line: N space-separated integers.",
        "output_format": "Print N space-separated integers representing the next greater element for each index.",
        "constraints": "1 <= N <= 10^5\n-10^9 <= A[i] <= 10^9",
        "sample_input": "3\n1 2 1",
        "hidden_inputs": [
            "4\n4 3 2 1",
            "1\n5"
        ],
        "ref_code": """#include <iostream>
#include <vector>
#include <stack>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int n;
    if (!(cin >> n)) return 0;
    vector<int> a(n);
    for (int i = 0; i < n; ++i) cin >> a[i];

    vector<int> ans(n, -1);
    stack<int> st;
    for (int i = 0; i < 2 * n; ++i) {
        int idx = i % n;
        while (!st.empty() && a[st.top()] < a[idx]) {
            ans[st.top()] = a[idx];
            st.pop();
        }
        if (i < n) st.push(idx);
    }
    for (int i = 0; i < n; ++i) {
        if (i > 0) cout << " ";
        cout << ans[i];
    }
    cout << "\\n";
    return 0;
}""",
        "templates": {
            "cpp": "#include <iostream>\n#include <vector>\n#include <stack>\nusing namespace std;\n\nint main() {\n    // Next greater element\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 12: JavaScript - Interval Overlap Condenser
    # -------------------------------------------------------------------------
    {
        "id": 12,
        "title": "Interval Overlap Condenser",
        "lang": "javascript",
        "statement": "<p>Given a collection of <code>N</code> intervals <code>[start, end]</code>, merge all overlapping intervals and return the condensed intervals sorted by start time.</p>",
        "input_format": "The first line contains N. The next N lines contain two integers start end.",
        "output_format": "For each merged interval, print start end on a new line.",
        "constraints": "1 <= N <= 1000\n0 <= start <= end <= 10^6",
        "sample_input": "4\n1 3\n2 6\n8 10\n15 18",
        "hidden_inputs": [
            "2\n1 4\n4 5",
            "1\n5 10"
        ],
        "ref_code": """let lines = readAllStdin().trim().split(/\\r?\\n/);
if (lines.length > 0) {
    let n = parseInt(lines[0]);
    let intervals = [];
    for (let i = 1; i <= n && i < lines.length; i++) {
        let parts = lines[i].trim().split(/\\s+/);
        if (parts.length >= 2) {
            intervals.push([parseInt(parts[0]), parseInt(parts[1])]);
        }
    }
    intervals.sort((a, b) => a[0] - b[0]);
    let merged = [];
    for (let inv of intervals) {
        if (merged.length === 0 || merged[merged.length - 1][1] < inv[0]) {
            merged.push(inv);
        } else {
            merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], inv[1]);
        }
    }
    for (let m of merged) {
        console.log(`${m[0]} ${m[1]}`);
    }
}""",
        "templates": {
            "javascript": "function main() {\n    // Merge overlapping intervals\n}\nmain();\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 13: C - Bitmask Subsets XOR Sum
    # -------------------------------------------------------------------------
    {
        "id": 13,
        "title": "Bitmask Subsets XOR Sum",
        "lang": "c",
        "statement": "<p>Given an array of <code>N</code> integers, find the sum of all XOR totals for every subset of the array. The XOR total of a subset is the bitwise XOR of all its elements (empty subset has XOR total 0).</p>",
        "input_format": "First line: N. Second line: N space-separated integers.",
        "output_format": "Output a single integer, the total sum of subset XOR values.",
        "constraints": "1 <= N <= 12\n0 <= A[i] <= 1000",
        "sample_input": "3\n5 1 6",
        "hidden_inputs": [
            "1\n3",
            "2\n3 4"
        ],
        "ref_code": """#include <stdio.h>

int main() {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int a[20];
    for (int i = 0; i < n; ++i) scanf("%d", &a[i]);

    long long total = 0;
    int subsets = 1 << n;
    for (int mask = 0; mask < subsets; ++mask) {
        int xor_sum = 0;
        for (int i = 0; i < n; ++i) {
            if (mask & (1 << i)) {
                xor_sum ^= a[i];
            }
        }
        total += xor_sum;
    }
    printf("%lld\\n", total);
    return 0;
}""",
        "templates": {
            "c": "#include <stdio.h>\n\nint main() {\n    // Calculate subset XOR sum\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 14: Python - Longest Palindromic Chunk
    # -------------------------------------------------------------------------
    {
        "id": 14,
        "title": "Longest Palindromic Chunk Decomposition",
        "lang": "python",
        "statement": "<p>Given a string <code>S</code>, find the maximum number of chunks <code>K</code> such that <code>S = A[1] + A[2] + ... + A[K]</code> where <code>A[i] == A[K - i + 1]</code> for all valid <code>1 <= i <= K</code>.</p>",
        "input_format": "A single line containing the string S.",
        "output_format": "Output the maximum number of chunks K.",
        "constraints": "1 <= length of S <= 1000",
        "sample_input": "ghiabcdefhelloadamhelloabcghi",
        "hidden_inputs": [
            "merchant",
            "antaprezatepnan"
        ],
        "ref_code": """import sys

def decompose(s):
    n = len(s)
    chunks = 0
    left_str = ""
    right_str = ""
    i = 0
    j = n - 1
    while i < j:
        left_str += s[i]
        right_str = s[j] + right_str
        if left_str == right_str:
            chunks += 2
            left_str = ""
            right_str = ""
        i += 1
        j -= 1
    if i == j or left_str != "":
        chunks += 1
    return chunks

def main():
    line = sys.stdin.read().strip()
    if line:
        print(decompose(line))

if __name__ == '__main__':
    main()""",
        "templates": {
            "python": "import sys\n\ndef main():\n    # Palindromic chunk decomposition\n    pass\n\nif __name__ == '__main__':\n    main()\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 15: C++ - Disjoint Set Island Counter
    # -------------------------------------------------------------------------
    {
        "id": 15,
        "title": "Disjoint Set Island Counter",
        "lang": "cpp",
        "statement": "<p>Given an <code>R x C</code> 2D grid containing <code>'1'</code>s (land) and <code>'0'</code>s (water), count the number of connected islands. An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.</p>",
        "input_format": "First line: R C. Next R lines: string of C characters representing grid rows.",
        "output_format": "Output a single integer, the number of islands.",
        "constraints": "1 <= R, C <= 300",
        "sample_input": "4 5\n11110\n11010\n11000\n00000",
        "hidden_inputs": [
            "4 5\n11000\n11000\n00100\n00011",
            "1 1\n0"
        ],
        "ref_code": """#include <iostream>
#include <vector>
#include <string>
using namespace std;

void dfs(vector<string>& g, int i, int j, int r, int c) {
    if (i < 0 || i >= r || j < 0 || j >= c || g[i][j] != '1') return;
    g[i][j] = '0';
    dfs(g, i + 1, j, r, c);
    dfs(g, i - 1, j, r, c);
    dfs(g, i, j + 1, r, c);
    dfs(g, i, j - 1, r, c);
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int r, c;
    if (!(cin >> r >> c)) return 0;
    vector<string> g(r);
    for (int i = 0; i < r; ++i) cin >> g[i];

    int islands = 0;
    for (int i = 0; i < r; ++i) {
        for (int j = 0; j < c; ++j) {
            if (g[i][j] == '1') {
                islands++;
                dfs(g, i, j, r, c);
            }
        }
    }
    cout << islands << "\\n";
    return 0;
}""",
        "templates": {
            "cpp": "#include <iostream>\n#include <vector>\n#include <string>\nusing namespace std;\n\nint main() {\n    // Count connected components\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 16: C - Subnet Mask & CIDR Classifier
    # -------------------------------------------------------------------------
    {
        "id": 16,
        "title": "Subnet Mask & Network Address",
        "lang": "c",
        "statement": "<p>Given an IPv4 address and a prefix length (CIDR notation, e.g. <code>192.168.1.50/24</code>), compute the Network Address and the Broadcast Address in standard dotted-decimal notation.</p>",
        "input_format": "A single string in the format A.B.C.D/M where 0 <= A,B,C,D <= 255 and 1 <= M <= 32.",
        "output_format": "Print two lines:\nNetwork: A.B.C.D\nBroadcast: A.B.C.D",
        "constraints": "Valid IPv4 address string.",
        "sample_input": "192.168.1.135/26",
        "hidden_inputs": [
            "10.0.0.1/8",
            "172.16.5.10/30"
        ],
        "ref_code": """#include <stdio.h>
#include <stdint.h>

int main() {
    int a, b, c, d, m;
    if (scanf("%d.%d.%d.%d/%d", &a, &b, &c, &d, &m) != 5) return 0;
    uint32_t ip = ((uint32_t)a << 24) | ((uint32_t)b << 16) | ((uint32_t)c << 8) | (uint32_t)d;
    uint32_t mask = (m == 0) ? 0 : (~0U << (32 - m));
    uint32_t net = ip & mask;
    uint32_t bcast = net | ~mask;

    printf("Network: %u.%u.%u.%u\\n", (net >> 24) & 0xFF, (net >> 16) & 0xFF, (net >> 8) & 0xFF, net & 0xFF);
    printf("Broadcast: %u.%u.%u.%u\\n", (bcast >> 24) & 0xFF, (bcast >> 16) & 0xFF, (bcast >> 8) & 0xFF, bcast & 0xFF);
    return 0;
}""",
        "templates": {
            "c": "#include <stdio.h>\n#include <stdint.h>\n\nint main() {\n    // Compute subnet\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 17: JavaScript - Key-Value Dot Path Query
    # -------------------------------------------------------------------------
    {
        "id": 17,
        "title": "Nested Dictionary Key Query",
        "lang": "javascript",
        "statement": "<p>Given a single-line JSON string representing nested objects and a dot-separated query path (e.g. <code>user.address.city</code>), retrieve the value at that path. If any key in the path does not exist, print <code>UNDEFINED</code>.</p>",
        "input_format": "Line 1: A JSON string. Line 2: The query path.",
        "output_format": "Print the retrieved value (as a primitive or JSON string), or UNDEFINED if not found.",
        "constraints": "JSON string <= 5000 chars.",
        "sample_input": "{\"user\":{\"name\":\"Alice\",\"address\":{\"city\":\"Tokyo\",\"zip\":100}}}\nuser.address.city",
        "hidden_inputs": [
            "{\"a\":{\"b\":[10,20]}}\na.b",
            "{\"x\":1}\nx.y.z"
        ],
        "ref_code": """let lines = readAllStdin().trim().split(/\\r?\\n/);
if (lines.length >= 2) {
    let jsonStr = lines[0].trim();
    let path = lines[1].trim().split('.');
    try {
        let obj = JSON.parse(jsonStr);
        let curr = obj;
        let found = true;
        for (let key of path) {
            if (curr !== null && typeof curr === 'object' && curr.hasOwnProperty(key)) {
                curr = curr[key];
            } else {
                found = false;
                break;
            }
        }
        if (found) {
            console.log(typeof curr === 'object' ? JSON.stringify(curr) : String(curr));
        } else {
            console.log("UNDEFINED");
        }
    } catch (e) {
        console.log("UNDEFINED");
    }
}""",
        "templates": {
            "javascript": "function main() {\n    // Parse JSON and resolve dot path\n}\nmain();\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 18: Python - 0/1 Knapsack with Attribute Weights
    # -------------------------------------------------------------------------
    {
        "id": 18,
        "title": "0/1 Knapsack with Attribute Weights",
        "lang": "python",
        "statement": "<p>You have a knapsack of capacity <code>W</code> and <code>N</code> items. Each item has a weight <code>w[i]</code> and value <code>v[i]</code>. Determine the maximum total value of items that can fit inside the knapsack without exceeding capacity <code>W</code>.</p>",
        "input_format": "First line: N W. Next N lines: w[i] v[i].",
        "output_format": "Print a single integer: the maximum achievable value.",
        "constraints": "1 <= N <= 100\n1 <= W <= 1000\n1 <= w[i], v[i] <= 1000",
        "sample_input": "3 50\n10 60\n20 100\n30 120",
        "hidden_inputs": [
            "1 10\n15 100",
            "4 7\n1 1\n3 4\n4 5\n5 7"
        ],
        "ref_code": """import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    cap = int(data[1])
    dp = [0] * (cap + 1)
    idx = 2
    for _ in range(n):
        w = int(data[idx])
        v = int(data[idx+1])
        idx += 2
        for j in range(cap, w - 1, -1):
            if dp[j - w] + v > dp[j]:
                dp[j] = dp[j - w] + v
    print(dp[cap])

if __name__ == '__main__':
    main()""",
        "templates": {
            "python": "import sys\n\ndef main():\n    # 0/1 Knapsack DP\n    pass\n\nif __name__ == '__main__':\n    main()\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 19: C++ - Task Scheduler with Cooldown
    # -------------------------------------------------------------------------
    {
        "id": 19,
        "title": "Task Scheduler with Cooldown",
        "lang": "cpp",
        "statement": "<p>Given an array of CPU tasks represented by uppercase letters (e.g. <code>A B C</code>) and a non-negative integer cooldown <code>N</code>. Between two identical tasks, there must be at least <code>N</code> intervals of cooling. Return the least number of intervals the CPU will take to finish all tasks.</p>",
        "input_format": "First line: string of task characters separated by spaces. Second line: cooldown integer N.",
        "output_format": "Output a single integer representing minimum total intervals.",
        "constraints": "1 <= tasks <= 1000\n0 <= N <= 100",
        "sample_input": "A A A B B B\n2",
        "hidden_inputs": [
            "A A A B B B\n0",
            "A B C D E\n3"
        ],
        "ref_code": """#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <sstream>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    string line;
    if (!getline(cin, line)) return 0;
    int n = 0;
    cin >> n;

    stringstream ss(line);
    char task;
    map<char, int> freq;
    int total = 0;
    while (ss >> task) {
        freq[task]++;
        total++;
    }
    int max_freq = 0;
    for (auto& p : freq) max_freq = max(max_freq, p.second);
    int count_max = 0;
    for (auto& p : freq) if (p.second == max_freq) count_max++;

    int ans = max(total, (max_freq - 1) * (n + 1) + count_max);
    cout << ans << "\\n";
    return 0;
}""",
        "templates": {
            "cpp": "#include <iostream>\n#include <string>\n#include <vector>\nusing namespace std;\n\nint main() {\n    // Task scheduler\n    return 0;\n}\n"
        }
    },

    # -------------------------------------------------------------------------
    # Problem 20: JavaScript - String Arithmetic Calculator
    # -------------------------------------------------------------------------
    {
        "id": 20,
        "title": "String Arithmetic Calculator",
        "lang": "javascript",
        "statement": "<p>Given an arithmetic expression string containing non-negative integers and operators <code>'+'</code>, <code>'-'</code>, <code>'*'</code>, evaluate the expression respecting standard operator precedence (multiplication before addition/subtraction). Division and parentheses are not present. Spaces may appear between tokens.</p>",
        "input_format": "A single line containing the mathematical expression.",
        "output_format": "Output a single integer: the evaluated result.",
        "constraints": "1 <= length of expression <= 10^5",
        "sample_input": "3 + 2 * 2 - 5",
        "hidden_inputs": [
            "10 * 10 * 10",
            "100 - 50 + 25"
        ],
        "ref_code": """let s = readAllStdin().trim().replace(/\\s+/g, '');
let num = 0;
let op = '+';
let stack = [];

for (let i = 0; i < s.length; i++) {
    let c = s[i];
    if (c >= '0' && c <= '9') {
        num = num * 10 + (c.charCodeAt(0) - 48);
    }
    if ((c < '0' || c > '9') || i === s.length - 1) {
        if (op === '+') {
            stack.push(num);
        } else if (op === '-') {
            stack.push(-num);
        } else if (op === '*') {
            stack.push(stack.pop() * num);
        }
        op = c;
        num = 0;
    }
}
let total = stack.reduce((a, b) => a + b, 0);
console.log(total);""",
        "templates": {
            "javascript": "function main() {\n    // Evaluate string arithmetic\n}\nmain();\n"
        }
    }
]

def build_problems():
    PROBLEMS_DIR.mkdir(exist_ok=True)
    # Clean out existing problem JSONs
    for p in PROBLEMS_DIR.glob("*.json"):
        p.unlink()

    print(f"Total problems to process: {len(RAW_PROBLEMS)}")

    # Verify each problem via sandbox_guard and save
    for prob in RAW_PROBLEMS:
        pid = prob["id"]
        lang = prob["lang"]
        ref_code = prob["ref_code"]
        sample_in = prob["sample_input"]

        print(f"[{pid}/20] Verifying '{prob['title']}' ({lang})...", end=" ")
        res = sandbox_guard.execute_sandboxed(lang, ref_code, sample_in + "\n")
        if res["returncode"] != 0:
            print(f"FAILED on sample input!\nStderr:\n{res['stderr']}")
            sys.exit(1)
        
        verified_sample_out = res["stdout"].rstrip()
        
        # Verify hidden testcases
        hidden_tests = []
        for h_in in prob["hidden_inputs"]:
            h_res = sandbox_guard.execute_sandboxed(lang, ref_code, h_in + "\n")
            if h_res["returncode"] != 0:
                print(f"FAILED on hidden input: {h_in}\nStderr:\n{h_res['stderr']}")
                sys.exit(1)
            hidden_tests.append({
                "input": h_in,
                "expected_output": h_res["stdout"].rstrip()
            })
        print("OK")

        final_obj = {
            "id": pid,
            "title": prob["title"],
            "exam_title": "TEST Lab Exam",
            "problem_index": f"{pid} / 20",
            "time_limit": "2s",
            "memory_limit": "256 MB",
            "locked_language": lang,
            "designated_language_name": LANG_MAP[lang],
            "statement": prob["statement"],
            "input_format": prob["input_format"],
            "output_format": prob["output_format"],
            "constraints": prob["constraints"],
            "sample_input": sample_in,
            "sample_output": verified_sample_out,
            "hidden_tests": hidden_tests,
            "templates": prob.get("templates", {
                "cpp": "#include <iostream>\nusing namespace std;\nint main(){\n    return 0;\n}\n",
                "python": "import sys\ndef main():\n    pass\nif __name__ == '__main__':\n    main()\n",
                "javascript": "function main(){\n}\nmain();\n",
                "c": "#include <stdio.h>\nint main(){\n    return 0;\n}\n"
            })
        }

        out_file = PROBLEMS_DIR / f"{pid}.json"
        out_file.write_text(json.dumps(final_obj, indent=2), encoding="utf-8")

    print("\n🎉 ALL 20 EXAM PROBLEMS SELF-VALIDATED AND WRITTEN TO problems/*.json SUCCESSFULLY!")


if __name__ == "__main__":
    build_problems()
