import React from 'react';
import {
  LayoutDashboard,
  Users,
  CreditCard,
  SlidersHorizontal,
  Settings,
  Activity,
  LogOut
} from 'lucide-react';

export default function Sidebar({ activeTab, onSelectTab, onSignOut, currentUser }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'subscribers', label: 'Subscribers', icon: Users },
    { id: 'plans', label: 'Plans', icon: CreditCard },
    { id: 'quote-defaults', label: 'Quote defaults', icon: SlidersHorizontal },
    { id: 'app-settings', label: 'App settings', icon: Settings },
    { id: 'activity', label: 'Activity', icon: Activity },
  ];

  return (
    <aside className="sidebar">
      <div>
        <div className="sidebar-brand" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 6, padding: '4px 8px 20px 8px' }}>
          <img
            src="/gramulate-logo-dark.png"
            alt="Gramulate"
            style={{ height: 28, maxWidth: 180, objectFit: 'contain' }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2 }}>
            <span style={{ fontSize: 10.5, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255, 255, 255, 0.45)', fontWeight: 600 }}>
              Admin Console
            </span>
            <span style={{ fontSize: 9.5, color: '#38A169', background: 'rgba(56, 161, 105, 0.15)', padding: '1px 6px', borderRadius: 4, fontWeight: 700 }}>
              LIVE
            </span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`nav-item ${isActive ? 'active' : ''}`}
                id={`nav-${item.id}`}
              >
                <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="sidebar-user">
        <div className="user-profile">
          <div className="user-avatar">
            {currentUser?.initials || 'AK'}
          </div>
          <div className="user-meta">
            <span className="user-name">{currentUser?.name || 'Amna Khan'}</span>
            <span className="user-role">{currentUser?.role || 'Owner'}</span>
          </div>
        </div>
        <button
          onClick={onSignOut}
          title="Sign out"
          className="logout-btn"
          id="btn-sidebar-signout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
}
