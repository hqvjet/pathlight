import ErrorPage from '@/components/ErrorPage';

export default function NotFoundPage() {
  return (
    <ErrorPage 
      errorCode="404"
      title="Ôi không! Có vẻ bạn đang bị lạc đường"
      subtitle="Trang bạn đang tìm kiếm có thể đã bị xóa, đổi tên hoặc tạm thời không khả dụng."
      buttonText="Trở Về Trang Chính"
      buttonLink="/"
    />
  );
}
