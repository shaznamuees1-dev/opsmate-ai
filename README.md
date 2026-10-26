# OpsMate AI — IT Service Management (ITSM) Assistant

OpsMate AI is an interview-ready, AI-powered IT operations assistant designed to monitor active IT incidents, calculate SLA risks deterministically, and provide actionable operational intelligence.

Built for an ITSM internship interview, OpsMate AI pairs a **FastAPI** backend and **React** dashboard with a **LangGraph + Groq** agent that grounds its answers in real Python tool execution rather than language-model guesswork.

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │    React + Vite Frontend (Port 5173)   │
                      │  - Incident KPI Cards                  │
                      │  - Multi-Filter Incident Table         │
                      │  - Interactive AI Assistant Panel      │
                      └──────────────────┬─────────────────────┘
                                         │ HTTP / REST
                                         ▼
                      ┌────────────────────────────────────────┐
                      │      FastAPI Backend (Port 8000)       │
                      │  GET  /api/health                      │
                      │  GET  /api/incidents (filterable)      │
                      │  GET  /api/incidents/summary           │
                      │  POST /api/chat                        │
                      └──────────┬──────────────────┬──────────┘
                                 │                  │
               ┌─────────────────┴─┐              ┌─┴────────────────────────┐
               │ LangGraph + Groq  │              │ Deterministic SLA Engine │
               │ Assistant         │              │ (Pure Python Logic)      │
               │                   │              │                          │
               │ Tools Invoked:    ├─────────────►│ - Elapsed / Remaining    │
               │ 1. list_incidents │              │ - Consumed Percentage    │
               │ 2. calculate_sla  │              │ - HEALTHY / AT_RISK /    │
               └───────────────────┘              │   BREACHED / RESOLVED    │
                                                  └─────────────┬────────────┘
                                                                │
                                                  ┌─────────────┴────────────┐
                                                  │ Synthetic Incident Store │
                                                  │ (In-Memory Dataset)      │
                                                  └──────────────────────────┘
```

### How a User Question Travels Through the System

1. **User asks a question** in the React chat panel (e.g., *"Which P1 incidents are still open?"*).
2. The frontend sends a `POST` request to `/api/chat` on the FastAPI server.
3. The FastAPI router passes the prompt to the **LangGraph** workflow.
4. If a valid `GROQ_API_KEY` is present, the Groq language model analyzes the query and issues a structured tool call (e.g. `list_incidents(priority="P1", status="Open")`).
5. LangGraph routes the call to the **deterministic Python tool**, which queries the in-memory incident dataset and computes live SLA metrics using the **deterministic SLA risk engine**.
6. The exact tool outputs are passed back to the model to produce a grounded summary.
7. The FastAPI backend returns the response along with the exact names of tools invoked (`["list_incidents"]`).
8. The frontend displays the assistant's answer and renders visual **tool-use badges** for transparency.
9. **Graceful Fallback**: If `GROQ_API_KEY` is not configured, the assistant returns a clear, user-friendly notice explaining how to configure the key, while the full incident table, filters, and SLA calculations remain 100% operational.

---

## Key Features

- **Synthetic IT Incident Dataset**: Realistic fictional incidents across payment gateways, databases, SSO authentication, catalog search, and email systems. No real customer data or external databases required.
- **Deterministic SLA Risk Engine**: All SLA calculations (elapsed time, remaining time, percentage consumed) are executed in pure Python code. Zero LLM math hallucination.
  - `RESOLVED`: Incident is resolved.
  - `BREACHED`: SLA target exceeded.
  - `AT_RISK`: Consumed $\ge 70\%$ of target time without breaching.
  - `HEALTHY`: Consumed $< 70\%$ of target time.
- **LangGraph + Groq Tool Calling**: Uses `llama-3.3-70b-versatile` with two core tools: `list_incidents` and `calculate_sla_risk`.
- **FastAPI REST API**: Validated with Pydantic models, CORS-enabled for local development, and fully documented via interactive Swagger UI.
- **Modern React Operations Dashboard**: Responsive dark-themed UI featuring KPI cards, multi-criteria filtering, live countdown badges, and interactive chat.
- **Automated Test Suite**: 23 unit and integration tests covering SLA edge cases, filtering, metrics, and API degradation states without paid API calls.

---

## Prerequisites

Before starting, confirm your environment meets the minimum versions:

- **Windows 10 or 11**
- **Python 3.12+** (tested with Python 3.12.4)
- **Node.js v18+** and **npm** (tested with Node v24.11.1 / npm 11.6.2)
- **Git**

---

## Step-by-Step Setup on Windows PowerShell

### Step 1: Open Two PowerShell Terminals

You will run the **FastAPI backend** in Terminal 1 and the **React frontend** in Terminal 2.

---

### Terminal 1 — Backend Setup & Run

1. Navigate to the backend directory:
   ```powershell
   cd "backend"
   ```

2. Create a Python virtual environment:
   ```powershell
   python -m venv .venv
   ```

3. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   > *Tip: If PowerShell blocks script execution, run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`*

4. Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

5. Configure your local environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

