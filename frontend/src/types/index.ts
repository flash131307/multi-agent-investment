export interface ResearchQueryRequest {
  query: string;
  session_id?: string;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PeerComparison {
  ticker: string;
  name: string;
  pe_ratio: number | null;
  pb_ratio: number | null;
  ps_ratio: number | null;
  is_main: boolean;
}

export interface VisualizationData {
  ticker: string;
  price_history: PricePoint[];
  week_52_high: number | null;
  week_52_low: number | null;
  current_price: number | null;
  current_position_pct: number | null;
  peer_comparison: PeerComparison[];
  period_high: number | null;
  period_low: number | null;
  average_volume: number | null;
}

export interface InvestorSnapshot {
  ticker: string;
  current_price: number | null;
  price_change_pct: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  investment_rating: 'strong_buy' | 'buy' | 'hold' | 'sell' | 'strong_sell';
  rating_explanation: string;
  key_highlights: string[];
  risk_warnings: string[];
}

export interface ReportMetadata {
  executed_agents: string[];  // Which agents executed
  data_sources: Record<string, boolean>;  // Which data sources have data
  intent: string;  // Query intent
  tickers: string[];  // Tickers analyzed
  report_template: string;  // Which template was used
}

export interface ResearchQueryResponse {
  session_id: string;
  query: string;
  report: string;
  tickers: string[];
  executed_agents: string[];  // List of agents that were executed
  agent_errors: Record<string, string>;  // Per-agent error messages
  intent?: string;  // Detected query intent
  routing_flags?: {  // Router's flag decisions
    market_data: boolean;
    sentiment: boolean;
    context: boolean;
  };
  market_data_available: boolean;
  sentiment_available: boolean;
  analyst_consensus_available: boolean;
  context_retrieved: number;
  deep_analysis_available: boolean;  // Whether deep analysis (SEC 10-K) is available
  can_request_deep_analysis: boolean;  // Whether user can request deep analysis
  visualization_data: VisualizationData[];
  snapshot: InvestorSnapshot | null;
  report_metadata: ReportMetadata | null;  // Report generation metadata
  timestamp: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: Message[];
  message_count: number;
}

export interface SessionSummary {
  session_id: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  first_query: string | null;
}

export interface SessionsResponse {
  sessions: SessionSummary[];
  total_count: number;
}

export interface DataAvailability {
  market_data: boolean;
  sentiment: boolean;
  analyst_consensus: boolean;
  context_retrieved: number;
}
