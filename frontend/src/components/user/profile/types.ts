export interface UserProfile {
  id: string;
  email: string;
  given_name?: string;
  family_name?: string;
  name?: string;
  birth_date?: string;
  dob?: string;
  sex?: string;
  bio?: string;
  avatar_id?: string;
  avatar_url?: string;
  level?: number;
  current_exp?: number;
  require_exp?: number;
  course_num?: number;
  total_courses?: number;
  completed_courses?: number;
  quiz_num?: number;
  total_quizzes?: number;
  lesson_num?: number;
  created_at?: string;
}

export interface ProfileFormData {
  given_name: string;
  family_name: string;
  birth_date: string; // dd/mm/yyyy
  sex: string;
  bio: string;
}
