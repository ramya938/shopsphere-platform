import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, ShoppingCart, Info, CheckCircle, Shield } from 'lucide-react';
import { productService } from '../services/product.service';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';

export const ProductDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();
  
  const [quantity, setQuantity] = useState(1);
  const [isAdding, setIsAdding] = useState(false);

  const { data: product, isLoading, error } = useQuery({
    queryKey: ['product', id],
    queryFn: () => productService.getProduct(id || ''),
    enabled: !!id,
  });

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    if (!product) return;
    setIsAdding(true);
    try {
      await addToCart(product.id, quantity);
    } catch (err) {
      console.error('Error adding to cart:', err);
    } finally {
      setIsAdding(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 text-center text-textLight dark:text-textDark">
        <h2 className="text-2xl font-bold">Product not found</h2>
        <Link to="/" className="mt-4 inline-flex items-center gap-1 text-primary hover:underline">
          <ArrowLeft className="h-4 w-4" />
          Back to Catalog
        </Link>
      </div>
    );
  }

  const isOutOfStock = product.inventory_quantity <= 0;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-semibold hover:text-primary transition-colors mb-6">
        <ArrowLeft className="h-4.5 w-4.5" />
        Back to Catalog
      </Link>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Left Side: Product Image */}
        <div className="h-96 w-full rounded-2xl bg-gradient-to-tr from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 flex items-center justify-center overflow-hidden shadow-premium">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="font-heading font-black text-6xl tracking-wide opacity-10">
              {product.name.substring(0, 3).toUpperCase()}
            </span>
          )}
        </div>

        {/* Right Side: Product Details */}
        <div className="flex flex-col justify-between">
          <div>
            <h1 className="font-heading text-3xl font-extrabold md:text-4xl">
              {product.name}
            </h1>
            
            <span className="mt-3 inline-flex items-center gap-1 rounded bg-slate-500/10 px-2.5 py-1 text-xs font-bold text-slate-500 border border-slate-500/20 uppercase tracking-wider">
              {product.status}
            </span>

            <p className="mt-4 text-slate-500 leading-relaxed text-sm dark:text-slate-400">
              {product.description}
            </p>

            <div className="mt-6 flex items-center gap-3">
              <span className="font-heading text-3xl font-black">
                ${product.price.toFixed(2)}
              </span>
              
              {isOutOfStock ? (
                <span className="rounded bg-red-500/10 px-2.5 py-1 text-xs font-bold text-red-500 border border-red-500/20">
                  Out of Stock
                </span>
              ) : (
                <span className="rounded bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-500 border border-emerald-500/20">
                  {product.inventory_quantity} Units in Stock
                </span>
              )}
            </div>
          </div>

          <div className="mt-8 border-t border-borderLight pt-6 dark:border-borderDark">
            {/* Quantity Selector */}
            {!isOutOfStock && (
              <div className="flex items-center gap-4 mb-4">
                <span className="text-sm font-semibold text-slate-500">Quantity:</span>
                <div className="flex items-center rounded-lg border border-borderLight bg-cardLight dark:border-borderDark dark:bg-cardDark">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="h-9 w-9 text-lg font-bold hover:bg-bgLight rounded-l-lg dark:hover:bg-borderDark"
                    disabled={quantity <= 1}
                  >
                    -
                  </button>
                  <span className="w-10 text-center text-sm font-bold">{quantity}</span>
                  <button
                    onClick={() => setQuantity(Math.min(product.inventory_quantity, quantity + 1))}
                    className="h-9 w-9 text-lg font-bold hover:bg-bgLight rounded-r-lg dark:hover:bg-borderDark"
                    disabled={quantity >= product.inventory_quantity}
                  >
                    +
                  </button>
                </div>
              </div>
            )}

            <Button
              className="w-full flex items-center justify-center gap-2"
              variant={isOutOfStock ? 'outline' : 'primary'}
              disabled={isOutOfStock}
              onClick={handleAddToCart}
              isLoading={isAdding}
            >
              <ShoppingCart className="h-5 w-5" />
              Add to Shopping Cart
            </Button>
          </div>
          
          {/* Trust Badges */}
          <div className="mt-6 grid grid-cols-2 gap-4 border-t border-borderLight pt-6 text-xs text-slate-500 dark:border-borderDark dark:text-slate-400">
            <div className="flex items-center gap-2">
              <Shield className="h-4.5 w-4.5 text-primary" />
              <span>Secured Checkout</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4.5 w-4.5 text-secondary" />
              <span>Restocking Policy</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetails;
