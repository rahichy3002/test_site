// Progsity Exam Simulator, Dynamic AI Problem Generator & Watermark Auditor Client

let editor = null;
let currentProblemId = 1;
let currentProblem = null;
let allProblems = [];
let submissionsCount = 0;
const MAX_SUBMISSIONS = 5;

// Proctoring stats
let tabSwitchCount = 0;
let fullscreenExitCount = 0;
let pasteBlockedCount = 0;
let trustedKeyCount = 0;
let untrustedKeyCount = 0;
let keyTimestamps = [];

document.addEventListener("DOMContentLoaded", () => {
  initCodeMirror();
  bindUIEvents();
  setupProctoringMonitors();
  setupWatermarkSimulator();
  loadProblemsListAndCurrent();
});

function initCodeMirror() {
  const textarea = document.getElementById("codeEditor");
  editor = CodeMirror.fromTextArea(textarea, {
    lineNumbers: true,
    theme: "material-darker",
    mode: "text/x-c++src",
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    lineWrapping: false,
    autoCloseBrackets: true,
    matchBrackets: true,
  });

  editor.setSize("100%", "100%");
}

function bindUIEvents() {
  // Navigation
  document.getElementById("btnPrevProblem").addEventListener("click", () => navigateProblem(-1));
  document.getElementById("btnNextProblem").addEventListener("click", () => navigateProblem(1));
  document.getElementById("btnPrevTop").addEventListener("click", () => navigateProblem(-1));
  document.getElementById("btnNextTop").addEventListener("click", () => navigateProblem(1));

  // Language selector
  document.getElementById("langSelect").addEventListener("change", (e) => {
    updateLanguage(e.target.value);
  });

  // Action buttons
  document.getElementById("btnRunSamples").addEventListener("click", runAgainstSamples);
  document.getElementById("btnSubmit").addEventListener("click", submitForGrading);
  document.getElementById("btnCustomInput").addEventListener("click", toggleCustomInputDrawer);

  // Close drawers
  document.getElementById("btnCloseCustomInput").addEventListener("click", () => {
    document.getElementById("customInputDrawer").style.display = "none";
  });
  document.getElementById("btnCloseResults").addEventListener("click", () => {
    document.getElementById("resultsDrawer").style.display = "none";
  });

  // Audit Console Toggle
  document.getElementById("btnAuditToggle").addEventListener("click", () => {
    const drawer = document.getElementById("auditDrawer");
    drawer.style.display = drawer.style.display === "none" ? "flex" : "none";
  });
  document.getElementById("btnCloseAudit").addEventListener("click", () => {
    document.getElementById("auditDrawer").style.display = "none";
  });

  // Fullscreen toggle checkbox
  document.getElementById("chkEnforceFullscreen").addEventListener("change", (e) => {
    if (e.target.checked) {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      }
    } else {
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      }
    }
  });
}

// --- Problem Loading & Navigation ---
async function loadProblemsListAndCurrent() {
  try {
    const res = await fetch("/api/problems");
    if (res.ok) {
      allProblems = await res.json();
    }
  } catch (e) {}
  loadProblem(currentProblemId);
}

async function loadProblem(id) {
  try {
    const res = await fetch(`/api/problem/${id}`);
    if (!res.ok) return;
    const data = await res.json();
    currentProblem = data;
    currentProblemId = data.id;
    renderProblem(data);
  } catch (err) {
    console.error("Failed to load problem:", err);
  }
}

