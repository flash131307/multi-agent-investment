import { Search, TrendingUp, Newspaper, FileText } from 'lucide-react';

export default function EmptyState() {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-12">
      <div className="max-w-2xl mx-auto text-center space-y-8">
        <div className="inline-flex p-6 bg-primary-600/10 rounded-full">
          <Search className="w-16 h-16 text-primary-500" />
        </div>

        <div className="space-y-3">
          <h3 className="text-2xl font-bold text-white">
            Multi-Agent Investment Analysis
          </h3>
          <p className="text-gray-400 text-lg">
            Enter a stock ticker to get a fused signal from three specialized AI agents
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
          <FeatureCard
            icon={TrendingUp}
            title="Technical Agent"
            description="ReAct loop with RSI, MACD, Bollinger, volume & pattern tools"
          />
          <FeatureCard
            icon={Newspaper}
            title="Sentiment Agent"
            description="FinBERT three-layer funnel on Finnhub news"
          />
          <FeatureCard
            icon={FileText}
            title="Fundamental Agent"
            description="Plan-and-Solve with SEC 10-K RAG retrieval"
          />
        </div>

        <div className="text-sm text-gray-500">
          Enter a ticker above to get started
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
