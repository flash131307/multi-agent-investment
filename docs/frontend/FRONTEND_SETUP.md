# Frontend Setup and Launch Guide

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/mayuhao/PythonProject/PythonProject/frontend
npm install
```

This will install all required packages:
- React 18 and React DOM
- TypeScript and build tools
- Tailwind CSS for styling
- React Query for data fetching
- Axios for API calls
- React Markdown for report rendering
- Lucide React for icons

### 2. Start Backend API

Before starting the frontend, ensure your backend is running:

```bash
# In a separate terminal, from project root
cd /Users/mayuhao/PythonProject/PythonProject
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

Verify backend is running:
```bash
curl http://localhost:8000/api/research/sessions
```

### 3. Start Frontend Development Server

```bash
cd /Users/mayuhao/PythonProject/PythonProject/frontend
npm run dev
```

The application will start at: **http://localhost:3000**

## What You'll See

### Initial Screen
- Professional dark-themed interface
- Session sidebar on the left (empty initially)
- Main content area with:
  - Query input form
  - Example queries
  - Empty state with feature overview

### After Submitting a Query

1. **Loading State (15-20 seconds)**
   - Animated progress indicators
   - Step-by-step analysis visualization
   - Shows which agents are working

2. **Report Display**
   - Query header with ticker badges
   - Data availability indicators (market data, sentiment, analyst consensus, context)
   - Full markdown-formatted research report
   - Professional tables and formatting
   - Timestamp and session ID

3. **Session Sidebar Updates**
   - New session appears in sidebar
   - Shows query preview and timestamp
   - Click to view full history

## Usage Examples

### Example 1: Microsoft Analysis
```
Query: "What is the investment outlook for Microsoft?"

Expected Response:
- Ticker: MSFT
- Market data: Current price, market cap, fundamentals
- 52-week trend analysis
- Analyst consensus and price targets
- Sentiment from recent news
- Peer valuation comparison
- Investment recommendation
```

### Example 2: Multi-Company Comparison
```
Query: "Compare Tesla and Ford stock performance"

Expected Response:
- Tickers: TSLA, F
- Comparative market metrics
- Valuation multiples comparison
- Growth analysis
- Risk assessment
```

## Features Walkthrough

### 1. Query Submission
- Large textarea for detailed questions
- Character counter
- Submit button with loading state
- 4 example queries for quick start

### 2. Loading Experience
- 6-step progress indicator
- Real-time status updates
- Educational tooltips
- Professional animations

### 3. Report Rendering
- **Markdown support**: Headers, lists, tables, emphasis
- **Syntax highlighting**: Code blocks and inline code
- **Data badges**: Visual indicators for tickers
- **Availability badges**: Shows which data sources returned results
- **Tables**: Styled for financial data presentation

### 4. Session Management
- **Automatic saving**: Every query creates/updates a session
- **Sidebar list**: All sessions with timestamps
- **Click to view**: Load full conversation history
- **New session**: Start fresh queries

### 5. History View
- User/Assistant message bubbles
- Timestamp for each message
- Full markdown rendering in responses
- Scrollable conversation thread

## API Integration Details

### Endpoints Used

1. **POST /api/research/query**
   ```json
   Request: {
     "query": "Your research question",
     "session_id": "optional-existing-session-id"
   }

   Response: {
     "session_id": "uuid",
     "query": "Your question",
     "report": "Full markdown report",
     "tickers": ["MSFT", "AAPL"],
     "market_data_available": true,
     "sentiment_available": true,
     "analyst_consensus_available": true,
     "context_retrieved": true,
     "timestamp": "2025-01-27T10:30:00Z"
   }
   ```

2. **GET /api/research/history/{session_id}**
   - Returns full conversation history
   - Shows all user queries and AI responses
   - Includes timestamps

3. **GET /api/research/sessions**
   - Lists all sessions (sorted by recency)
   - Shows message count per session
   - Includes first query as preview

### CORS Proxy
Vite automatically proxies `/api/*` requests to `http://localhost:8000`

## Architecture Highlights

### Component Structure
```
App.tsx (State Management)
├── Header (Branding)
├── SessionSidebar (Navigation)
│   └── React Query: Sessions List
└── Main Content
    ├── QueryInput (Form)
    ├── LoadingState (Progress)
    ├── ReportDisplay (Results)
    │   └── React Markdown
    ├── SessionHistory (Messages)
    │   └── React Query: History
    ├── ErrorState (Failures)
    └── EmptyState (Welcome)
```

