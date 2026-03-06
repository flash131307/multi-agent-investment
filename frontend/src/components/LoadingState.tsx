import { TrendingUp, Newspaper, FileText, Brain, CheckCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';

const ANALYSIS_STEPS = [
  { icon: Brain, label: 'Resolving ticker and initializing agents', duration: 1000 },
  { icon: TrendingUp, label: 'Technical Agent: Running indicator tools (RSI, MACD, Bollinger...)', duration: 4000 },
  { icon: Newspaper, label: 'Sentiment Agent: FinBERT analyzing news articles', duration: 6000 },
  { icon: FileText, label: 'Fundamental Agent: RAG search on SEC filings', duration: 10000 },
  { icon: Brain, label: 'Decision Hub: Fusing signals and computing recommendation', duration: 14000 },
];

export default function LoadingState() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const startTime = Date.now();

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const step = ANALYSIS_STEPS.findIndex((_, index) => {
        return index === ANALYSIS_STEPS.length - 1 || elapsed < ANALYSIS_STEPS[index + 1].duration;
      });
      setCurrentStep(Math.max(0, step));
    }, 500);

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
          <p className="text-gray-400">Three agents running in parallel via asyncio.gather</p>
        </div>

        <div className="space-y-3">
          {ANALYSIS_STEPS.map((step, index) => {
            const Icon = step.icon;
            const isComplete = index < currentStep;
            const isCurrent = index === currentStep;

            return (
              <div
                key={index}
                className={`flex items-center space-x-4 p-3 rounded-lg transition-all duration-500 ${
                  isCurrent ? 'bg-primary-600/10 border border-primary-600/50' :
                  isComplete ? 'bg-gray-800/50 border border-gray-700' :
                  'bg-gray-900 border border-gray-800'
                }`}
              >
                <div className={isCurrent ? 'animate-pulse' : ''}>
                  <Icon className={`w-5 h-5 ${
                    isComplete ? 'text-success-500' :
                    isCurrent ? 'text-primary-500' :
                    'text-gray-600'
                  }`} />
                </div>
                <p className={`text-sm font-medium flex-1 ${
                  isComplete ? 'text-gray-400' :
                  isCurrent ? 'text-white' :
                  'text-gray-600'
                }`}>
                  {step.label}
                </p>
                {isComplete && <CheckCircle2 className="w-4 h-4 text-success-500" />}
                {isCurrent && (
                  <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
