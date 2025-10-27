import axios from 'axios';
import type {
  ResearchQueryRequest,
  ResearchQueryResponse,
  SessionHistoryResponse,
  SessionsResponse,
} from '../types';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const researchApi = {
  submitQuery: async (data: ResearchQueryRequest): Promise<ResearchQueryResponse> => {
    const response = await apiClient.post<ResearchQueryResponse>('/research/query', data);
    return response.data;
  },

  getSessionHistory: async (sessionId: string): Promise<SessionHistoryResponse> => {
    const response = await apiClient.get<SessionHistoryResponse>(`/research/history/${sessionId}`);
    return response.data;
  },

  getSessions: async (): Promise<SessionsResponse> => {
    const response = await apiClient.get<SessionsResponse>('/research/sessions');
    return response.data;
  },
};

export default apiClient;
