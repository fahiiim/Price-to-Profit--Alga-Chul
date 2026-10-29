import React, { useState, useMemo } from 'react';
import { Download, Calendar, Filter } from 'lucide-react';
import TopHeader from '../components/TopHeader';

export default function ActivityPage({
  activities,
  onNavigateToSubscriber,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [eventFilter, setEventFilter] = useState('All');
  const [platformFilter, setPlatformFilter] = useState('All');
  const [timeframe, setTimeframe] = useState('30d'); // 'today', '7d', '30d'

  const filteredActivities = useMemo(() => {
    return activities.filter((act) => {
      if (eventFilter !== 'All' && act.event !== eventFilter) return false;
      if (platformFilter !== 'All' && act.platform !== platformFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesSub = act.subscriber.toLowerCase().includes(q);
        const matchesDet = act.details.toLowerCase().includes(q);
        const matchesEvt = act.event.toLowerCase().includes(q);
        if (!matchesSub && !matchesDet && !matchesEvt) return false;
      }
      return true;
    });
  }, [activities, eventFilter, platformFilter, searchQuery]);

  const handleExportCsv = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'Time,Subscriber,Event,Details,Platform\n' +
      filteredActivities
        .map((a) => `"${a.time}","${a.subscriber}","${a.event}","${a.details}","${a.platform}"`)
        .join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `activity_log_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getEventBadgeClass = (event) => {
    if (event === 'Renewed' || event === 'Subscribed') return 'badge-active';
    if (event === 'Trial started' || event === 'Quote created') return 'badge-trial';
    if (event === 'PDF shared') return 'badge-purple';
    if (event === 'Expired' || event === 'Free period granted') return 'badge-expired';
    if (event.includes('Disabled')) return 'badge-disabled';
    return 'badge-active';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <TopHeader
        title="Activity log"
        subtitle="Every subscription and usage event"
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        actions={
          <button className="btn-secondary" onClick={handleExportCsv} id="btn-export-activity-csv">
            <Download size={14} />
            <span>Export CSV</span>
          </button>
        }
      />

      <div className="page-body">
        {/* Filter Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          {/* Left filters: Date Range + Event Dropdown + Platform Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            {/* Date Range Picker */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: '#FFFFFF',
                border: '1px solid var(--card-border)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 14px',
                fontSize: 12.5,
                color: 'var(--text-heading)',
                fontWeight: 500,
              }}
            >
              <Calendar size={14} style={{ color: 'var(--text-light)' }} />
              <span>1 Oct – 15 Oct 2026</span>
            </div>

            {/* Event Dropdown */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 12, color: 'var(--text-light)', fontWeight: 600 }}>Event:</span>
              <select
                className="input-text"
                style={{ padding: '6px 12px', fontSize: 12.5 }}
                value={eventFilter}
                onChange={(e) => setEventFilter(e.target.value)}
              >
                <option value="All">All</option>
                <option value="Renewed">Renewed</option>
                <option value="Trial started">Trial started</option>
                <option value="Quote created">Quote created</option>
                <option value="PDF shared">PDF shared</option>
                <option value="Expired">Expired</option>
                <option value="Subscribed">Subscribed</option>
                <option value="Free period granted">Free period granted</option>
                <option value="Disabled by admin">Disabled by admin</option>
              </select>
            </div>

            {/* Platform Dropdown */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 12, color: 'var(--text-light)', fontWeight: 600 }}>Platform:</span>
              <select
                className="input-text"
                style={{ padding: '6px 12px', fontSize: 12.5 }}
                value={platformFilter}
                onChange={(e) => setPlatformFilter(e.target.value)}
              >
                <option value="All">All</option>
                <option value="iOS">iOS</option>
                <option value="Android">Android</option>
                <option value="Admin">Admin</option>
              </select>
            </div>
          </div>

          {/* Right Timeframe toggle pills */}
          <div className="tab-list">
            <button
              className={`tab-btn ${timeframe === 'today' ? 'active' : ''}`}
              onClick={() => setTimeframe('today')}
            >
              Today
            </button>
            <button
              className={`tab-btn ${timeframe === '7d' ? 'active' : ''}`}
              onClick={() => setTimeframe('7d')}
            >
              7 days
            </button>
            <button
              className={`tab-btn ${timeframe === '30d' ? 'active' : ''}`}
              onClick={() => setTimeframe('30d')}
            >
              30 days
            </button>
          </div>
        </div>

        {/* Activity Table Card */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '18%' }}>Time</th>
                  <th style={{ width: '25%' }}>Subscriber</th>
                  <th style={{ width: '20%' }}>Event</th>
                  <th style={{ width: '25%' }}>Details</th>
                  <th style={{ width: '12%' }}>Platform</th>
                </tr>
              </thead>
              <tbody>
                {filteredActivities.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-muted)' }}>
                      No events found matching the selected filters.
                    </td>
                  </tr>
                ) : (
                  filteredActivities.map((act) => (
                    <tr key={act.id}>
                      <td>
                        <span style={{ fontSize: 12.5, color: 'var(--text-muted)', fontWeight: 500 }}>
                          {act.time}
                        </span>
                      </td>

                      <td>
                        <span
                          style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: 'var(--text-heading)',
                            cursor: 'pointer',
                          }}
                          onClick={() => onNavigateToSubscriber && onNavigateToSubscriber(act.subscriber)}
                        >
                          {act.subscriber}
                        </span>
                      </td>

                      <td>
                        <span className={`badge ${getEventBadgeClass(act.event)}`}>
                          {act.event}
                        </span>
                      </td>

                      <td>
                        <span style={{ fontSize: 12.5, color: 'var(--text-body)' }}>
                          {act.details}
                        </span>
                      </td>

                      <td>
                        <span
                          style={{
                            fontSize: 11.5,
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: act.platform === 'iOS' ? '#F1F5F9' : act.platform === 'Android' ? '#ECFDF5' : '#FEF3C7',
                            color: act.platform === 'iOS' ? '#334155' : act.platform === 'Android' ? '#047857' : '#B45309',
                          }}
                        >
                          {act.platform}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