function renderProblem(data) {
  document.getElementById("examTitle").textContent = data.exam_title || "TEST Lab Exam";
  
  // Calculate index e.g. "X / N"
  const total = allProblems.length || 20;
  const idx = allProblems.findIndex(p => p.id === data.id) + 1;
  document.getElementById("problemIndex").textContent = `${idx > 0 ? idx : data.id} / ${total}`;
  
  document.getElementById("problemStatement").innerHTML = data.statement;
  document.getElementById("inputFormat").textContent = data.input_format;
  document.getElementById("outputFormat").textContent = data.output_format;
  document.getElementById("constraints").textContent = data.constraints;

  // Side-by-side Sample Boxes
  document.getElementById("sampleInputPre").textContent = data.sample_input || "";
  document.getElementById("sampleOutputPre").textContent = data.sample_output || "";

  // Handle Locked Language Mode
  const langSelect = document.getElementById("langSelect");
  const verSelect = document.getElementById("verSelect");
  const lockPill = document.getElementById("langLockPill");

  const langDisplayMap = {
    cpp: "C++",
    python: "Python 3",
    javascript: "JavaScript",
    c: "C",
    java: "Java"
  };

  if (data.locked_language) {
    const locked = data.locked_language.toLowerCase().trim();
    langSelect.value = locked;
    updateLanguage(locked);
    langSelect.disabled = true;
    verSelect.disabled = true;
    langSelect.classList.add("locked-select");
    verSelect.classList.add("locked-select");

    const disp = langDisplayMap[locked] || locked.toUpperCase();
    if (lockPill) {
      lockPill.textContent = `🔒 Locked: ${disp}`;
      lockPill.style.display = "inline-flex";
    }

    document.getElementById("metaLimits").innerHTML = `Time limit: ${data.time_limit} · Memory limit: ${data.memory_limit} &nbsp;|&nbsp; <span style="color:#ff9f43; font-weight:600;">🔒 Required: ${disp}</span>`;
  } else {
    langSelect.disabled = false;
    verSelect.disabled = false;
    langSelect.classList.remove("locked-select");
    verSelect.classList.remove("locked-select");
    if (lockPill) {
      lockPill.style.display = "none";
    }
    document.getElementById("metaLimits").textContent = `Time limit: ${data.time_limit} · Memory limit: ${data.memory_limit}`;
    const currentLang = langSelect.value;
    updateLanguage(currentLang);
  }
}

function navigateProblem(delta) {
  if (!allProblems.length) return;
  const currIdx = allProblems.findIndex(p => p.id === currentProblemId);
  let nextIdx = currIdx + delta;
  if (nextIdx < 0) nextIdx = allProblems.length - 1;
  if (nextIdx >= allProblems.length) nextIdx = 0;
  loadProblem(allProblems[nextIdx].id);
}

function updateLanguage(lang) {
  let mode = "text/x-c++src";
  const verSelect = document.getElementById("verSelect");
  verSelect.innerHTML = "";

  if (lang === "cpp") {
    mode = "text/x-c++src";
    verSelect.innerHTML = `<option value="cpp20" selected>C++20</option><option value="cpp17">C++17</option>`;
  } else if (lang === "c") {
    mode = "text/x-csrc";
    verSelect.innerHTML = `<option value="c17" selected>C17</option>`;
  } else if (lang === "python") {
    mode = "python";
    verSelect.innerHTML = `<option value="py312" selected>Python 3.12</option>`;
  } else if (lang === "javascript") {
    mode = "javascript";
    verSelect.innerHTML = `<option value="node20" selected>Node.js 20</option>`;
  } else if (lang === "java") {
    mode = "text/x-java";
    verSelect.innerHTML = `<option value="java21" selected>Java 21</option>`;
  }

  editor.setOption("mode", mode);

  if (currentProblem && currentProblem.templates && currentProblem.templates[lang]) {
    editor.setValue(currentProblem.templates[lang]);
  }
}

function toggleCustomInputDrawer() {
  const drawer = document.getElementById("customInputDrawer");
  drawer.style.display = drawer.style.display === "none" ? "flex" : "none";
}

