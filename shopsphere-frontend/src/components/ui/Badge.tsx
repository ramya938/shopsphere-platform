import React from 'react';
import { OrderStatus } from '../../types';

interface BadgeProps {
  status: OrderStatus | 'ACTIVE' | 'INACTIVE';
}

export const Badge: React.FC<BadgeProps> = ({ status }) => {
  const styles: Record<string, string> = {
    CREATED: 'bg-slate-500/10 text-slate-500 border border-slate-500/20',
    PAID: 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20',
    PROCESSING: 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/20',
    SHIPPED: 'bg-amber-500/10 text-amber-500 border border-amber-500/20',
    DELIVERED: 'bg-teal-500/10 text-teal-500 border border-teal-500/20',
    CANCELLED: 'bg-red-500/10 text-red-500 border border-red-500/20',
    ACTIVE: 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20',
    INACTIVE: 'bg-red-500/10 text-red-500 border border-red-500/20',
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${styles[status] || styles.CREATED}`}>
      {status}
    </span>
  );
};

export default Badge;
