"""Nexus Dashboard: Localhost Visualizer and Agent Observability Server."""
from __future__ import annotations

import asyncio
from typing import Any
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from nexus import __version__
from nexus.dashboard.telemetry import AgentEvent, EventType, event_bus


class DreamRequest(BaseModel):
    idea: str


def create_dashboard_app() -> FastAPI:
    """Build the FastAPI localhost visualizer application."""
    app = FastAPI(
        title="Nexus Visualizer",
        description="Localhost Agent Observability & Tracking Dashboard",
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
            "status": "online",
            "framework_version": __version__,
            "history_count": len(event_bus.get_history(1000)),
        }

    @app.get("/api/events")
    async def get_events(limit: int = 50) -> list[dict[str, Any]]:
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

    @app.post("/api/dream")
    async def trigger_dream(req: DreamRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
        """Trigger an IT squad run in the background while streaming progress."""
        from nexus.teams.it_pack.team import NexusITTeam

        def run_squad() -> None:
            team = NexusITTeam()
            team.build_from_idea(req.idea)

        background_tasks.add_task(run_squad)
        return {"status": "started", "idea": req.idea}

    @app.get("/", response_class=HTMLResponse)
    async def serve_dashboard() -> str:
        """Serve the standalone dark-mode single-page visualizer."""
        return DASHBOARD_HTML

    return app


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nexus Agent Visualizer</title>
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
      50% { opacity: 0.5; transform: scale(1.05); }
    }
    .pulsing { animation: pulse-fast 1.5s infinite; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased">
  <!-- Top Navigation -->
  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
        N
      </div>
      <div>
        <h1 class="text-sm font-semibold tracking-wide text-slate-100 flex items-center gap-2">
          Nexus Agent Visualizer
          <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Live Observability</span>
        </h1>
        <p class="text-xs text-slate-400">Localhost Orchestrator & Progress Tracking</p>
      </div>
    </div>
    <div class="flex items-center gap-4 text-xs">
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
        <span id="conn-dot" class="h-2 w-2 rounded-full bg-emerald-400"></span>
        <span id="conn-text" class="text-slate-300 font-medium">Connected to Stream</span>
      </div>
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
        <span class="text-slate-400">Total Spend:</span>
        <span id="total-spend" class="font-bold text-emerald-400">$0.000000</span>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto p-6 space-y-6">
    <!-- Action Prompt Header -->
    <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
      <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Deploy Virtual IT Squad</h2>
      <div class="flex gap-3">
        <input id="prompt-input" type="text" placeholder="Enter an app idea... (e.g. 'I want a Tinder for luxury watches with instant price comparison')" 
          class="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition">
        <button id="btn-deploy" onclick="deploySquad()" 
          class="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-5 py-2.5 rounded-lg text-sm shadow-md shadow-indigo-600/20 transition flex items-center gap-2">
          <span>🚀 Run IT Squad</span>
        </button>
      </div>
    </section>

    <!-- Visual Agent Topology Pipeline -->
    <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Agent Squad Topology & Real-Time Progress</h2>
        <span id="active-agent-badge" class="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-400">Squad Idle</span>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
        <!-- 1. BA -->
        <div id="card-ba" class="p-4 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-indigo-400">1. Business Analyst</span>
            <span id="status-ba" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-xs text-slate-400">Extracts user stories, features & HTML wireframe.</p>
        </div>

        <!-- 2. Manager -->
        <div id="card-manager" class="p-4 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-blue-400">2. Engineering Mgr</span>
            <span id="status-manager" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-xs text-slate-400">Architecture, DB schema & task breakdown.</p>
        </div>

        <!-- 3. Designer -->
        <div id="card-designer" class="p-4 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-teal-400">3. UI/UX Designer</span>
            <span id="status-designer" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-xs text-slate-400">React + Tailwind component code.</p>
        </div>

        <!-- 4. Engineer -->
        <div id="card-engineer" class="p-4 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-emerald-400">4. Backend Eng</span>
            <span id="status-engineer" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-xs text-slate-400">FastAPI microservice & Pydantic models.</p>
        </div>

        <!-- 5. QA -->
        <div id="card-qa" class="p-4 rounded-lg border border-slate-800 bg-slate-950/60 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-amber-400">5. QA & Security</span>
            <span id="status-qa" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Idle</span>
          </div>
          <p class="text-xs text-slate-400">Preflight check & automated pytest suite.</p>
        </div>
      </div>
    </section>

    <!-- Split Screen: Event Telemetry Stream & Artifacts Preview -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Live Terminal Event Stream -->
      <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col h-[460px]">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-emerald-400 pulsing"></span> Live Telemetry Feed
          </h2>
          <button onclick="clearLogs()" class="text-xs text-slate-500 hover:text-slate-300">Clear</button>
        </div>
        <div id="log-container" class="flex-1 overflow-y-auto font-mono text-xs space-y-2 pr-2 text-slate-300">
          <div class="text-slate-500">[System] Visualizer connected. Ready to stream agent execution.</div>
        </div>
      </section>

      <!-- Live Generated Artifacts Inspector -->
      <section class="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur flex flex-col h-[460px]">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Artifacts & Specifications</h2>
          <span id="artifact-count" class="text-xs font-mono text-slate-400">0 artifacts</span>
        </div>
        <div id="artifact-container" class="flex-1 overflow-y-auto space-y-3 pr-2">
          <div class="text-center py-16 text-slate-500 text-xs">
            Run an IT Squad task to inspect generated Proposals, Wireframes, and Code live.
          </div>
        </div>
      </section>
    </div>
  </main>

  <script>
    let accumulatedSpend = 0.0;
    let artifactCounter = 0;

    function appendLog(event) {
      const logContainer = document.getElementById('log-container');
      const row = document.createElement('div');
      row.className = 'border-l-2 pl-2.5 py-0.5 ' + getBorderColor(event.event_type);
      
      const timeStr = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '';
      row.innerHTML = `<span class="text-slate-500">[${timeStr}]</span> <span class="font-semibold ${getTextColor(event.agent_name)}">${event.agent_name || 'System'}:</span> <span>${event.message}</span>`;
      
      logContainer.appendChild(row);
      logContainer.scrollTop = logContainer.scrollHeight;

      // Update Agent Cards
      updateAgentCard(event);

      // Track Cost
      if (event.data && event.data.cost_usd) {
        accumulatedSpend += parseFloat(event.data.cost_usd);
        document.getElementById('total-spend').textContent = '$' + accumulatedSpend.toFixed(6);
      }

      // Track Artifacts
      if (event.event_type === 'artifact_generated') {
        artifactCounter++;
        document.getElementById('artifact-count').textContent = artifactCounter + ' artifacts';
        addArtifactCard(event);
      }
    }

    function updateAgentCard(event) {
      const name = (event.agent_name || '').toLowerCase();
      let key = '';
      if (name.includes('analyst') || name.includes('ba')) key = 'ba';
      else if (name.includes('manager')) key = 'manager';
      else if (name.includes('designer')) key = 'designer';
      else if (name.includes('engineer') || name.includes('backend')) key = 'engineer';
      else if (name.includes('qa')) key = 'qa';

      if (!key) return;

      const card = document.getElementById('card-' + key);
      const badge = document.getElementById('status-' + key);
      const topBadge = document.getElementById('active-agent-badge');

      if (event.event_type === 'agent_started') {
        card.className = 'p-4 rounded-lg border border-indigo-500 bg-indigo-950/20 shadow-lg shadow-indigo-500/10 transition';
        badge.className = 'text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-bold pulsing';
        badge.textContent = 'Active';
        topBadge.textContent = 'Active: ' + event.agent_name;
        topBadge.className = 'text-xs px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 font-semibold';
      } else if (event.event_type === 'step_completed') {
        card.className = 'p-4 rounded-lg border border-emerald-500/40 bg-emerald-950/10 transition';
        badge.className = 'text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold';
        badge.textContent = 'Done ✓';
      }
    }

    function addArtifactCard(event) {
      const container = document.getElementById('artifact-container');
      if (artifactCounter === 1) container.innerHTML = '';

      const card = document.createElement('div');
      card.className = 'p-3.5 rounded-lg border border-slate-800 bg-slate-950/80 text-xs space-y-1.5';
      card.innerHTML = `
        <div class="flex items-center justify-between font-semibold text-slate-200">
          <span>${event.message}</span>
          <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">${event.agent_name}</span>
        </div>
        <p class="text-slate-400 line-clamp-3 font-mono">${event.data && event.data.snippet ? event.data.snippet : 'Artifact compiled and verified.'}</p>
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
      if (a.includes('manager')) return 'text-blue-400';
      if (a.includes('designer')) return 'text-teal-400';
      if (a.includes('engineer')) return 'text-emerald-400';
      if (a.includes('qa')) return 'text-amber-400';
      return 'text-slate-400';
    }

    function clearLogs() {
      document.getElementById('log-container').innerHTML = '';
    }

    async function deploySquad() {
      const input = document.getElementById('prompt-input');
      const val = input.value.trim();
      if (!val) return;

      appendLog({
        event_type: 'agent_started',
        agent_name: 'Squad Orchestrator',
        message: 'Squad commissioned for task: ' + val,
        timestamp: new Date().toISOString()
      });

      try {
        await fetch('/api/dream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ idea: val })
        });
        input.value = '';
      } catch (err) {
        console.error('Failed to trigger squad:', err);
      }
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
