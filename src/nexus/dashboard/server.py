"""Nexus Dashboard: Pure Observability & Agent Squad Visualizer for External Orchestrators."""
from __future__ import annotations

import asyncio
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from nexus import __version__
from nexus.dashboard.telemetry import AgentEvent, EventType, event_bus


def create_dashboard_app() -> FastAPI:
    """Build the FastAPI localhost observability visualizer."""
    app = FastAPI(
        title="Nexus Telemetry Visualizer",
        description="Real-time Observability & Progress Visualizer for External AI Orchestrators",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
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

    @app.get("/", response_class=HTMLResponse)
    async def serve_dashboard() -> str:
        """Serve the pure observability HUD."""
        return DASHBOARD_HTML

    return app


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nexus Agent Squad Visualizer</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#eef2ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' }
          }
        }
      }
    }
  </script>
  <style>
    @keyframes pulse-fast {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(1.03); }
    }
    .pulsing { animation: pulse-fast 1.5s infinite; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased selection:bg-indigo-500/30">
  <!-- Top Navigation & Live Telemetry Bar -->
  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
        N
      </div>
      <div>
        <h1 class="text-sm font-semibold tracking-wide text-slate-100 flex items-center gap-2">
          Nexus Squad Visualizer
          <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Telemetry HUD</span>
        </h1>
        <p class="text-xs text-slate-400">Observing Orchestrator: <span class="text-slate-200 font-medium">Claude Code / Cursor / Codex / Gemini</span></p>
      </div>
    </div>
    <div class="flex items-center gap-3 text-xs">
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
        <span id="conn-dot" class="h-2 w-2 rounded-full bg-emerald-400"></span>
        <span id="conn-text" class="text-slate-300 font-medium">Listening on Localhost</span>
      </div>
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
        <span class="text-slate-400">Tokens:</span>
        <span id="total-tokens" class="font-mono text-slate-200">0</span>
      </div>
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
        <span class="text-slate-400">Spend:</span>
        <span id="total-spend" class="font-bold text-emerald-400 font-mono">$0.000000</span>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto p-6 space-y-6">
    <!-- Active Session Banner -->
    <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-4.5 backdrop-blur flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="h-3 w-3 rounded-full bg-indigo-500 pulsing"></span>
        <div>
          <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Current Task Under Orchestration</span>
          <p id="current-task" class="text-sm text-slate-200 font-medium mt-0.5 italic">Awaiting task delegation from orchestrator...</p>
        </div>
      </div>
      <div id="squad-status-pill" class="text-xs px-3 py-1 rounded-full bg-slate-800 text-slate-400 font-medium">
        Squad Standby
      </div>
    </section>

    <!-- 7-Stage Specialist IT Squad Topology -->
    <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
      <div class="flex items-center justify-between mb-3.5">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Squad Execution Topology</h2>
        <span id="active-agent-label" class="text-xs font-mono text-indigo-400">Ready</span>
      </div>
      
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2.5">
        <!-- 1. BA -->
        <div id="card-ba" class="p-3 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-indigo-400">1. BA</span>
            <span id="status-ba" class="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-[11px] text-slate-400">User Stories & Scope</p>
        </div>

        <!-- 2. Solution Architect -->
        <div id="card-solution_architect" class="p-3 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-sky-400">2. Solution Arch</span>
            <span id="status-solution_architect" class="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-[11px] text-slate-400">System Topology & Cloud</p>
        </div>

        <!-- 3. Data Architect -->
        <div id="card-data_architect" class="p-3 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-cyan-400">3. Data Arch</span>
            <span id="status-data_architect" class="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-[11px] text-slate-400">ERD & SQL Schema</p>
        </div>

        <!-- 4. UI/UX Designer -->
        <div id="card-ui_designer" class="p-3 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-teal-400">4. UI/UX</span>
            <span id="status-ui_designer" class="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-[11px] text-slate-400">Tokens & Wireframe</p>
        </div>

        <!-- 5. Full-Stack Engineer -->
        <div id="card-fullstack" class="p-3 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-emerald-400">5. Full-Stack</span>
            <span id="status-fullstack" class="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-[11px] text-slate-400">React + FastAPI Code</p>
        </div>

        <!-- 6. DevOps Engineer -->
        <div id="card-devops" class="p-3 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-purple-400">6. DevOps</span>
            <span id="status-devops" class="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-[11px] text-slate-400">Terraform IaC & CI/CD</p>
        </div>

        <!-- 7. QA & Security -->
        <div id="card-qa" class="p-3 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-amber-400">7. QA & Sec</span>
            <span id="status-qa" class="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-[11px] text-slate-400">Preflight & Tests</p>
        </div>
      </div>
    </section>

    <!-- Split Screen: Live Execution Trace & Delivered Artifacts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Live Orchestrator Telemetry Feed -->
      <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col h-[500px]">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-emerald-400 pulsing"></span> Real-Time Orchestrator Stream
          </h2>
          <button onclick="clearLogs()" class="text-xs text-slate-500 hover:text-slate-300">Clear</button>
        </div>
        <div id="log-container" class="flex-1 overflow-y-auto font-mono text-xs space-y-2 pr-2 text-slate-300">
          <div class="text-slate-500">[System] Visualizer HUD connected. Listening to orchestrator events...</div>
        </div>
      </section>

      <!-- Live Generated Artifacts Inspector -->
      <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col h-[500px]">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Artifacts & Code Output</h2>
          <span id="artifact-count" class="text-xs font-mono text-slate-400">0 artifacts</span>
        </div>
        <div id="artifact-container" class="flex-1 overflow-y-auto space-y-3 pr-2">
          <div class="text-center py-20 text-slate-500 text-xs">
            Awaiting artifacts from the active orchestrator workflow...
          </div>
        </div>
      </section>
    </div>
  </main>

  <script>
    let accumulatedSpend = 0.0;
    let accumulatedTokens = 0;
    let artifactCounter = 0;

    function appendLog(event) {
      const logContainer = document.getElementById('log-container');
      const row = document.createElement('div');
      row.className = 'border-l-2 pl-2.5 py-0.5 ' + getBorderColor(event.event_type);
      
      const timeStr = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '';
      row.innerHTML = `<span class="text-slate-500">[${timeStr}]</span> <span class="font-semibold ${getTextColor(event.agent_name)}">${event.agent_name || 'System'}:</span> <span>${event.message}</span>`;
      
      logContainer.appendChild(row);
      logContainer.scrollTop = logContainer.scrollHeight;

      // Update Task Banner if start of run
      if (event.event_type === 'agent_started' && event.message.includes('Analyzing requirements')) {
        document.getElementById('current-task').textContent = event.message.replace('Analyzing requirements for: ', '').replace('...', '');
        document.getElementById('squad-status-pill').textContent = 'Squad In Progress';
        document.getElementById('squad-status-pill').className = 'text-xs px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold';
      }

      // Update Squad Cards
      updateSquadCard(event);

      // Track Cost & Tokens
      if (event.data && event.data.cost_usd) {
        accumulatedSpend += parseFloat(event.data.cost_usd);
        document.getElementById('total-spend').textContent = '$' + accumulatedSpend.toFixed(6);
      }
      if (event.data && event.data.tokens) {
        accumulatedTokens += parseInt(event.data.tokens);
        document.getElementById('total-tokens').textContent = accumulatedTokens.toLocaleString();
      }

      // Track Artifacts
      if (event.event_type === 'artifact_generated') {
        artifactCounter++;
        document.getElementById('artifact-count').textContent = artifactCounter + ' artifacts';
        addArtifactCard(event);
      }

      if (event.event_type === 'run_completed') {
        document.getElementById('squad-status-pill').textContent = 'Delivery Complete ✓';
        document.getElementById('squad-status-pill').className = 'text-xs px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold';
      }
    }

    function updateSquadCard(event) {
      const name = (event.agent_name || '').toLowerCase();
      let key = '';
      if (name.includes('analyst') || name.includes('ba')) key = 'ba';
      else if (name.includes('solution')) key = 'solution_architect';
      else if (name.includes('data')) key = 'data_architect';
      else if (name.includes('designer') || name.includes('ui')) key = 'ui_designer';
      else if (name.includes('fullstack') || name.includes('full-stack') || name.includes('engineer')) key = 'fullstack';
      else if (name.includes('devops')) key = 'devops';
      else if (name.includes('qa')) key = 'qa';

      if (!key) return;

      const card = document.getElementById('card-' + key);
      const badge = document.getElementById('status-' + key);
      const topLabel = document.getElementById('active-agent-label');

      if (!card || !badge) return;

      if (event.event_type === 'agent_started') {
        card.className = 'p-3 rounded-lg border border-indigo-500 bg-indigo-950/30 shadow-md shadow-indigo-500/10 transition';
        badge.className = 'text-[9px] px-1 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-bold pulsing';
        badge.textContent = 'Active';
        topLabel.textContent = event.agent_name + ' running...';
      } else if (event.event_type === 'step_completed') {
        card.className = 'p-3 rounded-lg border border-emerald-500/40 bg-emerald-950/10 transition';
        badge.className = 'text-[9px] px-1 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold';
        badge.textContent = 'Done ✓';
      }
    }

    function addArtifactCard(event) {
      const container = document.getElementById('artifact-container');
      if (artifactCounter === 1) container.innerHTML = '';

      const card = document.createElement('div');
      card.className = 'p-3 rounded-lg border border-slate-800 bg-slate-950/80 text-xs space-y-1.5 transition hover:border-slate-700';
      card.innerHTML = `
        <div class="flex items-center justify-between font-semibold text-slate-200">
          <span>${event.message}</span>
          <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">${event.agent_name}</span>
        </div>
        <p class="text-slate-400 line-clamp-3 font-mono text-[11px] bg-slate-900/60 p-2 rounded border border-slate-800/80">${event.data && event.data.snippet ? event.data.snippet : 'Artifact compiled and verified.'}</p>
      `;
      container.appendChild(card);
    }

    function getBorderColor(type) {
      switch(type) {
        case 'agent_started': return 'border-indigo-500';
        case 'tool_call': return 'border-amber-500';
        case 'artifact_generated': return 'border-emerald-500';
        case 'guardrail_triggered': return 'border-rose-500';
        default: return 'border-slate-800';
      }
    }

    function getTextColor(agent) {
      const a = (agent || '').toLowerCase();
      if (a.includes('analyst')) return 'text-indigo-400';
      if (a.includes('solution')) return 'text-sky-400';
      if (a.includes('data')) return 'text-cyan-400';
      if (a.includes('designer') || a.includes('ui')) return 'text-teal-400';
      if (a.includes('fullstack') || a.includes('full-stack')) return 'text-emerald-400';
      if (a.includes('devops')) return 'text-purple-400';
      if (a.includes('qa')) return 'text-amber-400';
      return 'text-slate-400';
    }

    function clearLogs() {
      document.getElementById('log-container').innerHTML = '';
    }

    // Connect to SSE Stream
    const evtSource = new EventSource('/api/stream');
    evtSource.onmessage = function(e) {
      try {
        const data = JSON.parse(e.data);
        appendLog(data);
      } catch (err) {}
    };
    evtSource.onerror = function() {
      document.getElementById('conn-dot').className = 'h-2 w-2 rounded-full bg-rose-400';
      document.getElementById('conn-text').textContent = 'Stream Disconnected';
    };
  </script>
</body>
</html>
"""
