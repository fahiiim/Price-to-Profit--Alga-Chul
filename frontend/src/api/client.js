// API Client for Price to Profit Backend

const BASE_URL = '/v1';

export const apiClient = {
  getTokens() {
    return {
      accessToken: localStorage.getItem('ptp_admin_access_token'),
      refreshToken: localStorage.getItem('ptp_admin_refresh_token'),
    };
  },

  setTokens(accessToken, refreshToken) {
    if (accessToken) localStorage.setItem('ptp_admin_access_token', accessToken);
    if (refreshToken) localStorage.setItem('ptp_admin_refresh_token', refreshToken);
  },

  clearTokens() {
    localStorage.removeItem('ptp_admin_access_token');
    localStorage.removeItem('ptp_admin_refresh_token');
    localStorage.removeItem('ptp_admin_user');
  },

  async request(endpoint, options = {}) {
    const { accessToken } = this.getTokens();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    try {
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });

      if (res.status === 401 && this.getTokens().refreshToken) {
        // Attempt refresh
        const refreshed = await this.refreshToken();
        if (refreshed) {
          headers['Authorization'] = `Bearer ${this.getTokens().accessToken}`;
          return fetch(`${BASE_URL}${endpoint}`, { ...options, headers });
        }
      }
      return res;
    } catch (err) {
      console.warn(`API call ${endpoint} failed, falling back to local state:`, err);
      return null;
    }
  },

  async login(email, password) {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        this.setTokens(data.access_token, data.refresh_token);
        return { success: true, data };
      }
      return { success: false, error: 'Invalid credentials' };
    } catch (err) {
      console.warn('Backend login connection error, using admin console mode:', err);
      return { success: false, fallback: true };
    }
  },

  async refreshToken() {
    const { refreshToken } = this.getTokens();
    if (!refreshToken) return false;

    try {
      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (res.ok) {
        const data = await res.json();
        this.setTokens(data.access_token, data.refresh_token);
        return true;
      }
    } catch {
      // ignore
    }
    this.clearTokens();
    return false;
  },

  async checkHealth() {
    try {
      const res = await fetch('/health/live');
      return res.ok;
    } catch {
      return false;
    }
  },

  // --- Platform Admin Endpoints ---

  async getPlatformOverview() {
    const res = await this.request('/admin/platform/overview');
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async getPlatformSubscribers(params = {}) {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'All') query.append('status', params.status);
    if (params.plan && params.plan !== 'All') query.append('plan', params.plan);
    if (params.country && params.country !== 'All') query.append('country', params.country);
    if (params.search) query.append('search', params.search);

    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await this.request(`/admin/platform/subscribers${qs}`);
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async getPlatformSubscriber(subscriberId) {
    const res = await this.request(`/admin/platform/subscribers/${subscriberId}`);
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async grantFreePeriod(subscriberId, days = 30) {
    const res = await this.request(`/admin/platform/subscribers/${subscriberId}/grant-free`, {
      method: 'POST',
      body: JSON.stringify({ days }),
    });
    return res && res.ok;
  },

  async toggleSubscriberStatus(subscriberId, disabled) {
    const res = await this.request(`/admin/platform/subscribers/${subscriberId}/toggle-status`, {
      method: 'POST',
      body: JSON.stringify({ disabled }),
    });
    return res && res.ok;
  },

  async updateSubscriberNote(subscriberId, note) {
    const res = await this.request(`/admin/platform/subscribers/${subscriberId}/note`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    });
    return res && res.ok;
  },

  async getPlatformActivity() {
    const res = await this.request('/admin/platform/activity');
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async getPlansConfig() {
    const res = await this.request('/admin/platform/plans');
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async updatePlansConfig(payload) {
    const res = await this.request('/admin/platform/plans', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async getQuoteDefaults() {
    const res = await this.request('/admin/platform/defaults');
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async updateQuoteDefaults(payload) {
    const res = await this.request('/admin/platform/defaults', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async getAppSettings() {
    const res = await this.request('/admin/platform/settings');
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },

  async updateAppSettings(payload) {
    const res = await this.request('/admin/platform/settings', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    if (res && res.ok) {
      return await res.json();
    }
    return null;
  },
};
