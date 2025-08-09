// Barrel exports for modular API
export * from './http';
export { authApi } from './auth';
export { userApi } from './user';
export { courseApi } from './course';
export { quizApi } from './quiz';

// Unified api object (new preferred usage)
import { authApi } from './auth';
import { userApi } from './user';
import { courseApi } from './course';
import { quizApi } from './quiz';
import { apiClient } from './http';

export const api = {
  auth: authApi,
  user: userApi,
  course: courseApi,
  quiz: quizApi,
  client: apiClient,
};
