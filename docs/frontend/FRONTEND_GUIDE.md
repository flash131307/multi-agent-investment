# Investment Research System - Frontend User Guide

## Installation

### Step 1: Navigate to Frontend Directory
```bash
cd /Users/mayuhao/PythonProject/PythonProject/frontend
```

### Step 2: Install Dependencies
```bash
npm install
```

This installs:
- React 18.2.0
- TypeScript 5.3.3
- Vite 5.0.12
- Tailwind CSS 3.4.1
- React Query (TanStack Query) 5.17.0
- Axios 1.6.5
- React Markdown 9.0.1
- Lucide React 0.309.0

### Step 3: Start Backend (Required)
In a separate terminal:
```bash
cd /Users/mayuhao/PythonProject/PythonProject
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### Step 4: Start Frontend
```bash
npm run dev
```

Access at: **http://localhost:3000**

## User Interface Overview

### Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│                      HEADER                                  │
│  Investment Research System - Multi-Agent Equity Analysis   │
└─────────────────────────────────────────────────────────────┘
┌──────────┬──────────────────────────────────────────────────┐
│          │                                                   │
│ SESSION  │              MAIN CONTENT AREA                   │
│ SIDEBAR  │                                                   │
│          │  ┌──────────────────────────────────────┐        │
│ ┌──────┐ │  │     Query Input (Textarea)          │        │
│ │ New  │ │  │                                      │        │
│ │Query │ │  └──────────────────────────────────────┘        │
│ └──────┘ │                                                   │
│          │  ┌──────────────────────────────────────┐        │
│ Session1 │  │     Example Queries                  │        │
│ Session2 │  └──────────────────────────────────────┘        │
│ Session3 │                                                   │
│          │  ┌──────────────────────────────────────┐        │
│          │  │     Report / History Display         │        │
│          │  │                                      │        │
│          │  │     (Dynamic Content Area)           │        │
│          │  │                                      │        │
│          │  └──────────────────────────────────────┘        │
│          │                                                   │
└──────────┴──────────────────────────────────────────────────┘
```

## Features Breakdown

### 1. Header Component
**Location**: Top of screen, always visible

**Elements**:
- Logo with gradient effect and TrendingUp icon
- Title: "Investment Research System"
- Subtitle: "Multi-Agent Equity Analysis Platform"
- AI indicator badge

**Styling**: Dark gray background with bottom border

---

### 2. Session Sidebar
**Location**: Left side, 320px width

**Features**:
- **New Query Button**: Creates fresh session
- **Sessions List**: All previous sessions
- **Auto-refresh**: Updates every 10 seconds
- **Active indicator**: Highlights current session

**Session Card Shows**:
- First query preview (truncated to 60 chars)
- Time ago (e.g., "2h ago", "Just now")
- Message count
- Clickable to load history

**States**:
- Loading: Spinner animation
- Empty: "No sessions yet" message
- Error: Red error message

---

### 3. Query Input Form
**Location**: Top of main content area

**Features**:
- Large textarea (128px height)
- Character counter
- Submit button with loading state
- Disabled during processing
- Gradient submit button
- Send icon animation

**Example Queries Section**:
- 4 pre-written queries
- Click to populate textarea
- Hover effects
- Hidden during loading

**Validation**:
- Requires non-empty text
- Trims whitespace
- Clears after submission

---

### 4. Loading State
**Duration**: 15-20 seconds

**Displays**:
```
┌────────────────────────────────────────┐
│     Analyzing Investment Opportunity    │
│                                         │
│  [Spinner]                              │
│                                         │
│  Progress Steps:                        │
│  ✓ Routing query                        │
│  ✓ Extracting tickers                   │
│  → Fetching market data                 │
│  ○ Analyzing sentiment                  │
│  ○ Gathering analyst data               │
│  ○ Synthesizing report                  │
│                                         │
│  Processing Time: 15-20 seconds         │
└────────────────────────────────────────┘
```

**Steps** (with icons):
1. Brain icon - Query routing
2. Database icon - Ticker extraction
3. TrendingUp icon - Market data
4. FileText icon - Sentiment analysis
5. BarChart3 icon - Analyst consensus
6. CheckCircle icon - Report synthesis

**Colors**:
- Completed: Green checkmark
- Current: Blue with pulse animation
- Pending: Gray

---

### 5. Report Display
**Components**:

