<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">四层准入流程 Approval Workflow</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">从白名单、策略、产品到额度，形成可追踪的准入证据链。</p>
  </div>
  <TerminalSection title="准入工作流">
    <template #actions>
      <span class="status-tag blue">Evidence Chain</span>
      <span class="status-tag green ml-1.5">示例项目：转债增强稳健一号</span>
    </template>
    <div class="workflow map-steps">
      <div v-for="(stage, index) in workflowStages" :key="stage.name" class="workflow-step">
        <div class="step-index-col">
          <span class="stage-no mono">{{ String(index + 1).padStart(2, '0') }}</span>
          <span v-if="index < workflowStages.length - 1" class="step-line"></span>
        </div>
        <div class="workflow-step-body">
          <div class="stage-head">
            <div class="stage-title">
              <span>{{ stage.name }}</span>
              <small>Node {{ String(index + 1).padStart(2, '0') }} / {{ workflowStages.length }}</small>
            </div>
            <select v-model="workflowStatus[index]" class="select compact">
              <option v-for="option in workflowOptions" :key="option">{{ option }}</option>
            </select>
          </div>
          <div class="check-grid evidence-grid">
            <div v-for="(check, childIndex) in stage.checks" :key="check" class="check-item readonly-zone evidence-item">
              <strong>{{ check }}</strong>
              <small>{{ workflowStatus[index] === '已通过' ? '证据已归档' : childIndex % 2 ? '待补充说明' : '复核中' }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </TerminalSection>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import TerminalSection from '@esm/components/TerminalSection.vue';

const workflowStages = [
  { name: '白名单准入', checks: ['牌照', '历史', '合规', '托管', '法律文件'] },
  { name: '策略准入', checks: ['收益来源', '波动', '回撤', '流动性', '杠杆', '估值透明度', '穿透性'] },
  { name: '产品准入', checks: ['历史业绩', '组合结构', '集中度', '风险暴露', '运作稳定性'] },
  { name: '额度准入', checks: ['初始额度', '单一管理人上限', '单一策略上限', '止损线', '观察名单触发条件'] },
];

const workflowOptions = ['未开始', '进行中', '已通过', '驳回', '补充材料'];
const workflowStatus = ref(['已通过', '进行中', '补充材料', '未开始']);
</script>

