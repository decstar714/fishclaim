import axios from "axios";

const ACCESS_TOKEN_KEY = "auth_access_token";
const REFRESH_TOKEN_KEY = "auth_refresh_token";

const applyAccessTokenHeader = (token) => {
  if (token) {
    axios.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common.Authorization;
  }
};

export const parseTokenResponse = (payload = {}) => ({
  accessToken: payload.access_token || "",
  refreshToken: payload.refresh_token || "",
});

export const setSessionTokens = ({ accessToken, refreshToken }) => {
  if (accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    applyAccessTokenHeader(accessToken);
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    applyAccessTokenHeader("");
  }

  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  return {
    accessToken: accessToken || "",
    refreshToken: refreshToken || "",
  };
};

export const clearSession = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  applyAccessTokenHeader("");
};

export const loadStoredSession = () => {
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY) || "";
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY) || "";
  applyAccessTokenHeader(accessToken);
  return { accessToken, refreshToken };
};

export const refreshSession = async (apiBase) => {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }
  const res = await axios.post(`${apiBase}/auth/refresh`, {
    refresh_token: refreshToken,
  });
  const tokens = parseTokenResponse(res.data);
  setSessionTokens(tokens);
  return tokens;
};

export const registerAuthInterceptor = ({
  apiBase,
  onUnauthorized,
  onTokenRefreshed,
} = {}) => {
  let refreshPromise = null;

  const interceptorId = axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      const status = error?.response?.status;
      const originalRequest = error?.config || {};
      const originalUrl = originalRequest?.url || "";
      const isRefreshCall = originalUrl.includes("/auth/refresh");
      const hasRefreshToken = !!localStorage.getItem(REFRESH_TOKEN_KEY);

      if (status === 401 && !originalRequest._retry && !isRefreshCall && hasRefreshToken) {
        originalRequest._retry = true;
        if (!refreshPromise) {
          refreshPromise = refreshSession(apiBase);
        }
        try {
          const tokens = await refreshPromise;
          refreshPromise = null;
          onTokenRefreshed?.(tokens);
          originalRequest.headers = {
            ...(originalRequest.headers || {}),
            Authorization: `Bearer ${tokens.accessToken}`,
          };
          return axios(originalRequest);
        } catch (refreshErr) {
          refreshPromise = null;
          clearSession();
          onUnauthorized?.();
          return Promise.reject(refreshErr);
        }
      }

      if (status === 401) {
        clearSession();
        onUnauthorized?.();
      }

      return Promise.reject(error);
    }
  );

  return () => axios.interceptors.response.eject(interceptorId);
};
