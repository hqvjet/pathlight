'use client';

import React, { useState, useEffect, useRef } from 'react';
import { chatbotApi } from '@/lib/api/chatbot';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatbotProps {
  lessonId: string;
  courseId: string;
}

export default function LessonChatbot({ lessonId, courseId }: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [showIdlePrompt, setShowIdlePrompt] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [pendingChatId, setPendingChatId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastActivityRef = useRef<number>(Date.now());
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcome(false);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const resetIdleTimer = () => {
      lastActivityRef.current = Date.now();
      setShowIdlePrompt(false);
      
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
      
      idleTimerRef.current = setTimeout(() => {
        setShowIdlePrompt(true);
        setTimeout(() => setShowIdlePrompt(false), 10000);
      }, 2 * 60 * 1000);
    };

    const handleActivity = () => resetIdleTimer();
    
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('scroll', handleActivity);
    
    resetIdleTimer();

    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('scroll', handleActivity);
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!pendingChatId) return;

    const pollAnswer = async () => {
      try {
        const response = await chatbotApi.getAnswer(pendingChatId);
        const data = response.data;
        
        if (data.status === 200 && data.chat) {
          setMessages(prev => [
            ...prev,
            {
              id: data.chat!.chat_id,
              role: 'assistant',
              content: data.chat!.answer,
              timestamp: new Date(data.chat!.updated_at),
            },
          ]);
          setPendingChatId(null);
          setIsLoading(false);
        } else if (data.status === 500) {
          const errorMessage = data.message || 'Xin lỗi, mình gặp lỗi khi xử lý câu hỏi của bạn. Bạn có thể thử lại không?';
          setMessages(prev => [
            ...prev,
            {
              id: pendingChatId,
              role: 'assistant',
              content: `Xin lỗi, đã xảy ra lỗi: ${errorMessage}`,
              timestamp: new Date(),
            },
          ]);
          setPendingChatId(null);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error polling answer:', error);
        setPendingChatId(null);
        setIsLoading(false);
      }
    };

    pollingIntervalRef.current = setInterval(pollAnswer, 2000);
    pollAnswer();

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [pendingChatId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await chatbotApi.submitQuestion({
        message: inputValue,
        lesson_id: lessonId,
        course_id: courseId,
        chat_history: messages.map(m => ({
          role: m.role,
          content: m.content,
        })),
      });

      setPendingChatId(response.data.chat_id);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Xin lỗi, có lỗi xảy ra khi gửi câu hỏi. Vui lòng thử lại!',
          timestamp: new Date(),
        },
      ]);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {showWelcome && !isOpen && (
        <div className="absolute bottom-20 right-0 mb-2 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-lg px-4 py-3 w-56 relative">
            <div className="absolute bottom-0 right-8 w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-white transform translate-y-full"></div>
            <p className="text-sm text-gray-800 leading-relaxed">
              Có gì thắc mắc khó hiểu<br />bạn cứ hỏi mình nhé! 😊
            </p>
          </div>
        </div>
      )}

      {showIdlePrompt && !isOpen && (
        <div className="absolute bottom-20 right-0 mb-2 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-lg px-4 py-3 w-64 relative">
            <div className="absolute bottom-0 right-8 w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-white transform translate-y-full"></div>
            <p className="text-sm text-gray-800 leading-relaxed">
              Bạn có cần mình giải thích<br />thêm phần này không? 🤔
            </p>
          </div>
        </div>
      )}

      {/* Floating Chat Icon Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-gradient-to-r from-gray-700 to-gray-800 text-white p-2 rounded-full shadow-2xl hover:shadow-3xl hover:scale-110 transition-all duration-300 animate-scale-in"
          aria-label="Mở trợ lý chat"
        >
          <svg className="w-12 h-12" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
            {/* Robot head */}
            <rect x="6" y="8" width="12" height="10" rx="3" />
            {/* Eyes */}
            <circle cx="9" cy="12" r="0.8" fill="currentColor" />
            <circle cx="15" cy="12" r="0.8" fill="currentColor" />
            {/* Mouth */}
            <path d="M9 15h6" strokeLinecap="round" />
            {/* Antennas */}
            <line x1="8" y1="8" x2="8" y2="5" strokeLinecap="round" />
            <line x1="16" y1="8" x2="16" y2="5" strokeLinecap="round" />
            <circle cx="8" cy="4.5" r="1" />
            <circle cx="16" cy="4.5" r="1" />
            {/* Base */}
            <line x1="10" y1="18" x2="14" y2="18" strokeLinecap="round" strokeWidth={2} />
          </svg>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="bg-white rounded-2xl shadow-2xl w-80 h-[500px] flex flex-col mb-4 animate-scale-in">
          {/* Header */}
          <div className="bg-gradient-to-r from-gray-700 to-gray-800 text-white p-4 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-700" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                </svg>
              </div>
              <div>
                <h3 className="font-semibold">Trợ lý Pathlight</h3>
                <p className="text-xs text-gray-300">Luôn sẵn sàng hỗ trợ bạn</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {/* Initial greeting */}
            {messages.length === 0 && (
              <div className="flex gap-3">
                <div className="bg-white rounded-2xl p-3 shadow-sm max-w-[85%]">
                  <p className="text-sm text-gray-800">
                    Chào bạn! Mình là trợ lý Pathlight. Trong quá trình học nếu có gì khó hiểu, bạn cứ hỏi mình nhé!
                  </p>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`rounded-2xl p-3 shadow-sm max-w-[85%] ${
                    message.role === 'user'
                      ? 'bg-gray-600 text-white'
                      : 'bg-white text-gray-800'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="bg-white rounded-2xl p-3 shadow-sm">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Nhập câu hỏi của bạn..."
                disabled={isLoading}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="bg-gray-600 text-white p-2 rounded-full hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-5 h-5 rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes scale-in {
          from {
            opacity: 0;
            transform: scale(0.9);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }

        .animate-scale-in {
          animation: scale-in 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}