### State Management
- **React Query**: Server state (sessions, history)
- **Local State**: Current session, view mode, active report
- **Mutations**: Query submission with optimistic updates

### Styling Approach
- **Tailwind Utility Classes**: All styling
- **Custom CSS**: Markdown content styling
- **Color System**: Primary (blue), Success (green), Danger (red)
- **Dark Theme**: Gray-950 background, professional gradients

## Development Tips

### Hot Reload
Vite provides instant hot module replacement:
- Edit any `.tsx` file
- Changes appear immediately
- State is preserved when possible

### Component Editing
To modify components:
1. Edit files in `/Users/mayuhao/PythonProject/PythonProject/frontend/src/components/`
2. Save changes
3. Browser auto-refreshes

### Styling Changes
Edit `tailwind.config.js` for:
- Color scheme changes
- Font customization
- Breakpoint adjustments

### API Client
Edit `src/api/client.ts` to:
- Add new endpoints
- Change base URL
- Modify request headers

## Build for Production

### Create Optimized Build
```bash
npm run build
```

Output: `/Users/mayuhao/PythonProject/PythonProject/frontend/dist/`

### Preview Production Build
```bash
npm run preview
```

Serves production build at http://localhost:4173

### Deploy
The `dist/` folder contains static files ready for deployment to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting service

## Troubleshooting

### Problem: "Cannot GET /api/research/sessions"
**Solution**: Backend not running. Start with:
```bash
uvicorn backend.main:app --reload --port 8000
```

### Problem: Reports taking too long
**Normal**: Analysis takes 15-20 seconds
**Check**: Backend logs for errors
**Verify**: All data sources are accessible (Yahoo Finance, news APIs)

### Problem: Sessions not appearing
**Check**: MongoDB connection in backend
**Verify**: `backend.main:app` is running without errors
**Debug**: Check browser DevTools Network tab

### Problem: Styling looks broken
**Solution**: Rebuild Tailwind:
```bash
npm run dev
# Or for production:
npm run build
```

### Problem: TypeScript errors
**Solution**: Ensure types are correct:
```bash
npm run build
# Check for type errors
```

## Performance Optimization

### Already Implemented
- React Query caching (5 min stale time)
- Automatic session list refresh (10 sec)
- Lazy loading for markdown rendering
- Optimized re-renders with proper React patterns

### Future Enhancements
- Virtual scrolling for long session lists
- Pagination for history messages
- Service worker for offline support
- Image optimization and lazy loading

## Browser DevTools

### Useful Panels
1. **Network Tab**: Monitor API calls
2. **Console**: View React Query cache
3. **React DevTools**: Inspect component tree
4. **Performance**: Profile rendering

### React Query DevTools
Add to `App.tsx` for debugging:
```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

// In App component:
<ReactQueryDevtools initialIsOpen={false} />
```

## File Reference

### Configuration Files
- `package.json` - Dependencies and scripts
- `vite.config.ts` - Build configuration and proxy
- `tsconfig.json` - TypeScript settings
- `tailwind.config.js` - Styling theme
- `postcss.config.js` - CSS processing

### Source Files
- `src/main.tsx` - App entry point
- `src/App.tsx` - Main application logic
- `src/index.css` - Global styles
- `src/api/client.ts` - API integration
- `src/types/index.ts` - TypeScript interfaces

### Component Files
All in `src/components/`:
- `Header.tsx` - Top navigation bar
- `QueryInput.tsx` - Research query form
- `LoadingState.tsx` - Analysis progress
- `ReportDisplay.tsx` - Research report viewer
- `SessionSidebar.tsx` - Session navigation
- `SessionHistory.tsx` - Conversation viewer
- `ErrorState.tsx` - Error handling
- `EmptyState.tsx` - Welcome screen

## Next Steps

1. **Start Development**: Run `npm run dev` and begin testing
2. **Submit Queries**: Try the example queries
3. **Review Reports**: Check report formatting and data
4. **Test Sessions**: Create multiple sessions, switch between them
5. **Customize**: Adjust colors, fonts, or layout as needed

## Support

For issues:
1. Check backend logs: `uvicorn backend.main:app --reload --port 8000`
2. Check browser console for errors
3. Verify API responses in Network tab
4. Review component state in React DevTools

## Summary

You now have a fully functional investment research frontend with:
- Professional dark theme
- Real-time data visualization
- Session management
- Comprehensive report rendering
- Responsive design
- Error handling
- Loading states

Access at: **http://localhost:3000** after running `npm run dev`
