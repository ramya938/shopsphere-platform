export type UserRole = 'ADMIN' | 'CUSTOMER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  inventory_quantity: number;
  category_id: string;
  status: 'ACTIVE' | 'INACTIVE';
  image_url?: string;
  created_at: string;
}

export interface CartItem {
  productId: string;
  quantity: number;
  name: string;
  price: number;
  maxInventory: number;
}

export type OrderStatus = 'CREATED' | 'PAID' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED';

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  quantity: number;
  price?: number;
  price_at_purchase?: number;
  product_name?: string;
}

export interface Order {
  id: string;
  user_id: string;
  total_price: number;
  status: OrderStatus;
  shipping_address: string;
  created_at: string;
  items: OrderItem[];
}
