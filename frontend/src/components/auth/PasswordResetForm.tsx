// Password Reset Form Component
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { PasswordStrengthIndicator } from './PasswordStrength';
import { validatePassword, validateConfirmPassword } from '@/utils/validation';
import apiService from '@/services/api';
import { Lock, KeyRound } from 'lucide-react';

interface LocationState {
  userId?: string;
  code?: string;
}

export function PasswordResetForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;

  const [step, setStep] = useState<'request' | 'reset'>(state?.userId && state?.code ? 'reset' : 'request');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const passwordValidation = validatePassword(formData.password, [formData.email]);

  useEffect(() => {
    // Check if we're on the reset step with code
    if (state?.userId && state?.code) {
      setStep('reset');
    }
  }, [state]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (apiError) {
      setApiError('');
    }
  };

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');

    if (!formData.email) {
      setErrors({ email: 'Email is required' });
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiService.requestPasswordReset({ email: formData.email });
      setSuccessMessage(
        'If an account exists for this email, a password reset code has been sent.'
      );
      // Don't redirect immediately, let user see the message
    } catch (error: any) {
      setApiError(error.response?.data?.detail || 'Request failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');

    const newErrors: Record<string, string> = {};

    if (!passwordValidation.isValid) {
      newErrors.password = passwordValidation.errors[0];
    }

    const confirmResult = validateConfirmPassword(formData.password, formData.confirmPassword);
    if (!confirmResult.isValid) {
      newErrors.confirmPassword = confirmResult.errors[0];
    }

    if (!state?.userId || !state?.code) {
      newErrors.code = 'Invalid reset code';
    }

    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    setIsLoading(true);

    try {
      await apiService.resetPassword({
        user_id: state.userId!,
        code: state.code!,
        new_password: formData.password,
      });

      setSuccessMessage('Password reset successfully! You can now log in with your new password.');
      setTimeout(() => navigate('/login'), 3000);
    } catch (error: any) {
      setApiError(error.response?.data?.detail || 'Password reset failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
          <Lock className="w-8 h-8 text-primary-600" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900">
          {step === 'request' ? 'Reset Password' : 'Set New Password'}
        </h2>
      </div>

      {apiError && <Alert type="error" message={apiError} onClose={() => setApiError('')} />}

      {successMessage && <Alert type="success" message={successMessage} />}

      {step === 'request' ? (
        <form onSubmit={handleRequestSubmit} className="space-y-4">
          <p className="text-sm text-gray-600 mb-4">
            Enter your email address and we'll send you a code to reset your password.
          </p>

          <Input
            label="Email Address"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            error={errors.email}
            placeholder="you@example.com"
            autoComplete="email"
            required
          />

          <Button type="submit" variant="primary" size="lg" isLoading={isLoading} className="w-full">
            Send Reset Code
          </Button>

          <p className="text-center text-sm text-gray-600">
            Remember your password?{' '}
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Sign in
            </button>
          </p>

          <div className="text-center">
            <p className="text-xs text-gray-500">
              After receiving the code, you'll need to enter it to continue.
            </p>
          </div>
        </form>
      ) : (
        <form onSubmit={handleResetSubmit} className="space-y-4">
          <Input
            label="New Password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            error={errors.password}
            placeholder="••••••••••••"
            autoComplete="new-password"
            required
          />

          {formData.password && (
            <PasswordStrengthIndicator
              password={formData.password}
              strength={passwordValidation.passwordStrength}
            />
          )}

          <Input
            label="Confirm New Password"
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleChange}
            error={errors.confirmPassword}
            placeholder="••••••••••••"
            autoComplete="new-password"
            required
          />

          <Button type="submit" variant="primary" size="lg" isLoading={isLoading} className="w-full">
            Reset Password
          </Button>
        </form>
      )}
    </div>
  );
}
