import React from 'react';
import { Link } from 'react-router-dom';
import { Trash2, ShoppingBag, ArrowRight } from 'lucide-react';
import { useCart } from '../hooks/useCart';
import { Button } from '../components/ui/Button';

export const ShoppingCart: React.FC = () => {
  const { cartItems, updateQuantity, removeFromCart, cartTotal, isLoading } = useCart();

  if (cartItems.length === 0) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center text-textLight dark:bg-bgDark dark:text-textDark">
        <div className="flex flex-col items-center justify-center">
          <ShoppingBag className="h-16 w-16 text-slate-400 stroke-1 mb-4" />
          <h2 className="font-heading text-2xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Your Cart is Empty
          </h2>
          <p className="mt-2 text-sm text-slate-500 max-w-sm">
            It looks like you haven't added any products to your shopping cart yet. Let's find some great items!
          </p>
          <Link to="/" className="mt-6">
            <Button variant="primary">Start Shopping</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      <h1 className="font-heading text-3xl font-extrabold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-8">
        Shopping Cart
      </h1>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left Side: Cart Items List */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          {cartItems.map((item) => (
            <div
              key={item.productId}
              className="flex items-center justify-between rounded-2xl border border-borderLight bg-cardLight p-4 shadow-premium transition-all dark:border-borderDark dark:bg-cardDark"
            >
              {/* Product Info */}
              <div className="flex items-center gap-4 flex-1">
                {/* Mock Small Thumbnail */}
                <div className="h-16 w-16 rounded-xl bg-gradient-to-tr from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 flex items-center justify-center font-heading text-xs font-bold text-slate-400">
                  {item.name.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <Link to={`/products/${item.productId}`} className="font-heading font-bold hover:text-primary transition-colors block text-sm sm:text-base">
                    {item.name}
                  </Link>
                  <span className="text-xs text-slate-500">${item.price.toFixed(2)} each</span>
                </div>
              </div>

              {/* Controls & Price */}
              <div className="flex items-center gap-6">
                {/* Quantity Controls */}
                <div className="flex items-center rounded-lg border border-borderLight bg-cardLight dark:border-borderDark dark:bg-cardDark">
                  <button
                    onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                    className="h-8 w-8 text-sm font-bold hover:bg-bgLight rounded-l-lg dark:hover:bg-borderDark"
                    disabled={isLoading}
                  >
                    -
                  </button>
                  <span className="w-8 text-center text-xs font-bold">{item.quantity}</span>
                  <button
                    onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                    className="h-8 w-8 text-sm font-bold hover:bg-bgLight rounded-r-lg dark:hover:bg-borderDark"
                    disabled={isLoading || item.quantity >= item.maxInventory}
                  >
                    +
                  </button>
                </div>

                {/* Total Price & Delete */}
                <div className="text-right">
                  <span className="block font-heading font-bold text-sm sm:text-base">
                    ${(item.price * item.quantity).toFixed(2)}
                  </span>
                  <button
                    onClick={() => removeFromCart(item.productId)}
                    className="mt-1 text-xs text-red-500 hover:underline flex items-center gap-1 inline-flex"
                    disabled={isLoading}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">Remove</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Right Side: Order Summary Panel */}
        <div className="rounded-2xl border border-borderLight bg-cardLight p-6 shadow-premium h-fit dark:border-borderDark dark:bg-cardDark">
          <h2 className="font-heading text-lg font-bold border-b border-borderLight pb-3 mb-4 dark:border-borderDark">
            Order Summary
          </h2>

          <div className="flex justify-between text-sm mb-2">
            <span className="text-slate-500">Subtotal</span>
            <span className="font-semibold">${cartTotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm mb-4">
            <span className="text-slate-500">Shipping</span>
            <span className="font-semibold text-emerald-500">FREE</span>
          </div>

          <div className="flex justify-between font-heading font-bold text-lg border-t border-borderLight pt-3 mb-6 dark:border-borderDark">
            <span>Total Price</span>
            <span>${cartTotal.toFixed(2)}</span>
          </div>

          <Link to="/checkout" className="block w-full">
            <Button className="w-full flex items-center justify-center gap-2" variant="primary">
              Proceed to Checkout
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <div className="text-center mt-3">
            <Link to="/" className="text-xs text-slate-500 hover:text-primary transition-colors underline">
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShoppingCart;
