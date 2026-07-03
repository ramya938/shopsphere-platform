import { apiClient } from './api-client';
import { Product, Category } from '../types';

export const productService = {
  async getProducts(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    category_id?: string;
    min_price?: number;
    max_price?: number;
    status?: 'ACTIVE' | 'INACTIVE';
  }): Promise<Product[]> {
    const response = await apiClient.get('/api/v1/products', { params });
    if (response.data && Array.isArray(response.data.products)) {
      return response.data.products;
    }
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return [];
  },

  async getProduct(productId: string): Promise<Product> {
    const response = await apiClient.get(`/api/v1/products/${productId}`);
    return response.data;
  },

  async createProduct(productData: Partial<Product>): Promise<Product> {
    const response = await apiClient.post('/api/v1/products', productData);
    return response.data;
  },

  async updateProduct(productId: string, productData: Partial<Product>): Promise<Product> {
    const response = await apiClient.put(`/api/v1/products/${productId}`, productData);
    return response.data;
  },

  async deleteProduct(productId: string): Promise<void> {
    await apiClient.delete(`/api/v1/products/${productId}`);
  },

  async getCategories(): Promise<Category[]> {
    const response = await apiClient.get('/api/v1/categories');
    return response.data;
  },

  async createCategory(categoryData: Partial<Category>): Promise<Category> {
    const response = await apiClient.post('/api/v1/categories', categoryData);
    return response.data;
  },

  async updateCategory(categoryId: string, categoryData: Partial<Category>): Promise<Category> {
    const response = await apiClient.put(`/api/v1/categories/${categoryId}`, categoryData);
    return response.data;
  },

  async deleteCategory(categoryId: string): Promise<void> {
    await apiClient.delete(`/api/v1/categories/${categoryId}`);
  },
};
export default productService;
