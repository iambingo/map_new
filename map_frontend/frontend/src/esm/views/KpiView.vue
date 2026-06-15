<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">KPI 评估体系</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">按收益贡献、风险控制、策略有效性、研究能力、平台建设自动加权评分。</p>
  </div>
  <div class="score-layout">
    <Panel>
      <div class="score-list">
        <div v-for="(item, index) in scoreModel" :key="item.name" class="score-row">
          <div>
            <strong>{{ item.name }}</strong>
            <div class="muted">{{ item.items.join(' / ') }}</div>
          </div>
          <span class="status-tag blue">权重 {{ item.weight }}%</span>
          <input v-model.number="scores[index]" class="input compact mono" max="100" min="0" type="number" />
          <input v-model="notes[index]" class="input note" placeholder="备注" />
        </div>
      </div>
    </Panel>
    <div class="terminal-card score-card">
      <span class="status-tag blue">自动计算</span>
      <div class="score-big mono">{{ totalScore.toFixed(1) }}</div>
      <div>综合等级：<StatusTag :value="grade(totalScore)" /></div>
      <svg class="radar" viewBox="0 0 240 240" role="img" aria-label="KPI 评分雷达图">
        <polygon points="110,28 188,85 158,177 62,177 32,85" fill="none" stroke="var(--am-border)" />
        <polygon points="110,55 162,93 142,154 78,154 58,93" fill="none" stroke="var(--am-border-sub)" />
        <g v-for="axis in radarAxes" :key="axis.label">
          <line :x1="110" :x2="axis.x" :y1="110" :y2="axis.y" stroke="var(--am-border-sub)" />
          <text :x="axis.lx" :y="axis.ly" fill="var(--am-text-3)" font-size="11" text-anchor="middle">{{ axis.label }}</text>
        </g>
        <polygon :points="radarPoints" fill="rgba(59, 158, 255, 0.2)" stroke="var(--am-brand)" stroke-width="2" />
      </svg>
      <p class="muted">评分规则：90 分以上 A，75-89 分 B，60-74 分 C，60 分以下 D。重大风险违规可一票否决。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import Panel from '@esm/components/Panel.vue';
import StatusTag from '@esm/components/StatusTag.vue';

const scoreModel = [
  { name: '收益贡献', weight: 30, items: ['超额收益 bp', 'Sharpe 比率', 'Calmar 比率', '信息比率 IR', '相对内部组合提升幅度'] },
  { name: '风险控制', weight: 30, items: ['最大回撤', '波动率', '止损触发情况', '流动性事件', '信用事件', '重大风险违规一票否决'] },
  { name: '策略有效性', weight: 20, items: ['风险分散能力', '相关性降低程度', '极端行情表现', '组合稳定性提升', '对冲效果'] },
  { name: '研究能力', weight: 10, items: ['深度报告质量', '策略跟踪频率', '市场观点输出', '数据分析能力', '尽调深度'] },
  { name: '平台建设', weight: 10, items: ['策略库建设', '管理人评级体系', '数据库与系统建设', '流程标准化', '知识沉淀与分享'] },
];

const scores = ref([86, 82, 88, 79, 84]);
const notes = ref<string[]>([]);

const totalScore = computed(() => scoreModel.reduce((sum, item, index) => sum + Number(scores.value[index] || 0) * item.weight / 100, 0));

const radarPoints = computed(() => {
  const cx = 110;
  const cy = 110;
  const max = 82;
  return scoreModel.map((_, index) => {
    const angle = -Math.PI / 2 + index * Math.PI * 2 / scoreModel.length;
    const radius = max * Number(scores.value[index] || 0) / 100;
    return `${cx + Math.cos(angle) * radius},${cy + Math.sin(angle) * radius}`;
  }).join(' ');
});

const radarAxes = computed(() => {
  const cx = 110;
  const cy = 110;
  const max = 82;
  return scoreModel.map((item, index) => {
    const angle = -Math.PI / 2 + index * Math.PI * 2 / scoreModel.length;
    return {
      label: item.name,
      x: cx + Math.cos(angle) * max,
      y: cy + Math.sin(angle) * max,
      lx: cx + Math.cos(angle) * (max + 22),
      ly: cy + Math.sin(angle) * (max + 22),
    };
  });
});

function grade(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 75) return 'B';
  if (score >= 60) return 'C';
  return 'D';
}
</script>

