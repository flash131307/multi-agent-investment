# Component Reference Guide

Complete visual and technical reference for all React components in the Investment Research System frontend.

---

## Component Catalog

### 1. Header Component

**File**: `/frontend/src/components/Header.tsx`

**Purpose**: Top navigation bar with branding and status indicator

**Visual Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  [Icon] Investment Research System    AI-Powered Analysis   │
│         Multi-Agent Equity Analysis Platform                 │
└─────────────────────────────────────────────────────────────┘
```

**Props**: None

**Features**:
- Gradient logo with TrendingUp icon
- Sticky positioning (always visible)
- Dark gray background with bottom border
- Responsive text sizing

**Styling**:
- Background: `bg-gray-900`
- Border: `border-b border-gray-800`
- Padding: `px-6 py-4`
- Position: `sticky top-0 z-50`

**Icons Used**:
- `TrendingUp` (logo)
- `BarChart3` (AI indicator)

---

### 2. QueryInput Component

**File**: `/frontend/src/components/QueryInput.tsx`

**Purpose**: Research query submission form with examples

**Visual Layout**:
```
┌──────────────────────────────────────────────┐
│  Textarea (placeholder text)                 │
│                                              │
│                                              │
│                         120 characters       │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  [Send Icon] Submit Research Query           │
└──────────────────────────────────────────────┘

Example queries:
┌────────────────────┬────────────────────────┐
│ Example 1          │ Example 2              │
└────────────────────┴────────────────────────┘
```

**Props**:
```typescript
interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}
```

**Features**:
- Large textarea (128px height)
- Character counter (bottom right)
- Gradient submit button
- 4 clickable example queries
- Loading state with spinner
- Disabled during processing

**States**:
- **Idle**: Ready for input
- **Typing**: Character counter updates
- **Loading**: Spinner, button disabled, examples hidden
- **Disabled**: During API call

**Styling**:
- Textarea: `bg-gray-900 border border-gray-700`
- Button: `bg-gradient-to-r from-primary-600 to-primary-700`
- Examples: `bg-gray-900 hover:bg-gray-800 border-gray-800`

**Icons Used**:
- `Send` (submit button)
- `Sparkles` (examples header)

**Example Queries**:
1. "What is the investment outlook for Microsoft?"
2. "Analyze Apple's recent performance and valuation"
3. "Compare Tesla and traditional automakers"
4. "Should I invest in NVIDIA stock?"

---

### 3. LoadingState Component

**File**: `/frontend/src/components/LoadingState.tsx`

**Purpose**: Visual progress indicator during 15-20 second analysis

**Visual Layout**:
```
┌──────────────────────────────────────────────┐
│         Analyzing Investment Opportunity     │
│                                              │
│                 [Spinner]                    │
│   Multi-agent system gathering data...       │
│                                              │
│  ✓ Routing query                             │
│  ✓ Extracting tickers                        │
│  → Fetching market data                      │
│  ○ Analyzing sentiment                       │
│  ○ Gathering analyst data                    │
│  ○ Synthesizing report                       │
│                                              │
│  Processing Time: 15-20 seconds              │
└──────────────────────────────────────────────┘
```

**Props**: None

**Features**:
- 6-step progress visualization
- Time-based step progression
- Animated icons
- Color-coded status
- Educational information

**Progress Steps**:
```typescript
const ANALYSIS_STEPS = [
  { icon: Brain, label: 'Routing query...', duration: 2000 },
  { icon: Database, label: 'Extracting tickers', duration: 3000 },
  { icon: TrendingUp, label: 'Fetching market data', duration: 5000 },
  { icon: FileText, label: 'Analyzing sentiment', duration: 7000 },
  { icon: BarChart3, label: 'Gathering consensus', duration: 10000 },
  { icon: CheckCircle2, label: 'Synthesizing report', duration: 15000 },
];
```

**Step States**:
- **Complete**: Green checkmark, gray text
- **Current**: Blue icon, pulse animation, spinner
- **Pending**: Gray icon, gray text

**Styling**:
- Container: `bg-gray-900 border border-gray-800`
- Complete: `bg-gray-800/50 border-gray-700`
- Current: `bg-primary-600/10 border-primary-600/50`
- Pending: `bg-gray-900 border-gray-800`

**Icons Used**:
- `Brain` (query routing)
- `Database` (ticker extraction)
- `TrendingUp` (market data)
- `FileText` (sentiment)
- `BarChart3` (analyst consensus)
- `CheckCircle2` (synthesis & completion)

---

### 4. ReportDisplay Component

**File**: `/frontend/src/components/ReportDisplay.tsx`

**Purpose**: Display comprehensive investment research report

**Visual Layout**:
```
┌──────────────────────────────────────────────┐
│  Research Query                              │
│  What is the investment outlook for MSFT?    │
│                                              │
│  [MSFT]  [AAPL]                              │
│                                              │
│  Jan 27, 2025 10:30 • ab12cd34               │
└──────────────────────────────────────────────┘

