import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import SummaryCards from './components/SummaryCards';
import FilterBar from './components/FilterBar';
import IncidentTable from './components/IncidentTable';
import ChatPanel from './components/ChatPanel';

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [health, setHealth] = useState(null);
  const [servicesList, setServicesList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [priority, setPriority] = useState('');
  const [status, setStatus] = useState('');
  const [service, setService] = useState('');

  // Fetch health
  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch {
      setHealth({ status: 'offline', ai_ready: false });
    }
  }, []);

  // Fetch summary
  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch('/api/incidents/summary');
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Failed to fetch incident summary', err);
    }
  }, []);

  // Fetch filtered incidents
  const fetchIncidents = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.append('search', search.trim());
      if (priority) params.append('priority', priority);
      if (status) params.append('status', status);
      if (service) params.append('service', service);

      const res = await fetch(`/api/incidents?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data);

        // Populate available service names if not yet set
        setServicesList((prev) => {
          if (prev.length > 0) return prev;
          const distinct = Array.from(new Set(data.map((i) => i.service))).sort();
          return distinct;
        });
      }
    } catch (err) {
      console.error('Failed to fetch incidents', err);
    } finally {
      setIsLoading(false);
    }
  }, [search, priority, status, service]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([fetchHealth(), fetchSummary(), fetchIncidents()]);
    setIsRefreshing(false);
  };

  const handleResetFilters = () => {
    setSearch('');
    setPriority('');
    setStatus('');
    setService('');
  };

  useEffect(() => {
    fetchHealth();
    fetchSummary();
  }, [fetchHealth, fetchSummary]);

  useEffect(() => {
    // Debounce search/filter calls slightly
    const timer = setTimeout(() => {
      fetchIncidents();
    }, 200);
    return () => clearTimeout(timer);
  }, [fetchIncidents]);

  return (
    <div className="app-container">
      <Header
        health={health}
        isRefreshing={isRefreshing}
        onRefresh={handleRefresh}
      />

      <main className="dashboard-content">
        <SummaryCards summary={summary} />

        <div className="main-grid">
          {/* Left Column: Incidents Management */}
          <section className="incidents-section">
            <div className="section-header">
              <h2 className="section-title">
                Incident Operations
                <span className="section-count">{incidents.length} shown</span>
              </h2>
            </div>

            <FilterBar
              search={search}
              setSearch={setSearch}
              priority={priority}
              setPriority={setPriority}
              status={status}
              setStatus={setStatus}
              service={service}
              setService={setService}
              servicesList={servicesList}
              onReset={handleResetFilters}
            />

            <IncidentTable incidents={incidents} isLoading={isLoading} />
          </section>

          {/* Right Column: AI Assistant Panel */}
          <section className="ai-section">
            <ChatPanel />
          </section>
        </div>
      </main>
    </div>
  );
}
