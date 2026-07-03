import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, ShoppingCart, SlidersHorizontal, AlertCircle } from 'lucide-react';
import { productService } from '../services/product.service';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { SkeletonLoader } from '../components/ui/SkeletonLoader';
import { Button } from '../components/ui/Button';

export const ProductCatalog: React.FC = () => {
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();
  
  // Filter States
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [minPrice, setMinPrice] = useState<number | ''>('');
  const [maxPrice, setMaxPrice] = useState<number | ''>('');
  const [showFilters, setShowFilters] = useState(false);
  const [cartAddingId, setCartAddingId] = useState<string | null>(null);

  // Queries
  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => productService.getCategories(),
  });

  const { data: products = [], isLoading, error } = useQuery({
    queryKey: ['products', selectedCategory, search, minPrice, maxPrice],
    queryFn: () =>
      productService.getProducts({
        category_id: selectedCategory || undefined,
        search: search || undefined,
        min_price: minPrice !== '' ? minPrice : undefined,
        max_price: maxPrice !== '' ? maxPrice : undefined,
        status: 'ACTIVE',
      }),
  });

  const handleAddToCart = async (productId: string) => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }
    setCartAddingId(productId);
    try {
      await addToCart(productId, 1);
    } catch (err) {
      console.error('Error adding to cart:', err);
    } finally {
      setCartAddingId(null);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="font-heading text-3xl font-extrabold md:text-4xl bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Explore Catalog
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Discover modern high-quality products curated by ShopSphere AI
          </p>
        </div>

        {/* Search & Filter Trigger */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 md:w-80">
            <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search products..."
              className="h-10 w-full rounded-lg border border-borderLight bg-cardLight pl-10 pr-4 text-sm outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-borderDark dark:bg-cardDark"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <SlidersHorizontal className="h-4.5 w-4.5" />
            Filters
          </Button>
        </div>
      </div>

      {/* Expanded Filters Drawer */}
      {showFilters && (
        <div className="mt-4 rounded-xl border border-borderLight bg-cardLight p-5 shadow-premium dark:border-borderDark dark:bg-cardDark">
          <h3 className="font-heading font-bold mb-3">Refine Search</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* Price Filter */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-500">Price Range ($)</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  className="h-9 w-full rounded-lg border border-borderLight bg-transparent px-3 text-sm outline-none dark:border-borderDark"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value !== '' ? Number(e.target.value) : '')}
                />
                <span className="text-slate-400">-</span>
                <input
                  type="number"
                  placeholder="Max"
                  className="h-9 w-full rounded-lg border border-borderLight bg-transparent px-3 text-sm outline-none dark:border-borderDark"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value !== '' ? Number(e.target.value) : '')}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Category Chips */}
      <div className="mt-6 flex flex-wrap gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedCategory('')}
          className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
            selectedCategory === ''
              ? 'bg-primary text-white shadow-md'
              : 'border border-borderLight bg-cardLight hover:bg-bgLight dark:border-borderDark dark:bg-cardDark dark:hover:bg-borderDark'
          }`}
        >
          All Products
        </button>
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
              selectedCategory === category.id
                ? 'bg-primary text-white shadow-md'
                : 'border border-borderLight bg-cardLight hover:bg-bgLight dark:border-borderDark dark:bg-cardDark dark:hover:bg-borderDark'
            }`}
          >
            {category.name}
          </button>
        ))}
      </div>

      {/* Products Display Grid */}
      {isLoading ? (
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonLoader key={i} />
          ))}
        </div>
      ) : error ? (
        <div className="mt-12 flex flex-col items-center justify-center text-red-500">
          <AlertCircle className="h-12 w-12 mb-3" />
          <p className="font-bold text-lg">Failed to retrieve catalog data</p>
          <p className="text-sm text-slate-500">Check connection to API Gateway.</p>
        </div>
      ) : products.length > 0 ? (
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {products.map((product) => {
            const isOutOfStock = product.inventory_quantity <= 0;
            return (
              <div
                key={product.id}
                className="group flex flex-col justify-between rounded-2xl border border-borderLight bg-cardLight p-4 shadow-premium hover:-translate-y-1 hover:shadow-lg transition-all duration-300 dark:border-borderDark dark:bg-cardDark"
              >
                <div>
                  {/* Product Image */}
                  <div className="relative h-48 w-full overflow-hidden rounded-xl bg-gradient-to-tr from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 flex items-center justify-center">
                    {product.image_url ? (
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    ) : null}
                    {(!product.image_url) && (
                      <span className="font-heading font-extrabold text-2xl tracking-wide opacity-20 group-hover:scale-110 transition-transform duration-300">
                        {product.name.substring(0, 3).toUpperCase()}
                      </span>
                    )}
                    {isOutOfStock && (
                      <span className="absolute top-2 right-2 rounded bg-red-500 px-2 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
                        Out of stock
                      </span>
                    )}
                  </div>

                  {/* Title and Category */}
                  <div className="mt-4">
                    <Link
                      to={`/products/${product.id}`}
                      className="font-heading font-bold text-lg leading-tight hover:text-primary transition-colors block line-clamp-1"
                    >
                      {product.name}
                    </Link>
                    <p className="mt-1.5 text-xs text-slate-500 line-clamp-2">
                      {product.description}
                    </p>
                  </div>
                </div>

                {/* Pricing & Cart controls */}
                <div className="mt-4 flex items-center justify-between">
                  <span className="font-heading text-xl font-black">
                    ${product.price.toFixed(2)}
                  </span>

                  <Button
                    size="sm"
                    variant={isOutOfStock ? 'outline' : 'primary'}
                    disabled={isOutOfStock}
                    onClick={() => handleAddToCart(product.id)}
                    isLoading={cartAddingId === product.id}
                    className="flex items-center gap-1.5"
                  >
                    <ShoppingCart className="h-4 w-4" />
                    Buy
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="mt-16 flex flex-col items-center justify-center text-slate-500">
          <AlertCircle className="h-10 w-10 text-slate-400 stroke-1 mb-2" />
          <p className="text-sm font-medium">No matching products found</p>
        </div>
      )}
    </div>
  );
};

export default ProductCatalog;
