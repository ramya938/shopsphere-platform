import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Context Providers
import { ThemeProvider } from './hooks/useTheme';
import { AuthProvider } from './hooks/useAuth';
import { CartProvider } from './hooks/useCart';

// Layout Components
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import RouteGuard from './components/layout/RouteGuard';
import AdminRouteGuard from './components/layout/AdminRouteGuard';

// Pages
import ProductCatalog from './pages/ProductCatalog';
import ProductDetails from './pages/ProductDetails';
import ShoppingCart from './pages/ShoppingCart';
import Checkout from './pages/Checkout';
import OrderHistory from './pages/OrderHistory';
import UserProfile from './pages/UserProfile';
import AdminDashboard from './pages/AdminDashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

// Initialize React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const LayoutWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex min-h-screen flex-col bg-bgLight text-textLight transition-colors duration-300 dark:bg-bgDark dark:text-textDark">
      <Navbar />
      <main className="flex-grow">{children}</main>
      <Footer />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <CartProvider>
            <Router>
              <LayoutWrapper>
                <Routes>
                  {/* Public routes */}
                  <Route path="/" element={<ProductCatalog />} />
                  <Route path="/products/:id" element={<ProductDetails />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />

                  {/* Protected customer routes */}
                  <Route
                    path="/dashboard"
                    element={
                      <RouteGuard>
                        <Dashboard />
                      </RouteGuard>
                    }
                  />
                  <Route
                    path="/cart"
                    element={
                      <RouteGuard>
                        <ShoppingCart />
                      </RouteGuard>
                    }
                  />
                  <Route
                    path="/checkout"
                    element={
                      <RouteGuard>
                        <Checkout />
                      </RouteGuard>
                    }
                  />
                  <Route
                    path="/orders"
                    element={
                      <RouteGuard>
                        <OrderHistory />
                      </RouteGuard>
                    }
                  />
                  <Route
                    path="/profile"
                    element={
                      <RouteGuard>
                        <UserProfile />
                      </RouteGuard>
                    }
                  />

                  {/* Protected admin-only routes */}
                  <Route
                    path="/admin"
                    element={
                      <RouteGuard>
                        <AdminRouteGuard>
                          <AdminDashboard />
                        </AdminRouteGuard>
                      </RouteGuard>
                    }
                  />

                  {/* Fallback route */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </LayoutWrapper>
            </Router>
          </CartProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
