import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { Strategy, RatingRule, StrategyRating } from '@esm/types/domain';
import {
  fetchStrategies, fetchStrategyById, fetchStrategyClasses,
  updateAdmissionCheck, submitToCommittee, fetchRatingRules, strategyStatuses,
  saveStrategyKpi,
} from '@esm/api/strategy';

export const useStrategyStore = defineStore('strategy', () => {
  const strategies = ref<Strategy[]>([]);
  const activeStrategy = ref<Strategy | null>(null);
  const searchQuery = ref('');
  const categoryFilter = ref('全部');
  const statusFilter = ref('全部');
  const createdMonthFilter = ref('');
  const strategyClasses = ref<string[]>(['全部']);
  const ratingRules = ref<RatingRule[]>([]);

  const filteredStrategies = computed(() =>
    strategies.value.filter(item =>
      (categoryFilter.value === '全部' || item.primaryClass === categoryFilter.value)
      && (statusFilter.value === '全部' || item.status === statusFilter.value)
      && (!createdMonthFilter.value || item.createdAt.startsWith(createdMonthFilter.value))
      && Object.values(item).join('').includes(searchQuery.value),
    ),
  );

  async function load() {
    strategies.value = await fetchStrategies();
    strategyClasses.value = fetchStrategyClasses();
    ratingRules.value = fetchRatingRules();
  }

  async function loadDetail(id: string) {
    activeStrategy.value = await fetchStrategyById(id) ?? null;
  }

  async function updateCheck(strategyId: string, stageIdx: number, checkIdx: number, status: string, result?: string) {
    await updateAdmissionCheck(strategyId, stageIdx, checkIdx, status, result);
    if (activeStrategy.value?.id === strategyId) {
      activeStrategy.value = { ...activeStrategy.value };
    }
  }

  async function submitForCommittee(strategyId: string) {
    await submitToCommittee(strategyId);
    if (activeStrategy.value?.id === strategyId) {
      activeStrategy.value = { ...activeStrategy.value, status: '待投委审批' };
    }
    const idx = strategies.value.findIndex(s => s.id === strategyId);
    if (idx >= 0) strategies.value[idx] = { ...strategies.value[idx], status: '待投委审批' };
  }

  async function saveKPI(strategyId: string, scores: number[], totalScore: number, grade: StrategyRating) {
    await saveStrategyKpi(strategyId, scores, totalScore, grade);
    const now = new Date();
    const q = Math.ceil((now.getMonth() + 1) / 3);
    const kpiPeriod = `${now.getFullYear()}Q${q}`;
    const newKpi = { period: kpiPeriod, scores, totalScore, grade, evaluator: '当前用户' };
    if (activeStrategy.value?.id === strategyId) {
      const updated = { ...activeStrategy.value };
      updated.kpiHistory = [newKpi, ...updated.kpiHistory];
      updated.rating = grade;
      activeStrategy.value = updated;
    }
    const idx = strategies.value.findIndex(s => s.id === strategyId);
    if (idx >= 0) strategies.value[idx] = { ...strategies.value[idx], rating: grade };
  }

  function clearActive() {
    activeStrategy.value = null;
  }

  return {
    strategies, activeStrategy, searchQuery, categoryFilter, statusFilter,
    createdMonthFilter, strategyClasses, strategyStatuses, ratingRules,
    filteredStrategies, load, loadDetail, updateCheck, submitForCommittee, saveKPI, clearActive,
  };
});

