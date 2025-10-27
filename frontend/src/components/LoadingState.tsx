import { Brain, Database, TrendingUp, FileText, BarChart3, CheckCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';

const ANALYSIS_STEPS = [
  { icon: Brain, label: 'Router Agent: Analyzing query & extracting tickers', duration: 2000 },
  { icon: Database, label: 'Parallel Execution: Market Data, Sentiment, Analyst Consensus, RAG Retrieval', duration: 4000, isParallel: true },
  { icon: TrendingUp, label: 'Agents running in parallel...', duration: 8000, isParallel: true },
  { icon: BarChart3, label: 'Aggregating results from all agents', duration: 12000 },
  { icon: CheckCircle2, label: 'Report Agent: Synthesizing comprehensive analysis', duration: 15000 },
];

export default function LoadingState() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const checkStep = () => {
      const elapsed = Date.now() - startTime;
      const newStep = ANALYSIS_STEPS.findIndex((step, index) => {
        return index === ANALYSIS_STEPS.length - 1 || elapsed < ANALYSIS_STEPS[index + 1].duration;
      });
      setCurrentStep(Math.max(0, newStep));
    };

    const startTime = Date.now();
    const interval = setInterval(checkStep, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-8">
      <div className="max-w-2xl mx-auto space-y-8">
        <div className="text-center space-y-3">
          <div className="inline-flex p-4 bg-primary-600/10 rounded-full">
            <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h3 className="text-xl font-semibold text-white">Analyzing Investment Opportunity</h3>
          <p className="text-gray-400">Multi-agent system running in parallel across multiple data sources</p>
        </div>

        <div className="space-y-4">
          {ANALYSIS_STEPS.map((step, index) => {
            const Icon = step.icon;
            const isComplete = index < currentStep;
            const isCurrent = index === currentStep;
            const isPending = index > currentStep;

            return (
              <div
                key={index}
                className={`flex items-center space-x-4 p-4 rounded-lg transition-all duration-500 ${
                  isCurrent ? 'bg-primary-600/10 border border-primary-600/50' :
                  isComplete ? 'bg-gray-800/50 border border-gray-700' :
                  'bg-gray-900 border border-gray-800'
                }`}
              >
                <div className={`flex-shrink-0 ${
                  isCurrent ? 'animate-pulse' : ''
                }`}>
                  <Icon className={`w-6 h-6 ${
                    isComplete ? 'text-success-500' :
                    isCurrent ? 'text-primary-500' :
                    'text-gray-600'
                  }`} />
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-medium ${
                    isComplete ? 'text-gray-400' :
                    isCurrent ? 'text-white' :
                    'text-gray-600'
                  }`}>
                    {step.label}
                  </p>
                </div>
                {isComplete && (
                  <CheckCircle2 className="w-5 h-5 text-success-500 flex-shrink-0" />
                )}
                {isCurrent && (
                  <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
                )}
              </div>
            );
          })}
        </div>

        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 mt-0.5">
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
            </div>
            <div className="text-sm text-gray-400">
              <p className="font-medium text-gray-300 mb-1">Parallel Processing</p>
              <p>Multiple agents execute simultaneously to gather market data, sentiment, analyst consensus, and SEC filings. Typically completes in 15-20 seconds.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
