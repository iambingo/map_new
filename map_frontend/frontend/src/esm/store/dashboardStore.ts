import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import type { DashboardMetric, DashboardMetricGroup, DistributionItem, Strategy, Manager, CommitteeItem, RiskEvent, SPV } from '@esm/types/domain';
import { fetchStrategies } from '@esm/api/strategy';
import { fetchManagers } from '@esm/api/manager';
import { fetchCommitteeItems } from '@esm/api/committee';
import { fetchRiskEvents } from '@esm/api/risk';
import { fetchSPVs } from '@esm/api/spv';

export const useDashboardStore = defineStore('dashboard', () => {
  const strategies = ref<Strategy[]>([]);
  const managers = ref<Manager[]>([]);
  const committeeItems = ref<CommitteeItem[]>([]);
  const riskEvents = ref<RiskEvent[]>([]);
  const spvs = ref<SPV[]>([]);

  const totalStrategies = computed(() => strategies.value.length);

  const highRiskCount = computed(() => riskEvents.value.filter(item => item.level === '高').length);

  const admittedStrategyCount = computed(() => strategies.value.filter(item => item.status === '已准入').length);
  const watchStrategyCount = computed(() => strategies.value.filter(item => item.status === '观察池').length);
  const pendingCommitteeCount = computed(() => committeeItems.value.filter(item => item.status !== '已通过').length);
  const totalDelegatedAum = computed(() => spvs.value.reduce((sum, item) => sum + item.aum, 0));

  function currentMonthKey(): string {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }

  const currentMonth = computed(() => currentMonthKey());
  const newStrategyCount = computed(() =>
    strategies.value.filter(item => item.createdAt.startsWith(currentMonth.value)).length,
  );

  function parseAmount(value: string): number {
    const parsed = Number(value.replace(/[^\d.]/g, ''));
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function formatAmount(value: number): string {
    return value >= 100 ? value.toFixed(0) : value.toFixed(1);
  }

  const totalStrategyCapacity = computed(() =>
    strategies.value.reduce((sum, item) => sum + parseAmount(item.capacity), 0),
  );

  const availableQuota = computed(() =>
    Math.max(0, totalStrategyCapacity.value - totalDelegatedAum.value),
  );

  const dashboardMetricGroups = computed<DashboardMetricGroup[]>(() => [
    {
      id: 'strategy',
      title: '策略',
      columns: 4,
      items: [
        { id: 'strategy-total', label: '策略数量', value: String(strategies.value.length), desc: '查看全部策略明细' },
        { id: 'strategy-new-month', label: '本月新增策略', value: String(newStrategyCount.value), desc: `${currentMonth.value} 新建策略` },
        { id: 'strategy-admitted', label: '已准入策略', value: String(admittedStrategyCount.value), desc: '进入可配置与额度池' },
        { id: 'strategy-watch', label: '观察池策略', value: String(watchStrategyCount.value), desc: '持续跟踪与尽调' },
      ],
    },
    {
      id: 'manager',
      title: '管理人',
      columns: 3,
      items: [
        { id: 'manager-total', label: '管理人数量', value: String(managers.value.length), desc: '查看管理人库' },
        { id: 'spv-total', label: 'SPV总数', value: String(spvs.value.length), desc: '查看 SPV 明细表' },
        { id: 'delegated-aum', label: '当前委外规模', value: formatAmount(totalDelegatedAum.value), unit: '亿', desc: '按 SPV 在册规模汇总' },
      ],
    },
    {
      id: 'quota-risk',
      title: '额度、审批、风险',
      columns: 3,
      items: [
        { id: 'available-quota', label: '可投额度', value: formatAmount(availableQuota.value), unit: '亿', desc: '策略容量扣减委外规模' },
        { id: 'committee-pending', label: '待委员会审批', value: String(pendingCommitteeCount.value), desc: '进入投委审批队列' },
        { id: 'risk-alerts', label: '风险预警数量', value: String(riskEvents.value.length), desc: `高风险 ${highRiskCount.value} 项` },
      ],
    },
  ]);

  const dashboardMetrics = computed<DashboardMetric[]>(() => [
    { label: '策略数量', value: String(strategies.value.length), desc: '覆盖 6 个一级策略分类' },
    { label: '管理人数量', value: String(managers.value.length), desc: 'A/B/C/D 分层管理' },
    { label: '已准入策略', value: String(strategies.value.filter(item => item.status === '已准入').length), desc: '进入可配置与额度池' },
    { label: '观察池策略', value: String(strategies.value.filter(item => item.status === '观察池').length), desc: '持续跟踪与尽调' },
    { label: '当前委外规模', value: '382 亿', desc: '较上月 +18 亿' },
    { label: '风险预警数量', value: String(riskEvents.value.length), desc: `高风险 ${highRiskCount.value} 项` },
    { label: '本月新增策略', value: String(newStrategyCount.value), desc: `${currentMonth.value} 新建策略` },
    { label: '待投委会审批', value: String(committeeItems.value.filter(item => item.status !== '已通过').length), desc: '本月会议 2 场' },
    { label: 'SPV 总数', value: String(spvs.value.length), desc: '6 个策略分类' },
    { label: '策略池数量', value: '6', desc: '覆盖全部策略类型' },
  ]);

  const strategyStatusDistribution = computed<DistributionItem[]>(() =>
    ['研究中', '观察池', '已准入', '暂停', '退出'].map(name => ({
      name,
      count: strategies.value.filter(item => item.status === name).length,
    })),
  );

  const strategyClassDistribution = computed<DistributionItem[]>(() =>
    ['固收增强', '固收增强含权', '另类策略', '海外策略', '权益策略', '量化策略'].map(name => ({
      name,
      count: strategies.value.filter(item => item.primaryClass === name).length,
    })),
  );

  const recentCommitteeItems = computed(() => committeeItems.value.slice(0, 4));
  const recentRiskEvents = computed(() => riskEvents.value.slice(0, 4));

  const spvStrategyDistribution = computed<DistributionItem[]>(() =>
    ['固收增强含权', '固收增强', '量化策略', '权益策略', '另类策略', '海外策略'].map(name => ({
      name,
      count: spvs.value.filter(s => s.strategyTag === name).length,
    })),
  );

  const totalSPVs = computed(() => spvs.value.length);

  async function load() {
    [strategies.value, managers.value, committeeItems.value, riskEvents.value, spvs.value] = await Promise.all([
      fetchStrategies(),
      fetchManagers(),
      fetchCommitteeItems(),
      fetchRiskEvents(),
      fetchSPVs(),
    ]);
  }

  return {
    dashboardMetrics, dashboardMetricGroups, strategyStatusDistribution, strategyClassDistribution,
    recentCommitteeItems, recentRiskEvents, highRiskCount, totalStrategies,
    spvStrategyDistribution, totalSPVs,
    load,
  };
});

