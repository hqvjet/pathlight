# Generation Tracking API - Frontend Integration Guide

## Tổng quan

API này cung cấp real-time progress tracking cho quá trình tạo khóa học, giúp user biết được tiến trình chi tiết thay vì chờ đợi trong vô vọng.

## Endpoint để Frontend Poll

```
GET /api/courses/{course_id}/status
```

hoặc nếu dùng DynamoDB trực tiếp:
```javascript
// AWS SDK v3
import { DynamoDBClient, GetItemCommand } from "@aws-sdk/client-dynamodb";
import { unmarshall } from "@aws-sdk/util-dynamodb";

const client = new DynamoDBClient({ region: "your-region" });
const command = new GetItemCommand({
  TableName: "your-table-name",
  Key: { course_id: { S: courseId } }
});
const response = await client.send(command);
const status = unmarshall(response.Item);
```

## Response Schema

```typescript
interface CourseGenerationStatus {
  // Primary identifiers
  course_id: string;
  user_id: string;
  
  // Progress tracking
  status: "initializing" | "planning" | "creating_lessons" | "creating_tests" | "finalizing" | "completed" | "failed";
  progress_percentage: number; // 0-100
  current_step: string; // Tiếng Việt, human-readable
  current_step_detail: string; // Chi tiết về bước hiện tại
  
  // Estimated time
  estimated_time_remaining_seconds?: number; // Thời gian ước tính còn lại (giây)
  
  // Phase flags
  title_ready: boolean;
  lessons_ready: boolean;
  tests_ready: boolean;
  
  // Content metadata
  title?: string;
  description?: string;
  roadmap_count?: number; // Tổng số bài học dự kiến
  lessons_count?: number; // Số bài học đã tạo
  lessons_planned?: number; // Số bài học dự định tạo
  
  // Timestamps
  start_timestamp?: number; // Unix timestamp (seconds)
  end_timestamp?: number; // Unix timestamp khi hoàn thành/thất bại
  updated_at: string; // ISO 8601
  
  // Error handling
  error_message?: string; // Chỉ có khi status = "failed"
}
```

## Các Trạng Thái (Status Flow)

### 1. `initializing` (0%)
```javascript
{
  "status": "initializing",
  "progress_percentage": 0,
  "current_step": "Khởi tạo",
  "current_step_detail": "Đang khởi tạo workflow tạo khóa học...",
  "estimated_time_remaining_seconds": 240
}
```
**Hiển thị cho user**: "Đang khởi tạo..."

---

### 2. `planning` (20%)
```javascript
{
  "status": "planning",
  "progress_percentage": 20,
  "current_step": "Lập kế hoạch",
  "current_step_detail": "Đang phân tích yêu cầu và tạo roadmap khóa học...",
  "estimated_time_remaining_seconds": 210
}
```
**Hiển thị cho user**: "Đang phân tích và lập kế hoạch khóa học..."

---

### 3. `creating_lessons` (40-80%)
```javascript
{
  "status": "creating_lessons",
  "progress_percentage": 52, // Tính động: 40 + (2/5 * 40) = 56
  "current_step": "Tạo bài học 2/5",
  "current_step_detail": "Đang tạo nội dung chi tiết cho bài học thứ 2...",
  "title": "Mô hình tối ưu hóa chi phí",
  "roadmap_count": 5,
  "lessons_count": 2,
  "lessons_planned": 5,
  "estimated_time_remaining_seconds": 135
}
```

**Progress calculation**:
- Start: 40% (khi bắt đầu tạo lesson 1)
- End: 80% (khi hoàn thành tất cả lessons)
- Formula: `40 + (lessons_created / lessons_total * 40)`

**Hiển thị cho user**: 
```
Đang tạo bài học 2/5
[████████░░░░░░░░] 52%
Còn khoảng 2 phút 15 giây
```

---

### 4. `creating_tests` (85%)
```javascript
{
  "status": "creating_tests",
  "progress_percentage": 85,
  "current_step": "Tạo bài kiểm tra",
  "current_step_detail": "Đã hoàn thành 5 bài học. Đang tạo câu hỏi đánh giá...",
  "lessons_ready": true,
  "lessons_count": 5,
  "estimated_time_remaining_seconds": 30
}
```
**Hiển thị cho user**: "Đang tạo câu hỏi đánh giá..."

---

### 5. `finalizing` (95%)
```javascript
{
  "status": "finalizing",
  "progress_percentage": 95,
  "current_step": "Hoàn thiện",
  "current_step_detail": "Đang hoàn thiện và lưu khóa học...",
  "tests_ready": true,
  "estimated_time_remaining_seconds": 10
}
```
**Hiển thị cho user**: "Đang hoàn thiện khóa học..."

