import type { CommitteeItem } from '@esm/types/domain';
import { mockCommitteeItems } from './mocks/committee';
import { http } from './request';

const USE_MOCK = true;

export async function fetchCommitteeItems(): Promise<CommitteeItem[]> {
  if (USE_MOCK) return Promise.resolve(mockCommitteeItems);
  const { data } = await http.get('/committee');
  return data;
}

