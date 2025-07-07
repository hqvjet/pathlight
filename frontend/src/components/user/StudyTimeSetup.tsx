'use client';

import { useState } from 'react';
import { showToast } from '@/utils/toast';
import { api, storage } from '@/utils/api';
import Header from '../layout/Header';
import Image from 'next/image';
import { Montserrat } from 'next/font/google';

const montserrat = Montserrat({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
});

interface StudyTimeSetupProps {
  onComplete: () => void;
  onSkip?: () => void;
}

export default function StudyTimeSetup({ onComplete, onSkip }: StudyTimeSetupProps) {
  const [selectedHour, setSelectedHour] = useState('18');
  const [selectedMinute, setSelectedMinute] = useState('30');
  const [isLoading, setIsLoading] = useState(false);

  // Generate hour options (0-23)
  const hourOptions = Array.from({ length: 24 }, (_, i) => {
    const hour = i.toString().padStart(2, '0');
    const displayHour = i === 0 ? '12 AM' : i < 12 ? `${i} AM` : i === 12 ? '12 PM' : `${i - 12} PM`;
    return { value: hour, label: displayHour };
  });

  // Generate minute options (0-59)
  const minuteOptions = Array.from({ length: 60 }, (_, i) => {
    const minute = i.toString().padStart(2, '0');
    return { value: minute, label: minute };
  });

  const selectedTime = `${selectedHour}:${selectedMinute}`;

  const handleSetReminder = async () => {
    setIsLoading(true);
    try {
      const token = storage.getToken();
      if (!token) {
        showToast.authError('Vui lòng đăng nhập lại');
        return;
      }

      console.log('Setting reminder time:', selectedTime);

      const response = await api.user.setNotifyTime({
        remind_time: selectedTime
      });

      console.log('Response:', response);

      if (response.status === 200) {
        // Mark setup as completed
        storage.set('study_time_setup_completed', 'true');
        showToast.authSuccess('Đã đặt lịch nhắc học tập thành công!');
        onComplete();
      } else {
        showToast.authError(response.error || 'Có lỗi xảy ra, vui lòng thử lại');
      }
    } catch (error) {
      console.error('API Error:', error);
      showToast.authError('Lỗi kết nối, vui lòng thử lại');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <Header 
        variant="minimal" 
        showSocialLinks={false}
        backgroundColor="transparent"
      />

      {/* Main Content */}
      <div className="flex-1 flex pt-20">
        {/* Left side - Illustration */}
        <div className="hidden lg:flex flex-1 items-center justify-center p-8">
          <div className="max-w-lg w-full">
            <Image
              src="/assets/images/signup_success.png"
              alt="Đặt thời gian học tập"
              width={500}
              height={400}
              className="w-full h-auto object-contain"
              priority
            />
          </div>
        </div>

        {/* Right side - Setup Form */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-md w-full space-y-8">
            {/* Header */}
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <div className="w-20 h-20 flex items-center justify-center">
                  <svg className="w-10 h-10 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              
              <h1 className={`text-3xl font-bold text-gray-900 ${montserrat.className}`}>
                Đặt Thời Gian Học Tập
              </h1>
              
              <p className="text-gray-600 text-lg leading-relaxed">
                Chọn thời gian phù hợp để chúng tôi nhắc bạn học tập mỗi ngày. 
                Việc học đều đặn sẽ giúp bạn tiến bộ nhanh chóng!
              </p>
            </div>

            {/* Time Selection */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Chọn thời gian nhắc nhở:</h3>
              
              {/* Time Display */}
              <div className="text-center p-6 bg-orange-50 border-2 border-orange-200 rounded-xl">
                <div className="text-4xl font-bold text-orange-600 mb-2">
                  {selectedTime}
                </div>
                <p className="text-sm text-gray-600">Thời gian nhắc nhở đã chọn</p>
              </div>

              {/* Hour and Minute Selectors */}
              <div className="grid grid-cols-2 gap-4">
                {/* Hour Selector */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Giờ
                  </label>
                  <select
                    value={selectedHour}
                    onChange={(e) => setSelectedHour(e.target.value)}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all text-lg font-medium"
                  >
                    {hourOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Minute Selector */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Phút
                  </label>
                  <select
                    value={selectedMinute}
                    onChange={(e) => setSelectedMinute(e.target.value)}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all text-lg font-medium"
                  >
                    {minuteOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Time Description */}
              <div className="text-center p-4 bg-white rounded-lg border border-gray-200">
                <p className="text-sm text-gray-600">
                  💡 Bạn có thể thay đổi thời gian này bất cứ lúc nào trong phần cài đặt
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={handleSetReminder}
                disabled={isLoading}
                className={`w-full py-4 px-6 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold text-lg rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none ${montserrat.className}`}
              >
                {isLoading ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Đang đặt lịch...
                  </div>
                ) : (
                  'Đặt Lịch Nhắc Nhở'
                )}
              </button>

              {onSkip && (
                <button
                  onClick={onSkip}
                  disabled={isLoading}
                  className="w-full py-3 px-6 text-gray-600 hover:text-gray-800 font-medium transition-colors disabled:opacity-50"
                >
                  Bỏ qua, thiết lập sau
                </button>
              )}
            </div>

            {/* Benefits Info */}
            <div className="bg-white border border-blue-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <svg className="w-6 h-6 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-blue-800 mb-1">Tại sao nên đặt lịch nhắc?</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Duy trì thói quen học tập đều đặn</li>
                    <li>• Tăng hiệu quả ghi nhớ kiến thức</li>
                    <li>• Chọn chính xác thời gian phù hợp nhất</li>
                    <li>• Có thể thay đổi thời gian bất cứ lúc nào</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
