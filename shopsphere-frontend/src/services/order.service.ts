import { apiClient } from './api-client';
import { Order, OrderStatus } from '../types';

export interface CartResponse {
  id: string;
  user_id: string;
  items: Array<{
    product_id: string;
    quantity: number;
    price: number;
  }>;
}

export const orderService = {
  // Cart API
  async getCart(): Promise<CartResponse> {
    const response = await apiClient.get('/api/v1/cart');
    return response.data;
  },

  async addToCart(productId: string, quantity: number): Promise<CartResponse> {
    const response = await apiClient.post('/api/v1/cart/items', {
      product_id: productId,
      quantity,
    });
    return response.data;
  },

  async updateCartItem(productId: string, quantity: number): Promise<CartResponse> {
    const response = await apiClient.put(`/api/v1/cart/items/${productId}`, {
      quantity,
    });
    return response.data;
  },

  async removeFromCart(productId: string): Promise<CartResponse> {
    const response = await apiClient.delete(`/api/v1/cart/items/${productId}`);
    return response.data;
  },

  // Checkout API
  async checkout(shippingAddress: string): Promise<Order> {
    const response = await apiClient.post('/api/v1/orders/checkout', {
      shipping_address: shippingAddress,
    });
    return response.data;
  },

  async placeDirectOrder(items: Array<{ product_id: string; quantity: number }>, shippingAddress: string): Promise<Order> {
    const response = await apiClient.post('/api/v1/orders', {
      items,
      shipping_address: shippingAddress,
    });
    return response.data;
  },

  // Order History API
  async getMyOrders(): Promise<Order[]> {
    const response = await apiClient.get('/api/v1/orders/me');
    return response.data;
  },

  async getOrder(orderId: string): Promise<Order> {
    const response = await apiClient.get(`/api/v1/orders/${orderId}`);
    return response.data;
  },

  async cancelOrder(orderId: string): Promise<Order> {
    const response = await apiClient.patch(`/api/v1/orders/${orderId}/status`, {
      status: 'CANCELLED',
    });
    return response.data;
  },

  // Admin Order API
  async listAllOrders(skip: number = 0, limit: number = 100): Promise<Order[]> {
    const response = await apiClient.get('/api/v1/orders/', {
      params: { skip, limit },
    });
    return response.data;
  },

  async updateOrderStatus(orderId: string, status: OrderStatus): Promise<Order> {
    const response = await apiClient.patch(`/api/v1/orders/${orderId}/status`, {
      status,
    });
    return response.data;
  },
};
export default orderService;
