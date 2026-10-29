import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import SignInPage from './pages/SignInPage';
import OverviewPage from './pages/OverviewPage';
import SubscribersPage from './pages/SubscribersPage';
import SubscriberDetailPage from './pages/SubscriberDetailPage';
import PlansPage from './pages/PlansPage';
import QuoteDefaultsPage from './pages/QuoteDefaultsPage';
import AppSettingsPage from './pages/AppSettingsPage';
import ActivityPage from './pages/ActivityPage';
import {
  INITIAL_METRICS,
  INITIAL_SUBSCRIBERS,
  INITIAL_PLANS_CONFIG,
  INITIAL_QUOTE_DEFAULTS,
  INITIAL_APP_SETTINGS,
  INITIAL_ACTIVITIES,
} from './data/initialData';
import { apiClient } from './api/client';

export default function App() {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('ptp_admin_logged_in') !== 'false';
  });

  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('ptp_admin_user');
    return saved
      ? JSON.parse(saved)
      : {
          name: 'Amna Khan',
          initials: 'AK',
          email: 'amna@pricetoprofit.app',
          role: 'Owner',
        };
  });

  // Navigation State
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedSubscriber, setSelectedSubscriber] = useState(null);

  // Data Stores with LocalStorage Persistence
  const [metrics, setMetrics] = useState(() => {
    const saved = localStorage.getItem('ptp_admin_metrics');
    return saved ? JSON.parse(saved) : INITIAL_METRICS;
  });

  const [subscribers, setSubscribers] = useState(() => {
    const saved = localStorage.getItem('ptp_admin_subscribers');
    return saved ? JSON.parse(saved) : INITIAL_SUBSCRIBERS;
  });

  const [plansConfig, setPlansConfig] = useState(() => {
    const saved = localStorage.getItem('ptp_admin_plans');
    return saved ? JSON.parse(saved) : INITIAL_PLANS_CONFIG;
  });

  const [quoteDefaults, setQuoteDefaults] = useState(() => {
    const saved = localStorage.getItem('ptp_admin_quote_defaults');
    return saved ? JSON.parse(saved) : INITIAL_QUOTE_DEFAULTS;
  });

  const [appSettings, setAppSettings] = useState(() => {
    const saved = localStorage.getItem('ptp_admin_app_settings');
    return saved ? JSON.parse(saved) : INITIAL_APP_SETTINGS;
  });

  const [activities, setActivities] = useState(() => {
    const saved = localStorage.getItem('ptp_admin_activities');
    return saved ? JSON.parse(saved) : INITIAL_ACTIVITIES;
  });

  // Persist State
  useEffect(() => {
    localStorage.setItem('ptp_admin_subscribers', JSON.stringify(subscribers));
  }, [subscribers]);

  useEffect(() => {
    localStorage.setItem('ptp_admin_plans', JSON.stringify(plansConfig));
  }, [plansConfig]);

  useEffect(() => {
    localStorage.setItem('ptp_admin_quote_defaults', JSON.stringify(quoteDefaults));
  }, [quoteDefaults]);

  useEffect(() => {
    localStorage.setItem('ptp_admin_app_settings', JSON.stringify(appSettings));
  }, [appSettings]);

  // Auth Handlers
  const handleSignIn = (userData) => {
    setIsAuthenticated(true);
    setCurrentUser(userData);
    localStorage.setItem('ptp_admin_logged_in', 'true');
    localStorage.setItem('ptp_admin_user', JSON.stringify(userData));
  };

  const handleSignOut = () => {
    setIsAuthenticated(false);
    localStorage.setItem('ptp_admin_logged_in', 'false');
    apiClient.clearTokens();
  };

  // Subscriber Updates (e.g. Free Period, Disable Access, Note edit)
  const handleUpdateSubscriber = (updatedSub) => {
    setSubscribers((prev) =>
      prev.map((s) => (s.id === updatedSub.id ? updatedSub : s))
    );
    setSelectedSubscriber(updatedSub);
  };

  const handleNavigateToSubscriberByName = (businessName) => {
    const found = subscribers.find(
      (s) => s.name.toLowerCase() === businessName.toLowerCase()
    );
    if (found) {
      setSelectedSubscriber(found);
      setActiveTab('subscribers');
    }
  };

  // If unauthenticated, render the full 7.1 Admin - Sign In page
  if (!isAuthenticated) {
    return <SignInPage onSignInSuccess={handleSignIn} />;
  }

  return (
    <div className="app-container">
      {/* Dark Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={(tabId) => {
          setActiveTab(tabId);
          setSelectedSubscriber(null); // Clear selected subscriber when clicking sidebar
        }}
        onSignOut={handleSignOut}
        currentUser={currentUser}
      />

      {/* Main Content Area */}
      <main className="main-wrapper">
        {activeTab === 'overview' && (
          <OverviewPage
            metrics={metrics}
            onNavigateToActivity={() => setActiveTab('activity')}
            onNavigateToSubscribers={() => setActiveTab('subscribers')}
          />
        )}

        {activeTab === 'subscribers' && (
          selectedSubscriber ? (
            <SubscriberDetailPage
              subscriber={selectedSubscriber}
              onBack={() => setSelectedSubscriber(null)}
              onUpdateSubscriber={handleUpdateSubscriber}
            />
          ) : (
            <SubscribersPage
              subscribers={subscribers}
              onSelectSubscriber={(sub) => setSelectedSubscriber(sub)}
            />
          )
        )}

        {activeTab === 'plans' && (
          <PlansPage
            plansConfig={plansConfig}
            onSaveConfig={(newConfig) => setPlansConfig(newConfig)}
          />
        )}

        {activeTab === 'quote-defaults' && (
          <QuoteDefaultsPage
            quoteDefaults={quoteDefaults}
            onSaveDefaults={(newDefaults) => setQuoteDefaults(newDefaults)}
          />
        )}

        {activeTab === 'app-settings' && (
          <AppSettingsPage
            appSettings={appSettings}
            onSaveSettings={(newSettings) => setAppSettings(newSettings)}
          />
        )}

        {activeTab === 'activity' && (
          <ActivityPage
            activities={activities}
            onNavigateToSubscriber={handleNavigateToSubscriberByName}
          />
        )}
      </main>
    </div>
  );
}
