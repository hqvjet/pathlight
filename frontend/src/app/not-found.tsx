import Image from 'next/image';
import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="min-h-screen flex flex-col bg-white text-gray-900">
      <div className="flex-1 w-full flex items-center justify-center px-6">
        <div className="w-full max-w-7xl flex flex-col lg:flex-row items-center justify-between gap-12 py-12 lg:py-0">
          {/* Left */}
          <div className="flex-1 max-w-xl w-full">
            <h1 className="text-[56px] leading-none font-light text-gray-300 mb-6">Error 404</h1>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight mb-8">
              Ôi không! Có vẻ bạn đang bị lạc đường
            </h2>
            <Link
              href="/"
              className="inline-block bg-orange-500 hover:bg-orange-600 text-white font-medium text-sm px-8 py-3 rounded transition-colors"
            >
              Trở Về Trang Chính
            </Link>
          </div>

          {/* Right */}
          <div className="flex-1 flex items-center justify-center w-full">
            <div className="relative w-full max-w-xl">
              <Image
                src="/assets/images/error_page.png"
                alt="404 illustration"
                width={960}
                height={640}
                priority
                className="w-full h-auto select-none"
              />
            </div>
          </div>
        </div>
      </div>

      <footer className="w-full border-t border-gray-200 py-6 text-xs text-gray-500">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-center gap-8">
          <Link href="/faqs" className="hover:text-gray-700 transition-colors">FAQs</Link>
          <Link href="/privacy" className="hover:text-gray-700 transition-colors">Privacy Policy</Link>
          <Link href="/terms" className="hover:text-gray-700 transition-colors">Terms & Condition</Link>
        </div>
      </footer>
    </main>
  );
}
