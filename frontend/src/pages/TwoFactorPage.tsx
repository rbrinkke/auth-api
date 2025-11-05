// Two-Factor Authentication Page
import { useLocation } from 'react-router-dom';
import { TwoFactorForm } from '@/components/auth/TwoFactorForm';

export function TwoFactorPage() {
  const location = useLocation();
  const state = location.state as { userId?: string; email?: string; purpose?: string };

  if (!state?.userId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
        <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Invalid Request</h2>
          <p className="text-gray-600">Please start the login process again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <TwoFactorForm
        userId={state.userId}
        email={state.email}
        purpose={state.purpose as any || 'login'}
      />
    </div>
  );
}
