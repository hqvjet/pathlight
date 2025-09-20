'use client';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useEffect, useMemo, useState } from 'react';
import { courseApi } from '@/lib/api/course';

// API models (aligned with Course Service)
type SortOption = 'latest' | 'progress_desc' | 'title_asc';
interface ApiCourseSummary { course_id: string; title: string; description: string; duration: number; lesson_num: number; finish_lesson_num: number; updated_at: string; }
interface ApiCourseListResponse { status: number; courses?: ApiCourseSummary[] }

type UICourse = { id: string; title: string; description: string; durationMonths: number; lessons: number; progress: number; status: string; updatedAt: string };

function minutesToMonths(minutes: number) {
	const months = Math.round(minutes / (30 * 24 * 60));
	return Math.max(1, months || 0);
}

function mapCourse(c: ApiCourseSummary): UICourse {
	const progress = c.lesson_num > 0 ? Math.floor((c.finish_lesson_num / c.lesson_num) * 100) : 0;
	const status = progress >= 100 ? 'Hoàn thành' : progress === 0 ? 'Bản nháp' : 'Đang học';
	return {
		id: c.course_id,
		title: c.title,
		description: c.description,
		durationMonths: minutesToMonths(c.duration || 0),
		lessons: c.lesson_num,
		progress,
		status,
		updatedAt: c.updated_at,
	};
}

