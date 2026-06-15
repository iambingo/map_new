<template>
  <div v-if="store.activeStrategy" class="strategy-detail">
    <div class="detail-header">
      <button class="back-btn text-btn" @click="goBack">← 返回策略库</button>
      <div class="header-main">
        <div>
          <h2 class="text-base font-semibold text-[#E8ECF4]">{{ strategy.name }}</h2>
          <p class="mt-1 text-[11px] text-[#555E75]">
            {{ strategy.primaryClass }} · {{ strategy.secondaryClass }} · 创建于 {{ strategy.createdAt }}
          </p>
        </div>
        <div class="header-badges">
          <StatusTag :value="strategy.status" />
          <span v-if="strategy.rating" class="status-tag" :class="'rating-' + strategy.rating?.toLowerCase()">
            {{ strategy.rating }} {{ ratingLabel }}
          </span>
          <span v-if="strategy.quota" class="status-tag blue">
            额度 {{ strategy.quota.used }}/{{ strategy.quota.limit }} {{ strategy.quota.unit }}
          </span>
        </div>
      </div>
    </div>

    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <div class="tab-content">
      <AdmissionProgress
        v-if="activeTab === 'admission'"
        :strategy="strategy"
        @update-check="handleUpdateCheck"
        @submit-to-committee="handleSubmitCommittee"
      />
      <CommitteeResolution
        v-if="activeTab === 'committee'"
        :strategy="strategy"
        :committee-items="committeeItems"
        @initiate="handleSubmitCommittee"
      />
      <StrategyKpiPanel
        v-if="activeTab === 'kpi'"
        :strategy="strategy"
        @save-kpi="handleSaveKpi"
      />
      <StrategyRiskPanel
        v-if="activeTab === 'risk'"
        :strategy="strategy"
        :risk-events="riskEvents"
      />
      <StrategyPerformancePanel
        v-if="activeTab === 'performance'"
        :strategy="strategy"
      />
      <StrategyAuditPanel
        v-if="activeTab === 'audit'"
        :strategy="strategy"
      />
    </div>
  </div>
  <div v-else class="empty-state">
    <p class="muted">策略不存在</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusTag from '@esm/components/StatusTag.vue';
import AdmissionProgress from '@esm/components/AdmissionProgress.vue';
import CommitteeResolution from '@esm/components/CommitteeResolution.vue';
import StrategyKpiPanel from '@esm/components/StrategyKpiPanel.vue';
import StrategyRiskPanel from '@esm/components/StrategyRiskPanel.vue';
import StrategyPerformancePanel from '@esm/components/StrategyPerformancePanel.vue';
import StrategyAuditPanel from '@esm/components/StrategyAuditPanel.vue';
import { useStrategyStore } from '@esm/store/strategyStore';
import { useCommitteeStore } from '@esm/store/committeeStore';
import { useRiskStore } from '@esm/store/riskStore';

const route = useRoute();
const router = useRouter();
const store = useStrategyStore();
const committeeStore = useCommitteeStore();
const riskStore = useRiskStore();
const activeTab = ref('admission');

const strategy = computed(() => store.activeStrategy!);
const committeeItems = computed(() => committeeStore.committeeItems);
const riskEvents = computed(() => riskStore.riskEvents);

const ratingLabel = computed(() => {
  const rule = store.ratingRules.find(r => r.grade === strategy.value.rating);
  return rule ? rule.label : '';
});

const tabs = [
  { key: 'admission', label: '准入进度' },
  { key: 'committee', label: '投委决议' },
  { key: 'kpi', label: 'KPI 评估' },
  { key: 'risk', label: '风险监控' },
  { key: 'performance', label: '业绩追踪' },
  { key: 'audit', label: '操作记录' },
];

function goBack() {
  router.push('/esm/strategies');
}

async function handleUpdateCheck(stageIdx: number, checkIdx: number) {
  if (!strategy.value) return;
  await store.updateCheck(strategy.value.id, stageIdx, checkIdx, '已通过');
}

async function handleSubmitCommittee() {
  if (!strategy.value) return;
  await store.submitForCommittee(strategy.value.id);
}

async function handleSaveKpi(scores: number[], totalScore: number, grade: string) {
  if (!strategy.value) return;
  await store.saveKPI(strategy.value.id, scores, totalScore, grade as any);
}

onMounted(async () => {
  const id = route.params.id as string;
  if (id) {
    await store.loadDetail(id);
    if (!committeeStore.committeeItems.length) await committeeStore.load();
    if (!riskStore.riskEvents.length) await riskStore.load();
  }
});
</script>

<style scoped>
.strategy-detail { padding: 0; }
.detail-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--am-border);
}
.back-btn { font-size: 12px; margin-bottom: 8px; padding: 0; }
.header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.header-badges { display: flex; gap: 8px; align-items: center; }
.rating-a { color: #22c55e; background: rgba(34,197,94,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.rating-b { color: #3b9eff; background: rgba(59,158,255,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.rating-c { color: #f97316; background: rgba(249,115,22,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.rating-d { color: #ef4444; background: rgba(239,68,68,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }

.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--am-border);
  padding: 0 20px;
}
.tab-btn {
  padding: 10px 16px;
  font-size: 12px;
  color: var(--am-text-3);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
}
.tab-btn:hover { color: var(--am-text-2); }
.tab-btn.active {
  color: var(--am-brand);
  border-bottom-color: var(--am-brand);
}
.tab-content { padding: 16px 20px; }
.placeholder-panel {
  text-align: center;
  padding: 40px;
  color: var(--am-text-3);
}
</style>

