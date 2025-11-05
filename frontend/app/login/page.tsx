'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '../../lib/api';

export default function Login() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const tokens = await login(username, password);

      // Store tokens and user email in localStorage
      localStorage.setItem('accessToken', tokens.access_token);
      localStorage.setItem('refreshToken', tokens.refresh_token);
      localStorage.setItem('userEmail', username);

      setSuccess('Login successful! Redirecting to dashboard...');

      // Redirect after short delay
      setTimeout(() => {
        router.push('/dashboard');
      }, 1000);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h1>Login</h1>
      
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div>
            <label>Email (username):</label>
            <input
              type="email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
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
            />
          </div>

          <button type="submit">Login</button>
        </form>

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
      </div>

      <p>Don't have an account? <a href="/register">Register here</a></p>
    </div>
  );
}
