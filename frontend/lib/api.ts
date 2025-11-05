const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function register(email: string, password: string) {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

export async function verifyEmail(token: string) {
  const response = await fetch(`${API_URL}/auth/verify?token=${token}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Verification failed');
  }

  return response.json();
}

export async function login(username: string, password: string) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

export async function refreshToken(refreshToken: string) {
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Token refresh failed');
  }

  return response.json();
}

export async function logout(refreshToken: string) {
  const response = await fetch(`${API_URL}/auth/logout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  return response.ok;
}

export async function getHealth() {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}
