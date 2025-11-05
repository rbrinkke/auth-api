// API Types for Auth Endpoints

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface LoginResponse extends TokenResponse {}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
}

export interface EmailVerificationRequest {
  token: string;
}

export interface TwoFactorEnableResponse {
  qr_code_url: string;
  backup_codes: string[];
  secret: string;
  message: string;
}

export interface TwoFactorVerifyRequest {
  code: string;
}

export interface TwoFactorLoginRequest {
  user_id: string;
  code: string;
}

export interface TwoFactorVerifySetupResponse {
  verified: boolean;
  message: string;
  session_id?: string;
}

export interface TwoFactorVerifyResponse {
  verified: boolean;
  message?: string;
  session_id?: string;
}

export interface TwoFactorDisableRequest {
  password: string;
  code: string;
}

export interface TwoFactorDisableResponse {
  disabled: boolean;
  message: string;
}

export interface TwoFactorStatusResponse {
  two_factor_enabled: boolean;
}

// Error responses
export interface LoginErrorResponse {
  detail: string;
}

export interface TwoFactorRequiredResponse {
  detail: {
    message: string;
    two_factor_required: true;
    user_id: string;
  };
}

export interface RateLimitError {
  detail: string;
  retry_after?: number;
}
