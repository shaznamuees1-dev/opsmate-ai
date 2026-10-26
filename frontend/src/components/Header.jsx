import React from 'react';

export default function Header({ health, isRefreshing, onRefresh }) {
  const isHealthy = health?.status === 'healthy';
  const isAiReady = health?.ai_ready;

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo" aria-hidden="true">
          OM
        </div>
        <div className="brand-text">
          <h1>
            OpsMate AI
            <span className="brand-badge">ITSM Assistant</span>
          </h1>
          <p>Autonomous Incident Intelligence & Deterministic SLA Risk Monitoring</p>
        </div>
      </div>

      <div className="header-status-group">
        <div className="status-pill" title={isHealthy ? 'FastAPI Backend Online' : 'Connecting to Backend...'}>
          <span className={`status-dot ${isHealthy ? 'healthy' : 'offline'}`} />
          <span>{isHealthy ? 'API Online' : 'Connecting'}</span>
        </div>

        <div
          className="status-pill"
          title={
            isAiReady
              ? 'Groq AI Connected with LangGraph'
              : 'Groq API Key not configured (Deterministic rules & dashboard remain active)'
          }
        >
          <span className={`status-dot ${isAiReady ? 'healthy' : 'warning'}`} />
          <span>{isAiReady ? 'AI Agent Ready' : 'AI Key Standby'}</span>
        </div>

        <button
          onClick={onRefresh}
          className="reset-button"
          disabled={isRefreshing}
          title="Refresh incident data and health"
          style={{ padding: '4px 10px', fontSize: '0.8rem' }}
        >
          {isRefreshing ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>
    </header>
  );
}
