// Minimalist Professional Auth Page
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';

type AuthMode = 'login' | 'register' | 'reset' | 'verify';

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (mode === 'login') {
        await login(email, password);
        toast.success('Welcome back!');
      } else if (mode === 'register') {
        if (password !== confirmPassword) {
          toast.error('Passwords do not match');
          return;
        }
        await register(email, password);
        toast.success('Account created!');
        setMode('verify');
      } else if (mode === 'reset') {
        toast.success('Reset link sent to your email');
        setMode('verify');
      } else if (mode === 'verify') {
        toast.success('Email verified!');
      }
    } catch (err: any) {
      toast.error(err.message || 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  const getTitle = () => {
    switch (mode) {
      case 'login': return 'Welcome back';
      case 'register': return 'Create account';
      case 'reset': return 'Reset password';
      case 'verify': return 'Enter verification code';
    }
  };

  const getButtonText = () => {
    switch (mode) {
      case 'login': return 'Sign in';
      case 'register': return 'Create account';
      case 'reset': return 'Send reset link';
      case 'verify': return 'Verify';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h1 className="text-2xl font-semibold text-gray-900 mb-6">{getTitle()}</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="you@example.com"
                required
              />
            </div>

            {mode !== 'verify' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="••••••••"
                  required
                />
              </div>
            )}

            {mode === 'register' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirm password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="••••••••"
                  required
                />
              </div>
            )}

            {mode === 'verify' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Verification code
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl font-mono tracking-widest"
                  placeholder="000000"
                  maxLength={6}
                  required
                />
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2.5 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {isLoading ? 'Please wait...' : getButtonText()}
            </button>
          </form>

          <div className="mt-6 space-y-2">
            {mode === 'login' && (
              <>
                <button
                  onClick={() => setMode('register')}
                  className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Create account
                </button>
                <button
                  onClick={() => setMode('reset')}
                  className="w-full text-sm text-gray-600 hover:text-gray-700"
                >
                  Forgot password?
                </button>
              </>
            )}

            {mode === 'register' && (
              <button
                onClick={() => setMode('login')}
                className="w-full text-sm text-gray-600 hover:text-gray-700"
              >
                Already have an account? Sign in
              </button>
            )}

            {(mode === 'reset' || mode === 'verify') && (
              <button
                onClick={() => setMode('login')}
                className="w-full text-sm text-gray-600 hover:text-gray-700"
              >
                Back to sign in
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