// --- Sample Execution & Submit Grading ---
async function runAgainstSamples() {
  const resultsDrawer = document.getElementById("resultsDrawer");
  const resultStatus = document.getElementById("resultStatus");
  const resultContent = document.getElementById("resultContent");

  resultsDrawer.style.display = "flex";
  resultStatus.textContent = "Compiling & Running...";
  resultStatus.className = "result-status-badge";
  resultContent.innerHTML = "<p style='color: #8b909a;'>Executing solution against sample cases...</p>";

  const isCustom = document.getElementById("customInputDrawer").style.display !== "none";
  const customIn = isCustom ? document.getElementById("customInputText").value : null;

  try {
    const payload = {
      problem_id: currentProblemId,
      code: editor.getValue(),
      language: document.getElementById("langSelect").value,
      custom_input: customIn,
    };

    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (data.status === "Security Violation") {
      resultStatus.textContent = `Security Violation [Blocked by Sandbox]`;
      resultStatus.className = "result-status-badge badge-red";
    } else if (data.status === "Compilation Error") {
      resultStatus.textContent = `Compilation Error`;
      resultStatus.className = "result-status-badge badge-red";
    } else if (data.status === "Time Limit Exceeded") {
      resultStatus.textContent = `Time Limit Exceeded (> 2s)`;
      resultStatus.className = "result-status-badge badge-red";
    } else if (data.status === "Passed") {
      resultStatus.textContent = `Passed (${data.elapsed_ms}ms)`;
      resultStatus.className = "result-status-badge badge-green";
    } else if (data.status === "Failed") {
      resultStatus.textContent = `Wrong Answer (${data.elapsed_ms}ms)`;
      resultStatus.className = "result-status-badge badge-red";
    } else {
      resultStatus.textContent = data.status || "Finished";
      resultStatus.className = "result-status-badge";
    }

    let html = `<div style="margin-bottom: 8px;"><strong>Output:</strong></div>`;
    html += `<pre style="background:#111215; padding:8px; border-radius:4px; margin-bottom:12px;">${escapeHtml(data.stdout || "(no output)")}</pre>`;

    if (data.expected && (data.status === "Failed" || data.status === "Wrong Answer")) {
      html += `<div style="margin-bottom: 8px; color:#ff8566;"><strong>Expected:</strong></div>`;
      html += `<pre style="background:#111215; padding:8px; border-radius:4px; margin-bottom:12px;">${escapeHtml(data.expected)}</pre>`;
    }

    if (data.stderr) {
      const isSec = data.status === "Security Violation";
      html += `<div style="margin-bottom: 8px; color:${isSec ? '#ff4d4d' : '#e74c3c'};"><strong>${isSec ? '🛡️ Sandbox Security Violation:' : 'Stderr / Messages:'}</strong></div>`;
      html += `<pre style="background:${isSec ? '#330000' : '#2a1818'}; color:${isSec ? '#ff9999' : '#ff9999'}; padding:8px; border-radius:4px; border: 1px solid ${isSec ? '#ff3333' : '#552222'};">${escapeHtml(data.stderr)}</pre>`;
    }

    resultContent.innerHTML = html;

  } catch (err) {
    resultStatus.textContent = "Error";
    resultStatus.className = "result-status-badge badge-red";
    resultContent.textContent = String(err);
  }
}

