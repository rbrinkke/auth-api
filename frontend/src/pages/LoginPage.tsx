// Minimalist Professional Auth Page
import { useState, Component, ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';

type AuthMode = 'login' | 'register' | 'reset' | 'verify';
type LogType = 'info' | 'success' | 'error';

interface DebugLog {
  time: string;
  type: LogType;
  message: string;
  details?: string;
}

// Error Boundary to prevent blank pages
class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error?: Error }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('[ERROR-BOUNDARY] Caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-white rounded-lg shadow-sm border border-red-200 p-8">
            <h1 className="text-2xl font-semibold text-red-600 mb-4">Something went wrong</h1>
            <p className="text-gray-600 mb-4">The application encountered an error. Please refresh the page.</p>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function LoginPage() {
  console.log('[LOGIN-PAGE] Component rendering, mode:', mode);
  const { login, register, verifyEmail, user } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [logs, setLogs] = useState<DebugLog[]>([]);
  const [error, setError] = useState<string>('');

  const addLog = (type: LogType, message: string, details?: string) => {
    const log: DebugLog = {
      time: new Date().toLocaleTimeString('en-US', { hour12: false }),
      type,
      message,
      details,
    };
    setLogs((prev) => [...prev, log]);
    console.log(`[${log.time}] ${type.toUpperCase()}: ${message}`, details || '');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    addLog('info', `🚀 Starting ${mode.toUpperCase()} process`, `Email: ${email}`);

    try {
      if (mode === 'login') {
        addLog('info', '📤 Sending login request to backend...');
        await login(email, password);
        addLog('success', '✅ Login successful', 'User authenticated');
        toast.success('Welcome back!');
      } else if (mode === 'register') {
        addLog('info', '📤 Sending registration request to backend...', `Email: ${email}`);
        await register(email, password);
        addLog('success', '✅ Registration successful', 'Account created, redirecting to verification');
        toast.success('Account created!');
        addLog('info', '🔄 Switching to VERIFY mode for email verification');
        setMode('verify');
      } else if (mode === 'reset') {
        addLog('info', '📤 Sending password reset request...', `Email: ${email}`);
        addLog('success', '✅ Reset link sent', 'Check your email for the reset link');
        toast.success('Reset link sent to your email');
        addLog('info', '🔄 Switching to VERIFY mode');
        setMode('verify');
      } else if (mode === 'verify') {
        console.log('[VERIFY-PAGE] Mode is VERIFY');
        console.log('[VERIFY-PAGE] Code entered:', code);
        addLog('info', '📤 Sending verification code...', `Code: ${code}`);

        console.log('[VERIFY-PAGE] About to call verifyEmail()');
        try {
          const result = await verifyEmail(code);
          console.log('[VERIFY-PAGE] verifyEmail() returned:', result);
          addLog('success', '✅ Email verified successfully', 'DB updated - you can now login');
          toast.success('Email verified!');
          console.log('[VERIFY-PAGE] Success toast shown');
        } catch (verifyError: any) {
          console.log('[VERIFY-PAGE] verifyEmail() threw error:', verifyError);
          // Don't re-throw - let outer catch handle it
          const statusCode = verifyError.response?.status;
          let errorMsg = verifyError.message || 'Something went wrong';

          if (statusCode === 429) {
            errorMsg = 'Too many requests! Please wait before trying again.';
          } else if (verifyError.response?.data?.detail) {
            errorMsg = verifyError.response.data.detail;
          } else if (statusCode === 400) {
            // Specific handling for wrong verification code
            errorMsg = 'Invalid or expired verification code. Please try again.';
          }

          setError(errorMsg);
          addLog('error', '❌ Verification failed', `Status: ${statusCode} - ${errorMsg}`);
          console.error('Verification error:', verifyError);
          toast.error(errorMsg);
          setIsLoading(false);
          addLog('info', `🏁 VERIFY process completed with error`);
          return; // Exit early, don't continue to outer catch
        }
      }
    } catch (err: any) {
      console.log('[VERIFY-PAGE] Outer catch - handling error:', err);
      const statusCode = err.response?.status;
      let errorMsg = err.message || 'Something went wrong';

      // Special handling for rate limiting
      if (statusCode === 429) {
        errorMsg = 'Too many requests! Please wait before trying again.';
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (statusCode === 400 && mode === 'verify') {
        // Specific handling for wrong verification code
        errorMsg = 'Invalid or expired verification code. Please try again.';
      }

      setError(errorMsg);
      addLog('error', '❌ Request failed', `Status: ${statusCode} - ${errorMsg}`);
      console.error('Auth error:', err);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
      addLog('info', `🏁 ${mode.toUpperCase()} process completed`);
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
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-semibold text-gray-900">{getTitle()}</h1>
            <span className="text-xs text-gray-400 px-2 py-1 bg-gray-100 rounded">
              {mode.toUpperCase()}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (error) setError('');
                }}
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
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError('');
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="••••••••"
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
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
                  onChange={(e) => {
                    setCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                    if (error) setError('');
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl font-mono tracking-widest"
                  placeholder="000000"
                  maxLength={6}
                  required
                />
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-800 font-medium">Error</p>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                  <div className="ml-auto pl-3">
                    <button
                      onClick={() => setError('')}
                      className="text-red-400 hover:text-red-600"
                    >
                      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
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
                  onClick={() => {
                    setError('');
                    addLog('info', '🔄 Switching to REGISTER mode');
                    setMode('register');
                  }}
                  className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Create account
                </button>
                <button
                  onClick={() => {
                    setError('');
                    addLog('info', '🔄 Switching to RESET mode');
                    setMode('reset');
                  }}
                  className="w-full text-sm text-gray-600 hover:text-gray-700"
                >
                  Forgot password?
                </button>
              </>
            )}

            {mode === 'register' && (
              <button
                onClick={() => {
                  setError('');
                  addLog('info', '🔄 Switching to LOGIN mode');
                  setMode('login');
                }}
                className="w-full text-sm text-gray-600 hover:text-gray-700"
              >
                Already have an account? Sign in
              </button>
            )}

            {(mode === 'reset' || mode === 'verify') && (
              <button
                onClick={() => {
                  setError('');
                  addLog('info', '🔄 Switching to LOGIN mode');
                  setMode('login');
                }}
                className="w-full text-sm text-gray-600 hover:text-gray-700"
              >
                Back to sign in
              </button>
            )}
          </div>
        </div>

        {/* Enhanced Debug Console - Always Visible */}
        <div className="mt-4 bg-black rounded-lg p-4 text-green-400 font-mono text-xs max-h-48 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">🔧 Debug Console</span>
              <span className="text-gray-600">|</span>
              <span className="text-gray-500">Mode: <span className="text-yellow-400 font-bold">{mode.toUpperCase()}</span></span>
            </div>
            <button
              onClick={() => setLogs([])}
              className="text-gray-500 hover:text-gray-300"
            >
              Clear
            </button>
          </div>
          <div className="space-y-1">
            {logs.length === 0 ? (
              <div className="text-gray-500 py-2">
                ℹ️ Waiting for actions... Debug logs will appear here
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-gray-500 flex-shrink-0">[{log.time}]</span>
                  <span className="flex-shrink-0">
                    {log.type === 'error' && <span className="text-red-400">❌</span>}
                    {log.type === 'success' && <span className="text-green-400">✅</span>}
                    {log.type === 'info' && <span className="text-blue-400">ℹ️</span>}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="break-words">{log.message}</div>
                    {log.details && (
                      <div className="text-gray-500 mt-0.5 pl-4 border-l border-gray-700 break-words">
                        → {log.details}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}
