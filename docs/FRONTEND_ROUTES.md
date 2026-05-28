# Frontend Routes Reference

## Public Routes (No Authentication Required)

### `/` - Landing Page
- **File**: `frontend/src/app/page.tsx`
- **Purpose**: Marketing landing page for new visitors
- **Behavior**:
  - If user is authenticated (has `access_token`) → redirects to `/dashboard`
  - If not authenticated → shows full landing page
- **Sections**:
  - **Hero**: Eye-catching headline with animated background blobs, CTA buttons
  - **Features**: 6 key capabilities showcased with icons
    - 15-20 Personalized Questions
    - Skill-Based Practical Tests
    - Objective Scoring Rubric
    - Red Flag Detection
    - Interview Flow Guide
    - Match Analysis
  - **How It Works**: 3-step process explanation
  - **Supported Roles**: 9 engineering roles badges
  - **CTA Section**: Final conversion section with gradient background
  - **Footer**: Brand info and copyright
- **Actions**: 
  - "Get Started Free" button → `/login`
  - "Sign In" button → `/login`
  - "Start Generating Kits Now" button → `/login`
- **Design Features**:
  - Gradient backgrounds
  - Animated blob elements
  - Hover effects on feature cards
  - Responsive mobile-friendly layout
  - Modern Tailwind CSS styling

### `/login` - Authentication Page
- **File**: `frontend/src/app/login/page.tsx`
- **Purpose**: User login and registration
- **Features**:
  - Toggle between Login and Register modes
  - **Login Fields**: Email, Password
  - **Register Fields**: Full Name, Email, Password
- **On Success**: 
  - Stores `access_token` and `refresh_token` in localStorage
  - Redirects to `/dashboard`
- **API Calls**:
  - `POST /auth/register` - Create new account
  - `POST /auth/login` - Authenticate user

---

## Protected Routes (Authentication Required)

All protected routes check for `access_token` in localStorage on mount. If missing, redirects to `/login`.

### `/dashboard` - User Dashboard
- **File**: `frontend/src/app/dashboard/page.tsx`
- **Purpose**: View all generated interview kits
- **Features**:
  - List of all kits with status
  - "New Kit" button → `/generate`
  - "Logout" button → clears tokens, redirects to `/login`
- **API Calls**:
  - `GET /kits` - Fetch user's kits
- **Shows**:
  - Kit title, role type, status, creation date
  - Click on kit → `/kit/{id}`

### `/generate` - Kit Generation Form
- **File**: `frontend/src/app/generate/page.tsx`
- **Purpose**: Create a new interview kit
- **Form Fields**:
  - **Role Type** (dropdown):
    - Backend Engineer
    - Frontend Engineer
    - Full Stack Engineer
    - Data Engineer
    - Data Scientist
    - DevOps / SRE
    - ML Engineer
    - Mobile Developer
    - Engineering Manager
  - **Job Description** (textarea): Full JD text
  - **Resume** (two options):
    - File upload (PDF/DOCX)
    - OR paste resume text
- **On Submit**:
  - Creates FormData with `jd_text`, `role_type`, `resume_file` OR `resume_text`
  - `POST /kits/generate` → returns `{kit_id, job_id}`
  - Redirects to `/kit/{kit_id}`
- **API Calls**:
  - `POST /kits/generate` - Start kit generation

### `/kit/[id]` - View Generated Kit
- **File**: `frontend/src/app/kit/[id]/page.tsx`
- **Purpose**: Display a generated interview kit
- **Dynamic Route**: `[id]` is the kit UUID
- **Features**:
  - Shows generation progress if still processing
  - Displays all sections when complete:
    - Match Analysis
    - Interview Questions (15-20 questions with categories)
    - Practical Test (skill-based assessments)
    - Scoring Rubric
    - Red Flags
    - Interview Flow Guide
  - PDF export button
  - Share kit button
- **API Calls**:
  - `GET /kits/{id}` - Fetch kit details
  - `GET /export/pdf/{kit_id}` - Download PDF
  - `POST /export/share/{kit_id}` - Generate share link

---

## Route Hierarchy

```
/                           Landing page
├── /login                  Login/Register
│
├── /dashboard              Dashboard (protected)
│   └── Link to /generate
│   └── Link to /kit/{id}
│
├── /generate               Create kit (protected)
│   └── Submits → /kit/{id}
│
└── /kit/{id}               View kit (protected)
    └── Back to /dashboard
```

---

## Authentication Flow

### New User Flow
```
/ → /login (click "Get Started")
  → Fill registration form
  → POST /auth/register
  → POST /auth/login
  → Store tokens
  → Redirect to /dashboard
```

### Returning User Flow
```
/ → Check localStorage for access_token
  → If found: Redirect to /dashboard
  → If not found: Show landing page → /login
```

### Logout Flow
```
/dashboard → Click "Logout"
  → Clear localStorage (access_token, refresh_token)
  → Redirect to /login
```

---

## API Integration

### Authentication
All API requests automatically include `Authorization: Bearer {access_token}` header via axios interceptor in `frontend/src/lib/api-client.ts`.

### 401 Handler
If any API call returns 401 Unauthorized:
- Automatically clears `access_token` from localStorage
- Redirects to `/login`

### Base URL
Default: `http://localhost:8000/api/v1`  
Configurable via `NEXT_PUBLIC_API_URL` environment variable

---

## Components Used

### Shared Components
- `<FileUpload />` - File upload with drag & drop
- `<KitViewer />` - Display generated kit sections

### Toast Notifications
Uses `react-hot-toast` for success/error messages throughout the app.

---

## State Management

**Client-Side State**:
- `localStorage.access_token` - JWT access token
- `localStorage.refresh_token` - JWT refresh token (currently unused)

**No global state management** - each page manages its own state with React hooks.

---

## Styling

- **Framework**: Tailwind CSS
- **Brand Color**: `brand-600` (defined in tailwind.config.ts)
- **Design**: Clean, minimal, modern
- **Responsive**: Mobile-friendly layouts

---

## Navigation Patterns

### From Landing Page
- Unauthenticated: Shows "Get Started" & "Sign In" → `/login`
- Authenticated: Auto-redirects to `/dashboard`

### From Login
- After successful login → `/dashboard`

### From Dashboard
- Click kit → `/kit/{id}`
- Click "New Kit" → `/generate`
- Click "Logout" → `/login`

### From Generate
- After submission → `/kit/{id}` (newly created kit)

### From Kit View
- Browser back button or navigation → `/dashboard`

---

## Development URLs

When running locally:
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Routes work as**:
  - http://localhost:3000/ - Landing
  - http://localhost:3000/login - Login
  - http://localhost:3000/dashboard - Dashboard
  - http://localhost:3000/generate - Generate
  - http://localhost:3000/kit/{uuid} - View Kit
