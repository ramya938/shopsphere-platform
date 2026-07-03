import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-lg font-semibold tracking-wide transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50';
  
  const variants = {
    primary: 'bg-primary text-white shadow-md hover:bg-primary-hover focus:ring-primary/50',
    secondary: 'bg-secondary text-white shadow-md hover:bg-secondary-hover focus:ring-secondary/50',
    danger: 'bg-red-500 text-white shadow-md hover:bg-red-600 focus:ring-red-500/50',
    outline: 'border border-borderLight bg-transparent text-textLight hover:bg-bgLight dark:border-borderDark dark:text-textDark dark:hover:bg-borderDark focus:ring-slate-500/50',
    ghost: 'bg-transparent text-textLight hover:bg-bgLight dark:text-textDark dark:hover:bg-borderDark focus:ring-slate-500/50',
  };

  const sizes = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-5 text-sm',
    lg: 'h-12 px-6 text-base',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
      ) : null}
      {children}
    </button>
  );
};

export default Button;
