'use client';

import { useState, useEffect } from 'react';
import { getHealth } from '../lib/api';

export default function Home() {
  const [apiStatus, setApiStatus] = useState<any>(null);

  useEffect(() => {
    getHealth()
      .then(data => setApiStatus(data))
      .catch(err => setApiStatus({ status: 'error', message: err.message }));
  }, []);

  return (
    <div className="container">
      <h1>Activity App Frontend</h1>
      
      <div className="card">
        <h2>Welcome to Activity App</h2>
        <p>A minimalistic authentication service with React/Next.js frontend.</p>
      </div>

      <div className="card">
        <h3>Backend API Status</h3>
        {apiStatus ? (
          <div>
            <p><strong>Status:</strong> {apiStatus.status}</p>
            <p><strong>Service:</strong> {apiStatus.service}</p>
            <p><strong>Version:</strong> {apiStatus.version}</p>
            {apiStatus.dependencies && (
              <div>
                <p><strong>Dependencies:</strong></p>
                <ul>
                  <li>Database: {apiStatus.dependencies.database}</li>
                  <li>Redis: {apiStatus.dependencies.redis}</li>
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      <div className="card">
        <h3>Quick Start</h3>
        <ol>
          <li>Go to Register page to create an account</li>
          <li>Verify your email (check MailHog at http://localhost:8025)</li>
          <li>Login with your credentials</li>
          <li>Access the dashboard</li>
        </ol>
      </div>
    </div>
  );
}
