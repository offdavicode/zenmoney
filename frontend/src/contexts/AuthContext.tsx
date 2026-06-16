'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser, loginUser, logoutUser, UserOut } from '@/services/auth.service';
import { setToken as setApiToken, clearToken as clearApiToken } from '@/services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserOut | null;
  login: (email: string, password?: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<UserOut | null>(null);
  const router = useRouter();

  const loadUser = useCallback(async () => {
    try {
      if (typeof window !== 'undefined' && localStorage.getItem('zen_token')) {
        const userData = await getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Failed to load user session', error);
      clearApiToken();
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email: string, password?: string) => {
    setIsLoading(true);
    try {
      
      
      await loginUser({ email, password: password || '123456' });
      await loadUser();
      router.push('/dashboard');
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await logoutUser();
    } catch (e) {
      
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setIsLoading(false);
      router.push('/login');
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, user, login, logout, loadUser }}>
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
