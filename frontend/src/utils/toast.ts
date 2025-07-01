import { toast, ToastOptions } from 'react-toastify';

// Custom toast configuration
const defaultToastOptions: ToastOptions = {
  position: "top-right",
  autoClose: 5000,
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

export const showToast = {
  success: (message: string, options?: ToastOptions) => {
    toast.success(message, { ...defaultToastOptions, ...options });
  },
  
  error: (message: string, options?: ToastOptions) => {
    toast.error(message, { ...defaultToastOptions, ...options });
  },
  
  warning: (message: string, options?: ToastOptions) => {
    toast.warning(message, { ...defaultToastOptions, ...options });
  },
  
  info: (message: string, options?: ToastOptions) => {
    toast.info(message, { ...defaultToastOptions, ...options });
  },
  
  // Custom styled toasts
  authError: (message: string) => {
    toast.error(message, {
      ...defaultToastOptions,
      className: 'auth-error-toast',
    });
  },
  
  authSuccess: (message: string) => {
    toast.success(message, {
      ...defaultToastOptions,
      className: 'auth-success-toast',
    });
  },
};

export default showToast;
