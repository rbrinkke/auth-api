// Password Strength Indicator
import { Check, X } from 'lucide-react';
import { getPasswordStrengthLabel, getPasswordStrengthColor, formatCrackTime } from '@/utils/validation';
import type { PasswordStrength } from '@/types/validation';
import clsx from 'clsx';

interface PasswordStrengthProps {
  password: string;
  strength?: PasswordStrength;
  requirements?: string[];
}

export function PasswordStrengthIndicator({ password, strength, requirements = [] }: PasswordStrengthProps) {
  if (!password || !strength) return null;

  const score = strength.score;
  const label = getPasswordStrengthLabel(score);
  const color = getPasswordStrengthColor(score);

  const barColors = {
    0: 'bg-red-500',
    1: 'bg-red-500',
    2: 'bg-yellow-500',
    3: 'bg-blue-500',
    4: 'bg-green-500',
  };

  return (
    <div className="mt-2 space-y-3">
      {/* Strength Bar */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-700">Password Strength:</span>
          <span className={clsx('text-sm font-medium', `text-${color}-600`)}>
            {label}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={clsx('h-2 rounded-full transition-all duration-300', barColors[score])}
            style={{ width: `${((score + 1) / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Crack Time Estimates */}
      <div className="text-xs text-gray-600 space-y-1">
        <p className="font-medium text-gray-700">Time to crack:</p>
        <p>Offline (slow): {formatCrackTime(strength.crack_times_display.offline_slow_hashing_1e4_per_second)}</p>
        <p>Online (limited): {formatCrackTime(strength.crack_times_display.online_throttling_100_per_hour)}</p>
      </div>

      {/* Feedback */}
      {strength.feedback.warning && (
        <div className="text-sm text-yellow-700 bg-yellow-50 p-2 rounded">
          ⚠️ {strength.feedback.warning}
        </div>
      )}

      {strength.feedback.suggestions.length > 0 && (
        <div className="text-sm text-blue-700 bg-blue-50 p-2 rounded">
          💡 {strength.feedback.suggestions[0]}
        </div>
      )}
    </div>
  );
}

export function PasswordRequirementsChecklist({
  password,
  requirements = [],
}: {
  password: string;
  requirements?: string[];
}) {
  const checks = [
    { label: 'At least 12 characters', test: (p: string) => p.length >= 12 },
    { label: 'Uppercase letter', test: (p: string) => /[A-Z]/.test(p) },
    { label: 'Lowercase letter', test: (p: string) => /[a-z]/.test(p) },
    { label: 'Number', test: (p: string) => /\d/.test(p) },
    { label: 'Special character', test: (p: string) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
  ];

  return (
    <div className="mt-2 space-y-1">
      {checks.map((check) => {
        const passed = check.test(password);
        return (
          <div key={check.label} className="flex items-center text-sm">
            {passed ? (
              <Check className="w-4 h-4 text-green-600 mr-2" />
            ) : (
              <X className="w-4 h-4 text-gray-400 mr-2" />
            )}
            <span className={passed ? 'text-green-700' : 'text-gray-500'}>
              {check.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
