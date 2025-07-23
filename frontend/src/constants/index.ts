/**
 * =============================================================================
 * 🔗 PATHLIGHT FRONTEND - CONSTANTS
 * =============================================================================
 * Centralized constants for the PathLight application
 */

// =============================================================================
// 🏷️ APPLICATION CONSTANTS
// =============================================================================
export const APP_CONSTANTS = {
  NAME: 'PathLight',
  DESCRIPTION: 'Your Learning Management System',
  VERSION: '1.0.0',
  AUTHOR: 'PathLight Team',
} as const;

// =============================================================================
// 🔐 AUTHENTICATION CONSTANTS
// =============================================================================
export const AUTH_CONSTANTS = {
  TOKEN_KEY: 'token',
  REFRESH_TOKEN_KEY: 'refresh_token',
  PENDING_EMAIL_KEY: 'pending_email',
  USER_KEY: 'user',
  REMEMBER_ME_KEY: 'remember_me',
  
  // Token expiration times (in milliseconds)
  ACCESS_TOKEN_EXPIRY: 24 * 60 * 60 * 1000, // 24 hours
  REFRESH_TOKEN_EXPIRY: 7 * 24 * 60 * 60 * 1000, // 7 days
  
  // Password requirements
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_REQUIREMENTS: {
    minLength: 8,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
  },
} as const;

// =============================================================================
// 🌐 API CONSTANTS
// =============================================================================
export const API_CONSTANTS = {
  TIMEOUT: 15000, // 15 seconds (reduced from 30s for better UX)
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
  
  // HTTP Status Codes
  STATUS_CODES: {
    OK: 200,
    CREATED: 201,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    INTERNAL_SERVER_ERROR: 500,
  },
  
  // Content Types
  CONTENT_TYPES: {
    JSON: 'application/json',
    FORM_DATA: 'multipart/form-data',
    URL_ENCODED: 'application/x-www-form-urlencoded',
  },
} as const;

// =============================================================================
// 🎨 UI CONSTANTS
// =============================================================================
export const UI_CONSTANTS = {
  // Breakpoints (matching Tailwind CSS)
  BREAKPOINTS: {
    SM: 640,
    MD: 768,
    LG: 1024,
    XL: 1280,
    '2XL': 1536,
  },
  
  // Animation durations (in milliseconds)
  ANIMATIONS: {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500,
  },
  
  // Z-index levels
  Z_INDEX: {
    DROPDOWN: 1000,
    STICKY: 1020,
    FIXED: 1030,
    MODAL_BACKDROP: 1040,
    MODAL: 1050,
    POPOVER: 1060,
    TOOLTIP: 1070,
    TOAST: 1080,
  },
  
  // Common sizes
  SIZES: {
    SIDEBAR_WIDTH: 280,
    HEADER_HEIGHT: 64,
    FOOTER_HEIGHT: 80,
  },
} as const;

