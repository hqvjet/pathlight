'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Rocket, Clock, BookOpen, Gamepad2, Search, Sparkles } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-emerald-50">
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur supports-[backdrop-filter]:bg-white/70 border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2 font-semibold text-lg">
              <Image src="/assets/icons/logo.png" alt="PathLight logo" width={120} height={32} className="h-8 w-auto" />
            </Link>
            <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
              <Link href="#features" className="hover:text-foreground transition">Tính năng</Link>
              <Link href="#solutions" className="hover:text-foreground transition">Giải pháp</Link>
              <Link href="#testimonials" className="hover:text-foreground transition">Chứng thực</Link>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden md:block relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-5 w-5 text-muted-foreground" />
              <Input placeholder="Bạn muốn tìm kiếm gì...?" className="pl-9" />
            </div>
            <Button variant="ghost" asChild>
              <Link href="/auth/signin">Đăng nhập</Link>
            </Button>
            <Button asChild>
              <Link href="/auth/signup">Bắt đầu</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-transparent via-orange-100/40 to-transparent" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 flex flex-col lg:flex-row items-center gap-16">
          <div className="flex-1">
            <Badge variant="secondary" className="mb-4 gap-1">
              <Sparkles className="w-3.5 h-3.5" /> AI Learning Platform
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 text-gray-900">
              NỀN TẢNG A.I <span className="text-orange-600">DẪN LỐI TỰ HỌC</span> CÁ NHÂN HÓA
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground leading-relaxed mb-8 max-w-2xl">
              PathLight biến tài liệu (PDF, video, word...) tự động thành hệ thống tự học, sinh lộ trình, giao bài, chương trình, tạo bộ kiểm tra và mentor 24/7.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" asChild>
                <Link href="/auth/signup">Tham Gia Ngay</Link>
              </Button>
              <Button variant="outline" size="lg" asChild>
                <Link href="#features">Xem tính năng</Link>
              </Button>
            </div>
          </div>
          <div className="flex-1 relative">
            <div className="absolute -inset-6 bg-gradient-to-tr from-orange-200/40 via-white to-emerald-200/40 rounded-3xl blur-2xl" />
            <div className="relative h-[360px] w-full flex items-center justify-center">
              <div className="relative">
                <div className="w-80 h-60 bg-gray-900 rounded-xl shadow-2xl rotate-2 ring-8 ring-white/40">
                  <div className="w-full h-44 bg-white rounded-t-xl p-4 m-2">
                    <div className="w-full h-full bg-gradient-to-br from-orange-50 to-emerald-50 rounded flex items-center justify-center text-sm font-semibold text-gray-600 tracking-wide">
                      STUDY FLOW
                    </div>
                  </div>
                  <div className="w-full h-12 bg-gray-800 rounded-b-xl flex items-center justify-center text-xs text-gray-400">AI ENGINE</div>
                </div>
                <div className="absolute -right-16 top-8 w-24 h-32 bg-white/80 backdrop-blur rounded-lg shadow-lg -rotate-6 border border-orange-200 p-2">
                  <div className="space-y-1">
                    <div className="h-1.5 bg-orange-200 rounded" />
                    <div className="h-1.5 bg-emerald-200 rounded w-3/4" />
                    <div className="h-1.5 bg-orange-200 rounded w-1/2" />
                  </div>
                </div>
                <div className="absolute -right-10 top-24 w-20 h-20 bg-gradient-to-br from-orange-500 to-emerald-500 rounded-full shadow-xl animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: <Rocket className="w-5 h-5" />, title: 'Ingestion & RAG', desc: 'Nhập tài liệu, tách đoạn & index thông minh' },
              { icon: <BookOpen className="w-5 h-5" />, title: 'Lộ trình thích ứng', desc: 'Theo dõi mục tiêu & lịch học cá nhân' },
              { icon: <Clock className="w-5 h-5" />, title: 'Đánh giá tự động', desc: 'Sinh quiz & chấm điểm ngay lập tức' },
              { icon: <Gamepad2 className="w-5 h-5" />, title: 'Gamification', desc: 'XP, badge, quest & minigame giữ động lực' },
            ].map((f) => (
              <Card key={f.title} className="group">
                <CardHeader className="space-y-2">
                  <div className="w-10 h-10 rounded-lg bg-orange-500/10 text-orange-600 flex items-center justify-center group-hover:bg-orange-500 group-hover:text-white transition">
                    {f.icon}
                  </div>
                  <CardTitle>{f.title}</CardTitle>
                  <CardDescription>{f.desc}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Challenges */}
      <section className="py-20 bg-muted/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-2xl font-bold mb-10">Những thách thức PathLight giải quyết</h3>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { color: 'from-red-500 to-rose-500', title: 'Quá tải tài liệu', desc: 'Khó lọc kiến thức phù hợp' },
              { color: 'from-amber-500 to-orange-500', title: 'Thiếu lộ trình rõ ràng', desc: 'Và cam kết thời gian' },
              { color: 'from-sky-500 to-blue-600', title: 'Khó theo dõi tiến độ', desc: 'Can thiệp kịp thời' },
            ].map((c) => (
              <Card key={c.title} className="relative overflow-hidden">
                <div className={`absolute inset-0 bg-gradient-to-br ${c.color} opacity-10`} />
                <CardHeader>
                  <CardTitle>{c.title}</CardTitle>
                  <CardDescription>{c.desc}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Solutions */}
      <section id="solutions" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-2xl font-bold mb-6">Giải pháp của chúng tôi</h3>
          <p className="text-muted-foreground mb-12 max-w-3xl mx-auto">
            PathLight giúp mỗi người học tương tác với mọi tài liệu, có roadmap, đánh giá và bài học cốt lõi trên một nền tảng AI duy nhất.
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            {['Product 1', 'Product 2', 'Product 3'].map((p, i) => (
              <Card key={p} className="hover:shadow-lg transition group">
                <CardHeader>
                  <div className="w-20 h-20 bg-gradient-to-br from-orange-100 to-emerald-100 rounded-lg mx-auto flex items-center justify-center mb-2 text-2xl font-bold text-gray-500 group-hover:scale-105 transition">
                    {i + 1}
                  </div>
                  <CardTitle>{p}</CardTitle>
                  <CardDescription>Lorem ipsum dolor sit amet.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="link" className="px-0">Read more →</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 bg-muted/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-2xl font-bold text-center mb-12">Khách hàng nói gì về PathLight</h3>
          <div className="grid md:grid-cols-2 gap-8">
            {[
              { name: 'Đặng Hoài Nam', role: 'Giảng viên tiếng Anh', content: 'Hệ thống analytics giúp tôi phát hiện sớm vấn đề, giảm tải công việc và nâng tỷ lệ hoàn thành khóa lên 87%.' },
              { name: 'Tấn Quang Nam', role: 'Giảng viên Tin học', content: 'Soạn bài giảng nhanh hơn, học viên hào hứng hơn và tỷ lệ vượt chuẩn các bài test đạt đến 95%.' }
            ].map((t) => (
              <Card key={t.name} className="relative">
                <CardHeader className="pb-2 flex flex-row items-start gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-emerald-400 text-white flex items-center justify-center font-semibold shadow-md">
                    {t.name.split(' ').slice(-1)[0][0]}
                  </div>
                  <div>
                    <CardTitle className="text-base">{t.name}</CardTitle>
                    <CardDescription>{t.role}</CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 text-sm leading-relaxed text-muted-foreground">
                  “{t.content}”
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white/70 backdrop-blur py-8 text-center text-sm text-muted-foreground">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="order-2 md:order-1">© {new Date().getFullYear()} PathLight. All rights reserved.</p>
            <div className="flex items-center gap-6 order-1 md:order-2">
              <Link href="#" className="hover:text-foreground">FAQs</Link>
              <Link href="#" className="hover:text-foreground">Privacy</Link>
              <Link href="#" className="hover:text-foreground">Terms</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
