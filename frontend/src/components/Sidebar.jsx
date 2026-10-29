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
        <div className="sidebar-brand">
          <div className="brand-icon">P</div>
          <div className="brand-info">
            <span className="brand-title">Price to Profit</span>
            <span className="brand-badge">Admin Console</span>
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
