import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ShoppingBag, ShoppingCart, User, Calendar, DollarSign, Activity } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { orderService } from '../services/order.service';
import { Badge } from '../components/ui/Badge';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => orderService.getMyOrders(),
  });

  const recentOrders = orders.slice(0, 5);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-primary to-secondary p-6 text-white shadow-lg md:p-8">
        <h1 className="font-heading text-3xl font-extrabold md:text-4xl">
          Hello, {user?.full_name}!
        </h1>
        <p className="mt-2 text-sm text-white/80 max-w-xl">
          Welcome to your ShopSphere AI workspace. You are signed in as a{' '}
          <span className="font-bold underline">{user?.role}</span>. Manage your shopping cart, view orders, and track deliveries.
        </p>
      </div>

      {/* Quick Stats & Navigation */}
      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
        <Link
          to="/"
          className="flex items-center gap-4 rounded-xl border border-borderLight bg-cardLight p-5 hover:border-primary transition-all duration-200 shadow-premium dark:border-borderDark dark:bg-cardDark dark:hover:border-primary"
        >
          <div className="rounded-lg bg-primary/10 p-3 text-primary">
            <ShoppingBag className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-heading font-bold">Browse Catalog</h3>
            <p className="text-xs text-slate-500">Explore products & categories</p>
          </div>
        </Link>

        <Link
          to="/cart"
          className="flex items-center gap-4 rounded-xl border border-borderLight bg-cardLight p-5 hover:border-secondary transition-all duration-200 shadow-premium dark:border-borderDark dark:bg-cardDark dark:hover:border-secondary"
        >
          <div className="rounded-lg bg-secondary/10 p-3 text-secondary">
            <ShoppingCart className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-heading font-bold">Shopping Cart</h3>
            <p className="text-xs text-slate-500">Review items & checkout</p>
          </div>
        </Link>

        <Link
          to="/profile"
          className="flex items-center gap-4 rounded-xl border border-borderLight bg-cardLight p-5 hover:border-slate-400 transition-all duration-200 shadow-premium dark:border-borderDark dark:bg-cardDark dark:hover:border-slate-600"
        >
          <div className="rounded-lg bg-slate-500/10 p-3 text-slate-500">
            <User className="h-6 w-6" />
          </div>
          <div>
            <h3 className="font-heading font-bold">User Profile</h3>
            <p className="text-xs text-slate-500">Update security & settings</p>
          </div>
        </Link>
      </div>

      {/* Recent Orders Section */}
      <div className="mt-10 rounded-2xl border border-borderLight bg-cardLight p-6 shadow-premium dark:border-borderDark dark:bg-cardDark">
        <div className="flex items-center justify-between border-b border-borderLight pb-4 dark:border-borderDark">
          <h2 className="font-heading text-xl font-bold flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Recent Order Activity
          </h2>
          <Link to="/orders" className="text-xs font-semibold text-primary hover:underline">
            View All Orders
          </Link>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-10">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          </div>
        ) : recentOrders.length > 0 ? (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-borderLight dark:border-borderDark">
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4">Placed Date</th>
                  <th className="py-3 px-4">Shipping Address</th>
                  <th className="py-3 px-4">Total Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderLight dark:divide-borderDark">
                {recentOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-bgLight dark:hover:bg-borderDark/45 transition-colors">
                    <td className="py-4 px-4 font-mono text-xs max-w-[120px] truncate">
                      <Link to={`/orders?id=${order.id}`} className="text-primary hover:underline">
                        {order.id}
                      </Link>
                    </td>
                    <td className="py-4 px-4 flex items-center gap-1.5 text-xs">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-4 text-xs max-w-[200px] truncate">{order.shipping_address}</td>
                    <td className="py-4 px-4 font-bold text-xs">
                      ${order.total_price.toFixed(2)}
                    </td>
                    <td className="py-4 px-4 text-center">
                      <Badge status={order.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-slate-500">
            <Calendar className="h-10 w-10 text-slate-400 stroke-1 mb-2" />
            <p className="text-sm font-medium">No order activity found</p>
            <Link to="/" className="mt-3 rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-primary-hover transition-colors">
              Shop Now
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
