"""Nexus Dashboard: Pure Observability & Agent Squad Visualizer for External Orchestrators."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response, StreamingResponse

from nexus import __version__
from nexus.api import SecurityHeadersConfig, create_nexus_app
from nexus.dashboard.telemetry import event_bus

DASHBOARD_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)

DASHBOARD_SECURITY_HEADERS = SecurityHeadersConfig(
    content_security_policy=DASHBOARD_CSP,
    no_store_prefixes=("/api/",),
)


def create_dashboard_app(cors_origins: list[str] | None = None) -> FastAPI:
    """Build the FastAPI localhost observability visualizer.

    The bundled UI is served offline from the same origin with strict security headers
    (no external CDN, no inline scripts), so CORS stays closed by default.
    Pass ``cors_origins`` only if a separate front end must read the telemetry API.
    """
    app = create_nexus_app(
        title="Nexus Telemetry Visualizer",
        description="Real-time Observability & Progress Visualizer for External AI Orchestrators",
        version=__version__,
        cors_origins=cors_origins,
        security_headers=DASHBOARD_SECURITY_HEADERS,
        docs=False,
        ready_path=None,
    )

    @app.get("/api/status")
    async def get_status() -> dict[str, Any]:
        return {
            "status": "listening",
            "framework_version": __version__,
            "history_count": len(event_bus.get_history(1000)),
        }

    @app.get("/api/events")
    async def get_events(limit: int = 100) -> list[dict[str, Any]]:
        return event_bus.get_history(limit)

    @app.get("/api/stream")
    async def stream_events() -> StreamingResponse:
        """Server-Sent Events (SSE) live progress stream."""
        return StreamingResponse(
            event_bus.subscribe(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/dashboard.css", include_in_schema=False)
    async def serve_css() -> Response:
        return Response(
            DASHBOARD_CSS,
            media_type="text/css; charset=utf-8",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/dashboard.js", include_in_schema=False)
    async def serve_js() -> Response:
        return Response(
            DASHBOARD_JS,
            media_type="text/javascript; charset=utf-8",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/", response_class=HTMLResponse)
    async def serve_dashboard() -> HTMLResponse:
        """Serve the pure observability HUD."""
        return HTMLResponse(DASHBOARD_HTML, headers={"Cache-Control": "no-cache"})

    return app


DASHBOARD_CSS = """\
:root {
  --nx-bg: #020617;
  --nx-surface: #0f172a;
  --nx-surface-soft: rgba(15, 23, 42, 0.55);
  --nx-surface-deep: rgba(2, 6, 23, 0.72);
  --nx-border: #1e293b;
  --nx-border-strong: #334155;
  --nx-ink: #f1f5f9;
  --nx-ink-muted: #94a3b8;
  --nx-ink-faint: #64748b;
  --nx-indigo: #818cf8;
  --nx-indigo-bg: rgba(99, 102, 241, 0.16);
  --nx-indigo-border: #6366f1;
  --nx-sky: #38bdf8;
  --nx-cyan: #22d3ee;
  --nx-teal: #2dd4bf;
  --nx-emerald: #34d399;
  --nx-emerald-bg: rgba(16, 185, 129, 0.15);
  --nx-emerald-border: rgba(16, 185, 129, 0.45);
  --nx-purple: #c084fc;
  --nx-amber: #fbbf24;
  --nx-rose: #fb7185;
  --nx-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --nx-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  background: var(--nx-bg);
  color: var(--nx-ink);
  font-family: var(--nx-sans);
  line-height: 1.45;
  -webkit-font-smoothing: antialiased;
}

@keyframes pulse-fast {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.03); }
}

.pulsing { animation: pulse-fast 1.5s infinite; }

.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid var(--nx-border);
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
}

.brand { display: flex; align-items: center; gap: 0.75rem; }

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: #4f46e5;
  color: #ffffff;
  font-weight: 700;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.28);
}

