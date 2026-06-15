<template>
  <div class="fixed right-0 top-0 z-50 h-screen w-[420px] overflow-y-auto border-l border-[#2E3348] bg-[#202431] p-6">
    <button class="absolute right-4 top-4 cursor-pointer text-[#94A3B8] text-lg hover:text-[#E8ECF4]" type="button" @click="$emit('close')">✕</button>

    <h3 class="mb-5 pr-8 text-base font-semibold text-[#E8ECF4]">{{ spv.name }}</h3>

    <!-- 基本信息 -->
    <section class="mb-4">
      <h4 class="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">基本信息</h4>
      <div class="detail-row"><span class="detail-key">SPV 代码</span><span class="detail-val">{{ spv.code }}</span></div>
      <div class="detail-row"><span class="detail-key">管理人</span><span class="detail-val cursor-pointer text-[#3B9EFF] hover:underline" @click="goToManager">{{ spv.managerName }}</span></div>
      <div class="detail-row"><span class="detail-key">策略标签</span><span class="detail-val"><StatusTag :value="spv.strategyTag" /></span></div>
      <div class="detail-row"><span class="detail-key">规模</span><span class="detail-val">{{ spv.aum }} 亿</span></div>
      <div class="detail-row"><span class="detail-key">风险等级</span><span class="detail-val"><StatusTag :value="spv.riskLevel" /></span></div>
      <div class="detail-row"><span class="detail-key">成立日期</span><span class="detail-val">{{ spv.inceptionDate }}</span></div>
      <div class="detail-row"><span class="detail-key">到期日期</span><span class="detail-val">{{ spv.maturityDate }}</span></div>
      <div class="detail-row"><span class="detail-key">状态</span><span class="detail-val"><StatusTag :value="spv.status" /></span></div>
    </section>

    <!-- 管理人信息 -->
    <section v-if="manager" class="mb-4">
      <h4 class="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">管理人信息</h4>
      <div class="flex items-center gap-2 rounded bg-[#181C28] p-2">
        <div class="h-2 w-2 shrink-0 rounded-full" :class="managerDotColor" />
        <span class="text-xs text-[#3B9EFF]">{{ manager.name }}</span>
        <span class="ml-auto font-mono text-[11px] text-[#94A3B8]">AUM {{ manager.aum }}</span>
      </div>
      <div class="px-0 py-1 text-[11px] text-[#94A3B8]">
        评级：<span :class="ratingColor">{{ manager.rating }}</span> · 合作年限：{{ manager.cooperation }} · 旗下 SPV：{{ managerSpvCount }} 只
      </div>
    </section>

    <!-- 关联产品组合 -->
    <section class="mb-4">
      <h4 class="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">关联产品组合 ({{ spv.linkedProducts.length }})</h4>
      <div v-for="p in spv.linkedProducts" :key="p.name" class="detail-row">
        <span class="detail-key">{{ p.name }}</span>
        <span class="detail-val">持仓 {{ p.amount }}</span>
      </div>
      <p v-if="spv.linkedProducts.length === 0" class="py-2 text-center text-[11px] text-[#94A3B8]">暂无关联产品</p>
    </section>

    <!-- 业绩指标 -->
    <section>
      <h4 class="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">业绩指标</h4>
      <div class="detail-row"><span class="detail-key">年化收益率</span><span class="detail-val" :class="perfColor(spv.performance.annualReturn)">{{ spv.performance.annualReturn }}</span></div>
      <div class="detail-row"><span class="detail-key">最大回撤</span><span class="detail-val text-[#F04864]">{{ spv.performance.maxDrawdown }}</span></div>
      <div class="detail-row"><span class="detail-key">夏普比率</span><span class="detail-val">{{ spv.performance.sharpeRatio }}</span></div>
      <div class="detail-row"><span class="detail-key">波动率</span><span class="detail-val">{{ spv.performance.volatility }}</span></div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import StatusTag from '@esm/components/StatusTag.vue';
import type { SPV } from '@esm/types/domain';
import { useManagerStore } from '@esm/store/managerStore';
import { useSpvStore } from '@esm/store/spvStore';

const props = defineProps<{ spv: SPV }>();
defineEmits<{ close: [] }>();

const router = useRouter();
const managerStore = useManagerStore();
const spvStore = useSpvStore();

function goToManager() {
  router.push({ path: '/esm/managers', query: { search: props.spv.managerName } });
}

const manager = computed(() =>
  managerStore.managers.find(m => m.name === props.spv.managerName),
);

const managerSpvCount = computed(() =>
  spvStore.spvs.filter(s => s.managerName === props.spv.managerName).length,
);

const managerDotColor = computed(() => {
  const r = manager.value?.rating;
  if (r === 'A') return 'bg-[#00C9A7]';
  if (r === 'B') return 'bg-[#3B9EFF]';
  if (r === 'C') return 'bg-[#D89614]';
  return 'bg-[#F04864]';
});

const ratingColor = computed(() => {
  const r = manager.value?.rating;
  if (r === 'A') return 'text-[#00C9A7]';
  if (r === 'B') return 'text-[#3B9EFF]';
  if (r === 'C') return 'text-[#D89614]';
  return 'text-[#F04864]';
});

function perfColor(val: string) {
  if (val === '—') return '';
  return 'text-[#F04864]';
}
</script>

<style scoped>
.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #252A3A;
}
.detail-key {
  color: #B4BAC9;
  font-size: 12px;
}
.detail-val {
  font-family: "Consolas", "Courier New", monospace;
  font-size: 12px;
}
</style>

