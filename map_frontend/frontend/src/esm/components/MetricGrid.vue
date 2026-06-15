<template>
  <section class="dashboard-metric-panel">
    <div v-if="metricGroups.length" class="space-y-2">
      <div v-for="group in metricGroups" :key="group.id" class="metric-group">
        <div class="metric-group-title">
          <span class="am-title-bar"></span>
          <span>{{ group.title }}</span>
        </div>
        <div :class="gridClass(group.columns)">
          <MetricCard
            v-for="item in group.items"
            :key="item.id ?? item.label"
            :item="item"
            @click="$emit('itemClick', item)"
          />
        </div>
      </div>
    </div>
    <div v-else :class="gridClass(columns)">
      <MetricCard
        v-for="item in cards"
        :key="item.id ?? item.label"
        :item="item"
        @click="$emit('itemClick', item)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h } from 'vue';
import { trendClass } from '@esm/utils/format';

interface MetricItem {
  id?: string;
  label: string;
  value: string;
  unit?: string;
  delta?: string;
  trend?: 'up' | 'down' | 'flat';
  desc?: string;
}

interface MetricGroup {
  id: string;
  title: string;
  columns: 3 | 4;
  items: MetricItem[];
}

const props = defineProps<{
  items?: MetricItem[];
  groups?: MetricGroup[];
  columns?: 3 | 4;
}>();

defineEmits<{
  itemClick: [item: MetricItem];
}>();

const cards = computed(() => props.items ?? []);
const metricGroups = computed(() => props.groups ?? []);
const columns = computed(() => props.columns ?? 4);

function gridClass(count: 3 | 4): string {
  return count === 3
    ? 'grid grid-cols-1 gap-2 lg:grid-cols-3'
    : 'grid grid-cols-2 gap-2 lg:grid-cols-4';
}

const MetricCard = defineComponent({
  props: {
    item: {
      type: Object as () => MetricItem,
      required: true,
    },
  },
  emits: ['click'],
  setup(cardProps, { emit }) {
    return () => h('article', { class: 'dashboard-metric-card cursor-pointer', onClick: () => emit('click') }, [
      h('div', { class: 'flex items-center justify-between gap-2 text-[12px] leading-4 text-[var(--am-text-3)]' }, [
        h('span', { class: 'truncate' }, cardProps.item.label),
        cardProps.item.delta
          ? h('span', { class: ['shrink-0 font-mono tabular-nums', trendClass(cardProps.item.trend ?? 'flat')] }, cardProps.item.delta)
          : null,
      ]),
      h('div', { class: 'mt-2 flex items-end gap-1' }, [
        h('span', { class: 'font-mono text-[22px] font-semibold leading-none tabular-nums text-[var(--am-text-1)]' }, cardProps.item.value),
        cardProps.item.unit
          ? h('span', { class: 'pb-0.5 text-[12px] leading-none text-[var(--am-text-3)]' }, cardProps.item.unit)
          : null,
      ]),
      cardProps.item.desc
        ? h('div', { class: 'mt-1 truncate text-[12px] leading-4 text-[var(--am-text-3)]' }, cardProps.item.desc)
        : null,
    ]);
  },
});
</script>

<style scoped>
.dashboard-metric-panel {
  border: 1px solid var(--am-border);
  border-radius: 8px;
  background: var(--am-bg-panel);
  padding: 10px;
}

.dashboard-metric-card {
  min-height: 86px;
  border: 1px solid var(--am-border-sub);
  border-radius: 6px;
  background: #1A1E2B;
  padding: 10px 12px;
  transition: background-color 150ms ease, border-color 150ms ease;
}

.dashboard-metric-card:hover {
  border-color: var(--am-border);
  background: #202431;
}

.metric-group {
  display: grid;
  gap: 6px;
}

.metric-group-title {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--am-text-3);
  font-size: 11px;
  font-weight: 700;
}
</style>

