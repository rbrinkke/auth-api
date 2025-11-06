// frontend/src/components/auth/PasswordResetForm.tsx
import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';

const PasswordResetForm: React.FC = () => {
  const [step, setStep] = useState(1); // 1: Request, 2: Confirm
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  // const [confirmNewPassword, setConfirmNewPassword] = useState(''); // VERWIJDERD
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { 
    handleRequestReset, 
    handleConfirmReset, 
    setAuthMode, 
    isLoading, 
    error: authError, 
    clearError,
    success: authSuccess,
    clearSuccess
  } = useAuth();

  const handleSubmitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();
    setSuccessMessage(null);
    clearSuccess();

    try {
      await handleRequestReset({ email });
      // Success message is set from useAuth
      setSuccessMessage('Instructies voor wachtwoordherstel zijn naar je e-mail verzonden.');
      setStep(2); // Move to the next step
    } catch (error: any) {
      // Error is set in useAuth
      setLocalError(error.message || 'Er is een fout opgetreden.');
    }
  };

  const handleSubmitConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();
    setSuccessMessage(null);
    clearSuccess();

    try {
      // if (newPassword !== confirmNewPassword) { // VERWIJDERD
      //   throw new Error("Wachtwoorden komen niet overeen.");
      // }
      
      if (!newPassword || !code) { // AANGEPAST
        throw new Error("Code en nieuw wachtwoord zijn verplicht.");
      }

      await handleConfirmReset({ code, newPassword });
      setSuccessMessage("Je wachtwoord is gereset. Je kunt nu inloggen.");
      // Reset fields after successful reset
      setCode('');
      setNewPassword('');
      // setConfirmNewPassword(''); // VERWIJDERD
      
      // Switch to login after a delay
      setTimeout(() => {
        setAuthMode('login');
      }, 3000);

    } catch (error: any) {
      setLocalError(error.message || 'Er is een fout opgetreden.');
      setCode(''); // TOEGEVOEGD: Veld leegmaken bij fout
    }
  };

  const displayError = localError || authError;
  const displaySuccess = successMessage || authSuccess;

  return (
    <div className="space-y-4">
      {step === 1 ? (
        <form onSubmit={handleSubmitRequest} className="space-y-4">
          <h2 className="text-2xl font-semibold text-center">Wachtwoord Resetten</h2>
          
          {displayError && <Alert type="error" message={displayError} onClose={localError ? () => setLocalError(null) : clearError} />}
          {displaySuccess && <Alert type="success" message={displaySuccess} onClose={() => setSuccessMessage(null)} />}

          <p className="text-sm text-gray-600 text-center">
            Voer je e-mailadres in. We sturen je een code om je wachtwoord te resetten.
          </p>
          
          <Input
            id="reset-email"
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
            required
          />
          
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? 'Bezig...' : 'Verstuur Code'}
          </Button>
        </form>
      ) : (
        <form onSubmit={handleSubmitConfirm} className="space-y-4">
          <h2 className="text-2xl font-semibold text-center">Nieuw Wachtwoord</h2>
          
          {displayError && <Alert type="error" message={displayError} onClose={localError ? () => setLocalError(null) : clearError} />}
          {displaySuccess && <Alert type="success" message={displaySuccess} onClose={() => setSuccessMessage(null)} />}

          <p className="text-sm text-gray-600 text-center">
            Voer de code in die je per e-mail hebt ontvangen en kies een nieuw wachtwoord.
          </p>

          <Input
            id="reset-code"
            label="Reset Code"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            disabled={isLoading}
            required
          />

          <Input
            id="reset-new-password"
            label="Nieuw Wachtwoord"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            disabled={isLoading}
            required
          />

          {/* VERWIJDERD: Bevestig Wachtwoord Veld */}
          {/* <Input
            id="reset-confirm-new-password"
            label="Bevestig Nieuw Wachtwoord"
            type="password"
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
            disabled={isLoading}
            required
          /> */}

          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? 'Bezig...' : 'Wachtwoord Instellen'}
          </Button>
        </form>
      )}

      <div className="text-sm text-center">
        <button
          type="button"
          onClick={() => setAuthMode('login')}
          className="font-medium text-indigo-600 hover:text-indigo-500"
          disabled={isLoading}
        >
          Terug naar Inloggen
        </button>
      </div>
    </div>
  );
};

export default PasswordResetForm;
