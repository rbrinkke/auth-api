// frontend/src/components/auth/LoginForm.tsx
import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState(''); // TOEGEVOEGD
  const [localError, setLocalError] = useState<string | null>(null);

  const { handleLogin, setAuthMode, isLoading, error: authError, clearError } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email || !password || !code) { // TOEGEVOEGD
      setLocalError('Alle velden (email, wachtwoord en code) zijn verplicht.');
      return;
    }

    try {
      // Pass email, password, and code
      await handleLogin({ email, password, code }); // AANGEPAST
      // Success is handled by useAuth (e.g., switching to 2FA or setting authenticated)
    } catch (error: any) {
      // Error is already set in useAuth, but we catch to prevent unhandled promise rejection
      // The authError will be displayed by the Alert component
    }
  };

  const displayError = localError || authError;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-2xl font-semibold text-center">Inloggen</h2>
      
      {displayError && (
        <Alert type="error" message={displayError} onClose={localError ? () => setLocalError(null) : clearError} />
      )}

      <Input
        id="login-email"
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={isLoading}
        required
      />
      
      <Input
        id="login-password"
        label="Wachtwoord"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={isLoading}
        required
      />

      {/* --- NIEUW VELD --- */}
      <Input
        id="login-code"
        label="Code"
        type="text"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        disabled={isLoading}
        required
        autoComplete="one-time-code"
      />
      {/* --- EINDE NIEUW VELD --- */}

      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? 'Bezig...' : 'Inloggen'}
      </Button>

      <div className="text-sm text-center">
        <button
          type="button"
          onClick={() => setAuthMode('passwordReset')}
          className="font-medium text-indigo-600 hover:text-indigo-500"
          disabled={isLoading}
        >
          Wachtwoord vergeten?
        </button>
      </div>

      <div className="text-sm text-center">
        <p className="text-gray-600">
          Nog geen account?{' '}
          <button
            type="button"
            onClick={() => setAuthMode('register')}
            className="font-medium text-indigo-600 hover:text-indigo-500"
            disabled={isLoading}
          >
            Registreer hier
          </button>
        </p>
      </div>
    </form>
  );
};

export default LoginForm;
