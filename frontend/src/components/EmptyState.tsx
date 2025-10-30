import { Search, TrendingUp, LineChart, BarChart3 } from 'lucide-react';

export default function EmptyState() {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-12">
      <div className="max-w-2xl mx-auto text-center space-y-8">
        <div className="inline-flex p-6 bg-primary-600/10 rounded-full">
          <Search className="w-16 h-16 text-primary-500" />
        </div>

        <div className="space-y-3">
          <h3 className="text-2xl font-bold text-white">
            Welcome to the Investment Research System
          </h3>
          <p className="text-gray-400 text-lg">
            Get comprehensive equity analysis powered by multi-agent AI technology
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
          <FeatureCard
            icon={TrendingUp}
            title="Market Data"
            description="Real-time prices & fundamentals"
          />
          <FeatureCard
            icon={LineChart}
            title="Sentiment"
            description="News & market sentiment"
          />
          <FeatureCard
            icon={BarChart3}
            title="Analyst Views"
            description="Consensus & targets"
          />
        </div>

        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 text-left">
          <h4 className="text-sm font-semibold text-gray-300 mb-3">What you can ask:</h4>
          <ul className="space-y-2 text-sm text-gray-400">
            <li className="flex items-start space-x-2">
              <span className="text-primary-500 font-bold">•</span>
              <span>Investment outlook for specific companies (e.g., "What is the investment outlook for Microsoft?")</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-primary-500 font-bold">•</span>
              <span>Performance analysis and valuation metrics</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-primary-500 font-bold">•</span>
              <span>Market trends and analyst consensus views</span>
            </li>
          </ul>
        </div>

        <div className="text-sm text-gray-500">
          Enter your research query above to get started
        </div>
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
}

function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-2">
      <Icon className="w-8 h-8 text-primary-500 mx-auto" />
      <h5 className="text-sm font-semibold text-white">{title}</h5>
      <p className="text-xs text-gray-400">{description}</p>
    </div>
  );
}
