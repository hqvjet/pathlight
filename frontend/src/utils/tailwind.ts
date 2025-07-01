// Tailwind CSS utility classes and configurations for PathLight

export const colors = {
  primary: {
    50: '#fff7ed',
    100: '#ffedd5',
    200: '#fed7aa',
    300: '#fdba74',
    400: '#fb923c',
    500: '#f97316', // Main orange brand color
    600: '#ea580c',
    700: '#c2410c',
    800: '#9a3412',
    900: '#7c2d12',
  },
  secondary: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e', // Main green accent color
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  }
} as const;

export const spacing = {
  xs: '0.5rem',    // 8px
  sm: '0.75rem',   // 12px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
  '3xl': '4rem',   // 64px
} as const;

export const borderRadius = {
  sm: '0.25rem',   // 4px
  md: '0.375rem',  // 6px
  lg: '0.5rem',    // 8px
  xl: '0.75rem',   // 12px
  '2xl': '1rem',   // 16px
  '3xl': '1.5rem', // 24px
} as const;

// Common button classes
export const buttonClasses = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  outline: 'btn-outline',
  base: 'px-4 py-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2',
} as const;

// Common input classes
export const inputClasses = {
  base: 'input-field',
  error: 'input-field border-red-500 focus:ring-red-500',
  success: 'input-field border-green-500 focus:ring-green-500',
} as const;

// Common card classes
export const cardClasses = {
  base: 'card',
  interactive: 'card hover:scale-105 cursor-pointer',
  bordered: 'card border-2',
} as const;

// Common text classes
export const textClasses = {
  gradient: 'text-gradient',
  heading: 'font-bold text-gray-900',
  subheading: 'font-semibold text-gray-700',
  body: 'text-gray-600',
  caption: 'text-sm text-gray-500',
  responsive: {
    xl: 'text-responsive-xl',
    lg: 'text-responsive-lg',
    base: 'text-responsive-base',
  }
} as const;

// Common animation classes
export const animationClasses = {
  fadeIn: 'animate-fade-in',
  slideUp: 'animate-slide-up',
  bounce: 'animate-bounce-soft',
  spin: 'animate-spin',
} as const;

// Layout utility functions
export const cn = (...classes: (string | undefined | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};

// Responsive breakpoints (matching Tailwind defaults)
export const breakpoints = {
  sm: '640px',   // Mobile landscape
  md: '768px',   // Tablet
  lg: '1024px',  // Desktop
  xl: '1280px',  // Large desktop
  '2xl': '1536px', // Extra large desktop
} as const;

// Common screen size checks
export const screens = {
  mobile: `(max-width: ${breakpoints.md})`,
  tablet: `(min-width: ${breakpoints.md}) and (max-width: ${breakpoints.lg})`,
  desktop: `(min-width: ${breakpoints.lg})`,
  wide: `(min-width: ${breakpoints.xl})`,
} as const;