// =============================================================================
// 📄 PAGINATION CONSTANTS
// =============================================================================
export const PAGINATION_CONSTANTS = {
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

// =============================================================================
// 📊 VALIDATION CONSTANTS
// =============================================================================
export const VALIDATION_CONSTANTS = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE_REGEX: /^\+?[\d\s\-\(\)]+$/,
  URL_REGEX: /^https?:\/\/[^\s/$.?#].[^\s]*$/,
  
  // File upload limits
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  ALLOWED_DOCUMENT_TYPES: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
} as const;

// =============================================================================
// 🎓 COURSE CONSTANTS
// =============================================================================
export const COURSE_CONSTANTS = {
  DIFFICULTY_LEVELS: {
    BEGINNER: 'beginner',
    INTERMEDIATE: 'intermediate',
    ADVANCED: 'advanced',
    EXPERT: 'expert',
  },
  
  STATUS: {
    DRAFT: 'draft',
    PUBLISHED: 'published',
    ARCHIVED: 'archived',
  },
  
  ENROLLMENT_STATUS: {
    NOT_ENROLLED: 'not_enrolled',
    ENROLLED: 'enrolled',
    COMPLETED: 'completed',
    DROPPED: 'dropped',
  },
} as const;

// =============================================================================
// 📝 QUIZ CONSTANTS
// =============================================================================
export const QUIZ_CONSTANTS = {
  QUESTION_TYPES: {
    MULTIPLE_CHOICE: 'multiple_choice',
    TRUE_FALSE: 'true_false',
    SHORT_ANSWER: 'short_answer',
    ESSAY: 'essay',
    FILL_IN_BLANK: 'fill_in_blank',
  },
  
  STATUS: {
    NOT_STARTED: 'not_started',
    IN_PROGRESS: 'in_progress',
    COMPLETED: 'completed',
    SUBMITTED: 'submitted',
    GRADED: 'graded',
  },
  
  // Time limits (in minutes)
  DEFAULT_TIME_LIMIT: 60,
  MAX_TIME_LIMIT: 240,
} as const;

// =============================================================================
// 🚨 ERROR CONSTANTS
// =============================================================================
export const ERROR_CONSTANTS = {
  MESSAGES: {
    NETWORK_ERROR: 'Lỗi kết nối mạng. Vui lòng thử lại.',
    UNAUTHORIZED: 'Bạn không có quyền truy cập. Vui lòng đăng nhập lại.',
    FORBIDDEN: 'Bạn không có quyền thực hiện hành động này.',
    NOT_FOUND: 'Không tìm thấy trang hoặc tài nguyên yêu cầu.',
    SERVER_ERROR: 'Lỗi server. Vui lòng thử lại sau.',
    VALIDATION_ERROR: 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.',
    TIMEOUT_ERROR: 'Yêu cầu quá thời gian chờ. Vui lòng thử lại.',
  },
  
  CODES: {
    NETWORK_ERROR: 'NETWORK_ERROR',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
    AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
    NOT_FOUND_ERROR: 'NOT_FOUND_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  },
} as const;

// =============================================================================
// 🎯 ROUTES CONSTANTS
// =============================================================================
export const ROUTES = {
  // Public routes
  HOME: '/',
  ABOUT: '/about',
  CONTACT: '/contact',
  
  // Auth routes
  AUTH: {
    SIGNIN: '/auth/signin',
    SIGNUP: '/auth/signup',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
    VERIFY_EMAIL: '/auth/verify-email',
  },
  
  // Protected routes
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  
  // Course routes
  COURSES: {
    LIST: '/courses',
    DETAIL: (id: string) => `/courses/${id}`,
    LESSON: (courseId: string, lessonId: string) => `/courses/${courseId}/lessons/${lessonId}`,
  },
  
  // Quiz routes
  QUIZZES: {
    LIST: '/quizzes',
    DETAIL: (id: string) => `/quizzes/${id}`,
    TAKE: (id: string) => `/quizzes/${id}/take`,
    RESULTS: (id: string) => `/quizzes/${id}/results`,
  },
  
  // Admin routes
  ADMIN: {
    DASHBOARD: '/admin',
    USERS: '/admin/users',
    COURSES: '/admin/courses',
    QUIZZES: '/admin/quizzes',
    SETTINGS: '/admin/settings',
  },
} as const;

// =============================================================================
// 🔄 LOCAL STORAGE KEYS
// =============================================================================
export const STORAGE_KEYS = {
  // Authentication
  TOKEN: 'pathlight_token',
  REFRESH_TOKEN: 'pathlight_refresh_token',
  USER: 'pathlight_user',
  PENDING_EMAIL: 'pathlight_pending_email',
  
  // User preferences
  THEME: 'pathlight_theme',
  LANGUAGE: 'pathlight_language',
  SIDEBAR_COLLAPSED: 'pathlight_sidebar_collapsed',
  
  // Course progress
  COURSE_PROGRESS: 'pathlight_course_progress',
  QUIZ_PROGRESS: 'pathlight_quiz_progress',
  
  // UI state
  LAST_VISITED_PAGE: 'pathlight_last_visited_page',
  NOTIFICATION_SETTINGS: 'pathlight_notification_settings',
} as const;

// =============================================================================
// 🌍 LOCALIZATION CONSTANTS
// =============================================================================
export const LOCALE_CONSTANTS = {
  DEFAULT_LOCALE: 'vi',
  SUPPORTED_LOCALES: ['vi', 'en'],
  FALLBACK_LOCALE: 'en',
  
  DATE_FORMATS: {
    SHORT: 'dd/MM/yyyy',
    MEDIUM: 'dd/MM/yyyy HH:mm',
    LONG: 'dd MMMM yyyy HH:mm:ss',
  },
} as const;
