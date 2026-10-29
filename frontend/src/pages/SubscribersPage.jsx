import React, { useState, useMemo } from 'react';
import { Download, MoreHorizontal, ChevronLeft, ChevronRight, Eye, ShieldAlert, Gift } from 'lucide-react';
import TopHeader from '../components/TopHeader';

export default function SubscribersPage({
  subscribers,
  onSelectSubscriber,
  onExportCsv
}) {
  const [activeFilter, setActiveFilter] = useState('All'); // 'All', 'Active', 'Trial', 'Expired', 'Disabled'
  const [planFilter, setPlanFilter] = useState('All');
  const [countryFilter, setCountryFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const filterTabs = [
    { id: 'All', label: 'All', count: 1248 },
    { id: 'Active', label: 'Active', count: 982 },
    { id: 'Trial', label: 'Trial', count: 136 },
    { id: 'Expired', label: 'Expired', count: 118 },
    { id: 'Disabled', label: 'Disabled', count: 12 },
  ];

  const filteredSubscribers = useMemo(() => {
    return subscribers.filter((sub) => {
      // Status filter
      if (activeFilter !== 'All' && sub.status.toLowerCase() !== activeFilter.toLowerCase()) {
        return false;
      }
      // Plan filter
      if (planFilter !== 'All' && sub.plan !== planFilter) {
        return false;
      }
      // Country filter
      if (countryFilter !== 'All' && sub.country !== countryFilter) {
        return false;
      }
      // Search
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesName = sub.name.toLowerCase().includes(query);
        const matchesEmail = sub.email.toLowerCase().includes(query);
        const matchesOwner = sub.owner?.toLowerCase().includes(query);
        if (!matchesName && !matchesEmail && !matchesOwner) return false;
      }
      return true;
    });
  }, [subscribers, activeFilter, planFilter, countryFilter, searchQuery]);

  const handleDownloadCsv = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'Business,Email,Country,Plan,Status,Joined,Quotes,LastActive\n' +
      filteredSubscribers
        .map((s) => `"${s.name}","${s.email}","${s.country}","${s.plan}","${s.status}","${s.joined}",${s.quotesCount},"${s.lastActive}"`)
        .join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `subscribers_${activeFilter.toLowerCase()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <TopHeader
        title="Subscribers"
        subtitle="1,248 businesses using Price to Profit"
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        actions={
          <button
            className="btn-secondary"
            onClick={handleDownloadCsv}
            id="btn-subscribers-export-csv"
          >
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
            gap: 14,
          }}
        >
          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {filterTabs.map((tab) => {
              const isActive = activeFilter === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveFilter(tab.id);
                    setCurrentPage(1);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 14px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: 12.5,
                    fontWeight: 600,
                    backgroundColor: isActive ? 'var(--text-heading)' : '#FFFFFF',
                    color: isActive ? '#FFFFFF' : 'var(--text-muted)',
                    border: '1px solid',
                    borderColor: isActive ? 'var(--text-heading)' : 'var(--card-border)',
                    boxShadow: isActive ? '0 2px 6px rgba(0,0,0,0.1)' : 'var(--shadow-xs)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>{tab.label}</span>
                  <span
                    style={{
                      fontSize: 11,
                      opacity: isActive ? 0.85 : 0.65,
                      fontWeight: 500,
                    }}
                  >
                    {tab.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Right dropdowns */}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 12, color: 'var(--text-light)', fontWeight: 600 }}>Plan:</span>
              <select
                value={planFilter}
                onChange={(e) => setPlanFilter(e.target.value)}
                className="input-text"
                style={{ padding: '6px 12px', fontSize: 12.5, borderRadius: 'var(--radius-md)' }}
              >
                <option value="All">All</option>
                <option value="Annual">Annual</option>
                <option value="Monthly">Monthly</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 12, color: 'var(--text-light)', fontWeight: 600 }}>Country:</span>
              <select
                value={countryFilter}
                onChange={(e) => setCountryFilter(e.target.value)}
                className="input-text"
                style={{ padding: '6px 12px', fontSize: 12.5, borderRadius: 'var(--radius-md)' }}
              >
                <option value="All">All</option>
                <option value="UAE">UAE</option>
                <option value="Saudi Arabia">Saudi Arabia</option>
                <option value="UK">UK</option>
                <option value="Qatar">Qatar</option>
                <option value="Kuwait">Kuwait</option>
              </select>
            </div>
          </div>
        </div>

        {/* Subscribers Table Card */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Business</th>
                  <th>Country</th>
                  <th>Plan</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Quotes</th>
                  <th>Last Active</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSubscribers.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-muted)' }}>
                      No subscribers found matching the selected filters.
                    </td>
                  </tr>
                ) : (
                  filteredSubscribers.map((sub) => {
                    const statusClass =
                      sub.status === 'Active'
                        ? 'badge-active'
                        : sub.status === 'Trial'
                        ? 'badge-trial'
                        : sub.status === 'Expired'
                        ? 'badge-expired'
                        : 'badge-disabled';

                    return (
                      <tr
                        key={sub.id}
                        style={{ cursor: 'pointer' }}
                        onClick={() => onSelectSubscriber(sub)}
                      >
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <div
                              style={{
                                width: 34,
                                height: 34,
                                borderRadius: 'var(--radius-full)',
                                backgroundColor: '#1E2330',
                                color: '#FFFFFF',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: 12,
                                fontWeight: 700,
                              }}
                            >
                              {sub.initials}
                            </div>
                            <div>
                              <div style={{ fontWeight: 600, color: 'var(--text-heading)' }}>
                                {sub.name}
                              </div>
                              <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                                {sub.email}
                              </div>
                            </div>
                          </div>
                        </td>

                        <td>
                          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-body)' }}>
                            {sub.country}
                          </span>
                        </td>

                        <td>
                          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-body)' }}>
                            {sub.plan}
                          </span>
                        </td>

                        <td>
                          <span className={`badge ${statusClass}`}>{sub.status}</span>
                        </td>

                        <td>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            {sub.joined}
                          </span>
                        </td>

                        <td>
                          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-heading)' }}>
                            {sub.quotesCount}
                          </span>
                        </td>

                        <td>
                          <span style={{ fontSize: 12, color: 'var(--text-light)' }}>
                            {sub.lastActive}
                          </span>
                        </td>

                        <td style={{ textAlign: 'right' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectSubscriber(sub);
                            }}
                            className="icon-button"
                            style={{ width: 28, height: 28, display: 'inline-flex' }}
                            title="View details"
                          >
                            <MoreHorizontal size={14} />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 20px',
              borderTop: '1px solid var(--card-border)',
              backgroundColor: '#FAFAFB',
              fontSize: 12.5,
              color: 'var(--text-muted)',
            }}
          >
            <span>Showing 1-{filteredSubscribers.length} of 1,248</span>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button
                className="icon-button"
                style={{ width: 28, height: 28 }}
                disabled={currentPage === 1}
              >
                <ChevronLeft size={14} />
              </button>
              <button
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 'var(--primary)',
                  color: '#FFFFFF',
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                1
              </button>
              <button
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 'var(--radius-full)',
                  color: 'var(--text-body)',
                  fontSize: 12,
                }}
              >
                2
              </button>
              <button
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 'var(--radius-full)',
                  color: 'var(--text-body)',
                  fontSize: 12,
                }}
              >
                3
              </button>
              <span style={{ padding: '0 4px', color: 'var(--text-light)' }}>...</span>
              <button
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 'var(--radius-full)',
                  color: 'var(--text-body)',
                  fontSize: 12,
                }}
              >
                139
              </button>
              <button className="icon-button" style={{ width: 28, height: 28 }}>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
