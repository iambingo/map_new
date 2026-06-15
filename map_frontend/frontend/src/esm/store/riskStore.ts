import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { RiskEvent } from '@esm/types/domain';
import { fetchRiskEvents } from '@esm/api/risk';

export const useRiskStore = defineStore('risk', () => {
  const riskEvents = ref<RiskEvent[]>([]);
  const riskLevelFilter = ref('全部');

  const filteredRiskEvents = computed(() =>
    riskEvents.value.filter(item => riskLevelFilter.value === '全部' || item.level === riskLevelFilter.value),
  );

  const highRiskCount = computed(() => riskEvents.value.filter(item => item.level === '高').length);

  async function load() {
    riskEvents.value = await fetchRiskEvents();
  }

  return { riskEvents, riskLevelFilter, filteredRiskEvents, highRiskCount, load };
});