async function submitForGrading() {
  if (submissionsCount >= MAX_SUBMISSIONS) {
    showToast("Submission limit reached (5/5 used)!");
    return;
  }

  submissionsCount++;
  const left = MAX_SUBMISSIONS - submissionsCount;
  document.getElementById("subCount").textContent = `${submissionsCount} of ${MAX_SUBMISSIONS} submissions used`;
  document.getElementById("btnSubmitText").textContent = `Submit for grading (${left} left)`;

  const resultsDrawer = document.getElementById("resultsDrawer");
  const resultStatus = document.getElementById("resultStatus");
  const resultContent = document.getElementById("resultContent");

  resultsDrawer.style.display = "flex";
  resultStatus.textContent = "Grading Submissions...";
  resultStatus.className = "result-status-badge";

  try {
    const payload = {
      problem_id: currentProblemId,
      code: editor.getValue(),
      language: document.getElementById("langSelect").value,
    };

    const res = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (data.verdict === "Accepted") {
      resultStatus.textContent = `Accepted (Passed ${data.passed_count}/${data.total_count} tests in ${data.total_time_ms}ms)`;
      resultStatus.className = "result-status-badge badge-green";
    } else {
      resultStatus.textContent = `${data.verdict} (${data.passed_count}/${data.total_count} tests passed)`;
      resultStatus.className = "result-status-badge badge-red";
    }

    let html = `<div style="margin-bottom: 12px; font-size:13px;">Verdict: <strong>${data.verdict}</strong> (${data.total_time_ms}ms total)</div>`;
    html += `<div style="display:flex; flex-direction:column; gap:6px;">`;

    for (const t of data.test_results || []) {
      const isAc = t.verdict === "Accepted";
      html += `<div class="test-row" style="display:flex; justify-content:space-between; align-items:center;">
        <span>Testcase #${t.test}</span>
        <span class="${isAc ? 'badge-green' : 'badge-red'}" style="padding:2px 8px; border-radius:3px; font-size:11px;">${t.verdict} (${t.elapsed_ms}ms)</span>
      </div>`;
    }
    html += `</div>`;
    resultContent.innerHTML = html;

  } catch (err) {
    resultStatus.textContent = "Error";
    resultStatus.className = "result-status-badge badge-red";
    resultContent.textContent = String(err);
  }
}

// --- Progsity Watermark Simulator Engine ---
function setupWatermarkSimulator() {
  const chk = document.getElementById("chkWatermark");
  const rngIntensity = document.getElementById("rngWatermarkIntensity");
  const rngDensity = document.getElementById("rngWatermarkDensity");
  const rngAngle = document.getElementById("rngWatermarkAngle");
  const txtWatermark = document.getElementById("txtWatermark");

  const update = () => {
    const enabled = chk.checked;
    const intensity = parseInt(rngIntensity.value, 10);
    const density = parseInt(rngDensity.value, 10);
    const angle = parseInt(rngAngle.value, 10);
    const text = txtWatermark.value.trim() || "EXAM WATERMARK";

    document.getElementById("valWatermarkIntensity").textContent = `${intensity}%`;
    document.getElementById("valWatermarkDensity").textContent = `${density}px`;
    document.getElementById("valWatermarkAngle").textContent = `${angle}°`;

    renderWatermarkOverlay(enabled, text, intensity, density, angle);
  };

  chk.addEventListener("change", update);
  rngIntensity.addEventListener("input", update);
  rngDensity.addEventListener("input", update);
  rngAngle.addEventListener("input", update);
  txtWatermark.addEventListener("input", update);

  update();
}

