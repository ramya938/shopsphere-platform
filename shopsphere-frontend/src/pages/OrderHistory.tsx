import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, DollarSign, MapPin, Package, AlertCircle } from 'lucide-react';
import { orderService } from '../services/order.service';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const OrderHistory: React.FC = () => {
  const queryClient = useQueryClient();
  const location = useLocation();
  
  // Extract specific order ID query parameter if present
  const queryParams = new URLSearchParams(location.search);
  const highlightedOrderId = queryParams.get('id');

  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(highlightedOrderId);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const { data: orders = [], isLoading, error } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => orderService.getMyOrders(),
  });

  useEffect(() => {
    if (highlightedOrderId) {
      setExpandedOrderId(highlightedOrderId);
    }
  }, [highlightedOrderId]);

  // Mutation for cancelling an order
  const cancelOrderMutation = useMutation({
    mutationFn: (orderId: string) => orderService.cancelOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-orders'] });
    },
  });

  const handleCancelOrder = async (orderId: string) => {
    if (!window.confirm('Are you sure you want to cancel this order? This will restock items.')) {
      return;
    }
    setCancellingId(orderId);
    try {
      await cancelOrderMutation.mutateAsync(orderId);
    } catch (err) {
      console.error('Error cancelling order:', err);
    } finally {
      setCancellingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center text-red-500">
        <AlertCircle className="h-12 w-12 mx-auto mb-3" />
        <p className="font-bold text-lg font-heading">Failed to fetch order history</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      <h1 className="font-heading text-3xl font-extrabold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-8">
        My Orders
      </h1>

      {orders.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 rounded-2xl border border-dashed border-borderLight bg-cardLight dark:border-borderDark dark:bg-cardDark">
          <Package className="h-16 w-16 text-slate-400 stroke-1 mb-3" />
          <p className="font-medium text-slate-500">You haven't placed any orders yet</p>
          <Link to="/" className="mt-4">
            <Button variant="primary" size="sm">Browse Products</Button>
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {orders.map((order) => {
            const isExpanded = expandedOrderId === order.id;
            const canCancel = order.status !== 'DELIVERED' && order.status !== 'CANCELLED' && order.status !== 'SHIPPED';

            return (
              <div
                key={order.id}
                id={`order-${order.id}`}
                className={`rounded-2xl border bg-cardLight shadow-premium overflow-hidden transition-all duration-300 dark:bg-cardDark
                  ${isExpanded 
                    ? 'border-primary dark:border-primary' 
                    : 'border-borderLight dark:border-borderDark hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
              >
                {/* Order Summary Header */}
                <div
                  onClick={() => setExpandedOrderId(isExpanded ? null : order.id)}
                  className="flex flex-wrap items-center justify-between gap-4 p-5 cursor-pointer select-none"
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-mono text-xs font-bold text-slate-400">ORDER ID: {order.id.substring(0, 18)}...</span>
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      <Calendar className="h-3.5 w-3.5" />
                      {new Date(order.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="block font-heading font-extrabold text-sm sm:text-base">${order.total_price.toFixed(2)}</span>
                      <span className="text-[10px] text-slate-400">{order.items?.length || 0} items</span>
                    </div>
                    <Badge status={order.status} />
                  </div>
                </div>

                {/* Expanded Details Section */}
                {isExpanded && (
                  <div className="border-t border-borderLight bg-bgLight/40 p-5 dark:border-borderDark dark:bg-borderDark/20">
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                      {/* Shipping info */}
                      <div>
                        <h4 className="font-heading font-bold text-xs text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                          <MapPin className="h-4 w-4" />
                          Shipping Destination
                        </h4>
                        <p className="text-xs font-semibold leading-relaxed bg-cardLight dark:bg-cardDark border border-borderLight dark:border-borderDark p-3 rounded-lg">
                          {order.shipping_address}
                        </p>
                      </div>

                      {/* Controls / Cancel options */}
                      <div className="flex flex-col justify-end items-start sm:items-end">
                        {canCancel && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleCancelOrder(order.id)}
                            isLoading={cancellingId === order.id}
                          >
                            Cancel Order
                          </Button>
                        )}
                        {!canCancel && order.status === 'CANCELLED' && (
                          <span className="text-xs text-red-500 font-semibold bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-lg">
                            This order was cancelled. Restocked.
                          </span>
                        )}
                        {!canCancel && order.status === 'DELIVERED' && (
                          <span className="text-xs text-emerald-500 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
                            Successfully delivered to destination.
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Order Items List */}
                    <div className="mt-6">
                      <h4 className="font-heading font-bold text-xs text-slate-500 uppercase tracking-wider mb-3">
                        Order Content
                      </h4>
                      <div className="flex flex-col gap-3">
                        {order.items?.map((item) => (
                          <div
                            key={item.id}
                            className="flex items-center justify-between rounded-xl bg-cardLight border border-borderLight p-3 text-xs dark:bg-cardDark dark:border-borderDark"
                          >
                            <div>
                              <span className="font-bold text-sm block">{item.product_name || 'Product Details'}</span>
                              <span className="text-slate-400 block font-mono text-[10px]">ID: {item.product_id}</span>
                            </div>
                            <div className="text-right">
                              <span className="font-bold block">${(item.price ?? item.price_at_purchase ?? 0).toFixed(2)}</span>
                              <span className="text-slate-400 font-medium">Qty: {item.quantity}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default OrderHistory;
