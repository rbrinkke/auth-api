// Verification Code Page
import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import apiService from '@/services/api';
import { validateTwoFactorCode } from '@/utils/validation';
import { Mail, CheckCircle } from 'lucide-react';

interface LocationState {
  userId: string;
  email: string;
  purpose: 'verify' | 'reset';
  onSuccess?: () => void;
}

export function VerifyCodePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;

  const [code, setCode] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    if (!state?.userId || !state?.email || !state?.purpose) {
      navigate('/login');
    }
  }, [state, navigate]);

  const codeValidation = validateTwoFactorCode(code);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setCode(value);
    if (errors.code) {
      setErrors((prev) => ({ ...prev, code: '' }));
    }
    if (apiError) {
      setApiError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');

    const validation = validateTwoFactorCode(code);
    if (!validation.isValid) {
      setErrors({ code: validation.errors[0] });
      return;
    }

    setIsLoading(true);

    try {
      if (state.purpose === 'verify') {
        await apiService.verifyCode(state.userId, code);
        setIsSuccess(true);

        // Redirect to login after 2 seconds
        setTimeout(() => {
          navigate('/login', {
            state: { message: 'Email verified successfully! You can now login.' }
          });
        }, 2000);
      } else if (state.purpose === 'reset') {
        // Navigate to password reset form with user_id
        navigate('/reset-password', {
          state: {
            userId: state.userId,
            code
          }
        });
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Verification failed. Please try again.';
      setApiError(errorMessage);

      if (errorMessage.includes('lockout')) {
        setErrors({ code: 'Too many failed attempts. Please try again later.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    try {
      await apiService.resendVerification(state.email);
      setApiError('');
      // Show success message
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to resend code. Please try again.';
      setApiError(errorMessage);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
        <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h2>
          <p className="text-gray-600">Redirecting to login page...</p>
        </div>
      </div>
    );
  }

  if (!state?.userId || !state?.email) {
    return null; // or a loading state
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Mail className="w-8 h-8 text-primary-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">
            {state.purpose === 'verify' ? 'Verify Your Email' : 'Reset Your Password'}
          </h2>
          <p className="mt-2 text-gray-600">
            Code sent to {state.email}
          </p>
        </div>

        {apiError && <Alert type="error" message={apiError} onClose={() => setApiError('')} />}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter 6-digit verification code
            </label>
            <input
              type="text"
              value={code}
              onChange={handleChange}
              className={`
                w-full px-4 py-3 text-center text-2xl letter tracking-widest border rounded-lg
                focus:outline-none focus:ring-2 focus:ring-primary-500
                ${errors.code ? 'border-red-300' : 'border-gray-300'}
              `}
              placeholder="000000"
              maxLength={6}
              autoComplete="one-time-code"
            />
            {errors.code && <p className="mt-1 text-sm text-red-600">{errors.code}</p>}
          </div>

          <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
            <p className="font-medium mb-1">💡 Tips:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Check your email for the verification code</li>
              <li>Code expires in 5 minutes</li>
              <li>Enter code without spaces or dashes</li>
            </ul>
          </div>

          <Button type="submit" variant="primary" size="lg" isLoading={isLoading} className="w-full">
            {state.purpose === 'verify' ? 'Verify Email' : 'Continue'}
          </Button>

          <div className="text-center space-y-2">
            <button
              type="button"
              onClick={handleResendCode}
              className="text-sm text-primary-600 hover:text-primary-800 hover:underline"
            >
              Didn't receive a code? Resend
            </button>
            <div>
              <Link
                to="/login"
                className="text-sm text-gray-600 hover:text-gray-800 hover:underline"
              >
                Back to login
              </Link>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
