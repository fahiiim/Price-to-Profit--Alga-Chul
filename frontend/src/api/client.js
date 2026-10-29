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
  }
};