**A. Query Header**
```
┌────────────────────────────────────────┐
│ Research Query                          │
│ What is the investment outlook for MSFT?│
│                                         │
│ [MSFT] [AAPL]  ← Ticker badges         │
│                                         │
│ Jan 27, 2025 10:30 • ab12cd34           │
└────────────────────────────────────────┘
```

**B. Data Availability Indicators**
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Market Data  │ Sentiment    │ Analyst      │ Context      │
│ ✓ Available  │ ✓ Available  │ ✓ Available  │ ✓ Retrieved  │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**C. Markdown Report**
Full research report with:
- Headers (H1-H4)
- Bullet lists
- Tables (styled for financial data)
- Bold/italic text
- Code blocks
- Blockquotes
- Horizontal rules

**D. Disclaimer Footer**
AI-generated content warning

---

### 6. Session History View
**Triggered**: Clicking a session in sidebar

**Displays**:
```
┌────────────────────────────────────────┐
│ Session History • 4 messages            │
│ ab12cd34...                             │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ [User Icon] You               10:30 AM │
│ ┌────────────────────────────────────┐ │
│ │ What is MSFT outlook?              │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ [Bot Icon] Research Assistant 10:30 AM │
│ ┌────────────────────────────────────┐ │
│ │ Full markdown report...            │ │
│ │ (Rendered with formatting)         │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Features**:
- User messages: Left-aligned, blue gradient avatar
- AI messages: Left-aligned, gray gradient avatar
- Timestamps for each message
- Markdown rendering for AI responses
- Plain text for user queries

---

### 7. Empty State
**When**: No report loaded, new session

**Displays**:
```
┌────────────────────────────────────────┐
│     [Search Icon]                       │
│                                         │
│ Welcome to Investment Research System   │
│ Get comprehensive equity analysis       │
│                                         │
│ [4 Feature Cards]                       │
│ Market Data | Sentiment | Analyst | Val│
│                                         │
│ What you can ask:                       │
│ • Investment outlook for companies      │
│ • Performance analysis                  │
│ • Comparative analysis                  │
│ • Market trends                         │
│                                         │
│ Enter your research query above         │
└────────────────────────────────────────┘
```

---

### 8. Error State
**When**: API failure, network error

**Displays**:
```
┌────────────────────────────────────────┐
│     [Alert Icon]                        │
│                                         │
│     Something went wrong                │
│     Error message here...               │
│                                         │
│     [Try Again Button]                  │
│                                         │
│ Troubleshooting:                        │
│ • Backend running at localhost:8000?    │
│ • Internet connection stable?           │
│ • Valid stock symbols?                  │
└────────────────────────────────────────┘
```

---

## Color Scheme

### Primary (Blue)
- **600**: `#0284c7` - Main accent
- **700**: `#0369a1` - Hover states
- **500**: `#0ea5e9` - Highlights

### Success (Green)
- **500**: `#22c55e` - Available indicators
- **400**: `#4ade80` - Success text

### Danger (Red)
- **500**: `#ef4444` - Errors
- **400**: `#f87171` - Error text

### Grays (Background)
- **950**: `#030712` - Main background
- **900**: `#111827` - Cards
- **800**: `#1f2937` - Borders
- **700**: `#374151` - Dividers

---

## Typography

### Fonts
- **Sans**: Inter (UI text)
- **Mono**: JetBrains Mono (code, IDs)

### Sizes
- **3xl**: Markdown H1
- **2xl**: Markdown H2, page titles
- **xl**: Markdown H3, section headers
- **lg**: Markdown H4
- **base**: Body text
- **sm**: Metadata, labels
- **xs**: Timestamps, small text

---

## Responsive Design

### Breakpoints
- **Mobile**: < 768px
  - Sidebar hidden/collapsed
  - Single column layout
  - Full-width query input

- **Tablet**: 768px - 1024px
  - Sidebar visible
  - Adjusted spacing
  - 2-column grids

- **Desktop**: > 1024px
  - Full layout
  - Maximum content width: 1280px
  - 4-column grids

---

## Interactions

### Hover Effects
- **Buttons**: Background darkens, cursor pointer
- **Session cards**: Border highlights, chevron animates
- **Example queries**: Background change, text color shift

### Loading States
- **Submit button**: Shows spinner, text changes
- **Spinner animations**: Smooth rotation
- **Progress steps**: Pulse animations on current step

### Transitions
- **All elements**: 200ms duration
- **Background colors**: Smooth fade
- **Border colors**: Gentle shift
- **Text colors**: Instant or 200ms

---

## Data Flow

