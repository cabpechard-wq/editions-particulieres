/* shared auth helpers — inject AUTH_API via __AUTH_API__ */
window.FLIPCARDS_AUTH = {
  baseUrl: "__AUTH_API__",
  tokenKey: "flipcards_token",
  getToken() {
    return sessionStorage.getItem(this.tokenKey) || localStorage.getItem(this.tokenKey) || "";
  },
  setToken(token, remember) {
    sessionStorage.setItem(this.tokenKey, token);
    sessionStorage.setItem("flipcards_ok", "1");
    if (remember) localStorage.setItem(this.tokenKey, token);
    else localStorage.removeItem(this.tokenKey);
  },
  clearToken() {
    sessionStorage.removeItem(this.tokenKey);
    sessionStorage.removeItem("flipcards_ok");
    localStorage.removeItem(this.tokenKey);
  },
  async api(path, opts = {}) {
    const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    const token = this.getToken();
    if (token && !headers.Authorization) headers.Authorization = "Bearer " + token;
    const base = String(this.baseUrl || "").replace(/\/$/, "");
    const res = await fetch(base + path, {
      method: opts.method || "GET",
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    let data = {};
    try {
      data = await res.json();
    } catch (_) {}
    if (!res.ok) {
      const err = new Error(data.error || "Erreur " + res.status);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  },
  async requireSession() {
    const token = this.getToken();
    if (!token) return null;
    try {
      return await this.api("/api/me");
    } catch (_) {
      this.clearToken();
      return null;
    }
  },
};
