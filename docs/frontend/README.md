# Investment Research System - Frontend

Professional React-based frontend for the Multi-Agent Investment Research System.

## Features

- Comprehensive equity analysis interface
- Real-time market data visualization
- Session management and history
- Professional investment-grade dark theme
- Responsive design for all devices
- AI-powered research report generation
- Multi-source data aggregation display

## Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and builds
- **Tailwind CSS** for styling
- **React Query** for data fetching and caching
- **React Markdown** for report rendering
- **Lucide React** for icons
- **Axios** for API communication

## Prerequisites

- Node.js 18+ and npm
- Backend API running at http://localhost:8000

## Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Ensure backend is running:
```bash
# In the project root
uvicorn backend.main:app --reload --port 8000
```

## Development

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Build for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

## Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   │   └── client.ts
│   ├── components/       # React components
│   │   ├── Header.tsx
│   │   ├── QueryInput.tsx
│   │   ├── LoadingState.tsx
│   │   ├── ReportDisplay.tsx
│   │   ├── SessionSidebar.tsx
│   │   ├── SessionHistory.tsx
│   │   ├── ErrorState.tsx
│   │   └── EmptyState.tsx
│   ├── types/           # TypeScript interfaces
│   │   └── index.ts
│   ├── App.tsx          # Main application component
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Usage Guide

### Submitting Research Queries

1. Enter your investment research question in the text area
2. Click "Submit Research Query" or press Enter
3. Wait 15-20 seconds for the AI agents to analyze
4. Review the comprehensive report with market data, sentiment, and analyst insights

### Example Queries

- "What is the investment outlook for Microsoft?"
- "Analyze Apple's recent performance and valuation"
- "Compare Tesla and traditional automakers"
- "Should I invest in NVIDIA stock?"

### Session Management

- All queries are automatically saved in sessions
- Click any session in the sidebar to view its history
- Click "New Research Query" to start a fresh session
- Sessions persist across page refreshes (stored in MongoDB)

### Report Features

The generated reports include:

- **Market Data**: Real-time prices, fundamentals, 52-week trends
- **Sentiment Analysis**: News sentiment and market mood
- **Analyst Consensus**: Price targets, recommendations, upside/downside
- **Peer Valuation**: Comparison with sector peers
- **Context**: Historical data from SEC filings

### Data Availability Indicators

Each report shows which data sources were successfully retrieved:
- Green checkmark: Data available
- Gray X: Data unavailable or not applicable

## API Integration

The frontend communicates with the backend through three main endpoints:

1. **POST /api/research/query** - Submit research queries
2. **GET /api/research/history/{session_id}** - Retrieve session history
3. **GET /api/research/sessions** - List all sessions

CORS is handled via Vite proxy configuration.

## Customization

### Theme Colors

Edit `tailwind.config.js` to customize colors:

```js
colors: {
  primary: { ... },  // Accent color
  success: { ... },  // Positive indicators
  danger: { ... },   // Error states
}
```

### API Endpoint

To change the backend URL, edit `vite.config.ts`:

```ts
proxy: {
  '/api': {
    target: 'http://your-backend-url:port',
    changeOrigin: true,
  },
}
```

## Troubleshooting

### Backend Connection Issues

If you see connection errors:
1. Verify backend is running: `curl http://localhost:8000/api/research/sessions`
2. Check browser console for CORS errors
3. Ensure Vite proxy is configured correctly

### Slow Report Generation

Report generation takes 15-20 seconds due to:
- Real-time data fetching from multiple sources
- AI agent processing and synthesis
- News sentiment analysis

This is normal behavior.

### Session Not Loading

If sessions don't appear:
1. Check MongoDB connection in backend
2. Verify backend logs for errors
3. Clear browser cache and reload

## Performance Considerations

- React Query caches API responses for 5 minutes
- Sessions list refreshes every 10 seconds
- Large reports are rendered incrementally
- Images and external resources are lazy-loaded

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Modern mobile browsers

## License

Part of the Multi-Agent Investment Research System project.

## Disclaimer

This application generates AI-powered research reports and should not be considered financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.
