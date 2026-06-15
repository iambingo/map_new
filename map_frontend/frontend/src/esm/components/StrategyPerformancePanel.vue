<template>
  <div class="strategy-performance">
    <div v-if="strategy.performanceData.length === 0" class="empty-hint muted">暂无业绩数据</div>
    <template v-else>
      <div class="metrics-row">
        <div class="metric-card terminal-card">
          <label>累计净值</label>
          <strong class="mono">{{ latestNav }}</strong>
        </div>
        <div class="metric-card terminal-card">
          <label>累计收益</label>
          <strong :class="returnColor" class="mono">{{ cumulativeReturn }}</strong>
        </div>
        <div class="metric-card terminal-card">
          <label>超额收益</label>
          <strong :class="excessColor" class="mono">{{ excessReturn }}</strong>
        </div>
        <div class="metric-card terminal-card">
          <label>最大回撤</label>
          <strong class="text-red-400 mono">{{ maxDrawdown }}</strong>
        </div>
        <div class="metric-card terminal-card">
          <label>波动率</label>
          <strong class="mono">{{ strategy.volatility }}</strong>
        </div>
        <div class="metric-card terminal-card">
          <label>Sharpe</label>
          <strong class="mono">{{ sharpe }}</strong>
        </div>
      </div>

      <div ref="chartRef" class="nav-chart" />

      <div v-if="strategy.attribution.length" class="attribution-section">
        <h4 class="section-title">归因分析</h4>
        <div class="attr-grid">
          <div v-for="item in strategy.attribution" :key="item.factor" class="attr-bar terminal-card">
            <div class="attr-label">
              <strong>{{ item.factor }}</strong>
              <span class="mono">{{ (item.contribution * 100).toFixed(1) }}%</span>
            </div>
            <div class="attr-track">
              <div class="attr-fill" :style="{ width: (item.contribution * 100) + '%' }" />
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import type { Strategy } from '@esm/types/domain';

const props = defineProps<{ strategy: Strategy }>();

const chartRef = ref<HTMLElement>();
let chart: echarts.ECharts | null = null;

const latestNav = computed(() => {
  const d = props.strategy.performanceData;
  return d.length ? d[d.length - 1].nav.toFixed(4) : '—';
});

const cumulativeReturn = computed(() => {
  const d = props.strategy.performanceData;
  if (!d.length) return '—';
  const r = (d[d.length - 1].nav - 1) * 100;
  return (r >= 0 ? '+' : '') + r.toFixed(2) + '%';
});

const excessReturn = computed(() => {
  const d = props.strategy.performanceData;
  if (!d.length) return '—';
  const r = (d[d.length - 1].nav - d[d.length - 1].benchmark) * 100;
  return (r >= 0 ? '+' : '') + r.toFixed(2) + '%';
});

const returnColor = computed(() => {
  const d = props.strategy.performanceData;
  if (!d.length) return '';
  return d[d.length - 1].nav >= 1 ? 'text-green-400' : 'text-red-400';
});

const excessColor = computed(() => {
  const d = props.strategy.performanceData;
  if (!d.length) return '';
  return d[d.length - 1].nav >= d[d.length - 1].benchmark ? 'text-green-400' : 'text-red-400';
});

const maxDrawdown = computed(() => {
  const d = props.strategy.performanceData;
  if (!d.length) return '—';
  let peak = 0, mdd = 0;
  for (const p of d) {
    if (p.nav > peak) peak = p.nav;
    const dd = (peak - p.nav) / peak;
    if (dd > mdd) mdd = dd;
  }
  return '-' + (mdd * 100).toFixed(2) + '%';
});

const sharpe = computed(() => {
  const d = props.strategy.performanceData;
  if (d.length < 2) return '—';
  const returns = d.slice(1).map((p, i) => p.nav / d[i].nav - 1);
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const std = Math.sqrt(returns.reduce((s, r) => s + (r - mean) ** 2, 0) / returns.length);
  const annualized = mean * 12 / (std * Math.sqrt(12) || 1);
  return annualized.toFixed(2);
});

function renderChart() {
  if (!chartRef.value || !props.strategy.performanceData.length) return;
  if (!chart) chart = echarts.init(chartRef.value);

  const data = props.strategy.performanceData;
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { top: 30, right: 20, bottom: 30, left: 50 },
    tooltip: { trigger: 'axis', textStyle: { fontSize: 11 } },
    legend: { data: ['策略净值', '基准'], top: 4, textStyle: { fontSize: 11, color: '#888' } },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date),
      axisLabel: { fontSize: 10, color: '#555' },
      axisLine: { lineStyle: { color: '#333' } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 10, color: '#555' },
      splitLine: { lineStyle: { color: '#222' } },
    },
    series: [
      {
        name: '策略净值',
        type: 'line',
        data: data.map(d => d.nav),
        lineStyle: { color: '#3b9eff', width: 2 },
        itemStyle: { color: '#3b9eff' },
        symbol: 'none',
      },
      {
        name: '基准',
        type: 'line',
        data: data.map(d => d.benchmark),
        lineStyle: { color: '#666', width: 1, type: 'dashed' },
        itemStyle: { color: '#666' },
        symbol: 'none',
      },
    ],
  });
}

watch(() => props.strategy.performanceData, renderChart);
onMounted(renderChart);
onUnmounted(() => { chart?.dispose(); chart = null; });
</script>

<style scoped>
.strategy-performance { display: flex; flex-direction: column; gap: 16px; }
.empty-hint { padding: 12px 0; font-size: 12px; }

.metrics-row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
.metric-card { padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; }
.metric-card label { font-size: 10px; color: var(--am-text-3); }
.metric-card strong { font-size: 14px; }

.nav-chart { width: 100%; height: 280px; }

.attribution-section { border-top: 1px solid var(--am-border); padding-top: 12px; }
.section-title { font-size: 13px; font-weight: 600; color: var(--am-text-2); margin-bottom: 8px; }
.attr-grid { display: flex; flex-direction: column; gap: 6px; }
.attr-bar { padding: 8px 12px; }
.attr-label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; }
.attr-track { height: 4px; background: var(--am-border); border-radius: 2px; }
.attr-fill { height: 100%; background: var(--am-brand); border-radius: 2px; }
</style>

