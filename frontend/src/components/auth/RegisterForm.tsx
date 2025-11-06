// frontend/src/components/auth/RegisterForm.tsx
import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';
import PasswordStrength from './PasswordStrength';
import { validatePassword } from '../../utils/validation';
import { PasswordCriteria } from '../../types/validation';

const RegisterForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [code, setCode] = useState(''); // TOEGEVOEGD
  
  const [localError, setLocalError] = useState<string | null>(null);
  const [passwordCriteria, setPasswordCriteria] = useState<PasswordCriteria>({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    specialChar: false,
  });

  const { handleRegister, setAuthMode, isLoading, error: authError, clearError, success: authSuccess, clearSuccess } = useAuth();

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    setPasswordCriteria(validatePassword(newPassword));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();
    clearSuccess();

    if (password !== confirmPassword) {
      setLocalError('Wachtwoorden komen niet overeen.');
      return;
    }

    const isPasswordValid = Object.values(passwordCriteria).every(Boolean);
    if (!isPasswordValid) {
      setLocalError('Wachtwoord voldoet niet aan de criteria.');
      return;
    }

    if (!code) { // TOEGEVOEGD
      setLocalError('Code is verplicht.');
      return;
    }

    try {
      // Pass email, password, confirmPassword, and code
      await handleRegister({ email, password, confirmPassword, code }); // AANGEPAST
      // Success message is handled by useAuth and displayed
      // The form will switch to 'login' on success (handled in useAuth)
    } catch (error: any) {
      // Error is set in useAuth, no local action needed
    }
  };

  const displayError = localError || authError;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-2xl font-semibold text-center">Registreren</h2>

      {displayError && (
        <Alert type="error" message={displayError} onClose={localError ? () => setLocalError(null) : clearError} />
      )}
      
      {authSuccess && (
        <Alert type="success" message={authSuccess} onClose={clearSuccess} />
      )}

      <Input
        id="register-email"
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={isLoading}
        required
      />
      
      <Input
        id="register-password"
        label="Wachtwoord"
        type="password"
        value={password}
        onChange={handlePasswordChange}
        disabled={isLoading}
        required
      />
      
      <PasswordStrength criteria={passwordCriteria} />

      <Input
        id="register-confirm-password"
        label="Bevestig Wachtwoord"
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        disabled={isLoading}
        required
      />

      {/* --- NIEUW VELD --- */}
      <Input
        id="register-code"
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
        {isLoading ? 'Bezig...' : 'Registreren'}
      </Button>

      <div className="text-sm text-center">
        <p className="text-gray-600">
          Al een account?{' '}
          <button
            type="button"
            onClick={() => setAuthMode('login')}
            className="font-medium text-indigo-600 hover:text-indigo-500"
            disabled={isLoading}
          >
            Log hier in
          </button>
        </p>
      </div>
    </form>
  );
};

export default RegisterForm;
