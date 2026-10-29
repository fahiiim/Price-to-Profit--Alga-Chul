import React, { useState } from 'react';
import {
  ChevronLeft,
  Gift,
  ShieldAlert,
  DollarSign,
  FileText,
  Package,
  FileCheck2
} from 'lucide-react';
import TopHeader from '../components/TopHeader';

export default function SubscriberDetailPage({
  subscriber,
  onBack,
  onUpdateSubscriber,
}) {
  const [showGrantModal, setShowGrantModal] = useState(false);
  const [showDisableModal, setShowDisableModal] = useState(false);
  const [freeDays, setFreeDays] = useState(30);
  const [internalNote, setInternalNote] = useState(subscriber.internalNote || '');
  const [noteSaved, setNoteSaved] = useState(false);

  const handleGrantFreePeriod = () => {
    const updatedHistory = [
      {
        date: 'Today',
        event: 'Free period granted',
        plan: `${freeDays} days`,
        amount: '—',
        store: 'Admin',
      },
      ...(subscriber.history || []),
    ];

    onUpdateSubscriber(
      {
        ...subscriber,
        status: 'Active',
        history: updatedHistory,
      },
      'grant-free',
      { days: freeDays }
    );
    setShowGrantModal(false);
  };

  const handleToggleAccess = () => {
    const isNowDisabled = subscriber.status !== 'Disabled';
    const newStatus = isNowDisabled ? 'Disabled' : 'Active';
    const newHistory = [
      {
        date: 'Today',
        event: isNowDisabled ? 'Disabled by admin' : 'Re-enabled by admin',
        plan: subscriber.plan,
        amount: '—',
        store: 'Admin',
      },
      ...(subscriber.history || []),
    ];

    onUpdateSubscriber(
      {
        ...subscriber,
        status: newStatus,
        history: newHistory,
      },
      'toggle-status',
      { disabled: isNowDisabled }
    );
    setShowDisableModal(false);
  };

  const handleSaveNote = () => {
    onUpdateSubscriber(
      {
        ...subscriber,
        internalNote,
      },
      'save-note',
      { note: internalNote }
    );
    setNoteSaved(true);
    setTimeout(() => setNoteSaved(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <TopHeader
        title={subscriber.name}
        subtitle="Subscriber dossier & history"
        actions={
          <button className="btn-secondary" onClick={onBack}>
            <ChevronLeft size={16} />
            <span>Back to Subscribers</span>
          </button>
        }
      />

      <div className="page-body">
        {/* Breadcrumbs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)' }}>
          <button
            onClick={onBack}
            style={{ color: 'var(--primary)', fontWeight: 600, padding: 0 }}
          >
            Subscribers
          </button>
          <span>/</span>
          <span style={{ color: 'var(--text-heading)', fontWeight: 600 }}>{subscriber.name}</span>
        </div>

        {/* Business Header Card */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 'var(--radius-lg)',
                backgroundColor: '#1E2330',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                fontWeight: 700,
                letterSpacing: 0.5,
              }}
            >
              {subscriber.initials}
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-heading)' }}>
                  {subscriber.name}
                </h2>
                <span
                  className={`badge ${
                    subscriber.status === 'Active'
                      ? 'badge-active'
                      : subscriber.status === 'Trial'
                      ? 'badge-trial'
                      : subscriber.status === 'Expired'
                      ? 'badge-expired'
                      : 'badge-disabled'
                  }`}
                >
                  {subscriber.status}
                </span>
                <span className="badge badge-gold">
                  {subscriber.plan} — Pro
                </span>
              </div>

              <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 4 }}>
                {subscriber.owner} · {subscriber.email} · {subscriber.phone} · {subscriber.location}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              className="btn-secondary"
              onClick={() => setShowGrantModal(true)}
              id="btn-grant-free-period"
            >
              <Gift size={15} style={{ color: 'var(--primary)' }} />
              <span>Grant free period</span>
            </button>

            <button
              className="btn-danger-outline"
              onClick={() => setShowDisableModal(true)}
              id="btn-toggle-disable-access"
            >
              <ShieldAlert size={15} />
              <span>{subscriber.status === 'Disabled' ? 'Enable access' : 'Disable access'}</span>
            </button>
          </div>
        </div>

        {/* 4 Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-light)', fontSize: 11, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase' }}>
              <FileText size={15} style={{ color: 'var(--primary)' }} />
              <span>Quotes</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {subscriber.quotesCount}
            </div>
          </div>

          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-light)', fontSize: 11, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase' }}>
              <FileCheck2 size={15} style={{ color: 'var(--primary)' }} />
              <span>Invoices</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {subscriber.invoicesCount}
            </div>
          </div>

          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-light)', fontSize: 11, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase' }}>
              <Package size={15} style={{ color: 'var(--primary)' }} />
              <span>Products</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {subscriber.productsCount}
            </div>
          </div>

          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-light)', fontSize: 11, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase' }}>
              <DollarSign size={15} style={{ color: 'var(--gold)' }} />
              <span>Total Quoted</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-heading)', marginTop: 8 }}>
              {subscriber.totalQuoted}
            </div>
          </div>
        </div>

        {/* Two Column Layout: Subscription History Table (Left) & Business Profile (Right) */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
          {/* Subscription History Table */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--card-border)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>
                Subscription history
              </h3>
            </div>

            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Event</th>
                    <th>Plan</th>
                    <th>Amount</th>
                    <th>Store</th>
                  </tr>
                </thead>
                <tbody>
                  {(subscriber.history || []).map((row, idx) => (
                    <tr key={idx}>
                      <td>
                        <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--text-body)' }}>
                          {row.date}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            row.event.includes('Renewed') || row.event.includes('Subscribed')
                              ? 'badge-active'
                              : row.event.includes('Trial')
                              ? 'badge-trial'
                              : row.event.includes('Free')
                              ? 'badge-expired'
                              : 'badge-disabled'
                          }`}
                        >
                          {row.event}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: 12.5, color: 'var(--text-body)' }}>
                          {row.plan}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-heading)' }}>
                          {row.amount}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                          {row.store}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Business Profile Sidebar Card */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-heading)' }}>
              Business profile
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 12.5 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Owner</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.owner}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Phone</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.phone}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Instagram</span>
                <span style={{ fontWeight: 600, color: 'var(--primary)' }}>{subscriber.instagram}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Currency</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.currency}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Default VAT</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.defaultVat}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Default deposit</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.defaultDeposit}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Joined</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.joined}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Device</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.device}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>App version</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{subscriber.appVersion}</span>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--card-border)', paddingTop: 14 }}>
              <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.6, textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                Internal note
              </label>
              <textarea
                value={internalNote}
                onChange={(e) => setInternalNote(e.target.value)}
                rows={3}
                className="input-text"
                style={{ width: '100%', fontSize: 12, resize: 'vertical' }}
                placeholder="Add private staff note..."
              />
              <button
                className="btn-primary"
                onClick={handleSaveNote}
                style={{ marginTop: 8, padding: '6px 14px', fontSize: 11.5 }}
              >
                {noteSaved ? 'Saved!' : 'Save note'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Grant Free Period Modal */}
      {showGrantModal && (
        <div className="modal-overlay" onClick={() => setShowGrantModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-serif" style={{ fontSize: 22, color: 'var(--text-heading)', marginBottom: 8 }}>
              Grant complimentary access
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
              Extend full Pro subscription features for <strong>{subscriber.name}</strong> without charge.
            </p>

            <div className="form-group" style={{ marginBottom: 20 }}>
              <label className="form-label">Duration</label>
              <select
                value={freeDays}
                onChange={(e) => setFreeDays(Number(e.target.value))}
                className="input-text"
              >
                <option value={14}>14 days (VIP Trial extension)</option>
                <option value={30}>30 days (Complimentary masterclass)</option>
                <option value={60}>60 days (Ambassador partner)</option>
                <option value={365}>1 Year (VIP Studio pass)</option>
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button className="btn-secondary" onClick={() => setShowGrantModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleGrantFreePeriod}>
                Grant {freeDays} Days
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disable Access Modal */}
      {showDisableModal && (
        <div className="modal-overlay" onClick={() => setShowDisableModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-serif" style={{ fontSize: 22, color: 'var(--text-heading)', marginBottom: 8 }}>
              {subscriber.status === 'Disabled' ? 'Re-enable account access?' : 'Disable account access?'}
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
              {subscriber.status === 'Disabled'
                ? `This will restore mobile app access for ${subscriber.name}.`
                : `This will immediately revoke active sessions for ${subscriber.name} and block quote generation.`}
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button className="btn-secondary" onClick={() => setShowDisableModal(false)}>
                Cancel
              </button>
              <button className="btn-danger-outline" onClick={handleToggleAccess}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
