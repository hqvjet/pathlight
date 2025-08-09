/**
 * =============================================================================
 * 🌐 PATHLIGHT FRONTEND - ADVANCED API CLIENT
 * =============================================================================
 * Deprecated: This monolithic api-client is now split into modular files under lib/api/
 * Keeping backward-compatible exports. Migrate imports from '@/lib/api-client' to '@/lib/api'.
 */

export * from './api/http';
import { apiClient } from './api/http';
import { authApi } from './api/auth';
import { userApi } from './api/user';
import { courseApi } from './api/course';
import { quizApi } from './api/quiz';

// Backward compatible api object
export const api = {
  // Generic methods preserved for compatibility
  get: apiClient.get.bind(apiClient),
  post: apiClient.post.bind(apiClient),
  put: apiClient.put.bind(apiClient),
  patch: apiClient.patch.bind(apiClient),
  delete: apiClient.delete.bind(apiClient),
  uploadFile: apiClient.uploadFile.bind(apiClient),
  uploadFiles: apiClient.uploadMultipleFiles.bind(apiClient),
  // Domain groups
  auth: authApi,
  user: userApi,
  course: courseApi,
  quiz: quizApi,
};

export default api;
