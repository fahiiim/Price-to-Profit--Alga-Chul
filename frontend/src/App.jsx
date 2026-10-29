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

  // Load Live Dynamic Data from Backend API on Mount
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        const [ovData, subsData, plansData, actsData, defsData, settingsData] =
          await Promise.all([
            apiClient.getPlatformOverview(),
            apiClient.getPlatformSubscribers(),
            apiClient.getPlansConfig(),
            apiClient.getPlatformActivity(),
            apiClient.getQuoteDefaults(),
            apiClient.getAppSettings(),
          ]);

        if (!isMounted) return;

        if (ovData) setMetrics(ovData);
        if (subsData && Array.isArray(subsData) && subsData.length > 0) {
          setSubscribers(subsData);
        }
        if (plansData) setPlansConfig(plansData);
        if (actsData && Array.isArray(actsData) && actsData.length > 0) {
          setActivities(actsData);
        }
        if (defsData) {
          setQuoteDefaults((prev) => ({
            ...prev,
            defaultCurrency: defsData.currency || prev.defaultCurrency,
            defaultTaxRate:
              defsData.tax_rate_percent !== undefined
                ? Number(defsData.tax_rate_percent)
                : prev.defaultTaxRate,
            defaultMarkupRate:
              defsData.default_markup_percent !== undefined
                ? Number(defsData.default_markup_percent)
                : prev.defaultMarkupRate,
            defaultHourlyRate:
              defsData.hourly_rate !== undefined
                ? Number(defsData.hourly_rate)
                : prev.defaultHourlyRate,
            defaultDepositPercent:
              defsData.deposit_value !== undefined
                ? Number(defsData.deposit_value)
                : prev.defaultDepositPercent,
            depositMode:
              defsData.deposit_mode === 'fixed' ? 'Fixed Amount' : 'Percentage',
            quoteValidityDays:
              defsData.quote_validity_days || prev.quoteValidityDays,
            invoiceDueDays:
              defsData.invoice_due_days || prev.invoiceDueDays,
            quoteTerms: defsData.quote_terms || prev.quoteTerms,
            invoiceTerms: defsData.invoice_terms || prev.invoiceTerms,
          }));
        }
        if (settingsData) {
          setAppSettings((prev) => ({
            ...prev,
            supportEmail: settingsData.support_email || prev.supportEmail,
            supportPhone:
              settingsData.support_whatsapp || prev.supportPhone,
            termsUrl: settingsData.terms_url || prev.termsUrl,
            privacyUrl: settingsData.privacy_url || prev.privacyUrl,
            minAppVersion:
              settingsData.minimum_app_version || prev.minAppVersion,
            latestAppVersion:
              settingsData.latest_app_version || prev.latestAppVersion,
            maintenanceMode:
              settingsData.maintenance_mode !== undefined
                ? settingsData.maintenance_mode
                : prev.maintenanceMode,
            maintenanceNotice:
              settingsData.maintenance_message || prev.maintenanceNotice,
          }));
        }
      } catch (err) {
        console.warn('Backend API connection notice, using synchronized local store:', err);
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, []);

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

  // Live Subscriber Updates (Free Period, Disable Access, Note edit)
  const handleUpdateSubscriber = async (updatedSub, actionType, actionPayload) => {
    setSubscribers((prev) =>
      prev.map((s) => (s.id === updatedSub.id ? updatedSub : s))
    );
    setSelectedSubscriber(updatedSub);

    try {
      if (actionType === 'grant-free') {
        await apiClient.grantFreePeriod(updatedSub.id, actionPayload?.days || 30);
      } else if (actionType === 'toggle-status') {
        await apiClient.toggleSubscriberStatus(
          updatedSub.id,
          actionPayload?.disabled !== undefined ? actionPayload.disabled : true
        );
      } else if (actionType === 'save-note') {
        await apiClient.updateSubscriberNote(
          updatedSub.id,
          actionPayload?.note || updatedSub.internalNote
        );
      }

      // Refresh activity log & subscribers list
      const [freshSubs, freshActs] = await Promise.all([
        apiClient.getPlatformSubscribers(),
        apiClient.getPlatformActivity(),
      ]);
      if (freshSubs) setSubscribers(freshSubs);
      if (freshActs) setActivities(freshActs);
    } catch (err) {
      console.warn('Live subscriber update failed, local state retained:', err);
    }
  };

  const handleSavePlans = async (newConfig) => {
    setPlansConfig(newConfig);
    try {
      await apiClient.updatePlansConfig(newConfig);
      const freshActs = await apiClient.getPlatformActivity();
      if (freshActs) setActivities(freshActs);
    } catch (err) {
      console.warn('Live plans update failed:', err);
    }
  };

  const handleSaveQuoteDefaults = async (newDefaults) => {
    setQuoteDefaults(newDefaults);
    try {
      await apiClient.updateQuoteDefaults({
        currency: newDefaults.defaultCurrency,
        tax_label: 'VAT',
        tax_rate_percent: newDefaults.defaultTaxRate,
        hourly_rate: newDefaults.defaultHourlyRate,
        default_markup_percent: newDefaults.defaultMarkupRate,
        deposit_mode:
          newDefaults.depositMode === 'Fixed Amount' ? 'fixed' : 'percentage',
        deposit_value: newDefaults.defaultDepositPercent,
        whole_packs_default: true,
        quote_validity_days: newDefaults.quoteValidityDays,
        invoice_due_days: newDefaults.invoiceDueDays,
        quote_terms: newDefaults.quoteTerms,
        invoice_terms: newDefaults.invoiceTerms,
      });
      const freshActs = await apiClient.getPlatformActivity();
      if (freshActs) setActivities(freshActs);
    } catch (err) {
      console.warn('Live defaults update failed:', err);
    }
  };

  const handleSaveAppSettings = async (newSettings) => {
    setAppSettings(newSettings);
    try {
      await apiClient.updateAppSettings({
        support_email: newSettings.supportEmail,
        support_whatsapp: newSettings.supportPhone,
        terms_url: newSettings.termsUrl,
        privacy_url: newSettings.privacyUrl,
        minimum_app_version: newSettings.minAppVersion,
        latest_app_version: newSettings.latestAppVersion,
        maintenance_mode: newSettings.maintenanceMode,
        maintenance_message: newSettings.maintenanceNotice,
      });
      const freshActs = await apiClient.getPlatformActivity();
      if (freshActs) setActivities(freshActs);
    } catch (err) {
      console.warn('Live app settings update failed:', err);
    }
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
            onSaveConfig={handleSavePlans}
          />
        )}

        {activeTab === 'quote-defaults' && (
          <QuoteDefaultsPage
            quoteDefaults={quoteDefaults}
            onSaveDefaults={handleSaveQuoteDefaults}
          />
        )}

        {activeTab === 'app-settings' && (
          <AppSettingsPage
            appSettings={appSettings}
            onSaveSettings={handleSaveAppSettings}
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
