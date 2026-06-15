import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { SPV, SpvStrategyTag, SpvRiskLevel, StrategyPool } from '@esm/types/domain';
import { fetchSPVs } from '@esm/api/spv';

const strategyOrder: SpvStrategyTag[] = ['固收增强含权', '固收增强', '量化策略', '权益策略', '另类策略', '海外策略'];

export const useSpvStore = defineStore('spv', () => {
  const spvs = ref<SPV[]>([]);
  const selectedPoolStrategy = ref('');
  const activeSPV = ref<SPV | null>(null);
  const searchQuery = ref('');
  const statusFilter = ref('全部');
  const riskFilter = ref('全部');

  const filteredSPVs = computed(() =>
    spvs.value.filter(item => {
      if (selectedPoolStrategy.value && item.strategyTag !== selectedPoolStrategy.value) return false;
      if (statusFilter.value !== '全部' && item.status !== statusFilter.value) return false;
      if (riskFilter.value !== '全部' && item.riskLevel !== riskFilter.value) return false;
      if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        return item.name.toLowerCase().includes(q) || item.managerName.toLowerCase().includes(q);
      }
      return true;
    }),
  );

  const strategyPools = computed<StrategyPool[]>(() => {
    const metricConfig: Record<string, { label: string; compute: (s: SPV[]) => string }> = {
      '固收增强含权': { label: '平均久期', compute: () => '2.3Y' },
      '固收增强': { label: '平均久期', compute: () => '1.8Y' },
      '量化策略': { label: '平均波动', compute: s => (s.reduce((a, b) => a + parseFloat(b.performance.volatility), 0) / s.length).toFixed(1) + '%' },
      '权益策略': { label: '最大回撤', compute: s => Math.min(...s.map(x => parseFloat(x.performance.maxDrawdown))).toFixed(1) + '%' },
      '另类策略': { label: '夏普比率', compute: s => (s.reduce((a, b) => a + parseFloat(b.performance.sharpeRatio), 0) / s.length).toFixed(2) },
      '海外策略': { label: '年化收益', compute: s => (s.reduce((a, b) => a + parseFloat(b.performance.annualReturn), 0) / s.length).toFixed(1) + '%' },
    };

    return strategyOrder.map(tag => {
      const poolSpvs = spvs.value.filter(s => s.strategyTag === tag);
      const totalAum = poolSpvs.reduce((a, b) => a + b.aum, 0);
      const riskLevels = poolSpvs.map(s => s.riskLevel);
      const hasHigh = riskLevels.includes('高');
      const hasMid = riskLevels.includes('中');
      const riskLevel: SpvRiskLevel = hasHigh ? '高' : hasMid ? '中' : '低';
      const config = metricConfig[tag];

      return {
        strategyName: tag,
        spvCount: poolSpvs.length,
        totalAum: totalAum.toFixed(1),
        riskLevel,
        metricLabel: config.label,
        metricValue: poolSpvs.length > 0 ? config.compute(poolSpvs) : '—',
      };
    });
  });

  function selectPool(strategy: string) {
    selectedPoolStrategy.value = selectedPoolStrategy.value === strategy ? '' : strategy;
  }

  function selectSPV(spv: SPV) {
    activeSPV.value = spv;
  }

  function clearActiveSPV() {
    activeSPV.value = null;
  }

  async function load() {
    spvs.value = await fetchSPVs();
  }

  return {
    spvs, filteredSPVs, strategyPools,
    selectedPoolStrategy, activeSPV,
    searchQuery, statusFilter, riskFilter,
    selectPool, selectSPV, clearActiveSPV, load,
  };
});

