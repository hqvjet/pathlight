# 🤖 PathLight Frontend - Agent Documentation

**Last Updated:** October 23, 2025  
**Version:** 1.0.0  
**Framework:** Next.js 15.3.3 (App Router)  
**Repository:** pathlight  
**Branch:** scrum-60

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Core Modules](#core-modules)
5. [Components](#components)
6. [Pages & Routes](#pages--routes)
7. [State Management](#state-management)
8. [API Integration](#api-integration)
9. [Utilities](#utilities)
10. [Configuration](#configuration)
11. [Styling](#styling)
12. [Authentication Flow](#authentication-flow)
13. [Development Guidelines](#development-guidelines)
14. [Future Work Considerations](#future-work-considerations)

---

## 🎯 Overview

PathLight is an AI-powered personalized learning platform that transforms documents (PDF, videos, Word files) into automated learning systems with roadmaps, assignments, assessments, and 24/7 mentoring.

### Key Features
- 🔐 **Authentication**: Email/password + Google OAuth
- 📚 **Course Management**: Create and manage courses with AI assistance
- 📝 **Quiz System**: Automated quiz generation and tracking
- 👤 **User Dashboard**: Personal learning dashboard with progress tracking
- 🎮 **Gamification**: XP, badges, quests, and mini-games
- 🤖 **AI Integration**: RAG-based document ingestion and adaptive learning paths

---

## 🛠 Technology Stack

### Core Framework
- **Next.js 15.3.3** - React framework with App Router
- **React 19.0.0** - UI library
- **TypeScript 5** - Type safety

### UI & Styling
- **Tailwind CSS 3.4.17** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives
  - `@radix-ui/react-dialog`
  - `@radix-ui/react-checkbox`
  - `@radix-ui/react-avatar`
  - `@radix-ui/react-label`
  - `@radix-ui/react-slot`
- **Lucide React** - Icon library
- **React Icons** - Additional icons
- **Tailwind Plugins**:
  - `@tailwindcss/forms`
  - `@tailwindcss/typography`
  - `tailwindcss-animate`

### State & Data
- **React Context API** - Global state (AuthContext)
- **Custom Hooks** - Business logic encapsulation
- **js-cookie** - Cookie management

### Authentication
- **Google Auth Library** - OAuth integration
- **JWT** - Token-based authentication

### Utilities
- **clsx** - Conditional class names
- **tailwind-merge** - Merge Tailwind classes
- **class-variance-authority** - Component variants
- **react-toastify** - Notifications

### Development
- **ESLint** - Code linting
- **TypeScript Config** - Type checking
- **Next.js Dev Server** - Hot reload

---

## 📁 Project Structure

```
frontend/
├── public/                     # Static assets
│   ├── assets/
│   │   ├── icons/             # App icons
│   │   └── images/            # Images
│   └── *.svg                  # Next.js default icons
│
├── src/
│   ├── app/                   # Next.js App Router (Pages)
│   │   ├── api/               # API route handlers
│   │   │   ├── image-loader/  # Image optimization
│   │   │   ├── users/         # User API routes
│   │   │   └── v1/            # Versioned API
│   │   ├── auth/              # Authentication pages
│   │   │   ├── signin/
│   │   │   ├── signup/
│   │   │   ├── forgot-password/
│   │   │   ├── reset-password/
│   │   │   ├── verify-email/
│   │   │   └── email-sent/
│   │   ├── user/              # Protected user pages
│   │   │   ├── dashboard/
│   │   │   ├── profile/
│   │   │   ├── my-courses/
│   │   │   ├── my-quizzes/
│   │   │   ├── create-course/
│   │   │   ├── create-quiz/
│   │   │   ├── generation-tracking/
│   │   │   └── study-time-setup/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Landing page
│   │   ├── not-found.tsx      # 404 page
│   │   ├── globals.css        # Global styles
│   │   ├── global-nav.css     # Navigation styles
│   │   └── fonts.css          # Font declarations
│   │
│   ├── components/            # React components
│   │   ├── auth/              # Auth-specific components
│   │   ├── common/            # Shared components
│   │   ├── icons/             # Icon components
│   │   ├── layout/            # Layout components
│   │   ├── ui/                # UI primitives (shadcn-style)
│   │   └── user/              # User-specific components
│   │
│   ├── config/                # Configuration
│   │   ├── env.ts             # Environment config
│   │   └── index.ts           # Config barrel exports
│   │
│   ├── constants/             # App constants
│   │   └── index.ts
│   │
│   ├── context/               # React Context
│   │   └── AuthContext.tsx    # Authentication context
│   │
│   ├── fake/                  # Mock data
│   │   └── courses.ts         # Fake course data
│   │
│   ├── hooks/                 # Custom React hooks
│   │   ├── useAuth.ts         # Auth hook
│   │   ├── useGoogleOAuth.ts  # Google OAuth hook
│   │   └── middleware.ts      # Hook middleware
│   │
│   ├── lib/                   # Core libraries
│   │   ├── api/               # API client (modular)
│   │   │   ├── http.ts        # HTTP client
│   │   │   ├── auth.ts        # Auth API
│   │   │   ├── user.ts        # User API
│   │   │   ├── course.ts      # Course API
│   │   │   ├── quiz.ts        # Quiz API
│   │   │   ├── pool.ts        # Pool API
│   │   │   └── index.ts       # Barrel exports
│   │   ├── api-client.ts      # Legacy API client (deprecated)
│   │   └── utils.ts           # Lib utilities
│   │
│   ├── services/              # Business logic services
│   │   ├── auth.service.ts    # Auth service
│   │   ├── user.service.ts    # User service
│   │   └── index.ts           # Service exports
│   │
│   └── utils/                 # Utility functions
│       ├── api.ts             # API utilities
│       ├── auth.ts            # Auth utilities
│       ├── avatar.ts          # Avatar utilities
│       ├── cookies.ts         # Cookie utilities
│       ├── tailwind.ts        # Tailwind utilities
│       ├── toast.ts           # Toast notifications
│       └── types.ts           # Type utilities
│
├── middleware.ts              # Next.js middleware
├── next.config.ts             # Next.js configuration
├── tailwind.config.ts         # Tailwind configuration
├── tsconfig.json              # TypeScript configuration
├── eslint.config.mjs          # ESLint configuration
├── postcss.config.mjs         # PostCSS configuration
├── package.json               # Dependencies
├── Dockerfile                 # Docker config
└── README.md                  # Project documentation
```

---

## 🧩 Core Modules

### 1. Authentication (`src/lib/api/auth.ts`)
Handles all authentication-related API calls:
- `signup()` - User registration
- `signin()` - User login
- `signout()` - User logout
- `googleAuth()` - Google OAuth
- `verifyEmail()` - Email verification
- `forgotPassword()` - Password reset request
- `resetPassword()` - Password reset
- `refreshToken()` - Token refresh

### 2. User Management (`src/lib/api/user.ts`)
User profile and data management:
- `getInfo()` - Get user info
- `updateProfile()` - Update user profile
- `uploadAvatar()` - Upload profile picture
- `getStudyTime()` - Get study time settings
- `updateStudyTime()` - Update study time

### 3. Course Management (`src/lib/api/course.ts`)
Course-related operations:
- `list()` - List all courses
- `get()` - Get course details
- `create()` - Create new course
- `update()` - Update course
- `delete()` - Delete course
- `enroll()` - Enroll in course
- `upload()` - Upload course materials

### 4. Quiz Management (`src/lib/api/quiz.ts`)
Quiz and assessment features:
- `list()` - List all quizzes
- `get()` - Get quiz details
- `create()` - Create new quiz
- `submit()` - Submit quiz answers
- `getResults()` - Get quiz results
- `generate()` - AI-generate quiz

### 5. HTTP Client (`src/lib/api/http.ts`)
Core HTTP client with:
- Request/response interceptors
- Error handling
- Token management
- File upload support
- Retry logic

---

## 🎨 Components

### UI Components (`src/components/ui/`)
Reusable UI primitives based on Radix UI and shadcn patterns:

| Component | Description | Props |
|-----------|-------------|-------|
| `badge.tsx` | Label/tag component | `variant`, `size` |
| `button.tsx` | Button with variants | `variant`, `size`, `asChild` |
| `card.tsx` | Card container | `CardHeader`, `CardContent`, `CardTitle`, `CardDescription` |
| `checkbox.tsx` | Checkbox input | `checked`, `onCheckedChange` |
| `dialog.tsx` | Modal dialog | `open`, `onOpenChange` |
| `input.tsx` | Text input | `type`, `placeholder`, `error` |
| `label.tsx` | Form label | `htmlFor` |
| `progress.tsx` | Progress bar | `value`, `max` |

### Layout Components (`src/components/layout/`)

| Component | Purpose | Features |
|-----------|---------|----------|
| `GlobalNavWrapper.tsx` | Navigation wrapper | Route-aware navigation |
| `Header.tsx` | Site header | Logo, navigation links |
| `NavBar.tsx` | Main navigation | Dynamic based on auth |
| `NavBarAuth.tsx` | Authenticated navbar | User menu, logout |
| `NavBarPublic.tsx` | Public navbar | Login, signup links |
| `AuthLayout.tsx` | Auth page layout | Centered form layout |
| `UserLayout.tsx` | User page layout | Sidebar + content |
| `ResetPasswordLayout.tsx` | Password reset layout | Specialized form layout |

### Authentication Components (`src/components/auth/`)

| Component | Purpose |
|-----------|---------|
| `SignInForm.tsx` | Login form with email/password + Google |
| `SignUpForm.tsx` | Registration form |
| `ForgotPasswordPage.tsx` | Forgot password flow |
| `ResetPasswordContent.tsx` | Password reset form |
| `EmailVerificationResult.tsx` | Email verification status |
| `EmailSentPage.tsx` | Email sent confirmation |
| `EmailNotFoundContent.tsx` | Email not found error |

### Common Components (`src/components/common/`)

| Component | Purpose | Usage |
|-----------|---------|-------|
| `Avatar.tsx` | User avatar | Display user profile picture |
| `BrandLogo.tsx` | App logo | Branding consistency |
| `Button.tsx` | Legacy button | Use `ui/button.tsx` instead |
| `CookieWarning.tsx` | Cookie consent | GDPR compliance |
| `ErrorPage.tsx` | Error display | Error boundary fallback |
| `Layout.tsx` | Legacy layout | Deprecated |
| `LoadingSpinner.tsx` | Loading indicator | Async operations |
| `Notification.tsx` | Toast notifications | Success/error messages |

### User Components (`src/components/user/`)

| Component | Purpose |
|-----------|---------|
| `Dashboard.tsx` | User dashboard overview |
| `ProfilePage.tsx` | User profile view/edit |
| `StudyTimeSetup.tsx` | Study time configuration |
| `create-course/` | Course creation wizard |
| `dashboard/` | Dashboard widgets |
| `generation/` | AI generation tracking |
| `profile/` | Profile management |

---

## 🗺 Pages & Routes

### Public Routes

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Landing page with features, testimonials |
| `/auth/signin` | `app/auth/signin/page.tsx` | Login page |
| `/auth/signup` | `app/auth/signup/page.tsx` | Registration page |
| `/auth/forgot-password` | `app/auth/forgot-password/page.tsx` | Password reset request |
| `/auth/reset-password/:token` | `app/auth/reset-password/page.tsx` | Password reset with token |
| `/auth/verify-email/:token` | `app/auth/verify-email/page.tsx` | Email verification |
| `/auth/email-sent` | `app/auth/email-sent/page.tsx` | Email sent confirmation |

### Protected Routes (requires authentication)

| Route | File | Purpose |
|-------|------|---------|
| `/user/dashboard` | `app/user/dashboard/page.tsx` | User dashboard |
| `/user/profile` | `app/user/profile/page.tsx` | User profile management |
| `/user/my-courses` | `app/user/my-courses/page.tsx` | User's enrolled courses |
| `/user/my-quizzes` | `app/user/my-quizzes/page.tsx` | User's quizzes |
| `/user/create-course` | `app/user/create-course/page.tsx` | Create new course |
| `/user/create-quiz` | `app/user/create-quiz/page.tsx` | Create new quiz |
| `/user/generation-tracking` | `app/user/generation-tracking/page.tsx` | Track AI generation jobs |
| `/user/study-time-setup` | `app/user/study-time-setup/page.tsx` | Configure study schedule |

### API Routes (Next.js Route Handlers)

| Route | Purpose |
|-------|---------|
| `/api/image-loader/*` | Image optimization proxy |
| `/api/users/*` | User data proxy (optional) |
| `/api/v1/*` | Versioned API endpoints |

---

## 🔄 State Management

### Context API

#### AuthContext (`src/context/AuthContext.tsx`)
Manages global authentication state.

**State:**
- `token: string | null` - JWT auth token
- `user: AuthUser | null` - Current user info
- `loading: boolean` - Loading state
- `isAuthenticated: boolean` - Auth status
- `isRemembered: boolean` - "Remember me" flag

**Methods:**
- `login(token, remember)` - Authenticate user
- `logout()` - Clear auth state
- `refreshUser()` - Reload user data

**User Object:**
```typescript
interface AuthUser {
  id?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  name?: string;
}
```

### Custom Hooks

#### `useAuth` (`src/hooks/useAuth.ts`)
Provides auth state and methods. Wrapper around `useAuthContext`.

#### `useGoogleOAuth` (`src/hooks/useGoogleOAuth.ts`)
Handles Google OAuth flow.

**Returns:**
- `signInWithGoogle()` - Initiate Google sign-in
- `loading: boolean` - OAuth loading state
- `error: string | null` - OAuth error

---

## 🌐 API Integration

### API Client Architecture

The application uses a **modular API client** structure:

```
lib/api/
├── http.ts       # Core HTTP client
├── auth.ts       # Auth endpoints
├── user.ts       # User endpoints
├── course.ts     # Course endpoints
├── quiz.ts       # Quiz endpoints
├── pool.ts       # Pool endpoints
└── index.ts      # Unified exports
```

### HTTP Client (`src/lib/api/http.ts`)

**Features:**
- Automatic token injection
- Request/response interceptors
- Error handling with retry
- File upload support
- Type-safe responses

**Usage:**
```typescript
import { apiClient } from '@/lib/api/http';

// GET request
const response = await apiClient.get<DataType>('/endpoint');

// POST request
const response = await apiClient.post<ResponseType>('/endpoint', data);

// File upload
const response = await apiClient.uploadFile('/upload', file);
```

### API Modules

#### Auth API (`src/lib/api/auth.ts`)
```typescript
import { authApi } from '@/lib/api';

await authApi.signup({ email, password, first_name, last_name });
await authApi.signin({ email, password, remember });
await authApi.googleAuth({ credential });
await authApi.verifyEmail({ token });
await authApi.forgotPassword({ email });
await authApi.resetPassword({ token, new_password });
```

#### User API (`src/lib/api/user.ts`)
```typescript
import { userApi } from '@/lib/api';

const user = await userApi.getInfo();
await userApi.updateProfile({ first_name, last_name });
await userApi.uploadAvatar(file);
const studyTime = await userApi.getStudyTime();
await userApi.updateStudyTime({ daily_goal: 60 });
```

#### Course API (`src/lib/api/course.ts`)
```typescript
import { courseApi } from '@/lib/api';

const courses = await courseApi.list();
const course = await courseApi.get(courseId);
await courseApi.create({ title, description });
await courseApi.update(courseId, data);
await courseApi.delete(courseId);
await courseApi.enroll(courseId);
await courseApi.upload(courseId, files);
```

#### Quiz API (`src/lib/api/quiz.ts`)
```typescript
import { quizApi } from '@/lib/api';

const quizzes = await quizApi.list();
const quiz = await quizApi.get(quizId);
await quizApi.create({ title, questions });
await quizApi.submit(quizId, answers);
const results = await quizApi.getResults(quizId);
await quizApi.generate({ courseId, topic });
```

### Unified API Object
```typescript
import { api } from '@/lib/api';

// Use domain-specific APIs
await api.auth.signin({ email, password });
await api.user.getInfo();
await api.course.list();
await api.quiz.create(data);

// Direct HTTP client access
await api.client.get('/custom-endpoint');
```

---

## 🔧 Utilities

### API Utilities (`src/utils/api.ts`)

**Storage:**
```typescript
import { storage } from '@/utils/api';

storage.setToken(token, remember);
const token = storage.getToken();
storage.removeToken();
const isRemembered = storage.isRemembered();
```

**Auth Headers:**
```typescript
import { getAuthHeaders } from '@/utils/api';

const headers = getAuthHeaders();
// Returns: { Authorization: 'Bearer <token>' }
```

### Auth Utilities (`src/utils/auth.ts`)

```typescript
import { authUtils } from '@/utils/auth';

authUtils.logout(); // Clear all auth data
authUtils.isTokenExpired(token); // Check token validity
```

### Avatar Utilities (`src/utils/avatar.ts`)

```typescript
import { getAvatarUrl, getUserInitials } from '@/utils/avatar';

const avatarUrl = getAvatarUrl(user);
const initials = getUserInitials(user.name); // "JD" from "John Doe"
```

### Cookie Utilities (`src/utils/cookies.ts`)

```typescript
import { cookieStorage } from '@/utils/cookies';

cookieStorage.set('key', 'value', { expires: 7 });
const value = cookieStorage.get('key');
cookieStorage.remove('key');
```

### Toast Notifications (`src/utils/toast.ts`)

```typescript
import { showToast } from '@/utils/toast';

showToast.success('Operation successful!');
showToast.error('Something went wrong');
showToast.info('FYI: Important information');
showToast.warning('Warning: Check this out');
```

### Tailwind Utilities (`src/utils/tailwind.ts`)

**Class Merging:**
```typescript
import { cn } from '@/utils/tailwind';

const className = cn(
  'base-class',
  condition && 'conditional-class',
  'override-class'
);
```

**Predefined Classes:**
```typescript
import { 
  buttonClasses, 
  inputClasses, 
  cardClasses 
} from '@/utils/tailwind';

<button className={buttonClasses.primary}>Click me</button>
```

**Color Palette:**
```typescript
import { colors } from '@/utils/tailwind';

const primaryColor = colors.primary; // orange-600
const secondaryColor = colors.secondary; // emerald-600
```

---

## ⚙️ Configuration

### Environment Configuration (`src/config/env.ts`)

**API Configuration:**
```typescript
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  DIRECT_BACKEND: boolean,
  AUTH_SERVICE_URL: string,
  USER_SERVICE_URL: string,
  COURSE_SERVICE_URL: string,
  QUIZ_SERVICE_URL: string,
}
```

**Auth Configuration:**
```typescript
export const AUTH_CONFIG = {
  GOOGLE_CLIENT_ID: string,
  ENABLE_GOOGLE_AUTH: boolean,
  ENABLE_EMAIL_VERIFICATION: boolean,
  ENABLE_FORGOT_PASSWORD: boolean,
}
```

**App Configuration:**
```typescript
export const APP_CONFIG = {
  NAME: 'PathLight',
  VERSION: '1.0.0',
  ENVIRONMENT: 'production' | 'development',
  IS_DEVELOPMENT: boolean,
  IS_PRODUCTION: boolean,
}
```

**Feature Flags:**
```typescript
export const FEATURE_FLAGS = {
  ENABLE_GOOGLE_AUTH: boolean,
  ENABLE_EMAIL_VERIFICATION: boolean,
  ENABLE_FORGOT_PASSWORD: boolean,
}
```

### Environment Variables

Create `.env.local` with:
```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://api.pathlight.com/api
NEXT_PUBLIC_DIRECT_BACKEND=false

# Authentication
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id

# Application
NEXT_PUBLIC_APP_NAME=PathLight
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_ENVIRONMENT=development

# Site
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

---

## 🎨 Styling

### Tailwind Configuration (`tailwind.config.ts`)

**Theme Extensions:**
- Custom colors (orange, emerald)
- Font family (Montserrat)
- Animations
- Border radius
- Spacing

**Plugins:**
- `@tailwindcss/forms` - Form styles
- `@tailwindcss/typography` - Typography
- `tailwindcss-animate` - Animations

### Global Styles

**`globals.css`:**
- CSS custom properties
- Base styles
- Utility classes
- Dark mode support

**`global-nav.css`:**
- Navigation-specific styles
- Sticky header
- Mobile menu

**`fonts.css`:**
- Font-face declarations
- Font loading optimization

### Component Styling Patterns

**Using `cn()` utility:**
```typescript
import { cn } from '@/utils/tailwind';

<div className={cn(
  'base-styles',
  variant === 'primary' && 'primary-styles',
  size === 'lg' && 'large-styles',
  className // Allow external overrides
)} />
```

**Using Class Variance Authority (CVA):**
```typescript
import { cva } from 'class-variance-authority';

const buttonVariants = cva(
  'base-button-styles',
  {
    variants: {
      variant: {
        primary: 'bg-orange-600 text-white',
        secondary: 'bg-emerald-600 text-white',
      },
      size: {
        sm: 'px-3 py-1 text-sm',
        lg: 'px-6 py-3 text-lg',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'sm',
    },
  }
);
```

---

## 🔐 Authentication Flow

### Sign Up Flow
1. User fills registration form (`SignUpForm.tsx`)
2. Frontend validates input
3. `authApi.signup()` sends request
4. Backend creates user, sends verification email
5. Redirect to email sent page
6. User clicks verification link
7. `EmailVerificationResult.tsx` verifies token
8. User can now sign in

### Sign In Flow
1. User enters credentials (`SignInForm.tsx`)
2. `authApi.signin()` authenticates
3. Backend returns JWT token
4. Frontend stores token in cookies
5. `AuthContext` updates state
6. User redirected to dashboard
7. `middleware.ts` protects routes

### Google OAuth Flow
1. User clicks "Sign in with Google"
2. `useGoogleOAuth` hook initiates OAuth
3. Google popup for consent
4. Google returns credential
5. `authApi.googleAuth()` validates with backend
6. Backend returns JWT token
7. Frontend stores token
8. User redirected to dashboard

### Password Reset Flow
1. User enters email (`ForgotPasswordPage.tsx`)
2. `authApi.forgotPassword()` sends request
3. Backend sends reset email
4. User clicks reset link
5. `ResetPasswordContent.tsx` shows form
6. User enters new password
7. `authApi.resetPassword()` updates password
8. User can sign in with new password

### Middleware Protection (`middleware.ts`)

**Protected Routes:**
- `/user/dashboard`
- `/user/profile`
- `/user/my-courses`
- `/user/my-quizzes`
- `/admin`

**Public Routes:**
- `/auth/signin`
- `/auth/signup`
- `/auth/forgot-password`

**Logic:**
1. Check for auth token in cookies
2. Validate token expiry
3. Redirect unauthenticated users to `/auth/signin`
4. Redirect authenticated users away from auth pages
5. Clear expired tokens

---

## 📚 Development Guidelines

### Code Organization

**File Naming:**
- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Types: `types.ts` or inline
- Styles: `kebab-case.css`

**Import Order:**
1. External packages
2. Absolute imports (`@/...`)
3. Relative imports
4. Styles

**Example:**
```typescript
import React from 'react';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { cn } from '@/utils/tailwind';
import './styles.css';
```

### Component Patterns

**Functional Components:**
```typescript
interface Props {
  title: string;
  onAction: () => void;
}

export default function MyComponent({ title, onAction }: Props) {
  return <div>{title}</div>;
}
```

**Client Components:**
```typescript
'use client';

import { useState } from 'react';

export default function InteractiveComponent() {
  const [state, setState] = useState(false);
  return <button onClick={() => setState(!state)}>Toggle</button>;
}
```

**Server Components (default):**
```typescript
// No 'use client' directive
export default function ServerComponent() {
  // Can use async/await
  return <div>Server rendered</div>;
}
```

### Error Handling

**API Calls:**
```typescript
try {
  const response = await api.user.getInfo();
  if (response.status === 200) {
    // Success
  } else {
    showToast.error(response.error || 'Failed');
  }
} catch (error) {
  showToast.error('Network error');
  console.error(error);
}
```

**Form Validation:**
```typescript
const [errors, setErrors] = useState<Record<string, string>>({});

const validate = () => {
  const newErrors: Record<string, string> = {};
  if (!email) newErrors.email = 'Email required';
  if (!password) newErrors.password = 'Password required';
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

const handleSubmit = async (e: FormEvent) => {
  e.preventDefault();
  if (!validate()) return;
  // Submit
};
```

### Type Safety

**API Response Types:**
```typescript
interface ApiResponse<T> {
  status: number;
  data?: T;
  error?: string;
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

const response: ApiResponse<User> = await api.user.getInfo();
```

**Component Props:**
```typescript
interface ButtonProps 
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'lg';
}

export function Button({ 
  variant = 'primary', 
  size = 'sm',
  className,
  ...props 
}: ButtonProps) {
  return <button className={cn(/* ... */)} {...props} />;
}
```

### Performance Optimization

**Lazy Loading:**
```typescript
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <LoadingSpinner />,
});
```

**Memoization:**
```typescript
import { useMemo, useCallback } from 'react';

const memoizedValue = useMemo(() => computeExpensive(a, b), [a, b]);
const memoizedCallback = useCallback(() => doSomething(a), [a]);
```

**Image Optimization:**
```typescript
import Image from 'next/image';

<Image 
  src="/path/to/image.jpg"
  alt="Description"
  width={800}
  height={600}
  priority={false}
/>
```

---

## 🚀 Future Work Considerations

### Planned Features

#### 1. **Course Content Management**
- [ ] Rich text editor for lessons
- [ ] Video upload and streaming
- [ ] PDF viewer integration
- [ ] Progress tracking per lesson
- [ ] Bookmarking and notes

#### 2. **Quiz Enhancements**
- [ ] Multiple question types (multiple choice, true/false, essay)
- [ ] Timed quizzes
- [ ] Quiz analytics dashboard
- [ ] Peer review system
- [ ] Adaptive difficulty

#### 3. **Gamification Expansion**
- [ ] XP system with levels
- [ ] Achievement badges
- [ ] Leaderboards
- [ ] Daily quests
- [ ] Streak tracking
- [ ] Mini-games integration

#### 4. **AI Features**
- [ ] AI tutor chatbot
- [ ] Personalized study recommendations
- [ ] Automated content summarization
- [ ] Smart scheduling
- [ ] Learning style detection

#### 5. **Social Features**
- [ ] Study groups
- [ ] Discussion forums
- [ ] Peer mentoring
- [ ] Content sharing
- [ ] Collaborative learning

#### 6. **Analytics & Insights**
- [ ] Learning analytics dashboard
- [ ] Progress reports
- [ ] Time tracking
- [ ] Performance predictions
- [ ] Recommendations engine

### Technical Improvements

#### 1. **State Management**
- [ ] Consider Zustand or Redux for complex state
- [ ] Implement optimistic UI updates
- [ ] Add offline support with service workers
- [ ] Improve cache strategy

#### 2. **Testing**
- [ ] Add unit tests (Jest + React Testing Library)
- [ ] Add integration tests
- [ ] Add E2E tests (Playwright/Cypress)
- [ ] Set up CI/CD with test automation

#### 3. **Performance**
- [ ] Implement virtual scrolling for large lists
- [ ] Add skeleton loaders
- [ ] Optimize bundle size
- [ ] Implement code splitting strategies
- [ ] Add performance monitoring (Web Vitals)

#### 4. **Accessibility**
- [ ] Full WCAG 2.1 AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader optimization
- [ ] High contrast mode
- [ ] Focus management

#### 5. **Internationalization**
- [ ] i18n setup (next-intl)
- [ ] Multi-language support
- [ ] RTL language support
- [ ] Localized content

#### 6. **Security**
- [ ] Implement CSP headers
- [ ] Add rate limiting
- [ ] Enhance XSS protection
- [ ] Add CSRF tokens
- [ ] Security audit

### Component Library

#### Missing UI Components
- [ ] Accordion
- [ ] Alert/Banner
- [ ] Breadcrumb
- [ ] Dropdown Menu
- [ ] Modal variants
- [ ] Pagination
- [ ] Select/Combobox
- [ ] Slider
- [ ] Switch
- [ ] Tabs
- [ ] Textarea
- [ ] Tooltip
- [ ] Date Picker
- [ ] File Upload

### API Integration

#### Additional Endpoints
- [ ] Analytics API
- [ ] Notification API
- [ ] Chat/Messaging API
- [ ] Payment API (for premium features)
- [ ] Content recommendation API
- [ ] Search API

### Mobile Responsiveness

#### Areas Needing Improvement
- [ ] Mobile-first redesign of dashboard
- [ ] Touch-optimized interactions
- [ ] Mobile navigation improvements
- [ ] Progressive Web App (PWA) setup
- [ ] Native app (React Native) consideration

### Documentation

#### Documentation Needs
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Component documentation (Storybook)
- [ ] User guide
- [ ] Admin documentation
- [ ] Deployment guide
- [ ] Contributing guide

---

## 📝 Notes for AI Agents

### When Working on This Frontend:

1. **Always check authentication state** before making protected API calls
2. **Use the unified API client** (`@/lib/api`) for consistency
3. **Follow the component structure** - UI primitives in `components/ui/`, business logic in `components/auth|user/`
4. **Respect the middleware** - understand which routes are protected
5. **Use TypeScript strictly** - avoid `any` types
6. **Handle errors gracefully** - use toast notifications for user feedback
7. **Test responsive design** - mobile-first approach
8. **Check existing utilities** before creating new ones
9. **Follow naming conventions** - PascalCase for components, camelCase for functions
10. **Document complex logic** with comments

### Common Pitfalls to Avoid:

- ❌ Don't bypass middleware for protected routes
- ❌ Don't store sensitive data in localStorage (use httpOnly cookies)
- ❌ Don't hardcode API URLs (use env config)
- ❌ Don't ignore TypeScript errors
- ❌ Don't create duplicate utilities (check existing ones first)
- ❌ Don't forget error handling in async operations
- ❌ Don't mix client/server components incorrectly
- ❌ Don't forget to validate user input
- ❌ Don't use deprecated `api-client.ts` (use `lib/api/`)
- ❌ Don't ignore accessibility (add proper labels, ARIA)

### Quick Reference Commands:

```bash
# Development
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Run ESLint

# Type Checking
npm run typecheck    # TypeScript type checking (if configured)
```

### File Templates:

**New Page:**
```typescript
// src/app/new-page/page.tsx
export default function NewPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-4">New Page</h1>
      {/* Content */}
    </div>
  );
}
```

**New Component:**
```typescript
// src/components/category/NewComponent.tsx
import { cn } from '@/utils/tailwind';

interface NewComponentProps {
  className?: string;
}

export default function NewComponent({ className }: NewComponentProps) {
  return (
    <div className={cn('base-styles', className)}>
      {/* Component content */}
    </div>
  );
}
```

**New API Module:**
```typescript
// src/lib/api/new-feature.ts
import { apiClient } from './http';

export const newFeatureApi = {
  async list() {
    return apiClient.get('/new-feature');
  },
  async get(id: string) {
    return apiClient.get(`/new-feature/${id}`);
  },
  async create(data: CreateData) {
    return apiClient.post('/new-feature', data);
  },
};
```

---

## 🔗 Related Documentation

- [Backend Services Documentation](../docs/services.md)
- [API Documentation](../docs/docs.md)
- [Frontend Setup Guide](./README.md)
- [Architecture Overview](../docs/architecture.png)

---

**Last Updated:** October 23, 2025  
**Maintained by:** PathLight Development Team  
**For questions or updates, please refer to the main repository documentation.**
