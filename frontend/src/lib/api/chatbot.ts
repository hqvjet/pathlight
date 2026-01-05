/** Chatbot API helpers for course-service chatbot endpoints */
import { apiClient } from './http';

export interface ChatbotQuestionRequest {
  message: string;
  lesson_id: string;
  course_id: string;
  chat_id?: string;
  chat_history?: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
}

export interface ChatbotQuestionResponse {
  status: number;
  chat_id: string;
  message: string;
}

export interface ChatContextChunk {
  chunk_text: string;
  document_source: string;
  score: number;
}

export interface ChatbotAnswerDetail {
  chat_id: string;
  message: string;
  answer: string;
  lesson_id: string;
  course_id: string;
  user_id: string;
  status: 'processing' | 'done' | 'error';
  error_message?: string;
  context_chunks: ChatContextChunk[];
  created_at: string;
  updated_at: string;
}

export interface ChatbotAnswerResponse {
  status: number;
  chat?: ChatbotAnswerDetail;
  message?: string;
}

export const chatbotApi = {
  submitQuestion: (payload: ChatbotQuestionRequest) =>
    apiClient.post<ChatbotQuestionResponse>('/course/chatbot/question', payload),
  
  getAnswer: (chatId: string) =>
    apiClient.get<ChatbotAnswerResponse>(`/course/chatbot/answer/${chatId}`),
};
