import React, { createContext, useContext, useState, useEffect } from 'react';
import { CartItem } from '../types';
import { orderService } from '../services/order.service';
import { productService } from '../services/product.service';
import { useAuth } from './useAuth';

interface CartContextType {
  cartItems: CartItem[];
  isLoading: boolean;
  addToCart: (productId: string, quantity: number) => Promise<void>;
  updateQuantity: (productId: string, quantity: number) => Promise<void>;
  removeFromCart: (productId: string) => Promise<void>;
  clearCart: () => void;
  cartTotal: number;
  cartCount: number;
  refreshCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const { isAuthenticated } = useAuth();

  const refreshCart = async () => {
    if (!isAuthenticated) {
      setCartItems([]);
      return;
    }
    setIsLoading(true);
    try {
      const cartRes = await orderService.getCart();
      const items = cartRes.items || [];
      
      // Resolve product details (name, price, stock) for each item in the cart
      const resolvedItems = await Promise.all(
        items.map(async (item) => {
          try {
            const product = await productService.getProduct(item.product_id);
            return {
              productId: item.product_id,
              quantity: item.quantity,
              name: product.name,
              price: product.price,
              maxInventory: product.inventory_quantity,
            };
          } catch {
            return {
              productId: item.product_id,
              quantity: item.quantity,
              name: 'Unknown Product',
              price: 0,
              maxInventory: 99,
            };
          }
        })
      );
      setCartItems(resolvedItems);
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshCart();
  }, [isAuthenticated]);

  const addToCart = async (productId: string, quantity: number) => {
    setIsLoading(true);
    try {
      await orderService.addToCart(productId, quantity);
      await refreshCart();
    } finally {
      setIsLoading(false);
    }
  };

  const updateQuantity = async (productId: string, quantity: number) => {
    setIsLoading(true);
    try {
      if (quantity <= 0) {
        await orderService.removeFromCart(productId);
      } else {
        await orderService.updateCartItem(productId, quantity);
      }
      await refreshCart();
    } finally {
      setIsLoading(false);
    }
  };

  const removeFromCart = async (productId: string) => {
    setIsLoading(true);
    try {
      await orderService.removeFromCart(productId);
      await refreshCart();
    } finally {
      setIsLoading(false);
    }
  };

  const clearCart = () => {
    setCartItems([]);
  };

  const cartTotal = cartItems.reduce((acc, item) => acc + item.price * item.quantity, 0);
  const cartCount = cartItems.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <CartContext.Provider
      value={{
        cartItems,
        isLoading,
        addToCart,
        updateQuantity,
        removeFromCart,
        clearCart,
        cartTotal,
        cartCount,
        refreshCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
export default useCart;
