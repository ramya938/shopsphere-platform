import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  id,
  className = '',
  ...props
}) => {
  return (
    <div className="flex w-full flex-col gap-1.5">
      {label && (
        <label
          htmlFor={id}
          className="text-xs font-semibold text-slate-500 dark:text-slate-400"
        >
          {label}
        </label>
      )}
      <input
        id={id}
        className={`h-10 rounded-lg border bg-transparent px-3 text-sm outline-none transition-all duration-200 focus:ring-2
          ${error 
            ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' 
            : 'border-borderLight hover:border-slate-400 dark:border-borderDark dark:hover:border-slate-600 focus:border-primary focus:ring-primary/20'
          } ${className}`}
        {...props}
      />
      {error && (
        <span className="text-[11px] font-medium text-red-500">
          {error}
        </span>
      )}
    </div>
  );
};

export default Input;
