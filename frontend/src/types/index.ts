export interface ResearchQueryRequest {
  query: string;
  session_id?: string;
}

export interface ResearchQueryResponse {
  session_id: string;
  query: string;
  report: string;
  tickers: string[];
  market_data_available: boolean;
  sentiment_available: boolean;
  analyst_consensus_available: boolean;
  context_retrieved: number;
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
