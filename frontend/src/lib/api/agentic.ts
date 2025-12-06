import { apiClient } from './http';

export type AgenticCourseLevel = 'overview' | 'intermediate' | 'advance';
export type AgenticCourseConstraint =
  | 'professional'
  | 'academic'
  | 'friendly'
  | 'humorous'
  | 'chuyen-nghiep'
  | 'hoc-thuat'
  | 'gan-gui'
  | 'di-dom';

export interface CreateAgenticCourseRequest {
  user_position: string;
  short_user_prompt: string;
  course_duration: number; // unit: days
  documents?: string[];
  course_level: AgenticCourseLevel;
  course_constraint: AgenticCourseConstraint | string;
}

export interface AgenticAssessmentOption {
  option_content: string;
  option_correction: boolean | 0 | 1;
}

export interface AgenticAssessment {
  assessment_question: string;
  assessment_hint: string;
  assessment_explaination: string;
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
    apiClient.post<AgenticCourseResponse>(`/agentic/create-course`, payload),
};
