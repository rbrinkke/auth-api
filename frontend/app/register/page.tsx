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
            />
            <small>Minimum 8 characters</small>
          </div>

          <button type="submit">Register</button>
        </form>

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
      </div>

      <p>After registration, check your email (via MailHog at http://localhost:8025) and verify your account.</p>
    </div>
  );
}
