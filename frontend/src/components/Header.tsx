import { TrendingUp, BarChart3 } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="absolute inset-0 bg-primary-600 blur-lg opacity-50"></div>
              <div className="relative bg-gradient-to-br from-primary-600 to-primary-700 p-2 rounded-lg">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Investment Research System</h1>
              <p className="text-xs text-gray-400">Multi-Agent Equity Analysis Platform</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-gray-400">
            <BarChart3 className="w-5 h-5" />
            <span className="text-sm font-medium">AI-Powered Analysis</span>
          </div>
        </div>
      </div>
    </header>
  );
}
