'use client';
import Link from 'next/link';
import { useState, useMemo } from 'react';

interface QuizItem {
	id: string;
	title: string;
	description: string;
	questions: number;
	progress: number; // percent done or built
	status: 'Nháp' | 'Công khai' | 'Đang làm';
	updatedAt: string; // ISO date string
}

const fakeQuizzes: QuizItem[] = [
	{
		id: 'q1',
		title: 'JavaScript Cơ Bản',
		description: 'Ôn tập kiến thức nền tảng: scope, hoisting, closure, prototype, async.',
		questions: 40,
		progress: 70,
		status: 'Nháp',
		updatedAt: '2025-08-05',
	},
	{
		id: 'q2',
		title: 'React Hooks Nâng Cao',
		description: 'Tập trung vào performance tối ưu và patterns tái sử dụng hook.',
		questions: 25,
		progress: 100,
		status: 'Công khai',
		updatedAt: '2025-08-03',
	},
	{
		id: 'q3',
		title: 'Thuật Toán Cơ Bản',
		description: 'Kiểm tra kỹ năng giải quyết bài toán với array, string, hash map, recursion.',
		questions: 60,
		progress: 10,
		status: 'Nháp',
		updatedAt: '2025-07-28',
	},
];

type SortOption = 'latest' | 'questions_desc' | 'title_asc';

export default function MyQuizzesPage() {
	const [search, setSearch] = useState('');
	const [sort, setSort] = useState<SortOption>('latest');

	const filtered = useMemo(() => {
		let list = fakeQuizzes.filter((q) =>
			q.title.toLowerCase().includes(search.toLowerCase())
		);
		switch (sort) {
			case 'questions_desc':
				list = [...list].sort((a, b) => b.questions - a.questions);
				break;
			case 'title_asc':
				list = [...list].sort((a, b) => a.title.localeCompare(b.title, 'vi'));
				break;
			default:
				list = [...list].sort(
					(a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
				);
		}
		return list;
	}, [search, sort]);

	const greeting = (() => {
		const h = new Date().getHours();
		if (h < 12) return 'Chào buổi sáng';
		if (h < 18) return 'Chào buổi chiều';
		return 'Chào buổi tối';
	})();

	return (
		<div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-8">
			<div className="space-y-2">
				<p className="text-sm text-gray-500 font-medium tracking-wide">{greeting}</p>
				<div className="flex flex-wrap items-center justify-between gap-4">
					<h1 className="text-2xl font-semibold text-gray-900">Bộ Câu Hỏi Của Tôi</h1>
					<Link
						href="/user/create-quiz"
						className="inline-flex items-center gap-2 px-5 h-11 rounded-md bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold shadow-sm shadow-sky-500/30"
					>
						<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
						</svg>
						Tạo Quiz
					</Link>
				</div>
			</div>

			<div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
				<div className="flex-1 relative">
					<input
						value={search}
						onChange={(e) => setSearch(e.target.value)}
						placeholder="Tìm quiz ..."
						className="w-full h-11 pl-10 pr-4 rounded-lg border border-transparent bg-white shadow-sm focus:ring-2 focus:ring-sky-500/40 focus:border-sky-400 text-sm placeholder:text-gray-400 transition"
					/>
					<svg className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
						<path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.2-5.2M17 10a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>
				<div className="flex items-center gap-2">
					<label className="text-xs font-medium text-gray-500 uppercase tracking-wide hidden sm:block">Sắp xếp</label>
					<div className="relative">
						<select
							value={sort}
							onChange={(e) => setSort(e.target.value as SortOption)}
							className="appearance-none h-11 pl-4 pr-10 rounded-lg bg-white border border-transparent shadow-sm text-sm focus:ring-2 focus:ring-sky-500/40 focus:border-sky-400 cursor-pointer"
						>
							<option value="latest">Mới nhất</option>
							<option value="questions_desc">Số câu hỏi giảm dần</option>
							<option value="title_asc">Theo tên A-Z</option>
						</select>
						<svg className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
						</svg>
					</div>
				</div>
			</div>

			<div className="space-y-6">
				{filtered.map((quiz) => (
					<div key={quiz.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition group relative">
						<button className="absolute top-4 right-3 text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100" aria-label="Menu">
							<svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
								<path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zm6 0a2 2 0 11-4 0 2 2 0 014 0zm4 2a2 2 0 100-4 2 2 0 000 4z" />
							</svg>
						</button>
						<h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2 pr-10 line-clamp-2 group-hover:text-sky-600 transition-colors">
							{quiz.title}
						</h2>
						<p className="text-gray-600 text-sm leading-relaxed line-clamp-3 mb-4">{quiz.description}</p>
						<div className="flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-gray-600 mb-4">
							<div className="flex items-center gap-2">
								<svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l2.5 2.5M12 22a10 10 0 100-20 10 10 0 000 20z" />
								</svg>
								{quiz.questions} câu hỏi
							</div>
							<div className="flex items-center gap-3 w-full sm:w-auto flex-1 sm:flex-none">
								<div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
									<div className="h-full bg-gradient-to-r from-sky-500 to-cyan-500" style={{ width: quiz.progress + '%' }} aria-label={`Tiến độ ${quiz.progress}%`} />
								</div>
								<span className="text-xs font-medium text-gray-500 min-w-[34px] text-right">{quiz.progress}%</span>
							</div>
						</div>
						<div className="flex items-center gap-3">
							<span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">{quiz.status}</span>
							<button className="ml-auto text-sm font-semibold text-sky-600 hover:text-sky-700">Chỉnh sửa</button>
						</div>
					</div>
				))}
				{filtered.length === 0 && (
					<div className="bg-white rounded-xl p-12 text-center border border-dashed border-gray-300">
						<p className="text-gray-600 mb-4">Không tìm thấy quiz phù hợp.</p>
						<Link href="/user/create-quiz" className="inline-flex items-center gap-2 px-5 h-11 rounded-md bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold shadow-sm">
							<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
							</svg>
							Tạo Quiz Mới
						</Link>
					</div>
				)}
			</div>
			<footer className="pt-4 pb-10 text-xs text-gray-400 flex flex-wrap gap-6 justify-center">
				<span>FAQs</span>
				<span>Privacy Policy</span>
				<span>Terms & Condition</span>
			</footer>
		</div>
	);
}
