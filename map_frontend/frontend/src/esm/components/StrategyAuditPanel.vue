<template>
  <div class="strategy-audit">
    <div class="audit-toolbar">
      <select v-model="actionFilter" class="select">
        <option v-for="item in actionTypes" :key="item">{{ item }}</option>
      </select>
      <span class="status-tag blue">共 {{ filteredLogs.length }} 条</span>
    </div>
    <div v-if="filteredLogs.length === 0" class="empty-hint muted">暂无操作记录</div>
    <div v-else class="audit-timeline">
      <div v-for="log in filteredLogs" :key="log.timestamp + log.action" class="audit-row terminal-card">
        <div class="audit-time">
          <span class="mono">{{ log.timestamp }}</span>
          <span class="action-tag" :class="actionClass(log.action)">{{ log.action }}</span>
        </div>
        <div class="audit-body">
          <span class="audit-operator">{{ log.operator }}</span>
          <span class="audit-detail">{{ log.detail }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Strategy } from '@esm/types/domain';

const props = defineProps<{ strategy: Strategy }>();

const actionFilter = ref('全部');
const actionTypes = ['全部', '创建策略', '准入操作', '状态变更', '额度变更', 'KPI评分', '风险处置'];

const filteredLogs = computed(() =>
  actionFilter.value === '全部'
    ? props.strategy.auditLog
    : props.strategy.auditLog.filter(l => l.action === actionFilter.value),
);

function actionClass(action: string) {
  if (action === '风险处置') return 'tag-red';
  if (action === 'KPI评分') return 'tag-blue';
  if (action === '额度变更') return 'tag-orange';
  if (action === '状态变更') return 'tag-green';
  return 'tag-gray';
}
</script>

<style scoped>
.strategy-audit { display: flex; flex-direction: column; gap: 12px; }
.audit-toolbar { display: flex; align-items: center; gap: 12px; }
.empty-hint { padding: 12px 0; font-size: 12px; }
.audit-timeline { display: flex; flex-direction: column; gap: 6px; }
.audit-row { padding: 10px 12px; }
.audit-time { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 11px; color: var(--am-text-3); }
.audit-body { display: flex; gap: 8px; font-size: 12px; }
.audit-operator { color: var(--am-brand); font-weight: 500; min-width: 48px; }
.audit-detail { color: var(--am-text-2); }

.action-tag {
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 400;
}
.tag-red { color: #ef4444; background: rgba(239,68,68,0.1); }
.tag-blue { color: #3b9eff; background: rgba(59,158,255,0.1); }
.tag-orange { color: #f97316; background: rgba(249,115,22,0.1); }
.tag-green { color: #22c55e; background: rgba(34,197,94,0.1); }
.tag-gray { color: var(--am-text-3); background: var(--am-bg-elevated); }
</style>

