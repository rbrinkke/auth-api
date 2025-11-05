// Authentication Hook
import { useState, useEffect, createContext, useContext } from 'react';
import apiService from '@/services/api';

interface User {
  email: string;
  id: string;
  twoFactorEnabled: boolean;
  pendingVerificationId?: string; // User ID for pending email verification
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  verifyEmail: (code: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  const checkAuth = () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsLoading(false);
      // In a real app, you'd verify the token with the backend
      // For now, we'll just check if it exists
    } else {
      setIsLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      const response = await apiService.login({ username, password });

      // Check if 2FA is required
      if ('detail' in response.data && (response.data as any).detail?.two_factor_required) {
        throw new Error('2FA_REQUIRED');
      }

      const data = response.data as any;
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      // Fetch user info (simplified)
      setUser({
        email: username,
        id: 'user-id',
        twoFactorEnabled: false, // Would fetch from API
      });
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string) => {
    try {
      const response = await apiService.register({ email, password });
      // Store user_id for verification
      const data = response.data as any;
      setUser({
        email: data.email,
        id: data.user_id,
        twoFactorEnabled: false,
        pendingVerificationId: data.user_id,
      });
    } catch (error) {
      throw error;
    }
  };

  const verifyEmail = async (code: string) => {
    console.log('[VERIFY-FRONTEND] verifyEmail called with code:', code);
    console.log('[VERIFY-FRONTEND] user?.pendingVerificationId:', user?.pendingVerificationId);

    try {
      if (!user?.pendingVerificationId) {
        console.log('[VERIFY-FRONTEND] ERROR: No pending verification ID');
        throw new Error('No pending verification');
      }

      const userId = user.pendingVerificationId;
      console.log('[VERIFY-FRONTEND] About to call API with:', { userId, code });

      await apiService.verifyCode(userId, code);
      console.log('[VERIFY-FRONTEND] Success! Clearing pendingVerificationId');
      // Email verified successfully - clear pendingVerificationId
      setUser({
        ...user,
        pendingVerificationId: undefined,
      });

      return response;
    } catch (error: any) {
      console.log('[VERIFY-FRONTEND] ERROR:', error.message);
      console.log('[VERIFY-FRONTEND] Error response:', error.response?.data);
      console.log('[VERIFY-FRONTEND] Error status:', error.response?.status);
      throw error;
    }
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
    window.location.href = '/login';
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, register, verifyEmail, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