### Query Submission
```
User Input
   ↓
Validation
   ↓
API POST /api/research/query
   ↓
Loading State (15-20s)
   ↓
Response Received
   ↓
Report Display
   ↓
Session Sidebar Updates
```

### Session Loading
```
Click Session
   ↓
API GET /api/research/history/{id}
   ↓
Loading Spinner
   ↓
History Received
   ↓
Message List Display
```

---

## React Query Caching

### Sessions List
- **Cache key**: `['sessions']`
- **Refetch**: Every 10 seconds
- **Stale time**: 5 minutes
- **Retry**: Once on failure

### Session History
- **Cache key**: `['session-history', sessionId]`
- **Refetch**: On window focus
- **Stale time**: 5 minutes
- **Enabled**: Only when sessionId exists

### Query Mutation
- **Invalidates**: `['sessions']` on success
- **Optimistic**: No (waits for server response)
- **Retry**: Once on failure

---

## Accessibility

### Keyboard Navigation
- Tab through all interactive elements
- Enter to submit forms
- Escape to close modals (future)

### Screen Readers
- Semantic HTML (`<header>`, `<main>`, `<nav>`)
- ARIA labels on icons
- Alt text for images
- Proper heading hierarchy

### Color Contrast
- All text meets WCAG AA standards
- 4.5:1 ratio for normal text
- 3:1 ratio for large text

---

## Performance

### Optimizations
- React.memo for expensive components
- useMemo for computed values
- Debounced search (future)
- Lazy loading for routes (future)

### Bundle Size
- Vite code splitting
- Tree shaking
- Minimal dependencies
- Production build ~200KB gzipped

---

## Browser Compatibility

### Supported
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Features Used
- CSS Grid
- Flexbox
- CSS Variables
- Fetch API
- ES2020 features

---

## Development Workflow

### 1. Start Development
```bash
npm run dev
```

### 2. Make Changes
Edit files in `src/`
- Components auto-reload
- Styles rebuild instantly
- State preserved when possible

### 3. Test in Browser
- Open http://localhost:3000
- Check DevTools console
- Use React Query DevTools

### 4. Build for Production
```bash
npm run build
npm run preview
```

---

## Common Tasks

### Add New Component
1. Create `src/components/NewComponent.tsx`
2. Import in `App.tsx`
3. Add to component tree
4. Test in browser

### Modify Styles
1. Edit Tailwind classes in components
2. Or update `tailwind.config.js` for theme
3. Or add custom CSS in `index.css`

### Add API Endpoint
1. Add type in `src/types/index.ts`
2. Add function in `src/api/client.ts`
3. Use with React Query in component

### Change Colors
1. Edit `tailwind.config.js`
2. Update `colors.primary`, etc.
3. Rebuild with `npm run dev`

---

## Troubleshooting

### Issue: White screen
**Fix**: Check browser console for errors

### Issue: No sessions showing
**Fix**: Verify MongoDB connection in backend

### Issue: API errors
**Fix**: Check backend is running on port 8000

### Issue: Slow loading
**Normal**: Reports take 15-20 seconds

### Issue: Styles broken
**Fix**: Run `npm run dev` to rebuild

---

## File Quick Reference

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts           # API integration
│   ├── components/
│   │   ├── Header.tsx          # Top bar
│   │   ├── QueryInput.tsx      # Query form
│   │   ├── LoadingState.tsx    # Progress UI
│   │   ├── ReportDisplay.tsx   # Report viewer
│   │   ├── SessionSidebar.tsx  # Session list
│   │   ├── SessionHistory.tsx  # Chat view
│   │   ├── ErrorState.tsx      # Error UI
│   │   └── EmptyState.tsx      # Welcome screen
│   ├── types/
│   │   └── index.ts            # TypeScript types
│   ├── App.tsx                 # Main component
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles
├── index.html                  # HTML template
├── package.json                # Dependencies
├── vite.config.ts              # Build config
├── tailwind.config.js          # Theme config
└── tsconfig.json               # TypeScript config
```

---

## Summary

You now have a production-ready React frontend featuring:

- **Professional UI/UX**: Investment-grade dark theme
- **Real-time Updates**: Auto-refreshing sessions
- **Session Management**: Full conversation history
- **Rich Formatting**: Markdown reports with tables
- **Error Handling**: Graceful degradation
- **Responsive**: Works on all devices
- **Performance**: Optimized with React Query caching
- **Accessibility**: Keyboard and screen reader support

**Start using**: `npm run dev` → http://localhost:3000

**Test with**: "What is the investment outlook for Microsoft?"

Enjoy your professional investment research platform!
