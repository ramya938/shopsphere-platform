import React from 'react';

export const SkeletonLoader: React.FC = () => {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-borderLight bg-cardLight p-4 shadow-premium dark:border-borderDark dark:bg-cardDark">
      {/* Product Image */}
      <div className="h-48 w-full animate-shimmer rounded-xl"></div>
      
      {/* Category */}
      <div className="h-4 w-1/4 animate-shimmer rounded"></div>
      
      {/* Title */}
      <div className="h-6 w-3/4 animate-shimmer rounded"></div>
      
      {/* Price and Stock */}
      <div className="flex justify-between items-center mt-2">
        <div className="h-6 w-1/3 animate-shimmer rounded"></div>
        <div className="h-8 w-1/3 animate-shimmer rounded-lg"></div>
      </div>
    </div>
  );
};

export default SkeletonLoader;