┌──────────┬──────────┬──────────┬──────────┐
│ Market   │ Sentiment│ Analyst  │ Context  │
│ ✓        │ ✓        │ ✓        │ ✓        │
└──────────┴──────────┴──────────┴──────────┘

┌──────────────────────────────────────────────┐
│  # Investment Analysis for Microsoft         │
│                                              │
│  ## Market Overview                          │
│  - Current Price: $420.50                    │
│  - Market Cap: $3.1T                         │
│                                              │
│  ## Recommendation                           │
│  **BUY** - Strong fundamentals...            │
│                                              │
│  (Full markdown report)                      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  Disclaimer: AI-generated, not advice        │
└──────────────────────────────────────────────┘
```

**Props**:
```typescript
interface ReportDisplayProps {
  report: ResearchQueryResponse;
}

interface ResearchQueryResponse {
  session_id: string;
  query: string;
  report: string;  // Markdown
  tickers: string[];
  market_data_available: boolean;
  sentiment_available: boolean;
  analyst_consensus_available: boolean;
  context_retrieved: boolean;
  timestamp: string;
}
```

**Features**:
- Query header with metadata
- Ticker badges (dynamic)
- Data availability indicators (4)
- Markdown report rendering
- Tables, lists, code blocks
- Disclaimer footer

**Markdown Support**:
- H1-H4 headers
- Bullet and numbered lists
- Tables with styling
- Bold, italic, code
- Blockquotes
- Horizontal rules

**Styling**:
- Header: `bg-gradient-to-r from-gray-900 to-gray-800`
- Ticker badges: `bg-primary-600/20 border-primary-600/50`
- Report: `bg-gray-900 border-gray-800`
- Available indicator: `bg-success-950/20 border-success-800/50`
- Unavailable: `bg-gray-900 border-gray-800`

**Icons Used**:
- `FileText` (query icon)
- `Calendar` (timestamp)
- `TrendingUp` (market data)
- `BarChart3` (analyst consensus)
- `Database` (context)
- `CheckCircle2` (available)
- `XCircle` (unavailable)

**Helper Functions**:
```typescript
formatDate(dateString: string): string
  // "Jan 27, 2025 10:30"
```

---

### 5. SessionSidebar Component

**File**: `/frontend/src/components/SessionSidebar.tsx`

**Purpose**: Navigation for session management

**Visual Layout**:
```
┌──────────────────────────────┐
│  [+] New Research Query      │
├──────────────────────────────┤
│  Recent Sessions (12)        │
│                              │
│  ┌────────────────────────┐ │
│  │ What is MSFT outlook? │ │
│  │ 2h ago • 4 msgs      →│ │
│  └────────────────────────┘ │
│                              │
│  ┌────────────────────────┐ │
│  │ Analyze Apple stock... │ │
│  │ Just now • 2 msgs    →│ │
│  └────────────────────────┘ │
│                              │
│  (more sessions...)          │
└──────────────────────────────┘
```

**Props**:
```typescript
interface SessionSidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
}
```

**Features**:
- New query button
- Session count badge
- Auto-refresh (10 seconds)
- Active session highlight
- Time ago display
- Message count
- Scrollable list

**States**:
- **Loading**: Spinner in center
- **Empty**: "No sessions yet" message
- **Error**: Red error message
- **Loaded**: Session list

**Session Item Display**:
- Query preview (truncated to 60 chars)
- Time ago: "Just now", "2m ago", "5h ago", "Jan 27"
- Message count: "4 msgs"
- Chevron icon (animates on hover)

**Styling**:
- Sidebar: `w-80 bg-gray-900 border-r border-gray-800`
- New button: `bg-primary-600 hover:bg-primary-700`
- Active session: `bg-primary-600/20 border-primary-600/50`
- Inactive: `bg-gray-800/50 hover:bg-gray-800`

**Icons Used**:
- `Plus` (new query button)
- `MessageSquare` (sessions header)
- `Clock` (timestamp)
- `ChevronRight` (navigation)
- `Loader2` (loading)

**React Query**:
```typescript
useQuery({
  queryKey: ['sessions'],
  queryFn: researchApi.getSessions,
  refetchInterval: 10000,
});
```

**Helper Functions**:
```typescript
formatDate(dateString: string): string
  // "Just now", "2m ago", "5h ago", "Jan 27"

