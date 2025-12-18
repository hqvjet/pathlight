import { apiClient } from './http';

export type AgenticCourseLevel = 'overview' | 'intermediate' | 'advance';
export type AgenticCourseConstraint =
  | 'professional'
  | 'academic'
  | 'friendly'
  | 'humorous';

export interface CreateAgenticCourseRequest {
  type?: 'generate_course' | 'generate_quiz';
  user_role: string;
  short_prompt: string;
  course_duration: number; // unit: days
  documents?: string[];
  course_level: AgenticCourseLevel;
  course_constraint: AgenticCourseConstraint | string;
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

export const agenticApi = {
  createCourse: (payload: CreateAgenticCourseRequest) =>
    apiClient.post<AgenticCourseResponse>(`/course/create`, payload),
};
