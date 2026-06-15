<template>
  <div class="strategy-risk">
    <div v-if="relatedEvents.length" class="risk-events">
      <h4 class="section-title">风险事件</h4>
      <div class="event-list">
        <div v-for="evt in relatedEvents" :key="evt.triggerDate + evt.reason" class="event-card terminal-card">
          <div class="event-header">
            <StatusTag :value="evt.level" />
            <StatusTag :value="evt.exitStatus" />
            <span class="muted">{{ evt.triggerDate }}</span>
          </div>
          <p class="event-reason">{{ evt.reason }}</p>
        </div>
      </div>
    </div>
    <div v-else class="empty-hint muted">暂无关联风险事件</div>

    <div class="trigger-section">
      <h4 class="section-title">9 类触发条件监控</h4>
      <div class="trigger-grid">
        <div
          v-for="(trigger, i) in triggerStatuses"
          :key="trigger.name"
          class="trigger-card terminal-card"
          :class="trigger.cssClass"
        >
          <span class="trigger-status">{{ trigger.icon }}</span>
          <strong>{{ trigger.name }}</strong>
          <span class="trigger-state">{{ trigger.state }}</span>
        </div>
      </div>
    </div>

    <div v-if="strategy.status === '暂停' || strategy.status === '退出'" class="disposition">
      <h4 class="section-title">处置状态</h4>
      <div class="disp-card terminal-card">
        <StatusTag :value="strategy.status" />
        <span class="muted">{{ dispositionDesc }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Strategy, RiskEvent } from '@esm/types/domain';
import StatusTag from '@esm/components/StatusTag.vue';

const props = defineProps<{
  strategy: Strategy;
  riskEvents: RiskEvent[];
}>();

const relatedEvents = computed(() =>
  props.riskEvents.filter(e =>
    e.target.includes(props.strategy.name)
    || e.target.includes(props.strategy.managerName || '')
    || e.strategyClass === props.strategy.primaryClass,
  ),
);

const triggerNames = [
  '最大回撤超过阈值', '风格漂移', '核心人员离职',
  '流动性恶化', '杠杆异常', '估值异常',
  '业绩持续低于基准', '发生信用事件', '发生合规或风控事件',
];

// 根据策略状态和风险等级模拟触发条件状态
const triggerStatuses = computed(() => {
  const isHighRisk = props.strategy.rating === 'D' || props.strategy.status === '暂停' || props.strategy.status === '退出';
  const isMedRisk = props.strategy.rating === 'C';
  return triggerNames.map((name, i) => {
    if (isHighRisk && i < 3) return { name, icon: '🔴', state: '已触发', cssClass: 'triggered' };
    if (isMedRisk && i < 1) return { name, icon: '🟡', state: '接近阈值', cssClass: 'warning' };
    return { name, icon: '🟢', state: '正常', cssClass: 'normal' };
  });
});

const dispositionDesc = computed(() => {
  if (props.strategy.status === '暂停') return '策略已暂停新增投资，等待风控复核';
  if (props.strategy.status === '退出') return '策略已启动退出流程，持仓逐步清算';
  return '';
});
</script>

<style scoped>
.strategy-risk { display: flex; flex-direction: column; gap: 16px; }
.section-title { font-size: 13px; font-weight: 600; color: var(--am-text-2); margin-bottom: 8px; }
.event-list { display: flex; flex-direction: column; gap: 8px; }
.event-card { padding: 10px 12px; }
.event-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.event-reason { font-size: 12px; color: var(--am-text-2); }
.empty-hint { padding: 12px 0; font-size: 12px; }

.trigger-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.trigger-card {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  border-left: 3px solid transparent;
}
.trigger-card.normal { border-left-color: #22c55e; }
.trigger-card.warning { border-left-color: #f97316; }
.trigger-card.triggered { border-left-color: #ef4444; }
.trigger-status { font-size: 14px; }
.trigger-state { font-size: 11px; color: var(--am-text-3); }

.disposition { border-top: 1px solid var(--am-border); padding-top: 12px; }
.disp-card { display: flex; align-items: center; gap: 12px; padding: 10px 12px; }
</style>

