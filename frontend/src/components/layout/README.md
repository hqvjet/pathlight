# Layout Components

## NavBar Component

Component NavBar riêng dành cho user, có thể tái sử dụng ở nhiều trang khác nhau.

### Props:
- `user`: Object chứa thông tin user (name, avatar_url)
- `onLogout`: Function xử lý đăng xuất
- `showLogoutButton`: Boolean để hiển thị/ẩn nút đăng xuất (default: false)

### Usage:
```tsx
import NavBar from '@/components/layout/NavBar';

<NavBar 
  user={user} 
  onLogout={handleLogout}
  showLogoutButton={true}
/>
```

## UserLayout Component

Component layout wrapper cho các trang user, bao gồm NavBar và main content.

### Props:
- `children`: ReactNode - nội dung trang
- `user`: Object chứa thông tin user
- `onLogout`: Function xử lý đăng xuất
- `showNavLogout`: Boolean để hiển thị nút logout trên nav (default: true)

### Usage:
```tsx
import UserLayout from '@/components/layout/UserLayout';

<UserLayout user={user} onLogout={onLogout}>
  <div>Your page content here</div>
</UserLayout>
```

## Example

Xem `UserProfilePage.tsx` để biết cách sử dụng UserLayout trong thực tế.