export default function MyCoursesPage() {
	const [search, setSearch] = useState('');
	const [sort, setSort] = useState<SortOption>('latest');
	const [page, setPage] = useState(1);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [courses, setCourses] = useState<UICourse[]>([]);
	const pageSize = 5;

	useEffect(() => {
		let cancelled = false;
		const load = async () => {
			setLoading(true); setError(null);
			try {
				const resp = await courseApi.getAll();
				const data = resp.data as ApiCourseListResponse | undefined;
				const list = (data?.courses || []).map(mapCourse);
				if (!cancelled) setCourses(list);
			} catch {
				if (!cancelled) setError('Không thể tải danh sách khóa học.');
			} finally {
				if (!cancelled) setLoading(false);
			}
		};
		load();
		return () => { cancelled = true; };
	}, []);

	const filtered = useMemo(() => {
		let list = courses.filter((c) => c.title.toLowerCase().includes(search.toLowerCase()));
		switch (sort) {
			case 'progress_desc': list = [...list].sort((a, b) => b.progress - a.progress); break;
			case 'title_asc': list = [...list].sort((a, b) => a.title.localeCompare(b.title, 'vi')); break;
			default: list = [...list].sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
		}
		return list;
	}, [courses, search, sort]);

	const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
	const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize);

	const greeting = (() => { const h = new Date().getHours(); if (h < 12) return 'Chào buổi sáng'; if (h < 18) return 'Chào buổi chiều'; return 'Chào buổi tối'; })();

	const handleChangePage = (p: number) => { if (p < 1 || p > totalPages) return; setPage(p); };

	return (
		<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-6 sm:py-8 space-y-8">
			{/* Heading + Actions */}
			<div className="space-y-2">
				<p className="text-sm text-gray-500 font-medium tracking-wide">{greeting}</p>
				<div className="flex flex-wrap items-center justify-between gap-4">
					<h1 className="text-2xl font-semibold text-gray-900">Khóa Học Của Tôi</h1>
					<div className="flex items-center gap-3">
						<Link href="/user/generation-tracking">
							<Button variant="outline" className="border-gray-200">Theo dõi tiến trình</Button>
						</Link>
						<Link href="/user/create-course" className="inline-flex items-center gap-2 px-5 h-11 rounded-md bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold shadow-sm shadow-orange-500/30">
							<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
							Tạo Khóa Học
						</Link>
					</div>
				</div>
			</div>

			{/* Filters */}
			<div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
				<div className="flex-1 relative">
					<input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Tìm khóa học ..." className="w-full h-11 pl-10 pr-4 rounded-lg border border-transparent bg-white shadow-sm focus:ring-2 focus:ring-orange-500/40 focus:border-orange-400 text-sm placeholder:text-gray-400 transition" />
					<svg className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.2-5.2M17 10a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
				</div>
				<div className="flex items-center gap-2">
					<label className="text-xs font-medium text-gray-500 uppercase tracking-wide hidden sm:block">Sắp xếp</label>
					<div className="relative">
						<select value={sort} onChange={(e) => setSort(e.target.value as SortOption)} className="appearance-none h-11 pl-4 pr-10 rounded-lg bg-white border border-transparent shadow-sm text-sm focus:ring-2 focus:ring-orange-500/40 focus:border-orange-400 cursor-pointer">
							<option value="latest">Mới nhất</option>
							<option value="progress_desc">Tiến độ giảm dần</option>
							<option value="title_asc">Theo tên A-Z</option>
						</select>
						<svg className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
					</div>
				</div>
			</div>

			{/* Loading / Error */}
			{loading && (
				<div className="bg-white rounded-xl p-12 text-center border border-gray-100 shadow-sm">
					<div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 mx-auto"></div>
					<p className="mt-4 text-gray-600">Đang tải danh sách khóa học...</p>
				</div>
			)}
			{!loading && error && (
				<div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200">{error}</div>
			)}

			{/* Course List */}
			{!loading && !error && (
				<div className="space-y-6">
					{pageItems.map((course) => (
						<div key={course.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition group relative">
							<button className="absolute top-4 right-3 text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100" aria-label="Menu">
								<svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zm6 0a2 2 0 11-4 0 2 2 0 014 0zm4 2a2 2 0 100-4 2 2 0 000 4z" /></svg>
							</button>
							<h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2 pr-10 line-clamp-2 group-hover:text-orange-600 transition-colors">{course.title}</h2>
							<p className="text-gray-600 text-sm leading-relaxed line-clamp-3 mb-4">{course.description}</p>
							<div className="flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-gray-600 mb-4">
								<div className="flex items-center gap-2">
									<svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l2.5 2.5M12 22a10 10 0 100-20 10 10 0 000 20z" /></svg>
									{course.durationMonths} Month
								</div>
								<div>{course.lessons} Lesson</div>
								<div className="flex items-center gap-3 w-full sm:w-auto flex-1 sm:flex-none">
									<div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
										<div className="h-full bg-gradient-to-r from-sky-500 to-cyan-500" style={{ width: course.progress + '%' }} aria-label={`Tiến độ ${course.progress}%`} />
									</div>
									<span className="text-xs font-medium text-gray-500 min-w-[34px] text-right">{course.progress}%</span>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">{course.status}</span>
								<button className="ml-auto text-sm font-semibold text-orange-600 hover:text-orange-700">Tiếp tục học</button>
							</div>
						</div>
					))}
					{pageItems.length === 0 && (
						<div className="bg-white rounded-xl p-12 text-center border border-dashed border-gray-300">
							<p className="text-gray-600 mb-4">Không tìm thấy khóa học phù hợp.</p>
							<Link href="/user/create-course" className="inline-flex items-center gap-2 px-5 h-11 rounded-md bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold shadow-sm">
								<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
								Tạo Khóa Học Mới
							</Link>
						</div>
					)}
				</div>
			)}

			{/* Pagination */}
			{!loading && !error && totalPages > 1 && (
				<div className="flex items-center justify-center gap-2 pt-4">
					<button onClick={() => handleChangePage(page - 1)} disabled={page === 1} className="w-9 h-9 flex items-center justify-center rounded-full text-gray-500 hover:text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white shadow-sm border border-gray-200">
						<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
					</button>
					{Array.from({ length: totalPages }).map((_, i) => { const p = i + 1; const active = p === page; return (
						<button key={p} onClick={() => handleChangePage(p)} className={`w-9 h-9 rounded-full text-sm font-medium transition shadow-sm border ${active ? 'bg-orange-500 text-white border-orange-500' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'}`}>{p.toString().padStart(2, '0')}</button>
					); })}
					<button onClick={() => handleChangePage(page + 1)} disabled={page === totalPages} className="w-9 h-9 flex items-center justify-center rounded-full text-gray-500 hover:text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white shadow-sm border border-gray-200">
						<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
					</button>
				</div>
			)}

			{/* Footer links */}
			<footer className="pt-4 pb-10 text-xs text-gray-400 flex flex-wrap gap-6 justify-center">
				<span>FAQs</span>
				<span>Privacy Policy</span>
				<span>Terms & Condition</span>
			</footer>
		</div>
	);
}
