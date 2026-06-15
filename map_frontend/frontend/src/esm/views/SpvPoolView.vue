<template>
  <!-- 页头 -->
  <div class="mb-5 flex items-center justify-between">
    <div>
      <h2 class="text-lg font-semibold text-[#E8ECF4]">SPV 策略池</h2>
      <p class="mt-1 font-mono text-[11px] text-[#555E75]">MAP / SPV 策略池</p>
    </div>
    <span class="font-mono text-[11px] text-[#94A3B8]">数据更新：{{ lastUpdate }}</span>
  </div>

  <!-- 策略池卡片 -->
  <div class="mb-6 grid grid-cols-4 gap-3.5">
    <div
      v-for="pool in store.strategyPools"
      :key="pool.strategyName"
      class="cursor-pointer rounded-md border bg-[#202431] p-4 transition-colors hover:border-[#3B9EFF]"
      :class="store.selectedPoolStrategy === pool.strategyName ? 'border-[#3B9EFF] bg-[rgba(59,158,255,0.06)]' : 'border-[#2E3348]'"
      @click="store.selectPool(pool.strategyName)"
    >
      <div class="mb-2.5 flex items-center gap-2">
        <span class="text-sm font-semibold">{{ pool.strategyName }}</span>
        <span class="rounded-full bg-[rgba(59,158,255,0.15)] px-2 py-0.5 text-[11px] text-[#3B9EFF]">{{ pool.spvCount }} 只</span>
      </div>
      <div class="mb-1 flex justify-between">
        <span class="text-xs text-[#94A3B8]">总规模</span>
        <span class="font-mono text-[13px]">{{ pool.totalAum }} 亿</span>
      </div>
      <div class="flex justify-between">
        <span class="text-xs text-[#94A3B8]">{{ pool.metricLabel }}</span>
        <span class="font-mono text-[13px]">{{ pool.metricValue }}</span>
      </div>
      <div class="mt-2">
        <StatusTag :value="pool.riskLevel" />
      </div>
    </div>
  </div>

  <!-- 筛选栏 -->
  <div class="toolbar">
    <div class="filters">
      <input v-model="store.searchQuery" class="input" placeholder="搜索 SPV 名称 / 管理人" />
      <select v-model="store.statusFilter" class="select">
        <option v-for="s in spvStatuses" :key="s">{{ s }}</option>
      </select>
      <select v-model="store.riskFilter" class="select">
        <option v-for="r in spvRiskLevels" :key="r">{{ r }}</option>
      </select>
    </div>
    <span class="status-tag blue">共 {{ store.filteredSPVs.length }} 条</span>
  </div>

  <!-- SPV 表格 -->
  <div class="table-wrap">
    <table class="fin-table esm-table dense-fin-table">
      <thead>
        <tr>
          <th>SPV 名称</th>
          <th>管理人</th>
          <th>策略标签</th>
          <th>规模(亿)</th>
          <th>风险等级</th>
          <th>成立日期</th>
          <th>状态</th>
          <th>关联产品数</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="spv in store.filteredSPVs"
          :key="spv.code"
          class="cursor-pointer"
          :class="{ 'bg-[rgba(59,158,255,0.04)]': store.activeSPV?.code === spv.code }"
          @click="store.selectSPV(spv)"
        >
          <td class="font-medium text-[#3B9EFF]">{{ spv.name }}</td>
          <td class="cursor-pointer text-[#3B9EFF] hover:underline" @click.stop="goToManager(spv.managerName)">{{ spv.managerName }}</td>
          <td><StatusTag :value="spv.strategyTag" /></td>
          <td class="num-cell">{{ spv.aum }}</td>
          <td><StatusTag :value="spv.riskLevel" /></td>
          <td class="num-cell">{{ spv.inceptionDate }}</td>
          <td><StatusTag :value="spv.status" /></td>
          <td class="num-cell">{{ spv.linkedProducts.length }}</td>
        </tr>
        <tr v-if="store.filteredSPVs.length === 0">
          <td class="empty" colspan="8">暂无匹配 SPV</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- 详情滑出面板 -->
  <SpvDetailPanel v-if="store.activeSPV" :spv="store.activeSPV" @close="store.clearActiveSPV()" />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusTag from '@esm/components/StatusTag.vue';
import SpvDetailPanel from '@esm/components/SpvDetailPanel.vue';
import { useSpvStore } from '@esm/store/spvStore';
import { useManagerStore } from '@esm/store/managerStore';
import { spvStatuses, spvRiskLevels } from '@esm/api/spv';

const route = useRoute();
const router = useRouter();
const store = useSpvStore();
const managerStore = useManagerStore();

function goToManager(name: string) {
  router.push({ path: '/esm/managers', query: { search: name } });
}

const lastUpdate = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) + ' 09:30';

onMounted(async () => {
  await Promise.all([store.load(), managerStore.load()]);
  if (route.query.search) store.searchQuery = route.query.search as string;
  if (route.query.strategy) store.selectedPoolStrategy = route.query.strategy as string;
});
</script>

