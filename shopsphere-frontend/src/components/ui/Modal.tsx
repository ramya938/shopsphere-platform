import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children
}) => {
  // Prevent background scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />
      
      {/* Modal Container */}
      <div className="z-10 w-full max-w-lg scale-100 rounded-2xl border border-borderLight bg-cardLight p-6 text-textLight shadow-lg transition-all duration-300 dark:border-borderDark dark:bg-cardDark dark:text-textDark">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-borderLight pb-3 dark:border-borderDark">
          {title && <h3 className="font-heading text-lg font-bold">{title}</h3>}
          <button 
            onClick={onClose}
            className="rounded-lg p-1.5 hover:bg-bgLight transition-colors dark:hover:bg-borderDark"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="mt-4">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Modal;
