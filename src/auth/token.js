import axios from "axios";

const TOKEN_KEY = "auth_token";

export const setAuthToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
  axios.defaults.headers.common.Authorization = `Bearer ${token}`;
};

export const clearAuthToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  delete axios.defaults.headers.common.Authorization;
};

export const loadStoredToken = () => {
  const storedToken = localStorage.getItem(TOKEN_KEY) || "";
  if (storedToken) {
    axios.defaults.headers.common.Authorization = `Bearer ${storedToken}`;
  }
  return storedToken;
};

export const registerAuthInterceptor = (onUnauthorized) => {
  const interceptorId = axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error?.response?.status === 401) {
        clearAuthToken();
        onUnauthorized?.();
      }
      return Promise.reject(error);
    }
  );

  return () => axios.interceptors.response.eject(interceptorId);
};
