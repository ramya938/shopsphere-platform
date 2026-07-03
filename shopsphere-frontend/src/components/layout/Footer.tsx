import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-borderLight bg-cardLight py-6 text-center text-xs text-slate-500 transition-colors duration-300 dark:border-borderDark dark:bg-cardDark dark:text-slate-400">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="font-medium">
          &copy; {new Date().getFullYear()} ShopSphere AI. All rights reserved.
        </p>
        <p className="mt-1 text-[10px] text-slate-400 dark:text-slate-500">
          Powered by Clean Architecture, FastAPI, Apache Kafka, and Redis.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
