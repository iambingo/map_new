<template>
  <div class="strategy-kpi">
    <div class="kpi-history" v-if="strategy.kpiHistory.length">
      <h4 class="section-title">历史评分</h4>
      <div class="history-list">
        <div v-for="rec in strategy.kpiHistory" :key="rec.period" class="history-card terminal-card">
          <div class="history-header">
            <strong>{{ rec.period }}</strong>
            <span class="status-tag" :class="'rating-' + rec.grade.toLowerCase()">{{ rec.grade }} 级</span>
          </div>
          <div class="history-scores">
            <span v-for="(s, i) in rec.scores" :key="i" class="dim-score">
              {{ scoreModel[i].name }} {{ s }}
            </span>
          </div>
          <div class="history-footer">
            <span class="total-score mono">{{ rec.totalScore.toFixed(1) }}</span>
            <span v-if="rec.evaluator" class="muted">评估人：{{ rec.evaluator }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-hint muted">暂无历史评分</div>

    <div class="kpi-form">
      <h4 class="section-title">新评分</h4>
      <div class="score-rows">
        <div v-for="(dim, i) in scoreModel" :key="dim.name" class="score-row">
          <div class="dim-info">
            <strong>{{ dim.name }}</strong>
            <span class="muted">权重 {{ dim.weight }}%</span>
          </div>
          <input v-model.number="scores[i]" class="input compact mono" type="number" min="0" max="100" />
          <input v-model="notes[i]" class="input note" placeholder="备注" />
        </div>
      </div>
      <div class="score-summary">
        <div class="summary-left">
          <span class="total-label">加权总分</span>
          <span class="total-value mono">{{ totalScore.toFixed(1) }}</span>
          <span class="status-tag" :class="'rating-' + grade(totalScore).toLowerCase()">{{ grade(totalScore) }} 级</span>
        </div>
        <button class="btn-primary" @click="handleSave">保存评分</button>
      </div>
      <svg class="radar" viewBox="0 0 240 240" role="img" aria-label="KPI 评分雷达图">
        <polygon points="110,28 188,85 158,177 62,177 32,85" fill="none" stroke="var(--am-border)" />
        <polygon points="110,55 162,93 142,154 78,154 58,93" fill="none" stroke="var(--am-border-sub)" />
        <g v-for="axis in radarAxes" :key="axis.label">
          <line :x1="110" :x2="axis.x" :y1="110" :y2="axis.y" stroke="var(--am-border-sub)" />
          <text :x="axis.lx" :y="axis.ly" fill="var(--am-text-3)" font-size="11" text-anchor="middle">{{ axis.label }}</text>
        </g>
        <polygon :points="radarPoints" fill="rgba(59, 158, 255, 0.2)" stroke="var(--am-brand)" stroke-width="2" />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Strategy } from '@esm/types/domain';

const props = defineProps<{ strategy: Strategy }>();
const emit = defineEmits<{ saveKpi: [scores: number[], totalScore: number, grade: string] }>();

const scoreModel = [
  { name: '收益贡献', weight: 30 },
  { name: '风险控制', weight: 30 },
  { name: '策略有效性', weight: 20 },
  { name: '研究能力', weight: 10 },
  { name: '平台建设', weight: 10 },
];

const scores = ref<number[]>([0, 0, 0, 0, 0]);
const notes = ref<string[]>([]);

const totalScore = computed(() =>
  scoreModel.reduce((sum, dim, i) => sum + (scores.value[i] || 0) * dim.weight / 100, 0),
);

function grade(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 75) return 'B';
  if (score >= 60) return 'C';
  return 'D';
}

const radarPoints = computed(() => {
  const cx = 110, cy = 110, max = 82;
  return scoreModel.map((_, i) => {
    const angle = -Math.PI / 2 + i * Math.PI * 2 / scoreModel.length;
    const r = max * (scores.value[i] || 0) / 100;
    return `${cx + Math.cos(angle) * r},${cy + Math.sin(angle) * r}`;
  }).join(' ');
});

const radarAxes = computed(() => {
  const cx = 110, cy = 110, max = 82;
  return scoreModel.map((dim, i) => {
    const angle = -Math.PI / 2 + i * Math.PI * 2 / scoreModel.length;
    return {
      label: dim.name,
      x: cx + Math.cos(angle) * max,
      y: cy + Math.sin(angle) * max,
      lx: cx + Math.cos(angle) * (max + 22),
      ly: cy + Math.sin(angle) * (max + 22),
    };
  });
});

function handleSave() {
  emit('saveKpi', [...scores.value], totalScore.value, grade(totalScore.value));
  scores.value = [0, 0, 0, 0, 0];
  notes.value = [];
}
</script>

<style scoped>
.strategy-kpi { display: flex; flex-direction: column; gap: 16px; }
.section-title { font-size: 13px; font-weight: 600; color: var(--am-text-2); margin-bottom: 8px; }
.history-list { display: flex; gap: 10px; overflow-x: auto; }
.history-card { min-width: 220px; padding: 10px 12px; flex-shrink: 0; }
.history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.history-scores { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 11px; color: var(--am-text-3); margin-bottom: 6px; }
.history-footer { display: flex; justify-content: space-between; align-items: center; font-size: 11px; }
.total-score { font-size: 14px; font-weight: 600; color: var(--am-brand); }
.empty-hint { padding: 12px 0; font-size: 12px; }

.kpi-form { border-top: 1px solid var(--am-border); padding-top: 12px; }
.score-rows { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.score-row { display: flex; align-items: center; gap: 12px; }
.dim-info { width: 140px; display: flex; justify-content: space-between; font-size: 12px; }
.compact { width: 64px; text-align: center; }
.note { flex: 1; }
.score-summary { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
.summary-left { display: flex; align-items: center; gap: 8px; }
.total-label { font-size: 12px; color: var(--am-text-3); }
.total-value { font-size: 18px; font-weight: 600; color: var(--am-brand); }
.radar { width: 200px; height: 200px; margin: 8px auto; display: block; }
.btn-primary { padding: 6px 16px; background: var(--am-brand); color: #fff; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; }
.btn-primary:hover { opacity: 0.9; }

.rating-a { color: #22c55e; background: rgba(34,197,94,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.rating-b { color: #3b9eff; background: rgba(59,158,255,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.rating-c { color: #f97316; background: rgba(249,115,22,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.rating-d { color: #ef4444; background: rgba(239,68,68,0.1); padding: 2px 8px; border-radius: 3px; font-size: 11px; }
</style>

