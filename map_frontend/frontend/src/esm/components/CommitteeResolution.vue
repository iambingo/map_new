<template>
  <div class="committee-resolution">
    <div v-if="relatedItems.length === 0" class="empty-state">
      <p class="muted">暂无关联的投委决议</p>
      <button v-if="canSubmit" class="btn-primary" @click="$emit('initiate')">发起投委审批</button>
    </div>
    <div v-else>
      <div v-for="item in relatedItems" :key="item.title" class="resolution-card terminal-card">
        <div class="resolution-header">
          <strong>{{ item.title }}</strong>
          <StatusTag :value="item.status" />
        </div>
        <div class="resolution-meta">
          <span>提交人：{{ item.submitter }}</span>
          <span>风险评级：<StatusTag :value="item.riskLevel" /></span>
          <span>会议日期：{{ item.meetingDate }}</span>
        </div>
        <p class="muted">{{ item.recommendation }}</p>
        <p v-if="item.voteResult" class="vote-result">投票结果：{{ item.voteResult }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Strategy, CommitteeItem } from '@esm/types/domain';
import StatusTag from '@esm/components/StatusTag.vue';

const props = defineProps<{
  strategy: Strategy;
  committeeItems: CommitteeItem[];
}>();
defineEmits<{ initiate: [] }>();

const relatedItems = computed(() =>
  props.committeeItems.filter(c => c.title.includes(props.strategy.name)),
);

const canSubmit = computed(() =>
  ['准入评估中', '待投委审批', '观察池', '已准入'].includes(props.strategy.status),
);
</script>

<style scoped>
.resolution-card {
  padding: 12px 14px;
  margin-bottom: 10px;
}
.resolution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.resolution-meta {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: var(--am-text-3);
  margin-bottom: 6px;
}
.vote-result { font-size: 12px; color: var(--am-brand); }
.empty-state {
  text-align: center;
  padding: 24px;
}
.btn-primary {
  padding: 6px 16px;
  background: var(--am-brand);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  margin-top: 8px;
}
.btn-primary:hover { opacity: 0.9; }
</style>

