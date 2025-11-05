// Validation Utilities
import zxcvbn from 'zxcvbn';
import type {
  PasswordStrength,
  ValidationResult,
  EmailValidationResult,
  PasswordRequirements,
} from '@/types/validation';

// Enterprise-grade password requirements
export const PASSWORD_REQUIREMENTS: PasswordRequirements = {
  minLength: 12,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSpecialChars: true,
  minScore: 3, // Strong password
};

export function validateEmail(email: string): EmailValidationResult {
  const errors: string[] = [];

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!email) {
    errors.push('Email is required');
  } else if (!emailRegex.test(email)) {
    errors.push('Please enter a valid email address');
  } else if (email.length > 254) {
    errors.push('Email address is too long');
  }

  // Additional checks
  const parts = email.split('@');
  if (parts.length !== 2) {
    errors.push('Invalid email format');
  } else {
    const [local, domain] = parts;
    if (local.length > 64) {
      errors.push('Email local part is too long');
    }
    if (domain.length > 255) {
      errors.push('Email domain is too long');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

export function validatePassword(password: string, userInputs?: string[]): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check requirements
  if (password.length < PASSWORD_REQUIREMENTS.minLength) {
    errors.push(`Password must be at least ${PASSWORD_REQUIREMENTS.minLength} characters`);
  }

  if (PASSWORD_REQUIREMENTS.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (PASSWORD_REQUIREMENTS.requireLowercase && !/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (PASSWORD_REQUIREMENTS.requireNumbers && !/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  if (PASSWORD_REQUIREMENTS.requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }

  // Use zxcvbn for strength analysis
  const strength = zxcvbn(password, userInputs);

  // Add zxcvbn feedback
  if (strength.feedback.warning) {
    warnings.push(strength.feedback.warning);
  }

  strength.feedback.suggestions.forEach((suggestion) => {
    warnings.push(suggestion);
  });

  // Check minimum score
  if (strength.score < PASSWORD_REQUIREMENTS.minScore) {
    errors.push(`Password is too weak. Please use a stronger password.`);
  }

  return {
    isValid: errors.length === 0 && strength.score >= PASSWORD_REQUIREMENTS.minScore,
    errors,
    warnings,
    passwordStrength: {
      score: strength.score,
      feedback: strength.feedback,
      crack_times_display: {
        offline_slow_hashing_1e4_per_second: String(strength.crack_times_display.offline_slow_hashing_1e4_per_second),
        offline_fast_hashing_1e10_per_second: String(strength.crack_times_display.offline_fast_hashing_1e10_per_second),
        online_no_throttling_10_per_second: String(strength.crack_times_display.online_no_throttling_10_per_second),
        online_throttling_100_per_hour: String(strength.crack_times_display.online_throttling_100_per_hour),
      },
    },
  };
}

export function validateConfirmPassword(password: string, confirmPassword: string): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (password !== confirmPassword) {
    errors.push('Passwords do not match');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}

export function getPasswordStrengthLabel(score: number): string {
  const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  return labels[score] || 'Unknown';
}

export function getPasswordStrengthColor(score: number): string {
  const colors = ['red', 'red', 'yellow', 'blue', 'green'];
  return colors[score] || 'gray';
}

export function formatCrackTime(timeString: string): string {
  // Convert crack time to more readable format
  if (timeString.includes('centuries')) {
    return 'Centuries';
  }
  if (timeString.includes('years')) {
    return timeString.replace('years', 'years');
  }
  if (timeString.includes('days')) {
    return timeString.replace('days', 'days');
  }
  if (timeString.includes('hours')) {
    return timeString.replace('hours', 'hours');
  }
  if (timeString.includes('minutes')) {
    return timeString.replace('minutes', 'minutes');
  }
  return timeString;
}

export function validateTwoFactorCode(code: string): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!code) {
    errors.push('Verification code is required');
  } else if (!/^\d{6}$/.test(code)) {
    errors.push('Code must be exactly 6 digits');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}