---

### 6. `completed` (100%)
```javascript
{
  "status": "completed",
  "progress_percentage": 100,
  "current_step": "Hoàn thành",
  "current_step_detail": "Khóa học đã được tạo thành công!",
  "title_ready": true,
  "lessons_ready": true,
  "tests_ready": true,
  "title": "Mô hình tối ưu hóa chi phí",
  "description": "Khóa học về các mô hình...",
  "roadmap_count": 5,
  "lessons_count": 5,
  "estimated_time_remaining_seconds": 0,
  "start_timestamp": 1704326400,
  "end_timestamp": 1704326640
}
```
**Hiển thị cho user**: 
```
✓ Tạo khóa học thành công!
Hoàn thành trong 4 phút
```

---

### 7. `failed` (Error State)
```javascript
{
  "status": "failed",
  "progress_percentage": 0,
  "current_step": "Thất bại",
  "current_step_detail": "Đã xảy ra lỗi trong quá trình tạo khóa học",
  "error_message": "Validation error: content must be at least 50 chars",
  "end_timestamp": 1704326500
}
```
**Hiển thị cho user**: 
```
✗ Tạo khóa học thất bại
Lỗi: Validation error: content must be at least 50 chars
```

---

## Frontend Implementation Example

### React Hook
```typescript
import { useState, useEffect } from 'react';

interface UseGenerationStatusOptions {
  courseId: string;
  pollInterval?: number; // milliseconds, default: 2000
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useGenerationStatus({
  courseId,
  pollInterval = 2000,
  onComplete,
  onError
}: UseGenerationStatusOptions) {
  const [status, setStatus] = useState<CourseGenerationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchStatus = async () => {
      try {
        const response = await fetch(`/api/courses/${courseId}/status`);
        const data = await response.json();
        setStatus(data);
        setIsLoading(false);

        // Stop polling when completed or failed
        if (data.status === 'completed') {
          clearInterval(intervalId);
          onComplete?.();
        } else if (data.status === 'failed') {
          clearInterval(intervalId);
          onError?.(data.error_message);
        }
      } catch (error) {
        console.error('Failed to fetch status:', error);
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchStatus();

    // Poll every N seconds
    intervalId = setInterval(fetchStatus, pollInterval);

    return () => clearInterval(intervalId);
  }, [courseId, pollInterval, onComplete, onError]);

  return { status, isLoading };
}
```

### React Component
```typescript
import { useGenerationStatus } from './hooks/useGenerationStatus';

function CourseGenerationProgress({ courseId }: { courseId: string }) {
  const { status, isLoading } = useGenerationStatus({
    courseId,
    onComplete: () => {
      // Redirect to course page
      window.location.href = `/courses/${courseId}`;
    },
    onError: (error) => {
      alert(`Tạo khóa học thất bại: ${error}`);
    }
  });

  if (isLoading || !status) {
    return <div>Đang tải...</div>;
  }

  const formatTimeRemaining = (seconds?: number) => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) return `${mins} phút ${secs} giây`;
    return `${secs} giây`;
  };

  return (
    <div className="generation-progress">
      <h2>{status.current_step}</h2>
      <p>{status.current_step_detail}</p>
      
      {/* Progress bar */}
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${status.progress_percentage}%` }}
        />
      </div>
      <p>{status.progress_percentage}%</p>
      
      {/* Time remaining */}
      {status.estimated_time_remaining_seconds && (
        <p>Còn khoảng {formatTimeRemaining(status.estimated_time_remaining_seconds)}</p>
      )}
      
      {/* Lesson progress */}
      {status.status === 'creating_lessons' && (
        <p>
          Đã tạo {status.lessons_count}/{status.lessons_planned} bài học
        </p>
      )}
      
      {/* Error message */}
      {status.status === 'failed' && (
        <div className="error">
          <p>❌ {status.error_message}</p>
        </div>
      )}
    </div>
  );
}
```

---

## Thời gian ước tính

### Công thức tính estimated_time_remaining_seconds

```python
# Assumptions (có thể điều chỉnh):
PLANNING_TIME = 30  # seconds
LESSON_TIME = 45    # seconds per lesson
TESTS_TIME = 20     # seconds
FINALIZING_TIME = 10  # seconds

if status == "initializing":
    remaining = PLANNING_TIME + (total_lessons * LESSON_TIME) + TESTS_TIME + FINALIZING_TIME