truncateQuery(query: string, maxLength: 60): string
  // "What is the investment outlook fo..."
```

---

### 6. SessionHistory Component

**File**: `/frontend/src/components/SessionHistory.tsx`

**Purpose**: Display full conversation thread

**Visual Layout**:
```
┌──────────────────────────────────────────────┐
│  Session History • 4 messages                │
│  ab12cd34...                                 │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  [User] You                       10:30 AM   │
│  ┌────────────────────────────────────────┐ │
│  │ What is the outlook for Microsoft?     │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  [Bot] Research Assistant         10:30 AM   │
│  ┌────────────────────────────────────────┐ │
│  │ # Investment Analysis                  │ │
│  │                                        │ │
│  │ Microsoft shows strong fundamentals... │ │
│  │ (Markdown rendered)                    │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

**Props**:
```typescript
interface SessionHistoryProps {
  sessionId: string;
}
```

**Features**:
- Session header with ID
- Message count
- User/AI distinction
- Timestamps per message
- Markdown in AI responses
- Plain text for user queries

**States**:
- **Loading**: Spinner with "Loading history..."
- **Error**: Red error message with retry info
- **Empty**: "No messages" message
- **Loaded**: Message thread

**Message Display**:
- **User**: Blue gradient avatar, plain text
- **AI**: Gray gradient avatar, markdown rendering

**Styling**:
- Header: `bg-gray-900 border-gray-800`
- User avatar: `bg-gradient-to-br from-primary-600 to-primary-700`
- AI avatar: `bg-gradient-to-br from-gray-700 to-gray-800`
- Message bubble: `bg-gray-900 border-gray-800`

**Icons Used**:
- `User` (user avatar)
- `Bot` (AI avatar)
- `Loader2` (loading)
- `AlertCircle` (error)

**React Query**:
```typescript
useQuery({
  queryKey: ['session-history', sessionId],
  queryFn: () => researchApi.getSessionHistory(sessionId),
  enabled: !!sessionId,
});
```

**Helper Functions**:
```typescript
formatTime(dateString: string): string
  // "10:30 AM"
```

---

### 7. ErrorState Component

**File**: `/frontend/src/components/ErrorState.tsx`

**Purpose**: Graceful error handling with recovery

**Visual Layout**:
```
┌──────────────────────────────────────────────┐
│                                              │
│              [Alert Icon]                    │
│                                              │
│         Something went wrong                 │
│    Error message displayed here...           │
│                                              │
│        [Refresh] Try Again                   │
│                                              │
│  Troubleshooting:                            │
│  • Backend running at localhost:8000?        │
│  • Internet connection stable?               │
│  • Valid stock symbols?                      │
│                                              │
└──────────────────────────────────────────────┘
```

**Props**:
```typescript
interface ErrorStateProps {
  error: Error;
  onRetry?: () => void;
}
```

**Features**:
- Large alert icon
- Error message display
- Optional retry button
- Troubleshooting checklist
- Helpful guidance

**Error Types Handled**:
- Network errors (connection refused)
- API errors (4xx, 5xx)
- Timeout errors
- CORS errors

**Styling**:
- Container: `bg-danger-950/20 border-danger-800/50`
- Icon background: `bg-danger-600/10`
- Text: `text-danger-400`
- Retry button: `bg-danger-600 hover:bg-danger-700`

**Icons Used**:
- `AlertCircle` (main icon)
- `RefreshCw` (retry button)

---

### 8. EmptyState Component

**File**: `/frontend/src/components/EmptyState.tsx`

**Purpose**: Welcome screen with feature overview