function renderWatermarkOverlay(enabled, text, intensityPercent, spacingPx, angleDeg) {
  const overlay = document.getElementById("watermarkOverlay");
  if (!enabled) {
    overlay.style.backgroundImage = "none";
    return;
  }

  const opacity = (intensityPercent / 100).toFixed(3);
  const w = spacingPx * 2.2;
  const h = spacingPx * 1.2;

  // Build repeating SVG background pattern
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
    <style>
      text {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.8px;
        fill: rgba(255, 255, 255, ${opacity});
        user-select: none;
      }
    </style>
    <g transform="rotate(${angleDeg} ${w/2} ${h/2})">
      <text x="${w/2}" y="${h/2}" text-anchor="middle" dominant-baseline="middle">${escapeXml(text)}</text>
    </g>
  </svg>`;

  const b64 = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svg)));
  overlay.style.backgroundImage = `url("${b64}")`;
  overlay.style.backgroundRepeat = "repeat";
}



// --- Proctoring & Stealth Security Event Monitoring ---
function setupProctoringMonitors() {
  document.addEventListener("fullscreenchange", () => {
    const isEnforce = document.getElementById("chkEnforceFullscreen").checked;
    if (isEnforce && !document.fullscreenElement) {
      fullscreenExitCount++;
      document.getElementById("statFullscreenExits").textContent = fullscreenExitCount;
      showToast("⚠️ VIOLATION: Fullscreen exited! This breach is logged.");
      logAuditEvent("Fullscreen exited");
    }
  });

  document.addEventListener("visibilitychange", () => {
    const trackTab = document.getElementById("chkTrackTabSwitch").checked;
    if (trackTab && document.visibilityState === "hidden") {
      tabSwitchCount++;
      document.getElementById("statTabSwitches").textContent = tabSwitchCount;
      showToast("⚠️ VIOLATION: Tab switch detected!");
      logAuditEvent(`Tab hidden (State: ${document.visibilityState})`);
    }
  });

  window.addEventListener("blur", () => {
    const trackTab = document.getElementById("chkTrackTabSwitch").checked;
    if (trackTab) {
      tabSwitchCount++;
      document.getElementById("statTabSwitches").textContent = tabSwitchCount;
      logAuditEvent("Window lost focus (blur)");
    }
  });

  document.addEventListener("paste", (e) => {
    const blockPaste = document.getElementById("chkBlockPaste").checked;
    if (blockPaste) {
      e.preventDefault();
      pasteBlockedCount++;
      document.getElementById("statPasteBlocked").textContent = pasteBlockedCount;
      showToast("🚫 BLOCKED: Clipboard paste is disabled in exam mode!");
      logAuditEvent("Paste event intercepted & blocked");
    }
  });

  document.addEventListener("copy", (e) => {
    const blockPaste = document.getElementById("chkBlockPaste").checked;
    if (blockPaste) {
      showToast("Notice: Copy event intercepted.");
      logAuditEvent("Copy event detected");
    }
  });

  document.addEventListener("contextmenu", (e) => {
    const blockRightClick = document.getElementById("chkBlockRightClick").checked;
    if (blockRightClick) {
      e.preventDefault();
      showToast("Notice: Right-click context menu is disabled.");
      logAuditEvent("Right-click blocked");
    }
  });

  window.addEventListener("keydown", (e) => {
    const now = performance.now();
    keyTimestamps.push(now);
    if (keyTimestamps.length > 20) keyTimestamps.shift();

    if (e.isTrusted) {
      trustedKeyCount++;
      document.getElementById("statTrustedKeys").textContent = trustedKeyCount;
    } else {
      untrustedKeyCount++;
      document.getElementById("statUntrustedKeys").textContent = untrustedKeyCount;
    }

    if (keyTimestamps.length > 1) {
      const deltas = [];
      for (let i = 1; i < keyTimestamps.length; i++) {
        deltas.push(keyTimestamps[i] - keyTimestamps[i - 1]);
      }
      const avgInterval = Math.round(deltas.reduce((a, b) => a + b, 0) / deltas.length);
      document.getElementById("statKeyInterval").textContent = avgInterval;

      const totalSpanSec = (keyTimestamps[keyTimestamps.length - 1] - keyTimestamps[0]) / 1000;
      if (totalSpanSec > 0.5) {
        const wpm = Math.round(((keyTimestamps.length / 5) / (totalSpanSec / 60)));
        document.getElementById("statWpm").textContent = wpm;
      }
    }

    if (trustedKeyCount % 20 === 0) {
      logAuditEvent(`Key: '${e.key}' | trusted=${e.isTrusted}`);
    }
  }, true);
}

function showToast(message) {
  const toast = document.getElementById("violationToast");
  toast.textContent = message;
  toast.style.display = "block";
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.display = "none";
  }, 3500);
}

function logAuditEvent(msg) {
  const logBox = document.getElementById("auditEventLog");
  const timeStr = new Date().toTimeString().split(" ")[0];
  const line = document.createElement("div");
  line.textContent = `[${timeStr}] ${msg}`;
  logBox.prepend(line);
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeXml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}
