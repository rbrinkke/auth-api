// Two-Factor Authentication Form Component
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { validateTwoFactorCode } from '@/utils/validation';
import apiService from '@/services/api';
import { Shield, Smartphone } from 'lucide-react';

interface TwoFactorFormProps {
  userId: string;
  email?: string;
  purpose?: 'login' | 'reset' | 'verify';
}

export function TwoFactorForm({ userId, email, purpose = 'login' }: TwoFactorFormProps) {
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

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
      if (purpose === 'login') {
        const response = await apiService.loginWithTwoFactor({
          user_id: userId,
          code,
        });

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        navigate('/dashboard');
      } else {
        // Handle other purposes (reset, verify)
        await apiService.verifyTwoFactorCode(userId, code, purpose);
        navigate('/success');
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

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
          <Shield className="w-8 h-8 text-primary-600" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900">Two-Factor Verification</h2>
        <p className="mt-2 text-gray-600">
          {email && `Code sent to ${email}`}
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
          Verify & Continue
        </Button>

        <div className="text-center">
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Back to login
          </button>
        </div>
      </form>
    </div>
  );
}
