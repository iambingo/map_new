import type { RiskEvent } from '@esm/types/domain';
import { mockRiskEvents } from './mocks/risk';
import { http } from './request';

const USE_MOCK = true;

export const riskLevels = ['全部', '高', '中', '低'];

export async function fetchRiskEvents(): Promise<RiskEvent[]> {
  if (USE_MOCK) return Promise.resolve(mockRiskEvents);
  const { data } = await http.get('/risk-events');
  return data;
}

