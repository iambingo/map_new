<template>
  <section class="flex h-full min-h-[calc(100vh-64px)] flex-col gap-3 text-[#E8ECF4]">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[#2E3348] pb-3">
      <div class="flex min-w-0 items-center gap-2.5">
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-gradient-to-br from-[#3B9EFF] to-[#22D3EE] text-[11px] font-bold text-white shadow-[0_0_10px_rgba(59,158,255,0.25)]">
          ES
        </div>
        <div class="min-w-0">
          <h1 class="truncate text-[14px] font-bold tracking-wide text-[#F8FAFC]">外部策略管理</h1>
          <p class="mt-0.5 truncate font-mono text-[10px] uppercase tracking-widest text-[#555E75]">
            ESM / MOM / FOF / 委外策略闭环
          </p>
        </div>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <span class="inline-flex h-5 items-center rounded border border-[#3B9EFF]/25 bg-[#3B9EFF]/10 px-1.5 font-mono text-[10px] font-bold tracking-wide text-[#3B9EFF]">
          AUM 约 10,000 亿
        </span>
        <span class="inline-flex h-5 items-center rounded border border-[#2E3348] bg-[#181C28] px-1.5 font-mono text-[10px] tracking-wide text-[#94A3B8]">
          {{ today }}
        </span>
      </div>
    </div>

    <nav class="flex shrink-0 gap-1 overflow-x-auto border-b border-[#252A3A] pb-2 no-scrollbar">
      <button
        v-for="item in navItems"
        :key="item.name"
        type="button"
        :class="[
          'inline-flex h-8 shrink-0 items-center gap-1.5 rounded border px-2.5 text-xs font-medium transition-colors',
          isActive(item)
            ? 'border-[#3B9EFF]/30 bg-[#3B9EFF]/12 text-[#3B9EFF]'
            : 'border-transparent text-[#8B93A8] hover:bg-[#2A2E3D] hover:text-[#E8ECF4]',
        ]"
        @click="router.push({ name: item.name })"
      >
        <component :is="item.icon" class="h-3.5 w-3.5" />
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="min-h-0 flex-1">
      <router-view />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  Coin,
  Connection,
  DataAnalysis,
  DataBoard,
  Files,
  Medal,
  OfficeBuilding,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue';
import { ESM_ROUTE_NAMES } from '../router';

const route = useRoute();
const router = useRouter();

const navItems = [
  { name: ESM_ROUTE_NAMES.dashboard, label: '总览', icon: DataBoard, paths: ['/esm/dashboard'] },
  { name: ESM_ROUTE_NAMES.strategies, label: '策略库', icon: Files, paths: ['/esm/strategies'] },
  { name: ESM_ROUTE_NAMES.managers, label: '管理人库', icon: OfficeBuilding, paths: ['/esm/managers'] },
  { name: ESM_ROUTE_NAMES.spvPool, label: 'SPV 策略池', icon: Coin, paths: ['/esm/spv-pool'] },
  { name: ESM_ROUTE_NAMES.workflow, label: '准入流程', icon: Connection, paths: ['/esm/workflow'] },
  { name: ESM_ROUTE_NAMES.committee, label: '投委会', icon: UserFilled, paths: ['/esm/committee'] },
  { name: ESM_ROUTE_NAMES.kpi, label: 'KPI 评估', icon: DataAnalysis, paths: ['/esm/kpi'] },
  { name: ESM_ROUTE_NAMES.risk, label: '风险预警', icon: Warning, paths: ['/esm/risk'] },
  { name: ESM_ROUTE_NAMES.ratings, label: '评级体系', icon: Medal, paths: ['/esm/ratings'] },
];

const today = computed(() => new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
}));

function isActive(item: (typeof navItems)[number]): boolean {
  return item.paths.some((path) => route.path.startsWith(path));
}
</script>
