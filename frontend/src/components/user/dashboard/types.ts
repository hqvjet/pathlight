export interface LeaderboardUser {
  rank: number;
  name: string;
  level: number;
  experience: number;
  avatar_url?: string;
  id?: string;
  initials: string;
}

export interface UserProfile {
  id?: string;
  email: string;
  name: string;
  given_name?: string;
  family_name?: string;
  avatar_url?: string;
  avatar_id?: string;
  remind_time?: string;
  level?: number;
  current_exp?: number;
  require_exp?: number;
  course_num?: number;
  total_courses?: number;
  completed_courses?: number;
  finish_course_num?: number;
  quiz_num?: number;
  total_quizzes?: number;
  lesson_num?: number;
  average_score?: number;
  average_quiz_score?: number;
  study_streak?: number;
  total_study_time?: number;
  rank?: number;
  user_num?: number;
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
