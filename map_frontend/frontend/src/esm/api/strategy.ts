import type { Strategy, StrategyFilter, RatingRule, StrategyRating } from '@esm/types/domain';
import { mockStrategies, ratingRules } from './mocks/strategy';
import { http } from './request';

const USE_MOCK = true;

function applyFilter(data: Strategy[], filter: StrategyFilter): Strategy[] {
  return data.filter(item =>
    (filter.category === '全部' || !filter.category || item.primaryClass === filter.category)
    && (filter.status === '全部' || !filter.status || item.status === filter.status)
    && (!filter.createdMonth || item.createdAt.startsWith(filter.createdMonth))
    && (!filter.searchQuery || Object.values(item).join('').includes(filter.searchQuery)),
  );
}

export async function fetchStrategies(filter?: StrategyFilter): Promise<Strategy[]> {
  if (USE_MOCK) {
    return Promise.resolve(filter ? applyFilter(mockStrategies, filter) : mockStrategies);
  }
  const { data } = await http.get('/strategies', { params: filter });
  return data;
}

export async function fetchStrategyById(id: string): Promise<Strategy | undefined> {
  if (USE_MOCK) {
    return Promise.resolve(mockStrategies.find(s => s.id === id));
  }
  const { data } = await http.get(`/strategies/${id}`);
  return data;
}

export async function updateAdmissionCheck(strategyId: string, stageIdx: number, checkIdx: number, status: string, result?: string): Promise<void> {
  if (USE_MOCK) {
    const strategy = mockStrategies.find(s => s.id === strategyId);
    if (strategy) {
      strategy.admission[stageIdx].checks[checkIdx].status = status as any;
      if (result) strategy.admission[stageIdx].checks[checkIdx].result = result;
      strategy.admission[stageIdx].checks[checkIdx].date = new Date().toISOString().slice(0, 10);
    }
    return Promise.resolve();
  }
  await http.patch(`/strategies/${strategyId}/admission/${stageIdx}/${checkIdx}`, { status, result });
}

export async function submitToCommittee(strategyId: string): Promise<void> {
  if (USE_MOCK) {
    const strategy = mockStrategies.find(s => s.id === strategyId);
    if (strategy) strategy.status = '待投委审批';
    return Promise.resolve();
  }
  await http.post(`/strategies/${strategyId}/submit-committee`);
}

export function fetchStrategyClasses(): string[] {
  return ['全部', ...new Set(mockStrategies.map(item => item.primaryClass))];
}

export function fetchRatingRules(): RatingRule[] {
  return ratingRules;
}

export async function saveStrategyKpi(strategyId: string, scores: number[], totalScore: number, grade: StrategyRating): Promise<void> {
  if (USE_MOCK) {
    const strategy = mockStrategies.find(s => s.id === strategyId);
    if (strategy) {
      const now = new Date();
      const q = Math.ceil((now.getMonth() + 1) / 3);
      const period = `${now.getFullYear()}Q${q}`;
      strategy.kpiHistory.unshift({ period, scores, totalScore, grade, evaluator: '当前用户' });
      strategy.rating = grade;
    }
    return Promise.resolve();
  }
  await http.post(`/strategies/${strategyId}/kpi`, { scores, totalScore, grade });
}

export const strategyStatuses = ['全部', '研究中', '准入评估中', '待投委审批', '观察池', '已准入', '已驳回', '暂停', '退出'];

