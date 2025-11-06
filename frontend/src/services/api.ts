// frontend/src/services/api.ts
import axios, { AxiosError } from 'axios';
import { 
  LoginData, 
  RegisterData, 
  PasswordResetRequestData, 
  PasswordResetConfirmData, 
  TwoFactorLoginData,
  LoginResponse,
  RegisterResponse,
  RefreshTokenResponse,
  LogoutResponse,
  TwoFactorLoginResponse
} from '../types/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // This is crucial for handling cookies (like http-only refresh tokens)
});

// Interceptor to handle token refresh
let isRefreshing = false;
let failedQueue: { resolve: (token: string) => void; reject: (error: AxiosError) => void; }[] = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token as string);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any; // Using any to access _retry

    // If the error is 401 and it's not a retry, try to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If refreshing, add to queue
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return axios(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await api.post<RefreshTokenResponse>('/auth/refresh-token');
        const newAccessToken = data.access_token;

        api.defaults.headers.common['Authorization'] = 'Bearer ' + newAccessToken;
        originalRequest.headers['Authorization'] = 'Bearer ' + newAccessToken;
        
        processQueue(null, newAccessToken);
        return axios(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        // If refresh fails, redirect to login
        // This logic might be better handled in a global error handler or auth context
        console.error('Token refresh failed', refreshError);
        // We can't use useAuth hook here, so we might need another way to signal logout
        // For now, just reject the promise
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // For other errors, just reject the promise
    return Promise.reject(error);
  }
);


// Authentication API calls

export const loginUser = async (data: LoginData) => {
  // Sending email, password, AND code
  const response = await api.post<LoginResponse>('/auth/login', {
    email: data.email,
    password: data.password,
    code: data.code // TOEGEVOEGD
  });
  return response.data;
};

export const registerUser = async (data: RegisterData) => {
  // Sending email, password, confirmPassword, AND code
  const response = await api.post<RegisterResponse>('/auth/register', {
    email: data.email,
    password: data.password,
    confirmPassword: data.confirmPassword,
    code: data.code // TOEGEVOEGD
  });
  return response.data;
};

export const requestPasswordReset = async (data: PasswordResetRequestData) => {
  const response = await api.post('/auth/password-reset/request', data);
  return response.data;
};

export const confirmPasswordReset = async (data: PasswordResetConfirmData) => {
  const response = await api.post('/auth/password-reset/confirm', data);
  return response.data;
};

export const twoFactorLogin = async (data: TwoFactorLoginData) => {
  const response = await api.post<TwoFactorLoginResponse>('/auth/2fa/login', data);
  // Store the new access token
  if (response.data.access_token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
  }
  return response.data;
};

export const logoutUser = async () => {
  const response = await api.post<LogoutResponse>('/auth/logout');
  // Clear the authorization header
  delete api.defaults.headers.common['Authorization'];
  return response.data;
};

// Example of a protected route
export const getProtectedData = async () => {
  const response = await api.get('/protected-route'); // Adjust endpoint as needed
  return response.data;
};

export default api;
