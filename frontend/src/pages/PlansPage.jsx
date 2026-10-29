import React, { useState } from 'react';
import {
  ExternalLink,
  GripVertical,
  X,
  Plus,
  Crown,
  Check,
  Save,
  CheckCircle2
} from 'lucide-react';
import TopHeader from '../components/TopHeader';

export default function PlansPage({
  plansConfig,
  onSaveConfig,
}) {
  const [config, setConfig] = useState(plansConfig);
  const [newBenefit, setNewBenefit] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveToast, setSaveToast] = useState(false);

  const handleAnnualChange = (field, value) => {
    setConfig({
      ...config,
      annual: {
        ...config.annual,
        [field]: value,
      },
    });
  };

  const handleMonthlyChange = (field, value) => {
    setConfig({
      ...config,
      monthly: {
        ...config.monthly,
        [field]: value,
      },
    });
  };

  const handlePaywallChange = (field, value) => {
    setConfig({
      ...config,
      paywall: {
        ...config.paywall,
        [field]: value,
      },
    });
  };

  const handleAddBenefit = () => {
    if (!newBenefit.trim()) return;
    setConfig({
      ...config,
      paywall: {
        ...config.paywall,
        benefits: [...config.paywall.benefits, newBenefit.trim()],
      },
    });
    setNewBenefit('');
  };

  const handleRemoveBenefit = (index) => {
    const updated = config.paywall.benefits.filter((_, idx) => idx !== index);
    setConfig({
      ...config,
      paywall: {
        ...config.paywall,
        benefits: updated,
      },
    });
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      onSaveConfig(config);
      setSaveToast(true);
      setTimeout(() => setSaveToast(false), 2500);
    }, 350);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <TopHeader
        title="Plans & paywall"
        subtitle="How subscription plans appear in the app"
        actions={
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={isSaving}
            id="btn-save-plans"
          >
            <Save size={14} />
            <span>{isSaving ? 'Saving...' : 'Save changes'}</span>
          </button>
        }
      />

      <div className="page-body">
        {/* Info Banner */}
        <div
          style={{
            backgroundColor: '#FEF9C3',
            border: '1px solid #FDE047',
            borderRadius: 'var(--radius-lg)',
            padding: '14px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            fontSize: 13,
            color: '#713F12',
          }}
        >
          <div>
            Prices and free trials are managed in App Store Connect and Google Play Console.
            Here you control how plans are presented on the paywall.
          </div>
          <a
            href="https://appstoreconnect.apple.com"
            target="_blank"
            rel="noreferrer"
            style={{
              color: '#854D0E',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              whiteSpace: 'nowrap',
              textDecoration: 'none',
            }}
          >
            <span>Open App Store Connect</span>
            <ExternalLink size={13} />
          </a>
        </div>

        {/* 2 Plan Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
          {/* Annual Plan Card */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-heading)' }}>
                  {config.annual.displayName}
                </h3>
                {config.annual.badgeText && (
                  <span className="badge badge-gold">{config.annual.badgeText}</span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Show on paywall</span>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={config.annual.showOnPaywall}
                    onChange={(e) => handleAnnualChange('showOnPaywall', e.target.checked)}
                  />
                  <span className="slider" />
                </label>
              </div>
            </div>

            <div>
              <div style={{ fontSize: 26, fontWeight: 700, color: 'var(--primary)' }}>
                {config.annual.priceDisplay}
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--text-light)', marginTop: 2 }}>
                Synced from App Store & Google Play
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
                padding: '12px 14px',
                backgroundColor: '#F8FAFC',
                borderRadius: 'var(--radius-md)',
                fontSize: 12,
              }}
            >
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Product ID</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{config.annual.productId}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Free trial</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{config.annual.freeTrial}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Active subscribers</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{config.annual.activeSubscribers}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Trial→paid conversion</span>
                <span style={{ fontWeight: 600, color: '#16A34A' }}>{config.annual.conversionRate}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div className="form-group">
                <label className="form-label">Display name</label>
                <input
                  type="text"
                  className="input-text"
                  value={config.annual.displayName}
                  onChange={(e) => handleAnnualChange('displayName', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Badge text</label>
                <input
                  type="text"
                  className="input-text"
                  value={config.annual.badgeText}
                  onChange={(e) => handleAnnualChange('badgeText', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Monthly Plan Card */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-heading)' }}>
                  {config.monthly.displayName}
                </h3>
                {config.monthly.badgeText !== '—' && (
                  <span className="badge badge-gold">{config.monthly.badgeText}</span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Show on paywall</span>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={config.monthly.showOnPaywall}
                    onChange={(e) => handleMonthlyChange('showOnPaywall', e.target.checked)}
                  />
                  <span className="slider" />
                </label>
              </div>
            </div>

            <div>
              <div style={{ fontSize: 26, fontWeight: 700, color: 'var(--primary)' }}>
                {config.monthly.priceDisplay}
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--text-light)', marginTop: 2 }}>
                Synced from App Store & Google Play
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
                padding: '12px 14px',
                backgroundColor: '#F8FAFC',
                borderRadius: 'var(--radius-md)',
                fontSize: 12,
              }}
            >
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Product ID</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{config.monthly.productId}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Free trial</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{config.monthly.freeTrial}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Active subscribers</span>
                <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{config.monthly.activeSubscribers}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-light)', display: 'block' }}>Trial→paid conversion</span>
                <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{config.monthly.conversionRate}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div className="form-group">
                <label className="form-label">Display name</label>
                <input
                  type="text"
                  className="input-text"
                  value={config.monthly.displayName}
                  onChange={(e) => handleMonthlyChange('displayName', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Badge text</label>
                <input
                  type="text"
                  className="input-text"
                  value={config.monthly.badgeText}
                  onChange={(e) => handleMonthlyChange('badgeText', e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Paywall Copy (Left) + Live Mobile Preview (Right) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 20 }}>
          {/* Paywall Copy Editor */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-heading)' }}>Paywall copy</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Shown on the subscription screen in the mobile app</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 14 }}>
              <div className="form-group">
                <label className="form-label">Title</label>
                <input
                  type="text"
                  className="input-text"
                  value={config.paywall.title}
                  onChange={(e) => handlePaywallChange('title', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Subtitle</label>
                <input
                  type="text"
                  className="input-text"
                  value={config.paywall.subtitle}
                  onChange={(e) => handlePaywallChange('subtitle', e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Benefits</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {config.paywall.benefits.map((benefit, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      background: '#FFFFFF',
                      border: '1px solid var(--card-border)',
                      borderRadius: 'var(--radius-md)',
                      padding: '8px 12px',
                    }}
                  >
                    <GripVertical size={15} style={{ color: 'var(--text-light)', cursor: 'grab' }} />
                    <span style={{ flex: 1, fontSize: 13, color: 'var(--text-heading)' }}>{benefit}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveBenefit(idx)}
                      style={{ color: 'var(--text-light)', padding: 4 }}
                      title="Remove benefit"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}

                <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                  <input
                    type="text"
                    className="input-text"
                    style={{ flex: 1 }}
                    placeholder="Add custom benefit text..."
                    value={newBenefit}
                    onChange={(e) => setNewBenefit(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddBenefit()}
                  />
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleAddBenefit}
                    style={{ padding: '8px 16px' }}
                  >
                    <Plus size={14} />
                    <span>Add</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Live Mobile Paywall Preview */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-light)', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 16 }}>
              Live Preview
            </span>

            {/* Mobile Device Frame */}
            <div
              style={{
                width: 250,
                background: '#FFFFFF',
                borderRadius: 24,
                border: '2px solid #E2E8F0',
                boxShadow: '0 16px 36px rgba(18, 21, 29, 0.1)',
                padding: '24px 18px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                gap: 14,
              }}
            >
              {/* Crown Icon */}
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  background: 'var(--gold-light)',
                  border: '1.5px solid var(--gold-border)',
                  color: 'var(--gold)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(217, 162, 74, 0.2)',
                }}
              >
                <Crown size={24} />
              </div>

              <div>
                <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-heading)' }}>
                  {config.paywall.title}
                </h4>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  {config.paywall.subtitle}
                </p>
              </div>

              {/* Benefits list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%', textAlign: 'left', marginTop: 4 }}>
                {config.paywall.benefits.map((b, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11.5 }}>
                    <div
                      style={{
                        width: 16,
                        height: 16,
                        borderRadius: '50%',
                        backgroundColor: 'var(--primary)',
                        color: '#FFFFFF',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      <Check size={10} strokeWidth={3} />
                    </div>
                    <span style={{ color: 'var(--text-body)' }}>{b}</span>
                  </div>
                ))}
              </div>

              {/* Call to action */}
              <button
                className="btn-primary"
                style={{
                  width: '100%',
                  justifyContent: 'center',
                  fontSize: 12,
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-full)',
                  marginTop: 8,
                }}
              >
                Start 7-day free trial
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Save Success Toast */}
      {saveToast && (
        <div className="toast">
          <CheckCircle2 size={16} color="#4ADE80" />
          <span>Plans & paywall configuration saved successfully!</span>
        </div>
      )}
    </div>
  );
}
