import type { SPV } from '@esm/types/domain';
import { mockSPVs } from './mocks/spv';
import { http } from './request';

const USE_MOCK = true;

export async function fetchSPVs(): Promise<SPV[]> {
  if (USE_MOCK) return Promise.resolve(mockSPVs);
  const { data } = await http.get('/spvs');
  return data;
}

export async function fetchSPVByCode(code: string): Promise<SPV | undefined> {
  if (USE_MOCK) return Promise.resolve(mockSPVs.find(s => s.code === code));
  const { data } = await http.get(`/spvs/${code}`);
  return data;
}

export const spvStrategyTags: string[] = ['全部', '固收增强含权', '固收增强', '量化策略', '权益策略', '另类策略', '海外策略'];
export const spvStatuses: string[] = ['全部', '在投', '待审批', '冻结', '已退出'];
export const spvRiskLevels: string[] = ['全部', '低', '中', '高'];

