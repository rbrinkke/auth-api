// API Service Layer
import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  ApiError,
  PasswordResetRequest,
  PasswordResetConfirmRequest,
  EmailVerificationRequest,
  TwoFactorEnableResponse,
  TwoFactorVerifyRequest,
  TwoFactorLoginRequest,
  TwoFactorVerifySetupResponse,
  TwoFactorVerifyResponse,
  TwoFactorDisableRequest,
  TwoFactorDisableResponse,
  TwoFactorStatusResponse,
  TwoFactorRequiredResponse,
} from '@/types/auth';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.refreshToken(refreshToken);
              const { access_token } = response.data;
              localStorage.setItem('access_token', access_token);

              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.logout();
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async register(data: RegisterRequest) {
    return this.api.post<TokenResponse>('/auth/register', data);
  }

  async login(data: LoginRequest) {
    return this.api.post<TokenResponse | TwoFactorRequiredResponse>('/auth/login', data);
  }

  async verifyCode(userId: string, code: string) {
    return this.api.post('/auth/verify-code', { user_id: userId, code });
  }

  async resendVerification(email: string) {
    return this.api.post('/auth/resend-verification', { email });
  }

  async requestPasswordReset(data: PasswordResetRequest) {
    return this.api.post('/auth/request-password-reset', data);
  }

  async resetPassword(data: { user_id: string; code: string; new_password: string }) {
    return this.api.post('/auth/reset-password', data);
  }

  async refreshToken(refreshToken: string) {
    return this.api.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken });
  }

  async logout() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await this.api.post('/auth/logout', { refresh_token: refreshToken });
      } catch (error) {
        // Ignore logout errors
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // Two-factor authentication endpoints
  async enableTwoFactor() {
    return this.api.post<TwoFactorEnableResponse>('/auth/enable-2fa');
  }

  async verifyTwoFactorSetup(data: TwoFactorVerifyRequest) {
    return this.api.post<TwoFactorVerifySetupResponse>('/auth/verify-2fa-setup', data);
  }

  async loginWithTwoFactor(data: TwoFactorLoginRequest) {
    return this.api.post<TokenResponse>('/auth/login-2fa', data);
  }

  async verifyTwoFactorCode(userId: string, code: string, purpose: string) {
    return this.api.post<TwoFactorVerifyResponse>('/auth/verify-2fa', {
      user_identifier: userId,
      code,
      purpose,
    });
  }

  async disableTwoFactor(data: TwoFactorDisableRequest) {
    return this.api.post<TwoFactorDisableResponse>('/auth/disable-2fa', data);
  }

  async getTwoFactorStatus() {
    return this.api.get<TwoFactorStatusResponse>('/auth/2fa-status');
  }

  // Health check
  async healthCheck() {
    return this.api.get('/health');
  }

  // Get API instance for custom requests
  getApi() {
    return this.api;
  }
}

export const apiService = new ApiService();
export default apiService;
