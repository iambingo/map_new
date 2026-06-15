<script setup lang="ts">
import { reactive, computed, ref, onMounted } from 'vue'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import {
  UNIFIED_VOTE_CONFIG,
  calcTargetRange,
  committeeContextError,
  fetchCommitteeMeetingList,
  fetchCommitteePageData,
  resolveVotingMeetingId,
  submitVote,
  type UnifiedVoteConfigItem,
} from '@/store/demoStore'

function cn(...inputs: unknown[]) { return twMerge(clsx(inputs)) }

// ─── constants ────────────────────────────────────────────────────────────────
const SCORE_LABELS: Record<number, string> = {
  1: '谨慎', 2: '中性偏谨慎', 3: '中性', 4: '中性偏乐观', 5: '乐观',
}
// 2-字缩写：防止换行
const SCORE_LABELS_SHORT: Record<number, string> = {
  1: '谨慎', 2: '偏谨', 3: '中性', 4: '偏乐', 5: '乐观',
}

// A股惯例：红涨绿跌
// 激活态：高饱和色块 + 纯白文字
const SCORE_ACTIVE_BG: Record<number, string> = {
  1: 'bg-[#34C759]',
  2: 'bg-[#20C79A]',
  3: 'bg-[#3B9EFF]',
  4: 'bg-[#FF7A5C]',
  5: 'bg-[#F04864]',
}
// 提交摘要用颜色徽章
const SCORE_BADGE_COLORS: Record<number, string> = {
  1: 'bg-[#34C759]/15 border-[#34C759]/40 text-[#34C759]',
  2: 'bg-[#20C79A]/15 border-[#20C79A]/40 text-[#20C79A]',
  3: 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]',
  4: 'bg-[#FF7A5C]/15 border-[#FF7A5C]/40 text-[#FF7A5C]',
  5: 'bg-[#F04864]/15 border-[#F04864]/40 text-[#F04864]',
}

const TABS = ['固收', '含权', '另类'] as const
type TabKey = typeof TABS[number]

const TAB_ACCENT: Record<TabKey, string> = {
  '固收': '#3B9EFF',
  '含权': '#F04864',
  '另类': '#FFB800',
}

// ─── form state ───────────────────────────────────────────────────────────────
const formScores = reactive<Record<string, number>>(
  Object.fromEntries(UNIFIED_VOTE_CONFIG.map(c => [c.细分策略, 0])),
)
const formNewHigh = reactive<Record<string, boolean>>(
  Object.fromEntries(UNIFIED_VOTE_CONFIG.map(c => [c.细分策略, false])),
)
const formCoreView = ref('')

// ─── tab state ────────────────────────────────────────────────────────────────
const activeTab = ref<TabKey>('固收')

const tabItems = computed((): UnifiedVoteConfigItem[] =>
  UNIFIED_VOTE_CONFIG.filter(c => c.大类 === activeTab.value),
)

const tabCounts = computed(() =>
  Object.fromEntries(
    TABS.map(t => [t, UNIFIED_VOTE_CONFIG.filter(c => c.大类 === t).length]),
  ) as Record<TabKey, number>,
)

const tabAnswered = computed(() =>
  Object.fromEntries(
    TABS.map(t => [
      t,
      UNIFIED_VOTE_CONFIG
        .filter(c => c.大类 === t)
        .filter(c => formScores[c.细分策略] >= 1).length,
    ]),
  ) as Record<TabKey, number>,
)

// ─── global progress ──────────────────────────────────────────────────────────
const totalCount = UNIFIED_VOTE_CONFIG.length
const answeredCount = computed(() =>
  Object.values(formScores).filter(s => s >= 1 && s <= 5).length,
)
const progressPct = computed(() => Math.round((answeredCount.value / totalCount) * 100))
const canSubmit = computed(() => answeredCount.value === totalCount)

// ─── translation helpers ──────────────────────────────────────────────────────
function getAmplitudeText(cfg: UnifiedVoteConfigItem, score: number): string {
  if (!score) return '—'
  const label = SCORE_LABELS[score] as keyof typeof cfg.amplitude
  return cfg.amplitude[label] ?? '—'
}

