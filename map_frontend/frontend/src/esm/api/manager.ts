import type { Manager } from '@esm/types/domain';
import { mockManagers } from './mocks/manager';
import { http } from './request';

const USE_MOCK = true;

export const managerRatings = ['全部', 'A', 'B', 'C', 'D'];

export async function fetchManagers(): Promise<Manager[]> {
  if (USE_MOCK) return Promise.resolve(mockManagers);
  const { data } = await http.get('/managers');
  return data;
}

