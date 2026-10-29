import React, { useState } from 'react';
import { Upload, Save, CheckCircle2, RefreshCw } from 'lucide-react';
import TopHeader from '../components/TopHeader';

export default function AppSettingsPage({
  appSettings,
  onSaveSettings,
}) {
  const [settings, setSettings] = useState(appSettings);
  const [isSaving, setIsSaving] = useState(false);
  const [saveToast, setSaveToast] = useState(false);
  const [customLogoPreview, setCustomLogoPreview] = useState(null);

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCustomLogoPreview(event.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSlideChange = (index, value) => {
    const updated = [...settings.onboardingSlides];
    updated[index] = value;
    setSettings({
      ...settings,
      onboardingSlides: updated,
    });
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      onSaveSettings(settings);
      setSaveToast(true);
      setTimeout(() => setSaveToast(false), 2500);
    }, 350);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <TopHeader
        title="App settings & branding"
        subtitle="Global settings for the mobile app"
        actions={
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={isSaving}
            id="btn-save-app-settings"
          >
            <Save size={14} />
            <span>{isSaving ? 'Saving...' : 'Save changes'}</span>
          </button>
        }
      />

      <div className="page-body">
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 20 }}>
          {/* Left Column: Branding & Onboarding */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Branding */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-heading)' }}>
                Branding
              </h3>

              {/* App Icon Upload */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
                <div
                  style={{
                    width: 72,
                    height: 72,
                    borderRadius: 18,
                    background: customLogoPreview
                      ? `url(${customLogoPreview}) center/cover no-repeat`
                      : 'var(--primary-gradient)',
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: 'var(--font-serif)',
                    fontWeight: 700,
                    fontSize: 34,
                    boxShadow: '0 4px 14px rgba(194, 24, 91, 0.35)',
                    flexShrink: 0,
                  }}
                >
                  {!customLogoPreview && 'P'}
                </div>

                <div>
                  <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text-heading)' }}>
                    App icon & logo
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-light)', marginTop: 2 }}>
                    1024 × 1024 PNG, no transparency
                  </div>
                  <label
                    className="btn-secondary"
                    style={{
                      marginTop: 8,
                      display: 'inline-flex',
                      padding: '5px 12px',
                      fontSize: 11.5,
                      cursor: 'pointer',
                    }}
                  >
                    <Upload size={12} />
                    <span>Replace</span>
                    <input
                      type="file"
                      accept="image/png,image/jpeg"
                      style={{ display: 'none' }}
                      onChange={handleLogoUpload}
                    />
                  </label>
                </div>
              </div>

              {/* App Name */}
              <div className="form-group">
                <label className="form-label">App name</label>
                <input
                  type="text"
                  className="input-text"
                  value={settings.appName}
                  onChange={(e) => setSettings({ ...settings, appName: e.target.value })}
                />
              </div>

              {/* Accent Colors */}
              <div className="form-group">
                <label className="form-label">Accent colours</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <input
                      type="color"
                      value={settings.primaryColor}
                      onChange={(e) => setSettings({ ...settings, primaryColor: e.target.value })}
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: 8,
                        border: '1px solid var(--card-border)',
                        cursor: 'pointer',
                        padding: 2,
                      }}
                    />
                    <input
                      type="text"
                      className="input-text"
                      value={settings.primaryColor}
                      onChange={(e) => setSettings({ ...settings, primaryColor: e.target.value })}
                      style={{ width: '100%', fontFamily: 'monospace', fontSize: 12.5 }}
                    />
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <input
                      type="color"
                      value={settings.secondaryColor}
                      onChange={(e) => setSettings({ ...settings, secondaryColor: e.target.value })}
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: 8,
                        border: '1px solid var(--card-border)',
                        cursor: 'pointer',
                        padding: 2,
                      }}
                    />
                    <input
                      type="text"
                      className="input-text"
                      value={settings.secondaryColor}
                      onChange={(e) => setSettings({ ...settings, secondaryColor: e.target.value })}
                      style={{ width: '100%', fontFamily: 'monospace', fontSize: 12.5 }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Onboarding Copy */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-heading)' }}>
                  Onboarding copy
                </h3>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  3 slides shown on first launch
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {settings.onboardingSlides.map((slide, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span
                      style={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        backgroundColor: 'var(--status-trial-bg)',
                        color: 'var(--primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 11.5,
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {idx + 1}
                    </span>
                    <input
                      type="text"
                      className="input-text"
                      style={{ flex: 1 }}
                      value={slide}
                      onChange={(e) => handleSlideChange(idx, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Links & Support + App Control */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Links & Support */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-heading)' }}>
                Links & support
              </h3>

              <div className="form-group">
                <label className="form-label">Support email</label>
                <input
                  type="email"
                  className="input-text"
                  value={settings.supportEmail}
                  onChange={(e) => setSettings({ ...settings, supportEmail: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Terms of use URL</label>
                <input
                  type="url"
                  className="input-text"
                  value={settings.termsUrl}
                  onChange={(e) => setSettings({ ...settings, termsUrl: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Privacy policy URL</label>
                <input
                  type="url"
                  className="input-text"
                  value={settings.privacyUrl}
                  onChange={(e) => setSettings({ ...settings, privacyUrl: e.target.value })}
                />
              </div>
            </div>

            {/* App Control */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-heading)' }}>
                App control
              </h3>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div className="form-label">Maintenance mode</div>
                  <div className="form-sublabel">Shows a "back soon" screen to all users</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={settings.maintenanceMode}
                    onChange={(e) => setSettings({ ...settings, maintenanceMode: e.target.checked })}
                  />
                  <span className="slider" />
                </label>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div className="form-group">
                  <label className="form-label">Minimum app version</label>
                  <input
                    type="text"
                    className="input-text"
                    value={settings.minAppVersion}
                    onChange={(e) => setSettings({ ...settings, minAppVersion: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Latest version</label>
                  <input
                    type="text"
                    className="input-text"
                    value={settings.latestAppVersion}
                    onChange={(e) => setSettings({ ...settings, latestAppVersion: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid var(--card-border)' }}>
                <div>
                  <div className="form-label">Force update</div>
                  <div className="form-sublabel">Users below minimum must update</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={settings.forceUpdate}
                    onChange={(e) => setSettings({ ...settings, forceUpdate: e.target.checked })}
                  />
                  <span className="slider" />
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {saveToast && (
        <div className="toast">
          <CheckCircle2 size={16} color="#4ADE80" />
          <span>App settings & branding saved successfully!</span>
        </div>
      )}
    </div>
  );
}
