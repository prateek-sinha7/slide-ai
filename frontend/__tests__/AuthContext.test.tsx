import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AuthContext', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  describe('Initial State', () => {
    it('should initialize with no token and no user', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.token).toBeNull();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should load token and user from localStorage on mount', () => {
      const mockToken = 'test-jwt-token';
      const mockUser = { id: '123', username: 'testuser' };

      localStorageMock.setItem('jwt_token', mockToken);
      localStorageMock.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useAuth(), { wrapper });

      waitFor(() => {
        expect(result.current.token).toBe(mockToken);
        expect(result.current.user).toEqual(mockUser);
        expect(result.current.isAuthenticated).toBe(true);
      });
    });
  });

  describe('register', () => {
    it('should register a new user and store JWT token', async () => {
      const mockToken = 'new-jwt-token';
      const mockUser = { id: '456', username: 'newuser' };

      mockedAxios.post.mockResolvedValueOnce({
        data: { token: mockToken, user: mockUser },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.register('newuser', 'password123');
      });

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/register',
        { username: 'newuser', password: 'password123' }
      );

      expect(result.current.token).toBe(mockToken);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);

      expect(localStorageMock.getItem('jwt_token')).toBe(mockToken);
      expect(localStorageMock.getItem('user')).toBe(JSON.stringify(mockUser));
    });

    it('should throw error on registration failure', async () => {
      mockedAxios.post.mockRejectedValueOnce({
        isAxiosError: true,
        response: { data: { error: 'Username already exists' } },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await expect(
        act(async () => {
          await result.current.register('existinguser', 'password123');
        })
      ).rejects.toThrow('Username already exists');

      expect(result.current.token).toBeNull();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('login', () => {
    it('should login user and store JWT token', async () => {
      const mockToken = 'login-jwt-token';
      const mockUser = { id: '789', username: 'loginuser' };

      mockedAxios.post.mockResolvedValueOnce({
        data: { token: mockToken, user: mockUser },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.login('loginuser', 'password123');
      });

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/login',
        { username: 'loginuser', password: 'password123' }
      );

      expect(result.current.token).toBe(mockToken);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);

      expect(localStorageMock.getItem('jwt_token')).toBe(mockToken);
      expect(localStorageMock.getItem('user')).toBe(JSON.stringify(mockUser));
    });

    it('should throw error on invalid credentials', async () => {
      mockedAxios.post.mockRejectedValueOnce({
        isAxiosError: true,
        response: { data: { error: 'Invalid credentials' } },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await expect(
        act(async () => {
          await result.current.login('wronguser', 'wrongpass');
        })
      ).rejects.toThrow('Invalid credentials');

      expect(result.current.token).toBeNull();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear token and user from state and localStorage', async () => {
      const mockToken = 'test-jwt-token';
      const mockUser = { id: '123', username: 'testuser' };

      localStorageMock.setItem('jwt_token', mockToken);
      localStorageMock.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      act(() => {
        result.current.logout();
      });

      expect(result.current.token).toBeNull();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);

      expect(localStorageMock.getItem('jwt_token')).toBeNull();
      expect(localStorageMock.getItem('user')).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token and user exist', async () => {
      const mockToken = 'test-jwt-token';
      const mockUser = { id: '123', username: 'testuser' };

      mockedAxios.post.mockResolvedValueOnce({
        data: { token: mockToken, user: mockUser },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.login('testuser', 'password123');
      });

      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should return false when token or user is missing', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(false);
    });
  });
});
