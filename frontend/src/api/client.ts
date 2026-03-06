import axios from 'axios';
import type { AnalysisRequest, AnalysisResponse } from '../types';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function submitAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
  const response = await apiClient.post<AnalysisResponse>('/research/analyze', request);
  return response.data;
}

export default apiClient;
