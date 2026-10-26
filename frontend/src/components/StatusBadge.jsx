import React from 'react';

export function PriorityBadge({ priority }) {
  const p = priority ? priority.toUpperCase() : 'P4';
  const classMap = {
    P1: 'p1',
    P2: 'p2',
    P3: 'p3',
    P4: 'p4',
  };
  return <span className={`badge ${classMap[p] || 'p4'}`}>{p}</span>;
}

export function StatusBadge({ status }) {
  const s = status || 'Open';
  const isResolved = s.toLowerCase() === 'resolved';
  const isInProgress = s.toLowerCase() === 'in progress';

  return (
    <span
      className="badge"
      style={{
        backgroundColor: isResolved
          ? 'rgba(139, 92, 246, 0.15)'
          : isInProgress
          ? 'rgba(59, 130, 246, 0.15)'
          : 'rgba(107, 114, 128, 0.15)',
        color: isResolved ? '#a78bfa' : isInProgress ? '#60a5fa' : '#9ca3af',
        borderColor: isResolved
          ? 'rgba(139, 92, 246, 0.3)'
          : isInProgress
          ? 'rgba(59, 130, 246, 0.3)'
          : 'rgba(107, 114, 128, 0.3)',
      }}
    >
      {s}
    </span>
  );
}

export function SLABadge({ slaStatus }) {
  const status = slaStatus ? slaStatus.toUpperCase() : 'HEALTHY';
  const map = {
    HEALTHY: { text: 'Healthy', className: 'sla-healthy' },
    AT_RISK: { text: 'At Risk', className: 'sla-at-risk' },
    BREACHED: { text: 'Breached', className: 'sla-breached' },
    RESOLVED: { text: 'Resolved', className: 'sla-resolved' },
  };

  const item = map[status] || map.HEALTHY;
  return <span className={`badge ${item.className}`}>{item.text}</span>;
}