6. *(Optional)* Add your free Groq API key:
   - Open `backend\.env` in Notepad or your editor.
   - Obtain a free API key at [https://console.groq.com/keys](https://console.groq.com/keys).
   - Update `GROQ_API_KEY=gsk_your_actual_key_here`.
   > *Note: If you leave the key blank or use the placeholder, the entire dashboard and incident API still work completely. The chat assistant will politely inform you that the key is in standby.*

7. Start the FastAPI server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   The backend will be running at `http://127.0.0.1:8000`.

---

### Terminal 2 — Frontend Setup & Run

1. Navigate to the frontend directory:
   ```powershell
   cd "frontend"
   ```

2. Install Node dependencies:
   ```powershell
   npm install
   ```

3. Start the Vite React development server:
   ```powershell
   npm run dev
   ```
   The frontend will be running at `http://localhost:5173`.

---

## Application URLs

| Environment | Application | URL | Description |
| :--- | :--- | :--- | :--- |
| **Production** | **OpsMate Dashboard** | [https://opsmate-ai.vercel.app](https://opsmate-ai.vercel.app) | Live React frontend hosted on Vercel |
| **Production** | **Backend API & Docs** | [https://opsmate-ai.onrender.com/docs](https://opsmate-ai.onrender.com/docs) | Live FastAPI backend on Render |
| **Production** | **API Health** | [https://opsmate-ai.onrender.com/api/health](https://opsmate-ai.onrender.com/api/health) | Live status check on Render |
| **Local Dev** | **OpsMate Dashboard** | [http://localhost:5173](http://localhost:5173) | Interactive React incident operations dashboard |
| **Local Dev** | **Interactive API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI for testing FastAPI endpoints |
| **Local Dev** | **API Health Endpoint** | [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) | Live service status and AI readiness check |
| **Local Dev** | **Incident List API** | [http://127.0.0.1:8000/api/incidents](http://127.0.0.1:8000/api/incidents) | JSON feed with calculated SLA metrics |

---

## Running the Automated Test Suite

The test suite validates SLA boundary calculations, incident filtering, metrics aggregation, and API failure behavior. All tests are 100% offline and do not invoke external paid APIs.

In Terminal 1 (with `.venv` activated):
```powershell
cd "backend"
.\.venv\Scripts\pytest -v
```

Expected output:
```
tests/test_api.py::test_health_endpoint PASSED
tests/test_api.py::test_root_endpoint PASSED
tests/test_api.py::test_list_incidents_endpoint PASSED
tests/test_api.py::test_list_incidents_with_query_params PASSED
tests/test_api.py::test_incident_summary_endpoint PASSED
tests/test_api.py::test_single_incident_endpoint PASSED
tests/test_api.py::test_chat_endpoint_missing_api_key PASSED
tests/test_api.py::test_chat_endpoint_placeholder_api_key PASSED
tests/test_api.py::test_chat_endpoint_with_mocked_assistant PASSED
tests/test_incidents.py::test_filter_by_priority PASSED
tests/test_incidents.py::test_filter_by_status PASSED
tests/test_incidents.py::test_filter_by_service PASSED
tests/test_incidents.py::test_filter_by_keyword_search PASSED
tests/test_incidents.py::test_summary_metrics PASSED
tests/test_incidents.py::test_get_incident_by_id PASSED
tests/test_sla_engine.py::test_healthy_sla_calculation PASSED
tests/test_sla_engine.py::test_at_risk_sla_calculation PASSED
tests/test_sla_engine.py::test_at_risk_exact_70_percent_boundary PASSED
tests/test_sla_engine.py::test_breached_sla_calculation PASSED
tests/test_sla_engine.py::test_resolved_incident_within_sla PASSED
tests/test_sla_engine.py::test_resolved_incident_past_target PASSED
tests/test_sla_engine.py::test_invalid_or_negative_sla_target PASSED
tests/test_sla_engine.py::test_invalid_or_missing_timestamp PASSED
======================= 23 passed in 1.4s =======================
```

---

## Example Questions to Ask OpsMate AI

Click any of the suggested chips in the chat panel or type custom queries:

1. *"Which P1 incidents are still open?"*
   - Invokes `list_incidents(priority="P1", status="Open")` and summarizes the critical database and payment gateway incidents.
2. *"Which incidents are closest to breaching their SLAs?"*
   - Invokes `calculate_sla_risk()` and ranks incidents by shortest remaining time.
3. *"How many incidents have breached their SLAs?"*
   - Highlights incidents where elapsed time exceeded SLA target minutes.
4. *"Summarize the most urgent incidents."*
   - Synthesizes P1 and breached incidents into a concise executive briefing.
5. *"What is the status of INC-1001?"*
   - Evaluates incident `INC-1001` with its specific target, consumed percentage, and assigned engineer.

---

## Troubleshooting & Common Questions

### 1. `Activate.ps1 cannot be loaded because running scripts is disabled`
PowerShell has an execution policy restriction on new Windows installations. Run this once in PowerShell:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 2. `Port 8000 is already in use`
Another application is using port 8000. You can start Uvicorn on an alternative port:
```powershell
uvicorn app.main:app --reload --port 8001
```
*(If you change ports, update `proxy` in `frontend/vite.config.js` to match).*

### 3. `ModuleNotFoundError: No module named 'fastapi'`
You likely ran `uvicorn` outside the virtual environment. Always verify your virtual environment is active (indicated by `(.venv)` in your terminal prompt) or execute via the explicit path:
```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### 4. `What happens if I don't have a Groq API key?`
OpsMate AI is designed with graceful degradation. The entire dashboard, incident search, priority filters, and deterministic SLA calculations work without an API key. When you send a chat query without a key, OpsMate will clearly explain that the AI key is in standby mode and guide you to `.env`.

---

## Demo Limitations & Scope

As an MVP designed for internship demonstration:
- **In-Memory Store**: Incidents are kept in memory and reset on backend restart. No database (PostgreSQL, Supabase) is connected.
- **Read-Only Assistant**: The agent currently inspects and queries incidents; it does not perform automated incident re-assignments or status mutations.
- **Local Development**: Built for local demonstration on `localhost`. Authentication and public internet deployment are intentionally excluded.
