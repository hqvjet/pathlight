'use client';
import Link from 'next/link';
import { useState, useMemo, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { QuizCard, QuizCardData } from '@/components/user/quizzes/QuizCard';
import { quizApi } from '@/lib/api/quiz';
import { userApi } from '@/lib/api/user';
import { showToast } from '@/utils/toast';

type LevelFilter = 'all' | 'easy' | 'medium' | 'hard';
type StatusFilter = 'all' | 'completed' | 'draft';
type SortOption = 'latest' | 'questions_desc' | 'title_asc';
type TabType = 'my' | 'public';
type ViewMode = 'grid' | 'list';

const ITEMS_PER_PAGE = 9;

function MyQuizzesContent() {
	const searchParams = useSearchParams();
	const [activeTab, setActiveTab] = useState<TabType>('my');
	const [currentPage, setCurrentPage] = useState(1);
	const [search, setSearch] = useState('');
	const [sort, setSort] = useState<SortOption>('latest');
	const [levelFilter, setLevelFilter] = useState<LevelFilter>('all');
	const [statusFilter] = useState<StatusFilter>('all');
	const [viewMode, setViewMode] = useState<ViewMode>('grid');
	const [myQuizzes, setMyQuizzes] = useState<QuizCardData[]>([]);
	const [publicQuizzes, setPublicQuizzes] = useState<QuizCardData[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	// Set initial tab from URL parameter
	useEffect(() => {
		const tabParam = searchParams.get('tab');
		if (tabParam === 'public') {
			setActiveTab('public');
		}
	}, [searchParams]);

	// Reset to page 1 when switching tabs or filters
	useEffect(() => {
		setCurrentPage(1);
	}, [activeTab, search, sort, levelFilter, statusFilter]);

	useEffect(() => {
		let cancelled = false;
		const load = async () => {
			setLoading(true);
			setError(null);
			try {
				// Use recommendation API instead of listPublic
				const [myResp, publicResp] = await Promise.all([
					quizApi.listMine(),
					quizApi.getRecommended(20),
				]);
				const myData = (myResp?.data as { quizzes?: QuizCardData[] })?.quizzes || [];
				// Map recommended quiz items to QuizCardData format
				const publicItems = (publicResp?.data as { status: number; items?: unknown[] })?.items || [];
				const publicData: QuizCardData[] = publicItems.map((item: unknown) => {
				const quizItem = item as Record<string, unknown>;
				return {
					id: (quizItem.id || quizItem.quiz_id) as string | undefined,
					quiz_id: quizItem.quiz_id as string | undefined,
					title: (quizItem.title || 'Untitled Quiz') as string,
					description: (quizItem.description || quizItem.overview || '') as string | undefined,
					overview: (quizItem.overview || quizItem.description || '') as string | undefined,
					level: (quizItem.difficulty || 'medium') as 'easy' | 'medium' | 'hard',
					num_questions: (quizItem.num_questions as number) || 0,
					duration: (quizItem.duration as number) || 30,
					finish: false,
					publish: true,
					owner_id: quizItem.user_id as string | undefined,
					created_at: (quizItem.created_at as string) || new Date().toISOString(),
					updated_at: (quizItem.updated_at as string) || new Date().toISOString(),
					previous_score: quizItem.previous_score as number | null | undefined,
					recommendation_score: quizItem.recommendation_score as number | undefined,
				};
			});

			// Fetch owner names for all quizzes
			const allOwnerIds = [...new Set([...myData, ...publicData].map(q => q.owner_id).filter(Boolean))];
			
			if (allOwnerIds.length > 0) {
					try {
						const usersResp = await userApi.batchUsers(allOwnerIds as string[]);
						const usersData = usersResp?.data as Record<string, { name: string }>;
						
						// Map owner names to quizzes
						const addOwnerNames = (quizzes: QuizCardData[]) =>
							quizzes.map(q => ({
								...q,
								owner_name: q.owner_id && usersData?.[q.owner_id]?.name || undefined
							}));
						
						setMyQuizzes(addOwnerNames(myData));
						setPublicQuizzes(addOwnerNames(publicData));
					} catch (userError) {
						console.error('Failed to fetch owner names:', userError);
						// Continue without owner names
						setMyQuizzes(myData);
						setPublicQuizzes(publicData);
					}
				} else {
					setMyQuizzes(myData);
					setPublicQuizzes(publicData);
				}
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
		const source = activeTab === 'my' ? myQuizzes : publicQuizzes;
		let list = source.filter((q) =>
			q.title.toLowerCase().includes(search.toLowerCase())
		);

		if (levelFilter !== 'all') {
			list = list.filter((q) => q.level === levelFilter);
		}

		if (activeTab === 'my' && statusFilter === 'completed') {
			list = list.filter((q) => q.finish);
		} else if (activeTab === 'my' && statusFilter === 'draft') {
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
					(a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
				);
		}
		return list;
	}, [myQuizzes, publicQuizzes, activeTab, search, sort, levelFilter, statusFilter]);

	const totalPages = Math.ceil(filteredMy.length / ITEMS_PER_PAGE);
	const paginatedQuizzes = filteredMy.slice(
		(currentPage - 1) * ITEMS_PER_PAGE,
		currentPage * ITEMS_PER_PAGE
	);

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
		<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
			<div className="space-y-2">
				<p className="text-sm text-gray-500 font-medium tracking-wide">{greeting}</p>
				<div className="flex flex-wrap items-center justify-between gap-4">
					<h1 className="text-2xl font-bold text-gray-900">Bộ Câu Hỏi Của Tôi</h1>
					<div className="flex items-center gap-3">
						<Link
							href="/user/quiz-tracking"
							className="inline-flex items-center gap-2 px-4 h-10 rounded-lg border-2 border-sky-200 bg-sky-50 hover:bg-sky-100 text-sky-700 text-sm font-semibold transition-colors"
						>
							<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
							</svg>
							Tiến trình tạo
						</Link>
						<Link
							href="/user/create-quiz"
							className="inline-flex items-center gap-2 px-5 h-10 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 text-white text-sm font-semibold shadow-lg shadow-sky-500/30 transition-all"
						>
							<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
							</svg>
							Tạo Quiz
						</Link>
					</div>
				</div>
			</div>

			{error && (
				<div className="bg-red-50 text-red-700 rounded-xl p-4 border border-red-200 text-sm">
					{error}
				</div>
			)}

			{/* Tabs */}
			<div className="border-b">
				<div className="flex gap-6">
					<button
						onClick={() => setActiveTab('my')}
						className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
							activeTab === 'my'
								? 'border-sky-600 text-sky-600'
								: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
						}`}
					>
						Quiz Của Tôi
						<span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
							{myQuizzes.length}
						</span>
					</button>
					<button
						onClick={() => setActiveTab('public')}
						className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
							activeTab === 'public'
								? 'border-sky-600 text-sky-600'
								: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
						}`}
					>
						Quiz Công Khai
						<span className="ml-2 px-2 py-0.5 rounded-full bg-gray-100 text-xs">
							{publicQuizzes.length}
						</span>
					</button>
				</div>
			</div>

			<div className="space-y-6">
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

					<div className="flex flex-wrap items-center justify-between gap-3">
						<div className="flex flex-wrap items-center gap-3">
							<div className="flex items-center gap-2">
								<label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Độ khó</label>
								<select
									value={levelFilter}
									onChange={(e) => setLevelFilter(e.target.value as LevelFilter)}
									className="h-10 pl-3 pr-8 rounded-lg bg-white border border-gray-200 shadow-sm text-sm focus:ring-2 focus:ring-sky-500/40 focus:border-sky-400"
								>
									<option value="all">Tất cả</option>
									<option value="easy">Dễ</option>
									<option value="medium">Trung bình</option>
									<option value="hard">Khó</option>
								</select>
							</div>

							<div className="flex items-center gap-2">
								<label className="text-xs font-medium text-gray-500 uppercase tracking-wide hidden sm:block">Sắp xếp</label>
								<div className="relative">
									<select
										value={sort}
										onChange={(e) => setSort(e.target.value as SortOption)}
										className="appearance-none h-10 pl-4 pr-10 rounded-lg bg-white border border-gray-200 shadow-sm text-sm focus:ring-2 focus:ring-sky-500/40 focus:border-sky-400 cursor-pointer"
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
						
						{/* View mode toggle */}
						<div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
							<button
								onClick={() => setViewMode('grid')}
								className={`p-2 rounded-md transition-colors ${
									viewMode === 'grid' ? 'bg-white text-sky-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
								}`}
								title="Dạng lưới"
							>
								<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
								</svg>
							</button>
							<button
								onClick={() => setViewMode('list')}
								className={`p-2 rounded-md transition-colors ${
									viewMode === 'list' ? 'bg-white text-sky-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
								}`}
								title="Dạng danh sách"
							>
								<svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
								</svg>
							</button>
						</div>
					</div>
				</div>

				<div>
					{paginatedQuizzes.length === 0 ? (
						<div className="bg-white rounded-xl p-12 text-center border border-dashed border-gray-300">
							<p className="text-gray-600 mb-4">
								{filteredMy.length === 0 && (activeTab === 'my' ? myQuizzes : publicQuizzes).length === 0
									? (activeTab === 'my' ? 'Bạn chưa có quiz nào.' : 'Chưa có quiz công khai nào.')
									: 'Không tìm thấy quiz phù hợp.'}
							</p>
							{activeTab === 'my' && myQuizzes.length === 0 && (
								<Link href="/user/create-quiz" className="inline-flex items-center gap-2 px-5 h-11 rounded-md bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold shadow-sm">
									<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
									</svg>
									Tạo Quiz Mới
								</Link>
							)}
						</div>
					) : (
						<>
							<div className={viewMode === 'grid' ? 'grid gap-5 sm:grid-cols-2 lg:grid-cols-3' : 'space-y-4'}>
								{paginatedQuizzes.map((quiz) => (
									<QuizCard key={quiz.id || quiz.quiz_id} quiz={quiz} viewMode={viewMode} />
								))}
							</div>

							{/* Pagination */}
							{totalPages > 1 && (
								<div className="flex items-center justify-center gap-2 mt-6 pt-6 border-t">
									<button
										onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
										disabled={currentPage === 1}
										className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
									>
										<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
										</svg>
									</button>

									<div className="flex items-center gap-1">
										{[...Array(totalPages)].map((_, i) => {
											const pageNum = i + 1;
											if (
												pageNum === 1 ||
												pageNum === totalPages ||
												Math.abs(pageNum - currentPage) <= 1
											) {
												return (
													<button
														key={pageNum}
														onClick={() => setCurrentPage(pageNum)}
														className={`min-w-[32px] h-8 px-2 rounded-lg text-sm font-medium transition-colors ${
															currentPage === pageNum
																? 'bg-sky-600 text-white'
																: 'hover:bg-gray-100 text-gray-700'
														}`}
													>
														{pageNum}
													</button>
												);
											}

											if (pageNum === currentPage - 2 || pageNum === currentPage + 2) {
												return (
													<span key={pageNum} className="px-2 text-gray-400">
														...
													</span>
												);
											}

											return null;
										})}
									</div>

									<button
										onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
										disabled={currentPage === totalPages}
										className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
									>
										<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
										</svg>
									</button>
								</div>
							)}
						</>
					)}
				</div>
			</div>

			<footer className="pt-4 pb-10 text-xs text-gray-400 flex flex-wrap gap-6 justify-center">
				<span>FAQs</span>
				<span>Privacy Policy</span>
				<span>Terms & Condition</span>
			</footer>
		</div>
	);
}
export default function MyQuizzesPage() {
	return (
		<Suspense fallback={
			<div className="flex items-center justify-center min-h-screen">
				<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500" />
			</div>
		}>
			<MyQuizzesContent />
		</Suspense>
	);
}