// frontend/src/types/auth.ts
/* eslint-disable @typescript-eslint/no-unused-vars */

// This interface would typically define the user object structure
interface User {
  id: string;
  email: string;
  is_verified: boolean;
  is_2fa_enabled: boolean;
  // add other user properties as needed
}

// Defines the shape of the authentication state
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  // Add any other auth-related state properties
}

// Defines the shape of the authentication context
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  authMode: AuthMode;
  error: string | null;
  success: string | null;
  isLoading: boolean;
  setAuthMode: (mode: AuthMode) => void;
  handleLogin: (data: LoginData) => Promise<void>;
  handleRegister: (data: RegisterData) => Promise<void>;
  handleRequestReset: (data: PasswordResetRequestData) => Promise<void>;
  handleConfirmReset: (data: PasswordResetConfirmData) => Promise<void>;
  handleTwoFactorLogin: (data: TwoFactorLoginData) => Promise<void>;
  handleLogout: () => Promise<void>;
  clearError: () => void;
  clearSuccess: () => void;
}

export type AuthMode = 'login' | 'register' | 'passwordReset' | '2fa';

export interface LoginData {
  email: string;
  password: string;
  code: string;
}

export interface RegisterData {
  email: string;
  password: string;
  confirmPassword: string;
  code: string;
}

export interface LoginResponse {
  message: string;
  user: {
    id: string;
    email: string;
    is_verified: boolean;
    is_2fa_enabled: boolean;
  };
  // No tokens here, login initiates 2FA if needed, or separate call
}

export interface TwoFactorLoginData {
  email: string;
  code: string;
}

export interface TwoFactorLoginResponse {
  access_token: string;
  refresh_token: string;
  message: string;
}


export interface RegisterResponse {
  message: string;
  user: {
    id: string;
    email: string;
    is_verified: boolean;
  };
}

export interface PasswordResetRequestData {
  email: string;
}

export interface PasswordResetConfirmData {
  code: string;
  newPassword: string;
  // confirmNewPassword is validated in the form, not sent
}

export interface RefreshTokenResponse {
  access_token: string;
  message: string;
}

export interface LogoutResponse {
  message: string;
}

export interface ApiError {
  message: string;
  // You might have other properties like 'code' or 'details'
}
