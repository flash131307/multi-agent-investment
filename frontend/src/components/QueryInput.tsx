import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const EXAMPLE_QUERIES = [
  "What is the investment outlook for Microsoft?",
  "Analyze Apple's recent performance and valuation",
  "Compare Tesla and traditional automakers",
  "Should I invest in NVIDIA stock?",
];

export default function QueryInput({ onSubmit, isLoading }: QueryInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  const handleExampleClick = (example: string) => {
    if (!isLoading) {
      setQuery(example);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about any stock or company... (e.g., 'What is the investment outlook for Microsoft?')"
            className="w-full h-32 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none transition-all"
            disabled={isLoading}
          />
          {query.length > 0 && (
            <div className="absolute bottom-3 right-3 text-xs text-gray-500">
              {query.length} characters
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="w-full bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 disabled:from-gray-700 disabled:to-gray-800 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg shadow-primary-900/50 disabled:shadow-none"
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Generating Research Report...</span>
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              <span>Submit Research Query</span>
            </>
          )}
        </button>
      </form>

      {!isLoading && (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-gray-400 text-sm">
            <Sparkles className="w-4 h-4" />
            <span>Example queries:</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {EXAMPLE_QUERIES.map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="text-left text-sm px-4 py-2 bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-primary-700 rounded-lg text-gray-300 hover:text-primary-400 transition-all duration-200"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
