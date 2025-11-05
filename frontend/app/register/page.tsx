'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { register } from '../../lib/api';

export default function Register() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      await register(email, password);
      setSuccess('Registration successful! Please verify your email.');
      // Clear form
      setEmail('');
      setPassword('');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h1>Register</h1>

      <div className="card">
        <div className="password-policy">
          <h3>Password Requirements</h3>
          <ul>
            <li className={password.length >= 8 ? 'met' : ''}>
              ✓ Minimum 8 characters
            </li>
            <li>
              ✓ Strong password (zxcvbn score 3-4)
            </li>
            <li>
              ✓ Not found in known data breaches
            </li>
            <li>
              ✓ Use a mix of letters, numbers, and symbols
            </li>
            <li>
              ✓ Consider using a passphrase (e.g., 3-4 random words)
            </li>
          </ul>
          <div className="policy-note">
            <strong>Pro tip:</strong> A password like "CorrectHorseBatteryStaple!42" is
            both easy to remember and extremely secure.
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div>
            <label>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              placeholder="Enter a strong password"
            />
            {password && (
              <div className="password-feedback">
                {password.length < 8 ? (
                  <span className="weak">⚠️ Password too short (minimum 8 characters)</span>
                ) : (
                  <span className="strong">
                    ✓ Password meets minimum requirements. Server will validate strength.
                  </span>
                )}
              </div>
            )}
          </div>

          <button type="submit" disabled={password.length < 8}>
            Register
          </button>
        </form>

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
      </div>

      <p>After registration, check your email (via MailHog at http://localhost:8025) and verify your account.</p>
    </div>
  );
}
