'use client';

interface NotificationProps {
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  onClose?: () => void;
}

export default function Notification({ type, title, message, onClose }: NotificationProps) {
  const styles = {
    success: {
      container: 'bg-green-50 border border-green-200',
      icon: 'text-green-500',
      title: 'text-green-800',
      message: 'text-green-700'
    },
    error: {
      container: 'bg-red-50 border border-red-200',
      icon: 'text-red-500',
      title: 'text-red-800',
      message: 'text-red-700'
    },
    info: {
      container: 'bg-blue-50 border border-blue-200',
      icon: 'text-blue-500',
      title: 'text-blue-800',
      message: 'text-blue-700'
    },
    warning: {
      container: 'bg-yellow-50 border border-yellow-200',
      icon: 'text-yellow-500',
      title: 'text-yellow-800',
      message: 'text-yellow-700'
    }
  };

  const icons = {
    success: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    error: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    info: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    warning: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    )
  };

  const currentStyle = styles[type];

  return (
    <div className={`${currentStyle.container} rounded-lg p-4 mb-4`}>
      <div className="flex items-start">
        <div className={`${currentStyle.icon} mt-0.5 mr-3`}>
          {icons[type]}
        </div>
        <div className="flex-1">
          <h3 className={`font-medium ${currentStyle.title} mb-1`}>{title}</h3>
          <p className={`text-sm ${currentStyle.message}`}>{message}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className={`${currentStyle.icon} hover:opacity-70 ml-3`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
