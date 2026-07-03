import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShoppingBag, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useCart } from '../hooks/useCart';
import { orderService } from '../services/order.service';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const Checkout: React.FC = () => {
  const { cartItems, cartTotal, clearCart } = useCart();
  const navigate = useNavigate();
  
  const [shippingAddress, setShippingAddress] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [placedOrder, setPlacedOrder] = useState<any>(null);

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shippingAddress.trim()) {
      setError('Shipping address is required');
      return;
    }

    setError('');
    setIsLoading(true);
    try {
      const order = await orderService.checkout(shippingAddress);
      setPlacedOrder(order);
      setIsSuccess(true);
      clearCart();
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to place order. Please review stock limits.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess && placedOrder) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center text-textLight dark:bg-bgDark dark:text-textDark">
        <div className="rounded-2xl border border-borderLight bg-cardLight p-8 shadow-premium dark:border-borderDark dark:bg-cardDark">
          <div className="flex justify-center text-emerald-500 mb-4">
            <CheckCircle2 className="h-16 w-16" />
          </div>
          <h2 className="font-heading text-2xl font-extrabold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Order Confirmed!
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Thank you for your purchase. Your order has been placed successfully and is pending payment.
          </p>

          <div className="mt-6 border-t border-borderLight pt-4 text-left dark:border-borderDark">
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-slate-500">Order ID:</span>
              <span className="font-mono font-bold truncate max-w-[180px]">{placedOrder.id}</span>
            </div>
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-slate-500">Amount Paid/Due:</span>
              <span className="font-bold">${placedOrder.total_price.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Status:</span>
              <span className="font-bold text-primary uppercase">{placedOrder.status}</span>
            </div>
          </div>

          <div className="mt-8 flex flex-col gap-3">
            <Link to="/orders">
              <Button variant="primary" className="w-full">Track Order Status</Button>
            </Link>
            <Link to="/">
              <Button variant="outline" className="w-full">Back to Catalog</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (cartItems.length === 0) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center text-textLight dark:bg-bgDark dark:text-textDark">
        <ShoppingBag className="h-12 w-12 text-slate-400 mb-2 mx-auto" />
        <h2 className="font-heading text-xl font-bold">No active items for checkout</h2>
        <Link to="/" className="mt-4 inline-flex items-center gap-1 text-primary hover:underline">
          <ArrowLeft className="h-4 w-4" />
          Browse Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      <h1 className="font-heading text-3xl font-extrabold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-8">
        Checkout
      </h1>

      {error && (
        <div className="mb-6 rounded-lg bg-red-500/10 p-3 text-sm font-semibold text-red-500 border border-red-500/20">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Left Side: Shipping Address Form */}
        <form onSubmit={handleCheckout} className="rounded-2xl border border-borderLight bg-cardLight p-6 shadow-premium h-fit dark:border-borderDark dark:bg-cardDark">
          <h2 className="font-heading text-lg font-bold border-b border-borderLight pb-3 mb-4 dark:border-borderDark">
            Shipping Information
          </h2>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="address" className="text-xs font-semibold text-slate-500">
                Delivery Address
              </label>
              <textarea
                id="address"
                rows={4}
                placeholder="123 Enterprise Street, Suite 400, San Francisco, CA 94107"
                className="w-full rounded-lg border border-borderLight bg-transparent p-3 text-sm outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-borderDark"
                value={shippingAddress}
                onChange={(e) => setShippingAddress(e.target.value)}
                required
              />
            </div>

            <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
              Confirm & Place Order
            </Button>
          </div>
        </form>

        {/* Right Side: Order Review */}
        <div className="rounded-2xl border border-borderLight bg-cardLight p-6 shadow-premium h-fit dark:border-borderDark dark:bg-cardDark">
          <h2 className="font-heading text-lg font-bold border-b border-borderLight pb-3 mb-4 dark:border-borderDark">
            Review Your Items
          </h2>

          <div className="flex flex-col gap-4 max-h-60 overflow-y-auto mb-4">
            {cartItems.map((item) => (
              <div key={item.productId} className="flex justify-between text-xs">
                <div>
                  <span className="font-bold">{item.name}</span>
                  <span className="block text-slate-400">Qty: {item.quantity}</span>
                </div>
                <span className="font-semibold">${(item.price * item.quantity).toFixed(2)}</span>
              </div>
            ))}
          </div>

          <div className="border-t border-borderLight pt-4 dark:border-borderDark">
            <div className="flex justify-between text-sm mb-1.5">
              <span className="text-slate-500">Subtotal</span>
              <span className="font-semibold">${cartTotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm mb-4">
              <span className="text-slate-500">Shipping</span>
              <span className="font-semibold text-emerald-500">FREE</span>
            </div>
            <div className="flex justify-between font-heading font-bold text-lg border-t border-borderLight pt-3 dark:border-borderDark">
              <span>Order Total</span>
              <span>${cartTotal.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