.brand-title {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.brand-sub { margin: 0.1rem 0 0; font-size: 0.75rem; color: var(--nx-ink-muted); }
.brand-sub strong { color: #e2e8f0; font-weight: 500; }

.hud-badge {
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  background: var(--nx-indigo-bg);
  color: var(--nx-indigo);
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.metrics-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; font-size: 0.75rem; }

.metric-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.75rem;
  border-radius: 0.4rem;
  background: var(--nx-surface);
  border: 1px solid var(--nx-border);
  color: var(--nx-ink-muted);
}

.metric-value { font-family: var(--nx-mono); color: #e2e8f0; }
.metric-spend { font-family: var(--nx-mono); font-weight: 700; color: var(--nx-emerald); }

.dot { display: inline-block; width: 0.5rem; height: 0.5rem; border-radius: 9999px; flex-shrink: 0; }
.dot-lg { width: 0.75rem; height: 0.75rem; }
.dot-ok { background: var(--nx-emerald); }
.dot-err { background: var(--nx-rose); }
.dot-accent { background: var(--nx-indigo-border); }

.container {
  max-width: 80rem;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.panel {
  border-radius: 0.75rem;
  border: 1px solid var(--nx-border);
  background: var(--nx-surface-soft);
  padding: 1.15rem 1.25rem;
}

.banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.banner-left { display: flex; align-items: center; gap: 0.75rem; }

.kicker {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--nx-ink-muted);
}

.task-text { margin: 0.15rem 0 0; font-size: 0.875rem; font-weight: 500; color: #e2e8f0; font-style: italic; }

.status-pill {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: var(--nx-border);
  color: var(--nx-ink-muted);
}

.status-pill.in-progress { background: var(--nx-indigo-bg); color: #c7d2fe; font-weight: 600; }
.status-pill.complete { background: var(--nx-emerald-bg); color: var(--nx-emerald); font-weight: 600; }

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.panel-header-ruled { padding-bottom: 0.7rem; border-bottom: 1px solid var(--nx-border); }

.panel-title {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--nx-ink-muted);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mono-label { font-family: var(--nx-mono); font-size: 0.75rem; color: var(--nx-indigo); }
.mono-muted { font-family: var(--nx-mono); font-size: 0.75rem; color: var(--nx-ink-muted); }

.squad-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.625rem;
}

@media (min-width: 768px) { .squad-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@media (min-width: 1024px) { .squad-grid { grid-template-columns: repeat(7, minmax(0, 1fr)); } }

.stage-card {
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid var(--nx-border);
  background: var(--nx-surface-deep);
  transition: border-color 160ms ease, background 160ms ease;
}

.stage-card.active {
  border-color: var(--nx-indigo-border);
  background: rgba(49, 46, 129, 0.28);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.14);
}

.stage-card.done {
  border-color: var(--nx-emerald-border);
  background: rgba(6, 78, 59, 0.18);
}

.stage-head { display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; margin-bottom: 0.25rem; }
.stage-desc { margin: 0; font-size: 0.6875rem; color: var(--nx-ink-muted); }

.stage-badge {
  font-size: 0.6rem;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
  background: var(--nx-border);
  color: var(--nx-ink-muted);
}

.stage-badge.active { background: var(--nx-indigo-bg); color: var(--nx-indigo); font-weight: 700; }
.stage-badge.done { background: var(--nx-emerald-bg); color: var(--nx-emerald); font-weight: 700; }

.c-ba { font-weight: 700; color: var(--nx-indigo); }
.c-solution { font-weight: 700; color: var(--nx-sky); }
.c-data { font-weight: 700; color: var(--nx-cyan); }
.c-ui { font-weight: 700; color: var(--nx-teal); }
.c-fullstack { font-weight: 700; color: var(--nx-emerald); }
.c-devops { font-weight: 700; color: var(--nx-purple); }
.c-qa { font-weight: 700; color: var(--nx-amber); }
.c-system { font-weight: 600; color: var(--nx-ink-muted); }

.split-grid { display: grid; grid-template-columns: 1fr; gap: 1.25rem; }
@media (min-width: 1024px) { .split-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }

.feed-panel { display: flex; flex-direction: column; height: 500px; }

.feed-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 0.35rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.log-scroll { font-family: var(--nx-mono); font-size: 0.75rem; color: #cbd5e1; }

.log-row { border-left: 2px solid var(--nx-border); padding: 0.15rem 0 0.15rem 0.6rem; word-break: break-word; }
.log-row.ev-agent_started { border-left-color: var(--nx-indigo-border); }
.log-row.ev-tool_call { border-left-color: var(--nx-amber); }
.log-row.ev-artifact_generated { border-left-color: var(--nx-emerald); }
.log-row.ev-guardrail_triggered { border-left-color: var(--nx-rose); }

.log-time { color: var(--nx-ink-faint); margin-right: 0.35rem; }

.empty-note { text-align: center; padding: 4.5rem 1rem; color: var(--nx-ink-faint); font-size: 0.75rem; }

.artifact-card {
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid var(--nx-border);
  background: var(--nx-surface-deep);
  font-size: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.artifact-card:hover { border-color: var(--nx-border-strong); }

.artifact-head { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; font-weight: 600; color: #e2e8f0; }

.artifact-agent {
  font-size: 0.625rem;
  padding: 0.15rem 0.5rem;
  border-radius: 0.25rem;
  background: var(--nx-border);
  color: var(--nx-ink-muted);
  white-space: nowrap;
}

.artifact-snippet {
  margin: 0;
  font-family: var(--nx-mono);
  font-size: 0.6875rem;
  color: var(--nx-ink-muted);
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid var(--nx-border);
  border-radius: 0.35rem;
  padding: 0.5rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 5rem;
  overflow: hidden;
}

.clear-btn {
  background: transparent;
  border: 1px solid var(--nx-border);
  border-radius: 0.35rem;
  padding: 0.2rem 0.55rem;
  color: var(--nx-ink-muted);
  font-size: 0.75rem;
  cursor: pointer;
}

.clear-btn:hover { color: var(--nx-ink); border-color: var(--nx-border-strong); }
"""


DASHBOARD_JS = """\
(function () {
  "use strict";

  var accumulatedSpend = 0.0;
  var accumulatedTokens = 0;
  var artifactCounter = 0;

  var logContainer = document.getElementById("log-container");
  var artifactContainer = document.getElementById("artifact-container");
  var currentTask = document.getElementById("current-task");
  var squadStatusPill = document.getElementById("squad-status-pill");
  var activeAgentLabel = document.getElementById("active-agent-label");
  var totalSpend = document.getElementById("total-spend");
  var totalTokens = document.getElementById("total-tokens");
  var artifactCount = document.getElementById("artifact-count");
  var connDot = document.getElementById("conn-dot");
  var connText = document.getElementById("conn-text");
  var clearBtn = document.getElementById("clear-logs-btn");

  function agentColorClass(agent) {
    var a = (agent || "").toLowerCase();
    if (a.indexOf("analyst") !== -1 || a === "ba") return "c-ba";
    if (a.indexOf("solution") !== -1) return "c-solution";
    if (a.indexOf("data") !== -1) return "c-data";
    if (a.indexOf("designer") !== -1 || a.indexOf("ui") !== -1) return "c-ui";
    if (a.indexOf("fullstack") !== -1 || a.indexOf("full-stack") !== -1 || a.indexOf("engineer") !== -1) {
      return "c-fullstack";
    }
    if (a.indexOf("devops") !== -1) return "c-devops";
    if (a.indexOf("qa") !== -1) return "c-qa";
    return "c-system";
  }

  function stageKey(agent) {
    var name = (agent || "").toLowerCase();
    if (name.indexOf("analyst") !== -1 || name.indexOf("ba") !== -1) return "ba";
    if (name.indexOf("solution") !== -1) return "solution_architect";
    if (name.indexOf("data") !== -1) return "data_architect";
    if (name.indexOf("designer") !== -1 || name.indexOf("ui") !== -1) return "ui_designer";
    if (name.indexOf("fullstack") !== -1 || name.indexOf("full-stack") !== -1 || name.indexOf("engineer") !== -1) {
      return "fullstack";
    }
    if (name.indexOf("devops") !== -1) return "devops";
    if (name.indexOf("qa") !== -1) return "qa";
    return "";
  }

  function updateSquadCard(event) {
    var key = stageKey(event.agent_name);
    if (!key) return;
    var card = document.getElementById("card-" + key);
    var badge = document.getElementById("status-" + key);
    if (!card || !badge) return;

    if (event.event_type === "agent_started") {
      card.className = "stage-card active";
      badge.className = "stage-badge active pulsing";
      badge.textContent = "Active";
      if (activeAgentLabel) activeAgentLabel.textContent = (event.agent_name || "Agent") + " running...";
    } else if (event.event_type === "step_completed") {
      card.className = "stage-card done";
      badge.className = "stage-badge done";
      badge.textContent = "Done";
    }
  }

  function addArtifactCard(event) {
    if (!artifactContainer) return;
    if (artifactCounter === 1) {
      artifactContainer.textContent = "";
    }

    var card = document.createElement("div");
    card.className = "artifact-card";

    var head = document.createElement("div");
    head.className = "artifact-head";

    var title = document.createElement("span");
    title.textContent = String(event.message || "Artifact");

    var agent = document.createElement("span");
    agent.className = "artifact-agent";
    agent.textContent = String(event.agent_name || "System");

    head.appendChild(title);
    head.appendChild(agent);

    var snippet = document.createElement("p");
    snippet.className = "artifact-snippet";
    snippet.textContent =
      event.data && event.data.snippet
        ? String(event.data.snippet)
        : "Artifact compiled and verified.";

    card.appendChild(head);
    card.appendChild(snippet);
    artifactContainer.appendChild(card);
  }

  function appendLog(event) {
    if (!logContainer) return;

    var row = document.createElement("div");
    var knownTypes = {
      agent_started: "ev-agent_started",
      tool_call: "ev-tool_call",
      artifact_generated: "ev-artifact_generated",
      guardrail_triggered: "ev-guardrail_triggered"
    };
    row.className = "log-row " + (knownTypes[event.event_type] || "");

    var timeSpan = document.createElement("span");
    timeSpan.className = "log-time";
    var timeStr = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : "";
    timeSpan.textContent = "[" + timeStr + "]";

    var agentSpan = document.createElement("span");
    agentSpan.className = agentColorClass(event.agent_name);
    agentSpan.textContent = (event.agent_name || "System") + ": ";

    var msgSpan = document.createElement("span");
    msgSpan.textContent = String(event.message || "");

    row.appendChild(timeSpan);
    row.appendChild(agentSpan);
    row.appendChild(msgSpan);
    logContainer.appendChild(row);
    logContainer.scrollTop = logContainer.scrollHeight;

    var msg = String(event.message || "");
    if (event.event_type === "agent_started" && msg.indexOf("Analyzing requirements") !== -1) {
      if (currentTask) {
        currentTask.textContent = msg.replace("Analyzing requirements for: ", "").replace("...", "");
      }
      if (squadStatusPill) {
        squadStatusPill.textContent = "Squad In Progress";
        squadStatusPill.className = "status-pill in-progress";
      }
    }

    updateSquadCard(event);

    if (event.data && event.data.cost_usd) {
      var parsedCost = parseFloat(event.data.cost_usd);
      if (!isNaN(parsedCost)) {
        accumulatedSpend += parsedCost;
        if (totalSpend) totalSpend.textContent = "$" + accumulatedSpend.toFixed(6);
      }
    }
    if (event.data && event.data.tokens) {
      var parsedTokens = parseInt(event.data.tokens, 10);
      if (!isNaN(parsedTokens)) {
        accumulatedTokens += parsedTokens;
        if (totalTokens) totalTokens.textContent = accumulatedTokens.toLocaleString();
      }
    }

    if (event.event_type === "artifact_generated") {
      artifactCounter += 1;
      if (artifactCount) artifactCount.textContent = artifactCounter + " artifacts";
      addArtifactCard(event);
    }

    if (event.event_type === "run_completed" && squadStatusPill) {
      squadStatusPill.textContent = "Delivery Complete";
      squadStatusPill.className = "status-pill complete";
    }
  }

  if (clearBtn && logContainer) {
    clearBtn.addEventListener("click", function () {
      logContainer.textContent = "";
    });
  }

  var evtSource = new EventSource("/api/stream");
  evtSource.onopen = function () {
    if (connDot) connDot.className = "dot dot-ok";
    if (connText) connText.textContent = "Listening on Localhost";
  };
  evtSource.onmessage = function (e) {
    try {
      appendLog(JSON.parse(e.data));
    } catch (_err) {
      // ignore malformed frames
    }
  };
  evtSource.onerror = function () {
    if (connDot) connDot.className = "dot dot-err";
    if (connText) connText.textContent = "Stream Disconnected";
  };
})();
"""


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nexus Agent Squad Visualizer</title>
  <link rel="stylesheet" href="/dashboard.css">
</head>
<body>
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">N</div>
      <div>
        <h1 class="brand-title">
          Nexus Squad Visualizer
          <span class="hud-badge">Telemetry HUD</span>
        </h1>
        <p class="brand-sub">Observing Orchestrator: <strong>Claude Code / Cursor / Codex / Gemini</strong></p>
      </div>
    </div>
    <div class="metrics-bar">
      <div class="metric-chip">
        <span id="conn-dot" class="dot dot-ok"></span>
        <span id="conn-text">Listening on Localhost</span>
      </div>
      <div class="metric-chip">
        <span>Tokens:</span>
        <span id="total-tokens" class="metric-value">0</span>
      </div>
      <div class="metric-chip">
        <span>Spend:</span>
        <span id="total-spend" class="metric-spend">$0.000000</span>
      </div>
    </div>
  </header>

  <main class="container">
    <section class="panel banner">
      <div class="banner-left">
        <span class="dot dot-lg dot-accent pulsing"></span>
        <div>
          <span class="kicker">Current Task Under Orchestration</span>
          <p id="current-task" class="task-text">Awaiting task delegation from orchestrator...</p>
        </div>
      </div>
      <div id="squad-status-pill" class="status-pill">Squad Standby</div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">Squad Execution Topology</h2>
        <span id="active-agent-label" class="mono-label">Ready</span>
      </div>
      <div class="squad-grid">
        <div id="card-ba" class="stage-card">
          <div class="stage-head">
            <span class="c-ba">1. BA</span>
            <span id="status-ba" class="stage-badge">Idle</span>
          </div>
          <p class="stage-desc">User Stories &amp; Scope</p>
        </div>
        <div id="card-solution_architect" class="stage-card">
          <div class="stage-head">
            <span class="c-solution">2. Solution Arch</span>
            <span id="status-solution_architect" class="stage-badge">Idle</span>
          </div>
          <p class="stage-desc">System Topology &amp; Cloud</p>
        </div>
        <div id="card-data_architect" class="stage-card">
          <div class="stage-head">
            <span class="c-data">3. Data Arch</span>
            <span id="status-data_architect" class="stage-badge">Idle</span>
          </div>
          <p class="stage-desc">ERD &amp; SQL Schema</p>
        </div>
        <div id="card-ui_designer" class="stage-card">
          <div class="stage-head">
            <span class="c-ui">4. UI/UX</span>
            <span id="status-ui_designer" class="stage-badge">Idle</span>
          </div>
          <p class="stage-desc">Tokens &amp; Wireframe</p>
        </div>
        <div id="card-fullstack" class="stage-card">
          <div class="stage-head">
            <span class="c-fullstack">5. Full-Stack</span>
            <span id="status-fullstack" class="stage-badge">Idle</span>
          </div>
          <p class="stage-desc">React + FastAPI Code</p>
        </div>
        <div id="card-devops" class="stage-card">
          <div class="stage-head">
            <span class="c-devops">6. DevOps</span>
            <span id="status-devops" class="stage-badge">Idle</span>
          </div>
          <p class="stage-desc">Terraform IaC &amp; Deploy</p>
        </div>
        <div id="card-qa" class="stage-card">
          <div class="stage-head">
            <span class="c-qa">7. QA &amp; Sec</span>
            <span id="status-qa" class="stage-badge">Idle</span>
          </div>
          <p class="stage-desc">Preflight &amp; Tests</p>
        </div>
      </div>
    </section>

    <div class="split-grid">
      <section class="panel feed-panel">
        <div class="panel-header panel-header-ruled">
          <h2 class="panel-title">
            <span class="dot dot-ok pulsing"></span>
            Real-Time Orchestrator Stream
          </h2>
          <button id="clear-logs-btn" type="button" class="clear-btn">Clear</button>
        </div>
        <div id="log-container" class="feed-scroll log-scroll">
          <div class="log-row">[System] Visualizer HUD connected. Listening to orchestrator events...</div>
        </div>
      </section>

      <section class="panel feed-panel">
        <div class="panel-header panel-header-ruled">
          <h2 class="panel-title">Artifacts &amp; Code Output</h2>
          <span id="artifact-count" class="mono-muted">0 artifacts</span>
        </div>
        <div id="artifact-container" class="feed-scroll">
          <div class="empty-note">Awaiting artifacts from the active orchestrator workflow...</div>
        </div>
      </section>
    </div>
  </main>

  <script src="/dashboard.js" defer></script>
</body>
</html>
"""
