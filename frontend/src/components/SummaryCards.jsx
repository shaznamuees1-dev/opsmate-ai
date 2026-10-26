import React from 'react';

export default function SummaryCards({ summary }) {
  const activeCount = summary?.active_incidents ?? 0;
  const p1Count = summary?.p1_incidents ?? 0;
  const atRiskCount = summary?.at_risk_incidents ?? 0;
  const breachedCount = summary?.breached_incidents ?? 0;
  const totalCount = summary?.total_incidents ?? 0;

  return (
    <div className="summary-cards-grid">
      <div className="summary-card active">
        <div className="summary-card-header">
          <span className="summary-card-title">Active Incidents</span>
          <span style={{ fontSize: '1.1rem' }}>⚡</span>
        </div>
        <div className="summary-card-value">{activeCount}</div>
        <div className="summary-card-desc">{totalCount} total logged in system</div>
      </div>

      <div className="summary-card p1">
        <div className="summary-card-header">
          <span className="summary-card-title">P1 Critical</span>
          <span style={{ fontSize: '1.1rem' }}>🔥</span>
        </div>
        <div className="summary-card-value">{p1Count}</div>
        <div className="summary-card-desc">High-urgency active incidents</div>
      </div>

      <div className="summary-card at-risk">
        <div className="summary-card-header">
          <span className="summary-card-title">SLA At Risk</span>
          <span style={{ fontSize: '1.1rem' }}>⚠️</span>
        </div>
        <div className="summary-card-value">{atRiskCount}</div>
        <div className="summary-card-desc">≥ 70% of SLA time consumed</div>
      </div>

      <div className="summary-card breached">
        <div className="summary-card-header">
          <span className="summary-card-title">SLA Breached</span>
          <span style={{ fontSize: '1.1rem' }}>🚨</span>
        </div>
        <div className="summary-card-value">{breachedCount}</div>
        <div className="summary-card-desc">Target resolution deadline missed</div>
      </div>
    </div>
  );
}
