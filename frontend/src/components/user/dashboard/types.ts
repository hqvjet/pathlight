export interface LeaderboardUser {
  rank: number;
  name: string;
  level: number;
  experience: number;
  avatar_url?: string;
  google_avatar_url?: string;
  id?: string;
  initials: string;
  avatarKey?: number; // cache busting key
  streak?: number;
  completed_courses?: number;
  completed_quizzes?: number;
}

export interface UserProfile {
  streak?: number;
  id?: string;
  email: string;
  name: string;
  given_name?: string;
  family_name?: string;
  avatar_url?: string;
  google_avatar_url?: string;
  avatar_id?: string;
  avatarKey?: number;
  remind_time?: string;
  level?: number;
  current_exp?: number;
  require_exp?: number;
  // Course stats - from course-service
  total_courses?: number;
  completed_courses?: number;
  total_lessons?: number;
  // Quiz stats - from quiz-service
  total_quizzes?: number;
  completed_quizzes?: number;
  // User stats - from user-service
  rank?: number;
  total_users?: number;
  user_top_rank?: LeaderboardUser[];
}

export interface DashboardData {
  info: UserProfile & { user_top_rank?: LeaderboardUser[] };
  stats?: {
    study_hours?: number;
    total_courses?: number;
    completed_courses?: number;
    quiz_scores?: number;
  };
}