function getTargetRangeText(cfg: UnifiedVoteConfigItem, score: number): string {
  if (!score) return '—'
  const amp = getAmplitudeText(cfg, score)
  const r = calcTargetRange(cfg.当前点位, amp)
  if (r.low === null && r.high !== null) return `≤ ${r.high}`
  if (r.high === null && r.low !== null) return `≥ ${r.low}`
  if (r.low !== null && r.high !== null) return `${r.low} — ${r.high}`
  return '—'
}

// ─── submission ───────────────────────────────────────────────────────────────
const submitting = ref(false)
const submitted = ref(false)
const submitError = ref('')
const pageReady = ref(false)

const urlMeetingId = (() => {
  const raw = new URLSearchParams(window.location.search).get('meeting_id')
  if (!raw) return null
  const parsed = parseInt(raw, 10)
  return Number.isNaN(parsed) ? null : parsed
})()

onMounted(async () => {
  await Promise.all([fetchCommitteePageData(), fetchCommitteeMeetingList()])
  pageReady.value = true
})

async function handleSubmit() {
  if (!canSubmit.value || submitting.value || !pageReady.value) return
  submitting.value = true
  submitError.value = ''

  const meetingId = resolveVotingMeetingId({ urlMeetingId })

  if (!meetingId) {
    submitError.value = committeeContextError.value
      ? `会议信息加载失败：${committeeContextError.value}`
      : '未找到可投票会议，请确认会议已创建'
    submitting.value = false
    return
  }

  const payload: Record<string, unknown> = {
    committee_type: 'mixed',
    vote_dimension: 'monthly',
    section_a: { ...formScores },
    section_b: { ...formNewHigh },
  }
  if (formCoreView.value.trim()) payload.core_view = formCoreView.value.trim()

  try {
    await submitVote(meetingId, payload)
    submitted.value = true
  } catch (err) {
    submitError.value = '提交失败，请稍后重试'
    console.error('[H5 Vote] 提交失败:', err)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <!-- ── 提交成功态 ── -->
  <div
    v-if="submitted"
    class="min-h-screen bg-slate-950 flex flex-col items-center justify-center px-6 gap-5"
  >
    <div class="w-14 h-14 rounded-full bg-[#34C759]/15 border border-[#34C759]/40 flex items-center justify-center">
      <svg class="w-7 h-7 text-[#34C759]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    </div>
    <div class="text-center">
      <div class="text-[20px] font-bold text-white">选票已提交</div>
      <div class="text-[12px] font-mono text-slate-400 mt-1">数据已同步至投委会系统</div>
    </div>
    <div class="w-full bg-slate-900 border border-slate-700/50 rounded-2xl p-4 space-y-2">
      <div class="text-[11px] font-mono text-slate-500 uppercase tracking-wider mb-3">提交摘要</div>
      <div
        v-for="cfg in UNIFIED_VOTE_CONFIG"
        :key="cfg.id"
        class="flex items-center justify-between py-0.5"
      >
        <span class="text-[13px] text-slate-300">{{ cfg.细分策略 }}</span>
        <span
          :class="cn(
            'text-[11px] font-bold font-mono px-2 py-0.5 rounded border',
            SCORE_BADGE_COLORS[formScores[cfg.细分策略]] || 'text-slate-500 border-slate-700',
          )"
        >
          {{ formScores[cfg.细分策略] }} · {{ SCORE_LABELS[formScores[cfg.细分策略]] }}
        </span>
      </div>
    </div>
  </div>

  <!-- ── 填报主界面 ── -->
  <div v-else class="min-h-screen bg-slate-950 font-sans pb-[calc(88px+env(safe-area-inset-bottom,0px))]">

    <!-- ── 顶部导航栏（固定） ── -->
    <div class="sticky top-0 z-30 bg-slate-950/95 backdrop-blur-md border-b border-slate-800 px-4 py-2.5 flex items-center justify-between">
      <div>
        <div class="text-[10px] font-mono text-slate-500 uppercase tracking-wider">月度资产观点评分</div>
        <div class="text-[15px] font-bold text-white mt-0.5">混合投委会 · H5 投票</div>
      </div>
      <div class="text-right">
        <div class="text-[10px] font-mono text-slate-500">必填进度</div>
        <div
          :class="cn(
            'text-[16px] font-mono font-bold tabular-nums',
            canSubmit ? 'text-[#34C759]' : 'text-[#3B9EFF]',
          )"
        >
          {{ answeredCount }}<span class="text-slate-700">/{{ totalCount }}</span>
        </div>
      </div>
    </div>

    <!-- ── 水平 Tab 切换器（吸顶，Header 下方） ── -->
    <div class="sticky top-[57px] z-20 bg-slate-950/95 backdrop-blur-md border-b border-slate-800 px-3">
      <div class="flex">
        <button
          v-for="tab in TABS"
          :key="tab"
          @click="activeTab = tab"
          :class="cn(
            'flex-1 py-2.5 text-[13px] font-bold tracking-wide transition-all duration-150 relative',
            activeTab === tab
              ? 'text-white'
              : 'text-slate-500 active:text-slate-300',
          )"
        >
          {{ tab }}
          <span
            :class="cn(
              'ml-1 text-[11px] font-mono',
              activeTab === tab ? 'text-slate-300' : 'text-slate-600',
            )"
          >{{ tabAnswered[tab] }}/{{ tabCounts[tab] }}</span>
          <!-- 活跃指示线 -->
          <span
            v-if="activeTab === tab"
            class="absolute bottom-0 left-1/2 -translate-x-1/2 h-[2px] w-10 rounded-full transition-all duration-200"
            :style="{ backgroundColor: TAB_ACCENT[tab] }"
          ></span>
        </button>
      </div>
    </div>

    <!-- ── 当前 Tab 的资产卡片列表 ── -->
    <div class="px-3 pt-3 pb-2 space-y-2.5">
      <div
        v-for="cfg in tabItems"
        :key="cfg.id"
        class="bg-slate-800 rounded-2xl border border-slate-700/50 overflow-hidden"
      >
        <!-- 卡片头部：单行 flex justify-between -->
        <div class="px-3 py-2 flex items-center justify-between border-b border-slate-700/40">
          <div class="font-bold text-[15px] text-white truncate mr-3">{{ cfg.细分策略 }}</div>
          <div class="text-right shrink-0">
            <div class="text-[11px] font-mono text-slate-300 leading-tight">{{ cfg.标的指数 }}</div>
            <div class="text-[12px] font-mono font-bold text-slate-200 tabular-nums leading-tight">
              {{ cfg.当前点位 }}
              <span class="text-[10px] font-normal text-slate-500 ml-0.5">
                {{ cfg.amplitudeType === 'bp' ? 'bp' : 'pt' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 打分器：5档横向 grid -->
        <div class="px-3 pt-2.5 pb-2">
          <div class="grid grid-cols-5 gap-1">
            <button
              v-for="n in 5"
              :key="n"
              @click="formScores[cfg.细分策略] = n"
              :class="cn(
                'h-10 rounded-xl border transition-all duration-150 flex flex-col items-center justify-center gap-px select-none active:scale-95',
                formScores[cfg.细分策略] === n
                  ? cn(SCORE_ACTIVE_BG[n], 'border-transparent text-white font-bold drop-shadow-sm')
                  : 'bg-slate-700 border-slate-600/50 text-slate-200',
              )"
            >
              <span class="text-[13px] font-bold font-mono leading-none">{{ n }}</span>
              <span class="text-[10px] leading-none opacity-90">{{ SCORE_LABELS_SHORT[n] }}</span>
            </button>
          </div>
        </div>

        <!-- 动态联动区：极低高度半透明胶囊 -->
        <div class="mx-3 mb-2.5 rounded-xl bg-white/5 border border-white/8 px-3 py-1.5 min-h-[28px] flex items-center">
          <template v-if="formScores[cfg.细分策略]">
            <span class="text-[10px] font-mono text-slate-400 mr-1.5">幅度</span>
            <span class="text-[11px] font-mono font-bold text-blue-300">
              {{ getAmplitudeText(cfg, formScores[cfg.细分策略]) }}
            </span>
            <span class="mx-2 text-slate-600">·</span>
            <span class="text-[10px] font-mono text-slate-400 mr-1.5">预期</span>
            <span class="text-[11px] font-mono font-bold text-blue-300 tabular-nums">
              {{ getTargetRangeText(cfg, formScores[cfg.细分策略]) }}
            </span>
            <span class="text-[10px] font-mono text-slate-500 ml-0.5">
              {{ cfg.amplitudeType === 'bp' ? '%(收益率)' : '点' }}
            </span>
          </template>
          <template v-else>
            <span class="text-[11px] font-mono text-slate-600">选择档位后显示观点幅度与预期区间</span>
          </template>
        </div>
      </div>
    </div>

    <!-- 核心观点文本（可选，固定在列表末尾） -->
    <div class="px-3 pt-1 pb-4">
      <div class="bg-slate-800 border border-slate-700/50 rounded-2xl overflow-hidden">
        <div class="px-3 py-2 flex items-center gap-2 border-b border-slate-700/40">
          <div class="w-[3px] h-3.5 bg-slate-500 rounded-full shrink-0"></div>
          <span class="text-[12px] font-mono text-slate-300 uppercase tracking-wider">核心观点（选填）</span>
        </div>
        <div class="p-3">
          <textarea
            v-model="formCoreView"
            rows="3"
            placeholder="请输入本期核心投资观点..."
            class="w-full bg-slate-900 border border-slate-700/50 rounded-xl px-3 py-2 text-[13px] text-white placeholder-slate-600 font-sans resize-none outline-none focus:border-blue-400/50 transition-colors"
          ></textarea>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div
      v-if="submitError"
      class="mx-3 mb-4 bg-[#F04864]/10 border border-[#F04864]/30 rounded-xl px-4 py-3 text-[13px] font-mono text-[#F04864]"
    >
      {{ submitError }}
    </div>

    <!-- ── 悬浮提交区（Sticky Footer） ── -->
    <div
      class="fixed bottom-0 left-0 right-0 z-40 bg-slate-950/96 backdrop-blur-md border-t border-slate-800 px-4 pt-3"
      style="padding-bottom: max(12px, env(safe-area-inset-bottom));"
    >
      <div class="flex items-center gap-3">

        <!-- 左侧：全局进度 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-[12px] font-mono text-slate-400">
              已评
              <span
                :class="cn('font-bold tabular-nums', canSubmit ? 'text-[#34C759]' : 'text-white')"
              >{{ answeredCount }}</span>
              <span class="text-slate-600">/{{ totalCount }}</span>
              项
            </span>
            <span
              :class="cn(
                'text-[11px] font-mono font-bold tabular-nums',
                canSubmit ? 'text-[#34C759]' : 'text-slate-500',
              )"
            >{{ progressPct }}%</span>
          </div>
          <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="canSubmit ? 'bg-[#34C759]' : 'bg-[#3B9EFF]'"
              :style="{ width: progressPct + '%' }"
            ></div>
          </div>
        </div>

        <!-- 右侧：提交按钮 -->
        <button
          @click="handleSubmit"
          :disabled="!canSubmit || submitting || !pageReady"
          :class="cn(
            'shrink-0 px-5 py-2.5 rounded-xl font-bold text-[13px] tracking-wide border transition-all duration-200 whitespace-nowrap',
            canSubmit && !submitting && pageReady
              ? 'bg-[#3B9EFF] border-[#3B9EFF] text-white active:scale-95 active:opacity-80'
              : 'bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed',
          )"
        >
          <span v-if="!pageReady" class="font-mono">加载中…</span>
          <span v-else-if="submitting" class="font-mono">提交中…</span>
          <span v-else>确认提交</span>
        </button>
      </div>
    </div>

  </div>
</template>
