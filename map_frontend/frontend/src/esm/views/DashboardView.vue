<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">总览 Dashboard</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">以策略、管理人、额度、审批、风险五条主线跟踪外部策略闭环。</p>
  </div>

  <MetricGrid :groups="dashboardMetricGroups" @item-click="onMetricClick" />

  <div class="two-col mt-3">
    <TerminalSection title="策略状态分布">
      <template #actions><span class="status-tag blue">准入漏斗</span></template>
      <div class="bars">
        <BarRow
          v-for="row in strategyStatusDistribution"
          :key="row.name"
          :label="row.name"
          :value="row.count"
          :pct="Math.max(12, (row.count / totalStrategies) * 100)"
          @click="onStatusBarClick(row.name)"
        />
      </div>
    </TerminalSection>
    <TerminalSection title="一级策略覆盖">
      <template #actions><span class="status-tag green">多元分散</span></template>
      <div class="bars">
        <BarRow
          v-for="row in strategyClassDistribution"
          :key="row.name"
          :label="row.name"
          :value="row.count"
          :pct="Math.max(12, (row.count / totalStrategies) * 100)"
          @click="onClassBarClick(row.name)"
        />
      </div>
    </TerminalSection>
  </div>

  <div class="mt-3">
    <TerminalSection title="SPV 策略分布">
      <div class="bars">
        <BarRow
          v-for="row in spvStrategyDistribution"
          :key="row.name"
          :label="row.name"
          :value="row.count"
          :pct="Math.max(12, (row.count / totalSPVs) * 100)"
          @click="onSpvBarClick(row.name)"
        />
      </div>
    </TerminalSection>
  </div>

  <div class="two-col mt-3">
    <TerminalSection title="待办审批事项">
      <template #actions><span class="status-tag orange">投委会</span></template>
      <div class="mini-list">
        <div v-for="(item, index) in recentCommitteeItems" :key="item.title" class="mini-item">
          <div>
            <strong>{{ item.title }}</strong>
            <div class="muted">{{ item.department }} · {{ item.meetingDate }}</div>
          </div>
          <button class="text-btn" type="button" @click="committeeStore.showDetail(index)">查看</button>
        </div>
      </div>
    </TerminalSection>
    <TerminalSection title="风险热区">
      <template #actions><span class="status-tag red">需复核</span></template>
      <div class="risk-hot-list">
        <div v-for="item in recentRiskEvents" :key="item.target" class="risk-hot-row cursor-pointer" @click="onRiskClick(item.level)">
          <div class="min-w-0">
            <strong>{{ item.target }}</strong>
            <div>{{ item.reason }}</div>
          </div>
          <StatusTag :value="item.level" />
        </div>
      </div>
    </TerminalSection>
  </div>

  <CommitteeDetailModal
    :item="committeeStore.activeCommittee"
    :details="committeeStore.committeeDetails()"
    @close="committeeStore.closeDetail()"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import MetricGrid from '@esm/components/MetricGrid.vue';
import TerminalSection from '@esm/components/TerminalSection.vue';
import BarRow from '@esm/components/BarRow.vue';
import StatusTag from '@esm/components/StatusTag.vue';
import CommitteeDetailModal from '@esm/components/CommitteeDetailModal.vue';
import { useDashboardStore } from '@esm/store/dashboardStore';
import { useCommitteeStore } from '@esm/store/committeeStore';

interface MetricItem {
  id?: string;
  label: string;
  value: string;
  unit?: string;
  delta?: string;
  trend?: 'up' | 'down' | 'flat';
  desc?: string;
}

const router = useRouter();
const dashboardStore = useDashboardStore();
const committeeStore = useCommitteeStore();

const {
  dashboardMetricGroups, strategyStatusDistribution, strategyClassDistribution,
  recentCommitteeItems, recentRiskEvents, totalStrategies,
  spvStrategyDistribution, totalSPVs,
} = storeToRefs(dashboardStore);

function currentMonthKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

const metricRoutes: Record<string, { path: string; query?: Record<string, string> }> = {
  'strategy-total': { path: '/esm/strategies' },
  'strategy-new-month': { path: '/esm/strategies', query: { createdMonth: currentMonthKey() } },
  'strategy-admitted': { path: '/esm/strategies', query: { status: '已准入' } },
  'strategy-watch': { path: '/esm/strategies', query: { status: '观察池' } },
  'manager-total': { path: '/esm/managers' },
  'spv-total': { path: '/esm/spv-pool' },
  'delegated-aum': { path: '/esm/spv-pool' },
  'available-quota': { path: '/esm/strategies', query: { status: '已准入' } },
  'committee-pending': { path: '/esm/committee', query: { status: 'pending' } },
  'risk-alerts': { path: '/esm/risk' },
};

function onMetricClick(item: MetricItem) {
  const target = metricRoutes[item.id ?? item.label];
  if (target) router.push(target);
}

function onStatusBarClick(status: string) {
  router.push({ path: '/esm/strategies', query: { status } });
}

function onClassBarClick(category: string) {
  router.push({ path: '/esm/strategies', query: { category } });
}

function onSpvBarClick(strategy: string) {
  router.push({ path: '/esm/spv-pool', query: { strategy } });
}

function onRiskClick(level: string) {
  router.push({ path: '/esm/risk', query: { level } });
}

onMounted(() => { dashboardStore.load(); });
</script>

