import React from 'react';
import { Search, Bell } from 'lucide-react';

export default function TopHeader({
  title,
  subtitle,
  searchValue,
  onSearchChange,
  actions,
  notificationCount = 2,
}) {
  return (
    <header className="top-header">
      <div className="header-title-group">
        <h1>{title}</h1>
        {subtitle && <p className="header-subtitle">{subtitle}</p>}
      </div>

      <div className="header-actions">
        {onSearchChange && (
          <div className="search-input-box">
            <Search size={15} />
            <input
              type="text"
              placeholder="Search subscribers, quotes..."
              value={searchValue || ''}
              onChange={(e) => onSearchChange(e.target.value)}
              id="global-search-input"
            />
          </div>
        )}

        <button className="icon-button" title="Notifications" id="btn-notifications">
          <Bell size={16} />
          {notificationCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: 7,
                right: 7,
                width: 7,
                height: 7,
                backgroundColor: 'var(--primary)',
                borderRadius: '50%',
                border: '1.5px solid #FFFFFF',
              }}
            />
          )}
        </button>

        {actions}
      </div>
    </header>
  );
}
