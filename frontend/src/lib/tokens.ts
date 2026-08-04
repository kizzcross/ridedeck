/** Access-token storage. Refresh token is stored separately and only used to
 *  mint new access tokens. (A future hardening step moves refresh to an
 *  httpOnly cookie; the client API is designed so only this module changes.) */
const ACCESS_KEY = "rd_access";
const REFRESH_KEY = "rd_refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};
