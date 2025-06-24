'use client';

import Link from 'next/link';
import Image from 'next/image';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Image src="/icons/LOGO.svg" alt="PathLight logo" width={120} height={32} className="h-8 w-auto" />
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative hidden md:block">
                <input
                  type="text"
                  placeholder="Bạn muốn tìm kiếm gì...?"
                  className="border border-gray-300 px-4 py-2 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
                <svg className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <Link href="/notifications" className="p-2 text-gray-600 hover:text-gray-800">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5-5v-5a3 3 0 00-6 0v5l-5 5h5m5 0v1a3 3 0 01-6 0v-1m6 0H9" />
                </svg>
              </Link>
              <Link href="/profile" className="flex items-center">
                <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative w-full h-[500px] bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
        {/* Background Study Image */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-full h-full max-w-6xl mx-auto flex items-center justify-center px-4">
            {/* Laptop and Study Setup */}
            <div className="relative">
              <div className="w-80 h-60 bg-gray-800 rounded-lg shadow-2xl transform rotate-2">
                {/* Laptop Screen */}
                <div className="w-full h-44 bg-white rounded-t-lg p-4 m-2">
                  <div className="w-full h-full bg-gradient-to-br from-blue-100 to-orange-100 rounded flex items-center justify-center">
                    <span className="text-xs font-semibold text-gray-600">STUDY</span>
                  </div>
                </div>
                {/* Laptop Base */}
                <div className="w-full h-12 bg-gray-700 rounded-b-lg"></div>
              </div>
              
              {/* Notebook */}
              <div className="absolute -right-16 top-8 w-24 h-32 bg-white rounded shadow-lg transform -rotate-12 border-l-4 border-orange-400">
                <div className="p-2">
                  <div className="space-y-1">
                    <div className="h-1 bg-gray-300 rounded"></div>
                    <div className="h-1 bg-gray-300 rounded w-3/4"></div>
                    <div className="h-1 bg-gray-300 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
              
              {/* Pen */}
              <div className="absolute -right-8 top-20 w-16 h-2 bg-orange-500 rounded-full transform rotate-45 shadow-md"></div>
              
              {/* Eraser */}
              <div className="absolute -right-12 top-32 w-8 h-3 bg-pink-400 rounded shadow transform rotate-12"></div>
            </div>
          </div>
        </div>
        
        {/* Hero Content Overlay */}
        <div className="relative z-10 max-w-6xl mx-auto px-4 h-full flex items-center">
          <div className="text-left max-w-2xl">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4 leading-tight">
              NỀN TẢNG A.I <br />
              <span className="text-orange-500">DẪN LỐI TỰ HỌC</span> <br />
              CÁ NHÂN HÓA
            </h1>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              PathLight biến tài liệu (PDF, video, word...) tự động thành hệ thống tự học, 
              sinh lộ trình, giao bài, chương trình, tạo bộ kiểm tra và mentor 24/7.
            </p>
            <Link href="/auth/signup" className="inline-block bg-green-500 hover:bg-green-600 text-white px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
              Tham Gia Ngay
            </Link>
          </div>
        </div>
      </section>

      {/* What PathLight offers */}
      <section className="bg-white py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">PathLight mang đến điều gì?</h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mt-1">
                <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Ingestion & RAG</h3>
                <p className="text-sm text-gray-600">Nhập tài liệu, tách đoạn quan trọng và đánh index thông minh</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mt-1">
                <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Lộ trình học thích ứng</h3>
                <p className="text-sm text-gray-600">Thuật toán theo dõi mục tiêu, nền tảng, lịch học để sắp xếp bài học hợp lý</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mt-1">
                <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Bài giảng & Đánh giá tự động</h3>
                <p className="text-sm text-gray-600">Sinh nội dung, nhặt quiz, kèm bộ câu hỏi chấm điểm tức thì</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mt-1">
                <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Mentor 24/7 & Gamification</h3>
                <p className="text-sm text-gray-600">Chatbot theo dõi chấm, XP, badge, quest, minigame giúp duy trì động lực</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Challenges Solved */}
      <section className="bg-gray-50 py-16 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <h3 className="text-2xl font-bold text-gray-800 mb-10">Những thách thức PathLight đã giải quyết</h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">Quá tải tài liệu</h4>
              <p className="text-gray-600 text-sm">Khó lọc kiến thức phù hợp</p>
            </div>
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">Thiếu lộ trình rõ ràng</h4>
              <p className="text-gray-600 text-sm">& cam kết thời gian</p>
            </div>
            <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h4 className="font-semibold text-gray-800 mb-2">Giáo viên khó theo dõi tiến độ</h4>
              <p className="text-gray-600 text-sm">Can thiệp kịp thời</p>
            </div>
          </div>
        </div>
      </section>

      {/* Solutions Section */}
      <section className="bg-white py-16 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <h3 className="text-2xl font-bold text-gray-800 mb-10">Giải pháp của chúng tôi</h3>
          <p className="text-gray-600 mb-12 max-w-3xl mx-auto">
            PathLight giúp mỗi người học tiếp cận mọi tài liệu tả năng học tương tác, có roadmap, đánh giá và bài học chính mất ít số mình học - tất cả trên một nền tảng AI duy nhất.
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gray-50 p-8 rounded-lg hover:shadow-lg transition-shadow">
              <div className="w-20 h-20 bg-gray-200 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <span className="text-2xl font-bold text-gray-400">1</span>
              </div>
              <h4 className="font-semibold mb-3 text-gray-800">Product 1</h4>
              <Link href="#" className="text-green-600 hover:text-green-700 font-medium">
                Readmore →
              </Link>
            </div>
            <div className="bg-gray-50 p-8 rounded-lg hover:shadow-lg transition-shadow">
              <div className="w-20 h-20 bg-gray-200 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <span className="text-2xl font-bold text-gray-400">2</span>
              </div>
              <h4 className="font-semibold mb-3 text-gray-800">Product 2</h4>
              <Link href="#" className="text-green-600 hover:text-green-700 font-medium">
                Readmore →
              </Link>
            </div>
            <div className="bg-gray-50 p-8 rounded-lg hover:shadow-lg transition-shadow">
              <div className="w-20 h-20 bg-gray-200 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <span className="text-2xl font-bold text-gray-400">3</span>
              </div>
              <h4 className="font-semibold mb-3 text-gray-800">Product 3</h4>
              <Link href="#" className="text-green-600 hover:text-green-700 font-medium">
                Readmore →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="bg-gray-50 py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h3 className="text-2xl font-bold text-gray-800 text-center mb-10">Khách hàng nói gì về PathLight</h3>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-start mb-4">
                <div className="w-12 h-12 bg-gray-300 rounded-full flex-shrink-0 mr-4"></div>
                <div>
                  <div className="font-semibold text-gray-800">Đặng Hoài Nam</div>
                  <div className="text-sm text-gray-500">Giảng viên tiếng Anh</div>
                </div>
              </div>
              <p className="text-gray-700 leading-relaxed">
                "Hệ thống analytics giúp tôi sớm phát hiện vấn đề 'nguy cơ', cảm thấy nhẹ nhàng và chỉ cần thi là hoàn thành khóa học lên 87%."
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-start mb-4">
                <div className="w-12 h-12 bg-gray-300 rounded-full flex-shrink-0 mr-4"></div>
                <div>
                  <div className="font-semibold text-gray-800">Tấn Quang Nam</div>
                  <div className="text-sm text-gray-500">Giảng viên Tin học</div>
                </div>
              </div>
              <p className="text-gray-700 leading-relaxed">
                "Hệ thống giúp tôi soạn bài giảng siêu nhanh, bớt lặp lại. Học viên phản hồi rất tích cực và về sau tỉ lệ có đủ điểm để đậu tăng đều. Tỉ lệ học sinh vượt chuẩn các lần test lên đến 95%."
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-100 py-6 text-center text-sm text-gray-500">
        <p>FAQs · Privacy Policy · Terms & Condition</p>
      </footer>
    </div>
  );
}
