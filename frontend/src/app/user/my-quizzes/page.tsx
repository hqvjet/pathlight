'use client';
import Link from 'next/link';
import { useState, useMemo, useEffect } from 'react';
import { QuizCard, QuizCardData } from '@/components/user/quizzes/QuizCard';
import { quizApi } from '@/lib/api/quiz';
import { showToast } from '@/utils/toast';

type LevelFilter = 'all' | 'easy' | 'medium' | 'hard';
type StatusFilter = 'all' | 'completed' | 'draft';
type SortOption = 'latest' | 'questions_desc' | 'title_asc';

export default function MyQuizzesPage() {
	const [search, setSearch] = useState('');
	const [sort, setSort] = useState<SortOption>('latest');
	const [levelFilter, setLevelFilter] = useState<LevelFilter>('all');
	const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
	const [myQuizzes, setMyQuizzes] = useState<QuizCardData[]>([]);
	const [publicQuizzes, setPublicQuizzes] = useState<QuizCardData[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;
		const load = async () => {
			setLoading(true);
			setError(null);
			try {
				const [myResp, publicResp] = await Promise.all([
					quizApi.listMine(),
					quizApi.listPublic({}),
				]);

				if (cancelled) return;

				const myData = (myResp?.data as { quizzes?: QuizCardData[] })?.quizzes || [];
				const publicData = (publicResp?.data as { quizzes?: QuizCardData[] })?.quizzes || [];

				setMyQuizzes(myData);
				setPublicQuizzes(publicData);
			} catch (e: unknown) {
				if (!cancelled) {
					setError(e instanceof Error ? e.message : 'Không thể tải danh sách quiz');
					showToast.error('Không thể tải danh sách quiz');
				}
			} finally {
				if (!cancelled) setLoading(false);
			}
		};
		load();
		return () => { cancelled = true; };
	}, []);

	const filteredMy = useMemo(() => {
		let list = myQuizzes.filter((q) =>
			q.title.toLowerCase().includes(search.toLowerCase())
		);

		if (levelFilter !== 'all') {
			list = list.filter((q) => q.level === levelFilter);
		}

		if (statusFilter === 'completed') {
			list = list.filter((q) => q.finish);
		} else if (statusFilter === 'draft') {
			list = list.filter((q) => !q.publish);
		}

		switch (sort) {
			case 'questions_desc':
				list = [...list].sort((a, b) => b.num_questions - a.num_questions);
				break;
			case 'title_asc':
				list = [...list].sort((a, b) => a.title.localeCompare(b.title, 'vi'));
				break;
			default:
				list = [...list].sort(
					(a, b) => new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime()
				);
		}
		return list;
	}, [myQuizzes, search, sort, levelFilter, statusFilter]);

	const filteredPublic = useMemo(() => {
		let list = publicQuizzes.filter((q) =>
			q.title.toLowerCase().includes(search.toLowerCase())
		);

		if (levelFilter !== 'all') {
			list = list.filter((q) => q.level === levelFilter);
		}

		return list.sort(
			(a, b) => new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime()
		);
	}, [publicQuizzes, search, levelFilter]);

	const greeting = (() => {
		const h = new Date().getHours();
		if (h < 12) return 'Chào buổi sáng';
		if (h < 18) return 'Chào buổi chiều';
		return 'Chào buổi tối';
	})();

	if (loading) {
		return (
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
				<div className="bg-white rounded-xl p-10 text-center border border-gray-100 shadow-sm">
					<div className="animate-spin rounded-full h-10 w-10 border-b-2 border-sky-500 mx-auto" />
					<p className="mt-4 text-gray-600">Đang tải danh sách quiz...</p>
				</div>
			</div>
		);
	}

	return (
		<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-8">
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

			{error && (
				<div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">
					{error}
				</div>
			)}

			<div className="flex flex-col gap-4">
				<div className="relative">
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

				<div className="flex flex-wrap items-center gap-3">
					<div className="flex items-center gap-2">
						<label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Độ khó</label>
						<select
							value={levelFilter}
							onChange={(e) => setLevelFilter(e.target.value as LevelFilter)}
							className="h-11 pl-3 pr-8 rounded-lg bg-white border border-transparent shadow-sm text-sm focus:ring-2 focus:ring-sky-500/40"
						>
							<option value="all">Tất cả</option>
							<option value="easy">Dễ</option>
							<option value="medium">Trung bình</option>
							<option value="hard">Khó</option>
						</select>
					</div>

					<div className="flex items-center gap-2">
						<label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Trạng thái</label>
						<select
							value={statusFilter}
							onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
							className="h-11 pl-3 pr-8 rounded-lg bg-white border border-transparent shadow-sm text-sm focus:ring-2 focus:ring-sky-500/40"
						>
							<option value="all">Tất cả</option>
							<option value="completed">Hoàn thành</option>
							<option value="draft">Bản nháp</option>
						</select>
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
			</div>

			<div className="space-y-6">
				<div>
					<h2 className="text-lg font-semibold text-gray-900 mb-4">Quiz của tôi</h2>
					{filteredMy.length === 0 ? (
						<div className="bg-white rounded-xl p-12 text-center border border-dashed border-gray-300">
							<p className="text-gray-600 mb-4">
								{myQuizzes.length === 0 ? 'Bạn chưa có quiz nào.' : 'Không tìm thấy quiz phù hợp.'}
							</p>
							<Link href="/user/create-quiz" className="inline-flex items-center gap-2 px-5 h-11 rounded-md bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold shadow-sm">
								<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
								</svg>
								Tạo Quiz Mới
							</Link>
						</div>
					) : (
						<div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
							{filteredMy.map((quiz) => (
								<QuizCard key={quiz.id} quiz={quiz} />
							))}
						</div>
					)}
				</div>

				{filteredPublic.length > 0 && (
					<div className="pt-6 border-t border-gray-200">
						<h2 className="text-lg font-semibold text-gray-900 mb-4">Quiz công khai</h2>
						<div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
							{filteredPublic.map((quiz) => (
								<QuizCard key={quiz.id} quiz={quiz} />
							))}
						</div>
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
