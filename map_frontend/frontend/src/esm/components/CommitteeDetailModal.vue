<template>
  <div v-if="item" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-head">
        <h3>{{ item.title }}</h3>
        <button class="text-btn" type="button" @click="$emit('close')">关闭</button>
      </div>
      <div class="modal-body">
        <div class="detail-grid">
          <div v-for="detail in details" :key="detail.label" class="detail readonly-zone evidence-detail">
            <label>{{ detail.label }}</label>
            <strong v-if="detail.isStatus"><StatusTag :value="detail.value" /></strong>
            <strong v-else>{{ detail.value }}</strong>
          </div>
        </div>
        <div class="readonly-zone detail-note">
          <strong>审批摘要</strong>
          <p class="muted">
            准入建议基于管理人尽调、策略收益来源穿透、历史回撤归因、容量测算、组合适配性与风险事件核查。后续需在额度生效后纳入月度 KPI、风险预警和季度复评。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatusTag from '@esm/components/StatusTag.vue';
import type { CommitteeItem } from '@esm/types/domain';

interface DetailField {
  label: string;
  value: string;
  isStatus?: boolean;
}

defineProps<{
  item: CommitteeItem | null;
  details: DetailField[];
}>();

defineEmits<{
  close: [];
}>();
</script>

