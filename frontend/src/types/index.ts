// Enums matching backend models
export type Direction = 'BUY' | 'NEUTRAL' | 'SELL';
export type Strength = 'STRONG' | 'MODERATE' | 'WEAK';
export type RiskMode = 'NORMAL' | 'CAUTIOUS' | 'RISK';

// Per-agent signal (nullable fields if agent failed)
export interface AgentSignalResponse {
  agent_name: string;
  direction: Direction | null;
  strength: Strength | null;
  confidence: number | null;
  reasoning: string | null;
  error: string | null;
}

// Decision Hub output
export interface DecisionResponse {
  direction: Direction;
  confidence: number;
  risk_mode: RiskMode;
  consistency_score: number;
  aggregated_score: number;
  reasoning: string;
}

// Full API response from POST /api/research/analyze
export interface AnalysisResponse {
  ticker: string;
  decision: DecisionResponse;
  agents: AgentSignalResponse[];
  warnings: string[];
}

// Request body
export interface AnalysisRequest {
  ticker: string;
}

// Error response
export interface ErrorResponse {
  error: string;
  detail?: string;
}
