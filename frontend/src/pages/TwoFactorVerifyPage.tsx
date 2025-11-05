// Premium 2FA Verification Page
import { motion } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheckIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useState } from 'react';
import { toast } from 'sonner';

export function TwoFactorVerifyPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email || '';
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // TODO: Call 2FA verification API
      await new Promise(resolve => setTimeout(resolve, 1000));

      toast.success('Verification successful!');
      navigate('/dashboard');
    } catch (err: any) {
      setError('Invalid code. Please try again.');
      toast.error('Verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    // TODO: Call resend code API
    toast.success('New code sent to your email');
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-violet-950 via-purple-900 to-indigo-900">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-violet-500 opacity-20 blur-3xl"
          animate={{ scale: [1, 1.4, 1], opacity: [0.2, 0.35, 0.2] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-indigo-500 opacity-20 blur-3xl"
          animate={{ scale: [1.3, 1, 1.3], opacity: [0.35, 0.2, 0.35] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
        />
        <motion.div
          className="absolute top-1/3 right-1/3 w-64 h-64 rounded-full bg-purple-500 opacity-10 blur-2xl"
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
        />
      </div>

      <div className="relative z-10 flex min-h-screen items-center justify-center px-6 py-12">
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="glass-card rounded-3xl p-10 shadow-2xl">
            {/* Header */}
            <motion.div
              className="text-center mb-8"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <motion.div
                className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center"
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              >
                <ShieldCheckIcon className="w-10 h-10 text-white" />
              </motion.div>
              <h2 className="text-3xl font-bold text-white mb-2">
                Two-Factor Authentication
              </h2>
              <p className="text-violet-200">
                Enter the 6-digit code sent to{' '}
                <span className="font-semibold text-violet-100">{email}</span>
              </p>
            </motion.div>

            {/* Form */}
            <form onSubmit={handleVerify} className="space-y-6">
              <Input
                label="Verification Code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                className="text-center text-2xl tracking-widest font-mono bg-white/5 border-white/10"
                maxLength={6}
              />

              {error && (
                <motion.div
                  className="p-4 rounded-lg bg-red-500/10 border border-red-500/20"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <p className="text-sm text-red-400 text-center">{error}</p>
                </motion.div>
              )}

              <Button
                type="submit"
                fullWidth
                size="lg"
                isLoading={isLoading}
                className="mt-6 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
              >
                Verify Code
              </Button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={handleResend}
                  className="text-sm text-violet-300 hover:text-violet-200 transition-colors"
                >
                  Didn't receive a code? Resend
                </button>
              </div>
            </form>

            {/* Features */}
            <motion.div
              className="mt-8 pt-8 border-t border-white/10"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <div className="space-y-3">
                {[
                  { icon: '🔒', text: 'Secure verification' },
                  { icon: '⚡', text: 'Code expires in 5 minutes' },
                  { icon: '🛡️', text: 'Enterprise-grade security' },
                ].map((item, index) => (
                  <motion.div
                    key={index}
                    className="flex items-center gap-3 text-violet-200"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                  >
                    <span className="text-xl">{item.icon}</span>
                    <span className="text-sm">{item.text}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
