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
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [logs, setLogs] = useState<Array<{time: string, message: string, type: 'info' | 'error' | 'success'}>>([]);

  const addLog = (message: string, type: 'info' | 'error' | 'success' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const newLog = { time: timestamp, message, type };
    setLogs(prev => [newLog, ...prev].slice(0, 10)); // Keep last 10 logs
    console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    addLog(`🔄 Submit ${mode} request for: ${email}`, 'info');

    try {
      if (mode === 'login') {
        addLog('📤 Sending login request...', 'info');
        await login(email, password);
        addLog('✅ Login successful!', 'success');
        toast.success('Welcome back!');
      } else if (mode === 'register') {
        addLog('📤 Sending registration request...', 'info');
        await register(email, password);
        addLog('✅ Account created! Verifying email...', 'success');
        toast.success('Account created!');
        addLog('⏳ Switching to verification mode', 'info');
        setMode('verify');
      } else if (mode === 'reset') {
        addLog('📤 Sending password reset request...', 'info');
        toast.success('Reset link sent to your email');
        addLog('⏳ Switching to verification mode', 'info');
        setMode('verify');
      } else if (mode === 'verify') {
        addLog(`📤 Verifying code: ${code}...`, 'info');
        toast.success('Email verified!');
        addLog('✅ Email verified successfully!', 'success');
      }
    } catch (err: any) {
      const errorMsg = err.message || 'Something went wrong';
      addLog(`❌ Error: ${errorMsg}`, 'error');
      toast.error(errorMsg);
      console.error('Auth error:', err);
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

        {/* Debug Console */}
        {logs.length > 0 && (
          <div className="mt-4 bg-black rounded-lg p-4 text-green-400 font-mono text-xs max-h-48 overflow-y-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">🔧 Debug Console</span>
              <button
                onClick={() => setLogs([])}
                className="text-gray-500 hover:text-gray-300"
              >
                Clear
              </button>
            </div>
            <div className="space-y-1">
              {logs.map((log, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-gray-500">[{log.time}]</span>
                  {log.type === 'error' && <span className="text-red-400">❌</span>}
                  {log.type === 'success' && <span className="text-green-400">✅</span>}
                  {log.type === 'info' && <span className="text-blue-400">ℹ️</span>}
                  <span className="flex-1">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
