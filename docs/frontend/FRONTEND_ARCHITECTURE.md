# Frontend Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (Port 3000)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    React Application                       │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   Header     │  │  SessionList │  │  Main Content│    │ │
│  │  │  Component   │  │   Sidebar    │  │     Area     │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │           React Query (TanStack Query)               │ │ │
│  │  │  - Cache Management                                  │ │ │
│  │  │  - Auto-refresh Sessions                             │ │ │
│  │  │  - Optimistic Updates                                │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │              Axios API Client                        │ │ │
│  │  │  - POST /api/research/query                          │ │ │
│  │  │  - GET  /api/research/history/{id}                   │ │ │
│  │  │  - GET  /api/research/sessions                       │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                 Vite Development Server                    │ │
│  │  - Hot Module Replacement (HMR)                            │ │
│  │  - CORS Proxy: /api/* → http://localhost:8000             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                 ↓
                          HTTP Requests
                                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (Port 8000)                       │
│                   FastAPI + LangGraph Agents                     │
└─────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
<App>
├── <QueryClientProvider>
│   └── <AppContent>
│       ├── <Header>
│       │   ├── Logo + Icon
│       │   ├── Title + Subtitle
│       │   └── AI Indicator
│       │
│       ├── <div.flex> (Sidebar + Main)
│       │   │
│       │   ├── <SessionSidebar>
│       │   │   ├── New Query Button
│       │   │   ├── Sessions List Header
│       │   │   └── useQuery: sessions
│       │   │       └── map: <SessionItem>
│       │   │           ├── Query Preview
│       │   │           ├── Timestamp
│       │   │           ├── Message Count
│       │   │           └── Active Indicator
│       │   │
│       │   └── <main>
│       │       └── <div.max-w-5xl>
│       │           │
│       │           ├── <div.bg-gray-900>
│       │           │   └── <QueryInput>
│       │           │       ├── Textarea
│       │           │       ├── Character Counter
│       │           │       ├── Submit Button
│       │           │       └── Example Queries
│       │           │
│       │           └── <div> (Content Area)
│       │               │
│       │               ├── {isPending && <LoadingState>}
│       │               │   ├── Spinner
│       │               │   ├── Progress Steps (6)
│       │               │   └── Time Estimate
│       │               │
│       │               ├── {isError && <ErrorState>}
│       │               │   ├── Alert Icon
│       │               │   ├── Error Message
│       │               │   ├── Retry Button
│       │               │   └── Troubleshooting Tips
│       │               │
│       │               ├── {isSuccess && viewMode === 'new' && <ReportDisplay>}
│       │               │   ├── Query Header
│       │               │   │   ├── Query Text
│       │               │   │   ├── Ticker Badges
│       │               │   │   └── Timestamp
│       │               │   ├── Data Indicators (4)
│       │               │   │   ├── Market Data
│       │               │   │   ├── Sentiment
│       │               │   │   ├── Analyst Consensus
│       │               │   │   └── Context Retrieved
│       │               │   ├── Markdown Report
│       │               │   │   └── <ReactMarkdown>
│       │               │   │       ├── H1, H2, H3, H4
│       │               │   │       ├── Lists (ul, ol)
│       │               │   │       ├── Tables
│       │               │   │       ├── Code blocks
│       │               │   │       └── Blockquotes
│       │               │   └── Disclaimer
│       │               │
│       │               ├── {viewMode === 'history' && <SessionHistory>}
│       │               │   ├── Session Header
│       │               │   └── useQuery: history
│       │               │       └── map: <Message>
│       │               │           ├── Avatar (User/Bot)
│       │               │           ├── Name + Timestamp
│       │               │           └── Content
│       │               │               ├── {user: plain text}
│       │               │               └── {ai: <ReactMarkdown>}
│       │               │
│       │               └── {!pending && !error && !report && <EmptyState>}
│       │                   ├── Search Icon
│       │                   ├── Welcome Message
│       │                   ├── Feature Cards (4)
│       │                   ├── Usage Examples
│       │                   └── CTA
│       │
│       └── (end content area)
│
└── (end app)
```

## State Management Flow

### Local State (useState)
```
AppContent Component:
├── currentSessionId: string | null
│   - Tracks active session
│   - Updated on query submit or session click
│   - Used to fetch history
│
├── viewMode: 'new' | 'history'
│   - Determines content display
│   - 'new': Show latest report
│   - 'history': Show conversation thread
│   - Updated on session selection
│
└── currentReport: ResearchQueryResponse | null
    - Stores latest query result
    - Displayed in ReportDisplay
    - Cleared when switching to history
```

### Server State (React Query)

```
Query: ['sessions']
├── Fetcher: researchApi.getSessions()
├── Refetch: Every 10 seconds
├── Stale: 5 minutes
├── Used by: SessionSidebar
└── Updates: Auto-refreshes list

Query: ['session-history', sessionId]
├── Fetcher: researchApi.getSessionHistory(sessionId)
├── Refetch: On window focus
├── Stale: 5 minutes
├── Enabled: Only when sessionId exists
└── Used by: SessionHistory

Mutation: submitQuery
├── Mutator: researchApi.submitQuery({ query, session_id })
├── On Success:
│   ├── Set currentReport
│   ├── Set currentSessionId
│   ├── Set viewMode to 'new'
│   └── Invalidate ['sessions'] query
├── Loading: Show LoadingState
├── Error: Show ErrorState
└── Used by: QueryInput submit
```

## Data Flow Diagram

### Query Submission Flow
```
User Types Query
       ↓
Clicks Submit
       ↓
handleSubmitQuery()
       ↓
submitQueryMutation.mutate()
       ↓
API POST /api/research/query
{
  query: "What is...",
  session_id: "abc123" (optional)
}
       ↓
[15-20 seconds - Backend Processing]
├── Router Agent
├── Market Data Agent
├── Sentiment Agent
└── Report Generator
       ↓
Response Received
{
  session_id: "abc123",
  query: "What is...",
  report: "# Analysis...",
  tickers: ["MSFT"],
  market_data_available: true,
  sentiment_available: true,
  analyst_consensus_available: true,
  context_retrieved: true,
  timestamp: "2025-01-27T10:30:00Z"
}
       ↓
onSuccess Handler
├── setCurrentReport(data)
├── setCurrentSessionId(data.session_id)
├── setViewMode('new')
└── queryClient.invalidateQueries(['sessions'])
       ↓
React Re-renders
├── LoadingState → hidden
├── ReportDisplay → visible
└── SessionSidebar → refreshes
```

### Session Selection Flow
```
User Clicks Session in Sidebar
       ↓
handleSessionSelect(sessionId)
       ↓
setCurrentSessionId(sessionId)
setViewMode('history')
setCurrentReport(null)
       ↓
React Re-renders
       ↓
SessionHistory Mounts
       ↓
useQuery Triggered
       ↓
API GET /api/research/history/{sessionId}
       ↓
Response Received
{
  session_id: "abc123",
  messages: [
    {
      role: "user",
      content: "What is...",
      timestamp: "..."
    },
    {
      role: "assistant",
      content: "# Analysis...",
      timestamp: "..."
    }
  ],
  message_count: 2
}
       ↓
SessionHistory Renders
└── Maps over messages
    ├── User message bubble
    └── AI message bubble (with markdown)
```

### New Session Flow
```
User Clicks "New Research Query"
       ↓
handleNewSession()
       ↓
setCurrentSessionId(null)
setViewMode('new')
setCurrentReport(null)
submitQueryMutation.reset()
       ↓
React Re-renders
├── EmptyState → visible
├── ReportDisplay → hidden
└── SessionHistory → hidden
```

## API Integration Details

### Axios Client Configuration
```typescript
// Base URL: /api (proxied to http://localhost:8000)
// Headers: Content-Type: application/json
// Timeout: Default (no timeout)
// Retry: Handled by React Query (1 retry)
```

### Endpoint Mapping
```
Frontend Request          Vite Proxy              Backend Endpoint
────────────────          ──────────             ────────────────
POST /api/research/query  →  http://localhost:8000  →  POST /api/research/query
GET  /api/research/history/:id  →  http://localhost:8000  →  GET  /api/research/history/:id
GET  /api/research/sessions  →  http://localhost:8000  →  GET  /api/research/sessions
```

### Request/Response Flow
```
Component
   ↓
React Query (useMutation/useQuery)
   ↓
API Client (src/api/client.ts)
   ↓
Axios (with TypeScript types)
   ↓
Vite Dev Server (CORS proxy)
   ↓
Backend FastAPI (port 8000)
   ↓
LangGraph Multi-Agent System
   ↓
Response
   ↓
Axios (parses JSON)
   ↓
React Query (caches)
   ↓
Component (re-renders)
```

## Styling Architecture

### Tailwind CSS Utility Classes
```
Global Styles (index.css)
├── @tailwind base
├── @tailwind components
│   ├── .markdown-content (custom)
│   │   ├── h1, h2, h3, h4
│   │   ├── p, ul, ol, li
│   │   ├── table, thead, tbody
│   │   ├── code, pre
│   │   └── blockquote
│   └── .custom-scrollbar (custom)
└── @tailwind utilities
    └── .gradient-border (custom)

Component Styles (inline classes)
├── Layout: flex, grid, space-x, space-y
├── Colors: bg-gray-950, text-white, border-gray-800
├── Typography: text-xl, font-bold, leading-relaxed
├── Spacing: p-6, m-4, gap-3
├── Borders: border, rounded-lg, border-gray-800
├── Effects: hover:bg-gray-800, transition-all
└── Responsive: md:grid-cols-2, lg:max-w-5xl
```

### Theme Customization
```javascript
// tailwind.config.js
{
  theme: {
    extend: {
      colors: {
        primary: { 50-900 },
        success: { 50-900 },
        danger: { 50-900 }
      },
      fontFamily: {
        sans: ['Inter', ...],
        mono: ['JetBrains Mono', ...]
      }
    }
  }
}
```

## Performance Optimizations

### React Query Caching Strategy
```
Sessions List:
├── Cache Key: ['sessions']
├── Stale Time: 5 minutes
├── Refetch Interval: 10 seconds
├── Refetch on Focus: Yes
└── Benefit: Minimal API calls, fast navigation

Session History:
├── Cache Key: ['session-history', sessionId]
├── Stale Time: 5 minutes
├── Refetch on Focus: Yes
├── Enabled: Only when needed
└── Benefit: Instant history loading for recent sessions
```

### Component Rendering
```
Memoization:
├── React.memo on expensive components
├── useMemo for computed values
├── useCallback for event handlers
└── Benefit: Reduced re-renders

Code Splitting:
├── Vite automatic chunking
├── React.lazy for routes (future)
└── Benefit: Smaller initial bundle
```

### Asset Optimization
```
Fonts:
├── Google Fonts CDN
├── Preconnect in HTML
└── Benefit: Fast font loading

Icons:
├── Lucide React (tree-shakeable)
├── Only used icons imported
└── Benefit: Small icon bundle

CSS:
├── Tailwind purging
├── PostCSS optimization
└── Benefit: Minimal CSS size
```

## Development vs Production

### Development (npm run dev)
```
Port: 3000
Features:
├── Hot Module Replacement (instant updates)
├── Source maps (debugging)
├── Unminified code (readable)
├── CORS proxy (to backend)
└── Fast refresh (preserves state)
```

### Production (npm run build)
```
Output: dist/ folder
Optimizations:
├── Minified JavaScript
├── Minified CSS
├── Tree-shaken dependencies
├── Code splitting
├── Asset hashing
└── Gzipped ~200KB total
```

## Error Handling Strategy

### Network Errors
```
Error Types:
├── Connection refused (backend down)
├── Timeout (slow response)
├── Network failure (no internet)
└── CORS errors (proxy misconfigured)

Handling:
├── React Query retry: 1 attempt
├── Show ErrorState component
├── Display helpful message
└── Provide retry button
```

### API Errors
```
Error Types:
├── 400 Bad Request (invalid query)
├── 404 Not Found (session missing)
├── 500 Server Error (backend crash)
└── Validation errors

Handling:
├── Parse error response
├── Show specific message
├── Log to console
└── Allow user recovery
```

### UI Errors
```
Error Types:
├── Component render errors
├── State update errors
└── Event handler errors

Handling:
├── Error boundaries (future)
├── Try-catch in async functions
└── Graceful degradation
```

## Testing Strategy (Future)

### Unit Tests
```
Components:
├── Header rendering
├── QueryInput validation
├── LoadingState animations
└── ReportDisplay markdown

Utilities:
├── API client functions
├── Date formatting
├── Text truncation
└── Validation logic
```

### Integration Tests
```
Flows:
├── Query submission → report display
├── Session selection → history load
├── New session → empty state
└── Error handling → retry
```

### E2E Tests
```
User Journeys:
├── Complete research workflow
├── Multi-session navigation
├── Error recovery
└── Cross-browser compatibility
```

## Deployment Architecture

### Static Hosting (Recommended)
```
Build:
npm run build
  ↓
dist/ folder
  ├── index.html
  ├── assets/
  │   ├── index-[hash].js
  │   ├── index-[hash].css
  │   └── vendor-[hash].js
  └── vite.svg

Deploy to:
├── Vercel (recommended)
├── Netlify
├── AWS S3 + CloudFront
└── GitHub Pages
```

### Environment Variables
```
Development:
├── VITE_API_BASE_URL (optional)
└── Defaults to proxy config

Production:
├── Build-time env vars
├── Runtime API URL config
└── Feature flags (future)
```

## Security Considerations

### XSS Prevention
```
Markdown Rendering:
├── React Markdown sanitizes HTML
├── remark-gfm plugin (safe)
└── No dangerouslySetInnerHTML

User Input:
├── Controlled form components
├── No eval() or unsafe parsing
└── Server-side validation
```

### CORS
```
Development:
├── Vite proxy handles CORS
└── No exposed credentials

Production:
├── Backend CORS policy
└── Allowed origins configured
```

### Authentication (Future)
```
Planned:
├── JWT tokens
├── Session cookies
├── OAuth integration
└── Role-based access
```

## Monitoring and Analytics (Future)

### Performance Monitoring
```
Metrics:
├── Page load time
├── API response time
├── Component render time
└── Bundle size

Tools:
├── Lighthouse
├── Web Vitals
└── Sentry
```

### User Analytics
```
Events:
├── Query submissions
├── Session switches
├── Error occurrences
└── Feature usage

Tools:
├── Google Analytics
├── Mixpanel
└── PostHog
```

## Conclusion

The frontend architecture provides:

1. **Scalability**: Modular components, React Query caching
2. **Performance**: Optimized rendering, code splitting
3. **Maintainability**: TypeScript, clean architecture
4. **User Experience**: Loading states, error handling
5. **Accessibility**: WCAG compliance, keyboard support
6. **Developer Experience**: Hot reload, TypeScript, linting

The system is production-ready and built on modern best practices.
