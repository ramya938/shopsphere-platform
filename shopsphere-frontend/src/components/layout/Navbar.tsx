import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, User, Sun, Moon, LogOut, Menu, X, LayoutDashboard, ShoppingBag, ShieldAlert } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useCart } from '../../hooks/useCart';
import { useTheme } from '../../hooks/useTheme';

export const Navbar: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const { cartCount } = useCart();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-borderLight bg-cardLight/80 text-textLight shadow-premium backdrop-blur-md transition-colors duration-300 dark:border-borderDark dark:bg-cardDark/80 dark:text-textDark">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2 font-heading text-xl font-extrabold tracking-tight">
              <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                ShopSphere AI
              </span>
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden items-center gap-6 md:flex">
            <Link to="/" className="hover:text-primary transition-colors flex items-center gap-1.5 text-sm font-medium">
              <ShoppingBag className="h-4.5 w-4.5" />
              Catalog
            </Link>
            
            {isAuthenticated && (
              <>
                <Link to="/dashboard" className="hover:text-primary transition-colors flex items-center gap-1.5 text-sm font-medium">
                  <LayoutDashboard className="h-4.5 w-4.5" />
                  Dashboard
                </Link>
                {user?.role === 'ADMIN' && (
                  <Link to="/admin" className="hover:text-secondary transition-colors flex items-center gap-1.5 text-sm font-semibold text-secondary">
                    <ShieldAlert className="h-4.5 w-4.5" />
                    Admin
                  </Link>
                )}
              </>
            )}
          </div>

          {/* Utility Buttons */}
          <div className="hidden items-center gap-4 md:flex">
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleTheme}
              className="rounded-full p-2 hover:bg-bgLight transition-colors dark:hover:bg-borderDark"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="h-5 w-5 text-yellow-400" /> : <Moon className="h-5 w-5 text-gray-500" />}
            </button>

            {/* Shopping Cart */}
            <Link
              to="/cart"
              className="relative rounded-full p-2 hover:bg-bgLight transition-colors dark:hover:bg-borderDark"
            >
              <ShoppingCart className="h-5 w-5" />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">
                  {cartCount}
                </span>
              )}
            </Link>

            {/* User Controls */}
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <Link to="/profile" className="flex items-center gap-1.5 hover:text-primary transition-colors text-sm font-medium">
                  <User className="h-4.5 w-4.5" />
                  {user?.full_name.split(' ')[0]}
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 rounded-lg bg-red-500/10 px-3 py-1.5 text-sm font-semibold text-red-500 hover:bg-red-500/20 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link to="/login" className="text-sm font-medium hover:text-primary transition-colors">
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="rounded-lg bg-gradient-to-r from-primary to-secondary px-4 py-2 text-sm font-bold text-white shadow-md hover:opacity-90 transition-opacity"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-3 md:hidden">
            <button
              onClick={toggleTheme}
              className="rounded-full p-2 hover:bg-bgLight transition-colors dark:hover:bg-borderDark"
            >
              {theme === 'dark' ? <Sun className="h-5 w-5 text-yellow-400" /> : <Moon className="h-5 w-5 text-gray-500" />}
            </button>
            <Link
              to="/cart"
              className="relative rounded-full p-2 hover:bg-bgLight transition-colors dark:hover:bg-borderDark"
            >
              <ShoppingCart className="h-5 w-5" />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">
                  {cartCount}
                </span>
              )}
            </Link>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="rounded-full p-2 hover:bg-bgLight transition-colors dark:hover:bg-borderDark"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="border-t border-borderLight bg-cardLight px-4 pt-2 pb-4 shadow-lg md:hidden dark:border-borderDark dark:bg-cardDark">
          <div className="flex flex-col gap-3">
            <Link
              to="/"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 hover:bg-bgLight rounded-md transition-colors text-sm font-medium"
            >
              Catalog
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2 hover:bg-bgLight rounded-md transition-colors text-sm font-medium"
                >
                  Dashboard
                </Link>
                {user?.role === 'ADMIN' && (
                  <Link
                    to="/admin"
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-3 py-2 hover:bg-bgLight rounded-md text-secondary transition-colors text-sm font-semibold"
                  >
                    Admin Area
                  </Link>
                )}
                <Link
                  to="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2 hover:bg-bgLight rounded-md transition-colors text-sm font-medium"
                >
                  My Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-red-500 hover:bg-red-500/10 rounded-md transition-colors text-sm font-medium"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </>
            ) : (
              <div className="flex flex-col gap-2 mt-2 px-3">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex h-10 items-center justify-center rounded-lg border border-borderLight text-sm font-medium hover:bg-bgLight transition-colors dark:border-borderDark dark:hover:bg-borderDark"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex h-10 items-center justify-center rounded-lg bg-gradient-to-r from-primary to-secondary text-sm font-bold text-white shadow-md hover:opacity-90 transition-opacity"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
