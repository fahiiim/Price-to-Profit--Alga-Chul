import React, { useState } from 'react';
import {
  Download,
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileSpreadsheet,
  DollarSign,
  ArrowRight
} from 'lucide-react';
import TopHeader from '../components/TopHeader';

export default function OverviewPage({
  metrics,
  onNavigateToActivity,
  onNavigateToSubscribers,
}) {
  const [chartTimeframe, setChartTimeframe] = useState('12m'); // '12m' or '30d'
  const [searchValue, setSearchValue] = useState('');

  const monthlyPoints = [
    { label: 'Nov', value: 38 },
    { label: 'Dec', value: 45 },
    { label: 'Jan', value: 52 },
    { label: 'Feb', value: 48 },
    { label: 'Mar', value: 64 },
    { label: 'Apr', value: 70 },
    { label: 'May', value: 68 },
    { label: 'Jun', value: 85 },
    { label: 'Jul', value: 92 },
    { label: 'Aug', value: 110 },
    { label: 'Sep', value: 124 },
    { label: 'Oct', value: 148 },
  ];

  const dailyQuotes = [
    { day: '14d', val: 240 },
    { day: '13d', val: 310 },
    { day: '12d', val: 280 },
    { day: '11d', val: 350 },
    { day: '10d', val: 390 },
    { day: '9d', val: 320 },
    { day: '8d', val: 290 },
    { day: '7d', val: 420 },
    { day: '6d', val: 380 },
    { day: '5d', val: 410 },
    { day: '4d', val: 460 },
    { day: '3d', val: 390 },
    { day: '2d', val: 430 },
    { day: 'Today', val: 480, isToday: true },
  ];

  const recentEvents = [
    { id: 1, title: 'Glam Strands Studio renewed Annual', subtitle: 'iOS · AED 249.99', time: '2m ago', type: 'renewed' },
    { id: 2, title: 'Luxe Locks DXB started a free trial', subtitle: 'Android', time: '14m ago', type: 'trial' },
    { id: 3, title: 'Hair by Noor created 3 quotes', subtitle: 'iOS', time: '32m ago', type: 'quote' },
    { id: 4, title: 'Strand Society subscription expired', subtitle: 'iOS · Monthly', time: '1h ago', type: 'expired' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <TopHeader
        title="Overview"
        subtitle="Thursday, 15 October 2026"
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        actions={
          <button
            className="btn-secondary"
            onClick={() => alert('Exporting dashboard overview CSV...')}
            id="btn-overview-export"
          >
            <Download size={14} />
            <span>Export</span>
          </button>
        }
      />

      <div className="page-body">
        {/* Row 1: 6 Metric Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14 }}>
          {/* Card 1 */}
          <div className="card" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
                Total Subscribers
              </span>
              <span className="badge badge-active" style={{ fontSize: 10.5, padding: '1px 6px' }}>
                +8.2%
              </span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {metrics.totalSubscribers.toLocaleString()}
            </div>
          </div>

          {/* Card 2 */}
          <div className="card" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
                Active
              </span>
              <span className="badge badge-active" style={{ fontSize: 10.5, padding: '1px 6px' }}>
                +6.1%
              </span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {metrics.active.toLocaleString()}
            </div>
          </div>

          {/* Card 3 */}
          <div className="card" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
                On Trial
              </span>
              <span className="badge badge-active" style={{ fontSize: 10.5, padding: '1px 6px' }}>
                +14%
              </span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {metrics.onTrial.toLocaleString()}
            </div>
          </div>

          {/* Card 4 */}
          <div className="card" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
                Expired
              </span>
              <span className="badge badge-disabled" style={{ fontSize: 10.5, padding: '1px 6px' }}>
                -2.3%
              </span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {metrics.expired.toLocaleString()}
            </div>
          </div>

          {/* Card 5 */}
          <div className="card" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
                Quotes / Month
              </span>
              <span className="badge badge-active" style={{ fontSize: 10.5, padding: '1px 6px' }}>
                +11%
              </span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {metrics.quotesMonth.toLocaleString()}
            </div>
          </div>

          {/* Card 6 */}
          <div className="card" style={{ padding: '16px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
                Est. MRR
              </span>
              <span className="badge badge-active" style={{ fontSize: 10.5, padding: '1px 6px' }}>
                +9.4%
              </span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {metrics.estMrr}
            </div>
          </div>
        </div>

        {/* Row 2: Charts (New Subscribers Area Chart + Quotes Per Day Bar Chart) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.7fr 1fr', gap: 20 }}>
          {/* Chart 1: New Subscribers Area Chart */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>New subscribers</h3>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {chartTimeframe === '12m' ? 'Last 12 months' : 'Last 30 days'}
                </p>
              </div>

              <div className="tab-list">
                <button
                  className={`tab-btn ${chartTimeframe === '12m' ? 'active' : ''}`}
                  onClick={() => setChartTimeframe('12m')}
                >
                  12 months
                </button>
                <button
                  className={`tab-btn ${chartTimeframe === '30d' ? 'active' : ''}`}
                  onClick={() => setChartTimeframe('30d')}
                >
                  30 days
                </button>
              </div>
            </div>

            {/* SVG Smooth Area Chart */}
            <div style={{ flex: 1, minHeight: 180, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
              <svg viewBox="0 0 540 160" style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
                <defs>
                  <linearGradient id="berryAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#C2185B" stopOpacity="0.22" />
                    <stop offset="100%" stopColor="#C2185B" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Grid lines */}
                <line x1="0" y1="30" x2="540" y2="30" stroke="#F1F5F9" strokeDasharray="4 4" />
                <line x1="0" y1="80" x2="540" y2="80" stroke="#F1F5F9" strokeDasharray="4 4" />
                <line x1="0" y1="130" x2="540" y2="130" stroke="#F1F5F9" strokeDasharray="4 4" />

                {/* Area under curve */}
                <path
                  d="M 10 130 C 50 120, 90 115, 140 100 C 190 85, 240 90, 290 70 C 340 50, 400 45, 460 30 C 490 22, 515 16, 530 14 L 530 145 L 10 145 Z"
                  fill="url(#berryAreaGrad)"
                />

                {/* Main line */}
                <path
                  d="M 10 130 C 50 120, 90 115, 140 100 C 190 85, 240 90, 290 70 C 340 50, 400 45, 460 30 C 490 22, 515 16, 530 14"
                  fill="none"
                  stroke="var(--primary)"
                  strokeWidth="2.8"
                  strokeLinecap="round"
                />

                {/* End active pulse circle */}
                <circle cx="530" cy="14" r="5" fill="#FFFFFF" stroke="var(--primary)" strokeWidth="3" />
              </svg>

              {/* Month Labels */}
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 4px 0', borderTop: '1px solid #F1F5F9' }}>
                {monthlyPoints.map((pt, i) => (
                  <span key={i} style={{ fontSize: 10.5, color: 'var(--text-light)', fontWeight: 500 }}>
                    {pt.label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Chart 2: Quotes per day Bar Chart */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginBottom: 18 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>Quotes per day</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Last 14 days · avg 353</p>
            </div>

            <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end', gap: 7, height: 160, paddingBottom: 10 }}>
              {dailyQuotes.map((q, idx) => {
                const heightPercent = Math.round((q.val / 500) * 100);
                return (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 4,
                      height: '100%',
                      justifyContent: 'flex-end'
                    }}
                  >
                    <div
                      title={`${q.day}: ${q.val} quotes`}
                      style={{
                        width: '100%',
                        height: `${heightPercent}%`,
                        backgroundColor: q.isToday ? 'var(--primary)' : '#FCE4EC',
                        borderRadius: '3px 3px 0 0',
                        transition: 'all 0.2s',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--primary)';
                      }}
                      onMouseLeave={(e) => {
                        if (!q.isToday) e.currentTarget.style.backgroundColor = '#FCE4EC';
                      }}
                    />
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.5, color: 'var(--text-light)', paddingTop: 8, borderTop: '1px solid #F1F5F9' }}>
              <span>14d</span>
              <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Today · 480</span>
            </div>
          </div>
        </div>

        {/* Row 3: Recent Activity (Left) & Plan Mix / Top Countries (Right) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.7fr 1fr', gap: 20 }}>
          {/* Recent Activity Feed */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>Recent activity</h3>
              <button
                onClick={onNavigateToActivity}
                style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <span>View all</span>
                <ArrowRight size={13} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {recentEvents.map((evt) => (
                <div
                  key={evt.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 0',
                    borderBottom: '1px solid #F8FAFC',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div
                      style={{
                        width: 32,
                        height: 32,
                        borderRadius: 'var(--radius-full)',
                        backgroundColor: 'var(--status-trial-bg)',
                        color: 'var(--primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 13,
                        fontWeight: 700,
                      }}
                    >
                      {evt.type === 'renewed' && '↻'}
                      {evt.type === 'trial' && '✦'}
                      {evt.type === 'quote' && '✎'}
                      {evt.type === 'expired' && '✕'}
                    </div>
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text-heading)' }}>
                        {evt.title}
                      </div>
                      <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                        {evt.subtitle}
                      </div>
                    </div>
                  </div>
                  <span style={{ fontSize: 11.5, color: 'var(--text-light)', fontWeight: 500 }}>
                    {evt.time}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Plan Mix & Top Countries */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)', marginBottom: 10 }}>Plan mix</h3>
              <div style={{ height: 10, width: '100%', borderRadius: 10, overflow: 'hidden', display: 'flex', backgroundColor: '#F1F5F9' }}>
                <div style={{ width: '62%', backgroundColor: 'var(--primary)' }} title="Annual: 62%" />
                <div style={{ width: '38%', backgroundColor: 'var(--gold)' }} title="Monthly: 38%" />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--primary)' }} />
                  <span style={{ color: 'var(--text-body)', fontWeight: 600 }}>Annual · 62%</span>
                  <span style={{ color: 'var(--text-light)' }}>(608)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--gold)' }} />
                  <span style={{ color: 'var(--text-body)', fontWeight: 600 }}>Monthly · 38%</span>
                  <span style={{ color: 'var(--text-light)' }}>(374)</span>
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--card-border)', paddingTop: 16 }}>
              <h4 style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase', marginBottom: 12 }}>
                Top Countries
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  { name: 'United Arab Emirates', pct: 48 },
                  { name: 'Saudi Arabia', pct: 17 },
                  { name: 'United Kingdom', pct: 12 },
                  { name: 'Qatar', pct: 8 },
                ].map((c) => (
                  <div key={c.name}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                      <span style={{ color: 'var(--text-body)', fontWeight: 500 }}>{c.name}</span>
                      <span style={{ color: 'var(--text-heading)', fontWeight: 600 }}>{c.pct}%</span>
                    </div>
                    <div style={{ height: 5, width: '100%', borderRadius: 5, backgroundColor: '#F1F5F9', overflow: 'hidden' }}>
                      <div style={{ width: `${c.pct}%`, height: '100%', backgroundColor: 'var(--primary)', opacity: 0.85 }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
