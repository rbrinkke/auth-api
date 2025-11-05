// Premium Registration Page with Animated Background
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { EnvelopeIcon, LockClosedIcon, UserIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      toast.error('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      toast.error('Password too short');
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password);
      toast.success('Account created! Please verify your email.');
      navigate('/verify-email', { state: { email } });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
      toast.error('Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-emerald-950 via-teal-900 to-cyan-900">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-emerald-500 opacity-20 blur-3xl"
          animate={{ scale: [1, 1.3, 1], opacity: [0.2, 0.3, 0.2] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-cyan-500 opacity-20 blur-3xl"
          animate={{ scale: [1.2, 1, 1.2], opacity: [0.3, 0.2, 0.3] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 3 }}
        />
      </div>

      <div className="relative z-10 flex min-h-screen">
        {/* Left side - Form */}
        <div className="flex-1 flex items-center justify-center px-6 py-12 lg:px-8">
          <motion.div
            className="w-full max-w-md"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="glass-card rounded-3xl p-10 shadow-2xl">
              <motion.div
                className="text-center mb-8"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <h2 className="text-3xl font-bold text-white mb-2">
                  Create Account
                </h2>
                <p className="text-emerald-200">
                  Already have an account?{' '}
                  <Link
                    to="/login"
                    className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Sign in →
                  </Link>
                </p>
              </motion.div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <Input
                  label="Full Name"
                  type="text"
                  leftIcon={<UserIcon className="w-5 h-5" />}
                  placeholder="John Doe"
                  required
                  className="bg-white/5 border-white/10"
                />

                <Input
                  label="Email Address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  leftIcon={<EnvelopeIcon className="w-5 h-5" />}
                  placeholder="you@company.com"
                  required
                  autoComplete="email"
                  className="bg-white/5 border-white/10"
                />

                <Input
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  leftIcon={<LockClosedIcon className="w-5 h-5" />}
                  placeholder="••••••••"
                  required
                  autoComplete="new-password"
                  helperText="At least 8 characters"
                  className="bg-white/5 border-white/10"
                />

                <Input
                  label="Confirm Password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  leftIcon={<LockClosedIcon className="w-5 h-5" />}
                  placeholder="••••••••"
                  required
                  autoComplete="new-password"
                  className="bg-white/5 border-white/10"
                />

                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1 w-4 h-4 rounded border-white/20 bg-white/5 text-emerald-600 focus:ring-emerald-500"
                    required
                  />
                  <p className="text-sm text-emerald-200">
                    I agree to the{' '}
                    <Link to="/terms" className="text-emerald-400 hover:text-emerald-300 underline">
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link to="/privacy" className="text-emerald-400 hover:text-emerald-300 underline">
                      Privacy Policy
                    </Link>
                  </p>
                </div>

                {error && (
                  <motion.div
                    className="p-4 rounded-lg bg-red-500/10 border border-red-500/20"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                  >
                    <p className="text-sm text-red-400">{error}</p>
                  </motion.div>
                )}

                <Button
                  type="submit"
                  fullWidth
                  size="lg"
                  isLoading={isLoading}
                  className="mt-6 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                >
                  Create Account
                </Button>
              </form>
            </div>
          </motion.div>
        </div>

        {/* Right side - Branding */}
        <motion.div
          className="hidden lg:flex lg:flex-1 flex-col justify-center px-12 xl:px-24"
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <h1 className="text-5xl xl:text-6xl font-bold text-white mb-6">
              Join Our Community
            </h1>
            <p className="text-xl text-emerald-200 mb-8 leading-relaxed">
              Create your account and unlock a world of possibilities.
              Secure, fast, and effortless registration.
            </p>
            <div className="grid grid-cols-2 gap-4">
              {[
                { icon: '✅', title: 'Easy Signup', desc: 'Quick & simple' },
                { icon: '🔒', title: 'Secure', desc: 'Enterprise-grade' },
                { icon: '⚡', title: 'Fast', desc: 'Lightning quick' },
                { icon: '🎯', title: 'Smart', desc: '2FA enabled' },
              ].map((item, index) => (
                <motion.div
                  key={index}
                  className="glass-card rounded-xl p-6"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                >
                  <div className="text-3xl mb-2">{item.icon}</div>
                  <h3 className="font-semibold text-white mb-1">{item.title}</h3>
                  <p className="text-sm text-emerald-200">{item.desc}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
