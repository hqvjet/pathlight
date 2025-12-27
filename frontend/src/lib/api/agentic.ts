import { apiClient } from './http';

export type AgenticCourseLevel = 'overview' | 'intermediate' | 'advance';
export type AgenticCourseConstraint =
  | 'professional'
  | 'academic'
  | 'friendly'
  | 'humorous';

export interface CreateAgenticCourseRequest {
  type?: 'GENERATE_COURSE_WITH_VECTORIZE';
  id?: string; // Course ID, auto-generated if omitted
  s3_keys: string[]; // Required: array of S3 object keys
  difficulty?: string; // "easy" | "medium" | "hard", defaults to "medium"
  duration: number; // Course duration in minutes (not days!)
  user_id?: string; // Will be overridden by token on backend
}

export interface AgenticAssessmentOption {
  option_content: string;
  option_correction: boolean;
}

export interface AgenticAssessment {
  assessment_question: string;
  assessment_hint: string;
  assessment_explanation: string;
  assessment_level: number;
  assessment_options: AgenticAssessmentOption[];
}

export interface AgenticLesson {
  lesson_title: string;
  lesson_level: number;
  lesson_content: string;
  lesson_assessments: AgenticAssessment[];
}

export interface AgenticCourseResponse {
  course_title: string;
  course_overview: string;
  course_level: number;
  course_duration: number; // unit: days
  course_lessons: AgenticLesson[];
}

export interface AgenticQueuedCreateResponse {
  status?: number;
  message?: string;
  course_id?: string;
  sqs_message_id?: string;
}

export type AgenticCreateCourseResponse = AgenticCourseResponse | AgenticQueuedCreateResponse;

export const agenticApi = {
  createCourse: (payload: CreateAgenticCourseRequest) =>
    apiClient.post<AgenticCreateCourseResponse>(`/course/create`, payload),
};
