<template>
  <div class="admission-progress">
    <div v-for="(stage, si) in strategy.admission" :key="stage.stage" class="admission-stage">
      <div class="stage-header" :class="stageClass(stage.status)">
        <span class="stage-icon">{{ stageIcon(stage.status) }}</span>
        <span class="stage-name">{{ stage.stage }}</span>
        <span class="stage-status" :class="'tag-' + tagColor(stage.status)">{{ stage.status }}</span>
      </div>
      <div class="stage-checks">
        <div v-for="(check, ci) in stage.checks" :key="check.name" class="check-row">
          <span class="check-icon">{{ checkIcon(check.status) }}</span>
          <span class="check-name">{{ check.name }}</span>
          <span v-if="check.result" class="check-result muted">{{ check.result }}</span>
          <span v-if="check.operator" class="check-meta muted">{{ check.operator }} · {{ check.date }}</span>
          <span v-else class="check-meta muted">—</span>
          <button
            v-if="check.status === '未开始' || check.status === '驳回' || check.status === '补充材料'"
            class="text-btn"
            @click="$emit('updateCheck', si, ci)"
          >操作</button>
        </div>
      </div>
    </div>

    <div v-if="allStagesPassed" class="submit-section">
      <span class="status-tag blue">四层准入全部通过</span>
      <button
        v-if="strategy.status === '准入评估中'"
        class="btn-primary"
        @click="$emit('submitToCommittee')"
      >提交投委会审批</button>
      <span v-else-if="strategy.status === '待投委审批'" class="muted">已提交投委会，等待审议</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Strategy } from '@esm/types/domain';

const props = defineProps<{ strategy: Strategy }>();
defineEmits<{ updateCheck: [stageIdx: number, checkIdx: number]; submitToCommittee: [] }>();

const allStagesPassed = computed(() =>
  props.strategy.admission.length > 0 && props.strategy.admission.every(s => s.status === '已通过'),
);

function stageIcon(status: string) {
  if (status === '已通过') return '✓';
  if (status === '进行中') return '→';
  if (status === '驳回') return '✗';
  return '○';
}
function stageClass(status: string) {
  if (status === '已通过') return 'passed';
  if (status === '进行中') return 'active';
  if (status === '驳回') return 'rejected';
  return 'pending';
}
function checkIcon(status: string) {
  if (status === '已通过') return '✅';
  if (status === '驳回') return '❌';
  if (status === '进行中') return '🔄';
  if (status === '补充材料') return '📎';
  return '⬜';
}
function tagColor(status: string) {
  if (status === '已通过') return 'green';
  if (status === '进行中') return 'blue';
  if (status === '驳回') return 'red';
  if (status === '补充材料') return 'orange';
  return 'gray';
}
</script>

<style scoped>
.admission-stage {
  border: 1px solid var(--am-border);
  border-radius: 6px;
  margin-bottom: 12px;
  overflow: hidden;
}
.stage-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--am-bg-elevated);
  font-size: 13px;
  font-weight: 600;
}
.stage-header.passed { border-left: 3px solid #22c55e; }
.stage-header.active { border-left: 3px solid #3b9eff; }
.stage-header.rejected { border-left: 3px solid #ef4444; }
.stage-header.pending { border-left: 3px solid var(--am-border-sub); }
.stage-status { font-size: 11px; font-weight: 400; }
.tag-green { color: #22c55e; }
.tag-blue { color: #3b9eff; }
.tag-red { color: #ef4444; }
.tag-orange { color: #f97316; }
.tag-gray { color: var(--am-text-3); }
.stage-checks { padding: 4px 14px; }
.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--am-border-sub);
  font-size: 12px;
}
.check-row:last-child { border-bottom: none; }
.check-name { flex: 1; }
.check-result { font-size: 11px; }
.check-meta { font-size: 10px; min-width: 120px; text-align: right; }
.submit-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
}
.btn-primary {
  padding: 6px 16px;
  background: var(--am-brand);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.btn-primary:hover { opacity: 0.9; }
</style>

