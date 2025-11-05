// Password Reset Page
import { PasswordResetForm } from '@/components/auth/PasswordResetForm';

export function PasswordResetPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <PasswordResetForm />
    </div>
  );
}
