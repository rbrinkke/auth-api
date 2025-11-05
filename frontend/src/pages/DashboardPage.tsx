// Premium Dashboard with Stunning Animations
import { motion } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import {
  ArrowRightOnRectangleIcon,
  UserIcon,
  ShieldCheckIcon,
  KeyIcon,
  CheckCircleIcon,
  ClockIcon,
  LockClosedIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';
import { toast } from 'sonner';

export function DashboardPage() {
  const { user, logout } = useAuth();
  const [showToken, setShowToken] = useState(false);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-900 to-slate-900">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-indigo-500 opacity-10 blur-3xl"
          animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-purple-500 opacity-10 blur-3xl"
          animate={{ scale: [1.2, 1, 1.2], rotate: [360, 180, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        />
      </div>

      <div className="relative z-10 p-6 lg:p-12">
        {/* Header */}
        <motion.div
          className="max-w-7xl mx-auto"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="glass-card rounded-2xl p-8 mb-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <h1 className="text-4xl font-bold text-white mb-2">
                  Welcome back! 👋
                </h1>
                <p className="text-indigo-200 text-lg">
                  Manage your account and security settings
                </p>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Button
                  variant="outline"
                  onClick={handleLogout}
                  leftIcon={<ArrowRightOnRectangleIcon className="w-5 h-5" />}
                >
                  Logout
                </Button>
              </motion.div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* User Profile Card */}
            <motion.div
              className="lg:col-span-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="glass-card rounded-2xl p-8 h-full">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                    <UserIcon className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">Profile</h2>
                    <p className="text-indigo-200">Your account information</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <motion.div
                    className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10"
                    whileHover={{ scale: 1.02 }}
                  >
                    <div className="flex items-center gap-3">
                      <EnvelopeIcon className="w-5 h-5 text-indigo-400" />
                      <div>
                        <p className="text-sm text-indigo-200">Email</p>
                        <p className="text-white font-medium">{user?.email || 'N/A'}</p>
                      </div>
                    </div>
                    <CheckCircleIcon className="w-6 h-6 text-green-500" />
                  </motion.div>

                  <motion.div
                    className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10"
                    whileHover={{ scale: 1.02 }}
                  >
                    <div className="flex items-center gap-3">
                      <ShieldCheckIcon className="w-5 h-5 text-indigo-400" />
                      <div>
                        <p className="text-sm text-indigo-200">Two-Factor Auth</p>
                        <p className="text-white font-medium">
                          {user?.twoFactorEnabled ? 'Enabled' : 'Disabled'}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        user?.twoFactorEnabled
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}
                    >
                      {user?.twoFactorEnabled ? 'Secure' : 'Standard'}
                    </span>
                  </motion.div>

                  <motion.div
                    className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10"
                    whileHover={{ scale: 1.02 }}
                  >
                    <div className="flex items-center gap-3">
                      <ClockIcon className="w-5 h-5 text-indigo-400" />
                      <div>
                        <p className="text-sm text-indigo-200">Last Login</p>
                        <p className="text-white font-medium">Just now</p>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <div className="glass-card rounded-2xl p-8 h-full">
                <h2 className="text-2xl font-bold text-white mb-6">Quick Actions</h2>
                <div className="space-y-4">
                  {[
                    { icon: ShieldCheckIcon, label: 'Enable 2FA', color: 'from-purple-600 to-indigo-600' },
                    { icon: LockClosedIcon, label: 'Change Password', color: 'from-blue-600 to-cyan-600' },
                    { icon: KeyIcon, label: 'Reset Tokens', color: 'from-emerald-600 to-teal-600' },
                  ].map((action, index) => (
                    <motion.button
                      key={index}
                      className={`w-full p-4 rounded-xl bg-gradient-to-r ${action.color} text-white font-medium shadow-lg hover:shadow-xl transition-shadow`}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + index * 0.1 }}
                    >
                      <div className="flex items-center gap-3">
                        <action.icon className="w-5 h-5" />
                        <span>{action.label}</span>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Security Details */}
            <motion.div
              className="lg:col-span-3"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <div className="glass-card rounded-2xl p-8">
                <h2 className="text-2xl font-bold text-white mb-6">Security Features</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[
                    {
                      icon: '🔐',
                      title: 'Password Hashing',
                      desc: 'Argon2id (Industry Standard)',
                      color: 'from-blue-500 to-indigo-500',
                    },
                    {
                      icon: '🔄',
                      title: 'Token Rotation',
                      desc: 'Automatic refresh token rotation',
                      color: 'from-purple-500 to-pink-500',
                    },
                    {
                      icon: '🛡️',
                      title: '2FA Support',
                      desc: 'TOTP + Email codes + Backup codes',
                      color: 'from-emerald-500 to-cyan-500',
                    },
                    {
                      icon: '⚡',
                      title: 'Rate Limiting',
                      desc: 'Brute-force attack prevention',
                      color: 'from-orange-500 to-red-500',
                    },
                    {
                      icon: '✅',
                      title: 'Email Verification',
                      desc: 'Hard verification required',
                      color: 'from-teal-500 to-emerald-500',
                    },
                    {
                      icon: '🔍',
                      title: 'Password Policy',
                      desc: 'HIBP integration + Strength validation',
                      color: 'from-indigo-500 to-purple-500',
                    },
                  ].map((feature, index) => (
                    <motion.div
                      key={index}
                      className="p-6 rounded-xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 hover:border-white/20 transition-colors"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.6 + index * 0.1 }}
                      whileHover={{ y: -5 }}
                    >
                      <div className="text-4xl mb-3">{feature.icon}</div>
                      <h3 className="font-bold text-white mb-2">{feature.title}</h3>
                      <p className="text-sm text-indigo-200">{feature.desc}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