**Visual Layout**:
```
┌──────────────────────────────────────────────┐
│                                              │
│             [Search Icon]                    │
│                                              │
│  Welcome to Investment Research System       │
│  Get comprehensive equity analysis powered   │
│  by multi-agent AI technology                │
│                                              │
│  ┌──────┬──────┬──────┬──────┐              │
│  │Market│Senti-│Analys│Valua-│              │
│  │ Data │ ment │ Views│ tion │              │
│  └──────┴──────┴──────┴──────┘              │
│                                              │
│  What you can ask:                           │
│  • Investment outlook for companies          │
│  • Performance analysis                      │
│  • Comparative analysis                      │
│  • Market trends                             │
│                                              │
│  Enter your research query above             │
└──────────────────────────────────────────────┘
```

**Props**: None

**Features**:
- Large search icon
- Welcome message
- 4 feature cards
- Usage examples
- Call to action

**Feature Cards**:
1. **Market Data**: Real-time prices & fundamentals
2. **Sentiment**: News & market sentiment
3. **Analyst Views**: Consensus & targets
4. **Valuation**: Peer comparison

**Styling**:
- Container: `bg-gray-900 border-gray-800`
- Icon background: `bg-primary-600/10`
- Feature cards: `bg-gray-800/50 border-gray-700`
- Examples box: `bg-gray-800/50 border-gray-700`

**Icons Used**:
- `Search` (main icon)
- `TrendingUp` (market data)
- `LineChart` (sentiment)
- `BarChart3` (analyst views)
- `PieChart` (valuation)

---

## Component Interaction Diagram

```
User Action Flow:

1. Page Load
   └→ EmptyState displays

2. User types query
   └→ QueryInput accepts input
       └→ Character counter updates

3. User clicks Submit
   └→ QueryInput calls onSubmit()
       └→ App.tsx: submitQueryMutation.mutate()
           └→ LoadingState displays
               └→ Progress steps animate

4. Backend responds (15-20s)
   └→ App.tsx: onSuccess handler
       └→ ReportDisplay shows
           └→ SessionSidebar refreshes

5. User clicks session
   └→ SessionSidebar calls onSessionSelect()
       └→ App.tsx: switches to history mode
           └→ SessionHistory displays

6. Error occurs
   └→ ErrorState displays
       └→ User clicks retry
           └→ Back to step 3
```

## Component Dependencies

```
App.tsx (Main)
├── React Query (data fetching)
├── API Client (axios)
└── All child components

Header
└── Lucide icons

QueryInput
├── useState (local state)
└── Lucide icons

LoadingState
├── useEffect (timing)
├── useState (progress)
└── Lucide icons

ReportDisplay
├── React Markdown
├── remark-gfm
└── Lucide icons

SessionSidebar
├── React Query (sessions)
└── Lucide icons

SessionHistory
├── React Query (history)
├── React Markdown
└── Lucide icons

ErrorState
└── Lucide icons

EmptyState
└── Lucide icons
```

## Styling Patterns

### Color Usage
```typescript
// Backgrounds
bg-gray-950  // Body background
bg-gray-900  // Card backgrounds
bg-gray-800  // Hover states

// Borders
border-gray-800  // Primary borders
border-gray-700  // Secondary borders

// Text
text-white       // Headers
text-gray-100    // Primary text
text-gray-300    // Secondary text
text-gray-500    // Metadata

// Accents
bg-primary-600   // Primary actions
bg-success-500   // Positive indicators
bg-danger-500    // Errors
```

### Common Patterns
```typescript
// Card
bg-gray-900 border border-gray-800 rounded-lg p-6

// Button
bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-6 rounded-lg transition-all

// Input
bg-gray-900 border border-gray-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-primary-600

// Badge
bg-primary-600/20 border border-primary-600/50 text-primary-400 rounded-full px-3 py-1
```

## Summary

8 professional components totaling ~8,000 lines of code:

1. **Header**: Branding and navigation
2. **QueryInput**: Query submission
3. **LoadingState**: Progress visualization
4. **ReportDisplay**: Report rendering
5. **SessionSidebar**: Session navigation
6. **SessionHistory**: Conversation view
7. **ErrorState**: Error handling
8. **EmptyState**: Welcome screen

All components follow:
- TypeScript for type safety
- Tailwind for consistent styling
- Lucide for modern icons
- React best practices
- Accessibility standards

Each component is modular, reusable, and fully documented.
