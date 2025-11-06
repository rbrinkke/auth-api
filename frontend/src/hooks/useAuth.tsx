// frontend/src/hooks/useAuth.tsx
import { useState, useContext, createContext, ReactNode, useEffect } from 'react';
import { 
  loginUser, 
  registerUser, 
  requestPasswordReset, 
  confirmPasswordReset, 
  logoutUser,
  twoFactorLogin,
  getProtectedData // Example protected route
} from '../services/api';

import { 
  AuthMode, 
  LoginData, 
  RegisterData, 
  PasswordResetRequestData, 
  PasswordResetConfirmData,
  TwoFactorLoginData
} from '../types/auth';
import { AxiosError } from 'axios';

// Define the shape of the user object
interface User {
  id: string;
  email: string;
  is_verified: boolean;
  is_2fa_enabled: boolean;
}

// Define the shape of the auth context
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  authMode: AuthMode;
  setAuthMode: (mode: AuthMode) => void;
  error: string | null;
  success: string | null;
  isLoading: boolean;
  handleLogin: (data: LoginData) => Promise<void>;
  handleRegister: (data: RegisterData) => Promise<void>;
  handleRequestReset: (data: PasswordResetRequestData) => Promise<void>;
  handleConfirmReset: (data: PasswordResetConfirmData) => Promise<void>;
  handleTwoFactorLogin: (data: TwoFactorLoginData) => Promise<void>;
  handleLogout: () => Promise<void>;
  clearError: () => void;
  clearSuccess: () => void;
  fetchProtectedData: () => Promise<void>; // Example function
}

// Create the auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Temporary state to hold email during 2FA
  const [twoFactorEmail, setTwoFactorEmail] = useState<string | null>(null);

  // Clear errors and successes
  const clearError = () => setError(null);
  const clearSuccess = () => setSuccess(null);

  // Handle Login
  const handleLogin = async (data: LoginData) => {
    clearError();
    clearSuccess();
    setIsLoading(true);
    try {
      // Pass email, password, and code to loginUser
      const response = await loginUser({ 
        email: data.email, 
        password: data.password, 
        code: data.code // TOEGEVOEGD
      });
      
      // Check if 2FA is required
      if (response.user.is_2fa_enabled) {
        setUser(response.user); // Store user info temporarily
        setTwoFactorEmail(response.user.email); // Store email for 2FA step
        setAuthMode('2fa');
        setSuccess(response.message); // e.g., "2FA code sent"
      } else {
        // If 2FA is not enabled, login is successful
        setUser(response.user);
        setIsAuthenticated(true);
        setSuccess(response.message);
        // No tokens are returned from /login, they come from /2fa/login or are http-only
        // If login is successful without 2FA, we assume cookies (refresh) are set
      }
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.message || err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
      throw err; // Re-throw to be caught in the form
    } finally {
      setIsLoading(false);
    }
  };

  // Handle 2FA Login
  const handleTwoFactorLogin = async (data: TwoFactorLoginData) => {
    clearError();
    clearSuccess();
    setIsLoading(true);
    
    const email = data.email || twoFactorEmail;
    if (!email) {
      setError("No email address provided for 2FA.");
      setIsLoading(false);
      return;
    }

    try {
      const response = await twoFactorLogin({ email: email, code: data.code });
      setUser(prevUser => prevUser ? { ...prevUser, is_verified: true } : user); // Update user state
      setIsAuthenticated(true);
      setSuccess(response.message);
      setTwoFactorEmail(null); // Clear temporary email
      // Access token is now set in api.ts interceptor
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.message || err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
      throw err; // Re-throw to be caught in the form
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Register
  const handleRegister = async (data: RegisterData) => {
    clearError();
    clearSuccess();
    setIsLoading(true);
    try {
      // Pass all register data (email, password, confirm, code)
      const response = await registerUser({
        email: data.email,
        password: data.password,
        confirmPassword: data.confirmPassword,
        code: data.code // TOEGEVOEGD
      });
      setSuccess(response.message);
      setAuthMode('login'); // Switch to login after successful registration
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.message || err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
      throw err; // Re-throw to be caught in the form
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Password Reset Request
  const handleRequestReset = async (data: PasswordResetRequestData) => {
    clearError();
    clearSuccess();
    setIsLoading(true);
    try {
      const response = await requestPasswordReset(data);
      setSuccess(response.message);
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.message || err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
      throw err; // Re-throw to be caught in the form
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Confirm Password Reset
  const handleConfirmReset = async (data: PasswordResetConfirmData) => {
    clearError();
    clearSuccess();
    setIsLoading(true);
    try {
      const response = await confirmPasswordReset(data);
      setSuccess(response.message);
      setAuthMode('login'); // Switch to login after successful reset
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.message || err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
      throw err; // Re-throw to be caught in the form
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Logout
  const handleLogout = async () => {
    clearError();
    clearSuccess();
    setIsLoading(true);
    try {
      await logoutUser();
      setIsAuthenticated(false);
      setUser(null);
      setAuthMode('login');
      setSuccess('Successfully logged out.');
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.message || err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred during logout.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Example of fetching protected data
  const fetchProtectedData = async () => {
    clearError();
    setIsLoading(true);
    try {
      const data = await getProtectedData();
      console.log('Protected data:', data);
      // Handle the protected data (e.g., set in state)
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 401) {
          // This might be handled by the interceptor, but as a fallback:
          setError('You are not authorized. Please log in.');
          setIsAuthenticated(false);
          setUser(null);
          setAuthMode('login');
        } else {
          setError(err.response?.data?.message || err.message);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
    } finally {
      setIsLoading(false);
    }
  };


  // Check authentication status on mount (e.g., by checking for a refresh token)
  // This is a simplified example. In a real app, you might try to hit a
  // 'me' endpoint or refresh the token silently.
  useEffect(() => {
    // This is just a placeholder. A real implementation would be more complex.
    // For example, you could try to refresh the token.
    // If successful, setIsAuthenticated(true) and fetch user data.
    // If it fails, do nothing (user remains logged out).
    
    // Example:
    // const checkAuth = async () => {
    //   try {
    //     await api.post('/auth/refresh-token'); // Try to refresh
    //     // If refresh is successful, interceptor will set new token
    //     // Then fetch user data
    //     const userData = await api.get('/auth/me'); // Assuming a /me endpoint
    //     setUser(userData.data);
    //     setIsAuthenticated(true);
    //   } catch (error) {
    //     setIsAuthenticated(false);
    //     setUser(null);
    //   }
    // };
    // checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      user,
      authMode,
      setAuthMode,
      error,
      success,
      isLoading,
      handleLogin,
      handleRegister,
      handleRequestReset,
      handleConfirmReset,
      handleTwoFactorLogin,
      handleLogout,
      clearError,
      clearSuccess,
      fetchProtectedData
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
