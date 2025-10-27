# Quick Start Guide

## Installation (One Time)

```bash
cd /Users/mayuhao/PythonProject/PythonProject/frontend
npm install
```

## Running the Application

### Terminal 1: Backend
```bash
cd /Users/mayuhao/PythonProject/PythonProject
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd /Users/mayuhao/PythonProject/PythonProject/frontend
npm run dev
```

### Access
Open browser: **http://localhost:3000**

## First Test Query

Try this in the query input:
```
What is the investment outlook for Microsoft?
```

Wait 15-20 seconds for the AI analysis to complete.

## Common Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Check code quality |

## Project Structure

```
frontend/
├── src/
│   ├── components/    # UI components
│   ├── api/          # Backend integration
│   ├── types/        # TypeScript definitions
│   ├── App.tsx       # Main app
│   └── main.tsx      # Entry point
├── package.json      # Dependencies
└── vite.config.ts    # Configuration
```

## Key Features

1. **Submit Queries**: Type questions about stocks
2. **View Reports**: Comprehensive AI-generated analysis
3. **Session History**: All queries saved automatically
4. **Switch Sessions**: Click sessions in sidebar

## Configuration

### API Endpoint
Default: `http://localhost:8000`
Change in: `vite.config.ts` → `server.proxy`

### Port
Default: `3000`
Change in: `vite.config.ts` → `server.port`

### Theme Colors
Edit: `tailwind.config.js` → `theme.extend.colors`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend connection fails | Verify backend running on port 8000 |
| Sessions not loading | Check MongoDB connection |
| Slow report generation | Normal (15-20 seconds) |
| Styles broken | Run `npm run dev` |

## API Endpoints Used

- POST `/api/research/query` - Submit research questions
- GET `/api/research/history/{id}` - Load conversation history
- GET `/api/research/sessions` - List all sessions

## Development Tips

1. **Hot Reload**: Changes auto-refresh
2. **React DevTools**: Install browser extension
3. **Console Logs**: Check for errors
4. **Network Tab**: Monitor API calls

## Production Build

```bash
# Build
npm run build

# Output: dist/ folder

# Deploy to static hosting:
# - Vercel: vercel deploy
# - Netlify: netlify deploy
# - S3: aws s3 sync dist/ s3://bucket
```

## Need Help?

See detailed guides:
- `/Users/mayuhao/PythonProject/PythonProject/FRONTEND_SETUP.md`
- `/Users/mayuhao/PythonProject/PythonProject/FRONTEND_GUIDE.md`
- `frontend/README.md`

## Example Queries

Try these:
- "What is the investment outlook for Microsoft?"
- "Analyze Apple's recent performance"
- "Compare Tesla and Ford"
- "Should I invest in NVIDIA?"

## Next Steps

1. Run `npm run dev`
2. Open http://localhost:3000
3. Submit a test query
4. Explore the interface
5. Review the generated report
6. Check session history

That's it! Enjoy your investment research platform.
