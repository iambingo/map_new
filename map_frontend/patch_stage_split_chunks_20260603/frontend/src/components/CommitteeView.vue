﻿<template>
  <div class="flex flex-col h-full bg-[#161922] text-[#E8ECF4] overflow-hidden p-4 space-y-3">

    <!-- ═══ PORTAL: 会议选择中心 ═══ -->
    <div v-if="currentMeetingId == null" class="flex-1 flex flex-col items-center justify-center space-y-6">
      <div class="text-center space-y-2">
        <div class="w-2 h-12 bg-[#3B9EFF] rounded-sm mx-auto shadow-[0_0_24px_rgba(59,158,255,0.5)]"></div>
        <h1 class="text-xl font-bold text-white tracking-wider mt-3">投委会会议中心</h1>
        <p class="text-[13px] font-mono text-[#64748B]">Investment Committee Meeting Portal</p>
      </div>

      <div class="w-full max-w-2xl space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider">全部会议 ({{ meetingList.length }})</span>
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-2 border border-[#2E3348] rounded-lg px-2.5 py-1 bg-[#161922]">
              <span class="text-xs font-mono" :class="isGlobalMock ? 'text-[#3B9EFF]' : 'text-[#34C759]'">
                {{ isGlobalMock ? 'Mock 模式' : '联调模式' }}
              </span>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" class="sr-only peer" :checked="isGlobalMock" @change="(e) => toggleGlobalMock(e.target.checked)">
                <div class="w-8 h-4 rounded-full peer-focus:outline-none transition-colors duration-200"
                  :class="isGlobalMock ? 'bg-[#3B9EFF]' : 'bg-[#34C759]'">
                  <div class="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform duration-200 shadow-sm"
                    :class="isGlobalMock ? 'translate-x-4' : 'translate-x-0'"></div>
                </div>
              </label>
            </div>
            <button v-if="isSecretary" @click="quickCreateMeeting"
            class="text-[13px] px-3 py-1.5 rounded-lg border border-[#3B9EFF]/25 bg-[#3B9EFF]/10 text-[#3B9EFF] hover:bg-[#3B9EFF]/18 transition-colors flex items-center gap-1.5">
            <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div> 一键新增
          </button>
          </div>
        </div>
        <div class="space-y-2 max-h-[50vh] overflow-y-auto no-scrollbar">
          <div v-for="m in meetingList" :key="m.id"
            @click="enterMeeting(m.id)"
            class="bg-[#202431] border rounded-xl p-4 cursor-pointer hover:border-[#3B9EFF]/40 transition-all duration-200 group"
            :class="m.status === '进行中' ? 'border-[#3B9EFF]/30' : m.status === '已归档' ? 'border-[#252A3A]' : 'border-[#252A3A]'">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-2 h-2 rounded-full shrink-0"
                  :class="m.status === '进行中' ? 'bg-[#3B9EFF] animate-pulse' : m.status === '已归档' ? 'bg-[#6B7280]' : 'bg-[#3B9EFF]'"></div>
                <div>
                  <div class="text-[15px] font-semibold text-[#E8ECF4] group-hover:text-white transition-colors">{{ m.name }}</div>
                  <div class="text-[13px] font-mono text-[#64748B] mt-0.5">{{ m.date }} · {{ m.time }} · {{ m.location }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span :class="cn('text-xs font-mono px-2 py-1 rounded border',
                  m.status === '进行中' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]' :
                  m.status === '已归档' ? 'bg-[#6B7280]/10 border-[#2E3348] text-[#64748B]' :
                  m.status === '已结束' ? 'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]' :
                  'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]')">
                  {{ m.status }}
                </span>
                <button
                  v-if="isSecretary && m.status === '进行中'"
                  type="button"
                  @click.stop="deleteMeeting(m.id)"
                  class="text-xs font-mono px-2 py-1 rounded border border-[#F04864]/30 bg-[#F04864]/8 text-[#F97316] hover:bg-[#F04864]/15 hover:border-[#F04864]/45 transition-colors shrink-0"
                >
                  删除
                </button>
                <div class="w-0.5 h-4 rounded-full bg-[#4A5568] group-hover:bg-[#3B9EFF] transition-colors shrink-0"></div>
              </div>
            </div>
            <div v-if="m.decision" class="mt-2 text-[13px] font-mono text-[#94A3B8] truncate">{{ m.decision }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ MEETING DETAIL (原有内容) ═══ -->
    <template v-else>

    <!-- ═══ BFF 同步状态 / 离线 Mock ═══ -->
    <div
      v-if="committeeOfflineMock"
      class="shrink-0 text-xs font-mono px-3 py-2 rounded-lg border border-[#3B9EFF]/25 bg-[#1A1E2B] text-[#3B9EFF]"
    >
      离线 Mock（VITE_COMMITTEE_OFFLINE_MOCK）：未请求 portal-snapshot / page-context，决议表为前端默认数据。
    </div>
    <div
      v-else-if="portalSnapshotLoading || committeeContextLoading || portalSnapshotError || committeeContextError"
      class="shrink-0 text-xs font-mono px-3 py-2 rounded-lg border border-[#2E3348] bg-[#1A1E2B]"
      :class="(portalSnapshotError || committeeContextError) ? 'text-[#F97316] border-[#F97316]/25' : 'text-[#3B9EFF] border-[#3B9EFF]/20'"
    >
      <span v-if="portalSnapshotLoading || committeeContextLoading">正在从后端同步投委会数据（门户快照 + 会议上下文）…</span>
      <span v-else>
        <template v-if="portalSnapshotError">门户快照：{{ portalSnapshotError }}</template>
        <template v-if="portalSnapshotError && committeeContextError"> · </template>
        <template v-if="committeeContextError">投委会上下文：{{ committeeContextError }}</template>
      </span>
    </div>

    <!-- ═══ HEADER ═══ -->
    <div class="bg-gradient-to-r from-[#202431] to-[#1A1E2B] border border-[#2E3348] rounded-xl px-5 py-3.5 shrink-0 flex justify-between items-center shadow-[0_4px_24px_rgba(0,0,0,0.5)]">
      <div class="flex items-center space-x-4">
        <div class="w-1.5 h-8 bg-[#3B9EFF] rounded-sm shadow-[0_0_10px_rgba(59,158,255,0.3)] shrink-0"></div>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-base font-bold text-white tracking-wider">混合投资委员会</h2>
            <button @click="backToList" class="text-xs font-mono px-2 py-0.5 rounded border border-[#3B9EFF]/25 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 transition-colors flex items-center gap-1">
              切换会议
            </button>
            <button v-if="isSecretary" @click="handleQuickCreateAndEnter" class="text-xs font-mono px-2.5 py-0.5 rounded-lg border border-[#3B9EFF]/35 bg-[#3B9EFF]/12 text-[#3B9EFF] hover:bg-[#3B9EFF]/22 hover:border-[#3B9EFF]/55 transition-all flex items-center gap-1.5 shadow-[0_0_12px_rgba(59,158,255,0.15)]">
              <div class="w-0.5 h-3 bg-current rounded-sm shrink-0"></div> 一键新增会议
            </button>
            <span v-if="isViewingArchived" class="text-xs font-mono px-2 py-0.5 rounded border border-[#64748B]/25 bg-[#64748B]/10 text-[#64748B]">只读 · 历史归档</span>
          </div>
          <p class="text-xs text-[#94A3B8] mt-0.5 font-mono uppercase tracking-widest">{{ currentMeeting?.name ?? '2026 Q2 · 投资策略与TAA目标决议 · 全生命周期系统' }}</p>
        </div>
      </div>
      <div class="text-right space-y-2">
        <div class="flex items-center justify-end gap-2">
          <!-- Mock 切换开关 -->
          <div class="flex items-center gap-2 border border-[#2E3348] rounded-lg px-2.5 py-1 bg-[#161922]">
            <span class="text-xs font-mono" :class="isGlobalMock ? 'text-[#3B9EFF]' : 'text-[#34C759]'">
              {{ isGlobalMock ? 'Mock 模式' : '联调模式' }}
            </span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" class="sr-only peer" :checked="isGlobalMock" @change="(e) => toggleGlobalMock(e.target.checked)">
              <div class="w-8 h-4 rounded-full peer-focus:outline-none transition-colors duration-200"
                :class="isGlobalMock ? 'bg-[#3B9EFF]' : 'bg-[#34C759]'">
                <div class="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform duration-200 shadow-sm"
                  :class="isGlobalMock ? 'translate-x-4' : 'translate-x-0'"></div>
              </div>
            </label>
          </div>
          <!-- 当前角色标签 (由右上角个人中心统一切换) -->
          <div class="flex items-center gap-1.5 border border-[#2E3348] rounded-lg px-2.5 py-1 bg-[#161922]">
            <span class="text-xs font-mono text-[#4A5568]">当前视角</span>
            <span :class="cn('text-xs font-mono font-bold px-1.5 py-1 rounded border',
              isSecretary ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]' :
              isChairman  ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]' :
                            'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]')">
              {{ isSecretary ? '秘书' : isChairman ? '主任委员' : '委员' }}
            </span>
          </div>
          <!-- Recording Control (State Machine: idle / recording / paused / finished) -->
          <div class="flex items-center gap-1.5 border border-[#2E3348] rounded-lg px-2 py-1 bg-[#161922]">
            <!-- Timer -->
            <span class="text-[13px] font-mono tabular-nums min-w-[52px] text-center"
              :class="recState === 'recording' ? 'text-[#FF3B30] animate-pulse' : recState === 'paused' ? 'text-[#3B9EFF]' : recState === 'finished' ? 'text-[#3B9EFF]' : 'text-[#4A5568]'"
            >{{ recTimeDisplay }}</span>
            <div class="w-px h-4 bg-[#2E3348]"></div>
            <!-- Start / Resume -->
            <button @click="recStart"
              :disabled="recState === 'recording' || recState === 'finished'"
              :class="cn('w-7 h-7 flex items-center justify-center rounded transition-colors',
                recState === 'recording' ? 'opacity-40 cursor-not-allowed' : 'hover:bg-[#FF3B30]/15 cursor-pointer')"
            >
              <span class="w-2.5 h-2.5 rounded-full" :class="recState === 'idle' || recState === 'paused' ? 'bg-[#FF3B30]' : 'bg-[#FF3B30]/40'"></span>
            </button>
            <!-- Pause -->
            <button @click="recPause"
              :disabled="recState !== 'recording'"
              :class="cn('w-7 h-7 flex items-center justify-center rounded transition-colors',
                recState === 'recording' ? 'hover:bg-[#3B9EFF]/15 cursor-pointer' : 'opacity-40 cursor-not-allowed')"
            >
              <div class="flex items-center gap-[3px]">
                <div class="w-[3px] h-3 rounded-sm" :class="recState === 'recording' ? 'bg-[#3B9EFF]' : 'bg-[#3B9EFF]/40'"></div>
                <div class="w-[3px] h-3 rounded-sm" :class="recState === 'recording' ? 'bg-[#3B9EFF]' : 'bg-[#3B9EFF]/40'"></div>
              </div>
            </button>
            <!-- Stop -->
            <button @click="recStop"
              :disabled="recState !== 'recording' && recState !== 'paused'"
              :class="cn('w-7 h-7 flex items-center justify-center rounded transition-colors',
                recState === 'recording' || recState === 'paused' ? 'hover:bg-[#3B9EFF]/15 cursor-pointer' : 'opacity-40 cursor-not-allowed')"
            >
              <div class="w-2.5 h-2.5 rounded-[2px]" :class="recState === 'recording' || recState === 'paused' ? 'bg-[#3B9EFF]' : 'bg-[#3B9EFF]/40'"></div>
            </button>
          </div>
        </div>
        <div class="flex items-center justify-end gap-2">
          <div class="text-xs font-mono text-[#94A3B8] bg-[#1A1E2B] border border-[#252A3A] px-3 py-1.5 rounded-lg">
            会议编号 <span class="text-[#3B9EFF]">{{ meetingHeaderCode }}</span> · {{ meetingHeaderDate }}
          </div>
          <button
            v-if="isSecretary"
            @click="showMeetingDrawer = true"
            class="flex items-center gap-1.5 text-[13px] px-2.5 py-1.5 rounded-lg border border-[#3B9EFF]/25 bg-[#3B9EFF]/10 text-[#3B9EFF] hover:bg-[#3B9EFF]/18 transition-colors"
          >
            <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div> 会议管理
          </button>
        </div>
        <div class="flex items-center justify-end space-x-3 mt-1">
          <span class="text-xs font-mono text-[#94A3B8]">问卷回收 {{ submittedCount }} / {{ voteProgressTotal }}</span>
          <div class="w-20 h-1 bg-[#1A1E2B] rounded-full overflow-hidden">
            <div class="h-full bg-[#3B9EFF] rounded-full transition-all duration-500" :style="{ width: `${voteProgressPct}%` }"></div>
          </div>
          <span class="text-xs font-mono" :class="voteProgressComplete ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">{{ voteProgressComplete ? '全员完成' : '收集中' }}</span>
        </div>
      </div>
    </div>

    <!-- ═══ 录音状态横幅（会议记录中） ═══ -->
    <div v-if="recState === 'recording' || recState === 'paused'"
      class="shrink-0 flex items-center justify-center gap-3 py-1.5 rounded-lg border transition-all duration-300"
      :class="recState === 'recording'
        ? 'bg-[#FF3B30]/8 border-[#FF3B30]/25'
        : 'bg-[#3B9EFF]/8 border-[#3B9EFF]/25'">
      <div class="w-2 h-2 rounded-full animate-pulse" :class="recState === 'recording' ? 'bg-[#FF3B30]' : 'bg-[#3B9EFF]'"></div>
      <span class="text-xs font-mono font-bold" :class="recState === 'recording' ? 'text-[#FF3B30]' : 'text-[#3B9EFF]'">
        {{ recState === 'recording' ? '会议记录中' : '录音已暂停' }}
      </span>
      <span class="text-xs font-mono tabular-nums" :class="recState === 'recording' ? 'text-[#FF3B30]/70' : 'text-[#3B9EFF]/70'">{{ recTimeDisplay }}</span>
      <span class="text-xs font-mono text-[#64748B]">|</span>
      <span class="text-xs font-mono text-[#94A3B8]">本录音仅用于会议纪要生成，录音结束后将自动转写</span>
    </div>

    <!-- ═══ LEFT SIDEBAR + MAIN CONTENT ═══ -->
    <div class="flex-1 flex flex-row min-h-0">

      <!-- LEFT SIDEBAR -->
      <div class="w-[200px] shrink-0 bg-[#1A1E2B] border-r border-[#252A3A] flex flex-col py-3">
        <div v-for="tab in TAB_ITEMS" :key="tab.key"
          @click="activeTab = tab.key"
          :class="cn(
            'flex items-center space-x-3 px-4 py-3 cursor-pointer transition-all duration-150 border-l-4',
            activeTab === tab.key
              ? 'bg-[#3B9EFF]/10 border-[#3B9EFF] text-white'
              : 'border-transparent text-[#6B7280] hover:bg-[#252A3A]/50 hover:text-[#94A3B8]'
          )"
        >
          <span class="text-[11px] font-mono font-bold w-5 h-5 rounded flex items-center justify-center shrink-0"
            :class="activeTab === tab.key ? 'bg-[#3B9EFF] text-white' : 'bg-[#252A3A] text-[#6B7280]'">{{ tab.step }}</span>
          <span class="text-[13px] font-medium">{{ tab.label }}</span>
        </div>
      </div>

      <!-- MAIN CONTENT -->
      <div ref="mainScrollRef" class="flex-1 overflow-y-auto no-scrollbar bg-[#161922] p-4" @scroll="onMainScroll">

      <!-- ════════════════════════════════════════════════════════════
           STEP 0: 会前筹备与填报 (角色感知)
      ════════════════════════════════════════════════════════════ -->

      <!-- ════════════════════════════════════════════════════════════
           市场及产品表现回顾 (market_macro)
      ════════════════════════════════════════════════════════════ -->
      <div v-if="activeTab === 'market_macro'" class="space-y-4 pb-4">

        <!-- ──────────────────────────────────────────────────────────
             A. 宏观环境全景
        ────────────────────────────────────────────────────────── -->
        <div id="nav-macro-env" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>宏观环境全景</h3>
            <span class="text-xs font-mono text-[#94A3B8] bg-[#1A1E2B] px-2.5 py-1 rounded border border-[#252A3A]">数据截至 2026-04-30</span>
          </div>
          <div class="p-5 grid grid-cols-4 gap-3">
            <div
              v-for="ind in MACRO_INDICATORS" :key="ind.name"
              class="bg-[#1A1E2B] rounded-lg p-3.5 space-y-2 transition-colors hover:border-[#3B9EFF]/20"
              :class="ind.highlight ? 'border border-[#3B9EFF]/25' : 'border border-[#252A3A]'"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs font-mono text-[#94A3B8] truncate">{{ ind.name }}</span>
                <span
                  class="text-[10px] font-mono px-1.5 py-0.5 rounded border shrink-0"
                  :class="ind.trendDir === 'up'   ? 'bg-[#F04864]/10 border-[#F04864]/30 text-[#F04864]'
                        : ind.trendDir === 'down' ? 'bg-[#00C9A7]/10 border-[#00C9A7]/30 text-[#00C9A7]'
                        :                          'bg-[#3B9EFF]/10 border-[#3B9EFF]/30 text-[#3B9EFF]'"
                >{{ ind.trend }}</span>
              </div>
              <div class="flex items-baseline gap-1">
                <span class="text-[22px] font-mono font-bold tabular-nums text-white leading-none">{{ ind.value }}</span>
                <span class="text-[11px] font-mono text-[#64748B]">{{ ind.unit }}</span>
              </div>
              <div class="text-[11px] font-mono text-[#64748B] leading-relaxed">{{ ind.note }}</div>
            </div>
          </div>
        </div>

        <!-- ──────────────────────────────────────────────────────────
             B. 全资产估值水位与业绩看板 (TreeGrid)
        ────────────────────────────────────────────────────────── -->
        <div id="nav-asset-val" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>全资产估值水位与业绩看板</h3>
            <button
              class="flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded border border-[#3B9EFF]/30 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 transition-colors"
            >
              <div class="w-0.5 h-3 bg-current rounded-sm shrink-0"></div>
              导出数据 (Excel)
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full table-fixed font-mono text-xs border-collapse" style="min-width:900px">
              <colgroup>
                <col style="width:160px" />
                <col style="width:88px" />
                <col style="width:96px" />
                <col style="width:96px" />
                <col style="width:80px" />
                <col style="width:80px" />
                <col style="width:80px" />
                <col style="width:72px" />
                <col style="width:72px" />
                <col style="width:100px" />
              </colgroup>
              <thead class="bg-[#1A1E2B] border-b border-[#2E3348] sticky top-0 z-10">
                <tr>
                  <th class="px-4 py-2.5 text-left text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">资产名称</th>
                  <th class="px-3 py-2.5 text-right text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">当前点位</th>
                  <th class="px-3 py-2.5 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">近 5 年分位</th>
                  <th class="px-3 py-2.5 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">近 10 年分位</th>
                  <th class="px-3 py-2.5 text-right text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">本月</th>
                  <th class="px-3 py-2.5 text-right text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">YTD</th>
                  <th class="px-3 py-2.5 text-right text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">最大回撤</th>
                  <th class="px-3 py-2.5 text-right text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">夏普</th>
                  <th class="px-3 py-2.5 text-right text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">卡玛</th>
                  <th class="px-3 py-2.5 text-center text-xs font-bold text-[#94A3B8]">近一年走势</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <template v-for="grp in ASSET_VALUATION_GROUPS" :key="grp.key">
                  <!-- 分组行 (可折叠) -->
                  <tr
                    class="bg-[#1A1E2B]/70 cursor-pointer hover:bg-[#252A3A]/60 transition-colors select-none"
                    @click="toggleAssetGroup(grp.key)"
                  >
                    <td class="px-4 py-2 border-r border-[#2E3348]" colspan="1">
                      <div class="flex items-center gap-2">
                        <div class="w-1 h-3.5 rounded-sm bg-[#3B9EFF] shrink-0"></div>
                        <span class="text-xs font-bold text-[#E8ECF4]">{{ grp.label }}</span>
                        <span class="text-xs font-mono text-[#4A5568]">({{ grp.items.length }})</span>
                        <div
                          class="ml-auto w-3.5 h-3.5 flex items-center justify-center transition-transform duration-150"
                          :class="expandedAssetGroups[grp.key] ? 'rotate-90' : ''"
                        >
                          <div class="w-0 h-0 border-t-[4px] border-t-transparent border-b-[4px] border-b-transparent border-l-[6px] border-l-[#64748B]"></div>
                        </div>
                      </div>
                    </td>
                    <td colspan="9" class="px-3 py-2 text-xs text-[#4A5568]">
                      {{ expandedAssetGroups[grp.key] ? '点击收起' : '点击展开' }}
                    </td>
                  </tr>
                  <!-- 子行 -->
                  <template v-if="expandedAssetGroups[grp.key]">
                    <tr
                      v-for="row in grp.items" :key="row.name"
                      class="hover:bg-[#1A1E2B]/40 transition-colors"
                    >
                      <td class="px-4 py-2 pl-8 text-xs text-[#E8ECF4] border-r border-[#252A3A]">{{ row.name }}</td>
                      <td class="px-3 py-2 text-right tabular-nums text-[#B4BAC9] border-r border-[#252A3A]">{{ row.point }}</td>
                      <!-- 近5年分位水位条 -->
                      <td class="px-3 py-2 border-r border-[#252A3A]">
                        <div class="flex items-center gap-1.5">
                          <div class="flex-1 h-1.5 bg-[#161922] rounded-full overflow-hidden">
                            <div
                              class="h-full rounded-full transition-all duration-300"
                              :style="{ width: `${row.pct5y}%` }"
                              :class="row.pct5y >= 70 ? 'bg-[#F04864]' : row.pct5y >= 40 ? 'bg-[#3B9EFF]' : 'bg-[#00C9A7]'"
                            ></div>
                          </div>
                          <span class="tabular-nums text-xs w-8 text-right shrink-0"
                            :class="row.pct5y >= 70 ? 'text-[#F04864]' : row.pct5y >= 40 ? 'text-[#3B9EFF]' : 'text-[#00C9A7]'">
                            {{ row.pct5y }}%
                          </span>
                        </div>
                      </td>
                      <!-- 近10年分位水位条 -->
                      <td class="px-3 py-2 border-r border-[#252A3A]">
                        <template v-if="row.pct10y !== null">
                          <div class="flex items-center gap-1.5">
                            <div class="flex-1 h-1.5 bg-[#161922] rounded-full overflow-hidden">
                              <div
                                class="h-full rounded-full transition-all duration-300"
                                :style="{ width: `${row.pct10y}%` }"
                                :class="row.pct10y >= 70 ? 'bg-[#F04864]' : row.pct10y >= 40 ? 'bg-[#3B9EFF]' : 'bg-[#00C9A7]'"
                              ></div>
                            </div>
                            <span class="tabular-nums text-xs w-8 text-right shrink-0"
                              :class="row.pct10y >= 70 ? 'text-[#F04864]' : row.pct10y >= 40 ? 'text-[#3B9EFF]' : 'text-[#00C9A7]'">
                              {{ row.pct10y }}%
                            </span>
                          </div>
                        </template>
                        <span v-else class="text-[#4A5568] text-xs">N/A</span>
                      </td>
                      <!-- 本月收益 -->
                      <td class="px-3 py-2 text-right tabular-nums font-bold border-r border-[#252A3A]"
                        :class="row.retMonth > 0 ? 'text-[#F04864]' : row.retMonth < 0 ? 'text-[#00C9A7]' : 'text-[#94A3B8]'">
                        {{ row.retMonth > 0 ? '+' : '' }}{{ row.retMonth.toFixed(2) }}%
                      </td>
                      <!-- YTD -->
                      <td class="px-3 py-2 text-right tabular-nums font-bold border-r border-[#252A3A]"
                        :class="row.retYtd > 0 ? 'text-[#F04864]' : row.retYtd < 0 ? 'text-[#00C9A7]' : 'text-[#94A3B8]'">
                        {{ row.retYtd > 0 ? '+' : '' }}{{ row.retYtd.toFixed(2) }}%
                      </td>
                      <!-- 最大回撤 -->
                      <td class="px-3 py-2 text-right tabular-nums text-[#00C9A7] border-r border-[#252A3A]">
                        {{ row.maxdd.toFixed(1) }}%
                      </td>
                      <!-- 夏普 -->
                      <td class="px-3 py-2 text-right tabular-nums border-r border-[#252A3A]"
                        :class="row.sharpe >= 1 ? 'text-[#F04864]' : row.sharpe >= 0.5 ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">
                        {{ row.sharpe.toFixed(2) }}
                      </td>
                      <!-- 卡玛 -->
                      <td class="px-3 py-2 text-right tabular-nums border-r border-[#252A3A]"
                        :class="row.calmar >= 1 ? 'text-[#F04864]' : row.calmar >= 0.5 ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">
                        {{ row.calmar.toFixed(2) }}
                      </td>
                      <!-- 近一年走势 Sparkline（点击查看大图） -->
                      <td class="px-2 py-2 cursor-pointer group" @click="openSparklineModal(row)" title="点击查看完整走势图">
                        <svg :viewBox="'0 0 ' + (row.trend.length - 1) * 8 + ' 24'" class="w-full h-6 group-hover:opacity-70 transition-opacity" preserveAspectRatio="none">
                          <polyline fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                            :stroke="row.retYtd >= 0 ? '#F04864' : '#00C9A7'"
                            :points="row.trend.map((v, i) => {
                              const mn = Math.min(...row.trend);
                              const mx = Math.max(...row.trend);
                              const range = mx - mn || 1;
                              const x = i * 8;
                              const y = 24 - ((v - mn) / range) * 20 - 2;
                              return x + ',' + y;
                            }).join(' ')"
                          />
                        </svg>
                      </td>
                    </tr>
                  </template>
                </template>
              </tbody>
            </table>
          </div>
          <div class="px-5 py-2 border-t border-[#252A3A] bg-[#161922] flex items-center gap-6 text-xs font-mono text-[#4A5568]">
            <span>分位水位：<span class="text-[#F04864]">红 &ge;70%</span> 偏贵 · <span class="text-[#3B9EFF]">蓝 40-70%</span> 中性 · <span class="text-[#00C9A7]">绿 &lt;40%</span> 偏低</span>
            <span class="ml-auto">收益率：<span class="text-[#F04864]">红 = 上涨</span> · <span class="text-[#00C9A7]">绿 = 下跌</span> · 夏普/卡玛：红 &ge;1.0 优秀</span>
          </div>
        </div>

        <!-- ──────────────────────────────────────────────────────────
             C. 委员投票回顾与偏差评估 (GAP-2 增强)
        ────────────────────────────────────────────────────────── -->
        <div id="nav-vote-review" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>委员投票回顾与偏差评估</h3>
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono text-[#94A3B8]">上期 2026 Q1 · 复盘区间 2025-12-20 — 2026-03-28</span>
              <span class="text-xs font-mono px-2 py-1 rounded border border-[#3B9EFF]/30 bg-[#3B9EFF]/8 text-[#3B9EFF]">群体准确率 {{ COMMITTEE_ACCURACY_SCORE }}%</span>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full table-fixed font-mono text-xs border-collapse" style="min-width:760px">
              <colgroup>
                <col style="width:120px" />
                <col style="width:90px" />
                <col style="width:90px" />
                <col style="width:110px" />
                <col style="width:80px" />
                <col style="width:90px" />
              </colgroup>
              <thead class="bg-[#1A1E2B] border-b border-[#2E3348]">
                <tr>
                  <th class="px-4 py-2.5 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">核心资产</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">上期均值</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">方向判断</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">实际表现</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">偏离度</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8]">评估</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr
                  v-for="row in COMMITTEE_VOTE_REVIEW_ROWS" :key="row.asset"
                  class="hover:bg-[#1A1E2B]/40 transition-colors"
                  :class="row.verdict === '方向偏差' ? 'bg-[#F04864]/3' : row.verdict === '显著超额' ? 'bg-[#F04864]/4' : ''"
                >
                  <td class="px-4 py-2.5 font-semibold text-[#E8ECF4] border-r border-[#252A3A]">{{ row.asset }}</td>
                  <td class="px-3 py-2.5 text-center border-r border-[#252A3A]">
                    <div class="flex flex-col items-center gap-0.5">
                      <span class="tabular-nums font-bold text-[#E8ECF4]">{{ row.avgScore.toFixed(1) }}</span>
                      <span class="text-[10px] text-[#94A3B8]">{{ row.scoreLabel }}</span>
                    </div>
                  </td>
                  <td class="px-3 py-2.5 text-center border-r border-[#252A3A]">
                    <span class="text-xs px-2 py-0.5 rounded border font-mono"
                      :class="row.avgScore >= 3.5 ? 'bg-[#F04864]/10 border-[#F04864]/30 text-[#F04864]'
                             : row.avgScore <= 2.5 ? 'bg-[#00C9A7]/10 border-[#00C9A7]/30 text-[#00C9A7]'
                             : 'bg-[#3B9EFF]/10 border-[#3B9EFF]/30 text-[#3B9EFF]'">
                      {{ row.avgScore >= 3.5 ? '上行' : row.avgScore <= 2.5 ? '下行' : '震荡' }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-center tabular-nums font-bold border-r border-[#252A3A]"
                    :class="row.actualChange > 0 ? 'text-[#F04864]' : row.actualChange < 0 ? 'text-[#00C9A7]' : 'text-[#94A3B8]'">
                    {{ row.changeStr }}
                  </td>
                  <td class="px-3 py-2.5 text-center border-r border-[#252A3A]">
                    <span class="text-[10px] font-mono px-1.5 py-0.5 rounded border"
                      :class="row.deviationLevel === '极低' ? 'bg-[#F04864]/10 border-[#F04864]/30 text-[#F04864]'
                             : row.deviationLevel === '低' ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/30 text-[#3B9EFF]'
                             : 'bg-[#FFAB00]/10 border-[#FFAB00]/30 text-[#FFAB00]'">
                      {{ row.deviationLevel }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-center">
                    <span class="text-xs font-bold"
                      :class="row.verdict === '方向正确' || row.verdict === '显著超额' ? 'text-[#F04864]'
                             : row.verdict === '方向偏差' ? 'text-[#00C9A7]'
                             : 'text-[#3B9EFF]'">
                      {{ row.verdict }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- 偏离度说明 -->
          <div class="px-5 py-3 border-t border-[#252A3A] bg-[#1A1E2B]/40 grid grid-cols-3 gap-4 text-[11px] font-mono text-[#64748B]">
            <div>
              <span class="text-[#94A3B8] font-bold">偏离度定义：</span>委员均值与实际走势的方向匹配程度。极低偏离 = 判断高度一致；高偏离 = 群体预判有误差。
            </div>
            <div class="flex items-center justify-center gap-4">
              <span><span class="text-[#F04864]">极低</span> = 强匹配</span>
              <span><span class="text-[#3B9EFF]">低</span> = 方向正确</span>
              <span><span class="text-[#FFAB00]">高</span> = 预判偏差</span>
            </div>
            <div class="text-right">
              本期群体准确率 <span class="text-[#3B9EFF] font-bold tabular-nums">{{ COMMITTEE_ACCURACY_SCORE }}%</span>（{{ COMMITTEE_VOTE_REVIEW_ROWS.filter(r => r.verdict !== '方向偏差').length }}/{{ COMMITTEE_VOTE_REVIEW_ROWS.length }} 项正确）
            </div>
          </div>
        </div>

        <!-- ──────────────────────────────────────────────────────────
             D. 指引价值复盘：指引 vs 市场走势
        ────────────────────────────────────────────────────────── -->
        <div id="nav-guidance-val" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>指引价值复盘：指引 vs 市场走势</h3>
          </div>
          <div class="p-5 space-y-5">
            <!-- 三大基准时间轴 -->
            <div v-for="bench in GUIDANCE_BENCHMARKS" :key="bench.key" class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl overflow-hidden">
              <div class="px-4 py-3 border-b border-[#252A3A] flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-0.5 h-4 rounded-sm bg-[#3B9EFF]/70 shrink-0"></div>
                  <span class="text-[13px] font-medium text-[#E8ECF4]">{{ bench.name }}</span>
                </div>
                <!-- 指引有效性评分 -->
                <div class="flex items-center gap-2">
                  <span class="text-[11px] font-mono text-[#64748B]">指引有效性评分</span>
                  <div class="flex items-center gap-1.5">
                    <div class="w-20 h-1.5 bg-[#161922] rounded-full overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all duration-500"
                        :style="{ width: `${bench.score}%` }"
                        :class="bench.score >= 80 ? 'bg-[#F04864]' : bench.score >= 60 ? 'bg-[#3B9EFF]' : 'bg-[#FFAB00]'"
                      ></div>
                    </div>
                    <span
                      class="text-sm font-bold font-mono tabular-nums"
                      :class="bench.score >= 80 ? 'text-[#F04864]' : bench.score >= 60 ? 'text-[#3B9EFF]' : 'text-[#FFAB00]'"
                    >{{ bench.score }}%</span>
                  </div>
                </div>
              </div>
              <!-- 时间轴行 -->
              <div class="flex">
                <div v-for="(row, idx) in bench.rows" :key="idx"
                  class="flex-1 px-3 py-3 border-r border-[#252A3A] last:border-r-0 space-y-2">
                  <div class="text-xs font-mono text-[#4A5568] text-center">{{ row.period }}</div>
                  <!-- 指引气泡 -->
                  <div class="flex justify-center">
                    <span
                      class="text-[10px] font-mono px-2 py-0.5 rounded-full border"
                      :class="row.guidance === '乐观' || row.guidance === '偏乐观'
                        ? 'bg-[#F04864]/10 border-[#F04864]/30 text-[#F04864]'
                        : row.guidance === '谨慎' || row.guidance === '偏谨慎'
                        ? 'bg-[#00C9A7]/10 border-[#00C9A7]/30 text-[#00C9A7]'
                        : 'bg-[#3B9EFF]/10 border-[#3B9EFF]/30 text-[#3B9EFF]'"
                    >{{ row.guidance }}</span>
                  </div>
                  <!-- 连接线 -->
                  <div class="flex justify-center">
                    <div class="w-px h-4 bg-[#252A3A]"></div>
                  </div>
                  <!-- 实际走势 -->
                  <div class="text-center">
                    <span
                      v-if="row.actualChange !== '-'"
                      class="text-xs font-mono font-bold tabular-nums"
                      :class="row.actualChange.startsWith('+') ? 'text-[#F04864]'
                             : row.actualChange.startsWith('-') ? 'text-[#00C9A7]'
                             : 'text-[#94A3B8]'"
                    >{{ row.actualChange }}</span>
                    <span v-else class="text-xs font-mono text-[#4A5568]">进行中</span>
                  </div>
                  <!-- 匹配标记 -->
                  <div class="flex justify-center">
                    <span
                      v-if="row.actualChange !== '-'"
                      class="text-[10px] font-mono"
                      :class="row.match ? 'text-[#F04864]' : 'text-[#00C9A7]'"
                    >{{ row.match ? '匹配' : '偏差' }}</span>
                    <span v-else class="text-xs font-mono text-[#4A5568]">—</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 综合结论 -->
            <div class="bg-[#0D1520] border border-[#3B9EFF]/20 rounded-xl p-4 grid grid-cols-3 gap-6">
              <div v-for="bench in GUIDANCE_BENCHMARKS" :key="bench.key + '_summary'" class="space-y-2">
                <div class="flex items-center gap-1.5">
                  <div class="w-0.5 h-3.5 rounded-sm bg-[#3B9EFF]/70 shrink-0"></div>
                  <span class="text-xs font-mono text-[#94A3B8]">{{ bench.name }}</span>
                </div>
                <div class="flex items-baseline gap-2">
                  <span
                    class="text-3xl font-mono font-bold tabular-nums"
                    :class="bench.score >= 80 ? 'text-[#F04864]' : bench.score >= 60 ? 'text-[#3B9EFF]' : 'text-[#FFAB00]'"
                  >{{ bench.score }}%</span>
                  <span class="text-xs font-mono text-[#64748B]">指引有效率</span>
                </div>
                <div class="text-[11px] font-mono text-[#64748B]">
                  {{ bench.rows.filter(r => r.actualChange !== '-' && r.match).length }}/{{ bench.rows.filter(r => r.actualChange !== '-').length }} 期指引方向正确
                </div>
              </div>
            </div>
          </div>
          <!-- 行情+信号图：万得全A走势与投委会指引标记 -->
          <div class="p-4">
            <div class="text-xs font-mono text-[#94A3B8] mb-2">万得全A 近一年走势与投委会指引信号</div>
            <div ref="guidanceChartRef" style="height:240px;width:100%"></div>
          </div>
        </div>

      </div><!-- end market_macro -->

      <!-- ── 委员观点 · 顶部子视角切换 (全角色共享) ── -->
      <div v-if="activeTab === 'member_views'" class="flex items-center gap-2">
        <div class="inline-flex bg-[#161922] border border-[#252A3A] rounded-lg p-0.5 gap-0.5">
          <button
            @click="memberViewsSubTab = 'committee_stats'"
            :class="['px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all duration-150',
              memberViewsSubTab === 'committee_stats'
                ? 'bg-[#3B9EFF]/12 border border-[#3B9EFF]/30 text-[#3B9EFF]'
                : 'text-[#4A5568] hover:text-[#94A3B8]']"
          >委员会观点统计</button>
          <button
            @click="memberViewsSubTab = 'my_fill'"
            :class="['px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all duration-150',
              memberViewsSubTab === 'my_fill'
                ? 'bg-[#FFAB00]/12 border border-[#FFAB00]/30 text-[#FFAB00]'
                : 'text-[#4A5568] hover:text-[#94A3B8]']"
          >我的观点填报</button>
        </div>
      </div>

      <!-- ── 秘书视角 (投管): 管理与配置中心 ── -->
      <div v-if="activeTab === 'member_views' && isSecretary && memberViewsSubTab === 'my_fill'" class="pb-4 space-y-4">

        <!-- ── 秘书视图切换器 ── -->
        <div class="flex items-center gap-3">
          <div class="inline-flex bg-[#161922] border border-[#252A3A] rounded-lg p-0.5 gap-0.5">
            <button
              @click="secretaryView = 'progress'"
              :class="cn('px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all duration-150',
                secretaryView === 'progress'
                  ? 'bg-[#3B9EFF]/12 border border-[#3B9EFF]/30 text-[#3B9EFF]'
                  : 'text-[#4A5568] hover:text-[#94A3B8]')"
            >委员提交进度看板</button>
            <button
              @click="secretaryView = 'proxy'"
              :class="cn('px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all duration-150',
                secretaryView === 'proxy'
                  ? 'bg-[#FFAB00]/12 border border-[#FFAB00]/30 text-[#FFAB00]'
                  : 'text-[#4A5568] hover:text-[#94A3B8]')"
            >RPA / 人工代填工作台</button>
          </div>
        </div>

        <!-- ── 委员提交进度看板（原有内容） ── -->
        <div v-if="secretaryView === 'progress'" class="grid grid-cols-12 gap-4">

        <!-- ══ 投票截止时间控制面板 ══ -->
        <div class="col-span-12 bg-[#202431] border border-[#252A3A] rounded-xl px-5 py-3 flex items-center gap-4 flex-wrap">
          <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider shrink-0">投票窗口</div>
          <span :class="cn('text-xs font-mono px-2 py-1 rounded border shrink-0 transition-colors',
            isVoteOpen
              ? 'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]'
              : 'bg-[#F04864]/10 border-[#F04864]/25 text-[#F04864]')">
            {{ isVoteOpen ? '● 收集中' : '■ 已截止' }}
          </span>
          <div class="flex items-center gap-2.5 flex-1">
            <label class="text-xs font-mono text-[#64748B] shrink-0">截止时间</label>
            <input
              type="datetime-local"
              v-model="voteDeadlineInput"
              :disabled="voteForcedClosed"
              class="bg-[#161922] border border-[#2E3348] rounded px-2.5 py-1 text-[13px] font-mono text-[#E8ECF4] focus:border-[#3B9EFF] focus:outline-none transition-colors"
              :class="voteForcedClosed ? 'opacity-40 cursor-not-allowed' : 'hover:border-[#3B9EFF]/40'"
              style="color-scheme: dark;"
            />
            <span v-if="voteDeadlineInput && !voteForcedClosed" :class="cn('text-xs font-mono shrink-0', isVoteOpen ? 'text-[#3B9EFF]' : 'text-[#F04864]')">
              {{ isVoteOpen ? `剩余 ${voteCountdownDisplay}` : '已过期' }}
            </span>
            <span v-if="voteForcedClosed" class="text-xs font-mono text-[#F04864] shrink-0">强制截止中</span>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button
              v-if="isVoteOpen"
              @click="forceCloseVote"
              class="flex items-center gap-1.5 text-[13px] px-3 py-1.5 rounded-lg border border-[#F04864]/30 bg-[#F04864]/8 text-[#F04864] hover:bg-[#F04864]/15 transition-colors font-medium"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-[#F04864] shrink-0"></span>
              手动截止投票
            </button>
            <button
              v-else
              @click="reopenVote"
              class="flex items-center gap-1.5 text-[13px] px-3 py-1.5 rounded-lg border border-[#00C9A7]/30 bg-[#00C9A7]/8 text-[#00C9A7] hover:bg-[#00C9A7]/15 transition-colors font-medium"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-[#00C9A7] shrink-0"></span>
              重新开放
            </button>
          </div>
        </div>

        <!-- LEFT: 问卷题目管理 (动态投票资产) -->
        <div class="col-span-5 space-y-3">
          <div id="nav-qa-manage" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
            <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3 flex items-center justify-between">
              <h3 class="am-title-l2"><div class="am-title-bar"></div>问卷题目管理</h3>
              <span class="text-xs font-mono text-[#64748B]">{{ questionAssetList.length }} 项投票资产</span>
            </div>
            <div class="divide-y divide-[#252A3A]">
              <div
                v-for="(qa, idx) in questionAssetList"
                :key="qa.id"
                class="px-5 py-3 flex items-center justify-between hover:bg-[#1A1E2B]/50 transition-colors"
              >
                <div class="flex items-center gap-3 flex-1 min-w-0">
                  <span class="text-xs font-mono font-bold text-[#3B9EFF] w-5 shrink-0">{{ idx + 1 }}</span>
                  <div class="flex-1 min-w-0">
                    <div class="text-[14px] font-semibold text-[#E8ECF4] truncate">{{ qa.name }}</div>
                    <div class="flex items-center gap-2 mt-0.5">
                      <span class="text-xs font-mono text-[#64748B]">{{ qa.type }}</span>
                      <span :class="cn('text-xs font-mono px-1.5 py-1 rounded border',
                        qa.enabled ? 'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]' : 'bg-[#252A3A] border-[#2E3348] text-[#4A5568]')">{{ qa.enabled ? '启用' : '停用' }}</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <button @click="editQuestionAsset(qa.id)" class="text-xs px-2 py-1 rounded border border-[#252A3A] text-[#94A3B8] hover:border-[#3B9EFF]/30 hover:text-[#3B9EFF] transition-colors flex items-center gap-1">
                    <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div> 编辑
                  </button>
                  <button @click="deleteQuestionAsset(qa.id)" class="text-xs px-2 py-1 rounded border border-[#252A3A] text-[#94A3B8] hover:border-[#F04864]/30 hover:text-[#F04864] transition-colors flex items-center gap-1">
                    <div class="w-0.5 h-3 bg-current rounded-full shrink-0"></div> 删除
                  </button>
                </div>
              </div>
            </div>
            <div class="p-3 border-t border-[#252A3A]">
              <button @click="addQuestionAsset" class="w-full text-[14px] py-2.5 rounded-lg border border-dashed border-[#3B9EFF]/30 bg-[#3B9EFF]/5 text-[#3B9EFF] hover:bg-[#3B9EFF]/10 hover:border-[#3B9EFF]/50 transition-all flex items-center justify-center gap-1.5">
                <span class="text-[15px] leading-relaxed">+</span> 新增投票资产
              </button>
            </div>
          </div>

          <!-- 已提交委员详情查看 -->
          <div v-if="activeMemberId && memberSubmissions[activeMemberId]" class="bg-[#202431] border border-[#3B9EFF]/15 rounded-xl overflow-hidden">
            <div class="bg-gradient-to-r from-[#3B9EFF]/8 to-[#202431] border-b border-[#3B9EFF]/10 px-5 py-3 flex items-center justify-between">
              <h3 class="am-title-l2"><div class="am-title-bar" style="background:#3B9EFF"></div>{{ activeMember?.name }} · 已提交</h3>
              <span class="text-xs font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-1.5 py-1 rounded">{{ memberSubmissions[activeMemberId].submittedAt }}</span>
            </div>
            <div class="p-4 space-y-2 max-h-[280px] overflow-y-auto no-scrollbar">
              <div class="grid grid-cols-3 gap-1.5">
                <div v-for="(val, key) in memberSubmissions[activeMemberId].sectionA" :key="key" class="bg-[#1A1E2B] border border-[#252A3A] rounded px-2.5 py-1.5 flex items-center justify-between">
                  <span class="text-xs text-[#B4BAC9]">{{ key }}</span>
                  <span :class="cn('text-xs font-bold font-mono', SCORE_COLORS[val] || 'text-[#94A3B8]')">{{ val }} · {{ SCORE_LABELS[val] || '-' }}</span>
                </div>
              </div>
              <div class="flex flex-wrap gap-1.5 mt-1">
                <span
                  v-for="(val, key) in memberSubmissions[activeMemberId].sectionB" :key="key"
                  :class="cn('text-xs font-mono px-2 py-1 rounded border',
                    val ? 'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]' : 'bg-[#1A1E2B] border-[#252A3A] text-[#4A5568]')"
                >{{ key }}: {{ val ? '创新高' : '-' }}</span>
              </div>
              <p class="text-xs text-[#94A3B8] leading-relaxed line-clamp-3 mt-1">{{ memberSubmissions[activeMemberId].coreView }}</p>
            </div>
          </div>
        </div>

        <!-- RIGHT: 提交进度看板 -->
        <div class="col-span-7">
          <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden h-full flex flex-col">
            <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3 flex items-center justify-between">
              <h3 class="am-title-l2"><div class="am-title-bar"></div>提交进度看板</h3>
              <div class="flex items-center space-x-3">
                <span class="text-xs font-mono text-[#94A3B8]">{{ submittedCount }} / {{ MEMBERS_DATA.length }} 已提交</span>
                <div class="w-20 h-1 bg-[#1A1E2B] rounded-full overflow-hidden">
                  <div class="h-full bg-[#3B9EFF] rounded-full transition-all duration-500" :style="{ width: `${submittedCount / MEMBERS_DATA.length * 100}%` }"></div>
                </div>
              </div>
            </div>
            <div class="flex-1 overflow-y-auto no-scrollbar divide-y divide-[#1A1E2B]">
              <div
                v-for="m in MEMBERS_DATA" :key="m.id"
                @click="selectMember(m.id)"
                :class="cn(
                  'flex items-center px-5 py-3.5 cursor-pointer transition-all duration-150',
                  activeMemberId === m.id ? 'bg-[#3B9EFF]/08 border-l-2 border-[#3B9EFF]' : 'hover:bg-[#1A1E2B]/70 border-l-2 border-transparent'
                )"
              >
                <div :class="cn(
                  'w-2.5 h-2.5 rounded-full shrink-0 mr-4',
                  memberSubmissions[m.id] ? 'bg-[#34C759] shadow-[0_0_6px_rgba(52,199,89,0.4)]' : 'bg-[#4A5568]'
                )"></div>
                <div class="flex-1 min-w-0">
                  <div class="text-[14px] font-medium text-[#E8ECF4]">{{ m.name }}</div>
                  <div class="text-xs font-mono text-[#6B7280] mt-0.5">{{ m.role }}</div>
                </div>
                <div class="flex items-center space-x-2">
                  <span v-if="memberSubmissions[m.id]" class="text-xs font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-2 py-1 rounded">
                    已提交 {{ memberSubmissions[m.id].submittedAt }}
                  </span>
                  <span v-else class="text-xs font-mono text-[#F97316] bg-[#F97316]/10 border border-[#F97316]/20 px-2 py-1 rounded">未提交</span>
                  <button
                    v-if="!memberSubmissions[m.id]"
                    @click.stop="sendReminder(m.id)"
                    :class="cn(
                      'text-xs font-mono px-2.5 py-1 rounded border transition-all duration-150',
                      sentReminders.has(m.id) ? 'text-[#94A3B8] border-[#252A3A] cursor-default' : 'text-[#3B9EFF] border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/10'
                    )"
                  >{{ sentReminders.has(m.id) ? '已催' : '催办' }}</button>
                </div>
              </div>
            </div>
            <div class="p-3 border-t border-[#252A3A]">
              <button
                @click="sendAllReminders"
                class="w-full text-[14px] py-2.5 rounded-lg border border-[#3B9EFF]/25 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 hover:border-[#3B9EFF]/40 transition-all flex items-center justify-center space-x-2"
              >
                <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div>
                <span>一键邮件催办全部未提交委员</span>
              </button>
              <button
                @click="markMaterialsCollected"
                class="w-full mt-2 text-[14px] py-2.5 rounded-lg border border-[#34C759]/25 bg-[#34C759]/8 text-[#34C759] hover:bg-[#34C759]/15 hover:border-[#34C759]/40 transition-all flex items-center justify-center space-x-2"
              >
                <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div>
                <span>完成会前收集</span>
              </button>
            </div>
          </div>
        </div>
        </div>

        <!-- ── RPA / 人工代填工作台 ── -->
        <div v-else class="space-y-4">
          <!-- 警示横幅 -->
          <div class="flex items-center gap-3 px-4 py-2.5 bg-[#FFAB00]/5 border border-[#FFAB00]/30 rounded-xl">
            <div class="w-1.5 h-4 bg-[#FFAB00] rounded-sm shrink-0"></div>
            <span class="text-xs font-mono text-[#FFAB00] font-semibold">当前为秘书代操作模式</span>
            <span class="text-xs font-mono text-[#FFAB00]/55 ml-auto">代填操作将附加 isProxy: true 标记</span>
          </div>

          <!-- 委员选择器 -->
          <div class="bg-[#202431] border border-[#FFAB00]/25 rounded-xl overflow-hidden">
            <div class="bg-gradient-to-r from-[#FFAB00]/8 to-[#202431] border-b border-[#FFAB00]/15 px-5 py-3 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-4 bg-[#FFAB00] rounded-sm shrink-0"></div>
                <h3 class="text-sm font-semibold text-[#E8ECF4]">目标委员选择</h3>
              </div>
              <span class="text-xs font-mono text-[#FFAB00]/70 bg-[#FFAB00]/8 border border-[#FFAB00]/20 px-2 py-1 rounded">RPA 代填模式</span>
            </div>
            <div class="p-5">
              <label class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2 block">请选择目标委员</label>
              <select
                v-model="proxyTargetId"
                data-rpa-id="member-selector"
                class="w-full bg-[#1A1E2B] border border-[#FFAB00]/25 rounded-lg px-4 py-2.5 text-sm text-[#E8ECF4] font-mono focus:border-[#FFAB00]/50 focus:outline-none transition-colors cursor-pointer"
              >
                <option value="" disabled class="bg-[#161922] text-[#4A5568]">-- 选择委员 --</option>
                <option v-for="m in COMMITTEE_MEMBERS" :key="m.id" :value="m.id" class="bg-[#161922] text-[#E8ECF4]">
                  {{ m.name }} · {{ m.role }}
                </option>
              </select>
            </div>
          </div>

          <!-- 问卷填报区（代填目标已选） -->
          <div v-if="proxyTargetId" class="bg-[#202431] border border-[#FFAB00]/25 rounded-xl overflow-hidden">
            <!-- 代填成功状态 -->
            <div v-if="proxySubmitDone" class="p-8 flex flex-col items-center gap-3">
              <div class="w-1.5 h-8 bg-[#00C9A7] rounded-sm"></div>
              <p class="text-sm font-semibold text-[#00C9A7]">代填成功</p>
              <p class="text-xs font-mono text-[#64748B]">表单已清空，可为下一位委员代填</p>
            </div>
            <!-- 填报表单 -->
            <template v-else>
              <div class="bg-gradient-to-r from-[#FFAB00]/8 to-[#202431] border-b border-[#FFAB00]/15 px-5 py-3 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-1.5 h-4 bg-[#FFAB00] rounded-sm shrink-0"></div>
                  <h3 class="text-sm font-semibold text-[#E8ECF4]">代填：{{ proxyTargetMember?.name }} · {{ proxyTargetMember?.role }}</h3>
                </div>
                <span class="text-xs font-mono text-[#FFAB00]/60">资配观点填报（代填）</span>
              </div>
              <div class="p-6 space-y-6">
                <!-- A: 资产评分（树状分组） -->
                <div class="space-y-5">
                  <div v-for="group in MIXED_ASSET_GROUPS" :key="group.大类" class="space-y-2">
                    <div class="flex items-center gap-3">
                      <div class="h-px flex-1 bg-[#252A3A]"></div>
                      <div class="flex items-center gap-2 px-3 py-1 rounded-full border"
                        :class="MIXED_GROUP_HEADER_STYLE[group.大类] ?? 'border-[#2E3348] bg-[#1A1E2B]'">
                        <span class="text-[12px] font-bold font-mono" :class="MIXED_GROUP_TEXT_COLOR[group.大类] ?? 'text-[#94A3B8]'">{{ group.大类 }}</span>
                        <span class="text-xs font-mono text-[#4A5568]">{{ group.items.length }} 项策略</span>
                      </div>
                      <div class="h-px flex-1 bg-[#252A3A]"></div>
                    </div>
                    <div v-for="cfg in group.items" :key="cfg.细分策略"
                      class="bg-[#1A1E2B] border border-[#2E3348] rounded-xl p-4 space-y-3">
                      <div class="flex items-start justify-between gap-3">
                        <div class="min-w-0">
                          <div class="text-[15px] font-semibold text-[#E8ECF4]">{{ cfg.细分策略 }}</div>
                          <div class="flex items-center gap-1.5 mt-0.5">
                            <span class="text-xs font-mono text-[#4A5568] truncate">{{ cfg.标的指数 }}</span>
                            <span class="text-xs text-[#3A4555]">·</span>
                            <span class="text-[12px] font-mono font-bold tabular-nums text-[#64748B]">{{ cfg.当前点位 }}</span>
                          </div>
                        </div>
                        <button
                          @click="proxyFormB[cfg.细分策略] = !proxyFormB[cfg.细分策略]"
                          :class="cn('shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono transition-all duration-150',
                            proxyFormB[cfg.细分策略]
                              ? 'bg-[#00C9A7]/10 border-[#00C9A7]/35 text-[#00C9A7]'
                              : 'bg-transparent border-[#252A3A] text-[#4A5568] hover:border-[#2E3348] hover:text-[#64748B]')"
                        ><span class="text-xs">↑</span><span>创新高</span></button>
                      </div>
                      <!-- 评分按钮（带 RPA data 属性） -->
                      <div class="grid grid-cols-5 gap-2">
                        <button
                          v-for="n in 5" :key="n"
                          @click="proxyFormA[cfg.细分策略] = n"
                          :data-rpa-id="`vote-btn-${group.大类}-${cfg.细分策略}-${n}`"
                          :class="cn(
                            'py-3 rounded-lg border transition-all duration-150 flex flex-col items-center gap-1',
                            proxyFormA[cfg.细分策略] === n ? SCORE_COLORS[n] : SCORE_INACTIVE
                          )"
                        >
                          <span class="text-[22px] font-bold font-mono leading-none">{{ n }}</span>
                          <span class="text-[11px] font-mono opacity-75">{{ SCORE_LABELS_SHORT[n] }}</span>
                        </button>
                      </div>
                      <!-- 动态幅度 / 区间显示 -->
                      <div class="flex items-center gap-2 bg-[#161922] rounded-lg px-3 py-2 border border-[#252A3A]">
                        <span class="text-xs font-mono text-[#4A5568]">观点幅度</span>
                        <span class="text-[12px] font-mono font-bold text-[#3B9EFF]">{{ getAmplitudeText(cfg.细分策略, proxyFormA[cfg.细分策略]) }}</span>
                        <div class="w-px h-3 bg-[#2E3348] mx-1"></div>
                        <span class="text-xs font-mono text-[#4A5568]">预期区间</span>
                        <span class="text-[12px] font-mono font-bold text-[#3B9EFF] tabular-nums">{{ getTargetRangeText(cfg.细分策略, proxyFormA[cfg.细分策略]) }}</span>
                        <span class="text-xs font-mono text-[#3A4555] ml-0.5">{{ cfg.amplitudeType === 'bp' ? '%(收益率)' : '点' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- C: 重点资产 -->
                <div>
                  <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-3">C. 重点资产（多选）</div>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="item in QUESTIONNAIRE_CONFIG.sections[2].items" :key="item"
                      @click="proxyFormC[item] = !proxyFormC[item]"
                      :class="cn(
                        'px-3.5 py-1.5 text-[14px] rounded-lg border transition-all duration-150 font-medium',
                        proxyFormC[item]
                          ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#1A1E2B] border-[#252A3A] text-[#6B7280] hover:border-[#2E3348] hover:text-[#94A3B8]'
                      )"
                    >{{ item }}</button>
                  </div>
                </div>
                <!-- D: 核心观点 -->
                <div>
                  <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-3">D. 核心观点与论据</div>
                  <textarea
                    v-model="proxyFormCoreView"
                    rows="4"
                    class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-xl px-5 py-4 text-[15px] text-[#B4BAC9] placeholder-[#3A4555] outline-none focus:border-[#FFAB00]/40 transition-all resize-none leading-relaxed"
                    :placeholder="`代 ${proxyTargetMember?.name ?? '委员'} 输入本季度核心观点...`"
                  ></textarea>
                  <div class="flex items-center justify-between mt-1.5">
                    <div
                      @click="proxyFormRiskFlag = !proxyFormRiskFlag"
                      :class="cn(
                        'flex items-center space-x-2 px-3 py-1.5 rounded-lg border cursor-pointer transition-all duration-150',
                        proxyFormRiskFlag ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25' : 'bg-[#1A1E2B] border-[#252A3A] hover:border-[#2E3348]'
                      )"
                    >
                      <div :class="cn('w-3.5 h-3.5 rounded border flex items-center justify-center shrink-0 transition-all', proxyFormRiskFlag ? 'bg-[#3B9EFF] border-[#3B9EFF]' : 'border-[#2E3348]')">
                        <div v-if="proxyFormRiskFlag" class="w-0.5 h-2 bg-white rounded-sm"></div>
                      </div>
                      <span class="text-xs" :class="proxyFormRiskFlag ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">标记尾部风险事项</span>
                    </div>
                    <span class="text-xs font-mono text-[#4A5568]">{{ proxyFormCoreView.length }} 字</span>
                  </div>
                </div>
              </div>
              <!-- 提交区 -->
              <div class="p-5 border-t border-[#FFAB00]/15 space-y-2">
                <div class="flex items-center gap-2 bg-[#FFAB00]/5 border border-[#FFAB00]/20 rounded-lg px-4 py-2.5">
                  <div class="w-1.5 h-3.5 bg-[#FFAB00] rounded-sm shrink-0"></div>
                  <span class="text-[13px] text-[#FFAB00]">代填操作：数据将绑定至 {{ proxyTargetMember?.name }}，isProxy: true</span>
                </div>
                <button
                  @click="submitProxyVote"
                  :disabled="!proxyFormCoreView.trim()"
                  data-rpa-id="proxy-submit-btn"
                  :class="cn(
                    'w-full py-3.5 rounded-xl font-bold text-[15px] transition-all duration-200',
                    proxyFormCoreView.trim()
                      ? 'bg-gradient-to-r from-[#FFAB00]/80 to-[#FFAB00] text-[#161922] shadow-[0_4px_24px_rgba(255,171,0,0.3)] hover:shadow-[0_4px_36px_rgba(255,171,0,0.45)] active:scale-[0.99]'
                      : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed'
                  )"
                >确认代 {{ proxyTargetMember?.name ?? '委员' }} 提交问卷</button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ── 委员视角 (班子/部门长/投资经理): 纯填报入口 ── -->
      <div v-else-if="activeTab === 'member_views' && !isSecretary && memberViewsSubTab === 'my_fill'" class="pb-4">

        <!-- 已提交：只读确认状态 -->
        <div v-if="memberSubmitted" class="bg-[#202431] border border-[#34C759]/20 rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#34C759]/10 to-[#202431] border-b border-[#34C759]/15 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-full bg-[#34C759]/15 border border-[#34C759]/30 flex items-center justify-center">
                <div class="w-1.5 h-4 bg-[#00C9A7] rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="text-[15px] font-bold text-[#34C759]">已成功提交</h3>
                <p class="text-xs font-mono text-[#94A3B8] mt-0.5">提交于 {{ memberSubmitted.submittedAt }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span :class="cn('text-xs font-mono px-2 py-1 rounded border',
                isVoteOpen
                  ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/20 text-[#3B9EFF]'
                  : 'bg-[#94A3B8]/10 border-[#94A3B8]/20 text-[#94A3B8]')">
                {{ isVoteOpen ? '可更新' : '已锁定' }}
              </span>
            </div>
          </div>
          <div class="p-6 space-y-5">
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">A. 资产评分</div>
              <div class="grid grid-cols-3 gap-3">
                <div v-for="(val, key) in memberSubmitted.sectionA" :key="key" class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3 flex items-center justify-between">
                  <span class="text-[14px] text-[#B4BAC9]">{{ key }}</span>
                  <span :class="cn('text-[14px] font-bold font-mono', SCORE_COLORS[val])">{{ val }} · {{ SCORE_LABELS[val] }}</span>
                </div>
              </div>
            </div>
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">B. 新高预判</div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(val, key) in memberSubmitted.sectionB" :key="key"
                  :class="cn('text-xs font-mono px-2.5 py-1 rounded-lg border',
                    val ? 'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]' : 'bg-[#1A1E2B] border-[#252A3A] text-[#4A5568]')"
                >{{ key }}: {{ val ? '能' : '不能' }}</span>
              </div>
            </div>
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">C. 重点资产</div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(checked, key) in memberSubmitted.sectionC" :key="key"
                  :class="cn('text-xs font-mono px-2.5 py-1 rounded-lg border',
                    checked ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]' : 'bg-[#1A1E2B] border-[#252A3A] text-[#4A5568]')"
                >{{ key }}</span>
              </div>
            </div>
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">D. 核心观点</div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-5 py-4 text-[14px] text-[#B4BAC9] leading-relaxed">{{ memberSubmitted.coreView }}</div>
            </div>
            <div v-if="memberSubmitted.riskFlag" class="flex items-center space-x-2 bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 rounded-lg px-4 py-3">
              <div class="w-1.5 h-4 bg-[#3B9EFF] rounded-sm shrink-0"></div>
              <span class="text-[14px] text-[#3B9EFF]">已标记：存在需关注的尾部风险事项</span>
            </div>
          </div>
          <!-- 更新并重新提交入口（仅在投票窗口开放时显示） -->
          <div v-if="isVoteOpen" class="px-6 pb-5">
            <button
              @click="clearMemberSubmission"
              class="w-full py-2.5 rounded-xl font-medium text-[14px] border border-[#3B9EFF]/30 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 transition-all duration-200 flex items-center justify-center gap-2"
            >
              <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div>
              更新并重新提交
            </button>
          </div>
        </div>

        <!-- 未提交：全宽填报表单 -->
        <div v-else class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div id="nav-vote-form" class="w-8 h-8 rounded-full bg-gradient-to-br from-[#3B9EFF] to-[#3B9EFF] flex items-center justify-center shadow-[0_0_14px_rgba(59,158,255,0.25)]">
                <div class="w-1.5 h-4 bg-white/90 rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="am-title-l2"><div class="am-title-bar"></div>资配观点填报</h3>
                <p class="text-xs font-mono text-[#6B7280] mt-0.5">2026 Q2 · 请在截止时间前完成提交</p>
              </div>
            </div>
            <button @click="showHistoryModal = true" class="text-[13px] text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/18 hover:border-[#3B9EFF]/40 px-2.5 py-1 rounded flex items-center gap-1.5 transition-colors shrink-0">
              <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div> 查看历史投票
            </button>
          </div>
          <div class="p-6 space-y-6">
            <!-- 树状分组问卷：按固收 / 含权 / 另类 三大类展示 -->
            <div class="space-y-5">
              <div v-for="group in MIXED_ASSET_GROUPS" :key="group.大类" class="space-y-2">
                <!-- 大类标题 -->
                <div class="flex items-center gap-3">
                  <div class="h-px flex-1 bg-[#252A3A]"></div>
                  <div class="flex items-center gap-2 px-3 py-1 rounded-full border"
                    :class="MIXED_GROUP_HEADER_STYLE[group.大类] ?? 'border-[#2E3348] bg-[#1A1E2B]'">
                    <span class="text-[12px] font-bold font-mono"
                      :class="MIXED_GROUP_TEXT_COLOR[group.大类] ?? 'text-[#94A3B8]'">{{ group.大类 }}</span>
                    <span class="text-xs font-mono text-[#4A5568]">{{ group.items.length }} 项策略</span>
                  </div>
                  <div class="h-px flex-1 bg-[#252A3A]"></div>
                </div>
                <!-- 每个细分策略卡片 -->
                <div v-for="cfg in group.items" :key="cfg.细分策略"
                  class="bg-[#1A1E2B] border border-[#2E3348] rounded-xl p-4 space-y-3">
                  <!-- 卡片顶行：策略名 + 基准参考 + 创新高标签 -->
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="text-[15px] font-semibold text-[#E8ECF4]">{{ cfg.细分策略 }}</div>
                      <div class="flex items-center gap-1.5 mt-0.5">
                        <span class="text-xs font-mono text-[#4A5568] truncate">{{ cfg.标的指数 }}</span>
                        <span class="text-xs text-[#3A4555]">·</span>
                        <span class="text-[12px] font-mono font-bold tabular-nums text-[#64748B]">{{ cfg.当前点位 }}</span>
                      </div>
                    </div>
                    <!-- 创新高 — 卡片右上角可选辅助标签 -->
                    <button
                      @click="FORM_SECTION_B[cfg.细分策略] = !FORM_SECTION_B[cfg.细分策略]"
                      :class="cn('shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono transition-all duration-150',
                        FORM_SECTION_B[cfg.细分策略]
                          ? 'bg-[#00C9A7]/10 border-[#00C9A7]/35 text-[#00C9A7]'
                          : 'bg-transparent border-[#252A3A] text-[#4A5568] hover:border-[#2E3348] hover:text-[#64748B]')"
                    >
                      <span class="text-xs">↑</span>
                      <span>创新高</span>
                    </button>
                  </div>
                  <!-- 评分按钮行 (1-5档) -->
                  <div class="grid grid-cols-5 gap-2">
                    <button
                      v-for="n in 5" :key="n"
                      @click="FORM_SECTION_A[cfg.细分策略] = n"
                      :class="cn(
                        'py-3 rounded-lg border transition-all duration-150 flex flex-col items-center gap-1',
                        FORM_SECTION_A[cfg.细分策略] === n ? SCORE_COLORS[n] : SCORE_INACTIVE
                      )"
                    >
                      <span class="text-[22px] font-bold font-mono leading-none">{{ n }}</span>
                      <span class="text-[11px] font-mono opacity-75">{{ SCORE_LABELS_SHORT[n] }}</span>
                    </button>
                  </div>
                  <!-- 动态翻译：观点幅度 + 预期点位区间（实时联动核心） -->
                  <div class="flex items-center gap-2 bg-[#161922] rounded-lg px-3 py-2 border border-[#252A3A]">
                    <span class="text-xs font-mono text-[#4A5568]">观点幅度</span>
                    <span class="text-[12px] font-mono font-bold text-[#3B9EFF]">{{ getAmplitudeText(cfg.细分策略, FORM_SECTION_A[cfg.细分策略]) }}</span>
                    <div class="w-px h-3 bg-[#2E3348] mx-1"></div>
                    <span class="text-xs font-mono text-[#4A5568]">预期区间</span>
                    <span class="text-[12px] font-mono font-bold text-[#3B9EFF] tabular-nums">{{ getTargetRangeText(cfg.细分策略, FORM_SECTION_A[cfg.细分策略]) }}</span>
                    <span class="text-xs font-mono text-[#3A4555] ml-0.5">{{ cfg.amplitudeType === 'bp' ? '%(收益率)' : '点' }}</span>
                  </div>
                </div>
              </div>
            </div>
            <!-- C: 重点资产多选 -->
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-3">C. 重点资产（多选）</div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="item in QUESTIONNAIRE_CONFIG.sections[2].items" :key="item"
                  @click="FORM_SECTION_C[item] = !FORM_SECTION_C[item]"
                  :class="cn(
                    'px-3.5 py-1.5 text-[14px] rounded-lg border transition-all duration-150 font-medium',
                    FORM_SECTION_C[item]
                      ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                      : 'bg-[#1A1E2B] border-[#252A3A] text-[#6B7280] hover:border-[#2E3348] hover:text-[#94A3B8]'
                  )"
                >{{ item }}</button>
              </div>
            </div>
            <!-- D: 核心观点 Textarea -->
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-3">D. 核心观点与论据</div>
              <textarea
                v-model="formCoreView"
                rows="5"
                class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-xl px-5 py-4 text-[15px] text-[#B4BAC9] placeholder-[#3A4555] outline-none focus:border-[#3B9EFF]/45 focus:shadow-[0_0_20px_rgba(59,158,255,0.06)] transition-all resize-none leading-relaxed"
                placeholder="请输入您对本季度市场的核心判断与主要论据，将在会议屏幕上作为讨论依据展示..."
              ></textarea>
              <div class="flex items-center justify-between mt-1.5">
                <div
                  @click="formRiskFlag = !formRiskFlag"
                  :class="cn(
                    'flex items-center space-x-2 px-3 py-1.5 rounded-lg border cursor-pointer transition-all duration-150',
                    formRiskFlag ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25' : 'bg-[#1A1E2B] border-[#252A3A] hover:border-[#2E3348]'
                  )"
                >
                  <div :class="cn('w-3.5 h-3.5 rounded border flex items-center justify-center shrink-0 transition-all', formRiskFlag ? 'bg-[#3B9EFF] border-[#3B9EFF]' : 'border-[#2E3348]')">
                    <div v-if="formRiskFlag" class="w-0.5 h-2 bg-white rounded-sm"></div>
                  </div>
                  <span class="text-xs" :class="formRiskFlag ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">标记尾部风险事项</span>
                </div>
                <span class="text-xs font-mono text-[#4A5568]">{{ formCoreView.length }} 字</span>
              </div>
            </div>
          </div>
          <div class="p-5 border-t border-[#252A3A] space-y-2">
            <!-- 投票窗口已关闭提示 -->
            <div v-if="!isVoteOpen" class="flex items-center gap-2 bg-[#F04864]/8 border border-[#F04864]/20 rounded-lg px-4 py-2.5">
              <div class="w-1.5 h-3.5 bg-[#F04864] rounded-sm shrink-0"></div>
              <span class="text-[13px] text-[#F04864]">投票窗口已截止，无法提交</span>
            </div>
            <button
              @click="showVoteConfirm = true"
              :disabled="!formCoreView.trim() || !isVoteOpen"
              :class="cn(
                'w-full py-3.5 rounded-xl font-bold text-[15px] transition-all duration-200',
                formCoreView.trim() && isVoteOpen
                  ? 'bg-gradient-to-r from-[#3B9EFF] to-[#3B9EFF] text-white shadow-[0_4px_24px_rgba(59,158,255,0.3)] hover:shadow-[0_4px_36px_rgba(59,158,255,0.45)] active:scale-[0.99]'
                  : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed'
              )"
            >{{ !isVoteOpen ? '投票已截止' : '确认提交本次观点' }}</button>
          </div>
        </div>
      </div>

      <!-- ══ 会前问卷汇总 · 委员定性观点 (member_views "我的观点填报" 共享) ═══ -->
      <div v-if="activeTab === 'member_views' && memberViewsSubTab === 'my_fill'" class="space-y-4 pb-4">
        <div id="nav-pre-summary" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>会前问卷汇总 · 委员定性观点</h3>
            <div class="flex items-center space-x-2">
              <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] animate-pulse"></div>
              <span class="text-xs font-mono text-[#94A3B8]">来自会前收集 · 会中讨论参考</span>
            </div>
          </div>
          <div class="p-5 grid grid-cols-2 gap-3" v-if="committeeQualitativeViews.length > 0">
            <div
              v-for="(view, i) in committeeQualitativeViews" :key="view.author + i"
              class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg p-4 hover:border-[#2E3348] transition-all duration-200"
            >
              <div class="flex items-start justify-between mb-2.5">
                <div class="flex items-center space-x-2">
                  <div class="w-1 h-full min-h-[14px] rounded-full shrink-0" :style="{ backgroundColor: view.color, width: '3px' }"></div>
                  <span class="text-xs font-bold font-mono" :style="{ color: view.color }">{{ view.role }}</span>
                  <span class="text-xs text-[#94A3B8]">{{ view.author }}</span>
                </div>
                <span :class="cn('text-xs px-2 py-1 rounded-full border font-mono shrink-0 ml-2', view.sentiment === '偏多' ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/20 text-[#3B9EFF]' : view.sentiment === '偏空' ? 'bg-[#FF3B30]/10 border-[#FF3B30]/20 text-[#FF3B30]' : 'bg-[#3B9EFF]/10 border-[#3B9EFF]/20 text-[#3B9EFF]')">{{ view.sentiment }}</span>
              </div>
              <p class="text-[14px] text-[#B4BAC9] leading-relaxed">{{ view.content }}</p>
              <div class="flex flex-wrap gap-1.5 mt-2.5">
                <span v-for="tag in view.tags" :key="tag" class="text-xs text-[#94A3B8] bg-[#202431] border border-[#252A3A] px-1.5 py-1 rounded font-mono">{{ tag }}</span>
              </div>
            </div>
          </div>
          <div v-else class="p-8 text-center space-y-3">
            <div class="w-12 h-12 rounded-full bg-[#252A3A] flex items-center justify-center mx-auto">
              <div class="w-1.5 h-5 bg-[#4A5568] rounded-sm shrink-0"></div>
            </div>
            <div class="text-[14px] text-[#64748B]">暂无委员提交问卷观点</div>
            <div class="text-xs text-[#4A5568]">委员需在"委员观点"页面完成填报后，观点将自动汇总至此</div>
          </div>
        </div>
      </div>

      <!-- ══ 委员会观点统计 · 量化锚点 + 投票汇总 ══ -->
      <div v-if="activeTab === 'member_views' && memberViewsSubTab === 'committee_stats'" class="space-y-4 pb-4">

        <!-- ── A. 经典模型参考（核心模型结果） ── -->
        <div id="nav-model-anchors" class="bg-[#202431] border border-cyan-500/20 rounded-xl overflow-hidden shadow-[0_0_24px_rgba(6,182,212,0.05)]">
          <div class="bg-gradient-to-r from-[#0A1620] to-[#202431] border-b border-cyan-500/15 px-5 py-3.5 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-1 h-5 rounded-full bg-cyan-400/80 shrink-0"></div>
              <h3 class="text-[14px] font-bold text-white tracking-wide">经典模型参考</h3>
              <span class="text-xs font-mono px-2 py-0.5 rounded-full border border-cyan-500/30 text-cyan-400/80 bg-cyan-500/8">核心模型结果 · 本期实时</span>
            </div>
            <span class="text-xs font-mono text-[#64748B]">SAA 三模型建议配置</span>
          </div>
          <!-- ── 三模型智能对比矩阵 (Smart Matrix · Data Bars) ── -->
          <div class="select-none">

            <!-- 模型引擎卡片表头 -->
            <div class="flex border-b border-slate-700/60 bg-[#0E1118] px-3 pt-3 pb-0 gap-1.5">
              <div class="w-[38%] shrink-0 flex items-end pb-2.5 px-2">
                <span class="text-[11px] font-mono text-slate-600 uppercase tracking-widest">资产类别</span>
              </div>
              <!-- MC -->
              <div class="flex-1 bg-indigo-950/70 border border-indigo-500/30 border-b-0 rounded-t-lg px-3 py-2.5 space-y-1">
                <div class="flex items-start justify-between gap-1">
                  <div>
                    <div class="text-[10px] font-mono text-indigo-500/70 uppercase tracking-wider leading-none">MC-SIM</div>
                    <div class="text-[13px] font-bold text-indigo-300 mt-1 leading-none">蒙特卡洛</div>
                  </div>
                  <button @click.stop="openMCDialog()" class="shrink-0 text-[10px] font-mono text-indigo-500 hover:text-indigo-300 border border-indigo-500/25 bg-indigo-500/8 hover:bg-indigo-500/18 px-1.5 py-0.5 rounded transition-colors">查看详情</button>
                </div>
                <div class="text-[10px] text-slate-600 font-mono">10万次模拟 · SR 0.82</div>
              </div>
              <!-- BL -->
              <div class="flex-1 bg-blue-950/70 border border-blue-500/30 border-b-0 rounded-t-lg px-3 py-2.5 space-y-1">
                <div class="flex items-start justify-between gap-1">
                  <div>
                    <div class="text-[10px] font-mono text-blue-500/70 uppercase tracking-wider leading-none">BLACK-LIT</div>
                    <div class="text-[13px] font-bold text-blue-300 mt-1 leading-none">BL 模型</div>
                  </div>
                  <button @click.stop="openBLDialog()" class="shrink-0 text-[10px] font-mono text-blue-500 hover:text-blue-300 border border-blue-500/25 bg-blue-500/8 hover:bg-blue-500/18 px-1.5 py-0.5 rounded transition-colors">查看详情</button>
                </div>
                <div class="text-[10px] text-slate-600 font-mono">贝叶斯融合 · SR 0.95</div>
              </div>
              <!-- RP -->
              <div class="flex-1 bg-sky-950/70 border border-sky-600/30 border-b-0 rounded-t-lg px-3 py-2.5 space-y-1">
                <div class="flex items-start justify-between gap-1">
                  <div>
                    <div class="text-[10px] font-mono text-sky-600/70 uppercase tracking-wider leading-none">RP-ATAN</div>
                    <div class="text-[13px] font-bold text-sky-400 mt-1 leading-none">风险平价</div>
                  </div>
                  <button @click.stop="openRPDialog()" class="shrink-0 text-[10px] font-mono text-sky-600 hover:text-sky-400 border border-sky-600/25 bg-sky-500/8 hover:bg-sky-500/18 px-1.5 py-0.5 rounded transition-colors">查看详情</button>
                </div>
                <div class="text-[10px] text-slate-600 font-mono">等风险贡献 · SR 0.78</div>
              </div>
            </div>

            <!-- 数据行 -->
            <div class="divide-y divide-slate-800/50">
              <template v-for="row in MODEL_TREE_DATA" :key="row.category">

                <!-- 大类行 -->
                <div
                  class="flex items-stretch cursor-pointer bg-slate-800/40 hover:bg-slate-700/30 transition-colors duration-100"
                  @click="toggleModelTreeRow(row.category)"
                >
                  <div class="w-[38%] shrink-0 flex items-center gap-2 px-4 h-10 border-r border-slate-800/50">
                    <span class="text-slate-500 font-mono text-[11px] w-3 shrink-0 select-none">{{ expandedModelTree.has(row.category) ? '▾' : '▸' }}</span>
                    <span class="text-sm font-bold text-white tracking-wide">{{ row.category }}</span>
                  </div>
                  <div class="flex-1 relative flex items-center justify-center h-10 overflow-hidden border-r border-slate-800/40">
                    <div class="absolute inset-y-1.5 left-1.5 rounded bg-indigo-500/22" :style="{ width: `calc(${Math.min(row.mc * 1.8, 94)}% - 6px)` }"></div>
                    <span class="relative z-10 font-mono font-bold text-sm text-white tabular-nums">{{ row.mc }}<span class="text-[10px] text-slate-500 font-normal">%</span></span>
                  </div>
                  <div class="flex-1 relative flex items-center justify-center h-10 overflow-hidden border-r border-slate-800/40">
                    <div class="absolute inset-y-1.5 left-1.5 rounded bg-blue-500/22" :style="{ width: `calc(${Math.min(row.bl * 1.8, 94)}% - 6px)` }"></div>
                    <span class="relative z-10 font-mono font-bold text-sm text-white tabular-nums">{{ row.bl }}<span class="text-[10px] text-slate-500 font-normal">%</span></span>
                  </div>
                  <div class="flex-1 relative flex items-center justify-center h-10 overflow-hidden">
                    <div class="absolute inset-y-1.5 left-1.5 rounded bg-sky-500/22" :style="{ width: `calc(${Math.min(row.rp * 1.8, 94)}% - 6px)` }"></div>
                    <span class="relative z-10 font-mono font-bold text-sm text-white tabular-nums">{{ row.rp }}<span class="text-[10px] text-slate-500 font-normal">%</span></span>
                  </div>
                </div>

                <!-- 子资产行 -->
                <template v-if="expandedModelTree.has(row.category)">
                  <div
                    v-for="child in row.children" :key="child.sub"
                    class="flex items-stretch bg-[#0E1118] hover:bg-slate-700/30 transition-colors duration-100"
                  >
                    <div class="w-[38%] shrink-0 flex items-center pl-8 pr-4 h-10 border-r border-slate-800/50 gap-2">
                      <span class="text-slate-600 text-base select-none leading-none">·</span>
                      <span class="text-[13px] text-slate-300">{{ child.sub }}</span>
                    </div>
                    <div class="flex-1 relative flex items-center justify-center h-10 overflow-hidden border-r border-slate-800/40">
                      <div class="absolute inset-y-2 left-1.5 rounded bg-indigo-500/15" :style="{ width: `calc(${Math.min(child.mc * 1.8, 94)}% - 6px)` }"></div>
                      <span class="relative z-10 font-mono text-sm text-slate-100 tabular-nums">{{ child.mc }}<span class="text-[10px] text-slate-500 font-normal">%</span></span>
                    </div>
                    <div class="flex-1 relative flex items-center justify-center h-10 overflow-hidden border-r border-slate-800/40">
                      <div class="absolute inset-y-2 left-1.5 rounded bg-blue-500/15" :style="{ width: `calc(${Math.min(child.bl * 1.8, 94)}% - 6px)` }"></div>
                      <span class="relative z-10 font-mono text-sm text-slate-100 tabular-nums">{{ child.bl }}<span class="text-[10px] text-slate-500 font-normal">%</span></span>
                    </div>
                    <div class="flex-1 relative flex items-center justify-center h-10 overflow-hidden">
                      <div class="absolute inset-y-2 left-1.5 rounded bg-sky-500/15" :style="{ width: `calc(${Math.min(child.rp * 1.8, 94)}% - 6px)` }"></div>
                      <span class="relative z-10 font-mono text-sm text-slate-100 tabular-nums">{{ child.rp }}<span class="text-[10px] text-slate-500 font-normal">%</span></span>
                    </div>
                  </div>
                </template>

              </template>
            </div>

            <!-- 合计行 -->
            <div class="flex border-t border-slate-700/60 bg-[#0E1118]">
              <div class="w-[38%] shrink-0 flex items-center px-4 h-9 border-r border-slate-800/50">
                <span class="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-widest">合计</span>
              </div>
              <div class="flex-1 flex items-center justify-center h-9 border-r border-slate-800/40">
                <span class="font-mono font-bold text-sm text-indigo-300 tabular-nums">100<span class="text-[10px] text-slate-500 font-normal">%</span></span>
              </div>
              <div class="flex-1 flex items-center justify-center h-9 border-r border-slate-800/40">
                <span class="font-mono font-bold text-sm text-blue-300 tabular-nums">100<span class="text-[10px] text-slate-500 font-normal">%</span></span>
              </div>
              <div class="flex-1 flex items-center justify-center h-9">
                <span class="font-mono font-bold text-sm text-sky-400 tabular-nums">100<span class="text-[10px] text-slate-500 font-normal">%</span></span>
              </div>
            </div>

          </div>
        </div>

        <!-- ── B. 投票尚未开始提示 ── -->
        <div v-if="submittedCount === 0" class="flex items-center gap-3 bg-[#3B9EFF]/8 border border-[#3B9EFF]/20 rounded-xl px-5 py-3">
          <div class="w-8 h-8 rounded-full bg-[#3B9EFF]/15 flex items-center justify-center shrink-0">
            <div class="w-1.5 h-4 bg-[#3B9EFF] rounded-sm shrink-0"></div>
          </div>
          <div>
            <div class="text-[13px] font-medium text-[#3B9EFF]">尚无委员提交投票</div>
            <div class="text-xs text-[#94A3B8] mt-0.5">投票数据将在委员提交后自动汇总。请确认投票窗口已开启且委员已完成会前填报。</div>
          </div>
        </div>

        <!-- ── 尾部风险预警 ── -->
        <div v-if="hasAnyRiskFlag" class="flex items-center gap-3 bg-[#FF3B30]/8 border border-[#FF3B30]/25 rounded-xl px-5 py-3">
          <div class="w-8 h-8 rounded-full bg-[#FF3B30]/15 flex items-center justify-center shrink-0 animate-pulse">
            <div class="w-1.5 h-4 bg-[#F04864] rounded-sm shrink-0"></div>
          </div>
          <div>
            <div class="text-[13px] font-medium text-[#FF3B30]">有委员标记了尾部风险事项</div>
            <div class="text-xs text-[#94A3B8] mt-0.5">请主任委员在决策时重点关注以下委员提出的风险提示，并在会议纪要中记录应对措施。</div>
          </div>
          <div class="flex flex-wrap gap-1.5 ml-auto shrink-0">
            <span v-for="(s, id) in memberSubmissions" :key="id" v-show="s.riskFlag"
              class="text-xs font-mono px-2 py-1 rounded border border-[#FF3B30]/30 bg-[#FF3B30]/10 text-[#FF3B30]">
              {{ MEMBERS_DATA.find(m => m.id === id)?.name || '委员' }}
            </span>
          </div>
        </div>

        <!-- ── C. 混合投委会观点投票分布矩阵 ── -->
        <div id="nav-vote-matrix" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>混合投委会观点投票分布矩阵</h3>
            <div class="flex items-center gap-3">
              <span class="text-[12px] font-mono text-[#94A3B8]">{{ MEMBERS_DATA.length }} 名委员 · {{ MIXED_ASSET_LIST.length }} 项资产</span>
              <button @click="showHistoryModal = true" class="text-[12px] text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/18 hover:border-[#3B9EFF]/40 px-2.5 py-1 rounded flex items-center gap-1.5 transition-colors">
                <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div> 查询历史期会审结果
              </button>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full border-collapse table-fixed font-mono text-[12px]" style="min-width:860px">
              <colgroup>
                <col style="width:52px" />
                <col style="width:84px" />
                <col style="width:150px" />
                <col style="width:78px" />
                <col style="width:44px" />
                <col style="width:62px" />
                <col style="width:44px" />
                <col style="width:62px" />
                <col style="width:44px" />
                <col style="width:108px" />
                <col style="width:130px" />
              </colgroup>
              <thead class="bg-[#1A1E2B]">
                <tr class="border-b border-[#2E3348]">
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">大类</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">细分策略</th>
                  <th rowspan="2" class="px-3 py-2 text-left text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">标的/基准指数</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle whitespace-nowrap">当前点位</th>
                  <th colspan="5" class="px-2 py-1.5 text-center text-xs font-bold text-[#3B9EFF] border-r border-[#2E3348]">票数分布（各档投票人数）</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle whitespace-nowrap">委员会观点</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] align-middle whitespace-nowrap">对应点位区间</th>
                </tr>
                <tr class="border-b-2 border-[#3B9EFF]/25">
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#00C9A7] border-r border-[#2E3348]/40">谨慎<br/><span class="text-[11px] opacity-50">1分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40 leading-tight">中性<br/>偏谨慎<br/><span class="text-[11px] opacity-50">2分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40">中性<br/><span class="text-[11px] opacity-50">3分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40 leading-tight">中性<br/>偏乐观<br/><span class="text-[11px] opacity-50">4分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#F04864] border-r border-[#2E3348]">乐观<br/><span class="text-[11px] opacity-50">5分</span></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="row in MIXED_DIST_ROWS" :key="row.细分策略" class="hover:bg-[#1A1E2B]/40 transition-colors">
                  <td v-if="row.isFirstInGroup" :rowspan="row.groupSpan"
                    class="px-1 py-2 text-center text-xs font-bold tracking-widest border-r border-[#2E3348] align-middle text-[#3B9EFF] bg-[#3B9EFF]/4">
                    <span style="writing-mode:vertical-rl;letter-spacing:0.2em">{{ row.大类 }}</span>
                  </td>
                  <td class="px-2 py-2.5 font-semibold text-[12px] text-[#E8ECF4] border-r border-[#2E3348] whitespace-nowrap">{{ row.细分策略 }}</td>
                  <td class="px-3 py-2.5 text-xs text-[#64748B] truncate border-r border-[#2E3348]">{{ row.标的指数 }}</td>
                  <td class="px-2 py-2.5 text-center tabular-nums text-xs font-bold text-[#3B9EFF]/80 border-r border-[#2E3348]">{{ row.当前点位 }}</td>
                  <td v-for="(count, i) in row.dist" :key="i"
                    class="px-1 py-2.5 text-center transition-colors"
                    :class="[i < 4 ? 'border-r border-[#2E3348]/40' : 'border-r border-[#2E3348]', count > 0 && count === row.maxCount ? VOTE_DIST_HL_BG[i] : '']">
                    <span v-if="count > 0" class="text-[13px] font-bold tabular-nums leading-none"
                      :class="count === row.maxCount ? VOTE_DIST_HL_TEXT[i] : 'text-[#B4BAC9]'">{{ count }}</span>
                    <span v-else class="text-[#303848] text-xs select-none">—</span>
                  </td>
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span v-if="row.totalVotes > 0"
                      class="inline-block text-xs font-bold px-1.5 py-0.5 rounded border whitespace-nowrap"
                      :class="VOTE_CONSENSUS_STYLE[row.consensusLevel]">{{ row.consensusLevel }}</span>
                    <span v-else class="text-[#3A4555]">—</span>
                  </td>
                  <td class="px-2 py-2.5 text-center tabular-nums text-xs font-mono"
                    :class="row.totalVotes > 0 ? 'text-[#3B9EFF]' : 'text-[#3A4555]'">{{ row.rangeStr }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- 投票分布可视化摘要 -->
          <div v-if="MIXED_DIST_ROWS.some(r => r.totalVotes > 0)" class="border-t border-[#252A3A] px-5 py-3 space-y-2">
            <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">投票分布可视化</div>
            <div v-for="row in MIXED_DIST_ROWS" :key="row.细分策略" v-show="row.totalVotes > 0" class="flex items-center gap-3">
              <span class="text-xs text-[#B4BAC9] w-20 shrink-0 truncate font-mono">{{ row.细分策略 }}</span>
              <div class="flex-1 h-4 rounded-full overflow-hidden flex bg-[#1A1E2B]">
                <template v-for="(count, i) in row.dist" :key="i">
                  <div v-if="count > 0"
                    :style="{ width: `${count / row.totalVotes * 100}%`, backgroundColor: ['#00C9A7', '#3B9EFF', '#3B9EFF', '#3B9EFF', '#F04864'][i] }"
                    class="h-full transition-all duration-500 min-w-[4px]"
                  ></div>
                </template>
              </div>
              <span v-if="row.totalVotes > 0"
                class="text-xs font-bold px-1.5 py-0.5 rounded border whitespace-nowrap shrink-0"
                :class="VOTE_CONSENSUS_STYLE[row.consensusLevel]">{{ row.consensusLevel }}</span>
            </div>
          </div>
          <div class="px-5 py-2 border-t border-[#2E3348] bg-[#161922] flex items-center justify-between text-xs text-[#64748B] font-mono">
            <span>众数格底色高亮 · 委员会观点 = 加权均值对应档位 · 对应点位由观点幅度规则推算</span>
            <span class="flex items-center gap-4">
              <span class="text-[#00C9A7]">▪ 谨慎(1)</span>
              <span class="text-[#3B9EFF]">▪ 中性(2-4)</span>
              <span class="text-[#F04864]">▪ 乐观(5)</span>
            </span>
          </div>
        </div>

        <!-- ── D. 会议共识与边际变化（档位结论矩阵） ── -->
        <div id="nav-vote-consensus" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>会议共识与边际变化 · 档位结论矩阵</h3>
            <span class="text-[13px] font-mono text-[#94A3B8]">综合 {{ submittedCount }} 份问卷</span>
          </div>
          <div class="p-5 grid grid-cols-3 gap-3">
            <div v-for="ca in CONSENSUS_ANALYSIS" :key="ca.asset" class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg p-3.5">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[14px] font-bold text-[#E8ECF4]">{{ ca.asset }}</span>
                <span :class="cn('text-[13px] font-mono font-bold px-2 py-1 rounded border',
                  ca.label === '乐观' ? 'bg-[#F04864]/10 text-[#F04864] border-[#F04864]/25' :
                  ca.label === '中性偏乐观' ? 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25' :
                  ca.label === '中性' ? 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25' :
                  'bg-[#00C9A7]/10 text-[#00C9A7] border-[#00C9A7]/25')">{{ ca.label }}</span>
              </div>
              <div class="flex items-baseline gap-2 mb-1.5">
                <span class="text-lg font-bold font-mono tabular-nums text-[#3B9EFF]">{{ ca.avg.toFixed(1) }}</span>
                <span class="text-[13px] font-mono" :class="ca.delta > 0 ? 'text-[#F04864]' : ca.delta < 0 ? 'text-[#00C9A7]' : 'text-[#94A3B8]'">
                  {{ ca.delta > 0 ? '+' : '' }}{{ ca.delta.toFixed(1) }} vs 上期
                  <span v-if="ca.delta > 0">&#9650;</span>
                  <span v-else-if="ca.delta < 0">&#9660;</span>
                </span>
              </div>
              <div class="flex items-center justify-between text-[13px] text-[#94A3B8]">
                <span>{{ ca.newHighCount }} 人看创新高</span>
                <span class="font-mono text-[#3B9EFF]">{{ ca.consensus }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ── E. 决策审计时间线 ── -->
        <div class="border border-[#2E3348]/50 rounded-xl overflow-hidden">
          <button @click="showDecisionTimeline = !showDecisionTimeline" class="w-full px-5 py-3.5 flex items-center justify-between hover:bg-[#252A3A]/50 transition-all">
            <div class="flex items-center space-x-3">
              <div class="w-1.5 h-4 bg-[#94A3B8] rounded-sm shrink-0"></div>
              <span class="text-[13px] font-medium text-[#94A3B8]">决策审计时间线</span>
              <span class="text-xs font-mono text-[#64748B]">{{ DECISION_TIMELINE.length }} 事件</span>
            </div>
            <div class="w-0.5 h-3.5 bg-[#64748B] rounded-full transition-transform duration-200 origin-center" :class="showDecisionTimeline ? 'rotate-90' : ''"></div>
          </button>
          <div v-if="showDecisionTimeline" class="border-t border-[#252A3A] p-5">
            <div class="space-y-4">
              <div v-for="(evt, i) in DECISION_TIMELINE" :key="i" class="flex items-start gap-3">
                <div class="flex flex-col items-center shrink-0">
                  <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: evt.color }"></div>
                  <div v-if="i < DECISION_TIMELINE.length - 1" class="w-px flex-1 min-h-[24px] bg-[#252A3A]"></div>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-bold" :style="{ color: evt.color }">{{ evt.time }}</span>
                    <span class="text-[13px] font-medium text-[#E8ECF4]">{{ evt.event }}</span>
                  </div>
                  <div class="text-xs text-[#94A3B8] mt-0.5">{{ evt.detail }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div><!-- end committee_stats -->

      <!-- ════════════════════════════════════════════════════════════
           知行果复盘 (post_mortem) · 归因与排名迁移容器
      ════════════════════════════════════════════════════════════ -->
      <div v-if="activeTab === 'post_mortem'" class="space-y-4 pb-4">

        <!-- ══════════════════════════════════════════════════════
             MODULE 1: "行"的检验 · 指引回顾与执行跟踪 (GAP-3)
        ══════════════════════════════════════════════════════ -->
        <div id="nav-exec-track" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>"行"的检验：指引回顾与执行跟踪</h3>
            <span class="text-xs font-mono text-[#94A3B8] bg-[#1A1E2B] px-2.5 py-1 rounded border border-[#252A3A]">SASA 四层对比 · 截至 2026-04-30</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full table-fixed font-mono text-xs border-collapse" style="min-width:840px">
              <colgroup>
                <col style="width:120px" /><col style="width:88px" /><col style="width:88px" />
                <col style="width:88px" /><col style="width:88px" /><col style="width:88px" />
                <col style="width:72px" /><col style="width:80px" />
              </colgroup>
              <thead class="bg-[#1A1E2B] border-b border-[#2E3348]">
                <tr>
                  <th class="px-4 py-2.5 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">资产大类</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#3B9EFF] border-r border-[#2E3348]">委员会目标%</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">部门指引%</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">产品目标%</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#E8ECF4] border-r border-[#2E3348]">实际持仓%</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">偏差(pp)</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">上限(±pp)</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8]">状态</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="row in execTrackRows" :key="row.asset">
                  <tr class="border-b border-[#252A3A] hover:bg-[#1A1E2B]/40 transition-colors"
                    :class="row.status === 'breach' ? 'bg-[#F04864]/4' : row.status === 'warn' ? 'bg-[#FFAB00]/3' : ''">
                    <td class="px-4 py-2.5 font-semibold text-[#E8ECF4] border-r border-[#252A3A]">{{ row.asset }}</td>
                    <td class="px-3 py-2.5 text-right tabular-nums text-[#3B9EFF] border-r border-[#252A3A]">{{ row.targetCmt.toFixed(1) }}</td>
                    <td class="px-3 py-2.5 text-right tabular-nums text-[#94A3B8] border-r border-[#252A3A]">{{ row.targetDept.toFixed(1) }}</td>
                    <td class="px-3 py-2.5 text-right tabular-nums text-[#94A3B8] border-r border-[#252A3A]">{{ row.targetProd.toFixed(1) }}</td>
                    <td class="px-3 py-2.5 text-right tabular-nums font-bold text-[#E8ECF4] border-r border-[#252A3A]">{{ row.actual.toFixed(1) }}</td>
                    <td class="px-3 py-2.5 text-right tabular-nums font-bold border-r border-[#252A3A]" :class="execDeviationClass(row)">
                      {{ row.deviation > 0 ? '+' : '' }}{{ row.deviation.toFixed(1) }}
                    </td>
                    <td class="px-3 py-2.5 text-center tabular-nums text-[#64748B] border-r border-[#252A3A]">±{{ row.limit }}</td>
                    <td class="px-3 py-2.5 text-center">
                      <span class="text-[10px] font-mono px-1.5 py-0.5 rounded border"
                        :class="row.status === 'breach' ? 'bg-[#F04864]/12 border-[#F04864]/30 text-[#F04864]'
                               : row.status === 'warn'   ? 'bg-[#FFAB00]/12 border-[#FFAB00]/30 text-[#FFAB00]'
                               :                          'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]'">
                        {{ row.status === 'breach' ? '超限' : row.status === 'warn' ? '预警' : '达标' }}
                      </span>
                    </td>
                  </tr>
                  <!-- 超限/预警行：投资经理反馈区 -->
                  <tr v-if="row.status !== 'ok'" class="border-b border-[#252A3A] bg-[#161922]">
                    <td colspan="8" class="px-4 py-2">
                      <div class="flex items-start gap-3">
                        <div class="w-0.5 h-full min-h-[28px] rounded-sm shrink-0 mt-1"
                          :class="row.status === 'breach' ? 'bg-[#F04864]' : 'bg-[#FFAB00]'"></div>
                        <div class="flex-1">
                          <div class="text-[10px] font-mono mb-1"
                            :class="row.status === 'breach' ? 'text-[#F04864]' : 'text-[#FFAB00]'">
                            投资经理执行反馈（{{ row.asset }}）
                          </div>
                          <textarea
                            v-model="row.feedback"
                            rows="2"
                            :placeholder="`请填写 ${row.asset} 仓位偏差原因：如市场流动性限制、执行时机滞后、赎回压力导致被动偏离等…`"
                            class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded px-3 py-1.5 text-xs font-mono text-[#E8ECF4] placeholder-[#4A5568] resize-none focus:outline-none focus:border-[#3B9EFF]/40 transition-colors"
                          ></textarea>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <div class="px-5 py-2 border-t border-[#252A3A] bg-[#161922] flex items-center gap-6 text-xs font-mono text-[#4A5568]">
            <span>SASA 层级：<span class="text-[#3B9EFF]">委员会</span> → 部门 → 产品 → <span class="text-[#E8ECF4]">实际持仓</span></span>
            <span class="text-[#F04864]">超限 = |偏差| &gt; 上限</span>
            <span class="text-[#FFAB00]">预警 = |偏差| &gt; 上限 × 0.6</span>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════════
             MODULE 2: 产品序列表现与仓位分析
        ══════════════════════════════════════════════════════ -->
        <div id="nav-product-perf" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>产品序列表现与仓位分析</h3>
            <span class="text-xs font-mono text-[#94A3B8]">费前收益率 · 竞品排名 · 近一年趋势</span>
          </div>
          <!-- 上：产品表现表格 -->
          <div class="overflow-x-auto border-b border-[#252A3A]">
            <table class="w-full table-fixed font-mono text-xs border-collapse" style="min-width:700px">
              <colgroup>
                <col style="width:140px" /><col style="width:88px" /><col style="width:88px" />
                <col style="width:120px" /><col style="width:72px" /><col style="width:120px" /><col style="width:72px" />
              </colgroup>
              <thead class="bg-[#1A1E2B] border-b border-[#2E3348]">
                <tr>
                  <th class="px-4 py-2.5 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">产品类型</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">YTD 费前</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">近1年 费前</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">竞品排名 (YTD)</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">前%</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">竞品排名 (近1年)</th>
                  <th class="px-3 py-2.5 text-center text-[11px] font-bold text-[#94A3B8]">前%</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="r in PRODUCT_PERF_ROWS" :key="r.name"
                  class="hover:bg-[#1A1E2B]/40 transition-colors">
                  <td class="px-4 py-2.5 font-semibold text-[#E8ECF4] border-r border-[#252A3A]">{{ r.name }}</td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-bold border-r border-[#252A3A]"
                    :class="r.ytdGross >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                    {{ r.ytdGross >= 0 ? '+' : '' }}{{ r.ytdGross.toFixed(2) }}%
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-bold border-r border-[#252A3A]"
                    :class="r.y1Gross >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                    {{ r.y1Gross >= 0 ? '+' : '' }}{{ r.y1Gross.toFixed(2) }}%
                  </td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-[#B4BAC9] border-r border-[#252A3A]">{{ r.ytdRank }}</td>
                  <td class="px-3 py-2.5 text-center border-r border-[#252A3A]">
                    <span class="font-bold tabular-nums"
                      :class="r.ytdRankPct <= 20 ? 'text-[#F04864]' : r.ytdRankPct <= 40 ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">
                      前{{ r.ytdRankPct }}%
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-[#B4BAC9] border-r border-[#252A3A]">{{ r.y1Rank }}</td>
                  <td class="px-3 py-2.5 text-center">
                    <span class="font-bold tabular-nums"
                      :class="r.y1RankPct <= 20 ? 'text-[#F04864]' : r.y1RankPct <= 40 ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">
                      前{{ r.y1RankPct }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- 下：久期及权益仓位双轴图 -->
          <div class="p-4">
            <div class="text-xs font-mono text-[#94A3B8] mb-2">久期中枢（左轴） / 权益仓位%（右轴） · 近12月</div>
            <div ref="positionChartRef" style="height:240px;width:100%"></div>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════════
             MODULE 3: 收益来源与择时择券分析 (GAP-6)
        ══════════════════════════════════════════════════════ -->
        <div id="nav-return-decomp" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>收益来源与择时择券分析 · Brinson 三层归因</h3>
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-mono text-[#64748B]">选择产品：</span>
              <div class="flex gap-1">
                <button
                  v-for="(r, i) in RETURN_DECOMP_ROWS" :key="r.product"
                  @click="brinsonSelectedIdx = i"
                  class="text-[10px] font-mono px-2 py-0.5 rounded border transition-colors"
                  :class="brinsonSelectedIdx === i
                    ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                    : 'border-[#252A3A] text-[#4A5568] hover:border-[#3B9EFF]/25 hover:text-[#94A3B8]'"
                >{{ r.product }}</button>
              </div>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-0 divide-x divide-[#252A3A]">
            <!-- 左：收益分解表 -->
            <div class="overflow-x-auto">
              <table class="w-full table-fixed font-mono text-xs border-collapse">
                <colgroup>
                  <col style="width:130px" /><col style="width:72px" />
                  <col style="width:72px" /><col style="width:64px" />
                  <col style="width:72px" /><col style="width:72px" />
                </colgroup>
                <thead class="bg-[#1A1E2B] border-b border-[#2E3348]">
                  <tr>
                    <th class="px-4 py-2.5 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">产品</th>
                    <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">YTD年化%</th>
                    <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">Beta%</th>
                    <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">Alpha%</th>
                    <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">择时(bp)</th>
                    <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8]">择券(bp)</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#252A3A]">
                  <tr v-for="r in RETURN_DECOMP_ROWS" :key="r.product"
                    class="hover:bg-[#1A1E2B]/40 transition-colors cursor-pointer"
                    :class="RETURN_DECOMP_ROWS.indexOf(r) === brinsonSelectedIdx ? 'bg-[#3B9EFF]/5' : ''"
                    @click="brinsonSelectedIdx = RETURN_DECOMP_ROWS.indexOf(r)">
                    <td class="px-4 py-2 font-semibold text-[#E8ECF4] border-r border-[#252A3A]">{{ r.product }}</td>
                    <td class="px-3 py-2 text-right tabular-nums font-bold border-r border-[#252A3A]"
                      :class="r.ytdAnn >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                      {{ r.ytdAnn >= 0 ? '+' : '' }}{{ r.ytdAnn.toFixed(2) }}
                    </td>
                    <td class="px-3 py-2 text-right tabular-nums text-[#3B9EFF] border-r border-[#252A3A]">{{ r.beta.toFixed(1) }}</td>
                    <td class="px-3 py-2 text-right tabular-nums border-r border-[#252A3A]"
                      :class="r.alpha >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">{{ r.alpha.toFixed(1) }}</td>
                    <td class="px-3 py-2 text-right tabular-nums border-r border-[#252A3A]"
                      :class="r.timing >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                      {{ r.timing > 0 ? '+' : '' }}{{ r.timing }}
                    </td>
                    <td class="px-3 py-2 text-right tabular-nums"
                      :class="r.selection >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                      {{ r.selection > 0 ? '+' : '' }}{{ r.selection }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- 右：Brinson 瀑布图 -->
            <div class="p-4 flex flex-col">
              <div class="flex items-center gap-2 mb-2">
                <div class="w-0.5 h-3.5 rounded-sm bg-[#3B9EFF]/70 shrink-0"></div>
                <span class="text-xs font-mono text-[#94A3B8]">
                  Brinson 超额拆解 · {{ RETURN_DECOMP_ROWS[brinsonSelectedIdx]?.product }}
                </span>
                <span class="ml-auto text-[11px] font-mono text-[#64748B]">单位: bp</span>
              </div>
              <VChart :option="brinsonChartOption" autoresize style="flex:1;min-height:200px" />
              <div class="flex items-center gap-4 mt-2 text-xs font-mono text-[#4A5568]">
                <span><span class="inline-block w-3 h-2 rounded-sm bg-[#3B9EFF] mr-1"></span>基准/汇总</span>
                <span><span class="inline-block w-3 h-2 rounded-sm bg-[#F04864] mr-1"></span>正贡献</span>
                <span><span class="inline-block w-3 h-2 rounded-sm bg-[#00C9A7] mr-1"></span>负贡献</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════════════
             MODULE 4: "果"的检验 · 策略库建设与 SPV 评价
        ══════════════════════════════════════════════════════ -->
        <div id="nav-spv-eval" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>"果"的检验：策略库建设与 SPV 评价</h3>
            <button class="flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded border border-[#3B9EFF]/30 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 transition-colors">
              <div class="w-0.5 h-3 bg-current rounded-sm shrink-0"></div>导出数据 (Excel)
            </button>
          </div>

          <!-- SPV 资源分配效率汇总卡片 -->
          <div class="px-5 py-4 border-b border-[#252A3A] grid grid-cols-3 gap-4">
            <div class="bg-[#1A1E2B] border border-[#F04864]/20 rounded-xl p-4 space-y-1.5">
              <div class="flex items-center gap-1.5">
                <div class="w-0.5 h-4 rounded-sm bg-[#F04864] shrink-0"></div>
                <span class="text-[11px] font-mono text-[#94A3B8]">超跑为正的 SPV</span>
              </div>
              <div class="flex items-baseline gap-2 mt-1">
                <span class="text-2xl font-mono font-bold tabular-nums text-[#F04864]">{{ SPV_STATS.posScale }}</span>
                <span class="text-xs font-mono text-[#64748B]">亿元</span>
                <span class="text-xs font-mono font-bold text-[#F04864] ml-auto">{{ SPV_STATS.posPct }}%</span>
              </div>
              <div class="text-[11px] font-mono text-[#64748B]">
                {{ SPV_STATS.posCount }} 个 SPV 超跑为正，占总规模 {{ SPV_STATS.posPct }}%
              </div>
            </div>
            <div class="bg-[#1A1E2B] border border-[#3B9EFF]/20 rounded-xl p-4 space-y-1.5">
              <div class="flex items-center gap-1.5">
                <div class="w-0.5 h-4 rounded-sm bg-[#3B9EFF] shrink-0"></div>
                <span class="text-[11px] font-mono text-[#94A3B8]">超额/下行波动 前 30% SPV</span>
              </div>
              <div class="flex items-baseline gap-2 mt-1">
                <span class="text-2xl font-mono font-bold tabular-nums text-[#3B9EFF]">{{ SPV_STATS.top30Scale }}</span>
                <span class="text-xs font-mono text-[#64748B]">亿元</span>
                <span class="text-xs font-mono font-bold text-[#3B9EFF] ml-auto">{{ SPV_STATS.top30Pct }}%</span>
              </div>
              <div class="text-[11px] font-mono text-[#64748B]">
                风险调整收益最优 SPV 获配投资规模占比 {{ SPV_STATS.top30Pct }}%
              </div>
            </div>
            <div class="bg-[#1A1E2B] border border-[#94A3B8]/20 rounded-xl p-4 space-y-1.5">
              <div class="flex items-center gap-1.5">
                <div class="w-0.5 h-4 rounded-sm bg-[#94A3B8] shrink-0"></div>
                <span class="text-[11px] font-mono text-[#94A3B8]">超额/下行波动 前 50% SPV</span>
              </div>
              <div class="flex items-baseline gap-2 mt-1">
                <span class="text-2xl font-mono font-bold tabular-nums text-[#E8ECF4]">{{ SPV_STATS.top50Scale }}</span>
                <span class="text-xs font-mono text-[#64748B]">亿元</span>
                <span class="text-xs font-mono font-bold text-[#94A3B8] ml-auto">{{ SPV_STATS.top50Pct }}%</span>
              </div>
              <div class="text-[11px] font-mono text-[#64748B]">
                综合效率中位以上 SPV 获配规模占比 {{ SPV_STATS.top50Pct }}%
              </div>
            </div>
          </div>

          <!-- SPV 高密度数据表 -->
          <div class="overflow-x-auto">
            <table class="w-full table-fixed font-mono text-xs border-collapse" style="min-width:740px">
              <colgroup>
                <col style="width:108px" /><col style="width:88px" /><col style="width:88px" />
                <col style="width:120px" /><col style="width:110px" /><col style="width:120px" />
              </colgroup>
              <thead class="bg-[#1A1E2B] border-b border-[#2E3348]">
                <tr>
                  <th class="px-4 py-2.5 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">策略标签</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">YTD绝对收益</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">超跑%</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">今年以来平均规模(万)</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">超额/下行波动率</th>
                  <th class="px-3 py-2.5 text-right text-[11px] font-bold text-[#94A3B8]">策略池收益贡献(万)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="row in SPV_ROWS" :key="row.label"
                  class="transition-colors hover:opacity-90"
                  :class="spvRowClass(row)">
                  <td class="px-4 py-2.5 font-semibold border-r border-[#252A3A]"
                    :class="row.outpct >= 1.5 ? 'text-[#F04864]' : row.outpct <= -2 ? 'text-[#00C9A7]' : 'text-[#E8ECF4]'">
                    {{ row.label }}
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-bold border-r border-[#252A3A]"
                    :class="row.ytdAbs >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                    {{ row.ytdAbs >= 0 ? '+' : '' }}{{ row.ytdAbs.toFixed(1) }}%
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-bold border-r border-[#252A3A]"
                    :class="row.outpct > 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                    {{ row.outpct > 0 ? '+' : '' }}{{ row.outpct.toFixed(1) }}%
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums text-[#B4BAC9] border-r border-[#252A3A]">
                    {{ row.avgScale.toLocaleString() }}
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums border-r border-[#252A3A]"
                    :class="row.excessDownVol >= 2 ? 'text-[#F04864]' : row.excessDownVol >= 1 ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">
                    {{ row.excessDownVol.toFixed(2) }}
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-bold"
                    :class="row.poolContrib >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                    {{ row.poolContrib >= 0 ? '+' : '' }}{{ row.poolContrib.toFixed(1) }}
                  </td>
                </tr>
              </tbody>
              <tfoot class="border-t-2 border-[#2E3348] bg-[#1A1E2B]">
                <tr>
                  <td class="px-4 py-2.5 font-bold text-[#94A3B8] border-r border-[#252A3A]">合计</td>
                  <td class="px-3 py-2.5 text-right tabular-nums text-[#64748B] border-r border-[#252A3A]">—</td>
                  <td class="px-3 py-2.5 text-right tabular-nums text-[#64748B] border-r border-[#252A3A]">—</td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-bold text-[#E8ECF4] border-r border-[#252A3A]">
                    {{ SPV_ROWS.reduce((s,r) => s + r.avgScale, 0).toLocaleString() }}
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums text-[#64748B] border-r border-[#252A3A]">—</td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-bold"
                    :class="SPV_ROWS.reduce((s,r) => s + r.poolContrib, 0) >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                    {{ SPV_ROWS.reduce((s,r) => s + r.poolContrib, 0) >= 0 ? '+' : '' }}{{ SPV_ROWS.reduce((s,r) => s + r.poolContrib, 0).toFixed(1) }}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div class="px-5 py-2 border-t border-[#252A3A] bg-[#161922] flex items-center gap-6 text-xs font-mono text-[#4A5568]">
            <span>行高亮：<span class="text-[#F04864]">红底 = 超跑 &ge;+1.5%（显著正贡献）</span> · <span class="text-[#00C9A7]">绿底 = 超跑 &le;-2.0%（显著拖累）</span></span>
            <span class="ml-auto">超额/下行波动：<span class="text-[#F04864]">&ge;2.0 优秀</span> / <span class="text-[#3B9EFF]">1.0-2.0 良好</span></span>
          </div>
        </div>

        <!-- ────── 旧归因内容：已由上方 4 个模块替代，隐藏待清理 ────── -->
        <div class="hidden">
        <div id="nav-return-compare" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>指引表现 · 收益曲线回溯对比</h3>
            <span class="text-xs font-mono text-[#94A3B8] bg-[#1A1E2B] px-2.5 py-1 rounded border border-[#252A3A]">区间: 2025.10 — 2026.03</span>
          </div>
          <div class="p-5">
            <div class="relative h-[180px] w-full">
              <svg class="absolute inset-0 w-full h-full" viewBox="0 0 760 160" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="fillBlue2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#3B9EFF" stop-opacity="0.12" />
                    <stop offset="100%" stop-color="#3B9EFF" stop-opacity="0" />
                  </linearGradient>
                </defs>
                <line x1="0" y1="20" x2="760" y2="20" stroke="#252A3A" stroke-width="1" />
                <line x1="0" y1="60" x2="760" y2="60" stroke="#252A3A" stroke-width="1" />
                <line x1="0" y1="100" x2="760" y2="100" stroke="#252A3A" stroke-width="1" />
                <line x1="0" y1="140" x2="760" y2="140" stroke="#2E3348" stroke-width="1" />
                <line x1="127" y1="0" x2="127" y2="140" stroke="#252A3A" stroke-width="0.5" stroke-dasharray="3,4" />
                <line x1="254" y1="0" x2="254" y2="140" stroke="#252A3A" stroke-width="0.5" stroke-dasharray="3,4" />
                <line x1="381" y1="0" x2="381" y2="140" stroke="#252A3A" stroke-width="0.5" stroke-dasharray="3,4" />
                <line x1="508" y1="0" x2="508" y2="140" stroke="#252A3A" stroke-width="0.5" stroke-dasharray="3,4" />
                <line x1="635" y1="0" x2="635" y2="140" stroke="#252A3A" stroke-width="0.5" stroke-dasharray="3,4" />
                <path d="M0,120 L127,104 L254,82 L381,74 L508,58 L635,52 L760,44 L760,140 L0,140 Z" fill="url(#fillBlue2)" />
                <polyline points="0,120 127,104 254,82 381,74 508,58 635,52 760,44" fill="none" stroke="#3B9EFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
                <polyline points="0,120 127,110 254,92 381,85 508,76 635,68 760,62" fill="none" stroke="#3B9EFF" stroke-width="2" stroke-dasharray="7,4" stroke-linecap="round" />
                <polyline points="0,120 127,106 254,86 381,95 508,64 635,50 760,40" fill="none" stroke="#3B9EFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
                <circle v-for="(pt, i) in [[127,106],[254,86],[381,95],[508,64],[635,50],[760,40]]" :key="i" :cx="pt[0]" :cy="pt[1]" r="3" fill="#3B9EFF" />
              </svg>
              <div class="absolute left-0 top-0 bottom-5 flex flex-col justify-between text-xs font-mono text-[#6B7280] pointer-events-none">
                <span>+5.5%</span><span>+3.8%</span><span>+2.1%</span><span>+0.4%</span>
              </div>
              <div class="absolute bottom-0 left-6 right-0 flex justify-between text-xs font-mono text-[#6B7280]">
                <span>Oct '25</span><span>Nov '25</span><span>Dec '25</span><span>Jan '26</span><span>Feb '26</span><span>Mar '26</span>
              </div>
            </div>
            <div class="flex items-center space-x-6 mt-4 pl-6">
              <div class="flex items-center space-x-2"><div class="w-7 h-[2.5px] bg-[#3B9EFF] rounded-full"></div><span class="text-xs text-[#B4BAC9] font-mono">委员会指引</span></div>
              <div class="flex items-center space-x-2"><svg width="28" height="3"><line x1="0" y1="1.5" x2="28" y2="1.5" stroke="#3B9EFF" stroke-width="2" stroke-dasharray="5,3" /></svg><span class="text-xs text-[#B4BAC9] font-mono">部门指引</span></div>
              <div class="flex items-center space-x-2"><div class="w-7 h-[2.5px] bg-[#3B9EFF] rounded-full"></div><span class="text-xs text-[#B4BAC9] font-mono">实际收益</span></div>
            </div>

            <!-- ── 指引表现总结区 ───────────────────────────────────── -->
            <div class="mt-5 grid grid-cols-2 gap-4">
              <!-- 定量分析 (系统自动生成) -->
              <div class="bg-[#0D1520] border border-[#3B9EFF]/20 rounded-lg p-4">
                <div class="flex items-center space-x-2 mb-2.5">
                  <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0 animate-pulse"></div>
                  <span class="text-xs font-mono text-[#3B9EFF] uppercase tracking-widest">【定量分析】 · 系统自动生成</span>
                </div>
                <p class="text-[13px] leading-[1.7] text-[#B4BAC9] font-mono">{{ guidanceQuantAnalysis }}</p>
              </div>
              <!-- 定性评价 (PM 可编辑) -->
              <div class="bg-[#0D1520] border border-[#3B9EFF]/20 rounded-lg p-4 flex flex-col">
                <div class="flex items-center space-x-2 mb-2.5">
                  <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                  <span class="text-xs font-mono text-[#3B9EFF] uppercase tracking-widest">【定性评价】 · PM 主观复盘</span>
                </div>
                <template v-if="isSecretary || isChairman">
                  <textarea
                    v-model="guidanceQualReview"
                    rows="4"
                    placeholder="请 PM 填写上期指引执行情况的主观复盘，包括策略偏离原因、市场判断依据、改进方向等…"
                    class="flex-1 bg-transparent border border-[#3B9EFF]/15 rounded text-[13px] leading-[1.7] text-[#E8ECF4] font-mono placeholder-[#4A5568] p-2.5 resize-none focus:outline-none focus:border-[#3B9EFF]/40 transition-colors"
                  ></textarea>
                </template>
                <template v-else>
                  <p class="flex-1 text-[13px] leading-[1.7] text-[#B4BAC9] font-mono min-h-[5rem]">
                    {{ guidanceQualReview || '—' }}
                  </p>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- ── 产品表现：三类别深度视图 ────────────────────────────── -->
        <div id="nav-perf-attrib" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>产品类别表现 · 深度绩效归因</h3>
            <div class="flex items-center space-x-2">
              <div class="w-1.5 h-1.5 rounded-full bg-[#34C759] shrink-0"></div>
              <span class="text-xs font-mono text-[#94A3B8]">最后同步 09:47:32</span>
            </div>
          </div>
          <div class="p-5 space-y-6">
            <div v-for="cat in PRODUCT_CATEGORIES" :key="cat.label">
              <!-- 类别标题行 -->
              <div class="flex items-center space-x-3 mb-3">
                <div class="h-px flex-1 bg-gradient-to-r from-transparent" :style="{ backgroundImage: `linear-gradient(to right, transparent, ${cat.color}33)` }"></div>
                <span class="text-xs font-bold font-mono uppercase tracking-widest px-3 py-1 rounded border" :style="{ color: cat.color, borderColor: cat.color + '40', background: cat.color + '12' }">
                  【{{ cat.label }}】 · {{ cat.tag }}
                </span>
                <div class="h-px flex-1 bg-gradient-to-l from-transparent" :style="{ backgroundImage: `linear-gradient(to left, transparent, ${cat.color}33)` }"></div>
              </div>
              <!-- 产品卡片列表 -->
              <div class="space-y-3">
                <div v-for="item in cat.items" :key="item.name"
                     class="bg-[#1A1E2B] border rounded-xl px-4 py-3.5 transition-colors hover:border-white/10"
                     :style="{ borderColor: (item.ret >= 0 ? '#3B9EFF' : '#F04864') + '28' }">
                  <!-- 顶行: 名称 + 竞品排名 + 区间收益 -->
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-3">
                      <span class="text-[14px] font-semibold text-[#E8ECF4]">{{ item.name }}</span>
                      <!-- 竞品排名徽章 -->
                      <span class="text-xs font-bold font-mono px-2 py-1 rounded-full border"
                            :class="item.rankTier === 1 ? 'bg-[#F04864]/10 border-[#F04864]/35 text-[#F04864]' : item.rankTier === 2 ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/35 text-[#3B9EFF]' : 'bg-[#00C9A7]/10 border-[#00C9A7]/35 text-[#00C9A7]'">
                        {{ item.rank }}
                      </span>
                      <span class="text-xs font-mono text-[#6B7280]">竞品排名</span>
                    </div>
                    <div class="text-right">
                      <span class="text-[14px] font-bold font-mono" :class="item.ret >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                        {{ item.ret >= 0 ? '+' : '' }}{{ item.ret.toFixed(1) }}%
                      </span>
                      <span class="text-xs font-mono text-[#6B7280] ml-1.5">区间收益</span>
                    </div>
                  </div>
                  <!-- 收益来源分析 + 择时择券评价 双列 -->
                  <div class="grid grid-cols-2 gap-4">
                    <!-- 收益来源分析 -->
                    <div>
                      <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-widest mb-2">收益来源分析</div>
                      <div class="space-y-1.5">
                        <div class="flex items-center justify-between">
                          <span class="text-xs font-mono text-[#6B7280] w-16">Beta 收益</span>
                          <div class="flex-1 mx-2 h-1.5 bg-[#252A3A] rounded-full overflow-hidden">
                            <div class="h-full rounded-full" :style="{ width: `${Math.abs(item.beta) / 5 * 100}%`, background: item.beta >= 0 ? '#3B9EFF' : '#F04864' }"></div>
                          </div>
                          <span class="text-xs font-mono w-10 text-right" :class="item.beta >= 0 ? 'text-[#3B9EFF]' : 'text-[#F04864]'">{{ item.beta >= 0 ? '+' : '' }}{{ item.beta.toFixed(1) }}%</span>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs font-mono text-[#6B7280] w-16">Alpha 收益</span>
                          <div class="flex-1 mx-2 h-1.5 bg-[#252A3A] rounded-full overflow-hidden">
                            <div class="h-full rounded-full" :style="{ width: `${Math.abs(item.alpha) / 5 * 100}%`, background: item.alpha >= 0 ? '#3B9EFF' : '#F04864' }"></div>
                          </div>
                          <span class="text-xs font-mono w-10 text-right" :class="item.alpha >= 0 ? 'text-[#3B9EFF]' : 'text-[#F04864]'">{{ item.alpha >= 0 ? '+' : '' }}{{ item.alpha.toFixed(1) }}%</span>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs font-mono text-[#6B7280] w-16">杠杆收益</span>
                          <div class="flex-1 mx-2 h-1.5 bg-[#252A3A] rounded-full overflow-hidden">
                            <div class="h-full rounded-full" :style="{ width: `${Math.abs(item.lev) / 2 * 100}%`, background: item.lev >= 0 ? '#3B9EFF' : '#F04864' }"></div>
                          </div>
                          <span class="text-xs font-mono w-10 text-right" :class="item.lev >= 0 ? 'text-[#3B9EFF]' : 'text-[#F04864]'">{{ item.lev >= 0 ? '+' : '' }}{{ item.lev.toFixed(1) }}%</span>
                        </div>
                      </div>
                    </div>
                    <!-- 择时择券评价 + 最大回撤 -->
                    <div>
                      <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-widest mb-2">择时择券评价</div>
                      <div class="space-y-1.5">
                        <div class="flex items-center justify-between">
                          <span class="text-xs font-mono text-[#6B7280] w-20">调仓贡献度</span>
                          <div class="flex-1 mx-2 h-1.5 bg-[#252A3A] rounded-full overflow-hidden">
                            <div class="h-full rounded-full" :style="{ width: `${Math.min(100, Math.abs(item.timing) / 25 * 100)}%`, background: item.timing >= 0 ? '#3B9EFF' : '#F04864' }"></div>
                          </div>
                          <span class="text-xs font-mono w-14 text-right" :class="item.timing >= 0 ? 'text-[#3B9EFF]' : 'text-[#F04864]'">{{ item.timing >= 0 ? '+' : '' }}{{ item.timing }} bps</span>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs font-mono text-[#6B7280] w-20">择券胜率</span>
                          <div class="flex-1 mx-2 h-1.5 bg-[#252A3A] rounded-full overflow-hidden">
                            <div class="h-full rounded-full" :style="{ width: `${item.selRate}%`, background: item.selRate >= 60 ? '#F04864' : item.selRate >= 50 ? '#3B9EFF' : '#00C9A7' }"></div>
                          </div>
                          <span class="text-xs font-mono w-14 text-right" :class="item.selRate >= 60 ? 'text-[#F04864]' : item.selRate >= 50 ? 'text-[#3B9EFF]' : 'text-[#00C9A7]'">{{ item.selRate }}%</span>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-xs font-mono text-[#6B7280] w-20">最大回撤</span>
                          <div class="flex-1 mx-2"></div>
                          <span class="text-xs font-mono text-[#F04864] w-14 text-right">{{ item.maxdd }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div id="nav-strategy-rank" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>策略池红黑榜 · 本季度末综合评估</h3>
          </div>
          <div class="p-5 grid grid-cols-2 gap-5">
            <div>
              <div class="flex items-center space-x-2 mb-3">
                <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF]"></div>
                <span class="text-xs font-mono text-[#3B9EFF] uppercase tracking-wider">Top 5 优选子策略</span>
              </div>
              <div class="space-y-2">
                <div v-for="(s, i) in TOP_STRATEGIES" :key="i" class="bg-[#1A1E2B] border border-[#3B9EFF]/10 rounded-lg px-4 py-3 flex items-center justify-between hover:border-[#3B9EFF]/25 transition-colors">
                  <div class="flex items-center space-x-3">
                    <span class="text-xs font-bold font-mono text-[#3B9EFF]/50 w-4 shrink-0">#{{ i + 1 }}</span>
                    <div>
                      <div class="text-[14px] font-medium text-[#E8ECF4]">{{ s.name }}</div>
                      <div class="text-xs text-[#94A3B8] font-mono mt-0.5">{{ s.type }}</div>
                    </div>
                  </div>
                  <div class="text-right shrink-0 ml-3">
                    <div class="text-[14px] font-bold font-mono text-[#3B9EFF]">{{ s.return }}</div>
                    <div class="text-xs text-[#94A3B8] font-mono">夏普 {{ s.sharpe }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <div class="flex items-center space-x-2 mb-3">
                <div class="w-1.5 h-1.5 rounded-full bg-[#FF3B30] animate-pulse"></div>
                <span class="text-xs font-mono text-[#FF3B30] uppercase tracking-wider">需检视劣后策略</span>
                <span class="text-xs font-mono text-[#FF3B30]/60 bg-[#FF3B30]/10 border border-[#FF3B30]/20 px-1.5 py-1 rounded">预警</span>
              </div>
              <div class="space-y-2">
                <div v-for="(s, i) in BOTTOM_STRATEGIES" :key="i" class="bg-[#1A1E2B] border border-[#FF3B30]/15 rounded-lg px-4 py-3 flex items-center justify-between hover:border-[#FF3B30]/30 transition-colors">
                  <div class="flex items-center space-x-3">
                    <div class="w-1 h-8 rounded-full bg-[#FF3B30]/50 shrink-0"></div>
                    <div>
                      <div class="text-[14px] font-medium text-[#E8ECF4]">{{ s.name }}</div>
                      <div class="text-xs text-[#FF3B30]/70 font-mono mt-0.5">{{ s.issue }}</div>
                    </div>
                  </div>
                  <div class="text-right shrink-0 ml-3">
                    <div class="text-[14px] font-bold font-mono text-[#FF3B30]">{{ s.return }}</div>
                    <div class="text-xs text-[#94A3B8] font-mono">最大回撤 {{ s.maxdd }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ 上期决议胜率复盘 ══ -->
        <div id="nav-win-review" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>上期决议胜率复盘 · 2026 Q1</h3>
            <span class="text-xs font-mono px-2.5 py-1 rounded border border-[#3B9EFF]/30 text-[#3B9EFF] bg-[#3B9EFF]/6">复盘区间: 2025.12.20 — 2026.03.28</span>
          </div>

          <!-- 汇总文案 -->
          <div class="px-5 py-3 border-b border-[#252A3A] bg-[#1A1E2B]/50">
            <p class="text-[12px] font-mono leading-relaxed text-[#B4BAC9]">
              上期共对
              <span class="text-[#E8ECF4] font-bold">{{ PREV_REVIEW_SUMMARY.totalDirectional }}</span>
              项资产给出明确方向指引，其中
              <span class="font-bold" :class="PREV_REVIEW_SUMMARY.winRate >= 70 ? 'text-[#34C759]' : 'text-[#3B9EFF]'">{{ PREV_REVIEW_SUMMARY.correctCount }}</span>
              项方向正确，整体胜率
              <span class="text-[#3B9EFF] font-bold tabular-nums">{{ PREV_REVIEW_SUMMARY.winRate }}%</span>。
              <template v-if="PREV_REVIEW_SUMMARY.bestAsset">
                其中【<span class="text-[#34C759] font-bold">{{ PREV_REVIEW_SUMMARY.bestAsset }}</span>】策略产生显著超额（{{ PREV_REVIEW_SUMMARY.bestChange }}）。
              </template>
              <template v-if="PREV_REVIEW_SUMMARY.missAssets.length">
                【<span class="text-[#FF3B30]">{{ PREV_REVIEW_SUMMARY.missAssets.join('、') }}</span>】出现方向偏差。
              </template>
            </p>
          </div>

          <!-- 复盘表格 -->
          <div class="overflow-x-auto">
            <table class="w-full border-collapse table-fixed font-mono text-[12px]" style="min-width:660px">
              <colgroup>
                <col style="width:84px" />
                <col style="width:110px" />
                <col style="width:92px" />
                <col style="width:92px" />
                <col style="width:90px" />
                <col style="width:160px" />
              </colgroup>
              <thead class="bg-[#1A1E2B] border-b border-[#2E3348]">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">细分策略</th>
                  <th class="px-3 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">上期委员会观点</th>
                  <th class="px-3 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] whitespace-nowrap">上期决策点位</th>
                  <th class="px-3 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] whitespace-nowrap">当前实际点位</th>
                  <th class="px-3 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348]">实际涨跌幅</th>
                  <th class="px-3 py-2 text-center text-xs font-bold text-[#94A3B8]">观点验证</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="row in PREV_REVIEW_ROWS" :key="row.asset"
                  class="hover:bg-[#1A1E2B]/40 transition-colors"
                  :class="row.verdict === 'wrong' ? 'bg-[#FF3B30]/3' : row.verdict === 'correct' ? 'bg-[#34C759]/2' : ''">
                  <td class="px-3 py-2.5 font-semibold text-[12px] text-[#E8ECF4] border-r border-[#2E3348]">{{ row.asset }}</td>
                  <td class="px-3 py-2.5 text-center border-r border-[#2E3348]">
                    <span class="text-xs font-bold px-1.5 py-0.5 rounded border whitespace-nowrap"
                      :class="VOTE_CONSENSUS_STYLE[row.prevView]">{{ row.prevView }}</span>
                  </td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-xs text-[#94A3B8] border-r border-[#2E3348]">{{ row.prevPoint }}</td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-xs font-bold text-[#E8ECF4] border-r border-[#2E3348]">{{ row.currPoint }}</td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-[12px] font-bold border-r border-[#2E3348]"
                    :class="row.changeVal > 0 ? 'text-[#F04864]' : row.changeVal < 0 ? 'text-[#34C759]' : 'text-[#94A3B8]'">
                    {{ row.changeStr }}
                  </td>
                  <td class="px-3 py-2.5 text-center">
                    <span class="text-xs font-bold" :class="{
                      'text-[#34C759]': row.verdict === 'correct',
                      'text-[#FF3B30]': row.verdict === 'wrong',
                      'text-[#3B9EFF]': row.verdict === 'neutral_ok' || row.verdict === 'neutral_fail',
                    }">{{ row.verdictLabel }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 底部图例 -->
          <div class="px-5 py-2 border-t border-[#2E3348] bg-[#161922] flex flex-wrap items-center gap-4 text-xs font-mono text-[#64748B]">
            <span class="text-[#34C759]">✓ 方向正确</span>
            <span class="text-[#FF3B30]">✗ 方向偏差</span>
            <span class="text-[#3B9EFF]">● 震荡区间内</span>
            <span class="text-[#3B9EFF]">△ 超出震荡区间</span>
            <span class="ml-auto opacity-70">bp型：负值=利率下行=债券价格上涨</span>
          </div>
        </div>

        <!-- ══ 经典模型量化参考 ═══ -->
        <div id="nav-model-ref" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div
            class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between gap-3 cursor-pointer select-none hover:bg-[#2A3044]/20 transition-colors"
            role="button"
            :aria-expanded="showModelAnchors"
            tabindex="0"
            @click="showModelAnchors = !showModelAnchors"
            @keydown.enter.prevent="showModelAnchors = !showModelAnchors"
            @keydown.space.prevent="showModelAnchors = !showModelAnchors"
          >
            <h3 class="am-title-l2 min-w-0 flex-1"><div class="am-title-bar"></div>经典模型量化参考 · 建议配置比例</h3>
            <button
              type="button"
              @click.stop="showModelAnchors = !showModelAnchors"
              class="shrink-0 text-[#3B9EFF] text-[12px] font-mono flex items-center gap-1.5 px-1.5 py-1 rounded border border-[#3B9EFF]/25 bg-[#3B9EFF]/5 hover:bg-[#3B9EFF]/10 transition-colors"
            >
              <span>{{ showModelAnchors ? '收起' : '展开' }}</span>
              <component :is="showModelAnchors ? ArrowUp : ArrowDown" class="w-3.5 h-3.5" />
            </button>
          </div>
          <div v-show="showModelAnchors" class="p-5 grid grid-cols-3 gap-4">
            <div
              v-for="m in MODEL_OUTPUTS" :key="m.name"
              :class="cn(
                'bg-[#1A1E2B] border rounded-xl p-4 flex flex-col space-y-3 transition-all duration-200',
                m.highlight ? 'border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.07)]' : 'border-[#252A3A] hover:border-[#2E3348]'
              )"
            >
              <div class="flex items-start justify-between">
                <div>
                  <span class="text-xs font-mono px-2 py-1 rounded-full border" :style="{ color: m.color, borderColor: m.color + '40', backgroundColor: m.color + '15' }">{{ m.badge }}</span>
                  <div class="text-[15px] font-bold text-white mt-1.5">{{ m.name }}</div>
                  <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">{{ m.desc }}</div>
                </div>
              </div>
              <div class="space-y-2">
                <div v-for="alloc in m.allocations" :key="alloc.label" class="space-y-1">
                  <div class="flex justify-between">
                    <span class="text-xs text-[#94A3B8] font-mono">{{ alloc.label }}</span>
                    <span class="text-xs font-bold font-mono text-white">{{ alloc.weight }}%</span>
                  </div>
                  <div class="h-1.5 bg-[#161922] rounded-full overflow-hidden">
                    <div :style="{ width: `${alloc.weight}%`, backgroundColor: alloc.color }" class="h-full rounded-full"></div>
                  </div>
                </div>
              </div>
              <div class="pt-1 border-t border-[#252A3A] mt-auto space-y-1.5">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <span class="text-xs font-mono text-[#6B7280]">预期夏普: <span class="text-[#3B9EFF]">{{ m.sharpe }}</span></span>
                  <button
                    v-if="m.action"
                    type="button"
                    @click="showSAASandbox = true"
                    class="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 transition-colors"
                  >
                    <span>{{ m.actionLabel || '进入沙盘' }}</span>
                    <div class="w-0.5 h-3 bg-current rounded-sm shrink-0"></div>
                  </button>
                </div>
                <div class="flex justify-end">
                  <button
                    type="button"
                    @click.stop="openModelCenter"
                    class="text-[#3B9EFF] text-xs font-mono flex items-center gap-0.5 hover:opacity-90 transition-opacity"
                  >
                    <div class="w-1 h-2.5 bg-current rounded-sm shrink-0"></div>
                    <span>模型详情</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div><!-- end hidden legacy content -->
      </div>

      <!-- ═══ 配置指引 · 决策前参考区 (allocation Tab) ═══ -->
      <div v-if="activeTab === 'allocation'" class="space-y-4 pb-4">

        <!-- ── 三栏参考看板 ── -->
        <div id="nav-alloc-ref" class="grid grid-cols-3 gap-4">

          <!-- ① 委员会投票结论汇总 -->
          <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden flex flex-col">
            <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-4 py-3 flex items-center gap-2">
              <div class="am-title-bar shrink-0"></div>
              <h3 class="text-[13px] font-bold text-[#E8ECF4]">委员会投票结论汇总</h3>
              <span class="ml-auto text-xs font-mono text-[#64748B]">{{ submittedCount }} 票</span>
            </div>
            <div v-if="submittedCount === 0" class="flex-1 flex items-center justify-center py-6 text-xs font-mono text-[#4A5568]">
              等待委员提交...
            </div>
            <div v-else class="p-3 space-y-2 flex-1">
              <div v-for="ca in CONSENSUS_ANALYSIS" :key="ca.asset"
                class="flex items-center justify-between bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-3 py-2">
                <span class="text-[13px] font-medium text-[#B4BAC9] shrink-0 w-16 truncate">{{ ca.asset }}</span>
                <div class="flex items-baseline gap-2 flex-1 justify-end">
                  <span class="text-sm font-bold font-mono tabular-nums text-[#3B9EFF]">{{ ca.avg.toFixed(1) }}</span>
                  <span :class="cn('text-xs font-mono font-bold px-1.5 py-0.5 rounded border whitespace-nowrap',
                    ca.label === '乐观' ? 'bg-[#F04864]/10 text-[#F04864] border-[#F04864]/25' :
                    ca.label === '中性偏乐观' ? 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25' :
                    ca.label === '中性' ? 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25' :
                    'bg-[#00C9A7]/10 text-[#00C9A7] border-[#00C9A7]/25')">{{ ca.label }}</span>
                </div>
              </div>
            </div>
            <div class="px-4 py-2 border-t border-[#252A3A] bg-[#161922] text-xs font-mono text-[#64748B]">
              详情见委员观点 > 委员会观点统计
            </div>
          </div>

          <!-- ② 三模型智能对比矩阵（配置指引紧凑版） -->
          <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden flex flex-col select-none">
            <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-4 py-3 flex items-center gap-2">
              <div class="am-title-bar shrink-0"></div>
              <h3 class="text-[13px] font-bold text-[#E8ECF4]">三模型配置对比</h3>
              <span class="ml-auto text-[11px] font-mono text-[#64748B]">细分至子资产</span>
            </div>

            <!-- 紧凑表头 -->
            <div class="flex border-b border-slate-700/50 bg-[#0E1118]">
              <div class="w-[36%] shrink-0 flex items-center px-3 py-1.5 border-r border-slate-800/50">
                <span class="text-[10px] font-mono text-slate-600 uppercase tracking-widest">资产</span>
              </div>
              <div class="flex-1 flex items-center justify-center py-1.5 border-r border-slate-800/40">
                <span class="text-[10px] font-mono font-bold text-indigo-500 uppercase">MC</span>
              </div>
              <div class="flex-1 flex items-center justify-center py-1.5 border-r border-slate-800/40">
                <span class="text-[10px] font-mono font-bold text-blue-400 uppercase">BL</span>
              </div>
              <div class="flex-1 flex items-center justify-center py-1.5">
                <span class="text-[10px] font-mono font-bold text-sky-500 uppercase">RP</span>
              </div>
            </div>

            <!-- 数据行 -->
            <div class="flex-1 divide-y divide-slate-800/40 overflow-auto">
              <template v-for="row in MODEL_TREE_DATA" :key="row.category">
                <!-- 大类行 -->
                <div
                  class="flex items-stretch cursor-pointer bg-slate-800/35 hover:bg-slate-700/30 transition-colors"
                  @click="toggleModelTreeRow(row.category)"
                >
                  <div class="w-[36%] shrink-0 flex items-center gap-1.5 px-3 h-8 border-r border-slate-800/50">
                    <span class="text-slate-500 font-mono text-[10px] w-2.5 shrink-0">{{ expandedModelTree.has(row.category) ? '▾' : '▸' }}</span>
                    <span class="text-xs font-bold text-white">{{ row.category }}</span>
                  </div>
                  <div class="flex-1 relative flex items-center justify-center h-8 overflow-hidden border-r border-slate-800/40">
                    <div class="absolute inset-y-1 left-1 rounded bg-indigo-500/20" :style="{ width: `calc(${Math.min(row.mc * 1.8, 92)}% - 4px)` }"></div>
                    <span class="relative z-10 font-mono font-bold text-xs text-white tabular-nums">{{ row.mc }}<span class="text-[9px] text-slate-500">%</span></span>
                  </div>
                  <div class="flex-1 relative flex items-center justify-center h-8 overflow-hidden border-r border-slate-800/40">
                    <div class="absolute inset-y-1 left-1 rounded bg-blue-500/20" :style="{ width: `calc(${Math.min(row.bl * 1.8, 92)}% - 4px)` }"></div>
                    <span class="relative z-10 font-mono font-bold text-xs text-white tabular-nums">{{ row.bl }}<span class="text-[9px] text-slate-500">%</span></span>
                  </div>
                  <div class="flex-1 relative flex items-center justify-center h-8 overflow-hidden">
                    <div class="absolute inset-y-1 left-1 rounded bg-sky-500/20" :style="{ width: `calc(${Math.min(row.rp * 1.8, 92)}% - 4px)` }"></div>
                    <span class="relative z-10 font-mono font-bold text-xs text-white tabular-nums">{{ row.rp }}<span class="text-[9px] text-slate-500">%</span></span>
                  </div>
                </div>
                <!-- 子资产行 -->
                <template v-if="expandedModelTree.has(row.category)">
                  <div
                    v-for="child in row.children" :key="child.sub"
                    class="flex items-stretch bg-[#0E1118] hover:bg-slate-700/20 transition-colors"
                  >
                    <div class="w-[36%] shrink-0 flex items-center pl-6 pr-3 h-8 border-r border-slate-800/50 gap-1.5">
                      <span class="text-slate-600 select-none leading-none">·</span>
                      <span class="text-[11px] text-slate-400">{{ child.sub }}</span>
                    </div>
                    <div class="flex-1 relative flex items-center justify-center h-8 overflow-hidden border-r border-slate-800/40">
                      <div class="absolute inset-y-1.5 left-1 rounded bg-indigo-500/12" :style="{ width: `calc(${Math.min(child.mc * 1.8, 92)}% - 4px)` }"></div>
                      <span class="relative z-10 font-mono text-xs text-slate-200 tabular-nums">{{ child.mc }}<span class="text-[9px] text-slate-500">%</span></span>
                    </div>
                    <div class="flex-1 relative flex items-center justify-center h-8 overflow-hidden border-r border-slate-800/40">
                      <div class="absolute inset-y-1.5 left-1 rounded bg-blue-500/12" :style="{ width: `calc(${Math.min(child.bl * 1.8, 92)}% - 4px)` }"></div>
                      <span class="relative z-10 font-mono text-xs text-slate-200 tabular-nums">{{ child.bl }}<span class="text-[9px] text-slate-500">%</span></span>
                    </div>
                    <div class="flex-1 relative flex items-center justify-center h-8 overflow-hidden">
                      <div class="absolute inset-y-1.5 left-1 rounded bg-sky-500/12" :style="{ width: `calc(${Math.min(child.rp * 1.8, 92)}% - 4px)` }"></div>
                      <span class="relative z-10 font-mono text-xs text-slate-200 tabular-nums">{{ child.rp }}<span class="text-[9px] text-slate-500">%</span></span>
                    </div>
                  </div>
                </template>
              </template>
            </div>

            <div class="px-4 py-2 border-t border-[#252A3A] bg-[#161922]">
              <button @click="showSAASandbox = true" class="w-full text-xs font-mono text-[#3B9EFF] bg-[#3B9EFF]/8 border border-[#3B9EFF]/20 hover:bg-[#3B9EFF]/14 rounded px-2 py-1 transition-colors">
                进入 BL 沙盘演算
              </button>
            </div>
          </div>

          <!-- ③ 上期历史指引 -->
          <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden flex flex-col">
            <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-4 py-3 flex items-center gap-2">
              <div class="am-title-bar shrink-0"></div>
              <h3 class="text-[13px] font-bold text-[#E8ECF4]">上期历史指引</h3>
              <span class="ml-auto text-xs font-mono px-1.5 py-0.5 rounded border border-[#3B9EFF]/25 text-[#3B9EFF]">胜率 {{ PREV_REVIEW_SUMMARY.winRate }}%</span>
            </div>
            <div class="overflow-auto flex-1">
              <table class="w-full border-collapse font-mono text-xs">
                <thead class="bg-[#1A1E2B] sticky top-0">
                  <tr class="border-b border-[#2E3348]">
                    <th class="px-3 py-2 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">资产</th>
                    <th class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">上期观点</th>
                    <th class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">涨跌幅</th>
                    <th class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8]">验证</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#252A3A]">
                  <tr v-for="row in PREV_REVIEW_ROWS" :key="row.asset"
                    class="hover:bg-[#1A1E2B]/40 transition-colors"
                    :class="row.verdict === 'wrong' ? 'bg-[#FF3B30]/3' : row.verdict === 'correct' ? 'bg-[#34C759]/2' : ''">
                    <td class="px-3 py-2 font-semibold text-[12px] text-[#E8ECF4] border-r border-[#2E3348] whitespace-nowrap">{{ row.asset }}</td>
                    <td class="px-2 py-2 text-center border-r border-[#2E3348]">
                      <span class="text-[11px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap"
                        :class="VOTE_CONSENSUS_STYLE[row.prevView]">{{ row.prevView }}</span>
                    </td>
                    <td class="px-2 py-2 text-center tabular-nums text-[12px] font-bold border-r border-[#2E3348]"
                      :class="row.changeVal > 0 ? 'text-[#F04864]' : row.changeVal < 0 ? 'text-[#34C759]' : 'text-[#94A3B8]'">
                      {{ row.changeStr }}
                    </td>
                    <td class="px-2 py-2 text-center">
                      <span class="text-xs font-bold" :class="{
                        'text-[#34C759]': row.verdict === 'correct',
                        'text-[#FF3B30]': row.verdict === 'wrong',
                        'text-[#3B9EFF]': row.verdict === 'neutral_ok' || row.verdict === 'neutral_fail',
                      }">{{ row.verdictLabel }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="px-4 py-2 border-t border-[#252A3A] bg-[#161922] text-xs font-mono text-[#64748B]">
              复盘区间: 2025.12.20 — 2026.03.28
            </div>
          </div>

        </div><!-- end 三栏参考 -->

        <!-- ─── 以下投票矩阵与共识内容已迁移至"委员观点 > 委员会观点统计"，此处隐藏 ─── -->
        <template v-if="false">
        <!-- ══ 混合投委会观点投票分布矩阵 ══ -->
        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>混合投委会观点投票分布矩阵</h3>
            <div class="flex items-center gap-3">
              <span class="text-[12px] font-mono text-[#94A3B8]">{{ MEMBERS_DATA.length }} 名委员 · {{ MIXED_ASSET_LIST.length }} 项资产</span>
              <button @click="showHistoryModal = true" class="text-[12px] text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/18 hover:border-[#3B9EFF]/40 px-2.5 py-1 rounded flex items-center gap-1.5 transition-colors">
                <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div> 查询历史期会审结果
              </button>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full border-collapse table-fixed font-mono text-[12px]" style="min-width:860px">
              <colgroup>
                <col style="width:52px" />
                <col style="width:84px" />
                <col style="width:150px" />
                <col style="width:78px" />
                <col style="width:44px" />
                <col style="width:62px" />
                <col style="width:44px" />
                <col style="width:62px" />
                <col style="width:44px" />
                <col style="width:108px" />
                <col style="width:130px" />
              </colgroup>
              <thead class="bg-[#1A1E2B]">
                <tr class="border-b border-[#2E3348]">
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">大类</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">细分策略</th>
                  <th rowspan="2" class="px-3 py-2 text-left text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">标的/基准指数</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle whitespace-nowrap">当前点位</th>
                  <th colspan="5" class="px-2 py-1.5 text-center text-xs font-bold text-[#3B9EFF] border-r border-[#2E3348]">票数分布（各档投票人数）</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle whitespace-nowrap">委员会观点</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-xs font-bold text-[#94A3B8] align-middle whitespace-nowrap">对应点位区间</th>
                </tr>
                <tr class="border-b-2 border-[#3B9EFF]/25">
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#00C9A7] border-r border-[#2E3348]/40">谨慎<br/><span class="text-[11px] opacity-50">1分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40 leading-tight">中性<br/>偏谨慎<br/><span class="text-[11px] opacity-50">2分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40">中性<br/><span class="text-[11px] opacity-50">3分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40 leading-tight">中性<br/>偏乐观<br/><span class="text-[11px] opacity-50">4分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#F04864] border-r border-[#2E3348]">乐观<br/><span class="text-[11px] opacity-50">5分</span></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="row in MIXED_DIST_ROWS" :key="row.细分策略" class="hover:bg-[#1A1E2B]/40 transition-colors">
                  <!-- 大类：仅每组首行渲染，rowspan 合并 -->
                  <td v-if="row.isFirstInGroup" :rowspan="row.groupSpan"
                    class="px-1 py-2 text-center text-xs font-bold tracking-widest border-r border-[#2E3348] align-middle"
                    :class="row.大类 === '固收' ? 'text-[#3B9EFF] bg-[#3B9EFF]/4' : row.大类 === '含权' ? 'text-[#3B9EFF] bg-[#3B9EFF]/4' : 'text-[#3B9EFF] bg-[#3B9EFF]/4'">
                    <span style="writing-mode:vertical-rl;letter-spacing:0.2em">{{ row.大类 }}</span>
                  </td>
                  <td class="px-2 py-2.5 font-semibold text-[12px] text-[#E8ECF4] border-r border-[#2E3348] whitespace-nowrap">{{ row.细分策略 }}</td>
                  <td class="px-3 py-2.5 text-xs text-[#64748B] truncate border-r border-[#2E3348]">{{ row.标的指数 }}</td>
                  <td class="px-2 py-2.5 text-center tabular-nums text-xs font-bold text-[#3B9EFF]/80 border-r border-[#2E3348]">{{ row.当前点位 }}</td>
                  <!-- 5 档票数 -->
                  <td v-for="(count, i) in row.dist" :key="i"
                    class="px-1 py-2.5 text-center transition-colors"
                    :class="[
                      i < 4 ? 'border-r border-[#2E3348]/40' : 'border-r border-[#2E3348]',
                      count > 0 && count === row.maxCount ? VOTE_DIST_HL_BG[i] : '',
                    ]">
                    <span v-if="count > 0"
                      class="text-[13px] font-bold tabular-nums leading-none"
                      :class="count === row.maxCount ? VOTE_DIST_HL_TEXT[i] : 'text-[#B4BAC9]'">{{ count }}</span>
                    <span v-else class="text-[#303848] text-xs select-none">—</span>
                  </td>
                  <!-- 委员会观点 -->
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span v-if="row.totalVotes > 0"
                      class="inline-block text-xs font-bold px-1.5 py-0.5 rounded border whitespace-nowrap"
                      :class="VOTE_CONSENSUS_STYLE[row.consensusLevel]">{{ row.consensusLevel }}</span>
                    <span v-else class="text-[#3A4555]">—</span>
                  </td>
                  <!-- 对应点位区间 -->
                  <td class="px-2 py-2.5 text-center tabular-nums text-xs font-mono"
                    :class="row.totalVotes > 0 ? 'text-[#3B9EFF]' : 'text-[#3A4555]'">{{ row.rangeStr }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- ══ 投票分布可视化摘要（堆叠条） ══ -->
          <div v-if="MIXED_DIST_ROWS.some(r => r.totalVotes > 0)" class="border-t border-[#252A3A] px-5 py-3 space-y-2">
            <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">投票分布可视化</div>
            <div v-for="row in MIXED_DIST_ROWS" :key="row.细分策略" v-show="row.totalVotes > 0" class="flex items-center gap-3">
              <span class="text-xs text-[#B4BAC9] w-20 shrink-0 truncate font-mono">{{ row.细分策略 }}</span>
              <div class="flex-1 h-4 rounded-full overflow-hidden flex bg-[#1A1E2B]">
                <template v-for="(count, i) in row.dist" :key="i">
                  <div v-if="count > 0"
                    :style="{ width: `${count / row.totalVotes * 100}%`, backgroundColor: ['#00C9A7', '#3B9EFF', '#3B9EFF', '#3B9EFF', '#F04864'][i] }"
                    class="h-full transition-all duration-500 min-w-[4px]"
                  ></div>
                </template>
              </div>
              <span v-if="row.totalVotes > 0"
                class="text-xs font-bold px-1.5 py-0.5 rounded border whitespace-nowrap shrink-0"
                :class="VOTE_CONSENSUS_STYLE[row.consensusLevel]">{{ row.consensusLevel }}</span>
            </div>
          </div>
          <div class="px-5 py-2 border-t border-[#2E3348] bg-[#161922] flex items-center justify-between text-xs text-[#64748B] font-mono">
            <span>众数格底色高亮 · 委员会观点 = 加权均值四舍五入对应档位 · 对应点位由观点幅度规则推算</span>
            <span class="flex items-center gap-4">
              <span class="text-[#00C9A7]">▪ 谨慎(1)</span>
              <span class="text-[#3B9EFF]">▪ 中性偏谨慎(2)</span>
              <span class="text-[#3B9EFF]">▪ 中性(3)</span>
              <span class="text-[#3B9EFF]">▪ 中性偏乐观(4)</span>
              <span class="text-[#F04864]">▪ 乐观(5)</span>
            </span>
          </div>
        </div>

        <!-- ══ 决策审计时间线 ══ -->
        <div class="border border-[#2E3348]/50 rounded-xl overflow-hidden">
          <button @click="showDecisionTimeline = !showDecisionTimeline" class="w-full px-5 py-3.5 flex items-center justify-between hover:bg-[#252A3A]/50 transition-all">
            <div class="flex items-center space-x-3">
              <div class="w-1.5 h-4 bg-[#94A3B8] rounded-sm shrink-0"></div>
              <span class="text-[13px] font-medium text-[#94A3B8]">决策审计时间线</span>
              <span class="text-xs font-mono text-[#64748B]">{{ DECISION_TIMELINE.length }} 事件</span>
            </div>
            <div class="w-0.5 h-3.5 bg-[#64748B] rounded-full transition-transform duration-200 origin-center" :class="showDecisionTimeline ? 'rotate-90' : ''"></div>
          </button>
          <div v-if="showDecisionTimeline" class="border-t border-[#252A3A] p-5">
            <div class="space-y-4">
              <div v-for="(evt, i) in DECISION_TIMELINE" :key="i" class="flex items-start gap-3">
                <div class="flex flex-col items-center shrink-0">
                  <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: evt.color }"></div>
                  <div v-if="i < DECISION_TIMELINE.length - 1" class="w-px flex-1 min-h-[24px] bg-[#252A3A]"></div>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-bold" :style="{ color: evt.color }">{{ evt.time }}</span>
                    <span class="text-[13px] font-medium text-[#E8ECF4]">{{ evt.event }}</span>
                  </div>
                  <div class="text-xs text-[#94A3B8] mt-0.5">{{ evt.detail }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ 跨委员会共识参考（折叠） ══ -->
        <div class="border border-dashed border-[#2E3348]/50 rounded-xl overflow-hidden">
          <button
            @click="showCrossPanel = !showCrossPanel"
            class="w-full px-5 py-3 bg-[#11131A]/80 flex items-center justify-between hover:bg-[#11131A] transition-all duration-200"
          >
            <div class="flex items-center gap-2.5">
              <span class="text-[12px] font-mono text-[#3B9EFF]/60">⚡</span>
              <span class="text-[13px] font-medium text-[#6B7280]">展开全局跨委员会共识参考</span>
              <span class="text-xs font-mono px-1.5 py-0.5 rounded border border-dashed border-[#3B9EFF]/25 text-[#3B9EFF]/60">只读 · Mock</span>
            </div>
            <div class="w-0.5 h-3.5 bg-[#4A5568] rounded-full transition-transform duration-200 origin-center" :class="showCrossPanel ? 'rotate-90' : ''"></div>
          </button>

          <div v-if="showCrossPanel" class="border-t border-dashed border-[#2E3348]/50 bg-[#11131A]/90 p-4 space-y-4">

            <!-- Table A：FICC 投委会投票统计 -->
            <div>
              <div class="flex items-center gap-2 mb-2">
                <div class="w-1 h-3.5 rounded-full bg-[#3B9EFF]/40"></div>
                <span class="text-xs font-mono font-bold text-[#3B9EFF]/80 uppercase tracking-wider">A · FICC 投委会投票统计（本期 Mock）</span>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full border-collapse table-fixed font-mono text-xs">
                  <thead>
                    <tr class="border-b border-dashed border-[#2E3348]/50 text-[#4A5568]">
                      <th class="px-3 py-1.5 text-left font-medium" style="width:100px">资产</th>
                      <th class="px-3 py-1.5 text-left font-medium">标的指数</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:60px">均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:90px">档位</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:130px">共识区间</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:70px">归属</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dashed divide-[#2E3348]/30">
                    <tr v-for="cfg in FICC_ASSET_LIST" :key="cfg.id"
                      :class="SHARED_NAMES.has(cfg.细分策略) ? 'bg-[#3B9EFF]/4' : ''"
                      class="hover:bg-white/2 transition-colors">
                      <td class="px-3 py-2 font-semibold text-[#B4BAC9]">{{ cfg.细分策略 }}</td>
                      <td class="px-3 py-2 text-[#4A5568] truncate">{{ cfg.标的指数 }}</td>
                      <td class="px-2 py-2 text-center tabular-nums text-[#3B9EFF]">{{ CROSS_FICC_MOCK[cfg.细分策略]?.toFixed(1) ?? '—' }}</td>
                      <td class="px-2 py-2 text-center">
                        <span v-if="CROSS_FICC_MOCK[cfg.细分策略]" :class="[
                          'text-xs font-mono px-1 py-0.5 rounded border',
                          Math.round(CROSS_FICC_MOCK[cfg.细分策略]) === 5 ? 'border-[#F04864]/30 text-[#F04864]' :
                          Math.round(CROSS_FICC_MOCK[cfg.细分策略]) === 4 ? 'border-[#3B9EFF]/30 text-[#3B9EFF]' :
                          Math.round(CROSS_FICC_MOCK[cfg.细分策略]) === 2 ? 'border-[#3B9EFF]/30 text-[#3B9EFF]' :
                          Math.round(CROSS_FICC_MOCK[cfg.细分策略]) === 1 ? 'border-[#00C9A7]/30 text-[#00C9A7]' :
                          'border-[#3B9EFF]/30 text-[#3B9EFF]'
                        ]">{{ SCORE_LABELS[Math.round(CROSS_FICC_MOCK[cfg.细分策略])] }}</span>
                      </td>
                      <td class="px-2 py-2 text-center tabular-nums text-[#3B9EFF]/80">
                        {{ CROSS_FICC_MOCK[cfg.细分策略] ? calcRangeStr(cfg, CROSS_FICC_MOCK[cfg.细分策略]) : '—' }}
                      </td>
                      <td class="px-2 py-2 text-center">
                        <span v-if="SHARED_NAMES.has(cfg.细分策略)" class="text-[11px] font-mono px-1 py-0.5 rounded border border-dashed border-[#3B9EFF]/30 text-[#3B9EFF]/70">⚡ 共享</span>
                        <span v-else class="text-[11px] font-mono text-[#4A5568]">FICC专有</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 分割线 -->
            <div class="border-t border-dashed border-[#2E3348]/40"></div>

            <!-- Table B：公司级全局合并统计 -->
            <div>
              <div class="flex items-center gap-2 mb-2">
                <div class="w-1 h-3.5 rounded-full bg-[#3B9EFF]/40"></div>
                <span class="text-xs font-mono font-bold text-[#3B9EFF]/80 uppercase tracking-wider">B · 公司级全局大类配置共识（两委均值算术平均）</span>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full border-collapse table-fixed font-mono text-xs">
                  <thead>
                    <tr class="border-b border-dashed border-[#2E3348]/50 text-[#4A5568]">
                      <th class="px-3 py-1.5 text-left font-medium" style="width:100px">资产</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:70px">大类</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:55px">混合均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:55px">FICC均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:60px">全局均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:90px">全局档位</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:130px">全局共识区间</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:70px">来源</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dashed divide-[#2E3348]/30">
                    <tr v-for="row in CROSS_GLOBAL_ITEMS" :key="row.name"
                      :class="row.source === '⚡共享' ? 'bg-[#3B9EFF]/4' : row.source === 'FICC' ? 'bg-[#3B9EFF]/3' : ''"
                      class="hover:bg-white/2 transition-colors">
                      <td class="px-3 py-2 font-semibold text-[#B4BAC9]">{{ row.name }}</td>
                      <td class="px-2 py-2 text-center text-[#64748B]">{{ row.大类 }}</td>
                      <td class="px-2 py-2 text-center tabular-nums" :class="row.ownAvg !== null ? 'text-[#3B9EFF]' : 'text-[#3A4555]'">
                        {{ row.ownAvg !== null ? row.ownAvg.toFixed(1) : '—' }}
                      </td>
                      <td class="px-2 py-2 text-center tabular-nums" :class="row.crossAvg !== null ? 'text-[#3B9EFF]' : 'text-[#3A4555]'">
                        {{ row.crossAvg !== null ? row.crossAvg.toFixed(1) : '—' }}
                      </td>
                      <td class="px-2 py-2 text-center tabular-nums font-bold text-[#3B9EFF]">{{ row.globalAvg.toFixed(1) }}</td>
                      <td class="px-2 py-2 text-center">
                        <span :class="[
                          'text-xs px-1 py-0.5 rounded border',
                          row.globalLabel === '乐观' ? 'border-[#F04864]/30 text-[#F04864]' :
                          row.globalLabel === '中性偏乐观' ? 'border-[#3B9EFF]/30 text-[#3B9EFF]' :
                          row.globalLabel === '中性偏谨慎' ? 'border-[#3B9EFF]/30 text-[#3B9EFF]' :
                          row.globalLabel === '谨慎' ? 'border-[#00C9A7]/30 text-[#00C9A7]' :
                          'border-[#3B9EFF]/30 text-[#3B9EFF]'
                        ]">{{ row.globalLabel }}</span>
                      </td>
                      <td class="px-2 py-2 text-center tabular-nums text-[#3B9EFF]/80">{{ row.globalRange }}</td>
                      <td class="px-2 py-2 text-center">
                        <span :class="[
                          'text-[11px] font-mono px-1 py-0.5 rounded border border-dashed',
                          row.source === '⚡共享' ? 'border-[#3B9EFF]/30 text-[#3B9EFF]/70' :
                          row.source === 'FICC' ? 'border-[#3B9EFF]/25 text-[#3B9EFF]/60' :
                          'border-[#3B9EFF]/25 text-[#3B9EFF]/60'
                        ]">{{ row.source }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="mt-2 text-xs font-mono text-[#3A4555] px-1">
                ⚡ 共享资产全局均值 = (混合均值 + FICC均值) / 2 · 专有资产取所属委员会均值 · FICC数据为本期Mock
              </div>
            </div>

          </div>
        </div>

        <!-- ══ Consensus Summary ══ -->
        <div id="nav-consensus-2" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>会议共识与边际变化</h3>
            <span class="text-[13px] font-mono text-[#94A3B8]">综合 {{ submittedCount }} 份问卷</span>
          </div>
          <div class="p-5 grid grid-cols-3 gap-3">
            <div v-for="ca in CONSENSUS_ANALYSIS" :key="ca.asset" class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg p-3.5">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[14px] font-bold text-[#E8ECF4]">{{ ca.asset }}</span>
                <span :class="cn('text-[13px] font-mono font-bold px-2 py-1 rounded border',
                  ca.label === '乐观' ? 'bg-[#F04864]/10 text-[#F04864] border-[#F04864]/25' :
                  ca.label === '中性偏乐观' ? 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25' :
                  ca.label === '中性' ? 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25' :
                  'bg-[#00C9A7]/10 text-[#00C9A7] border-[#00C9A7]/25')">{{ ca.label }}</span>
              </div>
              <div class="flex items-baseline gap-2 mb-1.5">
                <span class="text-lg font-bold font-mono tabular-nums text-[#3B9EFF]">{{ ca.avg.toFixed(1) }}</span>
                <span class="text-[13px] font-mono" :class="ca.delta > 0 ? 'text-[#F04864]' : ca.delta < 0 ? 'text-[#00C9A7]' : 'text-[#94A3B8]'">
                  {{ ca.delta > 0 ? '+' : '' }}{{ ca.delta.toFixed(1) }} vs 上期
                  <span v-if="ca.delta > 0">&#9650;</span>
                  <span v-else-if="ca.delta < 0">&#9660;</span>
                </span>
              </div>
              <div class="flex items-center justify-between text-[13px] text-[#94A3B8]">
                <span>{{ ca.newHighCount }} 人看创新高</span>
                <span :class="cn('font-mono', ca.consensus === '高度一致' ? 'text-[#3B9EFF]' : ca.consensus === '方向趋同' ? 'text-[#3B9EFF]' : 'text-[#3B9EFF]')">{{ ca.consensus }}</span>
              </div>
            </div>
          </div>
        </div>
        </template><!-- end hidden old voting matrix (moved to member_views committee_stats) -->
      </div>

      <!-- ═══ 决议与配置指引 (allocation Tab) ═══ -->
      <div v-if="activeTab === 'allocation'" class="space-y-4 pb-4">

        <!-- ══ Card 1: 主任委员决策矩阵 ══ -->
        <div id="nav-chair-decision" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <h3 class="am-title-l2"><div class="am-title-bar"></div>配置决策矩阵 · 主任委员定调</h3>
              <span v-if="!isReadOnly" class="text-xs font-mono px-2 py-1 rounded bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 text-[#3B9EFF]">主任委员定调模式</span>
              <span v-else class="text-xs font-mono px-2 py-1 rounded bg-[#94A3B8]/10 border border-[#2E3348] text-[#64748B]">只读预览</span>
            </div>
            <span class="text-xs font-mono text-[#6B7280]">问卷均值 — 债券 {{ MATRIX_COL_AVG['债券']?.toFixed(1) ?? '-' }} · 权益 {{ MATRIX_COL_AVG['权益-红利']?.toFixed(1) ?? '-' }}</span>
          </div>
          <div class="p-5 space-y-5">

            <!-- ① 固收类久期（产品差异化） -->
            <div class="space-y-3">
              <div class="flex items-start gap-4" v-for="(pid, idx) in (['low','mid','hybrid'] as const)" :key="pid">
                <div class="w-28 shrink-0 pt-1">
                  <div class="text-[13px] font-semibold text-[#E8ECF4]">{{ ['低波产品久期','中波产品久期','混合产品久期'][idx] }}</div>
                  <div class="text-[13px] text-[#94A3B8] font-mono mt-0.5">{{ PRODUCT_BOND_LABELS[pid] }}</div>
                </div>
                <div class="flex gap-2 flex-wrap">
                  <template v-if="!isReadOnly">
                    <button v-for="g in (['高','中','低'] as const)" :key="g"
                      @click="chairDecision.perProductBondGrade[pid] = g"
                      :class="cn('px-4 py-2 rounded-lg border text-[13px] font-bold font-mono transition-all duration-150',
                        chairDecision.perProductBondGrade[pid] === g
                          ? g === '高' ? 'bg-[#F04864]/15 border-[#F04864]/50 text-[#F04864]'
                            : g === '低' ? 'bg-[#00C9A7]/15 border-[#00C9A7]/50 text-[#00C9A7]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/50 text-[#3B9EFF]'
                          : 'bg-[#1A1E2B] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8] hover:border-[#3B9EFF]/30')"
                    >
                      {{ g }}
                      <span class="ml-1.5 text-xs opacity-60 font-normal">{{ BOND_GRADE_DURATION[g] }}</span>
                    </button>
                  </template>
                  <template v-else>
                    <span :class="cn('px-4 py-2 rounded-lg border text-[13px] font-bold font-mono',
                      chairDecision.perProductBondGrade[pid] === '高' ? 'bg-[#F04864]/10 border-[#F04864]/30 text-[#F04864]'
                      : chairDecision.perProductBondGrade[pid] === '低' ? 'bg-[#00C9A7]/10 border-[#00C9A7]/30 text-[#00C9A7]'
                      : 'bg-[#3B9EFF]/10 border-[#3B9EFF]/30 text-[#3B9EFF]')">
                      {{ chairDecision.perProductBondGrade[pid] }}
                      <span class="ml-1.5 text-xs opacity-60 font-normal">{{ BOND_GRADE_DURATION[chairDecision.perProductBondGrade[pid]] }}</span>
                    </span>
                  </template>
                </div>
              </div>
            </div>

            <div class="h-px bg-[#252A3A]"></div>

            <!-- ② 权益总额评级 -->
            <div class="flex items-start gap-4">
              <div class="w-28 shrink-0 pt-1">
                <div class="text-[13px] font-semibold text-[#E8ECF4]">权益总额评级</div>
                <div class="text-[13px] text-[#94A3B8] font-mono mt-0.5">Equity Stance</div>
              </div>
              <div class="flex gap-2 flex-wrap">
                <template v-if="!isReadOnly">
                  <button v-for="n in [1,2,3,4,5]" :key="n"
                    @click="chairDecision.equityGrade = n"
                    :class="cn('px-3 py-2 rounded-lg border text-xs font-bold font-mono transition-all duration-150 min-w-[72px]',
                      chairDecision.equityGrade === n
                        ? GRADE_COLORS[n]
                        : 'bg-[#1A1E2B] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8] hover:border-[#3B9EFF]/30')"
                  >
                    <div>{{ n }}</div>
                    <div class="text-xs font-normal opacity-70 mt-0.5">{{ SCORE_LABELS[n] }}</div>
                  </button>
                </template>
                <template v-else>
                  <span :class="cn('px-3 py-2 rounded-lg border text-xs font-bold font-mono inline-flex flex-col items-center min-w-[72px]',
                    GRADE_COLORS[chairDecision.equityGrade] || 'bg-[#94A3B8]/10 text-[#94A3B8] border-[#94A3B8]/25')">
                    <span>{{ chairDecision.equityGrade }}</span>
                    <span class="text-xs font-normal opacity-70 mt-0.5">{{ SCORE_LABELS[chairDecision.equityGrade] }}</span>
                  </span>
                </template>
              </div>
            </div>

            <div class="h-px bg-[#252A3A]"></div>

            <!-- ③ 权益明细分配 -->
            <div class="flex items-start gap-4">
              <div class="w-28 shrink-0 pt-1">
                <div class="text-[13px] font-semibold text-[#E8ECF4]">权益明细</div>
                <div class="text-[13px] text-[#94A3B8] font-mono mt-0.5">Equity Mix (%)</div>
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-4 flex-wrap">
                  <template v-if="!isReadOnly">
                    <div v-for="k in (['红利','成长','价值'] as const)" :key="k" class="flex items-center gap-2">
                      <span class="text-xs text-[#94A3B8] font-mono w-8">{{ k }}</span>
                      <input type="number" min="0" max="100" step="5"
                        v-model.number="chairDecision.equityMix[k]"
                        class="w-16 bg-[#1A1E2B] border rounded text-[13px] font-mono text-center text-[#E8ECF4] px-2 py-1.5 focus:outline-none transition-colors"
                        :class="equityMixSum === 100 ? 'border-[#2E3348] focus:border-[#3B9EFF]' : 'border-[#F04864]/50 focus:border-[#F04864]'"
                      />
                      <span class="text-xs text-[#6B7280] font-mono">%</span>
                    </div>
                  </template>
                  <template v-else>
                    <div v-for="k in (['红利','成长','价值'] as const)" :key="k" class="flex items-center gap-2">
                      <span class="text-xs text-[#94A3B8] font-mono w-8">{{ k }}</span>
                      <span class="text-[13px] font-mono text-[#E8ECF4] w-10 text-right">{{ chairDecision.equityMix[k] }}</span>
                      <span class="text-xs text-[#6B7280] font-mono">%</span>
                    </div>
                  </template>
                  <span :class="cn('ml-auto text-xs font-bold font-mono px-3 py-1.5 rounded-lg border',
                    equityMixSum === 100
                      ? 'bg-[#00C9A7]/10 border-[#00C9A7]/30 text-[#00C9A7]'
                      : 'bg-[#F04864]/10 border-[#F04864]/40 text-[#F04864] animate-pulse')">
                    合计 {{ equityMixSum }}%
                    <span v-if="equityMixSum !== 100" class="ml-1 opacity-70">≠ 100%</span>
                  </span>
                </div>
              </div>
            </div>

            <div class="h-px bg-[#252A3A]"></div>

            <!-- ④ 另类资产定性 -->
            <div class="flex items-start gap-4">
              <div class="w-28 shrink-0 pt-1">
                <div class="text-[13px] font-semibold text-[#E8ECF4]">另类资产</div>
                <div class="text-[13px] text-[#94A3B8] font-mono mt-0.5">Alternatives (可选)</div>
              </div>
              <template v-if="!isReadOnly">
                <textarea v-model="chairDecision.altNotes" rows="2"
                  placeholder="黄金标配，关注地缘风险；原油谨慎，控制能源敞口…（可留空）"
                  class="flex-1 bg-[#1A1E2B] border border-[#2E3348] rounded-lg text-[13px] font-mono text-[#E8ECF4] placeholder-[#4A5568] px-3 py-2 resize-none focus:outline-none focus:border-[#3B9EFF]/50 transition-colors"
                ></textarea>
              </template>
              <template v-else>
                <p class="flex-1 text-[13px] font-mono text-[#B4BAC9] min-h-[2.5rem]">{{ chairDecision.altNotes || '—' }}</p>
              </template>
            </div>

          </div>
          <!-- 计算按钮 (主任委员专属) -->
          <div v-if="!isReadOnly" class="px-5 py-3.5 border-t border-[#252A3A] bg-[#161922] flex items-center justify-between">
            <span class="text-xs font-mono text-[#6B7280]">设置固收档位、权益评级和权益明细后，点击按钮自动填充三类产品指引仓位</span>
            <button @click="calcProductGuidances"
              :disabled="equityMixSum !== 100"
              :class="cn('px-5 py-2 rounded-lg border text-[13px] font-bold font-mono transition-all duration-200 flex items-center gap-2',
                equityMixSum === 100
                  ? 'bg-[#3B9EFF]/12 border-[#3B9EFF]/40 text-[#3B9EFF] hover:bg-[#3B9EFF]/20 hover:border-[#3B9EFF]/60'
                  : 'bg-[#1A1E2B] border-[#2E3348] text-[#4A5568] cursor-not-allowed')"
            >
              <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div>
              计算产品指引
            </button>
          </div>
        </div>

        <!-- ══ Card 2: 三类产品配置指引 (三层嵌套表头) ══ -->
        <div id="nav-product-guide" class="bg-[#202431] border rounded-xl overflow-hidden transition-all duration-300"
             :class="guidanceCalculated ? 'border-[#3B9EFF]/25' : 'border-[#252A3A]'">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <h3 class="am-title-l2"><div class="am-title-bar"></div>三类产品配置指引</h3>
              <span v-if="guidanceCalculated" class="text-xs font-mono px-2 py-1 rounded bg-[#3B9EFF]/10 border border-[#3B9EFF]/25 text-[#3B9EFF]">已计算</span>
              <span v-else class="text-xs font-mono px-2 py-1 rounded bg-[#94A3B8]/10 border border-[#2E3348] text-[#64748B]">待计算</span>
            </div>
            <span class="text-xs font-mono text-[#6B7280]">另类/流动性自动读取上期比例</span>
          </div>
          <div class="overflow-x-auto">
            <table class="table-fixed w-full border-collapse font-mono text-[13px]">
              <!-- ── 第一层表头 ── -->
              <thead class="bg-[#1A1E2B] border-b border-[#2E3348]">
                <tr>
                  <th rowspan="2" class="px-3 py-2.5 text-left text-xs text-[#94A3B8] font-semibold uppercase tracking-wider border-r border-[#2E3348]" style="width:90px">产品类型</th>
                  <th rowspan="2" class="px-2 py-1.5 text-center text-xs text-[#3B9EFF] font-semibold uppercase tracking-wider border-r border-[#2E3348]" style="width:130px">固收<br/><span class="text-xs font-normal text-[#3B9EFF]/50">久期指引</span></th>
                  <th colspan="5" class="px-2 py-1.5 text-center text-xs text-[#3B9EFF] font-semibold uppercase tracking-wider border-r border-[#2E3348]">权益</th>
                  <th rowspan="2" class="px-2 py-1.5 text-center text-xs text-[#3B9EFF] font-semibold uppercase tracking-wider border-r border-[#2E3348]" style="width:110px">另类</th>
                  <th rowspan="2" class="px-2 py-1.5 text-center text-xs text-[#94A3B8] font-semibold uppercase tracking-wider" style="width:55px">流动性</th>
                </tr>
                <tr class="border-b border-[#2E3348]">
                  <th class="px-1.5 py-1.5 text-center text-xs text-[#3B9EFF]/50 font-normal" style="width:80px">总仓位</th>
                  <th class="px-1.5 py-1.5 text-center text-xs text-[#3B9EFF]/50 font-normal">红利</th>
                  <th class="px-1.5 py-1.5 text-center text-xs text-[#3B9EFF]/50 font-normal">港股</th>
                  <th class="px-1.5 py-1.5 text-center text-xs text-[#3B9EFF]/50 font-normal">其他</th>
                  <th class="px-1.5 py-1.5 text-center text-xs text-[#3B9EFF]/50 font-normal border-r border-[#2E3348]">REITS</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <!-- ── 委员会决策行 ── -->
                <tr class="bg-[#252A3A]/40 hover:bg-[#252A3A]/60 transition-colors">
                  <td class="px-3 py-2.5 border-r border-[#2E3348]">
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                      <div>
                        <div class="text-[13px] font-bold text-[#3B9EFF]">委员会决策</div>
                        <div class="text-xs text-[#3B9EFF]/50">DECISION</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span class="text-xs font-bold text-[#3B9EFF]">差异化定调</span>
                    <div class="text-xs text-[#3B9EFF]/40 font-mono mt-0.5">见 Card 1</div>
                  </td>
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span class="text-[13px] font-bold text-[#3B9EFF]">{{ chairDecision.equityGrade }}档</span>
                    <div class="text-xs text-[#3B9EFF]/50 mt-0.5">{{ SCORE_LABELS[chairDecision.equityGrade] }}</div>
                  </td>
                  <td class="px-1.5 py-2.5 text-center text-xs text-[#94A3B8]">{{ chairDecision.equityMix['红利'] }}%</td>
                  <td class="px-1.5 py-2.5 text-center text-xs text-[#94A3B8]">—</td>
                  <td class="px-1.5 py-2.5 text-center text-xs text-[#94A3B8]">{{ chairDecision.equityMix['价值'] }}%</td>
                  <td class="px-1.5 py-2.5 text-center text-xs text-[#94A3B8] border-r border-[#2E3348]">—</td>
                  <td class="px-2 py-2.5 text-center text-xs text-[#3B9EFF]/70 border-r border-[#2E3348]">{{ chairDecision.altNotes || '—' }}</td>
                  <td class="px-1.5 py-2.5 text-center text-xs text-[#94A3B8]/50">—</td>
                </tr>
                <!-- ── 三类产品指引行 ── -->
                <tr v-for="row in productGuidances" :key="row.id" class="hover:bg-[#1A1E2B]/40 transition-colors">
                  <td class="px-3 py-2.5 border-r border-[#2E3348]">
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-5 rounded-full shrink-0" :style="{ background: row.color }"></div>
                      <div class="text-[13px] font-semibold text-[#E8ECF4]">{{ row.name }}</div>
                    </div>
                  </td>
                  <!-- 固收: 久期指引文字 -->
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span class="text-xs font-mono font-semibold text-[#3B9EFF]">
                      {{ BOND_GRADE_LABEL[chairDecision.perProductBondGrade[row.id] as BondGrade] }}
                    </span>
                    <template v-if="showHistoryDiff">
                      <span v-if="diffBondGrade(chairDecision.perProductBondGrade[row.id], PREV_SNAPSHOT.perProductBondGrade[row.id])"
                            class="block text-xs font-mono font-bold text-[#3B9EFF] mt-0.5">
                        {{ diffBondGrade(chairDecision.perProductBondGrade[row.id], PREV_SNAPSHOT.perProductBondGrade[row.id]) }}
                      </span>
                    </template>
                  </td>
                  <!-- 总权益仓位 -->
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span class="font-mono text-[13px]"
                          :class="guidanceCalculated ? 'text-[#3B9EFF] font-bold' : 'text-[#2E3348]'">
                      {{ guidanceCalculated ? row.equity + '%' : '—' }}
                    </span>
                    <template v-if="guidanceCalculated && showHistoryDiff">
                      <span v-if="diffBadge(row.equity, PREV_SNAPSHOT.products.find(p => p.id === row.id)!.equity)"
                            class="block text-xs font-mono font-bold mt-0.5"
                            :class="(row.equity - PREV_SNAPSHOT.products.find(p => p.id === row.id)!.equity) > 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                        {{ diffBadge(row.equity, PREV_SNAPSHOT.products.find(p => p.id === row.id)!.equity) }}
                      </span>
                    </template>
                  </td>
                  <!-- 权益细分: 红利/港股/其他/REITS -->
                  <td v-for="k in (['红利','港股','其他权益','REITS'] as const)" :key="k"
                      class="px-1.5 py-2.5 text-center text-[13px] text-[#94A3B8]">
                    {{ guidanceCalculated ? row.equitySub[k] + '%' : '—' }}
                    <template v-if="guidanceCalculated && showHistoryDiff">
                      <span v-if="diffBadge(row.equitySub[k], PREV_SNAPSHOT.products.find(p => p.id === row.id)!.equitySub[k])"
                            class="block text-xs font-mono font-bold"
                            :class="(row.equitySub[k] - PREV_SNAPSHOT.products.find(p => p.id === row.id)!.equitySub[k]) > 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                        {{ diffBadge(row.equitySub[k], PREV_SNAPSHOT.products.find(p => p.id === row.id)!.equitySub[k]) }}
                      </span>
                    </template>
                  </td>
                  <!-- 另类 -->
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <template v-if="!isReadOnly && guidanceCalculated">
                      <input type="number" min="0" max="100" v-model.number="row.alt"
                        class="w-14 bg-[#1A1E2B] border border-[#3B9EFF]/20 rounded text-[13px] font-mono text-center text-[#3B9EFF] px-1 py-1 focus:outline-none focus:border-[#3B9EFF]/50 transition-colors"/>
                    </template>
                    <template v-else>
                      <span class="font-mono text-[13px]"
                            :class="guidanceCalculated ? 'text-[#3B9EFF]' : 'text-[#2E3348]'">
                        {{ guidanceCalculated ? row.alt + '%' : '—' }}
                      </span>
                    </template>
                    <template v-if="guidanceCalculated && showHistoryDiff">
                      <span v-if="diffBadge(row.alt, PREV_SNAPSHOT.products.find(p => p.id === row.id)!.alt)"
                            class="block text-xs font-mono font-bold mt-0.5"
                            :class="(row.alt - PREV_SNAPSHOT.products.find(p => p.id === row.id)!.alt) > 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                        {{ diffBadge(row.alt, PREV_SNAPSHOT.products.find(p => p.id === row.id)!.alt) }}
                      </span>
                    </template>
                  </td>
                  <!-- 流动性 -->
                  <td class="px-1.5 py-2.5 text-center">
                    <span class="font-mono text-[13px]"
                          :class="guidanceCalculated ? 'text-[#94A3B8]' : 'text-[#2E3348]'">
                      {{ guidanceCalculated ? row.liquidity + '%' : '—' }}
                    </span>
                    <template v-if="guidanceCalculated && showHistoryDiff">
                      <span v-if="diffBadge(row.liquidity, PREV_SNAPSHOT.products.find(p => p.id === row.id)!.liquidity)"
                            class="block text-xs font-mono font-bold mt-0.5"
                            :class="(row.liquidity - PREV_SNAPSHOT.products.find(p => p.id === row.id)!.liquidity) > 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                        {{ diffBadge(row.liquidity, PREV_SNAPSHOT.products.find(p => p.id === row.id)!.liquidity) }}
                      </span>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="px-5 py-2 border-t border-[#252A3A] bg-[#161922] text-xs font-mono text-[#4A5568]">
            合计允许范围 95–105%（四舍五入容差）· 权益细分按产品系数自动计算 · 另类/流动性初值取自上期比例
          </div>
          <!-- ══ 折叠触发器：历史对比 ══ -->
          <button @click="showHistoryDiff = !showHistoryDiff" class="w-full px-5 py-2.5 border-t border-[#2E3348] bg-[#1A1E2B] text-[13px] font-mono text-[#94A3B8] hover:text-[#3B9EFF] hover:bg-[#1A1E2B]/80 transition-colors flex items-center justify-center gap-2">
            <div class="w-0.5 h-3 bg-current rounded-full transition-transform duration-200 origin-center" :class="showHistoryDiff ? 'rotate-90' : ''"></div>
            <span>{{ showHistoryDiff ? '收起' : '点击展开' }}与上期 (2025 Q4) 配置指引对比</span>
          </button>
          <!-- ══ 历史对比报表 ══ -->
          <div v-if="showHistoryDiff" class="border-t border-[#2E3348]">
            <div class="px-5 py-2 bg-[#161922] border-b border-[#2E3348]">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-4 rounded-full bg-[#64748B]"></div>
                <span class="text-[13px] font-bold text-[#64748B]">上期快照 · 2025 Q4</span>
                <span class="text-xs font-mono text-[#4A5568]">固收{{ PREV_SNAPSHOT.bondGrade }}（{{ PREV_SNAPSHOT.bondDuration }}）· 权益{{ PREV_SNAPSHOT.equityLabel }}</span>
              </div>
            </div>
            <div class="overflow-x-auto">
              <table class="table-fixed w-full border-collapse font-mono text-[13px] opacity-70">
                <thead class="bg-[#161922] border-b border-[#2E3348]">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs text-[#64748B] border-r border-[#2E3348]" style="width:90px">产品类型</th>
                    <th class="px-2 py-2 text-center text-xs text-[#3B9EFF]/40 border-r border-[#2E3348]" style="width:130px">久期指引</th>
                    <th class="px-2 py-2 text-center text-xs text-[#3B9EFF]/40 border-r border-[#2E3348]" style="width:80px">总权益</th>
                    <th class="px-1.5 py-2 text-center text-xs text-[#3B9EFF]/40">红利</th>
                    <th class="px-1.5 py-2 text-center text-xs text-[#3B9EFF]/40">港股</th>
                    <th class="px-1.5 py-2 text-center text-xs text-[#3B9EFF]/40">其他</th>
                    <th class="px-1.5 py-2 text-center text-xs text-[#3B9EFF]/40 border-r border-[#2E3348]">REITS</th>
                    <th class="px-2 py-2 text-center text-xs text-[#3B9EFF]/40 border-r border-[#2E3348]" style="width:110px">另类</th>
                    <th class="px-1.5 py-2 text-center text-xs text-[#94A3B8]/40" style="width:55px">流动性</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#252A3A]/50">
                  <tr v-for="p in PREV_SNAPSHOT.products" :key="p.id" class="hover:bg-[#161922]/60">
                    <td class="px-3 py-2 border-r border-[#2E3348]">
                      <span class="text-[13px] text-[#64748B]">{{ p.name }}</span>
                    </td>
                    <td class="px-2 py-2 text-center text-xs text-[#3B9EFF]/50 border-r border-[#2E3348]">
                      {{ BOND_GRADE_LABEL[PREV_SNAPSHOT.perProductBondGrade[p.id]] }}
                    </td>
                    <td class="px-2 py-2 text-center text-[#3B9EFF]/50 border-r border-[#2E3348]">{{ p.equity }}%</td>
                    <td class="px-1.5 py-2 text-center text-[#94A3B8]/40">{{ p.equitySub['红利'] }}%</td>
                    <td class="px-1.5 py-2 text-center text-[#94A3B8]/40">{{ p.equitySub['港股'] }}%</td>
                    <td class="px-1.5 py-2 text-center text-[#94A3B8]/40">{{ p.equitySub['其他权益'] }}%</td>
                    <td class="px-1.5 py-2 text-center text-[#94A3B8]/40 border-r border-[#2E3348]">{{ p.equitySub['REITS'] }}%</td>
                    <td class="px-2 py-2 text-center text-[#3B9EFF]/40 border-r border-[#2E3348]">{{ p.altText }}</td>
                    <td class="px-1.5 py-2 text-center text-[#94A3B8]/40">{{ p.liquidity }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ══ 校验 Toast ══ -->
        <Transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition-all duration-200" leave-to-class="opacity-0 -translate-y-2">
          <div v-if="showValidationToast && validationErrors.length > 0"
            class="bg-[#1A0A0E] border border-[#F04864]/40 rounded-xl px-5 py-4 space-y-2">
            <div class="flex items-center gap-2 mb-1">
              <div class="w-1.5 h-4 bg-[#F04864] rounded-sm shrink-0"></div>
              <span class="text-[13px] font-bold text-[#F04864] uppercase tracking-widest">校验失败 · 无法提交</span>
            </div>
            <div v-for="(err, i) in validationErrors" :key="i" class="flex items-start gap-2">
              <span class="text-[#F04864] font-mono text-xs mt-0.5 shrink-0">›</span>
              <span class="text-[13px] font-mono text-[#F04864]/80">{{ err }}</span>
            </div>
          </div>
        </Transition>

        <!-- ══ 提交区 ══ -->
        <div v-if="!decisionSubmitted" class="bg-[#202431] border border-[#252A3A] rounded-xl p-5 space-y-4">
          <div class="flex items-start gap-3">
            <div class="mt-0.5 shrink-0">
              <div v-if="validationErrors.length === 0 && guidanceCalculated" class="w-2 h-2 rounded-full bg-[#00C9A7] mt-1"></div>
              <div v-else class="w-2 h-2 rounded-full bg-[#F04864] mt-1"></div>
            </div>
            <div class="flex-1 space-y-1 text-xs font-mono text-[#64748B]">
              <div :class="equityMixSum === 100 ? 'text-[#00C9A7]' : 'text-[#F04864]'">
                {{ equityMixSum === 100 ? '✓' : '✗' }} 权益明细之和 {{ equityMixSum }}% {{ equityMixSum === 100 ? '（通过）' : '（须为 100%）' }}
              </div>
              <div :class="guidanceCalculated ? 'text-[#00C9A7]' : 'text-[#6B7280]'">
                {{ guidanceCalculated ? '✓' : '○' }} 产品指引已计算 {{ guidanceCalculated ? '（通过）' : '（待点击「计算产品指引」）' }}
              </div>
              <div v-for="row in productGuidances" :key="row.id"
                   :class="guidanceCalculated ? (Math.abs(row.bond + row.equity + row.alt + row.liquidity - 100) <= 5 ? 'text-[#00C9A7]' : 'text-[#F04864]') : 'text-[#6B7280]'">
                <template v-if="guidanceCalculated">
                  {{ Math.abs(row.bond + row.equity + row.alt + row.liquidity - 100) <= 5 ? '✓' : '✗' }}
                  【{{ row.name }}】合计 {{ row.bond + row.equity + row.alt + row.liquidity }}%
                  {{ Math.abs(row.bond + row.equity + row.alt + row.liquidity - 100) <= 5 ? '（通过）' : '（超出容差）' }}
                </template>
                <template v-else>○ 【{{ row.name }}】待计算</template>
              </div>
            </div>
          </div>
          <button @click="handleSubmitDecision"
            :disabled="!canSubmitDecision"
            :class="cn('w-full py-3.5 rounded-xl font-bold text-[15px] tracking-widest transition-all duration-300 flex items-center justify-center gap-2 border',
              canSubmitDecision
                ? 'bg-[#3B9EFF]/12 border-[#3B9EFF]/35 text-[#3B9EFF] hover:bg-[#3B9EFF]/20 hover:border-[#3B9EFF]/55'
                : 'bg-[#1A1E2B] border-[#2E3348] text-[#4A5568] cursor-not-allowed')"
          >
            <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
            正式提交 · 生成决议并同步部门资配指引
          </button>
        </div>

        <!-- ══ 决议下发与部门指引同步看板 ══ -->
        <div v-else class="space-y-3">
          <!-- 顶部成功 Banner -->
          <div class="bg-gradient-to-r from-[#051525] to-[#0A1A2B] border border-[#3B9EFF]/35 rounded-xl px-5 py-4 flex items-start gap-4">
            <div class="w-9 h-9 rounded-full bg-[#3B9EFF]/15 border border-[#3B9EFF]/35 flex items-center justify-center shrink-0 mt-0.5">
              <div class="w-1.5 h-4 bg-[#3B9EFF] rounded-sm shrink-0"></div>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-[14px] font-bold text-white leading-snug">已成功生成 2026年Q2混合投委会决议 并实时同步至部门战术资产配置 (TAA) 中心</div>
              <div class="flex items-center gap-3 mt-1.5">
                <span class="text-xs font-mono text-[#3B9EFF]">同步时间戳</span>
                <span class="text-xs font-mono tabular-nums text-[#94A3B8]">{{ syncedAt }}</span>
                <span class="text-xs font-mono px-2 py-0.5 rounded border border-[#3B9EFF]/30 bg-[#3B9EFF]/10 text-[#3B9EFF]">LIVE</span>
              </div>
            </div>
          </div>

          <!-- 核心：部门接收状态追踪流 -->
          <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl overflow-hidden">
            <div class="bg-gradient-to-r from-[#252A3A] to-[#1A1E2B] border-b border-[#252A3A] px-5 py-3 flex items-center gap-2">
              <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-sm shrink-0"></div>
              <h3 class="text-[13px] font-bold text-[#E8ECF4]">部门接收状态追踪流</h3>
              <span class="ml-auto text-xs font-mono text-[#64748B]">3 / 3 部门已同步</span>
            </div>
            <div class="p-4 grid grid-cols-3 gap-3">

              <!-- 固定收益投资部 -->
              <div class="bg-[#161922] border border-[#252A3A] rounded-xl p-4 space-y-3 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-[#3B9EFF] rounded-l-xl"></div>
                <div class="pl-2">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[12px] font-bold text-[#E8ECF4]">固定收益投资部</span>
                    <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded border border-[#3B9EFF]/40 bg-[#3B9EFF]/12 text-[#3B9EFF]">已接收</span>
                  </div>
                  <div class="text-xs text-[#94A3B8] mb-2.5">目标中枢已锁定</div>
                  <div class="space-y-1.5">
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                      <span class="text-xs font-mono text-[#B4BAC9]">利率 10Y</span>
                      <span class="ml-auto text-xs font-mono tabular-nums text-[#3B9EFF]">30%</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                      <span class="text-xs font-mono text-[#B4BAC9]">利率 30Y</span>
                      <span class="ml-auto text-xs font-mono tabular-nums text-[#3B9EFF]">20%</span>
                    </div>
                  </div>
                  <div class="mt-3 pt-2.5 border-t border-[#252A3A] flex items-center gap-2">
                    <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] animate-pulse shrink-0"></div>
                    <span class="text-[11px] font-mono text-[#64748B]">实时同步完成</span>
                  </div>
                </div>
              </div>

              <!-- 权益投资部 -->
              <div class="bg-[#161922] border border-[#252A3A] rounded-xl p-4 space-y-3 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-[#3B9EFF] rounded-l-xl"></div>
                <div class="pl-2">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[12px] font-bold text-[#E8ECF4]">权益投资部</span>
                    <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded border border-[#3B9EFF]/40 bg-[#3B9EFF]/12 text-[#3B9EFF]">已接收</span>
                  </div>
                  <div class="text-xs text-[#94A3B8] mb-2.5">风格中枢已下达</div>
                  <div class="space-y-1.5">
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                      <span class="text-xs font-mono text-[#B4BAC9]">红利</span>
                      <span class="ml-auto text-xs font-mono tabular-nums text-[#3B9EFF]">17%</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                      <span class="text-xs font-mono text-[#B4BAC9]">偏股混</span>
                      <span class="ml-auto text-xs font-mono tabular-nums text-[#3B9EFF]">16%</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                      <span class="text-xs font-mono text-[#B4BAC9]">恒生科技</span>
                      <span class="ml-auto text-xs font-mono tabular-nums text-[#3B9EFF]">9%</span>
                    </div>
                  </div>
                  <div class="mt-3 pt-2.5 border-t border-[#252A3A] flex items-center gap-2">
                    <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] animate-pulse shrink-0"></div>
                    <span class="text-[11px] font-mono text-[#64748B]">实时同步完成</span>
                  </div>
                </div>
              </div>

              <!-- 多资产/另类投资部 -->
              <div class="bg-[#161922] border border-[#252A3A] rounded-xl p-4 space-y-3 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-1 h-full bg-[#3B9EFF] rounded-l-xl"></div>
                <div class="pl-2">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[12px] font-bold text-[#E8ECF4]">多资产/另类投资部</span>
                    <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded border border-[#3B9EFF]/40 bg-[#3B9EFF]/12 text-[#3B9EFF]">已接收</span>
                  </div>
                  <div class="text-xs text-[#94A3B8] mb-2.5">商品仓位已下达</div>
                  <div class="space-y-1.5">
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0"></div>
                      <span class="text-xs font-mono text-[#B4BAC9]">黄金</span>
                      <span class="ml-auto text-xs font-mono tabular-nums text-[#3B9EFF]">15%</span>
                    </div>
                  </div>
                  <div class="mt-3 pt-2.5 border-t border-[#252A3A] flex items-center gap-2">
                    <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] animate-pulse shrink-0"></div>
                    <span class="text-[11px] font-mono text-[#64748B]">实时同步完成</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        <!-- ══ Monte Carlo 入口 ══ -->
        <div
          @click="showSAASandbox = true"
          class="relative group cursor-pointer overflow-hidden rounded-xl border border-cyan-500/25 bg-gradient-to-r from-[#06101A] via-[#1A1E2B] to-[#080C14] px-6 py-4 hover:border-cyan-400/50 transition-all duration-300 shadow-[0_0_30px_rgba(6,182,212,0.06)] hover:shadow-[0_0_50px_rgba(6,182,212,0.15)]"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/[0.04] via-transparent to-purple-500/[0.04] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div class="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out" />
          <div class="relative flex items-center justify-between">
            <div class="flex items-center space-x-4">
              <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500/15 to-purple-500/15 border border-cyan-500/25 flex items-center justify-center shadow-[0_0_16px_rgba(6,182,212,0.15)] group-hover:shadow-[0_0_32px_rgba(6,182,212,0.3)] transition-shadow duration-300">
                <div class="w-1.5 h-5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
              </div>
              <div>
                <div class="flex items-center space-x-3">
                  <span class="text-[15px] font-bold text-white tracking-wide">前瞻性蒙特卡洛压力测试</span>
                  <span class="text-xs font-mono text-cyan-400/70 bg-cyan-400/10 px-2 py-1 rounded-full border border-cyan-400/15 uppercase tracking-wider">Monte Carlo</span>
                </div>
                <p class="text-[13px] text-[#94A3B8] mt-0.5 font-mono">基于当前指引决议进行前瞻性压力测试与收益预测</p>
              </div>
            </div>
            <div class="flex items-center space-x-2 text-cyan-400 group-hover:translate-x-1 transition-transform duration-200 shrink-0 ml-6">
              <span class="text-[14px] font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200">进入沙盘</span>
              <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 会议纪要 (原 Step 4) ═══ -->
      <div v-if="activeTab === 'minutes'" class="space-y-4 pb-4">

        <!-- ══ S3 完成守卫 ══ -->
        <div v-if="!decisionSubmitted" class="bg-[#1A0E08] border border-[#3B9EFF]/30 rounded-xl p-5">
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
            <div>
              <div class="text-[15px] font-bold text-[#3B9EFF]">S3 决议尚未提交</div>
              <div class="text-[13px] font-mono text-[#94A3B8] mt-1">请先返回 Step 3，由主任委员完成决策并正式提交后，方可签发会议纪要。</div>
            </div>
          </div>
        </div>

        <!-- ══ 录音状态守卫 ══ -->
        <div id="nav-recording" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>全局录音状态</h3>
            <div class="flex items-center gap-2">
              <div v-if="recState === 'recording'" class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-[#FF3B30] animate-pulse"></div>
                <span class="text-[13px] font-mono text-[#FF3B30]">录音中 {{ recTimeDisplay }}</span>
              </div>
              <div v-else-if="recState === 'paused'" class="flex items-center gap-1.5">
                <div class="flex items-center gap-[2px]"><div class="w-[3px] h-3 rounded-sm bg-[#3B9EFF]"></div><div class="w-[3px] h-3 rounded-sm bg-[#3B9EFF]"></div></div>
                <span class="text-[13px] font-mono text-[#3B9EFF]">已暂停 · {{ recTimeDisplay }}</span>
              </div>
              <div v-else-if="recState === 'finished'" class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-[#3B9EFF]"></div>
                <span class="text-[13px] font-mono text-[#3B9EFF]">录音已结束 · {{ recTimeDisplay }}</span>
              </div>
              <div v-else class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-[#4A5568]"></div>
                <span class="text-[13px] font-mono text-[#6B7280]">未开始</span>
              </div>
            </div>
          </div>
          <div v-if="recState !== 'finished'" class="p-5 flex items-center gap-3">
            <div class="w-1.5 h-4 bg-[#3B9EFF] rounded-sm shrink-0"></div>
            <span class="text-[13px] text-[#3B9EFF]">请先在顶部全局控制栏结束录音，再生成 AI 纪要</span>
          </div>
          <div v-else class="p-5 flex items-center gap-3">
            <div class="w-1.5 h-4 bg-[#00C9A7] rounded-sm shrink-0"></div>
            <span class="text-[13px] text-[#00C9A7]">录音已完成，可生成 AI 纪要</span>
          </div>
        </div>

        <!-- ══ AI Minutes Generation (录音守卫) ══ -->
        <div v-if="recState === 'finished'" id="nav-ai-minutes" class="bg-[#202431] border border-[#3B9EFF]/20 rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#3B9EFF]/10 to-[#202431] border-b border-[#3B9EFF]/15 px-5 py-3.5 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h3 class="am-title-l2"><div class="am-title-bar"></div>AI 会议纪要</h3>
              <div v-if="aiMinutesLoading" class="flex items-center gap-1.5">
                <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] animate-pulse"></div>
                <span class="text-[13px] font-mono text-[#3B9EFF]">AI 正在处理...</span>
              </div>
            </div>
            <button v-if="!aiMinutesReady && !aiMinutesLoading" @click="generateAIMinutes" class="text-[13px] text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/18 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5">
              <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div> 生成 AI 纪要
            </button>
          </div>
          <div v-if="aiMinutesLoading" class="p-6 space-y-4">
            <div class="flex items-center gap-3">
              <div class="w-1.5 h-5 bg-[#3B9EFF] rounded-sm shrink-0 animate-pulse"></div>
              <span class="text-[15px] text-[#94A3B8]">AI 正在分析投票数据、识别争论焦点、生成结构化纪要...</span>
            </div>
            <div class="space-y-3">
              <div class="h-4 bg-[#1A1E2B] rounded animate-pulse w-3/4"></div>
              <div class="h-4 bg-[#1A1E2B] rounded animate-pulse w-1/2"></div>
              <div class="h-4 bg-[#1A1E2B] rounded animate-pulse w-2/3"></div>
              <div class="h-px bg-[#252A3A] my-2"></div>
              <div class="h-4 bg-[#1A1E2B] rounded animate-pulse w-5/6"></div>
              <div class="h-4 bg-[#1A1E2B] rounded animate-pulse w-3/5"></div>
              <div class="h-4 bg-[#1A1E2B] rounded animate-pulse w-4/5"></div>
            </div>
          </div>
          <div v-if="aiMinutesReady" class="p-6">
            <pre class="whitespace-pre-wrap text-[14px] font-mono text-[#B4BAC9] leading-relaxed bg-[#1A1E2B] border border-[#252A3A] rounded-lg p-5">{{ aiMinutesContent }}</pre>
          </div>
          <div v-if="!aiMinutesReady && !aiMinutesLoading" class="p-6 text-center">
            <p class="text-[13px] text-[#64748B]">点击上方按钮，AI 将基于投票矩阵和配置指引自动生成结构化会议纪要</p>
          </div>
        </div>

        <!-- ══ 签发人选择 + 正式签发 ══ -->
        <div v-if="recState === 'finished' && aiMinutesReady" class="bg-[#202431] border border-[#00C9A7]/20 rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#00C9A7]/10 to-[#202431] border-b border-[#00C9A7]/15 px-5 py-3.5">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-[#00C9A7]/15 border border-[#00C9A7]/30 flex items-center justify-center">
                <div class="w-1.5 h-4 bg-[#00C9A7] rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="text-[15px] font-bold text-[#00C9A7]">正式签发</h3>
                <p class="text-[13px] font-mono text-[#94A3B8] mt-0.5">选择签发人后确认签发</p>
              </div>
            </div>
          </div>
          <div class="p-5 space-y-4">
            <div class="flex items-center gap-4">
              <span class="text-[13px] text-[#94A3B8] shrink-0">签发人</span>
              <select v-model="signerId" :disabled="isIssued"
                class="bg-[#1A1E2B] border border-[#2E3348] text-[13px] font-mono rounded px-3 py-2 text-[#E8ECF4] focus:border-[#00C9A7] focus:outline-none transition-colors flex-1 max-w-[240px] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option v-for="m in MEMBERS_DATA" :key="m.id" :value="m.id">{{ m.name }}（{{ m.role }}）</option>
              </select>
              <span class="text-xs font-mono text-[#64748B]">{{ signerName }}</span>
            </div>
            <button
              @click="handleIssue"
              :disabled="isIssued || issuingLoading || !decisionSubmitted"
              :class="cn('w-full py-3.5 rounded-xl font-bold text-[15px] tracking-widest transition-all duration-300 flex items-center justify-center gap-2 border',
                isIssued ? 'bg-[#00C9A7]/10 border-[#00C9A7]/30 text-[#00C9A7] cursor-not-allowed' :
                issuingLoading ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/30 text-[#3B9EFF] cursor-wait' :
                'bg-[#00C9A7]/15 border-[#00C9A7]/30 text-[#00C9A7] hover:bg-[#00C9A7]/25')"
            >
              <div v-if="!issuingLoading" class="w-1.5 h-5 bg-current rounded-sm shrink-0"></div>
              <div v-else class="w-1.5 h-5 bg-current rounded-sm shrink-0 animate-pulse"></div>
              <span>{{ isIssued ? `已签发 · ${signerName} · ${issuedTime}` : issuingLoading ? '正在签发...' : '正式签发并全系统下达' }}</span>
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- ═══ 悬浮发令枪: 主任委员确认决议 ═══ -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div
        v-if="isChairman && activeTab === 'allocation' && !decisionSubmitted"
        class="fixed bottom-6 right-6 z-[8000]"
      >
        <button
          @click="handleSubmitDecision"
          :disabled="!canSubmitDecision"
          :class="cn(
            'px-8 py-4 rounded-2xl font-bold text-[16px] tracking-wide transition-all duration-200 flex items-center gap-3',
            canSubmitDecision
              ? 'bg-gradient-to-r from-[#3B9EFF] to-[#FF6B00] text-white shadow-[0_8px_32px_rgba(255,171,0,0.35)] hover:shadow-[0_12px_48px_rgba(255,171,0,0.5)] hover:scale-[1.02] active:scale-[0.98] backdrop-blur-xl'
              : 'bg-[#252A3A]/80 text-[#6B7280] cursor-not-allowed backdrop-blur-xl'
          )"
        >
          <div class="w-8 h-8 rounded-full flex items-center justify-center" :class="canSubmitDecision ? 'bg-white/20' : 'bg-[#1A1E2B]'">
            <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
          </div>
          <span>确认本期最终决议并全系统下发</span>
        </button>
      </div>
      <div
        v-else-if="isChairman && activeTab === 'allocation' && decisionSubmitted"
        class="fixed bottom-6 right-6 z-[8000]"
      >
        <div class="px-8 py-4 rounded-2xl font-bold text-[15px] bg-[#00C9A7]/15 border border-[#00C9A7]/30 text-[#00C9A7] backdrop-blur-xl shadow-lg flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-[#00C9A7]/20 flex items-center justify-center">
            <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
          </div>
          <span>决议已确认下发</span>
        </div>
      </div>
    </Transition>

    <!-- ═══ 悬浮发令枪: 秘书签发归档 ═══ -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div
        v-if="isSecretary && activeTab === 'minutes' && !isIssued"
        class="fixed bottom-6 right-6 z-[8000]"
      >
        <button
          @click="handleIssue"
          :disabled="issuingLoading || !decisionSubmitted"
          :class="cn(
            'px-8 py-4 rounded-2xl font-bold text-[16px] tracking-wide transition-all duration-200 flex items-center gap-3',
            !issuingLoading && decisionSubmitted
              ? 'bg-gradient-to-r from-[#3B9EFF] to-[#2563EB] text-white shadow-[0_8px_32px_rgba(59,158,255,0.35)] hover:shadow-[0_12px_48px_rgba(59,158,255,0.5)] hover:scale-[1.02] active:scale-[0.98] backdrop-blur-xl'
              : 'bg-[#252A3A]/80 text-[#6B7280] cursor-not-allowed backdrop-blur-xl'
          )"
        >
          <div v-if="issuingLoading" class="w-1.5 h-5 bg-current rounded-sm shrink-0 animate-pulse"></div>
          <div v-else class="w-8 h-8 rounded-full flex items-center justify-center" :class="!issuingLoading && decisionSubmitted ? 'bg-white/20' : 'bg-[#1A1E2B]'">
            <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
          </div>
          <span>{{ issuingLoading ? '正在签发...' : !decisionSubmitted ? '请先等待决议确认' : '确认签发会议纪要并归档' }}</span>
        </button>
      </div>
      <div
        v-else-if="isSecretary && activeTab === 'minutes' && isIssued"
        class="fixed bottom-6 right-6 z-[8000]"
      >
        <div class="px-8 py-4 rounded-2xl font-bold text-[15px] bg-[#34C759]/15 border border-[#34C759]/30 text-[#34C759] backdrop-blur-xl shadow-lg flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-[#34C759]/20 flex items-center justify-center">
            <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
          </div>
          <span>已签发归档 · {{ issuedTime }}</span>
        </div>
      </div>
    </Transition>

    <!-- ═══ Sparkline 大图浮层 ═══ -->
    <Teleport to="body">
      <Transition enter-active-class="transition-all duration-200 ease-out" enter-from-class="opacity-0" enter-to-class="opacity-100" leave-active-class="transition-all duration-150 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="showSparklineModal" class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="closeSparklineModal">
          <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-2xl overflow-hidden w-[600px] max-w-[95vw] shadow-[0_0_60px_rgba(0,0,0,0.6)]">
            <!-- 标题栏 -->
            <div class="flex items-center justify-between px-5 py-3.5 border-b border-[#252A3A] bg-[#202431]">
              <div class="flex items-center gap-3">
                <div class="am-title-bar shrink-0"></div>
                <span class="text-[14px] font-bold text-[#E8ECF4]">{{ sparklineModalRow?.name ?? '' }}</span>
                <span class="text-xs font-mono text-[#64748B]">近一年历史走势</span>
              </div>
              <div class="flex items-center gap-3">
                <span v-if="sparklineModalRow" class="text-xs font-mono font-bold tabular-nums"
                  :class="sparklineModalRow.retYtd >= 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                  YTD {{ sparklineModalRow.retYtd >= 0 ? '+' : '' }}{{ sparklineModalRow.retYtd.toFixed(2) }}%
                </span>
                <button @click="closeSparklineModal"
                  class="w-7 h-7 rounded-lg border border-[#2E3348] bg-[#161922] hover:bg-[#252A3A] text-[#94A3B8] hover:text-[#E8ECF4] transition-all flex items-center justify-center text-sm">
                  ✕
                </button>
              </div>
            </div>
            <!-- ECharts 图表区 -->
            <div class="p-4">
              <div ref="sparklineModalChartRef" style="height:280px;width:100%"></div>
            </div>
            <!-- 底部指标 -->
            <div v-if="sparklineModalRow" class="px-5 py-3 border-t border-[#252A3A] bg-[#161922] flex items-center gap-6 text-xs font-mono">
              <span class="text-[#64748B]">当前点位 <span class="text-[#E8ECF4] font-bold">{{ sparklineModalRow.point }}</span></span>
              <span class="text-[#64748B]">夏普 <span class="font-bold tabular-nums" :class="sparklineModalRow.sharpe >= 1 ? 'text-[#F04864]' : 'text-[#3B9EFF]'">{{ sparklineModalRow.sharpe.toFixed(2) }}</span></span>
              <span class="text-[#64748B]">卡玛 <span class="font-bold tabular-nums" :class="sparklineModalRow.calmar >= 1 ? 'text-[#F04864]' : 'text-[#3B9EFF]'">{{ sparklineModalRow.calmar.toFixed(2) }}</span></span>
              <span class="text-[#64748B]">最大回撤 <span class="text-[#00C9A7] font-bold tabular-nums">{{ sparklineModalRow.maxdd.toFixed(1) }}%</span></span>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ SAA SANDBOX ═══ -->
    <Teleport to="body">
      <Transition enter-active-class="transition-all duration-300 ease-out" enter-from-class="opacity-0 scale-[0.97]" enter-to-class="opacity-100 scale-100" leave-active-class="transition-all duration-200 ease-in" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-[0.97]">
        <div v-if="showSAASandbox" class="fixed inset-0 z-[9999] bg-[#161922]">
          <SAASimulator embedded @close="showSAASandbox = false" />
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ BL MODEL DETAIL DIALOG ═══ -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-250 ease-out"
        enter-from-class="opacity-0 scale-[0.98]"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-180 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-[0.98]"
      >
        <div
          v-if="showBLDialog"
          class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/65 backdrop-blur-sm"
          @click.self="closeBLDialog"
        >
          <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-2xl overflow-hidden shadow-[0_0_80px_rgba(0,0,0,0.7)] flex flex-col"
            style="width:82vw;max-width:1200px;max-height:88vh">

            <!-- ── 标题栏 ── -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-[#252A3A] bg-[#202431] shrink-0">
              <div class="flex items-center gap-3">
                <div class="w-1 h-5 bg-[#3B9EFF] rounded-full shrink-0"></div>
                <span class="text-[15px] font-bold text-white tracking-wide">BL 模型 · 原理与结果详情</span>
                <span class="text-xs font-mono px-2 py-0.5 rounded-full border border-cyan-500/30 text-cyan-400/80 bg-cyan-500/8">BLACK-LITTERMAN</span>
              </div>
              <button
                @click="closeBLDialog"
                class="w-7 h-7 rounded-lg border border-[#2E3348] bg-[#161922] hover:bg-[#252A3A] text-[#94A3B8] hover:text-[#E8ECF4] transition-all flex items-center justify-center text-sm"
              >✕</button>
            </div>

            <!-- ── 主体：左右分栏 ── -->
            <div class="flex flex-1 overflow-hidden">

              <!-- ══ 左侧：逻辑推导区 ══ -->
              <div class="w-[42%] border-r border-[#252A3A] overflow-y-auto p-5 space-y-5 shrink-0">

                <!-- 模型原理 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">模型原理</h4>
                  </div>
                  <p class="text-xs text-[#B4BAC9] leading-relaxed">
                    Black-Litterman 模型通过<span class="text-[#3B9EFF] font-medium">贝叶斯框架</span>，将两类信息源融合为统一的资产预期收益率：
                  </p>
                  <div class="mt-3 space-y-2">
                    <div class="flex items-start gap-2.5 bg-[#202431] rounded-lg px-3 py-2.5 border border-[#252A3A]">
                      <div class="w-1 h-3.5 bg-[#3B9EFF]/50 rounded-sm shrink-0 mt-0.5"></div>
                      <div>
                        <div class="text-xs font-medium text-[#E8ECF4]">先验分布 (Prior)</div>
                        <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">由市场均衡权重 w<sub>mkt</sub> 反向优化得出均衡隐含超额收益 <span class="font-mono text-[#3B9EFF]">Π</span>，代表市场"共识"。</div>
                      </div>
                    </div>
                    <div class="flex items-start gap-2.5 bg-[#202431] rounded-lg px-3 py-2.5 border border-[#252A3A]">
                      <div class="w-1 h-3.5 bg-cyan-400/50 rounded-sm shrink-0 mt-0.5"></div>
                      <div>
                        <div class="text-xs font-medium text-[#E8ECF4]">观点注入 (Views)</div>
                        <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">矩阵 <span class="font-mono text-cyan-400">P</span> 编码委员会对特定资产的主观判断，<span class="font-mono text-cyan-400">Q</span> 为预期超额收益，<span class="font-mono text-cyan-400">Ω</span> 表征观点不确定性。</div>
                      </div>
                    </div>
                    <div class="flex items-start gap-2.5 bg-[#202431] rounded-lg px-3 py-2.5 border border-[#252A3A]">
                      <div class="w-1 h-3.5 bg-[#00C9A7]/50 rounded-sm shrink-0 mt-0.5"></div>
                      <div>
                        <div class="text-xs font-medium text-[#E8ECF4]">后验融合 (Posterior)</div>
                        <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">贝叶斯更新产生新的期望收益向量 <span class="font-mono text-[#00C9A7]">E[R]</span>，再经均值-方差优化输出最终配置权重。</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 核心输入 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">核心输入参数</h4>
                    <span class="text-[11px] font-mono text-[#64748B] ml-auto">本期运行值</span>
                  </div>
                  <table class="w-full table-fixed text-xs">
                    <colgroup><col class="w-[52%]"><col class="w-[28%]"><col></colgroup>
                    <thead>
                      <tr class="border-b border-[#252A3A]">
                        <th class="text-left py-1.5 text-[#64748B] font-medium">参数</th>
                        <th class="text-right py-1.5 text-[#64748B] font-medium font-mono">数值</th>
                        <th class="text-right py-1.5 text-[#64748B] font-medium">说明</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-[#252A3A]/60">
                      <tr v-for="p in BL_PARAMS" :key="p.key">
                        <td class="py-2 text-[#B4BAC9]">
                          <span class="font-mono text-[#3B9EFF]">{{ p.symbol }}</span>
                          <span class="ml-1.5 text-[#94A3B8]">{{ p.name }}</span>
                        </td>
                        <td class="py-2 text-right font-mono font-bold tabular-nums" :class="p.highlight ? 'text-cyan-300' : 'text-[#E8ECF4]'">{{ p.value }}</td>
                        <td class="py-2 text-right text-[11px] text-[#64748B]">{{ p.note }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <!-- 计算公式 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">核心计算公式</h4>
                  </div>
                  <div class="space-y-2.5">
                    <div class="bg-[#0D1320] border border-[#252A3A] rounded-xl px-4 py-3.5">
                      <div class="text-[11px] font-mono text-[#64748B] mb-2 uppercase tracking-wider">Step 1 · 反向优化推导均衡收益</div>
                      <div class="font-mono text-[13px] text-[#E8ECF4] leading-loose text-center">
                        <span class="text-cyan-300">Π</span>
                        <span class="text-[#64748B] mx-1.5">=</span>
                        <span class="text-[#3B9EFF]">λ</span>
                        <span class="text-[#B4BAC9] mx-0.5">·</span>
                        <span class="text-[#3B9EFF]">Σ</span>
                        <span class="text-[#B4BAC9] mx-0.5">·</span>
                        <span class="text-[#E8ECF4]">w</span><sub class="text-[10px] text-[#64748B]">mkt</sub>
                      </div>
                      <div class="text-[11px] text-[#64748B] mt-2 leading-relaxed">λ = 风险厌恶系数，Σ = 历史协方差矩阵，w<sub>mkt</sub> = 市场基准权重</div>
                    </div>
                    <div class="bg-[#0D1320] border border-[#252A3A] rounded-xl px-4 py-3.5">
                      <div class="text-[11px] font-mono text-[#64748B] mb-2 uppercase tracking-wider">Step 2 · 贝叶斯更新后验期望</div>
                      <div class="font-mono text-[12px] text-[#E8ECF4] leading-loose text-center">
                        <span class="text-[#00C9A7]">E[R]</span>
                        <span class="text-[#64748B] mx-1.5">=</span>
                        <span class="text-[#94A3B8]">[</span>
                        <span class="text-[#3B9EFF]">(τΣ)</span><sup class="text-[10px]">-1</sup>
                        <span class="text-[#64748B] mx-1">+</span>
                        <span class="text-[#3B9EFF]">P'Ω</span><sup class="text-[10px]">-1</sup><span class="text-[#3B9EFF]">P</span>
                        <span class="text-[#94A3B8]">]</span><sup class="text-[10px]">-1</sup>
                      </div>
                      <div class="font-mono text-[12px] text-[#E8ECF4] text-center mt-0.5">
                        <span class="text-[#94A3B8]">·</span>
                        <span class="text-[#94A3B8] ml-1">[</span>
                        <span class="text-[#3B9EFF]">(τΣ)</span><sup class="text-[10px]">-1</sup>
                        <span class="text-cyan-300 mx-1">Π</span>
                        <span class="text-[#64748B] mx-1">+</span>
                        <span class="text-[#3B9EFF]">P'Ω</span><sup class="text-[10px]">-1</sup>
                        <span class="text-cyan-300">Q</span>
                        <span class="text-[#94A3B8]">]</span>
                      </div>
                      <div class="text-[11px] text-[#64748B] mt-2 leading-relaxed">P = 观点矩阵，Q = 观点预期超额收益，Ω = 观点不确定性协方差</div>
                    </div>
                    <div class="bg-[#0D1320] border border-[#252A3A] rounded-xl px-4 py-3.5">
                      <div class="text-[11px] font-mono text-[#64748B] mb-2 uppercase tracking-wider">Step 3 · 均值-方差最优化</div>
                      <div class="font-mono text-[13px] text-[#E8ECF4] leading-loose text-center">
                        <span class="text-[#00C9A7]">w*</span>
                        <span class="text-[#64748B] mx-1.5">=</span>
                        <span class="text-[#94A3B8]">(</span>
                        <span class="text-[#3B9EFF]">λΣ</span>
                        <span class="text-[#94A3B8]">)</span><sup class="text-[10px]">-1</sup>
                        <span class="text-[#B4BAC9] mx-1">·</span>
                        <span class="text-[#00C9A7]">E[R]</span>
                      </div>
                      <div class="text-[11px] text-[#64748B] mt-2 leading-relaxed">输出 w* 即为最终 BL 优化权重建议，受制于预设约束条件。</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- ══ 右侧：数据对比区 ══ -->
              <div class="flex-1 overflow-y-auto p-5 space-y-5">

                <!-- 资产权重对比图 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">资产权重对比</h4>
                    <span class="text-[11px] font-mono text-[#64748B] ml-auto">市场基准 vs BL 优化</span>
                  </div>
                  <div class="bg-[#202431] border border-[#252A3A] rounded-xl p-4">
                    <div ref="blDialogChartRef" style="height:220px;width:100%"></div>
                  </div>
                </div>

                <!-- 观点贡献度 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">委员会观点贡献度</h4>
                    <span class="text-[11px] font-mono text-[#64748B] ml-auto">本期观点对权重的拉动效应</span>
                  </div>
                  <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
                    <table class="w-full table-fixed text-xs">
                      <colgroup><col class="w-[30%]"><col class="w-[16%]"><col class="w-[16%]"><col class="w-[14%]"><col></colgroup>
                      <thead>
                        <tr class="border-b border-[#252A3A] bg-[#161922]">
                          <th class="text-left px-4 py-2.5 text-[#64748B] font-medium">观点内容</th>
                          <th class="text-right px-3 py-2.5 text-[#64748B] font-medium font-mono">预期超额</th>
                          <th class="text-right px-3 py-2.5 text-[#64748B] font-medium font-mono">权重拉动</th>
                          <th class="text-right px-3 py-2.5 text-[#64748B] font-medium">置信度</th>
                          <th class="text-left px-4 py-2.5 text-[#64748B] font-medium">方向</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-[#252A3A]/50">
                        <tr v-for="v in BL_VIEW_CONTRIBUTIONS" :key="v.asset" class="hover:bg-[#252A3A]/30 transition-colors">
                          <td class="px-4 py-2.5 text-[#B4BAC9]">
                            <div class="font-medium text-[#E8ECF4]">{{ v.asset }}</div>
                            <div class="text-[11px] text-[#64748B] mt-0.5">{{ v.source }}</div>
                          </td>
                          <td class="px-3 py-2.5 text-right font-mono font-bold tabular-nums"
                            :class="v.excessReturn > 0 ? 'text-[#F04864]' : 'text-[#00C9A7]'">
                            {{ v.excessReturn > 0 ? '+' : '' }}{{ v.excessReturn.toFixed(1) }}%
                          </td>
                          <td class="px-3 py-2.5 text-right font-mono font-bold tabular-nums"
                            :class="v.weightDelta > 0 ? 'text-[#F04864]' : (v.weightDelta < 0 ? 'text-[#00C9A7]' : 'text-[#94A3B8]')">
                            {{ v.weightDelta > 0 ? '+' : '' }}{{ v.weightDelta.toFixed(1) }}pp
                          </td>
                          <td class="px-3 py-2.5 text-right">
                            <div class="inline-flex items-center gap-1.5">
                              <div class="w-12 h-1.5 bg-[#161922] rounded-full overflow-hidden">
                                <div class="h-full rounded-full bg-[#3B9EFF]" :style="{ width: v.confidence + '%' }"></div>
                              </div>
                              <span class="font-mono text-[11px] text-[#94A3B8] tabular-nums">{{ v.confidence }}%</span>
                            </div>
                          </td>
                          <td class="px-4 py-2.5">
                            <span class="text-xs font-mono px-1.5 py-0.5 rounded border"
                              :class="v.direction === '看多' ? 'text-[#F04864] border-[#F04864]/30 bg-[#F04864]/8' : (v.direction === '看空' ? 'text-[#00C9A7] border-[#00C9A7]/30 bg-[#00C9A7]/8' : 'text-[#94A3B8] border-[#94A3B8]/20 bg-[#94A3B8]/5')">
                              {{ v.direction }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- 模型摘要 -->
                <div class="bg-[#202431] border border-cyan-500/15 rounded-xl px-5 py-4">
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-cyan-400/60 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">本期模型结论摘要</h4>
                  </div>
                  <div class="grid grid-cols-3 gap-3">
                    <div v-for="s in BL_SUMMARY_STATS" :key="s.label" class="bg-[#161922] rounded-lg px-3 py-2.5 text-center border border-[#252A3A]">
                      <div class="text-[11px] text-[#64748B] font-mono mb-1">{{ s.label }}</div>
                      <div class="text-[15px] font-bold font-mono tabular-nums" :class="s.color">{{ s.value }}</div>
                      <div class="text-[11px] text-[#94A3B8] mt-0.5">{{ s.note }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- ── 底部 Footer ── -->
            <div class="px-6 py-3.5 border-t border-[#252A3A] bg-[#161922] shrink-0 flex items-center justify-between">
              <span class="text-[11px] font-mono text-[#4A5568]">数据时间：本期会议 · {{ currentMeeting?.date ?? 'N/A' }} · BL 模型 v2.1</span>
              <button
                disabled
                class="text-xs font-mono px-4 py-1.5 rounded-lg border border-[#2E3348] text-[#4A5568] bg-[#161922] cursor-not-allowed opacity-50"
              >查看模型中心详情 (建设中)</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ MONTE CARLO DETAIL DIALOG ═══ -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-250 ease-out"
        enter-from-class="opacity-0 scale-[0.98]"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-180 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-[0.98]"
      >
        <div
          v-if="showMCDialog"
          class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/65 backdrop-blur-sm"
          @click.self="closeMCDialog"
        >
          <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-2xl overflow-hidden shadow-[0_0_80px_rgba(0,0,0,0.7)] flex flex-col"
            style="width:82vw;max-width:1200px;max-height:88vh">

            <!-- 标题栏 -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-[#252A3A] bg-[#202431] shrink-0">
              <div class="flex items-center gap-3">
                <div class="w-1 h-5 bg-[#3B9EFF] rounded-full shrink-0"></div>
                <span class="text-[15px] font-bold text-white tracking-wide">SAA 蒙特卡洛 · 有效前沿详情</span>
                <span class="text-xs font-mono px-2 py-0.5 rounded-full border border-[#3B9EFF]/30 text-[#3B9EFF]/80 bg-[#3B9EFF]/8">MC-SIM · 10万次</span>
              </div>
              <button
                @click="closeMCDialog"
                class="w-7 h-7 rounded-lg border border-[#2E3348] bg-[#161922] hover:bg-[#252A3A] text-[#94A3B8] hover:text-[#E8ECF4] transition-all flex items-center justify-center text-sm"
              >✕</button>
            </div>

            <!-- 主体：左右分栏 -->
            <div class="flex flex-1 overflow-hidden">

              <!-- 左侧：逻辑推导区 -->
              <div class="w-[38%] border-r border-[#252A3A] overflow-y-auto p-5 space-y-5 shrink-0">

                <!-- 模型说明 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">模型说明</h4>
                  </div>
                  <p class="text-xs text-[#B4BAC9] leading-relaxed">
                    蒙特卡洛模拟通过对大类资产收益率的<span class="text-[#3B9EFF] font-medium">随机抽样</span>（本期 <span class="font-mono text-[#3B9EFF]">100,000</span> 次），构造出海量可行权重组合并计算其预期收益与波动率，从而在风险-收益空间中描绘出<span class="text-[#3B9EFF] font-medium">均值-方差有效前沿</span>。
                  </p>
                  <div class="mt-3 space-y-2">
                    <div class="flex items-start gap-2.5 bg-[#202431] rounded-lg px-3 py-2.5 border border-[#252A3A]">
                      <div class="w-1 h-3.5 bg-[#3B9EFF]/50 rounded-sm shrink-0 mt-0.5"></div>
                      <div>
                        <div class="text-xs font-medium text-[#E8ECF4]">灰色散点</div>
                        <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">随机生成的 10 万组权重组合，分布在前沿曲线内侧，均为次优组合。</div>
                      </div>
                    </div>
                    <div class="flex items-start gap-2.5 bg-[#202431] rounded-lg px-3 py-2.5 border border-[#252A3A]">
                      <div class="w-1 h-3.5 bg-[#3B9EFF] rounded-sm shrink-0 mt-0.5"></div>
                      <div>
                        <div class="text-xs font-medium text-[#E8ECF4]">蓝色曲线（有效前沿）</div>
                        <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">在给定风险水平下预期收益最大的最优组合集合，代表可达到的最优风险-收益边界。</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 核心约束 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">核心约束条件</h4>
                    <span class="text-[11px] font-mono text-[#64748B] ml-auto">本期参数</span>
                  </div>
                  <div class="space-y-1.5">
                    <div v-for="c in MC_CONSTRAINTS" :key="c.label"
                      class="flex items-center justify-between bg-[#202431] border border-[#252A3A] rounded-lg px-3 py-2.5">
                      <div class="flex items-center gap-2">
                        <div class="w-1 h-3 rounded-sm shrink-0" :style="{ backgroundColor: c.color }"></div>
                        <span class="text-xs text-[#94A3B8]">{{ c.label }}</span>
                      </div>
                      <span class="text-xs font-mono font-bold text-[#E8ECF4]">{{ c.range }}</span>
                    </div>
                  </div>
                </div>

                <!-- 模拟参数 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">模拟运行参数</h4>
                  </div>
                  <table class="w-full table-fixed text-xs">
                    <colgroup><col class="w-[55%]"><col><col></colgroup>
                    <tbody class="divide-y divide-[#252A3A]/60">
                      <tr v-for="p in MC_SIM_PARAMS" :key="p.key">
                        <td class="py-2 text-[#94A3B8]">{{ p.name }}</td>
                        <td class="py-2 text-right font-mono font-bold tabular-nums" :class="p.highlight ? 'text-[#3B9EFF]' : 'text-[#E8ECF4]'">{{ p.value }}</td>
                        <td class="py-2 text-right text-[11px] text-[#64748B]">{{ p.unit }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 右侧：有效前沿图 + 配置明细 -->
              <div class="flex-1 overflow-y-auto p-5 space-y-4">
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">均值-方差有效前沿</h4>
                    <span class="text-[11px] font-mono text-[#64748B] ml-auto">点击蓝色节点查看配置</span>
                  </div>
                  <div class="bg-[#202431] border border-[#252A3A] rounded-xl p-4">
                    <div ref="mcChartRef" style="height:260px;width:100%"></div>
                  </div>
                </div>

                <!-- 点击后展示配置明细 -->
                <div v-if="mcSelectedAlloc" class="bg-[#202431] border border-[#3B9EFF]/25 rounded-xl px-5 py-4">
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF] rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">选中组合 · 大类资产配置明细</h4>
                    <div class="ml-auto flex items-center gap-3">
                      <span class="text-[11px] font-mono text-[#64748B]">波动率 <span class="text-[#3B9EFF] font-bold">{{ mcSelectedPoint?.vol }}%</span></span>
                      <span class="text-[11px] font-mono text-[#64748B]">收益 <span class="text-[#F04864] font-bold">{{ mcSelectedPoint?.ret }}%</span></span>
                      <span class="text-[11px] font-mono text-[#64748B]">Sharpe <span class="text-cyan-300 font-bold">{{ mcSelectedPoint?.sharpe }}</span></span>
                    </div>
                  </div>
                  <div class="space-y-2">
                    <div v-for="item in mcSelectedAlloc" :key="item.label" class="flex items-center gap-3">
                      <span class="text-[11px] font-mono text-[#94A3B8] w-[4.5rem] shrink-0">{{ item.label }}</span>
                      <div class="flex-1 h-2 bg-[#161922] rounded-full overflow-hidden">
                        <div class="h-full rounded-full transition-all duration-500" style="background:#3B9EFF" :style="{ width: item.weight + '%' }"></div>
                      </div>
                      <span class="text-[12px] font-mono font-bold text-[#3B9EFF] w-9 text-right shrink-0 tabular-nums">{{ item.weight }}%</span>
                    </div>
                  </div>
                </div>
                <div v-else class="flex items-center justify-center h-[72px] text-[12px] text-[#64748B] font-mono bg-[#202431] border border-dashed border-[#2E3348] rounded-xl">
                  ↑ 点击有效前沿上的蓝色节点，查看对应大类资产配置方案
                </div>

                <!-- 摘要指标 -->
                <div class="bg-[#202431] border border-[#252A3A] rounded-xl px-5 py-4">
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">本期模拟摘要</h4>
                  </div>
                  <div class="grid grid-cols-3 gap-3">
                    <div v-for="s in MC_SUMMARY" :key="s.label" class="bg-[#161922] rounded-lg px-3 py-2.5 text-center border border-[#252A3A]">
                      <div class="text-[11px] text-[#64748B] font-mono mb-1">{{ s.label }}</div>
                      <div class="text-[15px] font-bold font-mono tabular-nums" :class="s.color">{{ s.value }}</div>
                      <div class="text-[11px] text-[#94A3B8] mt-0.5">{{ s.note }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 底部 Footer -->
            <div class="px-6 py-3.5 border-t border-[#252A3A] bg-[#161922] shrink-0 flex items-center justify-between">
              <span class="text-[11px] font-mono text-[#4A5568]">数据时间：本期会议 · {{ currentMeeting?.date ?? 'N/A' }} · MC-SIM v1.4 · 100,000 次迭代</span>
              <button
                disabled
                class="text-xs font-mono px-4 py-1.5 rounded-lg border border-[#2E3348] text-[#4A5568] bg-[#161922] cursor-not-allowed opacity-50"
              >查看模型中心详情 (建设中)</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ RISK PARITY DETAIL DIALOG ═══ -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-250 ease-out"
        enter-from-class="opacity-0 scale-[0.98]"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-180 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-[0.98]"
      >
        <div
          v-if="showRPDialog"
          class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/65 backdrop-blur-sm"
          @click.self="closeRPDialog"
        >
          <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-2xl overflow-hidden shadow-[0_0_80px_rgba(0,0,0,0.7)] flex flex-col"
            style="width:82vw;max-width:1200px;max-height:88vh">

            <!-- 标题栏 -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-[#252A3A] bg-[#202431] shrink-0">
              <div class="flex items-center gap-3">
                <div class="w-1 h-5 bg-[#3B9EFF] rounded-full shrink-0"></div>
                <span class="text-[15px] font-bold text-white tracking-wide">Risk Parity · 风险平价模型详情</span>
                <span class="text-xs font-mono px-2 py-0.5 rounded-full border border-[#3B9EFF]/30 text-[#3B9EFF]/80 bg-[#3B9EFF]/8">RP-ATAN</span>
              </div>
              <button
                @click="closeRPDialog"
                class="w-7 h-7 rounded-lg border border-[#2E3348] bg-[#161922] hover:bg-[#252A3A] text-[#94A3B8] hover:text-[#E8ECF4] transition-all flex items-center justify-center text-sm"
              >✕</button>
            </div>

            <!-- 主体：左右分栏 -->
            <div class="flex flex-1 overflow-hidden">

              <!-- 左侧：模型原理 -->
              <div class="w-[42%] border-r border-[#252A3A] overflow-y-auto p-5 space-y-5 shrink-0">

                <!-- 模型原理 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">模型原理</h4>
                  </div>
                  <p class="text-xs text-[#B4BAC9] leading-relaxed">
                    风险平价（Risk Parity）的核心理念是<span class="text-[#3B9EFF] font-medium">风险等权</span>而非资金等权——不以资产金额多寡分配组合，而是令各类资产对组合总风险的<span class="text-[#3B9EFF] font-medium">贡献度相等</span>。由此实现真正意义上的分散化，防止单一资产的波动主导整体风险。
                  </p>
                  <div class="mt-3 space-y-2">
                    <div class="flex items-start gap-2.5 bg-[#202431] rounded-lg px-3 py-2.5 border border-[#252A3A]">
                      <div class="w-1 h-3.5 bg-[#3B9EFF]/50 rounded-sm shrink-0 mt-0.5"></div>
                      <div>
                        <div class="text-xs font-medium text-[#E8ECF4]">传统均值-方差</div>
                        <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">固收仓位 55% 但贡献约 20% 风险；权益仓位 30% 却贡献逾 60% 风险，风险高度集中。</div>
                      </div>
                    </div>
                    <div class="flex items-start gap-2.5 bg-[#202431] rounded-lg px-3 py-2.5 border border-[#252A3A]">
                      <div class="w-1 h-3.5 bg-[#00C9A7]/60 rounded-sm shrink-0 mt-0.5"></div>
                      <div>
                        <div class="text-xs font-medium text-[#E8ECF4]">风险平价优化后</div>
                        <div class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">每类资产风险贡献趋近 1/N，尾部风险显著压缩，组合回撤韧性更强。</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 计算公式 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">边际风险贡献公式</h4>
                  </div>
                  <div class="space-y-2.5">
                    <div class="bg-[#0D1320] border border-[#252A3A] rounded-xl px-4 py-4">
                      <div class="text-[11px] font-mono text-[#64748B] mb-3 uppercase tracking-wider">边际风险贡献 (MRC)</div>
                      <div class="font-mono text-[14px] text-[#E8ECF4] text-center leading-loose">
                        <span class="text-[#00C9A7]">RC</span><sub class="text-[10px] text-[#64748B]">i</sub>
                        <span class="text-[#64748B] mx-2">=</span>
                        <span class="text-[#3B9EFF]">w</span><sub class="text-[10px] text-[#64748B]">i</sub>
                        <span class="text-[#94A3B8] mx-1.5">·</span>
                        <span class="text-[#94A3B8] text-[16px]">∂</span><span class="text-[#3B9EFF]">σ</span><sub class="text-[10px] text-[#64748B]">p</sub>
                        <span class="text-[#64748B] mx-1">/</span>
                        <span class="text-[#94A3B8] text-[16px]">∂</span><span class="text-[#3B9EFF]">w</span><sub class="text-[10px] text-[#64748B]">i</sub>
                      </div>
                      <div class="mt-3 space-y-1">
                        <div class="text-[11px] text-[#64748B] leading-relaxed"><span class="font-mono text-[#00C9A7]">RC<sub>i</sub></span> — 第 i 类资产对组合总波动率的风险贡献</div>
                        <div class="text-[11px] text-[#64748B] leading-relaxed"><span class="font-mono text-[#3B9EFF]">w<sub>i</sub></span> — 第 i 类资产当前持仓权重</div>
                        <div class="text-[11px] text-[#64748B] leading-relaxed"><span class="font-mono text-[#3B9EFF]">σ<sub>p</sub></span> — 组合总波动率（由协方差矩阵 Σ 计算）</div>
                      </div>
                    </div>
                    <div class="bg-[#0D1320] border border-[#252A3A] rounded-xl px-4 py-3.5">
                      <div class="text-[11px] font-mono text-[#64748B] mb-2 uppercase tracking-wider">风险平价目标函数</div>
                      <div class="font-mono text-[13px] text-[#E8ECF4] text-center leading-loose">
                        <span class="text-[#64748B]">min</span>
                        <span class="text-[#94A3B8] mx-2">∑</span>
                        <span class="text-[#94A3B8]">(</span>
                        <span class="text-[#00C9A7]">RC</span><sub class="text-[10px] text-[#64748B]">i</sub>
                        <span class="text-[#64748B] mx-1">-</span>
                        <span class="text-[#3B9EFF]">σ</span><sub class="text-[10px] text-[#64748B]">p</sub>
                        <span class="text-[#64748B] mx-0.5">/</span>
                        <span class="text-[#E8ECF4]">N</span>
                        <span class="text-[#94A3B8]">)</span><sup class="text-[10px]">2</sup>
                      </div>
                      <div class="text-[11px] text-[#64748B] mt-2 leading-relaxed">使各资产风险贡献均等趋近于 σ<sub>p</sub>/N，迭代求解权重 w*。</div>
                    </div>
                  </div>
                </div>

                <!-- 模型参数 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">本期运行参数</h4>
                  </div>
                  <table class="w-full table-fixed text-xs">
                    <colgroup><col class="w-[52%]"><col><col></colgroup>
                    <tbody class="divide-y divide-[#252A3A]/60">
                      <tr v-for="p in RP_PARAMS" :key="p.key">
                        <td class="py-2 text-[#94A3B8]">{{ p.name }}</td>
                        <td class="py-2 text-right font-mono font-bold tabular-nums" :class="p.highlight ? 'text-[#00C9A7]' : 'text-[#E8ECF4]'">{{ p.value }}</td>
                        <td class="py-2 text-right text-[11px] text-[#64748B]">{{ p.note }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 右侧：资金权重 vs 风险贡献对比 -->
              <div class="flex-1 overflow-y-auto p-5 space-y-5">

                <div>
                  <div class="flex items-center gap-2 mb-1">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">资金分配权重 vs 风险贡献度</h4>
                  </div>
                  <p class="text-xs text-[#64748B] mb-3 pl-3">固收类占资金大头，但经 RP 优化后各资产风险贡献趋近均等——这正是模型核心价值所在。</p>
                  <div class="bg-[#202431] border border-[#252A3A] rounded-xl p-4">
                    <div ref="rpChartRef" style="height:260px;width:100%"></div>
                  </div>
                </div>

                <!-- 风险贡献明细表 -->
                <div>
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#3B9EFF]/70 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">各资产风险贡献明细</h4>
                  </div>
                  <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
                    <table class="w-full table-fixed text-xs">
                      <colgroup><col class="w-[24%]"><col class="w-[19%]"><col class="w-[19%]"><col class="w-[19%]"><col></colgroup>
                      <thead>
                        <tr class="border-b border-[#252A3A] bg-[#161922]">
                          <th class="text-left px-4 py-2.5 text-[#64748B] font-medium">资产类别</th>
                          <th class="text-right px-3 py-2.5 text-[#64748B] font-medium font-mono">资金权重</th>
                          <th class="text-right px-3 py-2.5 text-[#64748B] font-medium font-mono">风险贡献</th>
                          <th class="text-right px-3 py-2.5 text-[#64748B] font-medium font-mono">年化波动</th>
                          <th class="text-right px-4 py-2.5 text-[#64748B] font-medium">风险均衡度</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-[#252A3A]/50">
                        <tr v-for="a in RP_ASSET_DETAIL" :key="a.name" class="hover:bg-[#252A3A]/30 transition-colors">
                          <td class="px-4 py-2.5 text-[#E8ECF4] font-medium">{{ a.name }}</td>
                          <td class="px-3 py-2.5 text-right font-mono font-bold tabular-nums text-[#3B9EFF]">{{ a.capitalWeight }}%</td>
                          <td class="px-3 py-2.5 text-right font-mono font-bold tabular-nums text-[#00C9A7]">{{ a.riskContrib }}%</td>
                          <td class="px-3 py-2.5 text-right font-mono tabular-nums text-[#94A3B8]">{{ a.annVol }}%</td>
                          <td class="px-4 py-2.5 text-right">
                            <div class="inline-flex items-center gap-1.5">
                              <div class="w-14 h-1.5 bg-[#161922] rounded-full overflow-hidden">
                                <div class="h-full rounded-full bg-[#00C9A7]" :style="{ width: (a.riskContrib / 20 * 100) + '%' }"></div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- 摘要 -->
                <div class="bg-[#202431] border border-[#00C9A7]/15 rounded-xl px-5 py-4">
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-0.5 h-4 bg-[#00C9A7]/60 rounded-full shrink-0"></div>
                    <h4 class="text-[13px] font-semibold text-[#E8ECF4]">本期模型结论摘要</h4>
                  </div>
                  <div class="grid grid-cols-3 gap-3">
                    <div v-for="s in RP_SUMMARY" :key="s.label" class="bg-[#161922] rounded-lg px-3 py-2.5 text-center border border-[#252A3A]">
                      <div class="text-[11px] text-[#64748B] font-mono mb-1">{{ s.label }}</div>
                      <div class="text-[15px] font-bold font-mono tabular-nums" :class="s.color">{{ s.value }}</div>
                      <div class="text-[11px] text-[#94A3B8] mt-0.5">{{ s.note }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 底部 Footer -->
            <div class="px-6 py-3.5 border-t border-[#252A3A] bg-[#161922] shrink-0 flex items-center justify-between">
              <span class="text-[11px] font-mono text-[#4A5568]">数据时间：本期会议 · {{ currentMeeting?.date ?? 'N/A' }} · RP-ATAN v2.0 · 协方差窗口 252 日</span>
              <button
                disabled
                class="text-xs font-mono px-4 py-1.5 rounded-lg border border-[#2E3348] text-[#4A5568] bg-[#161922] cursor-not-allowed opacity-50"
              >查看模型中心详情 (建设中)</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ MEETING MANAGEMENT DRAWER (秘书专属) ═══ -->
    <Transition
      enter-active-class="transition-transform duration-300 ease-out"
      enter-from-class="translate-x-full"
      enter-to-class="translate-x-0"
      leave-active-class="transition-transform duration-200 ease-in"
      leave-from-class="translate-x-0"
      leave-to-class="translate-x-full"
    >
      <div v-if="showMeetingDrawer" class="fixed inset-y-0 right-0 z-[9000] w-[520px] max-w-[90vw] bg-[#161922] border-l border-[#2E3348] shadow-[-8px_0_30px_rgba(0,0,0,0.5)] flex flex-col">
        <!-- Drawer Header -->
        <div class="shrink-0 px-5 py-4 border-b border-[#2E3348] flex items-center justify-between bg-gradient-to-r from-[#202431] to-[#161922]">
          <div class="flex items-center gap-2">
            <div class="am-title-bar"></div>
            <span class="text-[15px] font-bold text-[#E8ECF4]">会议管理</span>
            <span class="text-xs font-mono text-[#64748B] bg-[#1A1E2B] px-2 py-1 rounded border border-[#252A3A]">CRUD</span>
          </div>
          <button @click="showMeetingDrawer = false" class="text-[#94A3B8] hover:text-[#E8ECF4] transition-colors p-1">
            <div class="w-0.5 h-4 bg-current rounded-full shrink-0"></div>
          </button>
        </div>

        <!-- Drawer Toolbar -->
        <div class="shrink-0 px-5 py-3 border-b border-[#252A3A] flex items-center justify-between bg-[#1A1E2B]">
          <span class="text-xs font-mono text-[#64748B]">共 {{ meetingList.length }} 条记录</span>
          <button @click="quickCreateMeeting" class="flex items-center gap-1.5 text-[13px] px-3 py-1.5 rounded-lg border border-[#3B9EFF]/25 bg-[#3B9EFF]/10 text-[#3B9EFF] hover:bg-[#3B9EFF]/18 transition-colors">
            <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div> 新增会议
          </button>
        </div>

        <!-- Drawer Body -->
        <div class="flex-1 overflow-y-auto no-scrollbar">
          <div class="divide-y divide-[#252A3A]">
            <div
              v-for="m in meetingList"
              :key="m.id"
              class="px-5 py-4 hover:bg-[#1A1E2B]/50 transition-colors"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-[14px] font-semibold text-[#E8ECF4] truncate">{{ m.name }}</span>
                    <span :class="cn('text-xs font-mono px-1.5 py-1 rounded border',
                      m.status === '已结束' ? 'bg-[#94A3B8]/10 border-[#94A3B8]/25 text-[#94A3B8]' :
                      m.status === '进行中' ? 'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]' :
                      'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]')">{{ m.status }}</span>
                  </div>
                  <div class="flex items-center gap-3 text-xs font-mono text-[#64748B]">
                    <span>{{ m.date }}</span>
                    <span>{{ m.time }}</span>
                    <span>{{ m.location }}</span>
                  </div>
                  <div v-if="m.decision" class="text-xs text-[#94A3B8] mt-1 truncate">{{ m.decision }}</div>
                </div>
                <div class="flex items-center gap-1 shrink-0 ml-3">
                  <button @click="openEditMeeting(m.id)" class="text-xs px-2 py-1 rounded border border-[#252A3A] text-[#94A3B8] hover:border-[#3B9EFF]/30 hover:text-[#3B9EFF] transition-colors flex items-center gap-1">
                    <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div> 编辑
                  </button>
                  <button
                    v-if="m.status === '进行中'"
                    @click="deleteMeeting(m.id)"
                    class="text-xs px-2 py-1 rounded border border-[#252A3A] text-[#94A3B8] hover:border-[#F04864]/30 hover:text-[#F04864] transition-colors flex items-center gap-1"
                  >
                    <div class="w-0.5 h-3 bg-current rounded-full shrink-0"></div> 删除
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="meetingList.length === 0" class="py-16 text-center">
            <p class="text-[13px] text-[#4A5568]">暂无会议记录</p>
          </div>
        </div>

        <!-- Drawer Footer -->
        <div class="shrink-0 px-5 py-3 border-t border-[#2E3348] bg-[#1A1E2B]">
          <div class="flex items-center justify-between text-xs font-mono text-[#4A5568]">
            <span>模拟数据 · 仅前端 CRUD 演示</span>
            <span>最后更新: {{ new Date().toLocaleDateString('zh-CN') }}</span>
          </div>
        </div>
      </div>
    </Transition>
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="showMeetingDrawer" class="fixed inset-0 z-[8999] bg-black/40 backdrop-blur-sm" @click="showMeetingDrawer = false"></div>
    </Transition>

      <!-- ═══ EDIT MEETING DRAWER ═══ -->
      <Transition
        enter-active-class="transition-transform duration-300 ease-out"
        enter-from-class="translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transition-transform duration-200 ease-in"
        leave-from-class="translate-x-0"
        leave-to-class="translate-x-full"
      >
        <div v-if="showEditMeetingDrawer" class="fixed inset-y-0 right-0 z-[9150] w-[640px] max-w-[95vw] bg-[#161922] border-l border-[#2E3348] shadow-[-10px_0_40px_rgba(0,0,0,0.65)] flex flex-col">
          <!-- Drawer Header -->
          <div class="shrink-0 px-6 py-4 border-b border-[#2E3348] flex items-center justify-between bg-gradient-to-r from-[#202431] to-[#161922]">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="am-title-bar" style="background:#3B9EFF; flex-shrink:0"></div>
              <span class="text-[15px] font-bold text-[#E8ECF4] shrink-0">编辑会议</span>
              <span class="text-xs font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-1.5 py-1 rounded truncate">{{ editingMeetingTitle }}</span>
            </div>
            <button @click="showEditMeetingDrawer = false" class="text-[#94A3B8] hover:text-[#E8ECF4] transition-colors p-1 shrink-0 ml-2">
              <div class="w-0.5 h-4 bg-current rounded-full shrink-0"></div>
            </button>
          </div>
          <!-- Drawer Body -->
          <div class="flex-1 overflow-y-auto no-scrollbar">
            <!-- ── 基础属性 ── -->
            <div class="px-6 py-5 border-b border-[#252A3A] space-y-4">
              <div class="text-xs font-mono text-[#3B9EFF] uppercase tracking-wider">基础属性</div>
              <!-- 会议属性 -->
              <div>
                <label class="text-xs font-mono text-[#94A3B8] block mb-2">会议属性</label>
                <div class="flex gap-2 flex-wrap">
                  <button v-for="t in MEETING_TYPES" :key="t"
                    @click="editingMeetingForm.meetingType = t; editingMeetingForm.meetingPeriod = PERIOD_OPTIONS[t][0]"
                    :class="cn('px-3.5 py-1 text-[14px] rounded-lg border transition-all',
                      editingMeetingForm.meetingType === t
                        ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                        : 'bg-[#1A1E2B] border-[#252A3A] text-[#6B7280] hover:text-[#94A3B8]')"
                  >{{ t }}</button>
                </div>
              </div>
              <!-- 期次 -->
              <div>
                <label class="text-xs font-mono text-[#94A3B8] block mb-2">期次</label>
                <div class="flex flex-wrap gap-2">
                  <button v-for="p in editingMeetingPeriodOptions" :key="p"
                    @click="editingMeetingForm.meetingPeriod = p"
                    :class="cn('px-3 py-1 text-[14px] rounded border font-mono transition-all',
                      editingMeetingForm.meetingPeriod === p
                        ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                        : 'bg-[#1A1E2B] border-[#252A3A] text-[#6B7280] hover:text-[#94A3B8]')"
                  >{{ p }}</button>
                </div>
              </div>
              <!-- 年份 -->
              <div>
                <label class="text-xs font-mono text-[#94A3B8] block mb-2">年份</label>
                <div class="flex gap-2">
                  <button v-for="y in [2024,2025,2026,2027]" :key="y"
                    @click="editingMeetingForm.meetingYear = y"
                    :class="cn('px-3 py-1 text-[14px] rounded border font-mono transition-all',
                      editingMeetingForm.meetingYear === y
                        ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                        : 'bg-[#1A1E2B] border-[#252A3A] text-[#6B7280] hover:text-[#94A3B8]')"
                  >{{ y }}</button>
                </div>
              </div>
              <!-- 标题预览 -->
              <div class="bg-[#1A1E2B] border border-[#3B9EFF]/15 rounded-lg px-4 py-2.5">
                <span class="text-xs font-mono text-[#3B9EFF] mr-2">标题预览</span>
                <span class="text-[14px] font-bold text-[#E8ECF4]">{{ editingMeetingTitle }}</span>
              </div>
              <!-- 日期 时间 地点 -->
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs font-mono text-[#94A3B8] block mb-1.5">日期</label>
                  <input type="date" v-model="editingMeetingForm.date" style="color-scheme:dark"
                    class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-lg px-3 py-1.5 text-[14px] text-[#E8ECF4] font-mono focus:border-[#3B9EFF] focus:outline-none transition-colors"
                  />
                </div>
                <div>
                  <label class="text-xs font-mono text-[#94A3B8] block mb-1.5">时间</label>
                  <input type="text" v-model="editingMeetingForm.time"
                    class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-lg px-3 py-1.5 text-[14px] text-[#E8ECF4] font-mono focus:border-[#3B9EFF] focus:outline-none transition-colors"
                  />
                </div>
              </div>
              <div>
                <label class="text-xs font-mono text-[#94A3B8] block mb-1.5">地点</label>
                <input type="text" v-model="editingMeetingForm.location"
                  class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-lg px-3 py-1.5 text-[14px] text-[#E8ECF4] font-mono focus:border-[#3B9EFF] focus:outline-none transition-colors"
                />
              </div>
              <!-- 状态 -->
              <div>
                <label class="text-xs font-mono text-[#94A3B8] block mb-2">状态</label>
                <div class="flex gap-2">
                  <button v-for="s in MEETING_STATUS_LIST" :key="s"
                    @click="editingMeetingForm.status = s"
                    :class="cn('px-3 py-1 text-[14px] rounded border transition-all',
                      editingMeetingForm.status === s
                        ? s === '进行中' ? 'bg-[#00C9A7]/15 border-[#00C9A7]/40 text-[#00C9A7]'
                          : s === '已结束' ? 'bg-[#94A3B8]/15 border-[#94A3B8]/40 text-[#94A3B8]'
                          : s === '已取消' ? 'bg-[#F04864]/15 border-[#F04864]/40 text-[#F04864]'
                          : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                        : 'bg-[#1A1E2B] border-[#252A3A] text-[#6B7280] hover:text-[#94A3B8]')"
                  >{{ s }}</button>
                </div>
              </div>
            </div>

            <!-- ── 投票截止控制 ── -->
            <div class="px-6 py-5 border-b border-[#252A3A] space-y-4">
              <div class="text-xs font-mono text-[#3B9EFF] uppercase tracking-wider">投票截止控制</div>
              <div>
                <label class="text-xs font-mono text-[#94A3B8] block mb-1.5">截止时间</label>
                <input type="datetime-local" v-model="editingMeetingForm.voteDeadline" style="color-scheme:dark"
                  class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-lg px-3 py-1.5 text-[14px] text-[#E8ECF4] font-mono focus:border-[#3B9EFF] focus:outline-none transition-colors"
                />
              </div>
              <label class="flex items-center gap-3 cursor-pointer group">
                <div
                  @click="editingMeetingForm.voteForcedClosed = !editingMeetingForm.voteForcedClosed"
                  :class="cn('w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-all',
                    editingMeetingForm.voteForcedClosed
                      ? 'bg-[#F04864] border-[#F04864]'
                      : 'border-[#2E3348] group-hover:border-[#F04864]/40')"
                >
                  <div v-if="editingMeetingForm.voteForcedClosed" class="w-0.5 h-2.5 bg-white rounded-sm"></div>
                </div>
                <span :class="cn('text-[14px]', editingMeetingForm.voteForcedClosed ? 'text-[#F04864]' : 'text-[#94A3B8]')">
                  强制截止（无论截止时间，立即锁定委员端）
                </span>
              </label>
            </div>

            <!-- ── 会前材料链接 ── -->
            <div class="px-6 py-5 border-b border-[#252A3A] space-y-3">
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider">会前材料链接</div>
              <textarea v-model="editingMeetingForm.preMaterials" rows="5"
                placeholder="每行粘贴一条文档/研报链接&#10;https://confluence.example.com/..."
                class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-xl px-4 py-3 text-[14px] text-[#B4BAC9] font-mono focus:border-[#3B9EFF] focus:outline-none resize-none placeholder-[#3A4555] leading-relaxed"
              ></textarea>
              <p class="text-xs font-mono text-[#4A5568]">材料链接将在会前通知邮件中自动附带</p>
            </div>

            <!-- ── 会议纪要模板 ── -->
            <div class="px-6 py-5 space-y-3">
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider">会议初步纪要模板</div>
              <textarea v-model="editingMeetingForm.minutesTemplate" rows="12"
                placeholder="在此输入纪要结构模板..."
                class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-xl px-4 py-3 text-[14px] text-[#B4BAC9] font-mono focus:border-[#3B9EFF] focus:outline-none resize-none placeholder-[#3A4555] leading-relaxed"
              ></textarea>
              <p class="text-xs font-mono text-[#4A5568]">此模板将在 AI 纪要生成时作为结构参考</p>
            </div>
          </div>
          <!-- Drawer Footer -->
          <div class="shrink-0 px-6 py-4 border-t border-[#2E3348] bg-[#1A1E2B] flex items-center justify-between">
            <button @click="showEditMeetingDrawer = false"
              class="px-4 py-2 text-[14px] text-[#94A3B8] border border-[#2E3348] rounded-lg hover:border-[#3B9EFF]/30 hover:text-[#3B9EFF] transition-colors">
              取消
            </button>
            <button @click="saveEditMeeting"
              class="px-5 py-2 text-[14px] bg-[#3B9EFF]/15 border border-[#3B9EFF]/40 text-[#3B9EFF] rounded-lg hover:bg-[#3B9EFF]/25 transition-colors font-bold">
              保存修改
            </button>
          </div>
        </div>
      </Transition>
      <!-- Edit drawer backdrop -->
      <Transition enter-active-class="transition-opacity duration-200" enter-from-class="opacity-0" enter-to-class="opacity-100" leave-active-class="transition-opacity duration-150" leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="showEditMeetingDrawer" class="fixed inset-0 z-[9050] bg-black/40 backdrop-blur-sm" @click="showEditMeetingDrawer = false"></div>
      </Transition>

      <div v-if="showHistoryModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showHistoryModal = false">
        <div class="bg-[#202431] border border-[#2E3348] rounded-lg shadow-2xl w-[700px] max-h-[80vh] overflow-hidden flex flex-col">
          <div class="px-4 py-3 border-b border-[#2E3348] flex items-center justify-between shrink-0">
            <div class="flex items-center gap-2">
              <div class="am-title-bar"></div>
              <span class="text-[15px] font-semibold text-[#E8ECF4]">历史投票记录</span>
              <span class="text-[13px] font-mono text-[#94A3B8]">近 3 期</span>
            </div>
            <button @click="showHistoryModal = false" class="text-[#94A3B8] hover:text-[#E8ECF4] transition-colors p-0.5">
              <div class="w-0.5 h-4 bg-current rounded-full shrink-0"></div>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto no-scrollbar p-4">
            <table class="w-full border-collapse table-fixed text-[14px]">
              <thead class="sticky top-0 bg-[#202431] z-10">
                <tr class="border-b border-[#2E3348] text-[#94A3B8]">
                  <th class="px-3 py-2 text-left font-medium" style="width:100px">期次</th>
                  <th v-for="asset in ASSET_LIST" :key="asset" class="px-2 py-2 text-center font-medium">{{ asset }}</th>
                  <th class="px-3 py-2 text-center font-medium" style="width:115px">新高预判</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="row in historicalVotes" :key="row.period" class="hover:bg-[#1A1E2B] transition-colors">
                  <td class="px-3 py-2.5 text-[#E8ECF4] font-mono font-semibold">{{ row.period }}</td>
                  <td v-for="asset in ASSET_LIST" :key="asset" class="px-2 py-2.5 text-center">
                    <span :class="cn('text-[13px] font-mono font-bold px-1.5 py-1 rounded border', SCORE_COLORS[row.scores[asset]] || '')">
                      {{ row.scores[asset] }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-center">
                    <span class="text-[13px] font-mono text-[#00C9A7]">{{ row.newHighs.join(', ') }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="px-4 py-2.5 border-t border-[#2E3348] shrink-0 text-[13px] text-[#64748B] font-mono text-center">
            评分对照: 1-谨慎 · 2-中性偏谨慎 · 3-中性 · 4-中性偏乐观 · 5-乐观
          </div>
        </div>
      </div>
    </template>

    <!-- ═══ 投票确认对话框 ═══ -->
    <Teleport to="body">
      <div v-if="showVoteConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showVoteConfirm = false">
        <div class="bg-[#202431] border border-[#2E3348] rounded-2xl w-full max-w-lg shadow-[0_8px_48px_rgba(0,0,0,0.6)]">
          <div class="bg-gradient-to-r from-[#3B9EFF]/10 to-[#202431] border-b border-[#252A3A] px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 flex items-center justify-center">
                <div class="w-1.5 h-4 bg-[#3B9EFF] rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="text-[15px] font-bold text-white">确认提交投票</h3>
                <p class="text-xs text-[#94A3B8] mt-0.5 font-mono">提交后投票窗口内仍可更新</p>
              </div>
            </div>
            <button @click="showVoteConfirm = false" class="w-7 h-7 rounded-lg border border-[#252A3A] flex items-center justify-center text-[#6B7280] hover:text-white hover:border-[#3B9EFF]/30 transition-colors">
              <div class="w-0.5 h-3.5 bg-current rounded-full shrink-0"></div>
            </button>
          </div>
          <div class="px-6 py-4 space-y-4 max-h-[50vh] overflow-y-auto no-scrollbar">
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">A. 资产评分摘要</div>
              <div class="grid grid-cols-3 gap-2">
                <div v-for="(score, asset) in FORM_SECTION_A" :key="asset" class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-3 py-2 flex items-center justify-between">
                  <span class="text-xs text-[#B4BAC9] truncate">{{ asset }}</span>
                  <span :class="cn('text-xs font-bold font-mono', SCORE_COLORS[score] || 'text-[#94A3B8]')">{{ score }} · {{ SCORE_LABELS[score] || '-' }}</span>
                </div>
              </div>
            </div>
            <div v-if="Object.values(FORM_SECTION_B).some(Boolean)">
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">B. 创新高预判</div>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="(val, key) in FORM_SECTION_B" :key="key" v-show="val"
                  class="text-xs font-mono px-2 py-1 rounded border bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]">{{ key }}</span>
              </div>
            </div>
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">C. 重点资产</div>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="(checked, key) in FORM_SECTION_C" :key="key" v-show="checked"
                  class="text-xs font-mono px-2 py-1 rounded border bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]">{{ key }}</span>
              </div>
            </div>
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">D. 核心观点</div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3 text-[13px] text-[#B4BAC9] leading-relaxed">{{ formCoreView }}</div>
            </div>
            <div v-if="formRiskFlag" class="flex items-center gap-2 bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 rounded-lg px-4 py-2.5">
              <div class="w-1.5 h-3.5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
              <span class="text-[13px] text-[#3B9EFF]">已标记尾部风险事项</span>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-[#252A3A] flex items-center gap-3">
            <button @click="showVoteConfirm = false" class="flex-1 py-2.5 rounded-lg border border-[#252A3A] text-[#94A3B8] hover:border-[#2E3348] hover:text-white transition-colors text-[13px]">返回修改</button>
            <button @click="showVoteConfirm = false; submitMemberFormSelf()" class="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-[#3B9EFF] to-[#3B9EFF] text-white font-bold text-[13px] shadow-[0_4px_16px_rgba(59,158,255,0.3)] hover:shadow-[0_4px_24px_rgba(59,158,255,0.45)] active:scale-[0.99] transition-all">确认提交</button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>

    <!-- ═══ 电梯导航 (Elevator Nav · 抽屉感应式) ═══ -->
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="navVisible && isScrollable"
        :class="isNavAutoExpanded ? 'translate-x-0' : 'translate-x-[92%] hover:translate-x-0'"
        class="fixed right-0 top-1/2 -translate-y-1/2 z-[100]
               transition-transform duration-300 ease-out
               flex items-stretch group"
      >
        <!-- 细竖边 (始终可见，表示导航存在) -->
        <div class="w-1.5 shrink-0 bg-[#3B9EFF]/20 group-hover:bg-[#3B9EFF]/45
                    rounded-l-md transition-colors duration-300"></div>

        <!-- 展开面板 -->
        <div class="bg-[#1A1E2B]/80 backdrop-blur-md border-y border-l border-[#252A3A]/60
                    rounded-l-lg py-2 px-1.5 space-y-0.5 select-none">
          <div
            v-for="item in currentNavItems" :key="item.id"
            @click.stop="scrollToNav(item.id)"
            class="flex items-center gap-1.5 px-2 py-1.5 rounded cursor-pointer
                   transition-colors duration-150 whitespace-nowrap"
            :class="activeNavId === item.id ? 'bg-[#3B9EFF]/10' : 'hover:bg-[#252A3A]/40'"
          >
            <div class="w-0.5 h-3 rounded-sm shrink-0 transition-colors duration-150"
              :class="activeNavId === item.id ? 'bg-[#3B9EFF]' : 'bg-[#4A5568]'"></div>
            <span class="text-[11px] font-mono transition-colors duration-150"
              :class="activeNavId === item.id ? 'text-white' : 'text-[#64748B]'">{{ item.label }}</span>
          </div>
        </div>
      </div>
    </Transition>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import VChart from 'vue-echarts';
import { use as echartsUse } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, MarkPointComponent, MarkLineComponent } from 'echarts/components';
echartsUse([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, MarkPointComponent, MarkLineComponent]);
import SAASimulator from './SAASimulator.vue';
import { http } from '@/api/request';
import {
  activeRole,
  committeeContextError,
  committeeContextLoading,
  committeeDecisionTable,
  committeePageContext,
  deptAllocationDecision,
  fetchCommitteePageData,
  isCommitteeOfflineMock,
  isGlobalMock,
  skipCommitteeHttp,
  toggleGlobalMock,
  useApi,
  portalSnapshotError,
  portalSnapshotLoading,
  MIXED_ASSET_LIST,
  FICC_ASSET_LIST,
  calcTargetRange,
  COMMITTEE_MEMBERS,
  submitVote,
} from '@/store/demoStore';

function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

const committeeOfflineMock = computed(() => isCommitteeOfflineMock());

const isCommitteeMember = computed(() =>
  ['班子', '部门长', '投资经理', '混合投资委员会委员'].includes(activeRole.value),
);

/** 右上角个人中心切换角色后驱动投委会页面权限 */
const isSecretary = computed(() => activeRole.value === '混合投资委员会秘书');
const isChairman = computed(() => activeRole.value === '混合投资委员会主任委员');

/**
 * 只读状态：当前角色无编辑权限 或 正在查看已归档会议时为 true。
 */
const currentMeetingId = ref<number | null>(null);
const currentMeeting = computed(() => currentMeetingId.value != null ? meetingList.find(m => m.id === currentMeetingId.value) : null);
const isViewingArchived = computed(() => currentMeeting.value?.status === '已归档' || currentMeeting.value?.status === '已结束');
const isReadOnly = computed(() => !isChairman.value || isViewingArchived.value);

function enterMeeting(id: number) {
  currentMeetingId.value = id;
  activeTab.value = 'market_macro';
  decisionSubmitted.value = false;
  isIssued.value = false;
  guidanceCalculated.value = false;
}
function backToList() {
  currentMeetingId.value = null;
}

const SCORE_LABELS: Record<number, string> = { 1: '谨慎', 2: '中性偏谨慎', 3: '中性', 4: '中性偏乐观', 5: '乐观' };
// 中国A股市场颜色惯例：红色=上涨/乐观（正面），绿色=下跌/谨慎（负面），蓝色=中性
const SCORE_COLORS: Record<number, string> = {
  1: 'bg-[#00C9A7]/15 border-[#00C9A7]/40 text-[#00C9A7]',    // 谨慎 — 绿（空头/悲观）
  2: 'bg-[#3B9EFF]/8  border-[#3B9EFF]/25  text-[#3B9EFF]/70', // 中性偏谨慎 — 淡蓝过渡
  3: 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]',    // 中性 — 蓝
  4: 'bg-[#F04864]/8  border-[#F04864]/25  text-[#F04864]/70', // 中性偏乐观 — 淡红过渡
  5: 'bg-[#F04864]/15 border-[#F04864]/40 text-[#F04864]',    // 乐观 — 红（多头/上涨）
};
const SCORE_INACTIVE = 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]';

const ROLE_BADGE_CLASSES: Record<string, string> = {
  '班子': 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]',
  '部门长': 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]',
  '投资经理': 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]',
};

// ── Core state ─────────────────────────────────────────────────
type TabKey = 'market_macro' | 'post_mortem' | 'member_views' | 'allocation' | 'minutes';
const activeTab = ref<TabKey>('market_macro');
const TAB_ITEMS: { key: TabKey; label: string; step: string }[] = [
  { key: 'market_macro', label: '市场及产品表现回顾', step: '01' },
  { key: 'post_mortem', label: '知行果复盘', step: '02' },
  { key: 'member_views', label: '委员观点', step: '03' },
  { key: 'allocation', label: '配置指引', step: '04' },
  { key: 'minutes', label: '会议纪要', step: '05' },
];

function markMaterialsCollected() {
  void 0;
}

// ══════════════════════════════════════════════════════════════
// market_macro — 市场及产品表现回顾 · 数据与状态
// ══════════════════════════════════════════════════════════════

const expandedAssetGroups = ref<Record<string, boolean>>({
  equity: true, bond: true, alternative: true, equity_style: false, equity_fund: false,
});
function toggleAssetGroup(key: string) {
  expandedAssetGroups.value[key] = !expandedAssetGroups.value[key];
}

interface MacroIndicator {
  name: string; value: string; unit: string; trend: string;
  trendDir: 'up' | 'down' | 'flat'; note: string; highlight?: boolean;
}
const MACRO_INDICATORS: MacroIndicator[] = [
  { name: 'DR007', value: '1.82', unit: '%', trend: '下行', trendDir: 'down', note: '资金面宽松，央行呵护明显，处近3年低位', highlight: true },
  { name: 'PMI 制造业', value: '49.7', unit: '', trend: '收缩', trendDir: 'down', note: '连续2月低于荣枯线，内需偏弱', highlight: false },
  { name: 'CPI (YoY)', value: '+0.3', unit: '%', trend: '低通胀', trendDir: 'flat', note: '需求端偏弱，服务价格略升，总体温和', highlight: false },
  { name: 'PPI (YoY)', value: '-2.1', unit: '%', trend: '通缩', trendDir: 'down', note: '工业品价格持续负增长，上游压力延续', highlight: false },
  { name: '汇率 USD/CNY', value: '7.2380', unit: '', trend: '人民币承压', trendDir: 'down', note: '美元指数强势，离岸汇率小幅走弱', highlight: false },
  { name: '10Y 国债', value: '1.79', unit: '%', trend: '历史低位', trendDir: 'down', note: '处近10年约12%分位，股债比价偏向权益', highlight: true },
  { name: '上证波动率', value: '18.2', unit: '', trend: '平稳', trendDir: 'flat', note: '市场情绪中性，无极端风险溢价', highlight: false },
  { name: '北向资金(月)', value: '-62', unit: '亿', trend: '净流出', trendDir: 'down', note: '外资阶段性离场，关注情绪边际变化', highlight: false },
];

interface AssetRow {
  name: string; point: string; pct5y: number; pct10y: number | null;
  retMonth: number; retYtd: number; maxdd: number; sharpe: number; calmar: number;
  trend: number[];
}
interface AssetGroup { key: string; label: string; items: AssetRow[]; }

// ── Sparkline 大图浮层 ────────────────────────────────────────────
const showSparklineModal = ref(false);
const sparklineModalRow = ref<AssetRow | null>(null);
const sparklineModalChartRef = ref<HTMLElement | null>(null);
let sparklineModalChart: echarts.ECharts | null = null;

function openSparklineModal(row: AssetRow) {
  sparklineModalRow.value = row;
  showSparklineModal.value = true;
  nextTick(() => {
    if (!sparklineModalChartRef.value) return;
    sparklineModalChart?.dispose();
    sparklineModalChart = echarts.init(sparklineModalChartRef.value);
    const r = sparklineModalRow.value!;
    const months = ['25/05','25/06','25/07','25/08','25/09','25/10','25/11','25/12','26/01','26/02','26/03','26/04'];
    const color = r.retYtd >= 0 ? '#F04864' : '#00C9A7';
    sparklineModalChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: '#202431', borderColor: '#252A3A', textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 }, formatter: (params: any) => `${params[0].name}<br/><span style="color:${color};font-weight:bold">${params[0].value.toFixed(1)}</span>` },
      grid: { top: 24, right: 20, bottom: 32, left: 48 },
      xAxis: { type: 'category', data: months.slice(0, r.trend.length), axisLine: { lineStyle: { color: '#2E3348' } }, axisTick: { show: false }, axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace' }, splitLine: { show: false } },
      yAxis: { type: 'value', axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v.toFixed(0) }, splitLine: { lineStyle: { color: '#2E3348', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
      series: [{
        type: 'line', data: r.trend, smooth: true, symbol: 'circle', symbolSize: 4,
        lineStyle: { color, width: 2 },
        itemStyle: { color },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: color + '30' }, { offset: 1, color: color + '00' }]) },
      }],
    });
  });
}

function closeSparklineModal() {
  showSparklineModal.value = false;
  sparklineModalChart?.dispose();
  sparklineModalChart = null;
  sparklineModalRow.value = null;
}

const ASSET_VALUATION_GROUPS: AssetGroup[] = [
  {
    key: 'equity', label: '权益',
    items: [
      { name: '纳斯达克',  point: '17,420', pct5y: 62, pct10y: 71, retMonth: 3.2,  retYtd: 8.1,  maxdd: -8.4,  sharpe: 1.02, calmar: 0.89, trend: [100, 103, 99, 104, 107, 105, 108, 106, 110, 109, 112, 108] },
      { name: '标普 500',  point: '5,280',  pct5y: 58, pct10y: 65, retMonth: 2.8,  retYtd: 5.3,  maxdd: -6.2,  sharpe: 0.94, calmar: 0.76, trend: [100, 101, 99, 102, 101, 103, 104, 103, 105, 104, 106, 105] },
      { name: '沪深 300',  point: '3,820',  pct5y: 28, pct10y: 32, retMonth: -0.8, retYtd: 2.1,  maxdd: -14.3, sharpe: 0.31, calmar: 0.18, trend: [100, 98, 96, 97, 99, 98, 100, 99, 101, 100, 102, 102] },
      { name: '恒生科技',  point: '4,190',  pct5y: 18, pct10y: null, retMonth: 5.1, retYtd: 15.4, maxdd: -22.1, sharpe: 0.48, calmar: 0.35, trend: [100, 96, 92, 95, 98, 102, 105, 108, 112, 110, 115, 115] },
      { name: '日经 225',  point: '38,450', pct5y: 72, pct10y: 78, retMonth: -1.2, retYtd: 3.8,  maxdd: -9.7,  sharpe: 0.82, calmar: 0.61, trend: [100, 102, 101, 103, 104, 102, 103, 105, 104, 103, 104, 104] },
    ],
  },
  {
    key: 'bond', label: '债券',
    items: [
      { name: '中债高信用1-3Y', point: '202.4', pct5y: 45, pct10y: 42, retMonth: 0.18, retYtd: 1.12, maxdd: -0.8,  sharpe: 1.85, calmar: 1.32, trend: [100, 100.1, 100.2, 100.1, 100.3, 100.4, 100.3, 100.5, 100.6, 100.5, 100.7, 100.8] },
      { name: '十年国债 ETF',   point: '105.3', pct5y: 15, pct10y: 12, retMonth: 0.32, retYtd: 2.84, maxdd: -3.2,  sharpe: 1.42, calmar: 0.98, trend: [100, 100.4, 100.8, 100.6, 101.0, 100.9, 101.3, 101.6, 101.4, 101.8, 102.2, 102.5] },
      { name: '美元债 LOF',     point: '112.7', pct5y: 38, pct10y: 35, retMonth: 0.84, retYtd: 3.21, maxdd: -5.4,  sharpe: 0.87, calmar: 0.64, trend: [100, 100.6, 101.2, 100.8, 101.5, 101.3, 101.8, 102.2, 101.9, 102.5, 103.0, 102.8] },
    ],
  },
  {
    key: 'alternative', label: '另类与商品',
    items: [
      { name: '南华商品指数', point: '1,823', pct5y: 41, pct10y: 38, retMonth: -1.4, retYtd: -2.8, maxdd: -18.2, sharpe: 0.24, calmar: 0.12, trend: [100, 98, 96, 97, 95, 93, 94, 92, 93, 95, 94, 97] },
      { name: '股票中性指数', point: '1,024', pct5y: 78, pct10y: 72, retMonth: 0.62, retYtd: 3.15, maxdd: -2.8,  sharpe: 2.14, calmar: 1.87, trend: [100, 100.3, 100.6, 100.9, 101.2, 101.0, 101.4, 101.7, 101.5, 101.9, 102.2, 102.6] },
      { name: 'CTA 指数',    point: '1,382', pct5y: 54, pct10y: 48, retMonth: 1.28, retYtd: 4.32, maxdd: -6.1,  sharpe: 1.12, calmar: 0.78, trend: [100, 101, 100.5, 102, 103, 102.5, 103.5, 104, 103.8, 104.5, 105, 104.2] },
      { name: '黄金 ETF 华安', point: '6.84', pct5y: 82, pct10y: 79, retMonth: 2.3,  retYtd: 14.2, maxdd: -8.3,  sharpe: 1.38, calmar: 1.14, trend: [100, 103, 106, 108, 107, 110, 112, 111, 114, 113, 116, 114] },
    ],
  },
  {
    key: 'equity_style', label: '权益风格',
    items: [
      { name: '中证红利全收益', point: '8,420', pct5y: 62, pct10y: 55, retMonth: 1.8,  retYtd: 7.2,  maxdd: -12.4, sharpe: 0.72, calmar: 0.54, trend: [100, 101, 100.5, 102, 103, 102.5, 103.5, 104, 105, 104.5, 106, 107] },
      { name: '中证 REITs 全收益', point: '1,124', pct5y: 25, pct10y: null, retMonth: 0.9, retYtd: 3.4, maxdd: -18.6, sharpe: 0.38, calmar: 0.22, trend: [100, 99, 97, 98, 99, 100, 101, 100, 102, 101, 103, 103] },
      { name: '国证价值 R',    point: '2,840', pct5y: 45, pct10y: 38, retMonth: 1.2,  retYtd: 5.8,  maxdd: -14.2, sharpe: 0.55, calmar: 0.41, trend: [100, 101, 100, 102, 103, 102, 103, 104, 105, 104, 106, 106] },
      { name: '沪深 300',      point: '3,820', pct5y: 28, pct10y: 32, retMonth: -0.8, retYtd: 2.1,  maxdd: -14.3, sharpe: 0.31, calmar: 0.18, trend: [100, 98, 96, 97, 99, 98, 100, 99, 101, 100, 102, 102] },
      { name: '国证成长 R',    point: '2,150', pct5y: 22, pct10y: 18, retMonth: -1.4, retYtd: -3.8, maxdd: -22.8, sharpe: 0.18, calmar: 0.09, trend: [100, 98, 95, 97, 96, 94, 95, 93, 94, 96, 95, 96] },
      { name: '上证指数',      point: '3,295', pct5y: 28, pct10y: 24, retMonth: 0.2,  retYtd: 1.8,  maxdd: -12.8, sharpe: 0.28, calmar: 0.14, trend: [100, 99, 98, 99, 100, 99, 100, 101, 100, 101, 102, 101.8] },
    ],
  },
  {
    key: 'equity_fund', label: '权益基金',
    items: [
      { name: '股票中性',       point: '1.024', pct5y: 76, pct10y: 68, retMonth: 0.58, retYtd: 2.94, maxdd: -2.1,  sharpe: 2.08, calmar: 1.76, trend: [100, 100.2, 100.5, 100.7, 100.9, 101.1, 101.3, 101.5, 101.7, 101.9, 102.2, 102.4] },
      { name: '混合债券型二级', point: '1.182', pct5y: 58, pct10y: 52, retMonth: 0.72, retYtd: 3.82, maxdd: -4.2,  sharpe: 1.42, calmar: 1.02, trend: [100, 100.3, 100.6, 100.9, 101.2, 101.5, 101.8, 102.1, 102.4, 102.7, 103.0, 103.2] },
      { name: '偏债混合型基金', point: '1.248', pct5y: 48, pct10y: 42, retMonth: 0.28, retYtd: 2.14, maxdd: -8.4,  sharpe: 0.92, calmar: 0.68, trend: [100, 100.2, 100.4, 100.3, 100.6, 100.8, 100.7, 101.0, 101.2, 101.1, 101.4, 101.5] },
      { name: '偏股混合型基金', point: '1.384', pct5y: 32, pct10y: 28, retMonth: -0.8, retYtd: 1.42, maxdd: -18.4, sharpe: 0.42, calmar: 0.22, trend: [100, 99, 97, 98, 100, 99, 101, 100, 101, 100, 101.5, 101.4] },
      { name: '可转债基金',     point: '1.127', pct5y: 44, pct10y: 38, retMonth: 0.92, retYtd: 4.82, maxdd: -12.6, sharpe: 0.78, calmar: 0.56, trend: [100, 100.5, 101, 100.8, 101.5, 102, 101.8, 102.3, 102.8, 103.2, 103.8, 104.2] },
    ],
  },
];

interface CommitteeVoteReviewRow {
  asset: string; avgScore: number; scoreLabel: string;
  actualChange: number; changeStr: string; deviationLevel: string; verdict: string;
}
const COMMITTEE_VOTE_REVIEW_ROWS: CommitteeVoteReviewRow[] = [
  { asset: '沪深 300',    avgScore: 3.8, scoreLabel: '偏乐观', actualChange: 2.1,   changeStr: '+2.1%',   deviationLevel: '低',   verdict: '方向正确' },
  { asset: '10Y 国债利率', avgScore: 2.1, scoreLabel: '偏谨慎', actualChange: -0.08, changeStr: '-8 bp',   deviationLevel: '低',   verdict: '方向正确' },
  { asset: '黄金 ETF',    avgScore: 4.2, scoreLabel: '乐观',   actualChange: 14.2,  changeStr: '+14.2%',  deviationLevel: '极低', verdict: '显著超额' },
  { asset: '纳斯达克',    avgScore: 3.0, scoreLabel: '中性',   actualChange: 8.1,   changeStr: '+8.1%',   deviationLevel: '高',   verdict: '方向偏差' },
  { asset: '中证 REITs',  avgScore: 3.4, scoreLabel: '偏乐观', actualChange: 3.4,   changeStr: '+3.4%',   deviationLevel: '低',   verdict: '方向正确' },
  { asset: '南华商品',    avgScore: 2.8, scoreLabel: '偏谨慎', actualChange: -2.8,  changeStr: '-2.8%',   deviationLevel: '极低', verdict: '方向正确' },
  { asset: '可转债基金',  avgScore: 3.6, scoreLabel: '偏乐观', actualChange: 4.82,  changeStr: '+4.82%',  deviationLevel: '低',   verdict: '方向正确' },
];
const COMMITTEE_ACCURACY_SCORE = computed(() => {
  const correct = COMMITTEE_VOTE_REVIEW_ROWS.filter(r => r.verdict !== '方向偏差').length;
  return Math.round(correct / COMMITTEE_VOTE_REVIEW_ROWS.length * 100);
});

interface GuidanceTimelineRow { period: string; guidance: string; actualChange: string; match: boolean; }
interface GuidanceBenchmark { name: string; key: string; rows: GuidanceTimelineRow[]; score: number; }
const GUIDANCE_BENCHMARKS: GuidanceBenchmark[] = [
  {
    name: '万得全 A (权益)',
    key: 'equity',
    score: 71,
    rows: [
      { period: '2025 Q2', guidance: '中性',   actualChange: '+1.8%',  match: true  },
      { period: '2025 Q3', guidance: '乐观',   actualChange: '+7.2%',  match: true  },
      { period: '2025 Q4', guidance: '谨慎',   actualChange: '-3.4%',  match: true  },
      { period: '2026 Q1', guidance: '偏乐观', actualChange: '+2.1%',  match: true  },
      { period: '2026 Q2', guidance: '中性',   actualChange: '-',       match: true  },
    ],
  },
  {
    name: '伦敦金现 (商品)',
    key: 'commodity',
    score: 57,
    rows: [
      { period: '2025 Q2', guidance: '乐观',   actualChange: '+8.4%',  match: true  },
      { period: '2025 Q3', guidance: '乐观',   actualChange: '-2.1%',  match: false },
      { period: '2025 Q4', guidance: '中性',   actualChange: '+11.3%', match: false },
      { period: '2026 Q1', guidance: '乐观',   actualChange: '+14.2%', match: true  },
      { period: '2026 Q2', guidance: '乐观',   actualChange: '-',       match: true  },
    ],
  },
  {
    name: '10Y 国债利率 (债券)',
    key: 'bond',
    score: 86,
    rows: [
      { period: '2025 Q2', guidance: '谨慎',   actualChange: '-12 bp', match: true  },
      { period: '2025 Q3', guidance: '谨慎',   actualChange: '-8 bp',  match: true  },
      { period: '2025 Q4', guidance: '中性',   actualChange: '+3 bp',  match: true  },
      { period: '2026 Q1', guidance: '谨慎',   actualChange: '-6 bp',  match: true  },
      { period: '2026 Q2', guidance: '谨慎',   actualChange: '-',       match: true  },
    ],
  },
];

// ══════════════════════════════════════════════════════════════
// post_mortem — 知行果复盘 · 数据与状态
// ══════════════════════════════════════════════════════════════

// ── Module 1: 指引回顾与执行跟踪 (GAP-3) ──────────────────────
interface ExecTrackRow {
  asset: string; targetCmt: number; targetDept: number; targetProd: number;
  actual: number; deviation: number; limit: number;
  status: 'ok' | 'warn' | 'breach'; feedback: string;
}
const execTrackRows = ref<ExecTrackRow[]>([
  { asset: '权益',     targetCmt: 25, targetDept: 23, targetProd: 22, actual: 24.3, deviation:  2.3, limit: 3, status: 'ok',     feedback: '' },
  { asset: '固收',     targetCmt: 45, targetDept: 47, targetProd: 48, actual: 46.8, deviation: -1.2, limit: 3, status: 'ok',     feedback: '' },
  { asset: '另类与商品', targetCmt: 15, targetDept: 14, targetProd: 13, actual: 11.2, deviation: -1.8, limit: 2, status: 'warn',   feedback: '' },
  { asset: '现金及等价物', targetCmt: 15, targetDept: 16, targetProd: 17, actual: 17.7, deviation:  0.7, limit: 3, status: 'ok',   feedback: '' },
  { asset: '境外权益',  targetCmt: 0,  targetDept: 0,  targetProd: 0,  actual: 4.1,  deviation:  4.1, limit: 3, status: 'breach', feedback: '' },
]);
function execDeviationClass(row: ExecTrackRow) {
  if (row.status === 'breach') return 'text-[#F04864] font-bold';
  if (row.status === 'warn')   return 'text-[#FFAB00] font-bold';
  return 'text-[#94A3B8]';
}

// ── Module 2: 产品序列表现与仓位分析 ──────────────────────────
interface ProductPerfRow {
  name: string; ytdGross: number; y1Gross: number;
  ytdRank: string; ytdRankPct: number; y1Rank: string; y1RankPct: number;
}
const PRODUCT_PERF_ROWS: ProductPerfRow[] = [
  { name: '偏股混合型',   ytdGross:  8.21, y1Gross: 12.43, ytdRank: '18/156', ytdRankPct: 12, y1Rank: '24/148', y1RankPct: 16 },
  { name: '偏债混合型',   ytdGross:  4.12, y1Gross:  6.84, ytdRank: '12/89',  ytdRankPct: 14, y1Rank: '8/84',   y1RankPct: 10 },
  { name: '混合债券二级', ytdGross:  3.84, y1Gross:  5.91, ytdRank: '22/134', ytdRankPct: 16, y1Rank: '31/128', y1RankPct: 24 },
  { name: '可转债基金',   ytdGross:  6.22, y1Gross:  9.14, ytdRank: '8/72',   ytdRankPct: 11, y1Rank: '11/69',  y1RankPct: 16 },
  { name: '纯债/短债',    ytdGross:  2.84, y1Gross:  4.21, ytdRank: '31/203', ytdRankPct: 15, y1Rank: '44/198', y1RankPct: 22 },
];
const PM_MONTHS = ['25/05','25/06','25/07','25/08','25/09','25/10','25/11','25/12','26/01','26/02','26/03','26/04'];
const DURATION_TRENDS: Record<string, number[]> = {
  '偏债混合':   [2.1,2.2,2.0,1.9,2.3,2.5,2.8,3.1,3.2,3.0,2.9,2.7],
  '混合债券二级': [1.8,1.9,1.7,1.6,2.0,2.2,2.4,2.7,2.9,2.8,2.6,2.4],
  '纯债/短债':  [3.2,3.1,3.3,3.4,3.6,3.8,4.0,4.2,4.1,4.0,3.9,3.8],
};
const EQUITY_POS_TRENDS: Record<string, number[]> = {
  '偏股混合': [72,75,78,71,68,74,80,82,79,76,78,81],
  '偏债混合': [18,20,22,19,17,21,25,28,26,24,22,20],
  '可转债':  [45,48,52,50,44,47,55,60,58,54,51,53],
};
const durationChartOption = computed(() => ({
  backgroundColor: 'transparent',
  grid: { top: 24, right: 8, bottom: 28, left: 38, containLabel: false },
  tooltip: { trigger: 'axis', backgroundColor: '#202431', borderColor: '#252A3A', textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 } },
  legend: { top: 2, right: 8, textStyle: { color: '#94A3B8', fontSize: 10, fontFamily: 'monospace' }, itemWidth: 14, itemHeight: 2 },
  xAxis: { type: 'category', data: PM_MONTHS, axisLine: { lineStyle: { color: '#252A3A' } }, axisTick: { show: false }, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' }, splitLine: { show: false } },
  yAxis: { type: 'value', min: 1, max: 5, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v.toFixed(1) }, splitLine: { lineStyle: { color: '#252A3A', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
  series: Object.entries(DURATION_TRENDS).map(([name, data], i) => ({
    name, type: 'line', data, smooth: true, symbol: 'none',
    lineStyle: { width: 2, color: ['#3B9EFF','#FFAB00','#00C9A7'][i] },
    itemStyle: { color: ['#3B9EFF','#FFAB00','#00C9A7'][i] },
  })),
}));
const equityPosChartOption = computed(() => ({
  backgroundColor: 'transparent',
  grid: { top: 24, right: 8, bottom: 28, left: 38, containLabel: false },
  tooltip: { trigger: 'axis', backgroundColor: '#202431', borderColor: '#252A3A', textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 } },
  legend: { top: 2, right: 8, textStyle: { color: '#94A3B8', fontSize: 10, fontFamily: 'monospace' }, itemWidth: 14, itemHeight: 2 },
  xAxis: { type: 'category', data: PM_MONTHS, axisLine: { lineStyle: { color: '#252A3A' } }, axisTick: { show: false }, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' }, splitLine: { show: false } },
  yAxis: { type: 'value', min: 0, max: 100, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v + '%' }, splitLine: { lineStyle: { color: '#252A3A', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
  series: Object.entries(EQUITY_POS_TRENDS).map(([name, data], i) => ({
    name, type: 'line', data, smooth: true, symbol: 'none',
    lineStyle: { width: 2, color: ['#F04864','#3B9EFF','#FFAB00'][i] },
    itemStyle: { color: ['#F04864','#3B9EFF','#FFAB00'][i] },
    areaStyle: { color: ['#F04864','#3B9EFF','#FFAB00'][i], opacity: 0.06 },
  })),
}));

// ── 双轴图：久期（左轴） + 权益仓位（右轴） ──────────────────────
import * as echarts from 'echarts';
const positionChartRef = ref<HTMLElement | null>(null);
const guidanceChartRef = ref<HTMLElement | null>(null);
let positionChart: echarts.ECharts | null = null;
let guidanceChart: echarts.ECharts | null = null;

const POSITION_DUAL_MONTHS = ['25/05','25/06','25/07','25/08','25/09','25/10','25/11','25/12','26/01','26/02','26/03','26/04'];
const DURATION_AVG = [2.4, 2.3, 2.1, 2.0, 2.2, 2.5, 2.8, 3.0, 2.9, 2.7, 2.6, 2.5];
const EQUITY_POS = [18, 20, 22, 19, 17, 21, 25, 28, 26, 24, 22, 20];

function initPositionChart() {
  if (!positionChartRef.value) return;
  positionChart?.dispose();
  positionChart = echarts.init(positionChartRef.value);
  positionChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#202431', borderColor: '#252A3A', textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 } },
    legend: { top: 0, right: 8, textStyle: { color: '#94A3B8', fontSize: 11, fontFamily: 'monospace' }, itemWidth: 14, itemHeight: 2 },
    grid: { top: 36, right: 56, bottom: 28, left: 44 },
    xAxis: { type: 'category', data: POSITION_DUAL_MONTHS, axisLine: { lineStyle: { color: '#252A3A' } }, axisTick: { show: false }, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' }, splitLine: { show: false } },
    yAxis: [
      { type: 'value', name: '久期(年)', nameTextStyle: { color: '#94A3B8', fontSize: 10, fontFamily: 'monospace' }, min: 1.0, max: 3.5, interval: 0.5, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v.toFixed(1) }, splitLine: { lineStyle: { color: '#2E3348', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
      { type: 'value', name: '仓位(%)', nameTextStyle: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' }, min: 0, max: 35, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v + '%' }, splitLine: { show: false }, axisLine: { show: false }, axisTick: { show: false } },
    ],
    series: [
      { name: '久期中枢', type: 'bar', data: DURATION_AVG, barWidth: '40%', itemStyle: { color: 'rgba(59,158,255,0.35)', borderRadius: [2, 2, 0, 0] }, yAxisIndex: 0 },
      { name: '权益仓位', type: 'line', data: EQUITY_POS, smooth: true, symbol: 'circle', symbolSize: 5, yAxisIndex: 1, lineStyle: { color: '#F04864', width: 2 }, itemStyle: { color: '#F04864' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(240,72,100,0.18)' }, { offset: 1, color: 'rgba(240,72,100,0)' }]) } },
    ],
  });
}

// ── 行情+信号图：万得全A走势与投委会指引标记 ──────────────────────
const WINDA_MONTHS = ['25/05','25/06','25/07','25/08','25/09','25/10','25/11','25/12','26/01','26/02','26/03','26/04'];
const WINDA_VALUES = [4380, 4420, 4350, 4410, 4280, 4360, 4450, 4520, 4510, 4480, 4560, 4580];

interface GuidanceSignal { monthIdx: number; direction: 'bullish' | 'bearish' | 'neutral'; label: string; }
const GUIDANCE_SIGNALS: GuidanceSignal[] = [
  { monthIdx: 1, direction: 'bullish', label: '乐观/加仓' },
  { monthIdx: 3, direction: 'bearish', label: '谨慎/减仓' },
  { monthIdx: 5, direction: 'bullish', label: '偏乐观' },
  { monthIdx: 7, direction: 'bullish', label: '乐观/加仓' },
  { monthIdx: 9, direction: 'neutral', label: '中性' },
];

function initGuidanceChart() {
  if (!guidanceChartRef.value) return;
  guidanceChart?.dispose();
  guidanceChart = echarts.init(guidanceChartRef.value);
  const markPointData = GUIDANCE_SIGNALS.map(s => ({
    coord: [WINDA_MONTHS[s.monthIdx], WINDA_VALUES[s.monthIdx]],
    symbol: s.direction === 'bullish' ? 'arrow' : s.direction === 'bearish' ? 'arrow' : 'diamond',
    symbolSize: 14,
    symbolRotate: s.direction === 'bullish' ? 180 : s.direction === 'bearish' ? 0 : 0,
    itemStyle: { color: s.direction === 'bullish' ? '#F04864' : s.direction === 'bearish' ? '#00C9A7' : '#3B9EFF' },
    label: { show: true, formatter: s.label, position: s.direction === 'bullish' ? 'bottom' : 'top', color: s.direction === 'bullish' ? '#F04864' : s.direction === 'bearish' ? '#00C9A7' : '#3B9EFF', fontSize: 10, fontFamily: 'monospace' },
  }));
  guidanceChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#202431', borderColor: '#252A3A', textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 } },
    grid: { top: 28, right: 16, bottom: 28, left: 52 },
    xAxis: { type: 'category', data: WINDA_MONTHS, axisLine: { lineStyle: { color: '#252A3A' } }, axisTick: { show: false }, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' }, splitLine: { show: false } },
    yAxis: { type: 'value', min: 4200, max: 4700, axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' }, splitLine: { lineStyle: { color: '#2E3348', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'line', data: WINDA_VALUES, smooth: true, symbol: 'none', lineStyle: { color: '#4A5568', width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(74,85,104,0.15)' }, { offset: 1, color: 'rgba(74,85,104,0)' }]) },
      markPoint: { data: markPointData, animation: true },
    }],
  });
}

function handleResize() {
  positionChart?.resize();
  guidanceChart?.resize();
}

// ── 电梯导航 (Elevator Nav) ──────────────────────────────────────
const mainScrollRef = ref<HTMLElement | null>(null);
const activeNavId = ref('');
const isScrollable = ref(true);
const isNavAutoExpanded = ref(false);
let navAutoCollapseTimer: number | null = null;

interface NavItem { id: string; label: string; }

// NAV_MAP — key 须与模板中对应 id="nav-*" 一一对应
const NAV_MAP: Record<string, NavItem[]> = {
  market_macro: [
    { id: 'nav-macro-env',     label: '宏观环境' },
    { id: 'nav-asset-val',     label: '估值水位' },
    { id: 'nav-vote-review',   label: '投票回顾' },
    { id: 'nav-guidance-val',  label: '指引复盘' },
  ],
  post_mortem: [
    { id: 'nav-exec-track',    label: '行检验' },
    { id: 'nav-product-perf',  label: '产品仓位' },
    { id: 'nav-return-decomp', label: 'Brinson归因' },
    { id: 'nav-spv-eval',      label: '策略评价' },
  ],
  // 委员会观点统计子视图 (committee_stats)
  member_views_stats: [
    { id: 'nav-model-anchors',   label: '量化锚点' },
    { id: 'nav-vote-matrix',     label: '投票矩阵' },
    { id: 'nav-vote-consensus',  label: '档位结论' },
  ],
  // 我的观点填报子视图 (my_fill)
  member_views_fill: [
    { id: 'nav-pre-summary', label: '观点汇总' },
  ],
  allocation: [
    { id: 'nav-alloc-ref',       label: '决策参考' },   // 三栏参考看板父容器
    { id: 'nav-chair-decision',  label: '主任定调' },
    { id: 'nav-product-guide',   label: '产品指引' },
  ],
  minutes: [
    { id: 'nav-recording',   label: '录音状态' },
    { id: 'nav-ai-minutes',  label: 'AI纪要' },
  ],
};

// 根据 Tab 及子 Tab 动态返回导航项
const currentNavItems = computed((): NavItem[] => {
  if (activeTab.value === 'member_views') {
    return memberViewsSubTab.value === 'committee_stats'
      ? (NAV_MAP['member_views_stats'] ?? [])
      : (NAV_MAP['member_views_fill'] ?? []);
  }
  return NAV_MAP[activeTab.value] ?? [];
});

const navVisible = computed(() => currentNavItems.value.length >= 2);

function checkScrollable() {
  // 优先使用锚点跨度判断（最贴近电梯导航真实需求）
  const anchorEls = currentNavItems.value
    .map(item => document.getElementById(item.id))
    .filter((el): el is HTMLElement => !!el);
  if (anchorEls.length >= 2) {
    const firstTop = anchorEls[0].getBoundingClientRect().top;
    const lastBottom = anchorEls[anchorEls.length - 1].getBoundingClientRect().bottom;
    const anchorSpan = lastBottom - firstTop;
    if (anchorSpan > window.innerHeight * 0.9) {
      isScrollable.value = true;
      return;
    }
  }

  if (!mainScrollRef.value) {
    const doc = document.documentElement;
    const body = document.body;
    const pageScrollHeight = Math.max(doc?.scrollHeight ?? 0, body?.scrollHeight ?? 0);
    const pageClientHeight = window.innerHeight;
    isScrollable.value = pageScrollHeight > pageClientHeight + 16;
    return;
  }
  const el = mainScrollRef.value;
  const mainScrollable = el.scrollHeight > el.clientHeight + 16;
  if (mainScrollable) {
    isScrollable.value = true;
  } else {
    const doc = document.documentElement;
    const body = document.body;
    const pageScrollHeight = Math.max(doc?.scrollHeight ?? 0, body?.scrollHeight ?? 0);
    const pageClientHeight = window.innerHeight;
    isScrollable.value = pageScrollHeight > pageClientHeight + 16;
  }
}

function scrollToNav(id: string) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function onMainScroll() {
  isNavAutoExpanded.value = true;
  if (navAutoCollapseTimer !== null) window.clearTimeout(navAutoCollapseTimer);
  navAutoCollapseTimer = window.setTimeout(() => {
    isNavAutoExpanded.value = false;
  }, 900);
  checkScrollable();

  // 用 viewport 坐标判断最近锚点（与哪个容器滚动无关）
  const viewCenter = window.innerHeight / 3;
  let closest: NavItem | null = null;
  let closestDist = Infinity;
  for (const item of currentNavItems.value) {
    const el = document.getElementById(item.id);
    if (!el) continue;
    const rect = el.getBoundingClientRect();
    const dist = Math.abs(rect.top - viewCenter);
    if (dist < closestDist) {
      closestDist = dist;
      closest = item;
    }
  }
  if (closest && activeNavId.value !== closest.id) {
    activeNavId.value = closest.id;
  }
}

function onWindowScroll() {
  onMainScroll();
}

function onMainScrollEnd() {
  isNavAutoExpanded.value = false;
}

function onScrollIntent() {
  // 某些容器滚动不会触发当前绑定的 scroll 目标，这里用滚动意图兜底
  onMainScroll();
}

function onKeyScrollIntent(e: KeyboardEvent) {
  if (['PageDown', 'PageUp', 'ArrowDown', 'ArrowUp', 'Space', 'Home', 'End'].includes(e.code)) {
    onMainScroll();
  }
}

// Tab 切换时重置高亮
watch(activeTab, async () => {
  activeNavId.value = '';
  isNavAutoExpanded.value = false;
  await nextTick();
  checkScrollable();
});

watch(currentMeetingId, async () => {
  isNavAutoExpanded.value = false;
  await nextTick();
  checkScrollable();
});

// memberViewsSubTab 的 watch 在声明之后补注册（见 memberViewsSubTab 声明处）

// ── Module 3: 收益来源与 Brinson 分析 (GAP-6) ─────────────────
interface ReturnDecompRow {
  product: string; ytdAnn: number;
  beta: number; alpha: number; lev: number; timing: number; selection: number;
}
const RETURN_DECOMP_ROWS: ReturnDecompRow[] = [
  { product: '偏股混合型',   ytdAnn:  8.21, beta:  4.8, alpha: 2.1, lev: 0.4, timing:  85, selection: 92 },
  { product: '偏债混合型',   ytdAnn:  4.12, beta:  2.1, alpha: 1.6, lev: 0.2, timing:  42, selection: 68 },
  { product: '混合债券二级', ytdAnn:  3.84, beta:  2.4, alpha: 1.1, lev: 0.1, timing:  38, selection: 55 },
  { product: '可转债基金',   ytdAnn:  6.22, beta:  3.2, alpha: 2.4, lev: 0.3, timing:  64, selection: 78 },
  { product: '纯债/短债',    ytdAnn:  2.84, beta:  2.6, alpha: 0.3, lev: 0.0, timing: -12, selection: 32 },
];
const brinsonSelectedIdx = ref(0);
const BRINSON_DATA_ALL: Array<Array<{ label: string; value: number; cumBase: number }>> = [
  [ // 偏股混合
    { label: '基准收益',     value: 312, cumBase: 0   },
    { label: '大类资产配置', value:  84, cumBase: 312 },
    { label: '行业择时',     value: -28, cumBase: 396 },
    { label: '个券择选',     value:  95, cumBase: 368 },
    { label: '交互效应',     value:  12, cumBase: 463 },
    { label: '组合总收益',   value: 475, cumBase: 0   },
  ],
  [ // 偏债混合
    { label: '基准收益',     value: 210, cumBase: 0   },
    { label: '大类资产配置', value:  42, cumBase: 210 },
    { label: '行业择时',     value:  18, cumBase: 252 },
    { label: '个券择选',     value:  52, cumBase: 270 },
    { label: '交互效应',     value: -10, cumBase: 322 },
    { label: '组合总收益',   value: 312, cumBase: 0   },
  ],
  [ // 混合债券二级
    { label: '基准收益',     value: 240, cumBase: 0   },
    { label: '大类资产配置', value:  28, cumBase: 240 },
    { label: '行业择时',     value: -14, cumBase: 268 },
    { label: '个券择选',     value:  42, cumBase: 254 },
    { label: '交互效应',     value:   8, cumBase: 296 },
    { label: '组合总收益',   value: 304, cumBase: 0   },
  ],
  [ // 可转债基金
    { label: '基准收益',     value: 268, cumBase: 0   },
    { label: '大类资产配置', value:  78, cumBase: 268 },
    { label: '行业择时',     value:  22, cumBase: 346 },
    { label: '个券择选',     value:  82, cumBase: 368 },
    { label: '交互效应',     value:   4, cumBase: 450 },
    { label: '组合总收益',   value: 454, cumBase: 0   },
  ],
  [ // 纯债/短债
    { label: '基准收益',     value: 268, cumBase: 0   },
    { label: '大类资产配置', value:  18, cumBase: 268 },
    { label: '行业择时',     value: -26, cumBase: 286 },
    { label: '个券择选',     value:  24, cumBase: 260 },
    { label: '交互效应',     value:   0, cumBase: 284 },
    { label: '组合总收益',   value: 284, cumBase: 0   },
  ],
];
const brinsonData = computed(() => BRINSON_DATA_ALL[brinsonSelectedIdx.value] ?? BRINSON_DATA_ALL[0]);
const brinsonMax = computed(() => Math.max(...brinsonData.value.map(d => d.cumBase + Math.max(0, d.value))));
const brinsonChartOption = computed(() => {
  const items = brinsonData.value;
  const labels = items.map(d => d.label);
  const isTotal = items.map(d => d.label === '基准收益' || d.label === '组合总收益');
  const bases   = items.map((d, i) => isTotal[i] ? 0 : d.cumBase);
  const values  = items.map(d => d.value);
  const colors  = items.map((d, i) => isTotal[i] ? '#3B9EFF' : d.value >= 0 ? '#F04864' : '#00C9A7');
  return {
    backgroundColor: 'transparent',
    grid: { top: 12, right: 12, bottom: 32, left: 50 },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'none' },
      backgroundColor: '#202431', borderColor: '#252A3A',
      textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 },
      formatter: (params: { dataIndex: number }[]) => {
        const i = params[0].dataIndex;
        return `${labels[i]}: ${values[i] > 0 ? '+' : ''}${values[i]} bp`;
      },
    },
    xAxis: { type: 'category', data: labels, axisLabel: { color: '#94A3B8', fontSize: 10, fontFamily: 'monospace', interval: 0 }, axisLine: { lineStyle: { color: '#252A3A' } }, axisTick: { show: false }, splitLine: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v + 'bp' }, splitLine: { lineStyle: { color: '#252A3A', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
    series: [
      { type: 'bar', stack: 'wf', data: bases, itemStyle: { color: 'transparent' }, silent: true },
      { type: 'bar', stack: 'wf', data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [2,2,0,0] } })), barMaxWidth: 40, label: { show: true, position: values.map(v => v >= 0 ? 'top' : 'bottom'), formatter: (p: { value: number }) => (p.value > 0 ? '+' : '') + p.value, color: '#E8ECF4', fontSize: 10, fontFamily: 'monospace' } },
    ],
  };
});

// ── Module 4: 策略库建设与 SPV 评价 ────────────────────────────
interface SpvRow {
  label: string; ytdAbs: number; outpct: number;
  avgScale: number; excessDownVol: number; poolContrib: number;
}
const SPV_ROWS: SpvRow[] = [
  { label: '量化多头',   ytdAbs:  8.4, outpct:  3.2, avgScale: 12400, excessDownVol: 2.84, poolContrib:  396.8 },
  { label: 'CTA 趋势',  ytdAbs:  5.1, outpct:  2.8, avgScale:  8200, excessDownVol: 1.92, poolContrib:  229.6 },
  { label: '套利策略',  ytdAbs:  2.3, outpct:  1.1, avgScale:  6800, excessDownVol: 3.21, poolContrib:   74.8 },
  { label: '可转债多策略', ytdAbs: 6.2, outpct:  0.9, avgScale: 11200, excessDownVol: 1.54, poolContrib:  100.8 },
  { label: '纯债久期',  ytdAbs:  2.8, outpct: -0.3, avgScale: 18400, excessDownVol: 4.12, poolContrib:  -55.2 },
  { label: '红利价值',  ytdAbs:  4.8, outpct: -0.8, avgScale:  9600, excessDownVol: 1.18, poolContrib:  -76.8 },
  { label: '行业主题',  ytdAbs: -1.2, outpct: -4.2, avgScale:  7200, excessDownVol: 0.41, poolContrib: -302.4 },
  { label: '中小盘成长', ytdAbs: -2.8, outpct: -5.8, avgScale:  4800, excessDownVol: 0.28, poolContrib: -278.4 },
];
const TOTAL_SCALE = SPV_ROWS.reduce((s, r) => s + r.avgScale, 0);
const SPV_STATS = computed(() => {
  const sorted = [...SPV_ROWS].sort((a, b) => b.excessDownVol - a.excessDownVol);
  const top30 = sorted.slice(0, Math.ceil(sorted.length * 0.3));
  const top50 = sorted.slice(0, Math.ceil(sorted.length * 0.5));
  const pos   = SPV_ROWS.filter(r => r.outpct > 0);
  const sumScale = (rows: SpvRow[]) => rows.reduce((s, r) => s + r.avgScale, 0);
  return {
    posCount:    pos.length,
    posScale:    (sumScale(pos) / 10000).toFixed(2),
    posPct:      ((sumScale(pos) / TOTAL_SCALE) * 100).toFixed(1),
    top30Scale:  (sumScale(top30) / 10000).toFixed(2),
    top30Pct:    ((sumScale(top30) / TOTAL_SCALE) * 100).toFixed(1),
    top50Scale:  (sumScale(top50) / 10000).toFixed(2),
    top50Pct:    ((sumScale(top50) / TOTAL_SCALE) * 100).toFixed(1),
  };
});
function spvRowClass(row: SpvRow) {
  if (row.outpct >= 1.5)  return 'bg-[#F04864]/8 border-l-2 border-l-[#F04864]';
  if (row.outpct <= -2.0) return 'bg-[#00C9A7]/8 border-l-2 border-l-[#00C9A7]';
  return '';
}

function handleQuickCreateAndEnter() {
  quickCreateMeeting();
  if (meetingList.length > 0) {
    enterMeeting(meetingList[0].id);
  }
}

// ── Step 0: Questionnaire config ───────────────────────────────
interface QSection { id: string; title: string; type: string; items: string[]; options: string[]; }

/** 投票资产列表 — 数据源：MIXED_ASSET_LIST（demoStore 统一观点字典） */
const ASSET_LIST = MIXED_ASSET_LIST.map(i => i.细分策略);
/** 快速查找 MIXED_ASSET_LIST 配置项 */
const VOTE_CONFIG_MAP = new Map(MIXED_ASSET_LIST.map(i => [i.细分策略, i]));

/** 评分档位按大类分组（固收 / 含权 / 另类），驱动 Tab 1 树状填报 */
const MIXED_ASSET_GROUPS = computed(() => {
  const orderMap = new Map<string, typeof MIXED_ASSET_LIST[number][]>();
  const order: string[] = [];
  for (const item of MIXED_ASSET_LIST) {
    if (!orderMap.has(item.大类)) { order.push(item.大类); orderMap.set(item.大类, []); }
    orderMap.get(item.大类)!.push(item);
  }
  return order.map(大类 => ({ 大类, items: orderMap.get(大类)! }));
});

/** 按钮内短标签（适配 2 行按钮布局） */
const SCORE_LABELS_SHORT: Record<number, string> = { 1: '谨慎', 2: '偏谨慎', 3: '中性', 4: '偏乐观', 5: '乐观' };

/** 大类标题配色 */
const MIXED_GROUP_HEADER_STYLE: Record<string, string> = {
  '固收': 'border-[#3B9EFF]/30 bg-[#3B9EFF]/8',
  '含权': 'border-[#3B9EFF]/30 bg-[#3B9EFF]/8',
  '另类': 'border-[#3B9EFF]/30 bg-[#3B9EFF]/8',
};
const MIXED_GROUP_TEXT_COLOR: Record<string, string> = {
  '固收': 'text-[#3B9EFF]',
  '含权': 'text-[#3B9EFF]',
  '另类': 'text-[#3B9EFF]',
};

const QUESTIONNAIRE_CONFIG: { sections: QSection[] } = {
  sections: [
    { id: 'A', title: '资产评分 (1-5档)', type: 'score', items: [...ASSET_LIST], options: ['1', '2', '3', '4', '5'] },
    { id: 'B', title: '新高预判', type: 'boolean', items: [...ASSET_LIST], options: [] },
    { id: 'C', title: '重点资产', type: 'multi-select', items: ['利率债', '信用债', '可转债', '港股', 'A股大盘', '黄金', 'REITs'], options: [] },
    { id: 'D', title: '核心观点', type: 'textarea', items: ['论据'], options: [] },
  ],
};

interface QuestionAsset {
  id: number;
  name: string;
  type: string;
  enabled: boolean;
}
let qaIdCounter = 7;
const questionAssetList = reactive<QuestionAsset[]>([
  { id: 1, name: '债券', type: '1-5 评分 + 新高预判', enabled: true },
  { id: 2, name: '权益-红利', type: '1-5 评分 + 新高预判', enabled: true },
  { id: 3, name: '权益-成长', type: '1-5 评分 + 新高预判', enabled: true },
  { id: 4, name: '权益-价值', type: '1-5 评分 + 新高预判', enabled: true },
  { id: 5, name: '黄金', type: '1-5 评分 + 新高预判', enabled: true },
  { id: 6, name: '原油', type: '1-5 评分 + 新高预判', enabled: true },
]);

function addQuestionAsset() {
  questionAssetList.push({ id: qaIdCounter++, name: `新资产 #${qaIdCounter - 1}`, type: '1-5 评分', enabled: true });
}

function editQuestionAsset(id: number) {
  const item = questionAssetList.find(q => q.id === id);
  if (item) item.name = item.name + ' (已编辑)';
}

function deleteQuestionAsset(id: number) {
  const idx = questionAssetList.findIndex(q => q.id === id);
  if (idx !== -1) questionAssetList.splice(idx, 1);
}

const FORM_SECTION_A = reactive<Record<string, number>>(Object.fromEntries(MIXED_ASSET_LIST.map(i => [i.细分策略, 3])));
const FORM_SECTION_B = reactive<Record<string, boolean>>(Object.fromEntries(MIXED_ASSET_LIST.map(i => [i.细分策略, false])));
const FORM_SECTION_C = reactive<Record<string, boolean>>({ '利率债': false, '信用债': false, '可转债': false, '港股': false, 'A股大盘': false, '黄金': false, 'REITs': false });
const formCoreView = ref('');
const formRiskFlag = ref(false);

interface MemberSubmission { sectionA: Record<string, number>; sectionB: Record<string, boolean>; sectionC: Record<string, boolean>; coreView: string; riskFlag: boolean; submittedAt: string; }

const MEMBERS_DATA = [
  { id: 'm0', name: '曾XX', role: '主任委员' },
  { id: 'm1', name: '陈XX', role: '班子' },
  { id: 'm2', name: '张XX', role: '部门长' },
  { id: 'm3', name: '李XX', role: '投资经理' },
  { id: 'm4', name: '王XX', role: '部门长' },
  { id: 'm5', name: '赵XX', role: '投资经理' },
  { id: 'm6', name: '刘XX', role: '风控合规总监' },
];

const memberSubmissions = reactive<Record<string, MemberSubmission>>({});

/**
 * 从后端加载混合投委会问卷提交记录，填充成员提交状态（含评分明细）。
 * GET /v1/committee/mixed/sessions?session_code=2026Q2
 */
const MOCK_SUBMISSIONS_RAW = [
  { submitter_id: 1, submitted_at: '14:12', questionnaire_json: { section_a: { '红利': 3, '偏股混': 3, '恒生科技': 3, '黄金': 4, '利率(10Y)': 4, '利率(30Y)': 4 }, section_b: { '红利': false, '偏股混': false, '恒生科技': false, '黄金': true, '利率(10Y)': true, '利率(30Y)': false }, section_c: [], core_view: '利率中枢大概率继续下移，长久期债券仍具配置价值。权益方面关注红利策略的防御属性，成长板块需等待政策催化。黄金在避险需求下维持超配。', risk_flag: false } },
  { submitter_id: 2, submitted_at: '14:25', questionnaire_json: { section_a: { '红利': 4, '偏股混': 2, '恒生科技': 4, '黄金': 3, '利率(10Y)': 3, '利率(30Y)': 3 }, section_b: { '红利': true, '偏股混': false, '恒生科技': true, '黄金': false, '利率(10Y)': false, '利率(30Y)': false }, section_c: [], core_view: '信用利差持续收窄，高等级信用债性价比下降。权益方面看好价值风格回归，红利策略确定性较高。恒生科技估值低位具吸引力。', risk_flag: false } },
  { submitter_id: 3, submitted_at: '14:31', questionnaire_json: { section_a: { '红利': 2, '偏股混': 2, '恒生科技': 3, '黄金': 5, '利率(10Y)': 5, '利率(30Y)': 5 }, section_b: { '红利': false, '偏股混': false, '恒生科技': false, '黄金': true, '利率(10Y)': true, '利率(30Y)': true }, section_c: [], core_view: '全球衰退风险上升，强烈看好长久期利率债和黄金的避险价值。权益应保持低配，成长板块估值仍偏高。', risk_flag: true } },
  { submitter_id: 4, submitted_at: '14:38', questionnaire_json: { section_a: { '红利': 4, '偏股混': 4, '恒生科技': 3, '黄金': 3, '利率(10Y)': 3, '利率(30Y)': 2 }, section_b: { '红利': true, '偏股混': true, '恒生科技': false, '黄金': false, '利率(10Y)': false, '利率(30Y)': false }, section_c: [], core_view: '科技板块盈利预期上修，成长股配置价值凸显。固收维持中性久期，适度下沉信用获取票息。黄金配置中性。', risk_flag: false } },
  { submitter_id: 5, submitted_at: '14:45', questionnaire_json: { section_a: { '红利': 3, '偏股混': 3, '恒生科技': 4, '黄金': 4, '利率(10Y)': 4, '利率(30Y)': 4 }, section_b: { '红利': false, '偏股混': false, '恒生科技': true, '黄金': true, '利率(10Y)': false, '利率(30Y)': false }, section_c: [], core_view: '跨资产配置以防御为主，利率债和黄金是核心底仓。权益内部偏向价值蓝筹，恒生科技具边际改善逻辑。', risk_flag: false } },
  { submitter_id: 6, submitted_at: '14:52', questionnaire_json: { section_a: { '红利': 3, '偏股混': 2, '恒生科技': 3, '黄金': 4, '利率(10Y)': 3, '利率(30Y)': 3 }, section_b: { '红利': false, '偏股混': false, '恒生科技': false, '黄金': false, '利率(10Y)': false, '利率(30Y)': false }, section_c: [], core_view: '风控视角：当前组合久期风险可控，信用风险需关注城投尾部。权益集中度偏高建议分散化。黄金对冲组合尾部风险效果显著。', risk_flag: false } },
];

async function loadMixedSubmissions() {
  const data = await useApi(
    () => http.get('/v1/committee/mixed/sessions'),
    { submissions: MOCK_SUBMISSIONS_RAW },
  );
  for (const sub of data.submissions ?? []) {
    const mid = `m${sub.submitter_id}`;
    const qj = sub.questionnaire_json ?? {};
    const sectionA = qj.section_a ?? {};
    const sectionB = qj.section_b ?? {};
    const sectionC: Record<string, boolean> = {};
    for (const key of (qj.section_c ?? [])) {
      sectionC[key] = true;
    }
    memberSubmissions[mid] = {
      sectionA: { ...sectionA },
      sectionB: { ...sectionB },
      sectionC,
      coreView: qj.core_view ?? '',
      riskFlag: qj.risk_flag ?? false,
      submittedAt: sub.submitted_at
        ? new Date(sub.submitted_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        : '-',
    };
  }
}

const activeMemberId = ref<string | null>(null);
const activeMember = computed(() => MEMBERS_DATA.find(m => m.id === activeMemberId.value));

// ── 秘书 RPA 代填工作台 ─────────────────────────────────────────────────────
const secretaryView = ref<'progress' | 'proxy'>('progress');
const memberViewsSubTab = ref<'my_fill' | 'committee_stats'>('committee_stats');
watch(memberViewsSubTab, async () => {
  activeNavId.value = '';
  isNavAutoExpanded.value = false;
  await nextTick();
  checkScrollable();
});

watch(currentNavItems, async () => {
  isNavAutoExpanded.value = false;
  await nextTick();
  checkScrollable();
});

const proxyTargetId = ref('');
const proxyFormA = reactive<Record<string, number>>({});
const proxyFormB = reactive<Record<string, boolean>>({});
const proxyFormC = reactive<Record<string, boolean>>({});
const proxyFormCoreView = ref('');
const proxyFormRiskFlag = ref(false);
const proxySubmitDone = ref(false);

const proxyTargetMember = computed(() =>
  COMMITTEE_MEMBERS.find(m => m.id === proxyTargetId.value) ?? null,
);

function resetProxyForm() {
  proxyTargetId.value = '';
  for (const k of Object.keys(proxyFormA)) delete proxyFormA[k];
  for (const k of Object.keys(proxyFormB)) delete proxyFormB[k];
  for (const k of Object.keys(proxyFormC)) delete proxyFormC[k];
  proxyFormCoreView.value = '';
  proxyFormRiskFlag.value = false;
  proxySubmitDone.value = false;
}

async function submitProxyVote() {
  if (!proxyTargetId.value) return;
  const meetingId = resolveVotingMeetingId();
  if (!meetingId) { alert('未找到可投票会议，请先创建并进入会议'); return; }
  try {
    const payload: Record<string, unknown> = {
      committee_type: 'mixed',
      vote_dimension: 'monthly',
    };
    if (Object.keys(proxyFormA).length > 0) payload.section_a = { ...proxyFormA };
    if (Object.keys(proxyFormB).length > 0) payload.section_b = { ...proxyFormB };
    const proxyFormCSelected = Object.keys(proxyFormC).filter(k => proxyFormC[k]);
    if (proxyFormCSelected.length > 0) payload.section_c = proxyFormCSelected;
    if (proxyFormCoreView.value.trim()) payload.core_view = proxyFormCoreView.value.trim();
    if (proxyFormRiskFlag.value) payload.risk_flag = true;

    const sub = await submitVote(meetingId, payload, proxyTargetId.value);
    memberSubmissions[proxyTargetId.value] = {
      sectionA: { ...proxyFormA },
      sectionB: { ...proxyFormB },
      sectionC: { ...proxyFormC },
      coreView: proxyFormCoreView.value,
      riskFlag: proxyFormRiskFlag.value,
      submittedAt: sub.submittedAt ?? '-',
    };
    proxySubmitDone.value = true;
    await fetchCommitteePageData();
    setTimeout(resetProxyForm, 2500);
  } catch (err) {
    console.error('[Committee] 代填提交失败:', err);
    alert('代填提交失败，请检查后端服务是否正常运行');
  }
}

// ── ⚠️ TODO: 以下为演示用 Mock 数据，待后端 API 实现后替换 ──────────────
// PRODUCT_CATEGORIES   → 待产品业绩系统 API (外部系统)
// TOP_STRATEGIES       → 待策略排行 API (外部系统)
// BOTTOM_STRATEGIES    → 待策略排行 API (外部系统)
// MODEL_OUTPUTS        → 待模型输出 API (外部系统: 回测/风控)
// MEMBERS_DATA         → 待用户目录 API (或从 JWT/配置读取)
// ────────────────────────────────────────────────────────────────────────

const showHistoryModal = ref(false);

interface CommitteeViewCard {
  author: string;
  role: string;
  color: string;
  sentiment: string;
  content: string;
  tags: string[];
}

/** 委员角色 → 主题色映射 */
const ROLE_COLORS: Record<string, string> = {
  '主任委员': '#3B9EFF',
  '班子': '#3B9EFF',
  '部门长': '#3B9EFF',
  '投资经理': '#3B9EFF',
  '风控合规总监': '#3B9EFF',
};

/** 根据委员评分均值推断情绪倾向 */
function inferSentiment(avgScore: number): string {
  if (avgScore >= 3.8) return '偏多';
  if (avgScore >= 2.8) return '中性';
  return '偏空';
}

/** 从核心观点文本中提取标签（简易关键词匹配） */
function extractTags(coreView: string, riskFlag: boolean): string[] {
  const tags: string[] = [];
  if (riskFlag) tags.push('风险预警');
  const keywordMap: [RegExp, string][] = [
    [/权益|股票|A股|港股/g, '权益'],
    [/债券|利率|久期|信用/g, '固收'],
    [/黄金|避险/g, '黄金'],
    [/原油|能源/g, '原油'],
    [/红利|高股息/g, '红利'],
    [/成长|科技/g, '成长'],
    [/价值|估值/g, '价值'],
    [/量化|CTA|趋势/g, '量化'],
    [/流动性|安全垫|风控/g, '风控'],
    [/政策|宏观/g, '宏观'],
  ];
  for (const [re, label] of keywordMap) {
    if (re.test(coreView)) tags.push(label);
  }
  return tags.length > 0 ? [...new Set(tags)].slice(0, 4) : ['观点'];
}

/**
 * 会前问卷汇总 · 委员定性观点
 * 从 memberSubmissions（真实后端数据）中提取 coreView，生成观点卡片。
 * 无提交数据的委员不展示。
 */
const committeeQualitativeViews = computed<CommitteeViewCard[]>(() => {
  return MEMBERS_DATA
    .filter(m => memberSubmissions[m.id]?.coreView?.trim())
    .map(m => {
      const sub = memberSubmissions[m.id];
      const scores = Object.values(sub.sectionA).filter((v): v is number => typeof v === 'number');
      const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 3;
      return {
        author: m.name,
        role: m.role,
        color: ROLE_COLORS[m.role] ?? '#94A3B8',
        sentiment: inferSentiment(avg),
        content: sub.coreView,
        tags: extractTags(sub.coreView, sub.riskFlag),
      };
    });
});

interface HistoricalVote {
  period: string;
  scores: Record<string, number>;
  newHighs: string[];
}

/** 历史投票数据，从后端加载 */
const historicalVotes = ref<HistoricalVote[]>([
  { period: '2026 Q1', scores: { '红利': 3, '偏股混': 2, '恒生科技': 3, '黄金': 4, '利率(10Y)': 4, '利率(30Y)': 4 }, newHighs: ['黄金', '利率(10Y)'] },
]);

/** 从后端加载历史会期评分数据 */
async function loadHistoryVotes() {
  if (skipCommitteeHttp()) return;
  try {
    const { data } = await http.get('/v1/committee/mixed/sessions/history', { params: { limit: 10 } });
    // data: { sessions: [{ session_code, submitted_count, scores: { asset: { avg, max, min, count } } }] }
    historicalVotes.value = (data.sessions ?? []).map(s => {
      const period = s.session_code.replace(/Q/g, ' Q');
      const scores: Record<string, number> = {};
      const newHighs: string[] = [];
      for (const [asset, info] of Object.entries(s.scores ?? {})) {
        if (typeof info === 'object' && info !== null && 'avg' in info) {
          scores[asset] = (info as { avg: number }).avg;
        }
      }
      return { period, scores, newHighs };
    });
  } catch {
    // 后端不可用时保留 mock 数据作为降级
  }
}

function handleUrgentRemind(memberName: string) {
  window.alert(`已向 ${memberName} 发送催办通知。`);
}

async function handleUrgentRemindApi(memberName: string, memberId?: number) {
  try {
    await http.post('/v1/committee/mixed/remind', { member_name: memberName, member_id: memberId });
    window.alert(`已向 ${memberName} 发送催办通知。`);
  } catch {
    window.alert(`催办通知发送失败，请稍后重试。`);
  }
}

function formatMeetingDate(iso: string | null | undefined): string {
  if (!iso) return '2026.04.15';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '2026.04.15';
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
}

const meetingHeaderCode = computed(
  () => committeePageContext.value?.meeting?.meeting_code ?? 'IC-2026-Q2-04',
);
const meetingHeaderDate = computed(() => {
  const r = committeePageContext.value?.resolution?.published_at;
  const s = committeePageContext.value?.meeting?.scheduled_at;
  return formatMeetingDate((r ?? s) as string | undefined);
});

/** 有后端投票记录时以前端为准展示回收进度；否则沿用本地 mock 提交数 */
const voteProgressTotal = computed(() => {
  const vn = committeePageContext.value?.votes?.length ?? 0;
  return vn > 0 ? Math.max(MEMBERS_DATA.length, vn) : MEMBERS_DATA.length;
});

const submittedCount = computed(() => {
  const vn = committeePageContext.value?.votes?.length ?? 0;
  if (vn > 0) return vn;
  return Object.keys(memberSubmissions).length;
});

const hasAnyRiskFlag = computed(() => {
  return Object.values(memberSubmissions).some(s => s.riskFlag);
});

const voteProgressPct = computed(() => {
  const t = voteProgressTotal.value;
  if (t <= 0) return 0;
  return Math.min(100, (submittedCount.value / t) * 100);
});

const voteProgressComplete = computed(() => submittedCount.value >= voteProgressTotal.value && voteProgressTotal.value > 0);
const sentReminders = reactive(new Set<string>());

function selectMember(id: string) { activeMemberId.value = id; }
function sendReminder(id: string) { sentReminders.add(id); }
function sendAllReminders() { MEMBERS_DATA.forEach(m => { if (!memberSubmissions[m.id]) sentReminders.add(m.id); }); }

const SELF_MEMBER_ID = computed(() => {
  const roleMap: Record<string, string> = {
    '班子': 'm1',
    '部门长': 'm2',
    '投资经理': 'm3',
    '混合投资委员会秘书': 'm0',
    '混合投资委员会委员': 'm3',
    '混合投资委员会主任委员': 'm0',
  };
  return roleMap[activeRole.value] || 'm3';
});
const memberSubmitted = computed(() => memberSubmissions[SELF_MEMBER_ID.value] || null);

function scoreToVoteChoice(score: number): 'underweight' | 'neutral' | 'overweight' {
  if (score <= 2) return 'underweight';
  if (score >= 4) return 'overweight';
  return 'neutral';
}

function buildVotePayload() {
  const payload: Record<string, unknown> = {
    committee_type: 'mixed',
    vote_dimension: 'monthly',
  };

  // section_a: 资产评分 {资产名: 1~5 整数}
  if (Object.keys(FORM_SECTION_A).length > 0) {
    payload.section_a = { ...FORM_SECTION_A };
  }

  // section_b: 创新高预判 {资产名: boolean}
  if (Object.keys(FORM_SECTION_B).length > 0) {
    payload.section_b = { ...FORM_SECTION_B };
  }

  // section_c: 重点资产列表
  const selectedFocus = Object.keys(FORM_SECTION_C).filter(k => FORM_SECTION_C[k]);
  if (selectedFocus.length > 0) {
    payload.section_c = selectedFocus;
  }

  // core_view: 委员综合市场观点
  if (formCoreView.value.trim()) {
    payload.core_view = formCoreView.value.trim();
  }

  // risk_flag: 风险提示标记 (boolean)
  if (formRiskFlag.value) {
    payload.risk_flag = true;
  }

  return payload;
}

function resolveVotingMeetingId(): number | null {
  if (currentMeetingId.value != null) return currentMeetingId.value;
  const contextMeetingId = committeePageContext.value?.meeting?.id;
  if (typeof contextMeetingId === 'number') return contextMeetingId;
  return meetingList.length > 0 ? meetingList[0].id : null;
}

async function submitMemberForm() {
  if (!activeMemberId.value || !formCoreView.value.trim()) return;
  const meetingId = resolveVotingMeetingId();
  if (!meetingId) {
    alert('未找到可投票会议，请先创建并进入会议');
    return;
  }
  try {
    await http.post(`/v1/committee/meetings/${meetingId}/submit-vote`, buildVotePayload());
    memberSubmissions[activeMemberId.value] = {
      sectionA: { ...FORM_SECTION_A }, sectionB: { ...FORM_SECTION_B }, sectionC: { ...FORM_SECTION_C },
      coreView: formCoreView.value, riskFlag: formRiskFlag.value,
      submittedAt: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    };
    await fetchCommitteePageData();
  } catch (err) {
    console.error('[Committee] 提交失败:', err);
    alert('提交失败，请检查后端服务是否正常运行');
  }
}

async function submitMemberFormSelf() {
  if (!formCoreView.value.trim()) return;
  const meetingId = resolveVotingMeetingId();
  if (!meetingId) {
    alert('未找到可投票会议，请先创建并进入会议');
    return;
  }
  try {
    await http.post(`/v1/committee/meetings/${meetingId}/submit-vote`, buildVotePayload());
    memberSubmissions[SELF_MEMBER_ID.value] = {
      sectionA: { ...FORM_SECTION_A }, sectionB: { ...FORM_SECTION_B }, sectionC: { ...FORM_SECTION_C },
      coreView: formCoreView.value, riskFlag: formRiskFlag.value,
      submittedAt: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    };
    await fetchCommitteePageData();
  } catch (err) {
    console.error('[Committee] 提交失败:', err);
    alert('提交失败，请检查后端服务是否正常运行');
  }
}

// ── Step 1: Product Category Performance ─────────────────────
interface ProdItem {
  name: string;
  ret: number;       // 区间收益率 %
  alpha: number;     // Alpha 收益 %
  beta: number;      // Beta 收益 %
  lev: number;       // 杠杆收益 %
  rank: string;      // 竞品排名标签 e.g. 'TOP 8%'
  rankTier: 1 | 2 | 3;  // 1=前四分位 2=中段 3=后段
  timing: number;    // 调仓贡献度 bps
  selRate: number;   // 择券胜率 0-100
  maxdd: string;
}

interface ProdCategory {
  label: string;
  tag: string;
  color: string;
  items: ProdItem[];
}

// ── 上期决议胜率复盘（Mock 数据：混合投委会 2026 Q1） ───────────────────────────

const PREV_PERIOD_REVIEW_MIXED = [
  { asset: '红利',      prevView: '中性偏乐观', prevPoint: 11520,  currPoint: 11945.58, amplitudeType: 'pct' as const },
  { asset: '偏股混',    prevView: '中性偏乐观', prevPoint: 7450,   currPoint: 7228.45,  amplitudeType: 'pct' as const },
  { asset: '恒生科技',  prevView: '中性偏谨慎', prevPoint: 5180,   currPoint: 4986.78,  amplitudeType: 'pct' as const },
  { asset: '黄金',      prevView: '乐观',       prevPoint: 6.05,   currPoint: 7.283,    amplitudeType: 'pct' as const },
  { asset: '利率(10Y)', prevView: '中性偏乐观', prevPoint: 1.95,   currPoint: 1.79,     amplitudeType: 'bp'  as const },
  { asset: '利率(30Y)', prevView: '中性偏乐观', prevPoint: 2.45,   currPoint: 2.281,    amplitudeType: 'bp'  as const },
  { asset: '转债',      prevView: '乐观',       prevPoint: 530.10, currPoint: 502.65,   amplitudeType: 'pct' as const },
  { asset: '二级债基',  prevView: '乐观',       prevPoint: 4868,   currPoint: 5224.57,  amplitudeType: 'pct' as const },
] as const;

type PrevReviewItem = typeof PREV_PERIOD_REVIEW_MIXED[number];

function calcReviewRow(item: PrevReviewItem) {
  const BULLISH = new Set<string>(['乐观', '中性偏乐观']);
  const BEARISH = new Set<string>(['谨慎', '中性偏谨慎']);
  const { prevView, prevPoint, currPoint, amplitudeType } = item;

  // changeVal in bp (bp type) or pct (pct type)
  const changeVal = amplitudeType === 'bp'
    ? parseFloat(((currPoint - prevPoint) * 100).toFixed(2))
    : parseFloat(((currPoint - prevPoint) / prevPoint * 100).toFixed(2));
  const changeStr = amplitudeType === 'bp'
    ? `${changeVal > 0 ? '+' : ''}${changeVal}bp`
    : `${changeVal > 0 ? '+' : ''}${changeVal}%`;

  let verdict: 'correct' | 'wrong' | 'neutral_ok' | 'neutral_fail';
  if (BULLISH.has(prevView)) {
    // bp: bullish = expect yield DOWN → negative changeVal = correct
    // pct: bullish = expect price UP → positive changeVal = correct
    verdict = (amplitudeType === 'bp' ? changeVal < 0 : changeVal > 0) ? 'correct' : 'wrong';
  } else if (BEARISH.has(prevView)) {
    verdict = (amplitudeType === 'bp' ? changeVal > 0 : changeVal < 0) ? 'correct' : 'wrong';
  } else {
    const thr = amplitudeType === 'bp' ? 10 : 3;
    verdict = Math.abs(changeVal) <= thr ? 'neutral_ok' : 'neutral_fail';
  }

  const verdictLabel: Record<typeof verdict, string> = {
    correct: '✓ 方向正确',
    wrong: '✗ 方向偏差',
    neutral_ok: '● 震荡区间内',
    neutral_fail: '△ 超出震荡区间',
  };

  return { ...item, changeVal, changeStr, verdict, verdictLabel: verdictLabel[verdict] };
}

const PREV_REVIEW_ROWS = computed(() => PREV_PERIOD_REVIEW_MIXED.map(calcReviewRow));

const PREV_REVIEW_SUMMARY = computed(() => {
  const rows = PREV_REVIEW_ROWS.value;
  const directional = rows.filter(r => r.verdict === 'correct' || r.verdict === 'wrong');
  const correct = directional.filter(r => r.verdict === 'correct');
  const total = directional.length;
  const winRate = total > 0 ? Math.round(correct.length / total * 100) : 0;

  const bullishCorrect = rows.filter(r => r.verdict === 'correct' && (r.prevView === '乐观' || r.prevView === '中性偏乐观'));
  const best = bullishCorrect.length
    ? bullishCorrect.reduce((a, b) => Math.abs(a.changeVal) > Math.abs(b.changeVal) ? a : b)
    : null;

  return {
    totalDirectional: total,
    correctCount: correct.length,
    winRate,
    bestAsset: best?.asset ?? '',
    bestChange: best?.changeStr ?? '',
    missAssets: rows.filter(r => r.verdict === 'wrong').map(r => r.asset),
  };
});

const PRODUCT_CATEGORIES: ProdCategory[] = [
  {
    label: '固收+低波', tag: 'LOW-VOL', color: '#3B9EFF',
    items: [
      { name: '稳健增利A', ret: 4.2,  alpha: 1.8,  beta: 2.1, lev: 0.3,  rank: 'TOP 8%',  rankTier: 1, timing: 12.5, selRate: 68, maxdd: '-1.2%' },
      { name: '启航1号',   ret: 3.8,  alpha: 1.2,  beta: 2.3, lev: 0.3,  rank: 'TOP 22%', rankTier: 1, timing: 8.1,  selRate: 62, maxdd: '-1.8%' },
    ],
  },
  {
    label: '固收+中波', tag: 'MID-VOL', color: '#3B9EFF',
    items: [
      { name: '全天候FOF', ret: 2.9,  alpha: 0.8,  beta: 1.9, lev: 0.2,  rank: 'TOP 35%', rankTier: 2, timing: 6.8,  selRate: 55, maxdd: '-2.5%' },
      { name: '高收益债',  ret: -2.1, alpha: -0.8, beta: -1.1, lev: -0.2, rank: 'BOT 12%', rankTier: 3, timing: -3.2, selRate: 38, maxdd: '-6.8%' },
    ],
  },
  {
    label: '混合', tag: 'HYBRID', color: '#3B9EFF',
    items: [
      { name: '成长精选',   ret: 5.1,  alpha: 2.4,  beta: 2.5,  lev: 0.2,  rank: 'TOP 6%',  rankTier: 1, timing: 18.7, selRate: 72, maxdd: '-5.3%' },
      { name: '量化对冲',   ret: 1.8,  alpha: 1.5,  beta: 0.2,  lev: 0.1,  rank: 'TOP 28%', rankTier: 2, timing: -1.5, selRate: 58, maxdd: '-3.1%' },
      { name: '港股通精选', ret: -1.9, alpha: -1.2, beta: -0.5, lev: -0.2, rank: 'BOT 18%', rankTier: 3, timing: -2.1, selRate: 42, maxdd: '-9.2%' },
    ],
  },
];

/** PM 定性评价（可编辑） */
const guidanceQualReview = ref('');

/** 系统自动生成的定量分析摘要 */
const guidanceQuantAnalysis = computed(() => {
  const all = PRODUCT_CATEGORIES.flatMap(c => c.items);
  const total = all.length;
  const pos = all.filter(i => i.ret > 0).length;
  const winRate = Math.round(pos / total * 100);
  const topQ = all.filter(i => i.rankTier === 1).length;
  const posT = all.filter(i => i.timing > 0).length;
  const avgAlpha = (all.reduce((s, i) => s + i.alpha, 0) / total).toFixed(2);
  const avgSel = Math.round(all.reduce((s, i) => s + i.selRate, 0) / total);
  return `本期共 ${total} 只产品完成回溯，${pos} 只正收益（胜率 ${winRate}%）；前四分位产品 ${topQ} 只（占 ${Math.round(topQ / total * 100)}%）。` +
    `Alpha 均值 ${Number(avgAlpha) >= 0 ? '+' : ''}${avgAlpha}%，固收+低波类别 Beta 来源占比最高（>50%），指引跟踪偏离最小（≤20bps）。` +
    `择时贡献为正的产品 ${posT} 只（${Math.round(posT / total * 100)}%）；择券平均胜率 ${avgSel}%，混合类别 Alpha 离散度较大，需审视主动管理能力稳定性。`;
});

const TOP_STRATEGIES = [
  { name: '利率债骑乘', type: '固收', return: '+4.2%', sharpe: '2.31' },
  { name: '红利低波',   type: '权益', return: '+3.8%', sharpe: '1.87' },
  { name: '可转债双低', type: '转债', return: '+3.5%', sharpe: '1.72' },
  { name: 'CTA趋势',   type: '另类', return: '+3.1%', sharpe: '1.65' },
  { name: '信用挖掘',  type: '固收', return: '+2.9%', sharpe: '1.53' },
];
const BOTTOM_STRATEGIES = [
  { name: '中小盘成长', issue: '回撤超限 · 风格漂移', return: '-5.8%', maxdd: '-12.3%' },
  { name: '高收益债',   issue: '信用利差走阔',         return: '-2.1%', maxdd: '-6.8%' },
  { name: '港股通精选', issue: '流动性不足',            return: '-1.9%', maxdd: '-9.2%' },
];

// ── Step 2: Consensus & Models ────────────────────────────────
const MATRIX_COL_EXTREMES = computed(() => {
  const result: Record<string, { max: number; min: number }> = {};
  for (const asset of ASSET_LIST) {
    const scores = MEMBERS_DATA
      .filter(m => memberSubmissions[m.id])
      .map(m => memberSubmissions[m.id].sectionA[asset] ?? 3);
    result[asset] = {
      max: scores.length > 0 ? Math.max(...scores) : 3,
      min: scores.length > 0 ? Math.min(...scores) : 3,
    };
  }
  return result;
});

const MATRIX_COL_AVG = computed(() => {
  const selfId = SELF_MEMBER_ID.value;
  const selfHasSubmitted = !!memberSubmissions[selfId];
  const result: Record<string, number> = {};
  for (const asset of ASSET_LIST) {
    const scores = MEMBERS_DATA
      .filter(m => memberSubmissions[m.id])
      .map(m => memberSubmissions[m.id].sectionA[asset] ?? 3);
    if (!selfHasSubmitted) {
      scores.push(FORM_SECTION_A[asset] ?? 3);
    }
    result[asset] = scores.length > 0 ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10 : 3;
  }
  return result;
});

// ── 投票分布汇总矩阵（混合投委会视角） ────────────────────────────────────────

const VOTE_DIST_HL_BG = ['bg-[#00C9A7]/15', 'bg-[#3B9EFF]/8', 'bg-[#3B9EFF]/12', 'bg-[#F04864]/8', 'bg-[#F04864]/14'] as const;
const VOTE_DIST_HL_TEXT = ['text-[#00C9A7]', 'text-[#3B9EFF]/70', 'text-[#3B9EFF]', 'text-[#F04864]/70', 'text-[#F04864]'] as const;
const VOTE_CONSENSUS_STYLE: Record<string, string> = {
  '谨慎':     'border-[#00C9A7]/40 bg-[#00C9A7]/10 text-[#00C9A7]',
  '中性偏谨慎': 'border-[#3B9EFF]/25 bg-[#3B9EFF]/6  text-[#3B9EFF]/70',
  '中性':     'border-[#3B9EFF]/40 bg-[#3B9EFF]/8  text-[#3B9EFF]',
  '中性偏乐观': 'border-[#F04864]/25 bg-[#F04864]/6  text-[#F04864]/70',
  '乐观':     'border-[#F04864]/40 bg-[#F04864]/10 text-[#F04864]',
};

const MIXED_DIST_ROWS = computed(() => {
  const LABELS = ['谨慎', '中性偏谨慎', '中性', '中性偏乐观', '乐观'] as const;
  const selfId = SELF_MEMBER_ID.value;
  const selfHasSubmitted = !!memberSubmissions[selfId];

  const groupOrder: string[] = [];
  const groupMap = new Map<string, typeof MIXED_ASSET_LIST[number][]>();
  for (const cfg of MIXED_ASSET_LIST) {
    if (!groupMap.has(cfg.大类)) { groupOrder.push(cfg.大类); groupMap.set(cfg.大类, []); }
    groupMap.get(cfg.大类)!.push(cfg);
  }

  return groupOrder.flatMap(大类 => {
    const items = groupMap.get(大类)!;
    return items.map((cfg, i) => {
      const dist = [0, 0, 0, 0, 0];
      for (const m of MEMBERS_DATA) {
        const sub = memberSubmissions[m.id];
        if (sub) {
          const s = sub.sectionA[cfg.细分策略];
          if (s >= 1 && s <= 5) dist[s - 1]++;
        }
      }
      // 实时同步：若本人尚未提交，将当前 FORM_SECTION_A 计入分布
      if (!selfHasSubmitted) {
        const s = FORM_SECTION_A[cfg.细分策略];
        if (s >= 1 && s <= 5) dist[s - 1]++;
      }
      const total = dist.reduce((a, b) => a + b, 0);
      const maxCount = total > 0 ? Math.max(...dist) : 0;
      const mean = total > 0 ? dist.reduce((acc, c, j) => acc + (j + 1) * c, 0) / total : 3;
      const label = LABELS[Math.max(0, Math.min(4, Math.round(mean) - 1))];
      const r = calcTargetRange(cfg.当前点位, cfg.amplitude[label]);
      const rangeStr = r.low !== null && r.high !== null ? `${r.low}~${r.high}`
        : r.low !== null ? `≥${r.low}` : r.high !== null ? `≤${r.high}` : '—';
      return {
        大类, isFirstInGroup: i === 0, groupSpan: items.length,
        细分策略: cfg.细分策略, 标的指数: cfg.标的指数, 当前点位: cfg.当前点位,
        dist, maxCount, totalVotes: total, consensusLevel: label, rangeStr,
      };
    });
  });
});

const CONSENSUS_ANALYSIS = computed(() => {
  const selfId = SELF_MEMBER_ID.value;
  const selfHasSubmitted = !!memberSubmissions[selfId];
  const submittedMembers = MEMBERS_DATA.filter(m => memberSubmissions[m.id]);
  return ASSET_LIST.map(asset => {
    const scores = submittedMembers.map(m => memberSubmissions[m.id].sectionA[asset] ?? 3);
    // 实时同步：本人未提交时，将当前填报分值纳入统计
    if (!selfHasSubmitted) {
      scores.push(FORM_SECTION_A[asset] ?? 3);
    }
    const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 3;
    const maxScore = scores.length > 0 ? Math.max(...scores) : 3;
    const minScore = scores.length > 0 ? Math.min(...scores) : 3;
    const newHighCount = submittedMembers.filter(m => memberSubmissions[m.id].sectionB[asset]).length
      + (!selfHasSubmitted && FORM_SECTION_B[asset] ? 1 : 0);
    const prevAvg = historicalVotes.value.length > 0 ? (historicalVotes.value[0].scores[asset] ?? 3) : 3;
    const delta = avg - prevAvg;
    const label = avg >= 4.5 ? '乐观' : avg >= 3.5 ? '中性偏乐观' : avg >= 2.5 ? '中性' : avg >= 1.5 ? '中性偏谨慎' : '谨慎';
    const spread = maxScore - minScore;
    const consensus = spread <= 1 ? '高度一致' : spread <= 2 ? '方向趋同' : '分歧明显';
    return { asset, avg: Math.round(avg * 10) / 10, maxScore, minScore, newHighCount, prevAvg, delta, label, consensus, scores, memberIds: submittedMembers.map(m => m.id) };
  });
});

const VOTING_MATRIX = computed(() => {
  const submittedMembers = MEMBERS_DATA.filter(m => memberSubmissions[m.id]);
  return { members: submittedMembers, assets: [...ASSET_LIST] };
});

const GUIDANCE_MAP: Record<string, { high: string; mid: string; low: string }> = {
  '红利': { high: '增配高股息标的，把握分红行情', mid: '标配红利策略，注重防御', low: '减持红利暴露，转向防御性资产' },
  '偏股混': { high: '积极布局偏股混合，把握结构性机会', mid: '均衡配置偏股混合', low: '规避高波动权益敞口，控制回撤' },
  '恒生科技': { high: '增配港股科技，把握估值修复行情', mid: '标配恒生科技，维持适度仓位', low: '减持港股科技，关注政策不确定性' },
  '黄金': { high: '增配黄金避险，对冲地缘风险', mid: '标配黄金，维持组合分散化', low: '减持黄金，释放资金效率' },
  '利率(10Y)': { high: '增配10Y利率债，积极拉长久期', mid: '维持中性久期，关注骑乘机会', low: '缩短久期，规避利率上行风险' },
  '利率(30Y)': { high: '增配30Y超长债，捕获期限溢价', mid: '波段操作30Y国债，维持中性', low: '规避超长端利率风险，回归短端' },
};

const GRADE_COLORS: Record<number, string> = {
  1: 'bg-[#00C9A7]/10 text-[#00C9A7] border-[#00C9A7]/25',   // 谨慎 — 绿
  2: 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25',   // 中性偏谨慎 — 青
  3: 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25',   // 中性 — 蓝
  4: 'bg-[#3B9EFF]/10 text-[#3B9EFF] border-[#3B9EFF]/25',   // 中性偏乐观 — 琥珀
  5: 'bg-[#F04864]/10 text-[#F04864] border-[#F04864]/25',   // 乐观 — 红
};

const chairmanGrades = reactive<Record<string, number>>({});
ASSET_LIST.forEach(a => { chairmanGrades[a] = MATRIX_COL_AVG[a] ? Math.round(MATRIX_COL_AVG[a]) : 3; });

const BOND_DURATION_MAP: Record<number, string> = { 1: '1-1.5年', 2: '1.5-2年', 3: '2-3年', 4: '3-4年', 5: '3-5年' };
const POSITION_MAP: Record<number, string> = { 1: '0-5%', 2: '5-10%', 3: '10-15%', 4: '15-20%', 5: '20-30%' };

const GUIDANCE_TEXT_MAP: Record<number, string> = {
  1: '谨慎规避，严格控制风险敞口',
  2: '中性偏谨慎，低配或观望',
  3: '中性标配，维持现有水平',
  4: '中性偏乐观，适度增配',
  5: '乐观积极，重点配置',
};

const RATE_ASSETS = new Set(['利率(10Y)', '利率(30Y)']);

/** 从统一字典中获取某资产在指定评分档的观点幅度文本 */
function getAmplitudeText(assetName: string, score: number): string {
  const cfg = VOTE_CONFIG_MAP.get(assetName);
  if (!cfg) return '—';
  const label = SCORE_LABELS[score] as keyof typeof cfg.amplitude;
  return cfg.amplitude[label] ?? '—';
}

/** 计算并格式化预期点位区间字符串 */
function getTargetRangeText(assetName: string, score: number): string {
  const cfg = VOTE_CONFIG_MAP.get(assetName);
  if (!cfg) return '—';
  const amp = getAmplitudeText(assetName, score);
  const r = calcTargetRange(cfg.当前点位, amp);
  if (r.low === null && r.high !== null) return `≤ ${r.high}`;
  if (r.high === null && r.low !== null) return `≥ ${r.low}`;
  if (r.low !== null && r.high !== null) return `${r.low} — ${r.high}`;
  return '—';
}

/** 根据列均值四舍五入后的档位计算共识点位区间 */
function getConsensusRangeText(assetName: string, avgScore: number): string {
  const grade = Math.round(avgScore);
  return getTargetRangeText(assetName, grade);
}

/** 返回单位标注（收益率 vs 点位） */
function getAmplitudeUnit(assetName: string): string {
  const cfg = VOTE_CONFIG_MAP.get(assetName);
  return cfg?.amplitudeType === 'bp' ? '%(收益率)' : '点';
}

const DYNAMIC_GUIDANCE = computed(() => {
  const result: Record<string, string> = {};
  for (const asset of ASSET_LIST) {
    const grade = chairmanGrades[asset] ?? 3;
    if (RATE_ASSETS.has(asset)) {
      result[asset] = `建议久期范围 ${BOND_DURATION_MAP[grade]}，${GUIDANCE_TEXT_MAP[grade]}`;
    } else {
      result[asset] = `建议配置比例 ${POSITION_MAP[grade]}，${GUIDANCE_TEXT_MAP[grade]}`;
    }
  }
  return result;
});

const DYNAMIC_METRIC = computed(() => {
  const result: Record<string, string> = {};
  for (const asset of ASSET_LIST) {
    const grade = chairmanGrades[asset] ?? 3;
    result[asset] = RATE_ASSETS.has(asset) ? `久期 ${BOND_DURATION_MAP[grade]}` : `仓位 ${POSITION_MAP[grade]}`;
  }
  return result;
});

const signerId = ref('m0');
const signerName = computed(() => MEMBERS_DATA.find(m => m.id === signerId.value)?.name ?? '-');

const GUIDANCE_RESULT = computed(() => {
  return CONSENSUS_ANALYSIS.value.map(ca => {
    const map = GUIDANCE_MAP[ca.asset];
    const guidance = ca.avg >= 4 ? map.high : ca.avg >= 2.5 ? map.mid : map.low;
    return { ...ca, guidance };
  });
});

const EQUITY_ASSETS = new Set(['红利', '偏股混', '恒生科技']);

// ═══════════════════════════════════════════════════════════════════════
// 跨委员会共识参考（Section 13 扩展：信息共享层）
// ═══════════════════════════════════════════════════════════════════════

const showCrossPanel = ref(false);

/** FICC 投委会对其6个资产的本期投票均值 Mock（供混合投委会交叉印证） */
const CROSS_FICC_MOCK: Record<string, number> = {
  '存单': 3.0, '信用': 3.2, '利率(10Y)': 3.8, '利率(30Y)': 4.0, '转债': 3.3, '二级债基': 3.5,
};

const FICC_VOTE_CONFIG_MAP_CROSS = new Map(FICC_ASSET_LIST.map(i => [i.细分策略, i]));
const SHARED_NAMES = new Set(['利率(10Y)', '利率(30Y)']);

/** 通用点位区间字符串（脚本侧，可用 as 类型断言） */
function calcRangeStr(cfg: { 当前点位: number; amplitude: Record<string, string> }, avg: number): string {
  const grade = Math.round(avg);
  const lm: Record<number, string> = { 1: '谨慎', 2: '中性偏谨慎', 3: '中性', 4: '中性偏乐观', 5: '乐观' };
  const amp = cfg.amplitude[lm[grade] as keyof typeof cfg.amplitude] ?? '—';
  const r = calcTargetRange(cfg.当前点位, amp);
  if (r.low === null && r.high !== null) return `≤${r.high}`;
  if (r.high === null && r.low !== null) return `≥${r.low}`;
  if (r.low !== null && r.high !== null) return `${r.low}~${r.high}`;
  return '—';
}

/** Table B：全局大类合并统计（混合均值 ⊕ FICC均值 算术平均） */
const CROSS_GLOBAL_ITEMS = computed(() => {
  const scoreLabels: Record<number, string> = { 1: '谨慎', 2: '中性偏谨慎', 3: '中性', 4: '中性偏乐观', 5: '乐观' };
  const items: Array<{
    name: string; 大类: string; source: string;
    ownAvg: number | null; crossAvg: number | null; globalAvg: number;
    globalLabel: string; globalRange: string;
  }> = [];

  for (const cfg of MIXED_ASSET_LIST) {
    const ownAvg = MATRIX_COL_AVG.value[cfg.细分策略] ?? null;
    const crossAvg = CROSS_FICC_MOCK[cfg.细分策略] ?? null;
    const globalAvg = ownAvg !== null && crossAvg !== null
      ? Math.round(((ownAvg + crossAvg) / 2) * 10) / 10
      : (ownAvg ?? crossAvg ?? 3);
    items.push({
      name: cfg.细分策略, 大类: cfg.大类,
      source: crossAvg !== null ? '⚡共享' : '混合',
      ownAvg: ownAvg !== null ? Math.round(ownAvg * 10) / 10 : null,
      crossAvg,
      globalAvg,
      globalLabel: scoreLabels[Math.round(globalAvg)] ?? '中性',
      globalRange: calcRangeStr(cfg, globalAvg),
    });
  }

  for (const cfg of FICC_ASSET_LIST) {
    if (SHARED_NAMES.has(cfg.细分策略)) continue;
    const crossAvg = CROSS_FICC_MOCK[cfg.细分策略] ?? null;
    if (crossAvg === null) continue;
    items.push({
      name: cfg.细分策略, 大类: cfg.大类,
      source: 'FICC',
      ownAvg: null,
      crossAvg,
      globalAvg: crossAvg,
      globalLabel: scoreLabels[Math.round(crossAvg)] ?? '中性',
      globalRange: calcRangeStr(cfg, crossAvg),
    });
  }
  return items;
});

// ════════════════════════════════════════════════════════════════════════

const EQUITY_STYLE_GUIDANCE = computed(() => {
  const items = CONSENSUS_ANALYSIS.value.filter(ca => EQUITY_ASSETS.has(ca.asset));
  if (items.length === 0) return { main: '数据不足', detail: '' };
  const sorted = [...items].sort((a, b) => b.avg - a.avg);
  const main = sorted[0];
  const worst = sorted[sorted.length - 1];
  const detail = main.avg === worst.avg
    ? `三种风格均值一致 (${main.avg.toFixed(1)})，建议均衡配置`
    : `当前建议主力风格: ${main.asset} (${main.avg.toFixed(1)}分)`;
  return { main: main.asset, avg: main.avg, detail, items: sorted };
});

const aiMinutesLoading = ref(false);
const aiMinutesReady = ref(false);
const aiMinutesContent = ref('');

function generateAIMinutes() {
  aiMinutesLoading.value = true;
  aiMinutesReady.value = false;
  const divergences = CONSENSUS_ANALYSIS.value
    .filter(ca => ca.consensus === '分歧明显')
    .map(ca => {
      const maxMember = ca.memberIds[ca.scores.indexOf(ca.maxScore)];
      const minMember = ca.memberIds[ca.scores.indexOf(ca.minScore)];
      const maxName = MEMBERS_DATA.find(m => m.id === maxMember)?.name ?? '某委员';
      const minName = MEMBERS_DATA.find(m => m.id === minMember)?.name ?? '某委员';
      return `${maxName}与${minName}在${ca.asset}资产的分歧较大（${ca.minScore}分 vs ${ca.maxScore}分）`;
    });

  const guidanceText = GUIDANCE_RESULT.value.map(g => `${g.asset}：均值 ${g.avg.toFixed(1)}（${g.label}）— ${g.guidance}`).join('\n');

  setTimeout(() => {
    aiMinutesContent.value = [
      `【会议纪要 · ${meetingHeaderCode.value}】`,
      `日期：${meetingHeaderDate.value}`,
      '',
      '一、投票汇总',
      `本次会议共收到 ${submittedCount.value} 份问卷，综合评分如下：`,
      ...CONSENSUS_ANALYSIS.value.map(ca => `  - ${ca.asset}: 均值 ${ca.avg.toFixed(1)}（${ca.label}），较上期 ${ca.delta >= 0 ? '+' : ''}${ca.delta.toFixed(1)}`),
      '',
      '二、配置指引',
      guidanceText,
      '',
      '三、权益风格建议',
      EQUITY_STYLE_GUIDANCE.value.detail,
      '',
      ...(divergences.length > 0 ? ['四、争论焦点', ...divergences.map(d => `  - ${d}`)] : []),
    ].join('\n');
    aiMinutesLoading.value = false;
    aiMinutesReady.value = true;
  }, 3000);
}

const MODEL_OUTPUTS = [
  { name: 'SAA 蒙特卡洛', badge: 'MC-SIM', color: '#3B9EFF', desc: '10万次随机模拟 · 均值-方差前沿', sharpe: '0.82', highlight: false, action: true, actionLabel: '运行模拟', allocations: [{ label: '权益', weight: 35, color: '#3B9EFF' }, { label: '固收', weight: 50, color: '#3B9EFF' }, { label: '另类', weight: 15, color: '#3B9EFF' }] },
  { name: 'BL 模型', badge: 'BLACK-LIT', color: '#3B9EFF', desc: '贝叶斯观点注入 · 委员预期融合', sharpe: '0.95', highlight: true, action: true, actionLabel: '进入沙盘', allocations: [{ label: '权益', weight: 42, color: '#3B9EFF' }, { label: '固收', weight: 43, color: '#3B9EFF' }, { label: '另类', weight: 15, color: '#3B9EFF' }] },
  { name: 'Risk Parity', badge: 'RP-ATAN', color: '#3B9EFF', desc: '等风险贡献 · 波动率平价', sharpe: '0.78', highlight: false, action: true, actionLabel: '查看模型详情', allocations: [{ label: '权益', weight: 28, color: '#3B9EFF' }, { label: '固收', weight: 55, color: '#3B9EFF' }, { label: '另类', weight: 17, color: '#3B9EFF' }] },
];

// ── 三模型资产配置树状数据（颗粒度下沉至细分资产）────────────────
interface ModelTreeChild { sub: string; mc: number; bl: number; rp: number; }
interface ModelTreeRow { category: string; mc: number; bl: number; rp: number; children: ModelTreeChild[]; }
const MODEL_TREE_DATA: ModelTreeRow[] = [
  {
    category: '固收', mc: 50, bl: 43, rp: 55,
    children: [
      { sub: '利率10Y', mc: 30, bl: 25, rp: 33 },
      { sub: '利率30Y', mc: 20, bl: 18, rp: 22 },
    ],
  },
  {
    category: '权益', mc: 35, bl: 42, rp: 28,
    children: [
      { sub: '红利',     mc: 14, bl: 17, rp: 11 },
      { sub: '偏股混',   mc: 13, bl: 16, rp: 11 },
      { sub: '恒生科技', mc:  8, bl:  9, rp:  6 },
    ],
  },
  {
    category: '另类', mc: 15, bl: 15, rp: 17,
    children: [
      { sub: '黄金', mc: 15, bl: 15, rp: 17 },
    ],
  },
];
const expandedModelTree = reactive(new Set<string>(['固收', '权益', '另类']));
function toggleModelTreeRow(cat: string) {
  expandedModelTree.has(cat) ? expandedModelTree.delete(cat) : expandedModelTree.add(cat);
}

// ── 决议同步状态 ────────────────────────────────────────────────
const isSynced = ref(false);
const syncedAt = ref('');

// ── Step 3: Decision table ────────────────────────────────────
const expandedGroups = reactive(new Set<string>(['债券', '权益']));
function toggleGroup(asset: string) { expandedGroups.has(asset) ? expandedGroups.delete(asset) : expandedGroups.add(asset); }

/** 决议表数据由 demoStore.committeeDecisionTable 提供（fetchMeetingResolution 从门户快照覆盖） */
const decisionTable = committeeDecisionTable;

const showModelAnchors = ref(true);
const showSAASandbox = ref(false);
const showDecisionTimeline = ref(false);

// ── BL Model Detail Dialog ────────────────────────────────────
const showBLDialog = ref(false);
const blDialogChartRef = ref<HTMLElement | null>(null);
let blDialogChart: echarts.ECharts | null = null;

// Mock data: market baseline weights vs BL optimized weights
// Logic: committee is bullish on equity → BL lifts equity, trims fixed income
const BL_WEIGHT_DATA = {
  assets: ['A股权益', '港股/海外权益', '利率债', '信用债', '商品/黄金', '现金/另类'],
  market:  [20, 15, 28, 22, 8,  7],
  blOpt:   [24, 18, 22, 21, 11, 4],
};

const BL_PARAMS = [
  { key: 'lambda', symbol: 'λ',   name: '风险厌恶系数', value: '2.50',  note: '市场均衡',  highlight: false },
  { key: 'tau',    symbol: 'τ',   name: '置信度系数',   value: '0.025', note: '先验权重',  highlight: true  },
  { key: 'omega',  symbol: 'Ω',   name: '观点不确定性', value: 'diag',  note: '对角矩阵',  highlight: false },
  { key: 'views',  symbol: 'n',   name: '本期观点数量', value: '4',     note: '委员会输入', highlight: false },
  { key: 'sharpe', symbol: 'SR',  name: '优化组合夏普', value: '0.95',  note: '较基准+0.13', highlight: true },
];

const BL_VIEW_CONTRIBUTIONS = [
  { asset: 'A股权益',     source: '委员多数看多',  excessReturn: 3.2,  weightDelta: 4.0,  confidence: 78, direction: '看多' },
  { asset: '港股/海外',   source: '委员多数看多',  excessReturn: 2.8,  weightDelta: 3.0,  confidence: 65, direction: '看多' },
  { asset: '商品/黄金',   source: '通胀对冲需求',  excessReturn: 1.5,  weightDelta: 3.0,  confidence: 72, direction: '看多' },
  { asset: '利率债',      source: '久期中性偏短',  excessReturn: -1.2, weightDelta: -6.0, confidence: 60, direction: '中性' },
  { asset: '现金/另类',   source: '流动性管理',    excessReturn: 0.0,  weightDelta: -3.0, confidence: 55, direction: '中性' },
];

const BL_SUMMARY_STATS = [
  { label: '预期年化收益',  value: '7.8%',  color: 'text-[#F04864]',  note: '较基准 +1.4%' },
  { label: '预期年化波动',  value: '9.2%',  color: 'text-[#3B9EFF]',  note: '风险可控' },
  { label: '优化夏普比率',  value: '0.95',  color: 'text-cyan-300',    note: '较基准 +0.13' },
];

function openBLDialog() {
  showBLDialog.value = true;
  nextTick(() => {
    if (!blDialogChartRef.value) return;
    blDialogChart?.dispose();
    blDialogChart = echarts.init(blDialogChartRef.value);
    blDialogChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#202431',
        borderColor: '#252A3A',
        textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 },
        formatter: (params: any) => {
          const lines = params.map((p: any) => `<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${p.color};margin-right:5px"></span>${p.seriesName}: <b style="font-family:monospace">${p.value}%</b>`);
          return `<b>${params[0].name}</b><br/>` + lines.join('<br/>');
        },
      },
      legend: {
        data: ['市场基准权重', 'BL 优化权重'],
        textStyle: { color: '#94A3B8', fontSize: 11, fontFamily: 'monospace' },
        top: 4,
        right: 8,
        itemWidth: 10,
        itemHeight: 10,
      },
      grid: { top: 36, right: 16, bottom: 40, left: 52 },
      xAxis: {
        type: 'category',
        data: BL_WEIGHT_DATA.assets,
        axisLine: { lineStyle: { color: '#2E3348' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace', interval: 0 },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        max: 35,
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v + '%' },
        splitLine: { lineStyle: { color: '#252A3A', type: 'dashed' } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          name: '市场基准权重',
          type: 'bar',
          data: BL_WEIGHT_DATA.market,
          barWidth: '28%',
          itemStyle: { color: '#3B9EFF', opacity: 0.55, borderRadius: [3, 3, 0, 0] },
          label: { show: true, position: 'top', color: '#64748B', fontSize: 10, fontFamily: 'monospace', formatter: (p: any) => p.value + '%' },
        },
        {
          name: 'BL 优化权重',
          type: 'bar',
          data: BL_WEIGHT_DATA.blOpt,
          barWidth: '28%',
          itemStyle: { color: '#22D3EE', borderRadius: [3, 3, 0, 0] },
          label: { show: true, position: 'top', color: '#22D3EE', fontSize: 10, fontFamily: 'monospace', formatter: (p: any) => p.value + '%' },
        },
      ],
    });
  });
}

function closeBLDialog() {
  showBLDialog.value = false;
  blDialogChart?.dispose();
  blDialogChart = null;
}

// ── Monte Carlo Detail Dialog ─────────────────────────────────
const showMCDialog = ref(false);
const mcChartRef = ref<HTMLElement | null>(null);
let mcChart: echarts.ECharts | null = null;

interface MCAllocItem { label: string; weight: number }
interface MCFrontierPoint { vol: number; ret: number; sharpe: string; alloc: MCAllocItem[] }

const mcSelectedAlloc = ref<MCAllocItem[] | null>(null);
const mcSelectedPoint = ref<{ vol: number; ret: number; sharpe: string } | null>(null);

const MC_FRONTIER: MCFrontierPoint[] = [
  { vol: 5.2,  ret: 3.8,  sharpe: '0.58', alloc: [{ label: '纯债',    weight: 55 }, { label: '信用债',   weight: 25 }, { label: '沪深300', weight: 5  }, { label: '港股',     weight: 5  }, { label: '商品/黄金', weight: 5  }, { label: '现金', weight: 5  }] },
  { vol: 6.3,  ret: 4.6,  sharpe: '0.65', alloc: [{ label: '纯债',    weight: 48 }, { label: '信用债',   weight: 22 }, { label: '沪深300', weight: 10 }, { label: '港股',     weight: 8  }, { label: '商品/黄金', weight: 7  }, { label: '现金', weight: 5  }] },
  { vol: 7.8,  ret: 5.5,  sharpe: '0.71', alloc: [{ label: '纯债',    weight: 40 }, { label: '信用债',   weight: 20 }, { label: '沪深300', weight: 15 }, { label: '港股',     weight: 12 }, { label: '商品/黄金', weight: 8  }, { label: '现金', weight: 5  }] },
  { vol: 9.5,  ret: 6.3,  sharpe: '0.76', alloc: [{ label: '纯债',    weight: 32 }, { label: '信用债',   weight: 18 }, { label: '沪深300', weight: 20 }, { label: '港股',     weight: 16 }, { label: '商品/黄金', weight: 9  }, { label: '现金', weight: 5  }] },
  { vol: 11.2, ret: 7.0,  sharpe: '0.79', alloc: [{ label: '纯债',    weight: 24 }, { label: '信用债',   weight: 15 }, { label: '沪深300', weight: 25 }, { label: '港股',     weight: 20 }, { label: '商品/黄金', weight: 10 }, { label: '现金', weight: 6  }] },
  { vol: 13.0, ret: 7.6,  sharpe: '0.82', alloc: [{ label: '纯债',    weight: 16 }, { label: '信用债',   weight: 12 }, { label: '沪深300', weight: 30 }, { label: '港股',     weight: 24 }, { label: '商品/黄金', weight: 11 }, { label: '现金', weight: 7  }] },
  { vol: 15.1, ret: 8.1,  sharpe: '0.80', alloc: [{ label: '纯债',    weight: 9  }, { label: '信用债',   weight: 8  }, { label: '沪深300', weight: 34 }, { label: '港股',     weight: 28 }, { label: '商品/黄金', weight: 12 }, { label: '现金', weight: 9  }] },
  { vol: 17.5, ret: 8.5,  sharpe: '0.76', alloc: [{ label: '纯债',    weight: 4  }, { label: '信用债',   weight: 5  }, { label: '沪深300', weight: 38 }, { label: '港股',     weight: 32 }, { label: '商品/黄金', weight: 13 }, { label: '现金', weight: 8  }] },
  { vol: 20.2, ret: 8.8,  sharpe: '0.68', alloc: [{ label: '纯债',    weight: 0  }, { label: '信用债',   weight: 2  }, { label: '沪深300', weight: 43 }, { label: '港股',     weight: 36 }, { label: '商品/黄金', weight: 13 }, { label: '现金', weight: 6  }] },
];

const MC_CONSTRAINTS = [
  { label: '权益类仓位上限',     range: '≤ 30%',      color: '#3B9EFF' },
  { label: '固定收益类下限',     range: '≥ 40%',      color: '#3B9EFF' },
  { label: '组合久期约束',       range: '1.5 – 3.0',  color: '#94A3B8' },
  { label: '单资产权重上限',     range: '≤ 40%',      color: '#94A3B8' },
  { label: '商品/另类上限',      range: '≤ 15%',      color: '#94A3B8' },
  { label: '现金/流动性下限',    range: '≥ 5%',       color: '#64748B' },
];

const MC_SIM_PARAMS = [
  { key: 'n',      name: '模拟次数',         value: '100,000', unit: '次',  highlight: true  },
  { key: 'window', name: '历史收益窗口',      value: '5 年',    unit: '滚动', highlight: false },
  { key: 'corr',   name: '协方差估计方法',    value: 'Ledoit',  unit: '压缩', highlight: false },
  { key: 'rf',     name: '无风险利率',        value: '2.0%',    unit: '年化', highlight: false },
  { key: 'seed',   name: '随机种子',          value: '20260415', unit: '',   highlight: false },
];

const MC_SUMMARY = [
  { label: '前沿最优夏普',  value: '0.82', color: 'text-cyan-300',    note: '波动率 13.0%' },
  { label: '前沿最小方差',  value: '5.2%', color: 'text-[#3B9EFF]',   note: '收益 3.8%' },
  { label: '最大收益组合',  value: '8.8%', color: 'text-[#F04864]',   note: '波动率 20.2%' },
];

function _genMCScatter(): [number, number][] {
  const pts: [number, number][] = [];
  let s = 0x9E3779B9;
  for (let i = 0; i < 220; i++) {
    s = ((s ^ (s >>> 16)) * 0x45d9f3b) >>> 0;
    s = ((s ^ (s >>> 16)) * 0x45d9f3b) >>> 0;
    const vol = 4.5 + (s % 17000) / 1000;
    s = ((s ^ (s >>> 16)) * 0x45d9f3b) >>> 0;
    const noise = ((s % 2000) / 1000) - 1.0;
    const retCeiling = 1.8 + Math.pow(Math.max(0, (vol - 4.5) / 16), 0.65) * 7.2;
    const ret = Math.max(1.2, retCeiling - 0.2 + noise * 1.2);
    if (ret < retCeiling + 0.1) pts.push([parseFloat(vol.toFixed(1)), parseFloat(ret.toFixed(1))]);
  }
  return pts;
}

function openMCDialog() {
  showMCDialog.value = true;
  mcSelectedAlloc.value = null;
  mcSelectedPoint.value = null;
  nextTick(() => {
    if (!mcChartRef.value) return;
    mcChart?.dispose();
    mcChart = echarts.init(mcChartRef.value);
    const frontierData = MC_FRONTIER.map(p => [p.vol, p.ret]);
    mcChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#202431',
        borderColor: '#252A3A',
        textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 },
        formatter: (params: any) => {
          if (params.seriesIndex === 1) {
            const fp = MC_FRONTIER[params.dataIndex];
            return `<b style="color:#3B9EFF">有效前沿节点</b><br/>
              波动率: <b style="font-family:monospace;color:#94A3B8">${params.data[0]}%</b><br/>
              预期收益: <b style="font-family:monospace;color:#F04864">${params.data[1]}%</b><br/>
              Sharpe: <b style="font-family:monospace;color:#22D3EE">${fp.sharpe}</b><br/>
              <span style="color:#64748B;font-size:10px">点击查看配置明细</span>`;
          }
          return `波动率: <b style="font-family:monospace">${params.data[0]}%</b>  收益: <b style="font-family:monospace">${params.data[1]}%</b>`;
        },
      },
      grid: { top: 24, right: 20, bottom: 40, left: 54 },
      xAxis: {
        type: 'value',
        name: '年化波动率 (%)',
        nameLocation: 'middle',
        nameGap: 28,
        nameTextStyle: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' },
        min: 3,
        max: 22,
        axisLine: { lineStyle: { color: '#2E3348' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v + '%' },
        splitLine: { lineStyle: { color: '#252A3A', type: 'dashed' } },
      },
      yAxis: {
        type: 'value',
        name: '预期年化收益 (%)',
        nameLocation: 'middle',
        nameGap: 42,
        nameTextStyle: { color: '#4A5568', fontSize: 10, fontFamily: 'monospace' },
        min: 0,
        max: 11,
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v + '%' },
        splitLine: { lineStyle: { color: '#252A3A', type: 'dashed' } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          name: '随机组合',
          type: 'scatter',
          data: _genMCScatter(),
          symbolSize: 3.5,
          itemStyle: { color: '#3B5070', opacity: 0.55 },
          silent: true,
          z: 1,
        },
        {
          name: '有效前沿',
          type: 'line',
          data: frontierData,
          smooth: true,
          symbolSize: 10,
          symbol: 'circle',
          lineStyle: { color: '#3B9EFF', width: 2.5 },
          itemStyle: { color: '#3B9EFF', borderColor: '#fff', borderWidth: 1.5 },
          emphasis: { itemStyle: { color: '#22D3EE', borderColor: '#fff', borderWidth: 2, shadowBlur: 8, shadowColor: '#3B9EFF' } },
          z: 10,
        },
      ],
    });
    mcChart.on('click', 'series', (params: any) => {
      if (params.seriesIndex === 1) {
        const fp = MC_FRONTIER[params.dataIndex];
        mcSelectedAlloc.value = fp.alloc;
        mcSelectedPoint.value = { vol: fp.vol, ret: fp.ret, sharpe: fp.sharpe };
      }
    });
  });
}

function closeMCDialog() {
  showMCDialog.value = false;
  mcChart?.dispose();
  mcChart = null;
  mcSelectedAlloc.value = null;
  mcSelectedPoint.value = null;
}

// ── Risk Parity Detail Dialog ─────────────────────────────────
const showRPDialog = ref(false);
const rpChartRef = ref<HTMLElement | null>(null);
let rpChart: echarts.ECharts | null = null;

const RP_DATA = {
  assets:         ['纯债', '信用债', '沪深300', '港股', '商品/黄金', '海外债'],
  capitalWeights: [35,     20,       20,        10,     8,           7],
  riskContribs:   [17,     17,       17,        17,     16,          16],
};

const RP_PARAMS = [
  { key: 'assets',  name: '纳入资产数量',     value: '6',      note: '大类',   highlight: false },
  { key: 'window',  name: '协方差估计窗口',   value: '252',    note: '交易日', highlight: false },
  { key: 'solver',  name: '优化求解器',       value: 'SLSQP',  note: '迭代',   highlight: false },
  { key: 'tol',     name: '收敛容差',         value: '1e-8',   note: '',       highlight: false },
  { key: 'sharpe',  name: '优化后夏普比率',   value: '0.78',   note: '较均配+0.09', highlight: true  },
];

const RP_ASSET_DETAIL = [
  { name: '纯债',     capitalWeight: 35, riskContrib: 17, annVol: 2.1  },
  { name: '信用债',   capitalWeight: 20, riskContrib: 17, annVol: 3.4  },
  { name: '沪深300',  capitalWeight: 20, riskContrib: 17, annVol: 18.5 },
  { name: '港股',     capitalWeight: 10, riskContrib: 17, annVol: 22.3 },
  { name: '商品/黄金', capitalWeight: 8, riskContrib: 16, annVol: 14.8 },
  { name: '海外债',   capitalWeight: 7,  riskContrib: 16, annVol: 5.2  },
];

const RP_SUMMARY = [
  { label: '组合年化波动',  value: '6.8%',  color: 'text-[#3B9EFF]',  note: '较均配降 22%' },
  { label: '最大回撤压缩',  value: '-31%',  color: 'text-[#00C9A7]',  note: '历史 5Y 回测' },
  { label: '优化夏普比率',  value: '0.78',  color: 'text-cyan-300',   note: '较基准 +0.09' },
];

function openRPDialog() {
  showRPDialog.value = true;
  nextTick(() => {
    if (!rpChartRef.value) return;
    rpChart?.dispose();
    rpChart = echarts.init(rpChartRef.value);
    rpChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#202431',
        borderColor: '#252A3A',
        textStyle: { color: '#E8ECF4', fontFamily: 'monospace', fontSize: 11 },
        formatter: (params: any) => {
          const lines = params.map((p: any) =>
            `<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${p.color};margin-right:5px"></span>${p.seriesName}: <b style="font-family:monospace">${p.value}%</b>`
          );
          return `<b>${params[0].name}</b><br/>` + lines.join('<br/>');
        },
      },
      legend: {
        data: ['资金分配权重', '风险贡献度'],
        textStyle: { color: '#94A3B8', fontSize: 11, fontFamily: 'monospace' },
        top: 4, right: 8, itemWidth: 10, itemHeight: 10,
      },
      grid: { top: 36, right: 16, bottom: 40, left: 52 },
      xAxis: {
        type: 'category',
        data: RP_DATA.assets,
        axisLine: { lineStyle: { color: '#2E3348' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace', interval: 0 },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        max: 40,
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'monospace', formatter: (v: number) => v + '%' },
        splitLine: { lineStyle: { color: '#252A3A', type: 'dashed' } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          name: '资金分配权重',
          type: 'bar',
          data: RP_DATA.capitalWeights,
          barWidth: '28%',
          itemStyle: { color: '#3B9EFF', opacity: 0.6, borderRadius: [3, 3, 0, 0] },
          label: { show: true, position: 'top', color: '#64748B', fontSize: 10, fontFamily: 'monospace', formatter: (p: any) => p.value + '%' },
        },
        {
          name: '风险贡献度',
          type: 'bar',
          data: RP_DATA.riskContribs,
          barWidth: '28%',
          itemStyle: { color: '#00C9A7', borderRadius: [3, 3, 0, 0] },
          label: { show: true, position: 'top', color: '#00C9A7', fontSize: 10, fontFamily: 'monospace', formatter: (p: any) => p.value + '%' },
        },
      ],
    });
  });
}

function closeRPDialog() {
  showRPDialog.value = false;
  rpChart?.dispose();
  rpChart = null;
}

const DECISION_TIMELINE = computed(() => {
  const events: Array<{ time: string; event: string; detail: string; color: string }> = [];
  const now = new Date();
  const fmt = (d: Date) => d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  // Meeting created
  events.push({ time: currentMeeting.value?.date ?? '2026-04-15', event: '会议创建', detail: `秘书创建会议，设定投票窗口`, color: '#3B9EFF' });
  // Votes arriving
  for (const [id, sub] of Object.entries(memberSubmissions)) {
    const member = MEMBERS_DATA.find(m => m.id === id);
    events.push({ time: sub.submittedAt, event: `${member?.name ?? '委员'} 提交投票`, detail: `已提交问卷观点${sub.riskFlag ? '（含尾部风险标记）' : ''}`, color: sub.riskFlag ? '#3B9EFF' : '#34C759' });
  }
  // Decision
  if (deptAllocationDecision.value) {
    events.push({ time: fmt(now), event: '主任委员提交决策', detail: '配置决策已最终确认', color: '#3B9EFF' });
  }
  return events;
});

function openModelCenter() {
  const url = new URL('model-center', window.location.href);
  window.open(url.href, '_blank', 'noopener,noreferrer');
}

// ── Step 3: Chairman Decision Matrix + Product Guidance ───────

type BondGrade = '高' | '中' | '低';

const BOND_GRADE_DURATION: Record<BondGrade, string> = {
  高: '3-5年',
  中: '1-3年',
  低: '0-1年',
};

const BOND_GRADE_LABEL: Record<BondGrade, string> = {
  高: '3-5Y (长久期策略)',
  中: '1-3Y (中枢久期策略)',
  低: '0-1Y (短久期/货币策略)',
};

const PRODUCT_BOND_LABELS: Record<string, string> = { low: '低波久期', mid: '中波久期', hybrid: '混合久期' };

/** 主任委员顶层配置决策 */
const chairDecision = reactive({
  bondGrade: '中' as BondGrade,
  perProductBondGrade: { low: '中' as BondGrade, mid: '中' as BondGrade, hybrid: '中' as BondGrade },
  equityGrade: 3,
  equityMix: { 红利: 40, 成长: 35, 价值: 25 } as Record<'红利' | '成长' | '价值', number>,
  altNotes: '',
});

type EquitySubKey = '红利' | '港股' | '其他权益' | 'REITS' | '黄金';

const EQUITY_SUB_KEYS: EquitySubKey[] = ['红利', '港股', '其他权益', 'REITS', '黄金'];

const PRODUCT_EQUITY_COEFF: Record<string, Record<EquitySubKey, number>> = {
  low:    { 红利: 0.50, 港股: 0.15, 其他权益: 0.10, REITS: 0.10, 黄金: 0.15 },
  mid:    { 红利: 0.45, 港股: 0.20, 其他权益: 0.15, REITS: 0.10, 黄金: 0.10 },
  hybrid: { 红利: 0.35, 港股: 0.20, 其他权益: 0.20, REITS: 0.15, 黄金: 0.10 },
};

/** 权益明细之和（用于校验） */
const equityMixSum = computed(() =>
  chairDecision.equityMix['红利'] + chairDecision.equityMix['成长'] + chairDecision.equityMix['价值'],
);

interface ProductGuidanceRow {
  id: string;
  name: string;
  tag: string;
  color: string;
  prevBond: number;
  prevEquity: number;
  prevAlt: number;
  prevLiquidity: number;
  bond: number;
  equity: number;
  equitySub: Record<EquitySubKey, number>;
  alt: number;
  altText: string;
  liquidity: number;
}

const productGuidances = reactive<ProductGuidanceRow[]>([
  { id: 'low',    name: '固收+中低波', tag: 'LOW-VOL', color: '#3B9EFF', prevBond: 75, prevEquity: 10, prevAlt: 5, prevLiquidity: 10, bond: 0, equity: 0, equitySub: { 红利: 0, 港股: 0, 其他权益: 0, REITS: 0, 黄金: 0 }, alt: 0, altText: '维持一档风险预算', liquidity: 0 },
  { id: 'mid',    name: '固收+中波', tag: 'MID-VOL', color: '#3B9EFF', prevBond: 58, prevEquity: 25, prevAlt: 8, prevLiquidity:  9, bond: 0, equity: 0, equitySub: { 红利: 0, 港股: 0, 其他权益: 0, REITS: 0, 黄金: 0 }, alt: 0, altText: '标配REITS+黄金', liquidity: 0 },
  { id: 'hybrid', name: '混合绝对收益', tag: 'HYBRID',  color: '#3B9EFF', prevBond: 38, prevEquity: 45, prevAlt: 8, prevLiquidity:  9, bond: 0, equity: 0, equitySub: { 红利: 0, 港股: 0, 其他权益: 0, REITS: 0, 黄金: 0 }, alt: 0, altText: '增配REITS+关注CTA', liquidity: 0 },
]);

/** 是否已点击"计算产品指引"完成自动填充 */
const guidanceCalculated = ref(false);

const showHistoryDiff = ref(false);

const PREV_SNAPSHOT = {
  bondGrade: '中' as BondGrade,
  bondDuration: '1-3年',
  equityGrade: 3,
  equityLabel: '中性',
  perProductBondGrade: { low: '低' as BondGrade, mid: '中' as BondGrade, hybrid: '中' as BondGrade },
  products: [
    { id: 'low', name: '固收+中低波', bond: 75, equity: 10, equitySub: { 红利: 5.0, 港股: 1.5, 其他权益: 1.0, REITS: 1.0, 黄金: 1.5 }, alt: 5, altText: '维持一档风险预算', liquidity: 10 },
    { id: 'mid', name: '固收+中波', bond: 58, equity: 25, equitySub: { 红利: 11.3, 港股: 5.0, 其他权益: 3.8, REITS: 2.5, 黄金: 2.5 }, alt: 8, altText: '标配REITS+黄金', liquidity: 9 },
    { id: 'hybrid', name: '混合绝对收益', bond: 38, equity: 45, equitySub: { 红利: 15.8, 港股: 9.0, 其他权益: 9.0, REITS: 6.8, 黄金: 4.5 }, alt: 8, altText: '增配REITS+关注CTA', liquidity: 9 },
  ],
};

function diffBadge(cur: number, prev: number, suffix = '%'): string | null {
  const d = cur - prev;
  if (Math.abs(d) < 0.01) return null;
  return (d > 0 ? '+' : '') + d.toFixed(1) + suffix;
}
function diffBondGrade(cur: BondGrade, prev: BondGrade): string | null {
  if (cur === prev) return null;
  return `由${prev}调${cur}`;
}

/** 债券档位 × 产品类型 → 基准固收仓位（索引: 高=0 中=1 低=2） */
const BASE_BOND: Record<string, [number, number, number]> = {
  low:    [78, 72, 65],
  mid:    [65, 58, 50],
  hybrid: [45, 38, 30],
};
/** 债券档位 × 产品类型 → 基准权益仓位 */
const BASE_EQUITY: Record<string, [number, number, number]> = {
  low:    [10, 12, 15],
  mid:    [20, 25, 30],
  hybrid: [38, 45, 55],
};

function calcProductGuidances() {
  const bgIdx: Record<BondGrade, number> = { 高: 0, 中: 1, 低: 2 };
  const eqAdj = (chairDecision.equityGrade - 3) * 5;
  for (const row of productGuidances) {
    const idx = bgIdx[chairDecision.perProductBondGrade[row.id] ?? chairDecision.bondGrade];
    const equity   = Math.max(0, Math.min(100, BASE_EQUITY[row.id][idx] + eqAdj));
    const bond     = Math.max(0, Math.min(100, BASE_BOND[row.id][idx]   - eqAdj));
    const alt      = row.prevAlt;
    const liquidity = Math.max(0, 100 - bond - equity - alt);
    row.bond      = bond;
    row.equity    = equity;
    row.alt       = alt;
    row.liquidity = liquidity;
    for (const k of EQUITY_SUB_KEYS) {
      row.equitySub[k] = +(equity * PRODUCT_EQUITY_COEFF[row.id][k]).toFixed(1);
    }
  }
  guidanceCalculated.value = true;
}

/** 规则校验：返回所有红线原因（空数组=通过） */
const validationErrors = computed((): string[] => {
  const errs: string[] = [];
  if (equityMixSum.value !== 100) {
    errs.push(`权益明细之和为 ${equityMixSum.value}%，必须等于 100%（当前差 ${100 - equityMixSum.value}%）`);
  }
  if (guidanceCalculated.value) {
    for (const row of productGuidances) {
      const total = row.bond + row.equity + row.alt + row.liquidity;
      if (total < 95 || total > 105) {
        errs.push(`【${row.name}】各资产合计 ${total}%，偏离 100% 超出 ±5% 容差`);
      }
    }
  }
  return errs;
});

const canSubmitDecision = computed(() =>
  guidanceCalculated.value && validationErrors.value.length === 0,
);

const showValidationToast = ref(false);
const decisionSubmitted = ref(false);

async function handleSubmitDecision() {
  if (!canSubmitDecision.value) {
    showValidationToast.value = true;
    setTimeout(() => { showValidationToast.value = false; }, 6000);
    return;
  }
  const hybrid = productGuidances.find(p => p.id === 'hybrid');
  const payload = {
    period: meetingList[0]?.name ?? '2026 Q2',
    decidedAt: new Date().toISOString(),
    decidedBy: '混合投资委员会主任委员',
    bondGrade: chairDecision.bondGrade,
    bondDuration: BOND_GRADE_DURATION[chairDecision.bondGrade],
    equityGrade: chairDecision.equityGrade,
    equityGradeLabel: SCORE_LABELS[chairDecision.equityGrade],
    equityMix: { ...chairDecision.equityMix },
    altNotes: chairDecision.altNotes,
    products: productGuidances.map(p => ({
      id: p.id, name: p.name,
      bond: p.bond, equity: p.equity, equitySub: { ...p.equitySub }, alt: p.alt, altText: p.altText, liquidity: p.liquidity,
    })),
  };
  deptAllocationDecision.value = payload;

  // 调用后端 API 持久化决议
  const meetingId = resolveVotingMeetingId();
  if (meetingId && !skipCommitteeHttp()) {
    try {
      await http.post(`/v1/committee/meetings/${meetingId}/resolution`, {
        bond_grade: chairDecision.bondGrade,
        bond_duration: BOND_GRADE_DURATION[chairDecision.bondGrade],
        equity_grade: chairDecision.equityGrade,
        equity_grade_label: SCORE_LABELS[chairDecision.equityGrade],
        equity_mix: { ...chairDecision.equityMix },
        alt_notes: chairDecision.altNotes,
        products: productGuidances.map(p => ({
          product_id: p.id,
          product_name: p.name,
          bond_grade: p.bondGrade ?? chairDecision.bondGrade,
          bond_pct: p.bond,
          equity_pct: p.equity,
          equity_sub: { ...p.equitySub },
          alt_pct: p.alt,
          liquidity_pct: p.liquidity,
        })),
      });
    } catch (err) {
      console.error('[Committee] 决议提交失败:', err);
    }
  }

  const activeMeeting = meetingList.find(m => m.status === '进行中');
  if (activeMeeting) {
    activeMeeting.status = '已结束';
    activeMeeting.decision =
      `决议：权益${SCORE_LABELS[chairDecision.equityGrade]}，` +
      `固收${chairDecision.bondGrade}久期（${BOND_GRADE_DURATION[chairDecision.bondGrade]}），` +
      `混合产品权益比例 ${hybrid?.equity ?? '-'}%`;
  }
  decisionSubmitted.value = true;
  isSynced.value = true;
  syncedAt.value = new Date().toLocaleString('zh-CN', { hour12: false });
}

// ── Meeting Management Drawer (秘书专属) ─────────────────────
const MEETING_TYPES = ['月度', '季度', '年度'] as const;
type MeetingType = (typeof MEETING_TYPES)[number];

const PERIOD_OPTIONS: Record<MeetingType, string[]> = {
  月度: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
  季度: ['Q1','Q2','Q3','Q4'],
  年度: ['上半年度','下半年度','年度'],
};

const MEETING_STATUS_LIST = ['待召开', '进行中', '已结束', '已取消'] as const;

interface MeetingItem {
  id: number;
  name: string;
  date: string;
  time: string;
  location: string;
  status: string;
  decision: string;
  meetingType: MeetingType;
  meetingPeriod: string;
  meetingYear: number;
  voteDeadline: string | null;
  voteForcedClosed: boolean;
  preMaterials: string;
  minutesTemplate: string;
}

const showMeetingDrawer = ref(false);
const showVoteConfirm = ref(false);

/** 将后端 MeetingStatus 映射为前端中文标签 */
function mapMeetingStatus(status: string): string {
  switch (status) {
    case 'draft': return '筹备中';
    case 'voting': return '进行中';
    case 'published': return '已结束';
    default: return status;
  }
}

/** 将后端 MeetingType 映射为前端会议类型标签 */
function mapMeetingType(type: string): MeetingType {
  return type === 'ficc' ? '固定收益' : '季度';
}

/** 从标题或会议编码中提取季度（Q1/Q2/Q3/Q4） */
function extractQuarter(text: string): string {
  const match = text.match(/Q([1-4])/);
  return match ? `Q${match[1]}` : 'Q4';
}

/** 从标题或会议编码中提取年份 */
function extractYear(text: string): number {
  const match = text.match(/(\d{4})/);
  return match ? parseInt(match[1], 10) : new Date().getFullYear();
}

/** 将后端 API 返回的会议转换为前端 MeetingItem 格式 */
function toMeetingItem(raw: {
  id: number; meeting_code: string; title: string;
  type: string; status: string; scheduled_at: string | null;
  created_by: number; created_at: string; updated_at: string;
}): MeetingItem {
  const scheduledAt = raw.scheduled_at ? new Date(raw.scheduled_at) : null;
  const dateStr = scheduledAt
    ? `${scheduledAt.getFullYear()}.${String(scheduledAt.getMonth() + 1).padStart(2, '0')}.${String(scheduledAt.getDate()).padStart(2, '0')}`
    : '—';
  const timeStr = scheduledAt
    ? `${String(scheduledAt.getHours()).padStart(2, '0')}:${String(scheduledAt.getMinutes()).padStart(2, '0')}`
    : '—';
  const quarter = extractQuarter(raw.title || raw.meeting_code);
  const year = extractYear(raw.title || raw.meeting_code);

  return {
    id: raw.id,
    name: raw.title,
    date: dateStr,
    time: timeStr,
    location: '总部3楼会议室',
    status: mapMeetingStatus(raw.status),
    decision: '',
    meetingType: mapMeetingType(raw.type),
    meetingPeriod: quarter,
    meetingYear: year,
    voteDeadline: null,
    voteForcedClosed: false,
    preMaterials: '',
    minutesTemplate: '',
  };
}

/** 后端 GET /v1/committee/meetings 行含 `title`；本地 MOCK_MEETINGS 用 `name`，不可走 toMeetingItem */
function isCommitteeMeetingApiRow(raw: unknown): raw is {
  id: number;
  meeting_code: string;
  title: string;
  type: string;
  status: string;
  scheduled_at: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
} {
  return (
    typeof raw === 'object' &&
    raw !== null &&
    typeof (raw as { title?: unknown }).title === 'string'
  );
}

const meetingList = reactive<MeetingItem[]>([]);

/** 从后端加载会议列表 */
const MOCK_MEETINGS: MeetingItem[] = [
  { id: 1, name: '混合投委会 2025 Q4 配置决策会议', date: '2025.10.15', time: '14:00-16:00', location: '总部8楼投委会议室', status: '已归档', decision: '决议：权益中性偏乐观，固收中久期，混合产品权益比例 30%', meetingType: '季度', meetingPeriod: 'Q4', meetingYear: 2025, voteDeadline: null, voteForcedClosed: false, preMaterials: '', minutesTemplate: '' },
  { id: 2, name: '混合投委会 2026 Q1 配置决策会议', date: '2026.01.20', time: '14:00-16:00', location: '总部8楼投委会议室', status: '已结束', decision: '决议：权益中性，固收中低久期，混合产品权益比例 25%', meetingType: '季度', meetingPeriod: 'Q1', meetingYear: 2026, voteDeadline: null, voteForcedClosed: false, preMaterials: '', minutesTemplate: '' },
  { id: 3, name: '混合投委会 2026 Q2 投资策略与TAA目标决议', date: '2026.04.15', time: '14:00-16:00', location: '总部8楼投委会议室', status: '进行中', decision: '', meetingType: '季度', meetingPeriod: 'Q2', meetingYear: 2026, voteDeadline: '2026-04-15T16:00', voteForcedClosed: false, preMaterials: '', minutesTemplate: '' },
];

async function loadMeetings() {
  const items = await useApi(
    () => http.get('/v1/committee/meetings', { params: { type: 'mixed' } }),
    MOCK_MEETINGS,
  );
  const parsed: MeetingItem[] = Array.isArray(items)
    ? items.map((raw) =>
        isCommitteeMeetingApiRow(raw) ? toMeetingItem(raw) : (raw as MeetingItem),
      )
    : [];
  meetingList.length = 0;
  meetingList.push(...parsed);
}

function buildUniqueMeetingCode(now: Date): string {
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  const quarter = m <= 3 ? 'Q1' : m <= 6 ? 'Q2' : m <= 9 ? 'Q3' : 'Q4';
  const stamp = `${String(now.getDate()).padStart(2, '0')}${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
  const rand = Math.floor(Math.random() * 100).toString().padStart(2, '0');
  return `IC-${y}-${quarter}-${stamp}${rand}`;
}

// ── 新增会议（自动标题，无弹窗）─────────────────────────────────
async function quickCreateMeeting() {
  const now = new Date();
  const m = now.getMonth() + 1;
  const year = now.getFullYear();
  let title: string;
  if (m === 12 || m === 1 || m === 2) {
    title = `${m === 12 ? year : year - 1}年度配置决策会议`;
  } else if (m >= 3 && m <= 5) {
    title = `${year} Q1 配置决策会议`;
  } else if (m >= 6 && m <= 8) {
    title = `${year} Q2 配置决策会议`;
  } else {
    title = `${year} Q3 配置决策会议`;
  }
  const payload = {
    title: `混合投资委员会 ${title}`,
    type: 'mixed',
  };
  try {
    // 发生唯一键冲突时自动重试，避免页面刷新后本地计数器重置导致撞码
    for (let i = 0; i < 3; i++) {
      try {
        await http.post('/v1/committee/meetings', {
          meeting_code: buildUniqueMeetingCode(new Date()),
          ...payload,
        });
        await loadMeetings();
        return;
      } catch (e: any) {
        const detail = e?.response?.data?.detail ?? '';
        const msg = String(detail);
        if (msg.includes('UNIQUE') || msg.includes('duplicate') || e?.response?.status === 409) {
          continue;
        }
        throw e;
      }
    }
    alert('创建会议失败：会议编码重复，请重试。');
  } catch (err: any) {
    const detail = err?.response?.data?.detail;
    console.error('[Committee] 创建会议失败:', err);
    alert(`创建会议失败：${detail ? String(detail) : '请检查后端服务'}`);
  }
}

// ── 编辑会议 Drawer ──────────────────────────────────────────
const showEditMeetingDrawer = ref(false);
const editingMeetingId = ref<number | null>(null);
const editingMeetingForm = reactive({
  meetingType: '季度' as MeetingType,
  meetingPeriod: 'Q3',
  meetingYear: 2026,
  date: '',
  time: '',
  location: '',
  status: '待召开' as string,
  decision: '',
  voteDeadline: '',
  voteForcedClosed: false,
  preMaterials: '',
  minutesTemplate: '',
});

const editingMeetingPeriodOptions = computed(() => PERIOD_OPTIONS[editingMeetingForm.meetingType]);
const editingMeetingTitle = computed(() =>
  `混合投资委员会 ${editingMeetingForm.meetingYear}年 ${editingMeetingForm.meetingPeriod} 配置决策会议`,
);

function openEditMeeting(id: number) {
  const item = meetingList.find(m => m.id === id);
  if (!item) return;
  editingMeetingId.value = id;
  Object.assign(editingMeetingForm, {
    meetingType: item.meetingType,
    meetingPeriod: item.meetingPeriod,
    meetingYear: item.meetingYear,
    date: item.date.replace(/\./g, '-'),
    time: item.time,
    location: item.location,
    status: item.status,
    decision: item.decision,
    voteDeadline: item.voteDeadline ?? '',
    voteForcedClosed: item.voteForcedClosed,
    preMaterials: item.preMaterials,
    minutesTemplate: item.minutesTemplate,
  });
  showEditMeetingDrawer.value = true;
}

function saveEditMeeting() {
  if (editingMeetingId.value === null) return;
  const item = meetingList.find(m => m.id === editingMeetingId.value);
  if (!item) return;
  Object.assign(item, {
    name: editingMeetingTitle.value,
    meetingType: editingMeetingForm.meetingType,
    meetingPeriod: editingMeetingForm.meetingPeriod,
    meetingYear: editingMeetingForm.meetingYear,
    date: editingMeetingForm.date ? editingMeetingForm.date.replace(/-/g, '.') : item.date,
    time: editingMeetingForm.time,
    location: editingMeetingForm.location,
    status: editingMeetingForm.status,
    decision: editingMeetingForm.decision,
    voteDeadline: editingMeetingForm.voteDeadline || null,
    voteForcedClosed: editingMeetingForm.voteForcedClosed,
    preMaterials: editingMeetingForm.preMaterials,
    minutesTemplate: editingMeetingForm.minutesTemplate,
  });
  showEditMeetingDrawer.value = false;
}

async function deleteMeeting(id: number) {
  if (!isSecretary.value) return;
  const target = meetingList.find(m => m.id === id);
  if (!target || target.status !== '进行中') return;
  if (!window.confirm('确定删除该「进行中」会议？此操作不可撤销。')) return;

  if (!skipCommitteeHttp()) {
    try {
      await http.delete(`/v1/committee/meetings/${id}`);
    } catch (err: unknown) {
      console.error('[Committee] 删除会议失败:', err);
      window.alert('删除失败，请稍后重试或检查后端服务。');
      return;
    }
  }

  const idx = meetingList.findIndex(m => m.id === id);
  if (idx !== -1) meetingList.splice(idx, 1);
  if (currentMeetingId.value === id) currentMeetingId.value = null;
}

// ── 全局投票截止控制（当前进行中会议）───────────────────────
const voteForcedClosed = ref(false);
const voteDeadlineInput = ref('');
const nowTick = ref(new Date());
let nowTickInterval: ReturnType<typeof setInterval> | null = null;

const isVoteOpen = computed(() => {
  if (voteForcedClosed.value) return false;
  if (!voteDeadlineInput.value) return true;
  return new Date(voteDeadlineInput.value) > nowTick.value;
});

const voteCountdownDisplay = computed(() => {
  if (!voteDeadlineInput.value || voteForcedClosed.value) return '';
  const diff = new Date(voteDeadlineInput.value).getTime() - nowTick.value.getTime();
  if (diff <= 0) return '已过期';
  const totalMin = Math.floor(diff / 60000);
  if (totalMin < 60) return `${totalMin}分钟`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return m > 0 ? `${h}小时${m}分钟` : `${h}小时`;
});

function forceCloseVote() { voteForcedClosed.value = true; }
function reopenVote() { voteForcedClosed.value = false; }

/** 允许委员在投票窗口开放期间重新编辑已提交的问卷 */
function clearMemberSubmission() {
  const id = SELF_MEMBER_ID.value;
  if (!id || !isVoteOpen.value) return;
  const sub = memberSubmissions[id];
  if (sub) {
    Object.assign(FORM_SECTION_A, sub.sectionA);
    Object.assign(FORM_SECTION_B, sub.sectionB);
    Object.assign(FORM_SECTION_C, sub.sectionC);
    formCoreView.value = sub.coreView;
    formRiskFlag.value = sub.riskFlag;
  }
  delete memberSubmissions[id];
}

// ── Step 4: Recording & Signing ───────────────────────────────
type MinuteState = 'draft' | 'pending' | 'ready';
const minuteState = ref<MinuteState>('draft');

const WAVE_COUNT = 30;
const waveformBars = ref<number[]>(Array.from({ length: WAVE_COUNT }, () => Math.random() * 32 + 6));

type RecState = 'idle' | 'recording' | 'paused' | 'finished';
const recState = ref<RecState>('idle');
const recSeconds = ref(0);
const recInterval = ref<ReturnType<typeof setInterval> | null>(null);

const recTimeDisplay = computed(() => {
  const h = Math.floor(recSeconds.value / 3600).toString().padStart(2, '0');
  const m = Math.floor((recSeconds.value % 3600) / 60).toString().padStart(2, '0');
  const s = (recSeconds.value % 60).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
});

const isRecording = computed(() => recState.value === 'recording');
const recordingStopped = computed(() => recState.value === 'finished');
const recordingTimeDisplay = recTimeDisplay;

function recTick() {
  recSeconds.value++;
  waveformBars.value = Array.from({ length: WAVE_COUNT }, () => Math.random() * 36 + 6);
}

function recStart() {
  if (recState.value === 'recording' || recState.value === 'finished') return;
  if (recState.value === 'idle') recSeconds.value = 0;
  recState.value = 'recording';
  aiPointsVisible.value = 0;
  if (recInterval.value) clearInterval(recInterval.value);
  recInterval.value = setInterval(recTick, 1000);
}

function recPause() {
  if (recState.value !== 'recording') return;
  recState.value = 'paused';
  if (recInterval.value) { clearInterval(recInterval.value); recInterval.value = null; }
}

function recStop() {
  if (recState.value !== 'recording' && recState.value !== 'paused') return;
  recState.value = 'finished';
  if (recInterval.value) { clearInterval(recInterval.value); recInterval.value = null; }
  waveformBars.value = Array.from({ length: WAVE_COUNT }, () => Math.random() * 20 + 8);
  let idx = 0;
  const iv = setInterval(() => {
    if (idx < AI_SUMMARY_POINTS.length) { aiPointsVisible.value = idx + 1; idx++; }
    else clearInterval(iv);
  }, 600);
}

function startRecording() { recStart(); }
function stopRecording() { recStop(); }

const aiPointsVisible = ref(0);
const AI_SUMMARY_POINTS = [
  '当前宏观环境支持适度提升权益配置比例，但需控制下行风险敞口',
  '利率下行趋势下，固收资产仍具配置价值，建议适度拉长久期',
  '黄金受地缘风险支撑，维持标配，关注美联储政策转向信号',
  '信用利差处于历史低位，需警惕信用事件风险，维持高等级配置',
  '建议加强组合流动性管理，预留充足安全垫应对潜在赎回压力',
  '委员会一致同意2026 Q3保持稳健偏积极的资产配置策略',
];

const chairmanInstruction = ref('');
const isIssued = ref(false);
const issuingLoading = ref(false);
const issuedTime = ref('');

function applyAIToInstruction() {
  const points = AI_SUMMARY_POINTS.slice(0, aiPointsVisible.value);
  if (points.length === 0) return;
  const suffix = points.map((p, i) => `${i + 1}. ${p}`).join('\n');
  chairmanInstruction.value = chairmanInstruction.value
    ? chairmanInstruction.value + '\n\n' + suffix
    : suffix;
}

function handleIssue() {
  if (isIssued.value || issuingLoading.value) return;
  if (!decisionSubmitted.value) return;
  issuingLoading.value = true;
  setTimeout(() => {
    issuingLoading.value = false;
    isIssued.value = true;
    issuedTime.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    const activeMeeting = meetingList.find(m => m.status === '已结束' || m.status === '进行中');
    if (activeMeeting) {
      activeMeeting.status = '已归档';
    }
  }, 2000);
}

// ── Tab 切换时用 nextTick 重新初始化原生 ECharts 实例 ──────────────
watch(activeTab, async (tab) => {
  await nextTick();
  if (tab === 'market_macro') {
    initGuidanceChart();
  }
  if (tab === 'post_mortem') {
    initPositionChart();
  }
});

onMounted(async () => {
  console.log(
    '%c🚀 [CommitteeView]',
    'color:#3B9EFF;font-weight:bold;font-size:12px',
    'onMounted → 加载会议列表 + 投委会数据',
  );
  await loadMeetings();
  void fetchCommitteePageData();
  void loadMixedSubmissions();
  void loadHistoryVotes();
  nowTickInterval = setInterval(() => { nowTick.value = new Date(); }, 30000);
  const activeMeeting = meetingList.find(m => m.status === '进行中');
  if (activeMeeting) {
    currentMeetingId.value = activeMeeting.id;
  }
  // market_macro 为默认 Tab，需要 nextTick 等待 v-if DOM 完成渲染
  await nextTick();
  initGuidanceChart();
  checkScrollable();
  window.addEventListener('resize', handleResize);
  window.addEventListener('scroll', onWindowScroll, { passive: true });
  document.addEventListener('scroll', onWindowScroll, { passive: true, capture: true });
  window.addEventListener('wheel', onScrollIntent, { passive: true });
  window.addEventListener('touchmove', onScrollIntent, { passive: true });
  window.addEventListener('keydown', onKeyScrollIntent);
  window.addEventListener('scrollend', onMainScrollEnd, { passive: true });
  if (mainScrollRef.value) {
    mainScrollRef.value.addEventListener('scrollend', onMainScrollEnd, { passive: true });
  }
});

watch(activeRole, () => {
  // eslint-disable-next-line no-console
  console.log('%c🚀 [CommitteeView]', 'color:#3B9EFF;font-weight:bold', 'activeRole 变化 → 重新拉取投委会数据');
  void fetchCommitteePageData();
});

onUnmounted(() => {
  if (recInterval.value) clearInterval(recInterval.value);
  if (nowTickInterval) clearInterval(nowTickInterval);
  positionChart?.dispose();
  positionChart = null;
  guidanceChart?.dispose();
  guidanceChart = null;
  sparklineModalChart?.dispose();
  sparklineModalChart = null;
  blDialogChart?.dispose();
  blDialogChart = null;
  mcChart?.dispose();
  mcChart = null;
  rpChart?.dispose();
  rpChart = null;
  window.removeEventListener('resize', handleResize);
  window.removeEventListener('scroll', onWindowScroll);
  document.removeEventListener('scroll', onWindowScroll, true);
  window.removeEventListener('wheel', onScrollIntent);
  window.removeEventListener('touchmove', onScrollIntent);
  window.removeEventListener('keydown', onKeyScrollIntent);
  window.removeEventListener('scrollend', onMainScrollEnd);
  if (mainScrollRef.value) {
    mainScrollRef.value.removeEventListener('scrollend', onMainScrollEnd);
  }
  if (navAutoCollapseTimer !== null) {
    window.clearTimeout(navAutoCollapseTimer);
    navAutoCollapseTimer = null;
  }
});
</script>

<style scoped>
.am-title-l2 {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.am-title-bar {
  width: 4px;
  height: 16px;
  border-radius: 9999px;
  background: #3B9EFF;
  flex-shrink: 0;
}
</style>
