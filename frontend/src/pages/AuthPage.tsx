import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import apiService from '@/services/api';

type AuthMode = 'login' | 'register' | 'reset';

export function AuthPage() {
  const { login, register, user } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [codeVerified, setCodeVerified] = useState(false);
  const [resetUserId, setResetUserId] = useState<string>('');

  const handleEmailChange = (value: string) => {
    setEmail(value);
    setError('');
  };

  const handleSendResetLink = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const response = await apiService.requestPasswordReset({ email });
      setResetUserId(response.data.user_id);
      setCodeSent(true);
      setPassword(''); // Clear password field
    } catch (err: any) {
      setError('Failed to send reset code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCodeChange = async (value: string) => {
    setCode(value);
    setError('');

    // Auto-verify code when it's 6 digits and code is sent
    if (mode === 'reset' && codeSent && value.length === 6 && !codeVerified) {
      try {
        await apiService.verifyCode(resetUserId, value);
        setCodeVerified(true);
        setPassword(''); // Clear password field for new password
      } catch (err: any) {
        setError('Invalid or expired code. Please try again.');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      if (mode === 'login') {
        // Login with email + password
        await login(email, password);
      } else if (mode === 'register') {
        // Register with email + password
        await register(email, password);
        // After register, verify with code
        if (code && user?.pendingVerificationId) {
          await apiService.verifyCode(user.pendingVerificationId, code);
        }
        setMode('login');
        setPassword('');
        setCode('');
      } else if (mode === 'reset') {
        // Reset with user_id + code + new password
        await apiService.resetPassword({
          user_id: resetUserId,
          code,
          new_password: password
        });
        setMode('login');
        setPassword('');
        setCode('');
        setCodeSent(false);
        setCodeVerified(false);
        setResetUserId('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setCode('');
    setError('');
    setCodeSent(false);
    setCodeVerified(false);
    setResetUserId('');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">
          {mode === 'login' ? 'Sign In' : mode === 'register' ? 'Create Account' : 'Reset Password'}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => handleEmailChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="you@example.com"
              required
            />
          </div>

          {/* Password field for register mode always, reset mode always */}
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError('');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="••••••••"
                required
              />
            </div>
          )}

          {/* Password field for reset mode - always visible with clear placeholder */}
          {mode === 'reset' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError('');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Choose a new password"
                required
              />
            </div>
          )}

          {/* Verification Code field */}
          {mode !== 'login' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Verification Code
                {mode === 'reset' && codeSent && !codeVerified && (
                  <span className="text-sm text-gray-500 ml-2">(sent to your email)</span>
                )}
              </label>
              <input
                type="text"
                value={code}
                onChange={(e) => handleCodeChange(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-center text-xl font-mono tracking-widest"
                placeholder="000000"
                maxLength={6}
                required
                disabled={mode === 'reset' && codeVerified}
              />
            </div>
          )}

          {/* Success Messages */}
          {mode === 'reset' && codeSent && !codeVerified && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center">
                <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-green-800">
                  ✓ Mail sent! Check your email for the 6-digit code
                </p>
              </div>
            </div>
          )}

          {mode === 'reset' && codeVerified && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center">
                <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-green-800">
                  ✓ Code verified! Enter your new password below
                </p>
              </div>
            </div>
          )}

          {mode === 'reset' && codeSent && !codeVerified && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800">
                👉 Step 1: Enter the 6-digit code from your email
              </p>
            </div>
          )}

          {/* Instruction Messages */}
          {mode === 'reset' && codeSent && !codeVerified && (
            <p className="text-sm text-gray-600">
              Enter the 6-digit code from your email
            </p>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Submit Button */}
          {mode === 'reset' && !codeSent ? (
            <button
              type="button"
              onClick={handleSendResetLink}
              disabled={isLoading || !email}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Sending...' : 'Send Reset Link'}
            </button>
          ) : (
            <button
              type="submit"
              disabled={isLoading || (mode === 'reset' && !codeVerified)}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Please wait...' :
                mode === 'login' ? 'Sign In' :
                mode === 'register' ? 'Create Account' : 'Reset Password'}
            </button>
          )}
        </form>

        <div className="mt-6 space-y-2 text-sm">
          {mode === 'login' && (
            <>
              <button
                onClick={() => setMode('register')}
                className="w-full text-blue-600 hover:text-blue-700"
              >
                Create account
              </button>
              <button
                onClick={() => {
                  setMode('reset');
                  resetForm();
                }}
                className="w-full text-gray-600 hover:text-gray-700"
              >
                Forgot password?
              </button>
            </>
          )}

          {(mode === 'register' || mode === 'reset') && (
            <button
              onClick={() => {
                setMode('login');
                resetForm();
              }}
              className="w-full text-gray-600 hover:text-gray-700"
            >
              Back to sign in
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
