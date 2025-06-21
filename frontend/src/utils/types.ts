export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Course {
  id: string;
  title: string;
  description: string;
  created_at: string;
}

export interface Quiz {
  id: string;
  title: string;
  description: string;
  course_id: string;
}
