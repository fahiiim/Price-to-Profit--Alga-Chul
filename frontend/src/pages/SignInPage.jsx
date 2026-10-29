import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, ArrowRight } from 'lucide-react';

export default function SignInPage({ onSignInSuccess }) {
  const [email, setEmail] = useState('amna@pricetoprofit.app');
  const [password, setPassword] = useState('••••••••••••');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');

    setTimeout(() => {
      setIsLoading(false);
      onSignInSuccess({
        name: 'Amna Khan',
        initials: 'AK',
        email: email,
        role: 'Owner'
      });
    }, 450);
  };

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden' }}>
      {/* Left Hero Column */}
      <div
        style={{
          flex: '1.1',
          background: 'var(--hero-gradient)',
          color: '#FFFFFF',
          padding: '48px 56px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <img
              src="/gramulate-logo-dark.png"
              alt="Gramulate"
              style={{ height: 38, objectFit: 'contain' }}
            />
          </div>

          <div style={{ marginTop: '12vh', maxWidth: 460 }}>
            <h1
              className="font-serif"
              style={{
                fontSize: 44,
                lineHeight: 1.15,
                fontWeight: 500,
                letterSpacing: -0.5,
                color: '#FFFFFF',
              }}
            >
              Run your quoting platform beautifully.
            </h1>
            <p
              style={{
                marginTop: 18,
                fontSize: 16,
                lineHeight: 1.5,
                color: 'rgba(255, 255, 255, 0.85)',
                fontWeight: 400,
              }}
            >
              Manage subscribers, plans and app-wide defaults — all in one place.
            </p>
          </div>
        </div>

        {/* Bottom 3 Stat Pill Cards */}
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.12)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 'var(--radius-lg)',
              padding: '14px 20px',
              minWidth: 120,
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 700, color: '#FFFFFF' }}>1,248</div>
            <div style={{ fontSize: 11.5, color: 'rgba(255, 255, 255, 0.75)', marginTop: 2 }}>Subscribers</div>
          </div>

          <div
            style={{
              background: 'rgba(255, 255, 255, 0.12)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 'var(--radius-lg)',
              padding: '14px 20px',
              minWidth: 130,
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 700, color: '#FFFFFF' }}>8,412</div>
            <div style={{ fontSize: 11.5, color: 'rgba(255, 255, 255, 0.75)', marginTop: 2 }}>Quotes this month</div>
          </div>

          <div
            style={{
              background: 'rgba(255, 255, 255, 0.12)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 'var(--radius-lg)',
              padding: '14px 20px',
              minWidth: 130,
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 700, color: '#FFFFFF' }}>AED 24.9k</div>
            <div style={{ fontSize: 11.5, color: 'rgba(255, 255, 255, 0.75)', marginTop: 2 }}>Est. MRR</div>
          </div>
        </div>
      </div>

      {/* Right Sign-in Form Column */}
      <div
        style={{
          flex: '1',
          background: 'var(--canvas-bg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 32,
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 420,
            background: '#FFFFFF',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid var(--card-border)',
            boxShadow: '0 8px 30px rgba(18, 21, 29, 0.06)',
            padding: '38px 36px',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <img
              src="/gramulate-logo.png"
              alt="Gramulate"
              style={{ height: 42, objectFit: 'contain', margin: '0 auto 16px auto', display: 'block' }}
            />
            <h2
              className="font-serif"
              style={{
                fontSize: 26,
                color: 'var(--text-heading)',
                fontWeight: 500,
                letterSpacing: -0.3,
              }}
            >
              Welcome back
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 6 }}>
              Sign in to the Gramulate admin console.
            </p>
          </div>

          {errorMsg && (
            <div
              style={{
                background: 'var(--status-disabled-bg)',
                color: 'var(--status-disabled-text)',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                fontSize: 13,
                marginBottom: 16,
              }}
            >
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="input-admin-email">Email</label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Mail
                  size={16}
                  style={{ position: 'absolute', left: 14, color: 'var(--text-light)', pointerEvents: 'none' }}
                />
                <input
                  id="input-admin-email"
                  type="email"
                  className="input-text"
                  style={{ width: '100%', paddingLeft: 40 }}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="input-admin-password">Password</label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Lock
                  size={16}
                  style={{ position: 'absolute', left: 14, color: 'var(--text-light)', pointerEvents: 'none' }}
                />
                <input
                  id="input-admin-password"
                  type={showPassword ? 'text' : 'password'}
                  className="input-text"
                  style={{ width: '100%', paddingLeft: 40, paddingRight: 40 }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ position: 'absolute', right: 12, color: 'var(--text-light)', padding: 4 }}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12.5 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 7, cursor: 'pointer', color: 'var(--text-body)' }}>
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  style={{ accentColor: 'var(--primary)', width: 15, height: 15 }}
                />
                <span>Remember me</span>
              </label>

              <button
                type="button"
                onClick={() => alert('Password reset email sent to ' + email)}
                style={{ color: 'var(--primary)', fontWeight: 600, fontSize: 12.5 }}
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              className="btn-primary"
              id="btn-admin-submit"
              disabled={isLoading}
              style={{
                width: '100%',
                justifyContent: 'center',
                padding: '12px',
                borderRadius: 'var(--radius-md)',
                marginTop: 6,
                fontSize: 14,
              }}
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p
            style={{
              textAlign: 'center',
              fontSize: 11.5,
              color: 'var(--text-light)',
              marginTop: 26,
            }}
          >
            Admin access only · Subscribers use the mobile app
          </p>
        </div>
      </div>
    </div>
  );
}
