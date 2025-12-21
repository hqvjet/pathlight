'use client';

import { useState } from 'react';
import { showToast } from '@/utils/toast';
import { storage } from '@/utils/api';
import { api } from '@/lib/api';
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

interface NotifyTimeResponse { status: number; message?: string; error?: string; }

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

      const response = await api.user.setNotifyTime({ remind_time: selectedTime }) as NotifyTimeResponse;

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
    <div className="min-h-screen bg-gradient-to-b from-orange-50 via-white to-white">
      <main className="px-4 sm:px-6 py-10 sm:py-14">
        <div className="max-w-5xl mx-auto">
          <div className="bg-white shadow-lg border border-orange-100 rounded-2xl p-5 sm:p-8 lg:p-10 space-y-8">
            <div className="flex flex-col lg:flex-row lg:items-center gap-6 lg:gap-10">
              <div className="space-y-3 flex-1">
                <div className="inline-flex items-center gap-2 rounded-full bg-orange-50 text-orange-700 px-3 py-1 text-sm font-semibold">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Nhắc học hằng ngày
                </div>
                <h1 className={`text-2xl sm:text-3xl font-bold text-gray-900 ${montserrat.className}`}>
                  Đặt thời gian học tập
                </h1>
                <p className="text-gray-600 text-base sm:text-lg leading-relaxed">
                  Chọn khung giờ cố định để PathLight gửi nhắc nhở. Bạn có thể đổi bất cứ lúc nào trong phần cài đặt.
                </p>
              </div>
              <div className="flex-1 flex justify-center lg:justify-end">
                <Image src="/assets/images/signup_success.png" alt="Đặt thời gian" width={220} height={180} className="max-w-[220px] w-full h-auto object-contain" />
              </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <div className="rounded-2xl border border-orange-100 bg-orange-50 px-5 py-4 sm:px-6 sm:py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <p className="text-sm text-orange-700 font-medium">Thời gian nhắc</p>
                    <div className="text-3xl sm:text-4xl font-bold text-orange-600 mt-1 tracking-tight">{selectedTime}</div>
                  </div>
                  <div className="text-xs text-orange-600 bg-white/80 px-3 py-1 rounded-full border border-orange-100 self-start sm:self-center">Giữ thói quen mỗi ngày</div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">Giờ</label>
                    <select
                      value={selectedHour}
                      onChange={(e) => setSelectedHour(e.target.value)}
                      className="w-full h-12 px-3 rounded-xl border border-gray-200 bg-white text-base font-medium focus:ring-2 focus:ring-orange-300 focus:border-orange-400 transition"
                    >
                      {hourOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="block text-sm font-semibold text-gray-700">Phút</label>
                    <select
                      value={selectedMinute}
                      onChange={(e) => setSelectedMinute(e.target.value)}
                      className="w-full h-12 px-3 rounded-xl border border-gray-200 bg-white text-base font-medium focus:ring-2 focus:ring-orange-300 focus:border-orange-400 transition"
                    >
                      {minuteOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                  <span className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl">
                    <svg className="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Có thể đổi bất cứ lúc nào
                  </span>
                  <span className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl">
                    <svg className="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Nhắc mỗi ngày vào giờ bạn chọn
                  </span>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <button
                    onClick={handleSetReminder}
                    disabled={isLoading}
                    className={`w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold shadow-md hover:shadow-lg transition transform hover:-translate-y-0.5 disabled:opacity-60 disabled:transform-none ${montserrat.className}`}
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Đang lưu...
                      </div>
                    ) : (
                      'Lưu thời gian nhắc'
                    )}
                  </button>
                  {onSkip && (
                    <button
                      onClick={onSkip}
                      disabled={isLoading}
                      className="w-full sm:w-auto px-6 py-3 rounded-xl border border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50 font-medium transition disabled:opacity-60"
                    >
                      Bỏ qua, làm sau
                    </button>
                  )}
                </div>
              </div>

              <div className="space-y-3 rounded-2xl border border-gray-100 bg-gray-50 p-5 text-sm text-gray-700">
                <h3 className="text-base font-semibold text-gray-800">Lợi ích</h3>
                <ul className="space-y-2">
                  <li className="flex gap-2"><span className="text-orange-500">•</span> Giữ nhịp học ổn định mỗi ngày</li>
                  <li className="flex gap-2"><span className="text-orange-500">•</span> Giảm quên lịch học khi bận rộn</li>
                  <li className="flex gap-2"><span className="text-orange-500">•</span> Linh hoạt đổi giờ bất cứ lúc nào</li>
                  <li className="flex gap-2"><span className="text-orange-500">•</span> Nhắc nhẹ, không làm phiền</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