elif status == "planning":
    remaining = PLANNING_TIME + (total_lessons * LESSON_TIME) + TESTS_TIME + FINALIZING_TIME
elif status == "creating_lessons":
    lessons_left = total_lessons - lessons_created
    remaining = (lessons_left * LESSON_TIME) + TESTS_TIME + FINALIZING_TIME
elif status == "creating_tests":
    remaining = TESTS_TIME + FINALIZING_TIME
elif status == "finalizing":
    remaining = FINALIZING_TIME
else:
    remaining = 0
```

**Ví dụ**: Khóa học 5 bài
- initializing: ~240s (4 phút)
- planning: ~240s
- creating_lessons (0/5): ~235s
- creating_lessons (3/5): ~145s
- creating_tests: ~30s
- finalizing: ~10s
- completed: 0s

---

## Polling Strategy

### Recommended
- **Interval**: 2 seconds (2000ms)
- **Stop conditions**: 
  - status === "completed"
  - status === "failed"
- **Exponential backoff** (optional): Nếu muốn giảm load, tăng interval dần (2s → 3s → 5s)

### Example với exponential backoff
```typescript
let pollInterval = 2000;
let consecutivePolls = 0;

const poll = () => {
  fetchStatus();
  consecutivePolls++;
  
  // Increase interval after 10 polls (20s)
  if (consecutivePolls > 10) {
    pollInterval = 3000;
  }
  if (consecutivePolls > 20) {
    pollInterval = 5000;
  }
  
  setTimeout(poll, pollInterval);
};
```

---

## UX Best Practices

### 1. Loading State
```
┌─────────────────────────────────┐
│  Đang tạo khóa học...           │
│  [████████░░░░░░░░] 52%         │
│                                 │
│  Tạo bài học 2/5                │
│  Đang tạo nội dung chi tiết...  │
│  Còn khoảng 2 phút              │
└─────────────────────────────────┘
```

### 2. Success State
```
┌─────────────────────────────────┐
│  ✓ Tạo khóa học thành công!     │
│  [████████████████████] 100%    │
│                                 │
│  Mô hình tối ưu hóa chi phí     │
│  5 bài học • 3 giờ học          │
│                                 │
│  [Xem khóa học]                 │
└─────────────────────────────────┘
```

### 3. Error State
```
┌─────────────────────────────────┐
│  ✗ Tạo khóa học thất bại        │
│                                 │
│  Lỗi: Validation error          │
│                                 │
│  [Thử lại] [Hủy]                │
└─────────────────────────────────┘
```

### 4. Prevent User Leaving
```javascript
useEffect(() => {
  if (status?.status && !['completed', 'failed'].includes(status.status)) {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = 'Khóa học đang được tạo. Bạn có chắc muốn rời khỏi trang?';
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }
}, [status]);
```

---

## Testing

### Mock Data cho Development
```typescript
// Mock different stages
const mockStatuses = {
  initializing: {
    status: 'initializing',
    progress_percentage: 0,
    current_step: 'Khởi tạo',
    estimated_time_remaining_seconds: 240
  },
  creating_lessons: {
    status: 'creating_lessons',
    progress_percentage: 52,
    current_step: 'Tạo bài học 2/5',
    lessons_count: 2,
    lessons_planned: 5,
    estimated_time_remaining_seconds: 135
  },
  completed: {
    status: 'completed',
    progress_percentage: 100,
    current_step: 'Hoàn thành'
  }
};
```

---

## Notes

1. **Real-time**: DynamoDB items được update real-time bởi backend agents
2. **Consistency**: Tất cả timestamps đều là Unix timestamp (seconds)
3. **Locale**: current_step và current_step_detail đã được localize sang Tiếng Việt
4. **Error handling**: Luôn check status === "failed" để hiển thị error
5. **Completion**: Khi status === "completed", có thể redirect user đến course page

---

## Summary

**Key Points cho Frontend**:
- ✅ Poll mỗi 2 giây endpoint `/api/courses/{course_id}/status`
- ✅ Hiển thị progress bar với `progress_percentage`
- ✅ Hiển thị text `current_step` và `current_step_detail`
- ✅ Hiển thị thời gian còn lại từ `estimated_time_remaining_seconds`
- ✅ Hiển thị lesson progress `lessons_count/lessons_planned` khi status = "creating_lessons"
- ✅ Stop polling khi status = "completed" hoặc "failed"
- ✅ Redirect khi completed, show error khi failed
- ✅ Prevent user rời trang khi đang tạo
