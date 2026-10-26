import React from 'react';

export default function FilterBar({
  search,
  setSearch,
  priority,
  setPriority,
  status,
  setStatus,
  service,
  setService,
  servicesList = [],
  onReset,
}) {
  const hasActiveFilters = Boolean(search || priority || status || service);

  return (
    <div className="filter-bar">
      <div className="search-input-wrapper">
        <span className="search-icon" aria-hidden="true">
          🔍
        </span>
        <input
          type="text"
          className="search-input"
          placeholder="Search by title, summary, or ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <select
        className="filter-select"
        value={priority}
        onChange={(e) => setPriority(e.target.value)}
        aria-label="Filter by Priority"
      >
        <option value="">All Priorities</option>
        <option value="P1">P1 (Critical)</option>
        <option value="P2">P2 (High)</option>
        <option value="P3">P3 (Medium)</option>
        <option value="P4">P4 (Low)</option>
      </select>

      <select
        className="filter-select"
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        aria-label="Filter by Status"
      >
        <option value="">All Statuses</option>
        <option value="Open">Open</option>
        <option value="In Progress">In Progress</option>
        <option value="Resolved">Resolved</option>
      </select>

      <select
        className="filter-select"
        value={service}
        onChange={(e) => setService(e.target.value)}
        aria-label="Filter by Service"
      >
        <option value="">All Services</option>
        {servicesList.map((svc) => (
          <option key={svc} value={svc}>
            {svc}
          </option>
        ))}
      </select>

      {hasActiveFilters && (
        <button
          type="button"
          onClick={onReset}
          className="reset-button"
          title="Clear all filters"
        >
          ✕ Clear Filters
        </button>
      )}
    </div>
  );
}
