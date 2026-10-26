import React from 'react';
import { PriorityBadge, StatusBadge, SLABadge } from './StatusBadge';

export default function IncidentTable({ incidents = [], isLoading }) {
  if (isLoading) {
    return (
      <div className="empty-state">
        <div className="empty-state-title">Loading Incidents...</div>
        <p>Fetching real-time incident state and deterministic SLA assessments.</p>
      </div>
    );
  }

  if (incidents.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-title">No Incidents Found</div>
        <p>Try adjusting your search criteria or clearing active filters.</p>
      </div>
    );
  }

  const formatRemainingTime = (sla) => {
    if (!sla) return '—';
    if (sla.sla_status === 'RESOLVED') {
      return <span className="remaining-time resolved">Resolved ({sla.elapsed_minutes}m)</span>;
    }
    if (sla.breached) {
      return (
        <span className="remaining-time negative" title={`Overdue by ${Math.abs(sla.remaining_minutes)} mins`}>
          -{Math.abs(sla.remaining_minutes)}m overdue
        </span>
      );
    }
    if (sla.sla_status === 'AT_RISK') {
      return (
        <span className="remaining-time warning" title={`${sla.percentage_consumed}% SLA consumed`}>
          +{sla.remaining_minutes}m left
        </span>
      );
    }
    return (
      <span className="remaining-time positive" title={`${sla.percentage_consumed}% SLA consumed`}>
        +{sla.remaining_minutes}m left
      </span>
    );
  };

  return (
    <div className="table-container">
      <table className="incident-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title & Summary</th>
            <th>Service</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Assignee</th>
            <th>SLA Status</th>
            <th>Remaining SLA</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((inc) => (
            <tr key={inc.id}>
              <td>
                <span className="incident-id">{inc.id}</span>
              </td>
              <td className="incident-title-cell">
                <span className="incident-title-text" title={inc.title}>
                  {inc.title}
                </span>
                <span className="incident-summary-subtext" title={inc.summary}>
                  {inc.summary}
                </span>
              </td>
              <td>
                <span className="service-tag">{inc.service}</span>
              </td>
              <td>
                <PriorityBadge priority={inc.priority} />
              </td>
              <td>
                <StatusBadge status={inc.status} />
              </td>
              <td>
                <span className="assignee-text">{inc.assigned_to}</span>
              </td>
              <td>
                <SLABadge slaStatus={inc.sla?.sla_status} />
              </td>
              <td>{formatRemainingTime(inc.sla)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
