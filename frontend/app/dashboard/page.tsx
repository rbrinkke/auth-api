'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { refreshToken, logout } from '../../lib/api';

export default function Dashboard() {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string>('');
  const [message, setMessage] = useState('You are logged in!');
  const [error, setError] = useState('');
  const [hasAccessToken, setHasAccessToken] = useState<boolean | null>(null);
  const [hasRefreshToken, setHasRefreshToken] = useState<boolean | null>(null);

  useEffect(() => {
    // Check if user is logged in
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken_val = localStorage.getItem('refreshToken');

    if (!accessToken || !refreshToken_val) {
      router.push('/login');
      return;
    }

    setHasAccessToken(true);
    setHasRefreshToken(true);

    // For demo purposes, show email from localStorage if available
    const savedEmail = localStorage.getItem('userEmail');
    if (savedEmail) {
      setUserEmail(savedEmail);
    }
  }, [router]);

  const handleRefreshToken = async () => {
    try {
      const refreshToken_val = localStorage.getItem('refreshToken');
      if (!refreshToken_val) {
        throw new Error('No refresh token');
      }

      const tokens = await refreshToken(refreshToken_val);
      
      // Update stored tokens
      localStorage.setItem('accessToken', tokens.access_token);
      localStorage.setItem('refreshToken', tokens.refresh_token);
      
      setMessage('Token refreshed successfully!');
      setError('');
    } catch (err: any) {
      setError(err.message);
      setMessage('');
    }
  };

  const handleLogout = async () => {
    try {
      const refreshToken_val = localStorage.getItem('refreshToken');
      if (refreshToken_val) {
        await logout(refreshToken_val);
      }
    } catch (err) {
      // Ignore errors on logout
    } finally {
      // Clear localStorage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userEmail');
      
      // Redirect to home
      router.push('/');
    }
  };

  return (
    <div className="container">
      <h1>Dashboard</h1>
      
      <div className="card">
        <h2>Welcome!</h2>
        <p>{message}</p>
        {userEmail && <p><strong>Email:</strong> {userEmail}</p>}
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h3>Actions</h3>
        <button onClick={handleRefreshToken}>
          Refresh Access Token
        </button>
        <button onClick={handleLogout} style={{ backgroundColor: '#ffcccc' }}>
          Logout
        </button>
      </div>

      <div className="card">
        <h3>Token Information</h3>
        <p><strong>Access Token:</strong> {hasAccessToken ? 'Present' : 'Missing'}</p>
        <p><strong>Refresh Token:</strong> {hasRefreshToken ? 'Present' : 'Missing'}</p>
      </div>
    </div>
  );
}
