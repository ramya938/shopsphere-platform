import { apiClient } from './api-client';
import { User, AuthResponse } from '../types';

export const authService = {
  async register(email: string, password: string, fullName: string, role: 'CUSTOMER' | 'ADMIN' = 'CUSTOMER'): Promise<User> {
    const response = await apiClient.post('/api/v1/auth/register', {
      email,
      password,
      full_name: fullName,
      role,
    });
    return response.data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/login', {
      email,
      password,
    });
    const data = response.data;
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  },

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/api/v1/users/me');
    return response.data;
  },

  async updateProfile(fullName?: string, email?: string, password?: string): Promise<User> {
    const response = await apiClient.put('/api/v1/users/me', {
      full_name: fullName || undefined,
      email: email || undefined,
      password: password || undefined,
    });
    return response.data;
  },

  async deleteAccount(): Promise<void> {
    await apiClient.delete('/api/v1/users/me');
    this.logout();
  },

  async listUsers(skip: number = 0, limit: number = 100): Promise<User[]> {
    const response = await apiClient.get('/api/v1/users/', {
      params: { skip, limit },
    });
    return response.data;
  },
};
export default authService;
