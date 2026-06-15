<template>
  <div class="flex flex-col h-full bg-[#161922] text-[#E8ECF4] overflow-hidden p-4 space-y-3">

    <!-- ═══ PORTAL: FICC 会议选择中心 ═══ -->
    <div v-if="currentMeetingId == null" class="flex-1 flex flex-col items-center justify-center space-y-6">
      <div class="text-center space-y-2">
        <div class="w-2 h-12 bg-[#3B9EFF] rounded-sm mx-auto shadow-[0_0_24px_rgba(59,158,255,0.5)]"></div>
        <h1 class="text-xl font-bold text-white tracking-wider mt-3">FICC 投委会会议中心</h1>
        <p class="text-[13px] font-mono text-[#64748B]">FICC Investment Committee Meeting Portal</p>
      </div>
      <div class="w-full max-w-2xl space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider">全部会议 ({{ ficcMeetingList.length }})</span>
          <button v-if="isSecretary" @click="handleQuickCreateAndEnter"
            class="text-[13px] px-3 py-1.5 rounded-lg border border-[#3B9EFF]/25 bg-[#3B9EFF]/10 text-[#3B9EFF] hover:bg-[#3B9EFF]/18 transition-colors flex items-center gap-1.5">
            <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div> 一键新增
          </button>
        </div>
        <div class="space-y-2 max-h-[50vh] overflow-y-auto no-scrollbar">
          <div v-for="m in ficcMeetingList" :key="m.id"
            @click="enterMeeting(m.id)"
            class="bg-[#202431] border rounded-xl p-4 cursor-pointer hover:border-[#3B9EFF]/40 transition-all duration-200 group"
            :class="m.status === '进行中' ? 'border-[#3B9EFF]/30' : 'border-[#252A3A]'">
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
                <span :class="cn('text-[11px] font-mono px-2 py-1 rounded border',
                  m.status === '进行中' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]' :
                  m.status === '已归档' ? 'bg-[#6B7280]/10 border-[#2E3348] text-[#64748B]' :
                  m.status === '已结束' ? 'bg-[#00C9A7]/10 border-[#00C9A7]/25 text-[#00C9A7]' :
                  'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]')">
                  {{ m.status }}
                </span>
                <button
                  v-if="isSecretary && m.status === '进行中'"
                  type="button"
                  @click.stop="deleteFiccMeeting(m.id)"
                  class="text-[11px] font-mono px-2 py-1 rounded border border-[#F04864]/30 bg-[#F04864]/8 text-[#F97316] hover:bg-[#F04864]/15 hover:border-[#F04864]/45 transition-colors shrink-0"
                >
                  删除
                </button>
                <div class="w-0.5 h-4 rounded-full bg-[#4A5568] group-hover:bg-[#3B9EFF] transition-colors shrink-0"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ MEETING DETAIL ═══ -->
    <template v-else>

    <!-- ═══ HEADER ═══ -->
    <div class="bg-gradient-to-r from-[#202431] to-[#1A1E2B] border border-[#2E3348] rounded-xl px-5 py-3.5 shrink-0 flex justify-between items-center shadow-[0_4px_24px_rgba(0,0,0,0.5)]">
      <div class="flex items-center space-x-4">
        <div class="w-1.5 h-8 bg-[#3B9EFF] rounded-sm shadow-[0_0_10px_rgba(59,158,255,0.3)] shrink-0"></div>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-base font-bold text-white tracking-wider">FICC 投资委员会</h2>
            <button @click="backToList" class="text-[11px] font-mono px-2 py-0.5 rounded border border-[#3B9EFF]/25 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 transition-colors flex items-center gap-1">
              切换会议
            </button>
            <button v-if="isSecretary" @click="handleQuickCreateAndEnter" class="text-[11px] font-mono px-2.5 py-0.5 rounded-lg border border-[#3B9EFF]/35 bg-[#3B9EFF]/12 text-[#3B9EFF] hover:bg-[#3B9EFF]/22 hover:border-[#3B9EFF]/55 transition-all flex items-center gap-1.5 shadow-[0_0_12px_rgba(59,158,255,0.15)]">
              <div class="w-0.5 h-3 bg-current rounded-sm shrink-0"></div> 一键新增会议
            </button>
            <span v-if="isViewingArchived" class="text-[11px] font-mono px-2 py-0.5 rounded border border-[#64748B]/25 bg-[#64748B]/10 text-[#64748B]">只读 · 历史归档</span>
          </div>
          <p class="text-xs text-[#94A3B8] mt-0.5 font-mono uppercase tracking-widest">{{ currentMeeting?.name ?? 'FICC · 固定收益与货币市场策略决议' }}</p>
        </div>
      </div>
      <div class="text-right space-y-2">
        <div class="flex items-center justify-end gap-2">
          <!-- Mock 切换开关 -->
          <div class="flex items-center gap-2 border border-[#2E3348] rounded-lg px-2.5 py-1 bg-[#161922]">
            <span class="text-[11px] font-mono" :class="isGlobalMock ? 'text-[#3B9EFF]' : 'text-[#34C759]'">
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
          <div class="flex items-center gap-1.5 border border-[#2E3348] rounded-lg px-2.5 py-1 bg-[#161922]">
            <span class="text-xs font-mono text-[#4A5568]">当前视角</span>
            <span :class="cn('text-xs font-mono font-bold px-1.5 py-1 rounded border',
              isSecretary ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]' :
              isChairman ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]' :
              'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]')">
              {{ isSecretary ? '秘书' : isChairman ? '主任委员' : '委员' }}
            </span>
          </div>
          <!-- Recording Control (State Machine: idle / recording / paused / finished) -->
          <div class="flex items-center gap-1.5 border border-[#2E3348] rounded-lg px-2 py-1 bg-[#161922]">
            <span class="text-[13px] font-mono tabular-nums min-w-[52px] text-center"
              :class="recordState === 'recording' ? 'text-[#FF3B30] animate-pulse' : recordState === 'paused' ? 'text-[#3B9EFF]' : recordState === 'finished' ? 'text-[#3B9EFF]' : 'text-[#4A5568]'"
            >{{ recordingTimeDisplay }}</span>
            <div class="w-px h-4 bg-[#2E3348]"></div>
            <button @click="startRecording"
              :disabled="recordState === 'recording'"
              :class="cn('w-7 h-7 flex items-center justify-center rounded transition-colors',
                recordState === 'recording' ? 'opacity-40 cursor-not-allowed' : 'hover:bg-[#FF3B30]/15 cursor-pointer')"
            >
              <span class="w-2.5 h-2.5 rounded-full" :class="recordState === 'idle' || recordState === 'paused' ? 'bg-[#FF3B30]' : 'bg-[#FF3B30]/40'"></span>
            </button>
            <button @click="pauseRecording"
              :disabled="recordState !== 'recording'"
              :class="cn('w-7 h-7 flex items-center justify-center rounded transition-colors',
                recordState === 'recording' ? 'hover:bg-[#3B9EFF]/15 cursor-pointer' : 'opacity-40 cursor-not-allowed')"
            >
              <div class="flex items-center gap-[3px]">
                <div class="w-[3px] h-3 rounded-sm" :class="recordState === 'recording' ? 'bg-[#3B9EFF]' : 'bg-[#3B9EFF]/40'"></div>
                <div class="w-[3px] h-3 rounded-sm" :class="recordState === 'recording' ? 'bg-[#3B9EFF]' : 'bg-[#3B9EFF]/40'"></div>
              </div>
            </button>
            <button @click="stopRecording"
              :disabled="recordState !== 'recording' && recordState !== 'paused'"
              :class="cn('w-7 h-7 flex items-center justify-center rounded transition-colors',
                recordState === 'recording' || recordState === 'paused' ? 'hover:bg-[#3B9EFF]/15 cursor-pointer' : 'opacity-40 cursor-not-allowed')"
            >
              <div class="w-2.5 h-2.5 rounded-[2px]" :class="recordState === 'recording' || recordState === 'paused' ? 'bg-[#3B9EFF]' : 'bg-[#3B9EFF]/40'"></div>
            </button>
          </div>
        </div>
        <div class="text-xs font-mono text-[#94A3B8] bg-[#1A1E2B] border border-[#252A3A] px-3 py-1.5 rounded-lg">
          会议编号 <span class="text-[#3B9EFF]">FICC-2026-Q2-04</span> · {{ currentMeeting?.date ?? '2026.04.15' }}
        </div>
        <div class="flex items-center justify-end space-x-3 mt-1">
          <span class="text-xs font-mono text-[#94A3B8]">投票回收 {{ ficcVoteCount }} / {{ FICC_MEMBERS.length }}</span>
          <div class="w-20 h-1 bg-[#1A1E2B] rounded-full overflow-hidden">
            <div class="h-full bg-[#3B9EFF] rounded-full transition-all duration-500" :style="{ width: `${ficcVoteCount / FICC_MEMBERS.length * 100}%` }"></div>
          </div>
          <span class="text-xs font-mono" :class="ficcVoteCount === FICC_MEMBERS.length ? 'text-[#3B9EFF]' : 'text-[#94A3B8]'">
            {{ ficcVoteCount === FICC_MEMBERS.length ? '全员完成' : '收集中' }}
          </span>
        </div>
      </div>
    </div>

    <!-- ═══ 录音状态横幅（会议记录中） ═══ -->
    <div v-if="recordState === 'recording' || recordState === 'paused'"
      class="shrink-0 flex items-center justify-center gap-3 py-1.5 rounded-lg border transition-all duration-300"
      :class="recordState === 'recording'
        ? 'bg-[#FF3B30]/8 border-[#FF3B30]/25'
        : 'bg-[#3B9EFF]/8 border-[#3B9EFF]/25'">
      <div class="w-2 h-2 rounded-full animate-pulse" :class="recordState === 'recording' ? 'bg-[#FF3B30]' : 'bg-[#3B9EFF]'"></div>
      <span class="text-xs font-mono font-bold" :class="recordState === 'recording' ? 'text-[#FF3B30]' : 'text-[#3B9EFF]'">
        {{ recordState === 'recording' ? '会议记录中' : '录音已暂停' }}
      </span>
      <span class="text-xs font-mono tabular-nums" :class="recordState === 'recording' ? 'text-[#FF3B30]/70' : 'text-[#3B9EFF]/70'">{{ recordingTimeDisplay }}</span>
      <span class="text-xs font-mono text-[#64748B]">|</span>
      <span class="text-xs font-mono text-[#94A3B8]">本录音仅用于会议纪要生成，录音结束后将自动转写</span>
    </div>

    <!-- ═══ LEFT SIDEBAR + MAIN CONTENT ═══ -->
    <div class="flex-1 flex flex-row min-h-0">

      <!-- LEFT SIDEBAR -->
      <div class="w-[200px] shrink-0 bg-[#1A1E2B] border-r border-[#252A3A] flex flex-col py-3">
        <div v-for="tab in FICC_TAB_ITEMS" :key="tab.key"
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
      <div class="flex-1 overflow-y-auto no-scrollbar bg-[#161922] p-4">

      <!-- ════════════════════════════════════════════════════════════
           STEP 0: 会前筹备与征集 (角色感知)
      ════════════════════════════════════════════════════════════ -->

      <!-- ── 秘书视角: 材料汇总看板 ── -->
      <div v-if="activeTab === 'materials' && isSecretary" class="pb-4 space-y-4">

        <!-- ── 秘书视图切换器 ── -->
        <div class="flex items-center gap-3">
          <div class="inline-flex bg-[#161922] border border-[#252A3A] rounded-lg p-0.5 gap-0.5">
            <button
              @click="ficcSecretaryView = 'progress'"
              :class="cn('px-4 py-1.5 rounded-md text-[11px] font-mono font-medium transition-all duration-150',
                ficcSecretaryView === 'progress'
                  ? 'bg-[#3B9EFF]/12 border border-[#3B9EFF]/30 text-[#3B9EFF]'
                  : 'text-[#4A5568] hover:text-[#94A3B8]')"
            >委员提交进度看板</button>
            <button
              @click="ficcSecretaryView = 'proxy'"
              :class="cn('px-4 py-1.5 rounded-md text-[11px] font-mono font-medium transition-all duration-150',
                ficcSecretaryView === 'proxy'
                  ? 'bg-[#FFAB00]/12 border border-[#FFAB00]/30 text-[#FFAB00]'
                  : 'text-[#4A5568] hover:text-[#94A3B8]')"
            >RPA / 人工代填工作台</button>
          </div>
        </div>

        <!-- ── 委员提交进度看板（原有内容） ── -->
        <div v-if="ficcSecretaryView === 'progress'" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden flex flex-col">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>委员材料提交进度</h3>
              <div class="flex items-center space-x-3">
                <span class="text-[11px] font-mono text-[#94A3B8]">{{ ficcMaterialCount }} / {{ FICC_MEMBERS.length }} 已提交</span>
                <div class="w-20 h-1 bg-[#1A1E2B] rounded-full overflow-hidden">
                  <div class="h-full bg-[#3B9EFF] rounded-full transition-all duration-500" :style="{ width: `${ficcMaterialCount / FICC_MEMBERS.length * 100}%` }"></div>
                </div>
              </div>
            </div>
            <div class="flex-1 overflow-y-auto no-scrollbar divide-y divide-[#1A1E2B]">
              <div
                v-for="m in FICC_MEMBERS" :key="m.id"
                class="flex items-center px-5 py-3.5"
              >
                <div :class="cn(
                  'w-2.5 h-2.5 rounded-full shrink-0 mr-4',
                  ficcMaterials[m.id] ? 'bg-[#34C759] shadow-[0_0_6px_rgba(52,199,89,0.4)]' : 'bg-[#4A5568]'
                )"></div>
                <div class="flex-1 min-w-0">
                  <div class="text-[13px] font-medium text-[#E8ECF4]">{{ m.name }}</div>
                  <div class="text-[11px] font-mono text-[#6B7280] mt-0.5">{{ m.role }}</div>
                </div>
                <div class="flex items-center space-x-2">
                  <span v-if="ficcMaterials[m.id]" class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-2 py-1 rounded">
                    已提交 {{ ficcMaterials[m.id].submittedAt }}
                  </span>
                  <span v-else class="text-[11px] font-mono text-[#F97316] bg-[#F97316]/10 border border-[#F97316]/20 px-2 py-1 rounded">未提交</span>
                  <button
                    v-if="!ficcMaterials[m.id]"
                    @click="sendFiccReminder(m.id)"
                    :class="cn(
                      'text-[11px] font-mono px-2.5 py-1 rounded border transition-all duration-150',
                      ficcSentReminders.has(m.id) ? 'text-[#94A3B8] border-[#252A3A] cursor-default' : 'text-[#3B9EFF] border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/10'
                    )"
                  >{{ ficcSentReminders.has(m.id) ? '已催' : '催办' }}</button>
                </div>
              </div>
            </div>
            <div class="p-3 border-t border-[#252A3A] space-y-2">
              <button
                @click="sendAllFiccReminders"
                class="w-full text-[13px] py-2.5 rounded-lg border border-[#3B9EFF]/25 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 hover:border-[#3B9EFF]/40 transition-all flex items-center justify-center space-x-2"
              >
                <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div>
                <span>一键邮件催办全部未提交委员</span>
              </button>
              <button
                @click="markMaterialsCollected"
                :class="cn(
                  'w-full py-3 rounded-xl font-bold text-[15px] transition-all duration-200',
                  ficcMaterialCount > 0
                    ? 'bg-gradient-to-r from-[#34C759] to-[#3B9EFF] text-white shadow-[0_4px_24px_rgba(52,199,89,0.3)] hover:shadow-[0_4px_36px_rgba(52,199,89,0.45)] active:scale-[0.99]'
                    : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed'
                )"
              >
                <span class="flex items-center justify-center space-x-2">
                  <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
                  <span>完成材料收集</span>
                </span>
              </button>
            </div>
          </div>

        <!-- ── RPA / 人工代填工作台 ── -->
        <div v-else class="space-y-4">
          <!-- 警示横幅 -->
          <div class="flex items-center gap-3 px-4 py-2.5 bg-[#FFAB00]/5 border border-[#FFAB00]/30 rounded-xl">
            <div class="w-1.5 h-4 bg-[#FFAB00] rounded-sm shrink-0"></div>
            <span class="text-[11px] font-mono text-[#FFAB00] font-semibold">当前为秘书代操作模式</span>
            <span class="text-[11px] font-mono text-[#FFAB00]/55 ml-auto">代填操作将附加 isProxy: true 标记</span>
          </div>

          <!-- 委员选择器 -->
          <div class="bg-[#202431] border border-[#FFAB00]/25 rounded-xl overflow-hidden">
            <div class="bg-gradient-to-r from-[#FFAB00]/8 to-[#202431] border-b border-[#FFAB00]/15 px-5 py-3 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-4 bg-[#FFAB00] rounded-sm shrink-0"></div>
                <h3 class="text-sm font-semibold text-[#E8ECF4]">目标委员选择</h3>
              </div>
              <span class="text-[11px] font-mono text-[#FFAB00]/70 bg-[#FFAB00]/8 border border-[#FFAB00]/20 px-2 py-1 rounded">RPA 代填模式</span>
            </div>
            <div class="p-5">
              <label class="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider mb-2 block">请选择目标委员</label>
              <select
                v-model="ficcProxyTargetId"
                data-rpa-id="member-selector"
                class="w-full bg-[#1A1E2B] border border-[#FFAB00]/25 rounded-lg px-4 py-2.5 text-[13px] text-[#E8ECF4] font-mono focus:border-[#FFAB00]/50 focus:outline-none transition-colors cursor-pointer"
              >
                <option value="" disabled class="bg-[#161922] text-[#4A5568]">-- 选择委员 --</option>
                <option v-for="m in FICC_COMMITTEE_MEMBERS" :key="m.id" :value="m.id" class="bg-[#161922] text-[#E8ECF4]">
                  {{ m.name }} · {{ m.role }}
                </option>
              </select>
            </div>
          </div>

          <!-- 问卷填报区（代填目标已选） -->
          <div v-if="ficcProxyTargetId" class="bg-[#202431] border border-[#FFAB00]/25 rounded-xl overflow-hidden">
            <!-- 代填成功状态 -->
            <div v-if="ficcProxySubmitDone" class="p-8 flex flex-col items-center gap-3">
              <div class="w-1.5 h-8 bg-[#00C9A7] rounded-sm"></div>
              <p class="text-[13px] font-semibold text-[#00C9A7]">代填成功</p>
              <p class="text-[11px] font-mono text-[#64748B]">表单已清空，可为下一位委员代填</p>
            </div>
            <!-- 填报表单 -->
            <template v-else>
              <div class="bg-gradient-to-r from-[#FFAB00]/8 to-[#202431] border-b border-[#FFAB00]/15 px-5 py-3 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-1.5 h-4 bg-[#FFAB00] rounded-sm shrink-0"></div>
                  <h3 class="text-[13px] font-semibold text-[#E8ECF4]">代填：{{ ficcProxyTargetMember?.name }} · {{ ficcProxyTargetMember?.role }}</h3>
                </div>
                <span class="text-[11px] font-mono text-[#FFAB00]/60">月度资产评分（代填）</span>
              </div>
              <div class="p-5 space-y-5">
                <div v-for="group in FICC_ASSET_GROUPS" :key="group.大类" class="space-y-2">
                  <div class="flex items-center gap-3">
                    <div class="h-px flex-1 bg-[#252A3A]"></div>
                    <div class="flex items-center gap-2 px-3 py-1 rounded-full border"
                      :class="FICC_GROUP_HEADER_STYLE[group.大类] ?? 'border-[#2E3348] bg-[#1A1E2B]'">
                      <span class="text-[11px] font-bold font-mono" :class="FICC_GROUP_TEXT_COLOR[group.大类] ?? 'text-[#94A3B8]'">{{ group.大类 }}</span>
                      <span class="text-[11px] font-mono text-[#4A5568]">{{ group.items.length }} 项策略</span>
                    </div>
                    <div class="h-px flex-1 bg-[#252A3A]"></div>
                  </div>
                  <div v-for="cfg in group.items" :key="cfg.细分策略" class="bg-[#1A1E2B] border border-[#2E3348] rounded-xl p-4 space-y-3">
                    <div class="flex items-start justify-between gap-3">
                      <div class="min-w-0">
                        <div class="text-[13px] font-semibold text-[#E8ECF4]">{{ cfg.细分策略 }}</div>
                        <div class="flex items-center gap-1.5 mt-0.5">
                          <span class="text-[11px] font-mono text-[#4A5568] truncate">{{ cfg.标的指数 }}</span>
                          <span class="text-[11px] text-[#3A4555]">·</span>
                          <span class="text-[11px] font-mono font-bold tabular-nums text-[#64748B]">{{ cfg.当前点位 }}</span>
                        </div>
                      </div>
                      <button @click="ficcProxyNewHighFlags[cfg.细分策略] = !ficcProxyNewHighFlags[cfg.细分策略]"
                        :class="cn('shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-mono transition-all duration-150',
                          ficcProxyNewHighFlags[cfg.细分策略] ? 'bg-[#00C9A7]/10 border-[#00C9A7]/35 text-[#00C9A7]' : 'bg-transparent border-[#252A3A] text-[#4A5568] hover:border-[#2E3348]')">
                        <span class="text-[11px]">↑</span><span>创新高</span>
                      </button>
                    </div>
                    <!-- 评分按钮（带 RPA data 属性） -->
                    <div class="grid grid-cols-5 gap-1.5">
                      <button v-for="n in 5" :key="n"
                        @click="ficcProxyScores[cfg.细分策略] = n"
                        :data-rpa-id="`vote-btn-${group.大类}-${cfg.细分策略}-${n}`"
                        :class="cn('py-2 rounded-lg border transition-all duration-150 flex flex-col items-center gap-0.5',
                          ficcProxyScores[cfg.细分策略] === n ? FICC_SCORE_COLORS[n] : FICC_SCORE_INACTIVE)">
                        <span class="text-[22px] font-bold font-mono leading-none">{{ n }}</span>
                        <span class="text-[11px] font-mono opacity-70">{{ FICC_SCORE_LABELS_SHORT[n] }}</span>
                      </button>
                    </div>
                    <!-- 幅度 / 区间显示 -->
                    <div class="flex items-center gap-2 bg-[#161922] rounded-lg px-3 py-2 border border-[#252A3A]">
                      <span class="text-[11px] font-mono text-[#4A5568]">观点幅度</span>
                      <span class="text-[11px] font-mono font-bold text-[#3B9EFF]">{{ getFiccAmplitudeText(cfg.细分策略, ficcProxyScores[cfg.细分策略]) }}</span>
                      <div class="w-px h-3 bg-[#2E3348] mx-1"></div>
                      <span class="text-[11px] font-mono text-[#4A5568]">预期区间</span>
                      <span class="text-[11px] font-mono font-bold text-[#3B9EFF] tabular-nums">{{ getFiccTargetRangeText(cfg.细分策略, ficcProxyScores[cfg.细分策略]) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 提交区 -->
              <div class="p-5 border-t border-[#FFAB00]/15 space-y-2">
                <div class="flex items-center gap-2 bg-[#FFAB00]/5 border border-[#FFAB00]/20 rounded-lg px-4 py-2.5">
                  <div class="w-1.5 h-3.5 bg-[#FFAB00] rounded-sm shrink-0"></div>
                  <span class="text-[13px] text-[#FFAB00]">代填操作：数据将绑定至 {{ ficcProxyTargetMember?.name }}，isProxy: true</span>
                </div>
                <button
                  @click="submitFiccProxyScores"
                  data-rpa-id="proxy-submit-btn"
                  :class="cn(
                    'w-full py-3.5 rounded-xl font-bold text-[15px] transition-all duration-200',
                    'bg-gradient-to-r from-[#FFAB00]/80 to-[#FFAB00] text-[#161922] shadow-[0_4px_24px_rgba(255,171,0,0.3)] hover:shadow-[0_4px_36px_rgba(255,171,0,0.45)] active:scale-[0.99]'
                  )"
                >确认代 {{ ficcProxyTargetMember?.name ?? '委员' }} 提交问卷</button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ── 委员视角: 市场观点与材料提交 ── -->
      <div v-else-if="activeTab === 'materials' && isFiccMember" class="pb-4 space-y-4">

        <!-- 已提交：只读确认 -->
        <div v-if="ficcSelfMaterial" class="bg-[#202431] border border-[#34C759]/20 rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#34C759]/10 to-[#202431] border-b border-[#34C759]/15 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-full bg-[#34C759]/15 border border-[#34C759]/30 flex items-center justify-center">
                <div class="w-1.5 h-4 bg-[#00C9A7] rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="text-[15px] font-bold text-[#34C759]">观点与材料已成功提交</h3>
                <p class="text-[11px] font-mono text-[#94A3B8] mt-0.5">提交于 {{ ficcSelfMaterial.submittedAt }} · 数据已锁定</p>
              </div>
            </div>
            <span class="text-[11px] font-mono text-[#34C759] bg-[#34C759]/10 border border-[#34C759]/20 px-2 py-1 rounded">只读</span>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <div class="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider mb-2">本期宏观与 FICC 市场观点</div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-5 py-4 text-[13px] text-[#B4BAC9] leading-relaxed">{{ ficcSelfMaterial.summary }}</div>
            </div>
            <div v-if="ficcUploadedFiles.length">
              <div class="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider mb-2">已提交附件</div>
              <div class="space-y-1.5">
                <div v-for="(f, i) in ficcUploadedFiles" :key="i" class="flex items-center bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-2.5">
                  <div class="w-1 h-3.5 bg-[#64748B] rounded-sm shrink-0 mr-3"></div>
                  <span class="text-[13px] text-[#B4BAC9] flex-1 min-w-0 truncate">{{ f.name }}</span>
                  <span class="text-[11px] font-mono text-[#64748B] ml-3">{{ f.size }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 未提交：填写观点 + 上传附件 -->
        <div v-else class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#3B9EFF] to-[#3B9EFF] flex items-center justify-center shadow-[0_0_14px_rgba(59,158,255,0.25)]">
                <div class="w-1.5 h-4 bg-white/90 rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="am-title-l2"><div class="am-title-bar"></div>本期宏观与 FICC 市场观点</h3>
                <p class="text-[11px] font-mono text-[#6B7280] mt-0.5">请在会前截止时间前提交观点与材料</p>
              </div>
            </div>
            <span class="text-[11px] font-mono px-3 py-1.5 rounded-lg border" :class="ROLE_BADGE_CLASSES[activeRole] || 'bg-[#94A3B8]/10 border-[#94A3B8]/25 text-[#94A3B8]'">{{ activeRole }}</span>
          </div>
          <div class="p-6 space-y-5">

            <!-- 观点文本域 -->
            <div>
              <div class="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider mb-3">本期宏观与 FICC 市场观点</div>
              <textarea
                v-model="ficcSummaryDraft"
                rows="10"
                class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-xl px-5 py-4 text-[15px] text-[#B4BAC9] placeholder-[#3A4555] outline-none focus:border-[#3B9EFF]/45 focus:shadow-[0_0_20px_rgba(59,158,255,0.06)] transition-all resize-none leading-relaxed"
                placeholder="请输入您对本期宏观与 FICC 市场的核心观点，包括利率走势判断、信用策略偏好、境外债市观点等..."
              ></textarea>
              <div class="flex justify-end mt-1.5">
                <span class="text-[11px] font-mono text-[#4A5568]">{{ ficcSummaryDraft.length }} 字</span>
              </div>
            </div>

            <!-- 附件上传区域 (Mock) -->
            <div>
              <div class="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider mb-3">附件上传</div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-4 space-y-3">
                <div v-if="ficcUploadedFiles.length" class="space-y-1.5">
                  <div v-for="(f, i) in ficcUploadedFiles" :key="i" class="flex items-center bg-[#202431] border border-[#252A3A] rounded-lg px-4 py-2.5 group">
                    <div :class="cn(
                      'w-6 h-6 rounded flex items-center justify-center mr-3 shrink-0',
                      f.type === 'pdf' ? 'bg-[#EF4444]/15 text-[#EF4444]' : 'bg-[#22C55E]/15 text-[#22C55E]'
                    )">
                      <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="text-[13px] text-[#B4BAC9] truncate">{{ f.name }}</div>
                      <div class="text-[11px] font-mono text-[#64748B]">{{ f.size }} · {{ f.type === 'pdf' ? 'PDF 文档' : 'Excel 表格' }}</div>
                    </div>
                    <button @click="removeMockFile(i)" class="ml-2 p-1 rounded hover:bg-[#EF4444]/10 text-[#64748B] hover:text-[#EF4444] transition-all">
                      <div class="w-0.5 h-3.5 bg-current rounded-full shrink-0"></div>
                    </button>
                  </div>
                </div>
                <div v-else class="text-center py-3">
                  <div class="w-1.5 h-8 bg-[#3A4555] rounded-sm mx-auto mb-2"></div>
                  <p class="text-[11px] text-[#4A5568]">暂无附件，点击下方按钮添加</p>
                </div>
                <div class="flex items-center space-x-2 pt-1">
                  <button @click="addMockFile" class="flex-1 text-[13px] py-2.5 rounded-lg border border-[#3B9EFF]/25 bg-[#3B9EFF]/8 text-[#3B9EFF] hover:bg-[#3B9EFF]/15 hover:border-[#3B9EFF]/40 transition-all flex items-center justify-center space-x-2">
                    <div class="w-1 h-3.5 bg-current rounded-sm shrink-0"></div>
                    <span>添加附件 (Mock)</span>
                  </button>
                  <span class="text-[11px] font-mono text-[#4A5568]">支持 PDF / Excel</span>
                </div>
              </div>
            </div>
          </div>
            <!-- ── 维度切换：月度填报 | 季度展望 ── -->
            <div class="px-6 pt-4 pb-3">
              <div class="inline-flex bg-[#161922] border border-[#252A3A] rounded-lg p-0.5 gap-0.5">
                <button
                  @click="ficcVoteDimension = 'monthly'"
                  :class="cn('px-4 py-1.5 rounded-md text-[12px] font-mono font-medium transition-all duration-150',
                    ficcVoteDimension === 'monthly'
                      ? 'bg-[#3B9EFF]/12 border border-[#3B9EFF]/30 text-[#3B9EFF]'
                      : 'text-[#4A5568] hover:text-[#94A3B8]')"
                >月度填报</button>
                <button
                  @click="ficcVoteDimension = 'quarterly'"
                  :class="cn('px-4 py-1.5 rounded-md text-[12px] font-mono font-medium transition-all duration-150',
                    ficcVoteDimension === 'quarterly'
                      ? 'bg-[#3B9EFF]/12 border border-[#3B9EFF]/30 text-[#3B9EFF]'
                      : 'text-[#4A5568] hover:text-[#94A3B8]')"
                >季度展望</button>
              </div>
            </div>

            <!-- ── 月度填报 ── -->
            <div v-if="ficcVoteDimension === 'monthly'" class="px-6 pb-2 space-y-5">
              <div v-for="group in FICC_ASSET_GROUPS" :key="group.大类" class="space-y-2">
                <div class="flex items-center gap-3">
                  <div class="h-px flex-1 bg-[#252A3A]"></div>
                  <div class="flex items-center gap-2 px-3 py-1 rounded-full border"
                    :class="FICC_GROUP_HEADER_STYLE[group.大类] ?? 'border-[#2E3348] bg-[#1A1E2B]'">
                    <span class="text-[12px] font-bold font-mono" :class="FICC_GROUP_TEXT_COLOR[group.大类] ?? 'text-[#94A3B8]'">{{ group.大类 }}</span>
                    <span class="text-[11px] font-mono text-[#4A5568]">{{ group.items.length }} 项策略</span>
                  </div>
                  <div class="h-px flex-1 bg-[#252A3A]"></div>
                </div>
                <div v-for="cfg in group.items" :key="cfg.细分策略" class="bg-[#1A1E2B] border border-[#2E3348] rounded-xl p-4 space-y-3">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="text-[14px] font-semibold text-[#E8ECF4]">{{ cfg.细分策略 }}</div>
                      <div class="flex items-center gap-1.5 mt-0.5">
                        <span class="text-[11px] font-mono text-[#4A5568] truncate">{{ cfg.标的指数 }}</span>
                        <span class="text-[11px] text-[#3A4555]">·</span>
                        <span class="text-[11px] font-mono font-bold tabular-nums text-[#64748B]">{{ cfg.当前点位 }}</span>
                      </div>
                    </div>
                    <button @click="ficcNewHighFlags[cfg.细分策略] = !ficcNewHighFlags[cfg.细分策略]"
                      :class="cn('shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-mono transition-all duration-150',
                        ficcNewHighFlags[cfg.细分策略] ? 'bg-[#00C9A7]/10 border-[#00C9A7]/35 text-[#00C9A7]' : 'bg-transparent border-[#252A3A] text-[#4A5568] hover:border-[#2E3348]')">
                      <span class="text-[11px]">↑</span><span>创新高</span>
                    </button>
                  </div>
                  <div class="grid grid-cols-5 gap-1.5">
                    <button v-for="n in 5" :key="n" @click="ficcSelfScores[cfg.细分策略] = n"
                      :class="cn('py-2 rounded-lg border transition-all duration-150 flex flex-col items-center gap-0.5',
                        ficcSelfScores[cfg.细分策略] === n ? FICC_SCORE_COLORS[n] : FICC_SCORE_INACTIVE)">
                      <span class="text-[22px] font-bold font-mono leading-none">{{ n }}</span>
                      <span class="text-[11px] font-mono opacity-70">{{ FICC_SCORE_LABELS_SHORT[n] }}</span>
                    </button>
                  </div>
                  <div class="flex items-center gap-2 bg-[#161922] rounded-lg px-3 py-2 border border-[#252A3A]">
                    <span class="text-[11px] font-mono text-[#4A5568]">观点幅度</span>
                    <span class="text-[12px] font-mono font-bold text-[#3B9EFF]">{{ getFiccAmplitudeText(cfg.细分策略, ficcSelfScores[cfg.细分策略]) }}</span>
                    <div class="w-px h-3 bg-[#2E3348] mx-1"></div>
                    <span class="text-[11px] font-mono text-[#4A5568]">预期区间</span>
                    <span class="text-[12px] font-mono font-bold text-[#3B9EFF] tabular-nums">{{ getFiccTargetRangeText(cfg.细分策略, ficcSelfScores[cfg.细分策略]) }}</span>
                    <span class="text-[11px] font-mono text-[#3A4555] ml-0.5">{{ cfg.amplitudeType === 'bp' ? '%(收益率)' : '点' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- ── 季度展望填报 ── -->
            <div v-else class="px-6 pb-2 space-y-5">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-[11px] font-mono text-[#3B9EFF]/70 bg-[#3B9EFF]/8 border border-[#3B9EFF]/20 px-2.5 py-1 rounded">季度视角 · 幅度档位较月度更宽</span>
              </div>
              <div v-for="group in FICC_QUARTERLY_ASSET_GROUPS" :key="group.大类" class="space-y-2">
                <div class="flex items-center gap-3">
                  <div class="h-px flex-1 bg-[#252A3A]"></div>
                  <div class="flex items-center gap-2 px-3 py-1 rounded-full border"
                    :class="FICC_GROUP_HEADER_STYLE[group.大类] ?? 'border-[#2E3348] bg-[#1A1E2B]'">
                    <span class="text-[12px] font-bold font-mono" :class="FICC_GROUP_TEXT_COLOR[group.大类] ?? 'text-[#94A3B8]'">{{ group.大类 }}</span>
                    <span class="text-[11px] font-mono text-[#4A5568]">{{ group.items.length }} 项策略</span>
                  </div>
                  <div class="h-px flex-1 bg-[#252A3A]"></div>
                </div>
                <div v-for="cfg in group.items" :key="cfg.细分策略" class="bg-[#1A1E2B] border border-[#3B9EFF]/15 rounded-xl p-4 space-y-3">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="text-[14px] font-semibold text-[#E8ECF4]">{{ cfg.细分策略 }}</div>
                      <div class="flex items-center gap-1.5 mt-0.5">
                        <span class="text-[11px] font-mono text-[#4A5568] truncate">{{ cfg.标的指数 }}</span>
                        <span class="text-[11px] text-[#3A4555]">·</span>
                        <span class="text-[11px] font-mono font-bold tabular-nums text-[#64748B]">{{ cfg.当前点位 }}</span>
                      </div>
                    </div>
                    <button @click="ficcQNewHighFlags[cfg.细分策略] = !ficcQNewHighFlags[cfg.细分策略]"
                      :class="cn('shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-mono transition-all duration-150',
                        ficcQNewHighFlags[cfg.细分策略] ? 'bg-[#00C9A7]/10 border-[#00C9A7]/35 text-[#00C9A7]' : 'bg-transparent border-[#252A3A] text-[#4A5568] hover:border-[#2E3348]')">
                      <span class="text-[11px]">↑</span><span>创新高</span>
                    </button>
                  </div>
                  <div class="grid grid-cols-5 gap-1.5">
                    <button v-for="n in 5" :key="n" @click="ficcSelfQScores[cfg.细分策略] = n"
                      :class="cn('py-2 rounded-lg border transition-all duration-150 flex flex-col items-center gap-0.5',
                        ficcSelfQScores[cfg.细分策略] === n ? FICC_SCORE_COLORS[n] : FICC_SCORE_INACTIVE)">
                      <span class="text-[22px] font-bold font-mono leading-none">{{ n }}</span>
                      <span class="text-[11px] font-mono opacity-70">{{ FICC_SCORE_LABELS_SHORT[n] }}</span>
                    </button>
                  </div>
                  <div class="flex items-center gap-2 bg-[#161922] rounded-lg px-3 py-2 border border-[#252A3A]">
                    <span class="text-[11px] font-mono text-[#3B9EFF]/70">季度幅度</span>
                    <span class="text-[12px] font-mono font-bold text-[#3B9EFF]">{{ getFiccQAmplitudeText(cfg.细分策略, ficcSelfQScores[cfg.细分策略]) }}</span>
                    <div class="w-px h-3 bg-[#2E3348] mx-1"></div>
                    <span class="text-[11px] font-mono text-[#4A5568]">季度区间</span>
                    <span class="text-[12px] font-mono font-bold text-[#3B9EFF] tabular-nums">{{ getFiccQTargetRangeText(cfg.细分策略, ficcSelfQScores[cfg.细分策略]) }}</span>
                    <span class="text-[11px] font-mono text-[#3A4555] ml-0.5">{{ cfg.amplitudeType === 'bp' ? '%(收益率)' : '点' }}</span>
                  </div>
                </div>
              </div>
            </div>

          <div class="px-6 pb-1 pt-4 border-t border-[#252A3A] space-y-2">
            <button v-if="ficcVoteDimension === 'monthly'"
              @click="submitFiccScores"
              :disabled="ficcScoreSubmitted"
              :class="cn('w-full py-2.5 rounded-lg font-semibold text-[13px] transition-all duration-200',
                !ficcScoreSubmitted
                  ? 'bg-[#3B9EFF]/10 border border-[#3B9EFF]/30 text-[#3B9EFF] hover:bg-[#3B9EFF]/18'
                  : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed')"
            >{{ ficcScoreSubmitted ? '✓ 月度观点已提交' : '提交月度观点评分' }}</button>
            <button v-else
              @click="submitFiccQScores"
              :disabled="ficcQScoreSubmitted"
              :class="cn('w-full py-2.5 rounded-lg font-semibold text-[13px] transition-all duration-200',
                !ficcQScoreSubmitted
                  ? 'bg-[#3B9EFF]/10 border border-[#3B9EFF]/30 text-[#3B9EFF] hover:bg-[#3B9EFF]/18'
                  : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed')"
            >{{ ficcQScoreSubmitted ? '✓ 季度展望已提交' : '提交季度展望评分' }}</button>
          </div>

          <div class="px-6 pb-5">
            <button
              @click="showFiccVoteConfirm = true"
              :disabled="!ficcSummaryDraft.trim()"
              :class="cn(
                'w-full py-3.5 rounded-xl font-bold text-[15px] transition-all duration-200',
                ficcSummaryDraft.trim()
                  ? 'bg-gradient-to-r from-[#3B9EFF] to-[#3B9EFF] text-white shadow-[0_4px_24px_rgba(59,158,255,0.3)] hover:shadow-[0_4px_36px_rgba(59,158,255,0.45)] active:scale-[0.99]'
                  : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed'
              )"
            >提交观点与材料</button>
          </div>
        </div>

        <!-- 查看历史观点 -->
        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <button @click="showFiccHistory = !showFiccHistory" class="w-full px-6 py-3.5 flex items-center justify-between hover:bg-[#252A3A]/50 transition-all">
            <div class="flex items-center space-x-3">
              <div class="w-1.5 h-4 bg-[#94A3B8] rounded-sm shrink-0"></div>
              <span class="text-[13px] font-medium text-[#94A3B8]">查看往期会议核心观点</span>
            </div>
            <div class="w-0.5 h-3.5 bg-[#64748B] rounded-full transition-transform duration-200 origin-center" :class="showFiccHistory ? 'rotate-90' : ''"></div>
          </button>
          <div v-if="showFiccHistory" class="border-t border-[#252A3A] p-5 space-y-4">
            <div v-for="h in FICC_HISTORY_OPINIONS" :key="h.meeting" class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg overflow-hidden">
              <div class="px-4 py-2.5 border-b border-[#252A3A] flex items-center justify-between">
                <span class="text-[11px] font-mono font-bold text-[#E8ECF4]">{{ h.meeting }}</span>
                <span class="text-[11px] font-mono text-[#64748B]">{{ h.date }}</span>
              </div>
              <div class="p-4 space-y-3">
                <div v-for="(op, oi) in h.opinions" :key="oi" class="flex items-start space-x-3">
                  <div class="w-1 h-full min-h-[32px] bg-[#3B9EFF]/20 rounded-full shrink-0 mt-0.5"></div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center space-x-2 mb-0.5">
                      <span class="text-[11px] font-medium text-[#E8ECF4]">{{ op.author }}</span>
                      <span class="text-[11px] font-mono text-[#64748B]">{{ op.role }}</span>
                    </div>
                    <p class="text-[13px] text-[#94A3B8] leading-relaxed">{{ op.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══ 委员观点与材料汇总大屏 (materials Tab 共享) ═══ -->
      <div v-if="activeTab === 'materials'" class="space-y-4 pb-4">
        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>委员观点与材料 · 会前征集汇总大屏</h3>
            <div class="flex items-center space-x-2">
              <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] animate-pulse"></div>
              <span class="text-[11px] font-mono text-[#94A3B8]">来自 S0 会前征集 · {{ ficcMaterialCount }} / {{ FICC_MEMBERS.length }} 已提交</span>
            </div>
          </div>
          <div class="p-5">
            <div class="grid grid-cols-2 gap-4">
              <div
                v-for="m in FICC_MEMBERS" :key="m.id"
                class="bg-[#1A1E2B] border rounded-xl overflow-hidden transition-all duration-200"
                :class="ficcMaterials[m.id] ? 'border-[#252A3A] hover:border-[#3B9EFF]/30' : 'border-[#252A3A]/50 opacity-40'"
              >
                <div class="px-5 py-3 border-b border-[#252A3A] flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <div :class="cn(
                      'w-2.5 h-2.5 rounded-full shrink-0',
                      ficcMaterials[m.id] ? 'bg-[#34C759] shadow-[0_0_6px_rgba(52,199,89,0.4)]' : 'bg-[#4A5568]'
                    )"></div>
                    <span class="text-[13px] font-bold text-[#E8ECF4]">{{ m.name }}</span>
                    <span class="text-[11px] font-mono text-[#64748B]">{{ m.role }}</span>
                  </div>
                  <span v-if="ficcMaterials[m.id]" class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-2 py-0.5 rounded">{{ ficcMaterials[m.id].submittedAt }}</span>
                  <span v-else class="text-[11px] font-mono text-[#F97316]">未提交</span>
                </div>
                <div class="p-5">
                  <template v-if="ficcMaterials[m.id]">
                    <p class="text-[13px] text-[#B4BAC9] leading-relaxed">{{ ficcMaterials[m.id].summary }}</p>
                    <div v-if="FICC_MEMBER_ATTACHMENTS[m.id]?.length" class="mt-3 pt-3 border-t border-[#252A3A] space-y-1.5">
                      <div class="text-[11px] font-mono text-[#64748B] uppercase tracking-wider mb-1">附件材料</div>
                      <div v-for="att in FICC_MEMBER_ATTACHMENTS[m.id]" :key="att.name" class="flex items-center space-x-2 bg-[#202431] border border-[#252A3A] rounded-lg px-3 py-2">
                        <div :class="cn(
                          'w-5 h-5 rounded flex items-center justify-center shrink-0',
                          att.type === 'pdf' ? 'bg-[#EF4444]/15 text-[#EF4444]' : att.type === 'excel' ? 'bg-[#22C55E]/15 text-[#22C55E]' : 'bg-[#3B9EFF]/15 text-[#3B9EFF]'
                        )">
                          <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div>
                        </div>
                        <span class="text-[11px] text-[#B4BAC9] flex-1 min-w-0 truncate">{{ att.name }}</span>
                        <span class="text-[11px] font-mono text-[#64748B] shrink-0">{{ att.size }}</span>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <p class="text-[11px] text-[#4A5568] italic">该委员尚未提交观点与材料</p>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ════════════════════════════════════════════════════════════
           STEP 1: 会中 · 回顾与复盘 (大屏演示)
      ════════════════════════════════════════════════════════════ -->
      <div v-if="activeTab === 'anchors'" class="space-y-4 pb-4">

        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>指引表现 · 纯债 / 固收+ 收益曲线回溯对比</h3>
            <span class="text-[11px] font-mono text-[#94A3B8] bg-[#1A1E2B] px-2.5 py-1 rounded border border-[#252A3A]">区间: 2025.10 — 2026.03</span>
          </div>
          <div class="p-5">
            <div class="relative h-[180px] w-full">
              <svg class="absolute inset-0 w-full h-full" viewBox="0 0 760 160" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="ficcFillBlue" x1="0" y1="0" x2="0" y2="1">
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
                <!-- 纯债指引 -->
                <path d="M0,118 L127,106 L254,90 L381,84 L508,72 L635,64 L760,56 L760,140 L0,140 Z" fill="url(#ficcFillBlue)" />
                <polyline points="0,118 127,106 254,90 381,84 508,72 635,64 760,56" fill="none" stroke="#3B9EFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
                <!-- 固收+指引 -->
                <polyline points="0,118 127,108 254,96 381,90 508,80 635,70 760,62" fill="none" stroke="#3B9EFF" stroke-width="2" stroke-dasharray="7,4" stroke-linecap="round" />
                <!-- 实际净值 -->
                <polyline points="0,118 127,104 254,87 381,94 508,68 635,60 760,52" fill="none" stroke="#3B9EFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
                <circle v-for="(pt, i) in [[127,104],[254,87],[381,94],[508,68],[635,60],[760,52]]" :key="i" :cx="pt[0]" :cy="pt[1]" r="3" fill="#3B9EFF" />
              </svg>
              <div class="absolute left-0 top-0 bottom-5 flex flex-col justify-between text-[11px] font-mono text-[#6B7280] pointer-events-none">
                <span>+4.2%</span><span>+3.0%</span><span>+1.8%</span><span>+0.6%</span>
              </div>
              <div class="absolute bottom-0 left-6 right-0 flex justify-between text-[11px] font-mono text-[#6B7280]">
                <span>Oct '25</span><span>Nov '25</span><span>Dec '25</span><span>Jan '26</span><span>Feb '26</span><span>Mar '26</span>
              </div>
            </div>
            <div class="flex items-center space-x-6 mt-4 pl-6">
              <div class="flex items-center space-x-2"><div class="w-7 h-[2.5px] bg-[#3B9EFF] rounded-full"></div><span class="text-[11px] text-[#B4BAC9] font-mono">纯债指引</span></div>
              <div class="flex items-center space-x-2"><svg width="28" height="3"><line x1="0" y1="1.5" x2="28" y2="1.5" stroke="#3B9EFF" stroke-width="2" stroke-dasharray="5,3" /></svg><span class="text-[11px] text-[#B4BAC9] font-mono">固收+指引</span></div>
              <div class="flex items-center space-x-2"><div class="w-7 h-[2.5px] bg-[#3B9EFF] rounded-full"></div><span class="text-[11px] text-[#B4BAC9] font-mono">实际净值</span></div>
            </div>
          </div>
        </div>

        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>产品表现与收益归因 · 信用择券超额 / 久期择时超额</h3>
          </div>
          <div class="p-5 space-y-5">
            <div class="flex items-center space-x-3 bg-[#0D1520] border border-[#3B9EFF]/25 rounded-lg px-4 py-2.5">
              <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] shrink-0 animate-pulse"></div>
              <span class="text-xs text-[#3B9EFF] font-mono tracking-wide">LIVE &nbsp;·&nbsp; 实时调用固收组合分析系统归因数据</span>
              <div class="ml-auto flex items-center space-x-2">
                <div class="w-1.5 h-1.5 rounded-full bg-[#34C759]"></div>
                <span class="text-[11px] font-mono text-[#94A3B8]">最后同步 09:47:32</span>
              </div>
            </div>
            <div class="space-y-3">
              <div class="flex items-center pl-[92px] space-x-5 mb-1">
                <div class="flex items-center space-x-1.5"><div class="w-3 h-2 rounded-sm bg-[#3B9EFF]/75"></div><span class="text-[11px] text-[#94A3B8] font-mono">久期择时超额 (bps)</span></div>
                <div class="flex items-center space-x-1.5"><div class="w-3 h-2 rounded-sm bg-[#3B9EFF]/75"></div><span class="text-[11px] text-[#94A3B8] font-mono">信用择券超额 (bps)</span></div>
              </div>
              <div v-for="item in FICC_ATTRIBUTION_DATA" :key="item.name" class="flex items-center space-x-3">
                <span class="text-[11px] text-[#B4BAC9] w-[88px] shrink-0 text-right font-mono">{{ item.name }}</span>
                <div class="flex-1 h-6 bg-[#1A1E2B] rounded overflow-hidden flex">
                  <div :style="{ width: `${Math.abs(item.timing) / 20 * 100}%`, backgroundColor: item.timing < 0 ? '#FF3B30' : '#3B9EFF' }" class="h-full opacity-80"></div>
                  <div :style="{ width: `${item.selection / 20 * 100}%`, backgroundColor: '#3B9EFF' }" class="h-full opacity-80"></div>
                </div>
                <div class="flex space-x-2 shrink-0 w-28 justify-end">
                  <span :class="cn('text-[11px] font-mono w-12 text-right', item.timing >= 0 ? 'text-[#3B9EFF]' : 'text-[#FF3B30]')">{{ item.timing >= 0 ? '+' : '' }}{{ item.timing }}</span>
                  <span class="text-[11px] font-mono text-[#3B9EFF] w-12 text-right">+{{ item.selection }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>固收策略红黑榜 · 本期综合评估</h3>
          </div>
          <div class="p-5 grid grid-cols-2 gap-5">
            <div>
              <div class="flex items-center space-x-2 mb-3">
                <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF]"></div>
                <span class="text-[11px] font-mono text-[#3B9EFF] uppercase tracking-wider">Top 5 优选策略</span>
              </div>
              <div class="space-y-2">
                <div v-for="(s, i) in FICC_TOP_STRATEGIES" :key="i" class="bg-[#1A1E2B] border border-[#3B9EFF]/10 rounded-lg px-4 py-3 flex items-center justify-between hover:border-[#3B9EFF]/25 transition-colors">
                  <div class="flex items-center space-x-3">
                    <span class="text-[11px] font-bold font-mono text-[#3B9EFF]/50 w-4 shrink-0">#{{ i + 1 }}</span>
                    <div>
                      <div class="text-[13px] font-medium text-[#E8ECF4]">{{ s.name }}</div>
                      <div class="text-[11px] text-[#94A3B8] font-mono mt-0.5">{{ s.type }}</div>
                    </div>
                  </div>
                  <div class="text-right shrink-0 ml-3">
                    <div class="text-[13px] font-bold font-mono text-[#3B9EFF]">{{ s.return }}</div>
                    <div class="text-[11px] text-[#94A3B8] font-mono">夏普 {{ s.sharpe }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <div class="flex items-center space-x-2 mb-3">
                <div class="w-1.5 h-1.5 rounded-full bg-[#FF3B30] animate-pulse"></div>
                <span class="text-[11px] font-mono text-[#FF3B30] uppercase tracking-wider">需检视劣后策略</span>
                <span class="text-[11px] font-mono text-[#FF3B30]/60 bg-[#FF3B30]/10 border border-[#FF3B30]/20 px-1.5 py-1 rounded">预警</span>
              </div>
              <div class="space-y-2">
                <div v-for="(s, i) in FICC_BOTTOM_STRATEGIES" :key="i" class="bg-[#1A1E2B] border border-[#FF3B30]/15 rounded-lg px-4 py-3 flex items-center justify-between hover:border-[#FF3B30]/30 transition-colors">
                  <div class="flex items-center space-x-3">
                    <div class="w-1 h-8 rounded-full bg-[#FF3B30]/50 shrink-0"></div>
                    <div>
                      <div class="text-[13px] font-medium text-[#E8ECF4]">{{ s.name }}</div>
                      <div class="text-[11px] text-[#FF3B30]/70 font-mono mt-0.5">{{ s.issue }}</div>
                    </div>
                  </div>
                  <div class="text-right shrink-0 ml-3">
                    <div class="text-[13px] font-bold font-mono text-[#FF3B30]">{{ s.return }}</div>
                    <div class="text-[11px] text-[#94A3B8] font-mono">最大回撤 {{ s.maxdd }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ 上期决议胜率复盘 ══ -->
        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>上期决议胜率复盘 · 2026 Q1</h3>
            <span class="text-[11px] font-mono px-2.5 py-1 rounded border border-[#3B9EFF]/30 text-[#3B9EFF] bg-[#3B9EFF]/6">复盘区间: 2025.12.20 — 2026.03.28</span>
          </div>

          <!-- 汇总文案 -->
          <div class="px-5 py-3 border-b border-[#252A3A] bg-[#1A1E2B]/50">
            <p class="text-[12px] font-mono leading-relaxed text-[#B4BAC9]">
              上期共对
              <span class="text-[#E8ECF4] font-bold">{{ FICC_PREV_REVIEW_SUMMARY.totalDirectional }}</span>
              项资产给出明确方向指引，其中
              <span class="font-bold" :class="FICC_PREV_REVIEW_SUMMARY.winRate >= 70 ? 'text-[#34C759]' : 'text-[#3B9EFF]'">{{ FICC_PREV_REVIEW_SUMMARY.correctCount }}</span>
              项方向正确，整体胜率
              <span class="text-[#3B9EFF] font-bold tabular-nums">{{ FICC_PREV_REVIEW_SUMMARY.winRate }}%</span>。
              <template v-if="FICC_PREV_REVIEW_SUMMARY.bestAsset">
                其中【<span class="text-[#34C759] font-bold">{{ FICC_PREV_REVIEW_SUMMARY.bestAsset }}</span>】产生显著正贡献（{{ FICC_PREV_REVIEW_SUMMARY.bestChange }}）。
              </template>
              <template v-if="FICC_PREV_REVIEW_SUMMARY.missAssets.length">
                【<span class="text-[#FF3B30]">{{ FICC_PREV_REVIEW_SUMMARY.missAssets.join('、') }}</span>】出现方向偏差。
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
                  <th class="px-3 py-2 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">细分策略</th>
                  <th class="px-3 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">上期委员会观点</th>
                  <th class="px-3 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] whitespace-nowrap">上期决策点位</th>
                  <th class="px-3 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] whitespace-nowrap">当前实际点位</th>
                  <th class="px-3 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348]">实际涨跌幅</th>
                  <th class="px-3 py-2 text-center text-[11px] font-bold text-[#94A3B8]">观点验证</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="row in FICC_PREV_REVIEW_ROWS" :key="row.asset"
                  class="hover:bg-[#1A1E2B]/40 transition-colors"
                  :class="row.verdict === 'wrong' ? 'bg-[#FF3B30]/3' : row.verdict === 'correct' ? 'bg-[#34C759]/2' : ''">
                  <td class="px-3 py-2.5 font-semibold text-[12px] text-[#E8ECF4] border-r border-[#2E3348]">{{ row.asset }}</td>
                  <td class="px-3 py-2.5 text-center border-r border-[#2E3348]">
                    <span class="text-[11px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap"
                      :class="VOTE_CONSENSUS_STYLE[row.prevView]">{{ row.prevView }}</span>
                  </td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-[11px] text-[#94A3B8] border-r border-[#2E3348]">{{ row.prevPoint }}</td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-[11px] font-bold text-[#E8ECF4] border-r border-[#2E3348]">{{ row.currPoint }}</td>
                  <td class="px-3 py-2.5 text-center tabular-nums text-[12px] font-bold border-r border-[#2E3348]"
                    :class="row.changeVal > 0 ? 'text-[#F04864]' : row.changeVal < 0 ? 'text-[#34C759]' : 'text-[#94A3B8]'">
                    {{ row.changeStr }}
                  </td>
                  <td class="px-3 py-2.5 text-center">
                    <span class="text-[11px] font-bold" :class="{
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
          <div class="px-5 py-2 border-t border-[#2E3348] bg-[#161922] flex flex-wrap items-center gap-4 text-[11px] font-mono text-[#64748B]">
            <span class="text-[#34C759]">✓ 方向正确</span>
            <span class="text-[#FF3B30]">✗ 方向偏差</span>
            <span class="text-[#3B9EFF]">● 震荡区间内</span>
            <span class="text-[#3B9EFF]">△ 超出震荡区间</span>
            <span class="ml-auto opacity-70">bp型：负值=利率下行=债券价格上涨</span>
          </div>
        </div>

        <!-- ══ 量化模型锚点 ═══ -->
        <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div
            class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between gap-3 cursor-pointer select-none hover:bg-[#2A3044]/20 transition-colors duration-200"
            role="button"
            :aria-expanded="showModelAnchors"
            tabindex="0"
            @click="showModelAnchors = !showModelAnchors"
            @keydown.enter.prevent="showModelAnchors = !showModelAnchors"
            @keydown.space.prevent="showModelAnchors = !showModelAnchors"
          >
            <h3 class="am-title-l2 min-w-0 flex-1"><div class="am-title-bar"></div>量化模型锚点 · 固收参考建议</h3>
            <button
              type="button"
              @click.stop="showModelAnchors = !showModelAnchors"
              class="shrink-0 text-[#3B9EFF] text-xs font-mono flex items-center gap-1.5 px-1.5 py-1 rounded border border-[#3B9EFF]/25 bg-[#3B9EFF]/5 hover:bg-[#3B9EFF]/10 transition-colors duration-200"
            >
              <span>{{ showModelAnchors ? '收起' : '展开' }}</span>
              <component :is="showModelAnchors ? ArrowUp : ArrowDown" class="w-3.5 h-3.5" />
            </button>
          </div>
          <Transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 -translate-y-1"
          >
            <div v-show="showModelAnchors" class="p-5 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div
                v-for="m in FICC_MODEL_OUTPUTS" :key="m.name"
                :class="cn(
                  'bg-[#1A1E2B] border rounded-xl p-4 flex flex-col min-h-0 transition-all duration-200',
                  m.highlight ? 'border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.07)]' : 'border-[#252A3A] operable-zone hover:border-[#2E3348]'
                )"
              >
                <div>
                  <span
                    class="text-[11px] font-mono px-2 py-1 rounded-full border"
                    :style="{ color: m.color, borderColor: m.color + '40', backgroundColor: m.color + '15' }"
                  >{{ m.badge }}</span>
                  <div class="text-[15px] font-bold text-white mt-1.5">{{ m.name }}</div>
                  <p class="text-xs text-[#94A3B8] mt-0.5 leading-relaxed">{{ m.desc }}</p>
                </div>
                <div class="mt-3 rounded-lg bg-[#161922] border border-[#252A3A] px-3 py-2.5 flex flex-col gap-0.5">
                  <div class="text-[11px] text-[#64748B] font-mono uppercase tracking-wider">建议锚点</div>
                  <div class="flex flex-col gap-0.5">
                    <div class="text-xs text-[#B4BAC9]">{{ m.anchorLabel }}</div>
                    <div
                      class="text-lg font-bold font-mono tabular-nums text-[#E8ECF4] tracking-tight"
                      :class="m.highlight ? 'text-[#3B9EFF]' : ''"
                    >{{ m.anchorValue }}</div>
                    <div v-if="m.anchorHint" class="text-[11px] font-mono text-[#6B7280]">{{ m.anchorHint }}</div>
                  </div>
                </div>
                <div
                  class="mt-auto pt-3 border-t border-[#252A3A] flex items-center gap-2 w-full"
                  :class="m.showSandbox ? 'justify-between' : 'justify-end'"
                >
                  <button
                    v-if="m.showSandbox"
                    type="button"
                    @click="showSAASandbox = true"
                    class="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
                  >
                    <span>进入沙盘</span>
                    <div class="w-0.5 h-3 bg-current rounded-sm shrink-0"></div>
                  </button>
                  <button
                    type="button"
                    @click.stop="openFiccModelCenter"
                    class="text-[#3B9EFF] text-xs font-mono flex items-center gap-0.5 hover:opacity-90 transition-opacity shrink-0"
                  >
                    <div class="w-1 h-3 bg-current rounded-sm shrink-0"></div>
                    <span>详情</span>
                  </button>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <!-- ═══ 投票与聚合矩阵 (原 Step 3) ═══ -->
      <div v-if="activeTab === 'decision'" class="space-y-4 pb-4">

        <!-- ═══ 投票尚未开始提示 ═══ -->
        <div v-if="ficcVoteCount === 0" class="flex items-center gap-3 bg-[#3B9EFF]/8 border border-[#3B9EFF]/20 rounded-xl px-5 py-3">
          <div class="w-8 h-8 rounded-full bg-[#3B9EFF]/15 flex items-center justify-center shrink-0">
            <div class="w-1.5 h-4 bg-[#3B9EFF] rounded-sm shrink-0"></div>
          </div>
          <div>
            <div class="text-[13px] font-medium text-[#3B9EFF]">尚无委员提交投票</div>
            <div class="text-xs text-[#94A3B8] mt-0.5">投票数据将在委员提交后自动汇总。请确认投票窗口已开启且委员已完成会前填报。</div>
          </div>
        </div>

        <!-- ══ 维度切换：月度策略投票 | 季度观点展望 ══ -->
        <div class="flex items-center gap-3">
          <div class="inline-flex bg-[#1A1E2B] border border-[#252A3A] rounded-lg p-0.5 gap-0.5">
            <button
              @click="ficcDecisionDimension = 'monthly'"
              :class="cn('px-5 py-2 rounded-md text-[13px] font-mono font-semibold transition-all duration-150',
                ficcDecisionDimension === 'monthly'
                  ? 'bg-[#3B9EFF]/12 border border-[#3B9EFF]/30 text-[#3B9EFF]'
                  : 'text-[#4A5568] hover:text-[#94A3B8]')"
            >月度策略投票</button>
            <button
              @click="ficcDecisionDimension = 'quarterly'"
              :class="cn('px-5 py-2 rounded-md text-[13px] font-mono font-semibold transition-all duration-150',
                ficcDecisionDimension === 'quarterly'
                  ? 'bg-[#3B9EFF]/12 border border-[#3B9EFF]/30 text-[#3B9EFF]'
                  : 'text-[#4A5568] hover:text-[#94A3B8]')"
            >季度观点展望</button>
          </div>
          <span class="text-[11px] font-mono text-[#4A5568]">
            {{ ficcDecisionDimension === 'monthly' ? `${FICC_ASSET_LIST.length} 项月度资产` : `${FICC_QUARTERLY_ASSET_LIST.length} 项季度资产` }}
          </span>
        </div>

        <!-- ══ FICC 观点投票分布汇总矩阵 ══ -->
        <div v-if="ficcDecisionDimension === 'monthly'" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>FICC 月度观点 · 投票分布矩阵</h3>
            <span class="text-[12px] font-mono text-[#94A3B8]">{{ FICC_MEMBERS.length }} 名委员 · {{ FICC_ASSET_LIST.length }} 项资产</span>
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
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">大类</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">细分策略</th>
                  <th rowspan="2" class="px-3 py-2 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">标的/基准指数</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle whitespace-nowrap">当前点位</th>
                  <th colspan="5" class="px-2 py-1.5 text-center text-[11px] font-bold text-[#3B9EFF] border-r border-[#2E3348]">票数分布（各档投票人数）</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle whitespace-nowrap">委员会观点</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] align-middle whitespace-nowrap">对应点位区间</th>
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
                <tr v-for="row in FICC_DIST_ROWS" :key="row.细分策略" class="hover:bg-[#1A1E2B]/40 transition-colors">
                  <!-- 大类：仅每组首行渲染，使用 rowspan 合并 -->
                  <td v-if="row.isFirstInGroup" :rowspan="row.groupSpan"
                    class="px-1 py-2 text-center text-[11px] font-bold tracking-widest border-r border-[#2E3348] align-middle"
                    :class="row.大类 === '固收' ? 'text-[#3B9EFF] bg-[#3B9EFF]/4' : row.大类 === '含权' ? 'text-[#3B9EFF] bg-[#3B9EFF]/4' : 'text-[#3B9EFF] bg-[#3B9EFF]/4'">
                    <span style="writing-mode:vertical-rl;letter-spacing:0.2em">{{ row.大类 }}</span>
                  </td>
                  <td class="px-2 py-2.5 font-semibold text-[12px] text-[#E8ECF4] border-r border-[#2E3348] whitespace-nowrap">{{ row.细分策略 }}</td>
                  <td class="px-3 py-2.5 text-[11px] text-[#64748B] truncate border-r border-[#2E3348]">{{ row.标的指数 }}</td>
                  <td class="px-2 py-2.5 text-center tabular-nums text-[11px] font-bold text-[#3B9EFF]/80 border-r border-[#2E3348]">{{ row.当前点位 }}</td>
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
                    <span v-else class="text-[#303848] text-[11px] select-none">—</span>
                  </td>
                  <!-- 委员会观点 -->
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span v-if="row.totalVotes > 0"
                      class="inline-block text-[11px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap"
                      :class="VOTE_CONSENSUS_STYLE[row.consensusLevel]">{{ row.consensusLevel }}</span>
                    <span v-else class="text-[#3A4555]">—</span>
                  </td>
                  <!-- 对应点位区间 -->
                  <td class="px-2 py-2.5 text-center tabular-nums text-[11px] font-mono"
                    :class="row.totalVotes > 0 ? 'text-[#3B9EFF]' : 'text-[#3A4555]'">{{ row.rangeStr }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- ══ 投票分布可视化摘要（堆叠条） ══ -->
          <div v-if="FICC_DIST_ROWS.some(r => r.totalVotes > 0)" class="border-t border-[#252A3A] px-5 py-3 space-y-2">
            <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">投票分布可视化</div>
            <div v-for="row in FICC_DIST_ROWS" :key="row.细分策略" v-show="row.totalVotes > 0" class="flex items-center gap-3">
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
          <div class="px-5 py-2 border-t border-[#2E3348] bg-[#161922] flex items-center justify-between text-[11px] text-[#64748B] font-mono">
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

        <!-- ══ 季度观点展望 · 投票分布矩阵 ══ -->
        <div v-if="ficcDecisionDimension === 'quarterly'" class="bg-[#202431] border border-[#3B9EFF]/20 rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar bg-[#3B9EFF]"></div>FICC 季度观点展望 · 投票分布矩阵</h3>
            <div class="flex items-center gap-3">
              <span class="text-[11px] font-mono px-2 py-1 rounded border border-[#3B9EFF]/25 bg-[#3B9EFF]/8 text-[#3B9EFF]">幅度档位 ×3 宽于月度</span>
              <span class="text-[12px] font-mono text-[#94A3B8]">{{ FICC_MEMBERS.length }} 名委员 · {{ FICC_QUARTERLY_ASSET_LIST.length }} 项资产</span>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full border-collapse table-fixed font-mono text-[12px]" style="min-width:920px">
              <colgroup>
                <col style="width:52px" />
                <col style="width:90px" />
                <col style="width:160px" />
                <col style="width:78px" />
                <col style="width:44px" />
                <col style="width:62px" />
                <col style="width:44px" />
                <col style="width:62px" />
                <col style="width:44px" />
                <col style="width:108px" />
                <col style="width:140px" />
              </colgroup>
              <thead class="bg-[#1A1E2B]">
                <tr class="border-b border-[#2E3348]">
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">大类</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">细分策略</th>
                  <th rowspan="2" class="px-3 py-2 text-left text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle">标的/基准指数</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#94A3B8] border-r border-[#2E3348] align-middle whitespace-nowrap">当前点位</th>
                  <th colspan="5" class="px-2 py-1.5 text-center text-[11px] font-bold text-[#3B9EFF] border-r border-[#2E3348]">票数分布（各档投票人数）</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#3B9EFF]/80 border-r border-[#2E3348] align-middle whitespace-nowrap">季度共识观点</th>
                  <th rowspan="2" class="px-2 py-2 text-center text-[11px] font-bold text-[#3B9EFF]/80 align-middle whitespace-nowrap">季度预期区间</th>
                </tr>
                <tr class="border-b-2 border-[#3B9EFF]/20">
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#00C9A7] border-r border-[#2E3348]/40">谨慎<br/><span class="text-[11px] opacity-50">1分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40 leading-tight">中性<br/>偏谨慎<br/><span class="text-[11px] opacity-50">2分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40">中性<br/><span class="text-[11px] opacity-50">3分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#3B9EFF] border-r border-[#2E3348]/40 leading-tight">中性<br/>偏乐观<br/><span class="text-[11px] opacity-50">4分</span></th>
                  <th class="px-1 py-1.5 text-center text-[11px] font-semibold text-[#F04864] border-r border-[#2E3348]">乐观<br/><span class="text-[11px] opacity-50">5分</span></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#252A3A]">
                <tr v-for="row in FICC_QUARTERLY_DIST_ROWS" :key="row.细分策略" class="hover:bg-[#1A1E2B]/40 transition-colors">
                  <td v-if="row.isFirstInGroup" :rowspan="row.groupSpan"
                    class="px-1 py-2 text-center text-[11px] font-bold tracking-widest border-r border-[#2E3348] align-middle"
                    :class="row.大类 === '固收' ? 'text-[#3B9EFF] bg-[#3B9EFF]/4' : row.大类 === '含权' ? 'text-[#3B9EFF] bg-[#3B9EFF]/4' : 'text-[#3B9EFF] bg-[#3B9EFF]/4'">
                    <span style="writing-mode:vertical-rl;letter-spacing:0.2em">{{ row.大类 }}</span>
                  </td>
                  <td class="px-2 py-2.5 font-semibold text-[12px] text-[#E8ECF4] border-r border-[#2E3348] whitespace-nowrap">{{ row.细分策略 }}</td>
                  <td class="px-3 py-2.5 text-[11px] text-[#64748B] truncate border-r border-[#2E3348]">{{ row.标的指数 }}</td>
                  <td class="px-2 py-2.5 text-center tabular-nums text-[11px] font-bold text-[#3B9EFF]/70 border-r border-[#2E3348]">{{ row.当前点位 }}</td>
                  <td v-for="(count, i) in row.dist" :key="i"
                    class="px-1 py-2.5 text-center transition-colors"
                    :class="[
                      i < 4 ? 'border-r border-[#2E3348]/40' : 'border-r border-[#2E3348]',
                      count > 0 && count === row.maxCount ? VOTE_DIST_HL_BG[i] : '',
                    ]">
                    <span v-if="count > 0" class="text-[13px] font-bold tabular-nums leading-none"
                      :class="count === row.maxCount ? VOTE_DIST_HL_TEXT[i] : 'text-[#B4BAC9]'">{{ count }}</span>
                    <span v-else class="text-[#303848] text-[11px] select-none">—</span>
                  </td>
                  <td class="px-2 py-2.5 text-center border-r border-[#2E3348]">
                    <span v-if="row.totalVotes > 0"
                      class="inline-block text-[11px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap"
                      :class="VOTE_CONSENSUS_STYLE[row.consensusLevel]">{{ row.consensusLevel }}</span>
                    <span v-else class="text-[#3A4555]">—</span>
                  </td>
                  <td class="px-2 py-2.5 text-center tabular-nums text-[11px] font-mono"
                    :class="row.totalVotes > 0 ? 'text-[#3B9EFF]' : 'text-[#3A4555]'">{{ row.rangeStr }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="px-5 py-2 border-t border-[#2E3348] bg-[#161922] flex items-center justify-between text-[11px] text-[#64748B] font-mono">
            <span>季度区间 = 当前点位 × (1 ± 季度幅度%) 或 收益率 ± 季度bp · 众数格高亮 · 观点为加权均值四舍五入</span>
            <span class="flex items-center gap-3">
              <span class="text-[#00C9A7]">▪ 谨慎</span>
              <span class="text-[#3B9EFF]">▪ 中性偏谨慎</span>
              <span class="text-[#3B9EFF]">▪ 中性</span>
              <span class="text-[#3B9EFF]">▪ 中性偏乐观</span>
              <span class="text-[#F04864]">▪ 乐观</span>
            </span>
          </div>
        </div>

        <!-- ══ 跨委员会共识参考（折叠） ══ -->
        <div class="border border-dashed border-[#2E3348]/50 rounded-xl overflow-hidden">
          <button
            @click="showFiccCrossPanel = !showFiccCrossPanel"
            class="w-full px-5 py-3 bg-[#11131A]/80 flex items-center justify-between hover:bg-[#11131A] transition-all duration-200"
          >
            <div class="flex items-center gap-2.5">
              <span class="text-[12px] font-mono text-[#3B9EFF]/60">⚡</span>
              <span class="text-[13px] font-medium text-[#6B7280]">展开全局跨委员会共识参考</span>
              <span class="text-[11px] font-mono px-1.5 py-0.5 rounded border border-dashed border-[#3B9EFF]/25 text-[#3B9EFF]/60">只读 · Mock</span>
            </div>
            <div class="w-0.5 h-3.5 bg-[#4A5568] rounded-full transition-transform duration-200 origin-center" :class="showFiccCrossPanel ? 'rotate-90' : ''"></div>
          </button>

          <div v-if="showFiccCrossPanel" class="border-t border-dashed border-[#2E3348]/50 bg-[#11131A]/90 p-4 space-y-4">

            <!-- Table A：混合投委会投票统计 -->
            <div>
              <div class="flex items-center gap-2 mb-2">
                <div class="w-1 h-3.5 rounded-full bg-[#3B9EFF]/40"></div>
                <span class="text-[11px] font-mono font-bold text-[#3B9EFF]/80 uppercase tracking-wider">A · 混合投委会投票统计（本期 Mock）</span>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full border-collapse table-fixed font-mono text-[11px]">
                  <thead>
                    <tr class="border-b border-dashed border-[#2E3348]/50 text-[#4A5568]">
                      <th class="px-3 py-1.5 text-left font-medium" style="width:100px">资产</th>
                      <th class="px-3 py-1.5 text-left font-medium">标的指数</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:60px">均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:90px">档位</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:130px">共识区间</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:70px">归属</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:90px">两委差异</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dashed divide-[#2E3348]/30">
                    <tr v-for="cfg in MIXED_ASSET_LIST" :key="cfg.id"
                      :class="FICC_SHARED_NAMES.has(cfg.细分策略) ? 'bg-[#3B9EFF]/4' : ''"
                      class="hover:bg-white/2 transition-colors">
                      <td class="px-3 py-2 font-semibold text-[#B4BAC9]">{{ cfg.细分策略 }}</td>
                      <td class="px-3 py-2 text-[#4A5568] truncate">{{ cfg.标的指数 }}</td>
                      <td class="px-2 py-2 text-center tabular-nums text-[#3B9EFF]">{{ CROSS_MIXED_MOCK[cfg.细分策略]?.toFixed(1) ?? '—' }}</td>
                      <td class="px-2 py-2 text-center">
                        <span v-if="CROSS_MIXED_MOCK[cfg.细分策略]" :class="[
                          'text-[11px] font-mono px-1 py-0.5 rounded border',
                          Math.round(CROSS_MIXED_MOCK[cfg.细分策略]) === 5 ? 'border-[#F04864]/30 text-[#F04864]' :
                          Math.round(CROSS_MIXED_MOCK[cfg.细分策略]) === 4 ? 'border-[#3B9EFF]/30 text-[#3B9EFF]' :
                          Math.round(CROSS_MIXED_MOCK[cfg.细分策略]) === 2 ? 'border-[#3B9EFF]/30 text-[#3B9EFF]' :
                          Math.round(CROSS_MIXED_MOCK[cfg.细分策略]) === 1 ? 'border-[#00C9A7]/30 text-[#00C9A7]' :
                          'border-[#3B9EFF]/30 text-[#3B9EFF]'
                        ]">{{ FICC_SCORE_LABELS[Math.round(CROSS_MIXED_MOCK[cfg.细分策略])] }}</span>
                      </td>
                      <td class="px-2 py-2 text-center tabular-nums text-[#3B9EFF]/80">
                        {{ CROSS_MIXED_MOCK[cfg.细分策略] ? calcFiccRangeStr(cfg, CROSS_MIXED_MOCK[cfg.细分策略]) : '—' }}
                      </td>
                      <td class="px-2 py-2 text-center">
                        <span v-if="FICC_SHARED_NAMES.has(cfg.细分策略)" class="text-[11px] font-mono px-1 py-0.5 rounded border border-dashed border-[#3B9EFF]/30 text-[#3B9EFF]/70">⚡ 共享</span>
                        <span v-else class="text-[11px] font-mono text-[#4A5568]">混合专有</span>
                      </td>
                      <!-- 两委差异 -->
                      <td class="px-2 py-2 text-center">
                        <template v-if="FICC_SHARED_NAMES.has(cfg.细分策略) && CROSS_MIXED_MOCK[cfg.细分策略]">
                          <span v-if="Math.abs(CROSS_MIXED_MOCK[cfg.细分策略] - getCrossFiccDiff(cfg.细分策略)) >= 1"
                            class="text-[11px] font-bold px-1.5 py-0.5 rounded bg-[#FF3B30]/10 border border-[#FF3B30]/25 text-[#FF3B30]">
                            ⚠ 差异{{ Math.abs(CROSS_MIXED_MOCK[cfg.细分策略] - getCrossFiccDiff(cfg.细分策略)).toFixed(1) }}
                          </span>
                          <span v-else class="text-[11px] font-mono text-[#34C759]">一致</span>
                        </template>
                        <span v-else class="text-[11px] font-mono text-[#4A5568]">—</span>
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
                <span class="text-[11px] font-mono font-bold text-[#3B9EFF]/80 uppercase tracking-wider">B · 公司级全局大类配置共识（两委均值算术平均）</span>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full border-collapse table-fixed font-mono text-[11px]">
                  <thead>
                    <tr class="border-b border-dashed border-[#2E3348]/50 text-[#4A5568]">
                      <th class="px-3 py-1.5 text-left font-medium" style="width:100px">资产</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:70px">大类</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:55px">FICC均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:55px">混合均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:60px">全局均值</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:90px">全局档位</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:130px">全局共识区间</th>
                      <th class="px-2 py-1.5 text-center font-medium" style="width:70px">来源</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-dashed divide-[#2E3348]/30">
                    <tr v-for="row in FICC_CROSS_GLOBAL_ITEMS" :key="row.name"
                      :class="row.source === '⚡共享' ? 'bg-[#3B9EFF]/4' : row.source === '混合' ? 'bg-[#3B9EFF]/3' : ''"
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
                          'text-[11px] px-1 py-0.5 rounded border',
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
                          row.source === '混合' ? 'border-[#3B9EFF]/25 text-[#3B9EFF]/60' :
                          'border-[#3B9EFF]/25 text-[#3B9EFF]/60'
                        ]">{{ row.source }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="mt-2 text-[11px] font-mono text-[#3A4555] px-1">
                ⚡ 共享资产全局均值 = (FICC均值 + 混合均值) / 2 · 专有资产取所属委员会均值 · 混合数据为本期Mock
              </div>
            </div>

          </div>
        </div>

        <!-- ── 委员投票区 (仅委员可见且未投票) ── -->
        <div v-if="isFiccMember && !ficcSelfVoteSubmitted" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#3B9EFF] to-[#3B9EFF] flex items-center justify-center shadow-[0_0_14px_rgba(59,158,255,0.25)]">
                <div class="w-1.5 h-4 bg-white/90 rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="am-title-l2"><div class="am-title-bar"></div>下月 FICC 策略投票 · 子策略观点</h3>
                <p class="text-[11px] font-mono text-[#6B7280] mt-0.5">未来1个月操作计划 / 建议 / 点位预测</p>
              </div>
            </div>
            <span class="text-[11px] font-mono px-3 py-1.5 rounded-lg border" :class="ROLE_BADGE_CLASSES[activeRole] || 'bg-[#94A3B8]/10 border-[#94A3B8]/25 text-[#94A3B8]'">{{ activeRole }}</span>
          </div>
          <div class="p-6 space-y-5">

            <!-- Q1: 现金 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 space-y-4">
              <div class="flex items-center space-x-2.5 pb-3 border-b border-[#252A3A]">
                <span class="text-[11px] font-bold font-mono px-2 py-1 rounded bg-[#94A3B8]/15 border border-[#94A3B8]/30 text-[#94A3B8]">Q1</span>
                <span class="text-[13px] font-bold text-[#E8ECF4]">现金</span>
                <span class="text-xs font-mono text-[#64748B]">货币市场 · 久期与杠杆管理</span>
              </div>
              <div class="grid grid-cols-2 gap-x-8 gap-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">久期</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['谨慎','中性','乐观']" :key="opt" @click="ficcForm.q1Duration = opt"
                      :class="cn('px-3.5 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q1Duration === opt
                          ? opt === '乐观' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '谨慎' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">杠杆</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['谨慎','中性','乐观']" :key="opt" @click="ficcForm.q1Leverage = opt"
                      :class="cn('px-3.5 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q1Leverage === opt
                          ? opt === '乐观' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '谨慎' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="flex items-center space-x-3 bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-2.5">
                  <span class="text-xs font-mono text-[#94A3B8] shrink-0">R007（月均）</span>
                  <input v-model.number="ficcForm.q1R007" type="number" step="0.01" placeholder="1.72" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                  <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
                </div>
                <div class="flex items-center space-x-3 bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-2.5">
                  <span class="text-xs font-mono text-[#94A3B8] shrink-0">1年存单（月末）</span>
                  <input v-model.number="ficcForm.q1CD1Y" type="number" step="0.01" placeholder="1.85" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                  <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
                </div>
              </div>
            </div>

            <!-- Q2: 稳定 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 space-y-4">
              <div class="flex items-center space-x-2.5 pb-3 border-b border-[#252A3A]">
                <span class="text-[11px] font-bold font-mono px-2 py-1 rounded bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 text-[#3B9EFF]">Q2</span>
                <span class="text-[13px] font-bold text-[#E8ECF4]">稳定</span>
                <span class="text-xs font-mono text-[#64748B]">定期存款类资产</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[13px] text-[#B4BAC9] w-24 shrink-0">配置仓位</span>
                <div class="flex space-x-2">
                  <button v-for="opt in ['超配','平配','低配']" :key="opt" @click="ficcForm.q2Position = opt"
                    :class="cn('px-4 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                      ficcForm.q2Position === opt
                        ? opt === '超配' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : opt === '低配' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                          : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                        : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                </div>
              </div>
              <div class="flex items-center space-x-3 bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-2.5">
                <span class="text-xs font-mono text-[#94A3B8] shrink-0">1Y 定存（平均水平）</span>
                <input v-model.number="ficcForm.q2Deposit1Y" type="number" step="0.01" placeholder="1.30" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
              </div>
            </div>

            <!-- Q3: 债券 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 space-y-4">
              <div class="flex items-center space-x-2.5 pb-3 border-b border-[#252A3A]">
                <span class="text-[11px] font-bold font-mono px-2 py-1 rounded bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 text-[#3B9EFF]">Q3</span>
                <span class="text-[13px] font-bold text-[#E8ECF4]">债券</span>
                <span class="text-xs font-mono text-[#64748B]">利率债 · 信用债 · 收益率口径</span>
              </div>
              <div class="grid grid-cols-2 gap-x-8 gap-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">走势</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['看上','看平','看下']" :key="opt" @click="ficcForm.q3Trend = opt"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q3Trend === opt
                          ? opt === '看下' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '看上' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">期限</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['1Y内','1-3Y','3-5Y']" :key="opt" @click="ficcForm.q3Term = opt"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q3Term === opt
                          ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">信用利差</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['走阔','稳定','收窄']" :key="opt" @click="ficcForm.q3CreditSpread = opt"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q3CreditSpread === opt
                          ? opt === '收窄' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '走阔' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">量化</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['超配','平配','低配']" :key="opt" @click="ficcForm.q3Quant = opt"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q3Quant === opt
                          ? opt === '超配' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '低配' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3 pt-1">
                <div class="flex items-center space-x-3 bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-2.5">
                  <span class="text-xs font-mono text-[#94A3B8] shrink-0">10年国债（月末）</span>
                  <input v-model.number="ficcForm.q3Bond10Y" type="number" step="0.01" placeholder="2.15" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                  <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
                </div>
                <div class="flex items-center space-x-3 bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-2.5">
                  <span class="text-xs font-mono text-[#94A3B8] shrink-0">3年AA+（月末）</span>
                  <input v-model.number="ficcForm.q3BondA3Y" type="number" step="0.01" placeholder="2.38" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                  <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
                </div>
              </div>
            </div>

            <!-- Q4: 含权 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 space-y-4">
              <div class="flex items-center space-x-2.5 pb-3 border-b border-[#252A3A]">
                <span class="text-[11px] font-bold font-mono px-2 py-1 rounded bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 text-[#3B9EFF]">Q4</span>
                <span class="text-[13px] font-bold text-[#E8ECF4]">含权</span>
                <span class="text-xs font-mono text-[#64748B]">可转债 · 二级债基</span>
              </div>
              <div class="grid grid-cols-2 gap-x-8 gap-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">走势</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['下跌','震荡','上涨']" :key="opt" @click="ficcForm.q4Trend = opt"
                      :class="cn('px-3.5 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q4Trend === opt
                          ? opt === '上涨' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '下跌' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">结构</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['转债','二级债基','其他']" :key="opt" @click="toggleFiccQ4Structure(opt)"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-lg border transition-all duration-150 font-medium',
                        ficcForm.q4Structure.includes(opt)
                          ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-3 bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-2.5">
                <span class="text-xs font-mono text-[#94A3B8] shrink-0">转债等权（月度涨跌幅）</span>
                <input v-model.number="ficcForm.q4CB" type="number" step="0.1" placeholder="1.2" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
              </div>
            </div>

            <!-- Q5: 创新 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 space-y-4">
              <div class="flex items-center space-x-2.5 pb-3 border-b border-[#252A3A]">
                <span class="text-[11px] font-bold font-mono px-2 py-1 rounded bg-[#F97316]/15 border border-[#F97316]/30 text-[#F97316]">Q5</span>
                <span class="text-[13px] font-bold text-[#E8ECF4]">创新</span>
                <span class="text-xs font-mono text-[#64748B]">REITs · 另类固收</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[13px] text-[#B4BAC9] w-24 shrink-0">配置仓位</span>
                <div class="flex space-x-2">
                  <button v-for="opt in ['超配','平配','低配']" :key="opt" @click="ficcForm.q5Position = opt"
                    :class="cn('px-4 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                      ficcForm.q5Position === opt
                        ? opt === '超配' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : opt === '低配' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                          : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                        : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                </div>
              </div>
            </div>

            <!-- Q6: 跨境固收 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 space-y-4">
              <div class="flex items-center space-x-2.5 pb-3 border-b border-[#252A3A]">
                <span class="text-[11px] font-bold font-mono px-2 py-1 rounded bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 text-[#3B9EFF]">Q6</span>
                <span class="text-[13px] font-bold text-[#E8ECF4]">跨境固收</span>
                <span class="text-xs font-mono text-[#64748B]">美债 · 收益率口径</span>
              </div>
              <div class="grid grid-cols-3 gap-x-6 gap-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">走势</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['看上','看平','看下']" :key="opt" @click="ficcForm.q6Trend = opt"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q6Trend === opt
                          ? opt === '看下' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '看上' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">期限</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['2Y','5Y','10Y']" :key="opt" @click="ficcForm.q6Term = opt"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q6Term === opt
                          ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#B4BAC9] w-16 shrink-0">信用利差</span>
                  <div class="flex space-x-2">
                    <button v-for="opt in ['走阔','稳定','收窄']" :key="opt" @click="ficcForm.q6CreditSpread = opt"
                      :class="cn('px-3 py-1.5 text-[13px] rounded-full border transition-all duration-150 font-bold',
                        ficcForm.q6CreditSpread === opt
                          ? opt === '收窄' ? 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                            : opt === '走阔' ? 'bg-[#FF3B30]/15 border-[#FF3B30]/40 text-[#FF3B30]'
                            : 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]'
                          : 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]')">{{ opt }}</button>
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-3 gap-3 pt-1">
                <div class="flex items-center space-x-2 bg-[#161922] border border-[#252A3A] rounded-lg px-3 py-2.5">
                  <span class="text-xs font-mono text-[#94A3B8] shrink-0">2Y美债</span>
                  <input v-model.number="ficcForm.q6USD2Y" type="number" step="0.01" placeholder="4.52" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                  <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
                </div>
                <div class="flex items-center space-x-2 bg-[#161922] border border-[#252A3A] rounded-lg px-3 py-2.5">
                  <span class="text-xs font-mono text-[#94A3B8] shrink-0">10Y美债</span>
                  <input v-model.number="ficcForm.q6USD10Y" type="number" step="0.01" placeholder="4.38" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                  <span class="text-xs font-mono text-[#64748B] shrink-0">%</span>
                </div>
                <div class="flex items-center space-x-2 bg-[#161922] border border-[#252A3A] rounded-lg px-3 py-2.5">
                  <span class="text-xs font-mono text-[#94A3B8] shrink-0">人民币汇率</span>
                  <input v-model.number="ficcForm.q6USDCNY" type="number" step="0.001" placeholder="7.280" class="flex-1 bg-transparent text-right text-[13px] font-mono font-bold text-[#E8ECF4] outline-none placeholder-[#3A4555] min-w-0" />
                </div>
              </div>
            </div>

            <!-- 附加题 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 space-y-3">
              <div class="flex items-center space-x-2.5 pb-3 border-b border-[#252A3A]">
                <span class="text-[11px] font-bold font-mono px-2 py-1 rounded bg-[#94A3B8]/15 border border-[#94A3B8]/30 text-[#94A3B8]">附加</span>
                <span class="text-[13px] font-bold text-[#E8ECF4]">最看好的机会与重点提示的风险</span>
              </div>
              <textarea v-model="ficcForm.comment" rows="4"
                class="w-full bg-[#161922] border border-[#2E3348] rounded-xl px-5 py-4 text-[15px] text-[#B4BAC9] placeholder-[#3A4555] outline-none focus:border-[#3B9EFF]/45 focus:shadow-[0_0_20px_rgba(59,158,255,0.06)] transition-all resize-none leading-relaxed"
                placeholder="请输入您最看好的一个机会，以及需要重点提示的一个风险（如有）..."></textarea>
              <div class="flex justify-end"><span class="text-[11px] font-mono text-[#4A5568]">{{ ficcForm.comment.length }} 字</span></div>
            </div>

            <!-- 实时票型得分预览 -->
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-4">
              <div class="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider mb-3">实时票型得分预览（提交后自动聚合）</div>
              <div class="grid grid-cols-3 gap-3">
                <div v-for="dim in FICC_DIM_KEYS" :key="dim" class="bg-[#202431] border border-[#252A3A] rounded-lg px-4 py-3 text-center">
                  <div class="text-[11px] font-mono text-[#64748B] mb-1">{{ FICC_DIM_LABELS[dim] }}</div>
                  <div class="text-[20px] font-mono font-bold" :style="{ color: FICC_DIM_COLORS[dim] }">{{ ficcDraftScores[dim] }}<span class="text-[11px] text-[#64748B]">%</span></div>
                  <div class="mt-1.5 h-1 bg-[#161922] rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-300" :style="{ width: `${ficcDraftScores[dim]}%`, backgroundColor: FICC_DIM_COLORS[dim] }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="p-5 border-t border-[#252A3A]">
            <button @click="submitFiccVote"
              class="w-full py-3.5 rounded-xl font-bold text-[15px] transition-all duration-200 bg-gradient-to-r from-[#3B9EFF] to-[#3B9EFF] text-white shadow-[0_4px_24px_rgba(59,158,255,0.3)] hover:shadow-[0_4px_36px_rgba(59,158,255,0.45)] active:scale-[0.99]"
            >提交我的投票</button>
          </div>
        </div>

        <!-- ── 委员已提交只读确认 ── -->
        <div v-if="isFiccMember && ficcSelfVoteSubmitted" class="bg-[#202431] border border-[#34C759]/20 rounded-xl overflow-hidden">
          <div class="bg-gradient-to-r from-[#34C759]/10 to-[#202431] border-b border-[#34C759]/15 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-full bg-[#34C759]/15 border border-[#34C759]/30 flex items-center justify-center">
                <div class="w-1.5 h-4 bg-[#00C9A7] rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="text-[15px] font-bold text-[#34C759]">投票已提交</h3>
                <p class="text-[11px] font-mono text-[#94A3B8] mt-0.5">提交于 {{ ficcSelfVoteSubmitted.submittedAt }} · 数据已锁定</p>
              </div>
            </div>
            <span class="text-[11px] font-mono text-[#34C759] bg-[#34C759]/10 border border-[#34C759]/20 px-2 py-1 rounded">只读</span>
          </div>
          <div class="p-6 grid grid-cols-3 gap-4">
            <div v-for="dim in FICC_DIM_KEYS" :key="dim" class="text-center bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-4">
              <div class="text-[11px] font-mono text-[#64748B] mb-1">{{ FICC_DIM_LABELS[dim] }}</div>
              <div class="text-[20px] font-mono font-bold" :style="{ color: FICC_DIM_COLORS[dim] }">{{ ficcSelfVoteSubmitted[dim] }}<span class="text-[13px] text-[#64748B]">%</span></div>
            </div>
          </div>
        </div>

        <!-- ── 委员隐私模式：仅显示本人票型建议分析 ── -->
        <div v-if="isMemberPrivateS3" class="bg-[#202431] border border-[#3B9EFF]/18 rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#3B9EFF]/10 to-[#202431] border-b border-[#3B9EFF]/15 px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar" style="background:#3B9EFF"></div>我的票型建议分析</h3>
            <span class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-2 py-1 rounded">隐私模式</span>
          </div>
          <div class="p-5 space-y-4">
            <div class="grid grid-cols-3 gap-3">
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3">
                <div class="text-[11px] font-mono text-[#64748B] mb-1">稳定资产仓位</div>
                <div class="text-[15px] font-mono font-bold text-[#3B9EFF]">{{ selfVoteSuggestion.positionTier }}</div>
                <div class="text-[11px] font-mono text-[#4A5568] mt-1">约 {{ selfVoteSuggestion.positionPct }}%</div>
              </div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3">
                <div class="text-[11px] font-mono text-[#64748B] mb-1">久期使用率</div>
                <div class="text-[15px] font-mono font-bold text-[#3B9EFF]">{{ selfVoteSuggestion.durationTier }}</div>
                <div class="text-[11px] font-mono text-[#4A5568] mt-1">低波 {{ selfVoteSuggestion.durationLowVol }} · 中低波 {{ selfVoteSuggestion.durationMidLowVol }}</div>
              </div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3">
                <div class="text-[11px] font-mono text-[#64748B] mb-1">含权使用率</div>
                <div class="text-[15px] font-mono font-bold text-[#3B9EFF]">{{ selfVoteSuggestion.equityTier }}</div>
                <div class="text-[11px] font-mono text-[#4A5568] mt-1">低波 ≤{{ selfVoteSuggestion.equityLowVol }} · 中低波 ≤{{ selfVoteSuggestion.equityMidLowVol }}</div>
              </div>
            </div>
            <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3 text-[11px] font-mono text-[#64748B] leading-relaxed">
              主任委员未提交决策前，仅展示本人票型生成分析；委员明细、全体均值及最终配置指引暂不可见。
            </div>
          </div>
        </div>

        <!-- ── FICC 投票结果矩阵 (主任/秘书可见；决策提交后全员可见) ── -->
        <div v-if="canViewFullS3Board" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>FICC 投票结果矩阵</h3>
            <div class="flex items-center space-x-3">
              <span class="text-[11px] font-mono text-[#94A3B8]">{{ ficcVoteCount }} / {{ FICC_MEMBERS.length }} 票已回收</span>
              <div class="w-20 h-1 bg-[#1A1E2B] rounded-full overflow-hidden">
                <div class="h-full bg-[#3B9EFF] rounded-full transition-all" :style="{ width: `${ficcVoteCount / FICC_MEMBERS.length * 100}%` }"></div>
              </div>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full border-collapse table-fixed">
              <thead>
                <tr class="border-b border-[#252A3A] bg-[#1A1E2B]">
                  <th class="px-5 py-3 text-left text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest" style="width:160px">委员</th>
                  <th v-for="dim in FICC_DIM_KEYS" :key="dim" class="px-4 py-3 text-center text-[11px] font-bold uppercase tracking-widest" :style="{ color: FICC_DIM_COLORS[dim] }">
                    {{ FICC_DIM_LABELS[dim] }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="m in FICC_MEMBERS" :key="m.id"
                  class="border-b border-[#1A1E2B]/60 hover:bg-[#1A1E2B]/30 transition-colors"
                >
                  <td class="px-5 py-3">
                    <div class="flex items-center space-x-3">
                      <div :class="cn(
                        'w-2 h-2 rounded-full shrink-0',
                        ficcBallots[m.id] ? 'bg-[#34C759] shadow-[0_0_4px_rgba(52,199,89,0.4)]' : 'bg-[#4A5568]'
                      )"></div>
                      <div>
                        <span class="text-[13px] font-medium text-[#E8ECF4]">{{ m.name }}</span>
                        <span v-if="m.id === 'f1'" class="text-[11px] font-mono text-[#3B9EFF] ml-1.5">主任委员</span>
                      </div>
                    </div>
                  </td>
                  <td v-for="dim in FICC_DIM_KEYS" :key="dim" class="px-4 py-3 text-center">
                    <template v-if="ficcBallots[m.id]">
                      <span class="text-[15px] font-mono" :class="ficcVoteCellStyle(dim, ficcBallots[m.id][dim])">
                        {{ ficcBallots[m.id][dim] }}<span class="text-[11px] text-[#64748B]">%</span>
                      </span>
                    </template>
                    <span v-else class="text-[11px] font-mono text-[#3A4555]">—</span>
                  </td>
                </tr>
                <!-- 均值行 -->
                <tr class="border-t-2 border-[#3B9EFF]/30 bg-[#1A1E2B]/60">
                  <td class="px-5 py-3">
                    <div class="flex items-center space-x-2">
                      <div class="w-1 h-3.5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
                      <span class="text-[13px] font-bold text-[#3B9EFF]">均值 Mean</span>
                    </div>
                  </td>
                  <td v-for="dim in FICC_DIM_KEYS" :key="dim" class="px-4 py-3 text-center">
                    <span class="text-[15px] font-mono font-bold" :style="{ color: FICC_DIM_COLORS[dim] }">
                      {{ ficcVoteMeans[dim] }}<span class="text-[11px] text-[#64748B]">%</span>
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="p-3 border-t border-[#252A3A] bg-[#1A1E2B]/30 flex items-center justify-between">
            <div class="flex items-center space-x-4">
              <div class="flex items-center space-x-1.5"><div class="w-2 h-2 rounded-full bg-[#34C759]"></div><span class="text-[11px] font-mono text-[#64748B]">最高值</span></div>
              <div class="flex items-center space-x-1.5"><div class="w-2 h-2 rounded-full bg-[#FF3B30]"></div><span class="text-[11px] font-mono text-[#64748B]">最低值</span></div>
            </div>
            <span class="text-[11px] font-mono text-[#64748B]">绿色 = 列最高 · 红色 = 列最低</span>
          </div>
        </div>

        <!-- ── 自动统计看板：三个仪表盘 ── -->
        <div v-if="canViewFullS3Board" class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar"></div>票型聚合看板 · 全员平均</h3>
            <div class="flex items-center space-x-2">
              <div class="w-1 h-3.5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
              <span class="text-[11px] font-mono text-[#94A3B8]">{{ ficcVoteCount }} 票聚合</span>
            </div>
          </div>
          <div class="p-5 grid grid-cols-3 gap-5">
            <div v-for="g in ficcGaugeData" :key="g.dim" class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl p-5 flex flex-col items-center">
              <div class="text-[11px] font-mono text-[#94A3B8] uppercase tracking-widest mb-3">{{ g.label }}</div>
              <div class="relative w-32 h-32 mb-3">
                <svg viewBox="0 0 120 120" class="w-full h-full -rotate-90">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#1A1E2B" stroke-width="10" />
                  <circle cx="60" cy="60" r="50" fill="none" :stroke="g.color" stroke-width="10"
                    stroke-linecap="round" :stroke-dasharray="`${Math.PI * 100}`" :stroke-dashoffset="`${Math.PI * 100 * (1 - g.value / 100)}`"
                    class="transition-all duration-700" />
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <span class="text-[24px] font-mono font-bold" :style="{ color: g.color }">{{ g.value }}</span>
                </div>
              </div>
              <div class="text-[13px] font-bold text-[#E8ECF4]">{{ g.tier }}</div>
              <div class="text-[11px] font-mono text-[#64748B] mt-1">
                {{ g.dim === 'position' ? '3档映射' : '5档映射' }}
              </div>
            </div>
          </div>
        </div>

        <!-- ── 主任委员决策面板 ── -->
        <div v-if="canViewFullS3Board" class="bg-[#202431] border border-[#3B9EFF]/20 rounded-xl overflow-hidden shadow-lg">
          <div class="bg-gradient-to-r from-[#3B9EFF]/10 to-[#202431] border-b border-[#3B9EFF]/15 px-5 py-3.5 flex items-center justify-between">
            <h3 class="am-title-l2"><div class="am-title-bar" style="background: #3B9EFF"></div>主任委员决策面板</h3>
            <div class="flex items-center space-x-2">
              <span v-if="ficcDecisionConfirmed" class="text-[11px] font-mono text-[#34C759] bg-[#34C759]/10 border border-[#34C759]/20 px-2 py-1 rounded">已下发</span>
              <span v-else-if="isChairman" class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-2 py-1 rounded">待决策</span>
              <span v-else class="text-[11px] font-mono text-[#94A3B8] bg-[#94A3B8]/10 border border-[#94A3B8]/20 px-2 py-1 rounded">只读</span>
            </div>
          </div>
          <div class="p-5 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div v-for="pk in FICC_PRODUCT_KEYS" :key="pk" class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl overflow-hidden">
                <div class="px-5 py-3 border-b border-[#252A3A] flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: FICC_PRODUCT_COLORS[pk] }"></div>
                    <span class="text-[13px] font-bold text-[#E8ECF4]">{{ FICC_PRODUCT_LABELS[pk] }}</span>
                  </div>
                  <span class="text-[11px] font-mono text-[#64748B]">默认 = 投票均值档位</span>
                </div>
                <div class="p-4 space-y-3">
                  <div v-for="dim in FICC_DIM_KEYS" :key="dim" class="flex items-start justify-between gap-3">
                    <span class="text-[11px] text-[#94A3B8] font-mono w-24 shrink-0 pt-1">{{ FICC_DIM_LABELS[dim] }}</span>
                    <div class="flex-1 min-w-0 text-right">
                      <template v-if="isChairman && !ficcDecisionConfirmed">
                        <select
                          v-model="ficcProductDecisions[pk][dim]"
                          class="bg-[#161922] border border-[#3B9EFF]/30 text-[13px] font-mono font-bold text-[#E8ECF4] outline-none rounded px-3 py-1.5 focus:border-[#3B9EFF] transition-all cursor-pointer"
                        >
                          <option value="" disabled>请选择</option>
                          <option v-for="t in FICC_DIM_TIERS[dim]" :key="t.label" :value="t.label">{{ t.label }}</option>
                        </select>
                      </template>
                      <template v-else>
                        <span class="text-[15px] font-mono font-bold" :style="{ color: FICC_DIM_COLORS[dim] }">{{ ficcProductDecisions[pk][dim] || '—' }}</span>
                      </template>
                      <div class="mt-1 text-[11px] font-mono text-[#64748B]">
                        {{ ficcDecisionHint(pk, dim, ficcProductDecisions[pk][dim]) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 子委员会专项投资建议 -->
            <div class="bg-[#1A1E2B] border border-[#3B9EFF]/20 rounded-xl overflow-hidden">
              <div class="px-5 py-3 border-b border-[#3B9EFF]/15 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-1 h-3.5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
                  <span class="text-[13px] font-bold text-[#E8ECF4]">子委员会专项投资建议</span>
                </div>
                <span class="text-[11px] font-mono text-[#64748B]">Mock 预填 · 主任可手动调整</span>
              </div>
              <div class="p-5 grid grid-cols-2 gap-4">
                <div class="bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-3 space-y-2">
                  <div class="text-[11px] font-mono text-[#94A3B8]">(1) 稳定资产结构建议</div>
                  <template v-if="isChairman && !ficcDecisionConfirmed">
                    <input v-model="ficcSpecialAdvice.stableStructure" class="w-full bg-transparent border border-[#2E3348] rounded px-3 py-2 text-[13px] text-[#E8ECF4] outline-none focus:border-[#3B9EFF]/40" />
                  </template>
                  <div v-else class="text-[13px] text-[#B4BAC9] leading-relaxed">{{ ficcSpecialAdvice.stableStructure }}</div>
                </div>
                <div class="bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-3 space-y-2">
                  <div class="text-[11px] font-mono text-[#94A3B8]">(2) 期限结构建议</div>
                  <template v-if="isChairman && !ficcDecisionConfirmed">
                    <select v-model="ficcSpecialAdvice.tenorStructure" class="w-full bg-[#161922] border border-[#2E3348] rounded px-3 py-2 text-[13px] text-[#E8ECF4] outline-none focus:border-[#3B9EFF]/40">
                      <option v-for="opt in FICC_TENOR_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
                    </select>
                  </template>
                  <div v-else class="text-[13px] text-[#B4BAC9] leading-relaxed">{{ ficcSpecialAdvice.tenorStructure }}</div>
                </div>
                <div class="bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-3 space-y-2">
                  <div class="text-[11px] font-mono text-[#94A3B8]">(3) 信用利差建议</div>
                  <template v-if="isChairman && !ficcDecisionConfirmed">
                    <div class="flex items-center gap-2">
                      <span class="text-[12px] text-[#64748B] shrink-0">倾向</span>
                      <select v-model="ficcSpecialAdvice.creditBias" class="bg-[#161922] border border-[#2E3348] rounded px-2.5 py-1.5 text-[12px] text-[#E8ECF4] outline-none focus:border-[#3B9EFF]/40">
                        <option v-for="opt in FICC_CREDIT_BIAS_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
                      </select>
                    </div>
                    <textarea v-model="ficcSpecialAdvice.creditOpportunities" rows="3" class="w-full bg-transparent border border-[#2E3348] rounded px-3 py-2 text-[12px] text-[#B4BAC9] outline-none focus:border-[#3B9EFF]/40 resize-none"></textarea>
                  </template>
                  <div v-else class="text-[13px] text-[#B4BAC9] leading-relaxed">倾向 {{ ficcSpecialAdvice.creditBias }}；{{ ficcSpecialAdvice.creditOpportunities }}</div>
                </div>
                <div class="bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-3 space-y-2">
                  <div class="text-[11px] font-mono text-[#94A3B8]">(4) 含权结构建议</div>
                  <template v-if="isChairman && !ficcDecisionConfirmed">
                    <div class="flex items-center gap-2">
                      <span class="text-[12px] text-[#64748B] shrink-0">倾向</span>
                      <select v-model="ficcSpecialAdvice.equityBias" class="bg-[#161922] border border-[#2E3348] rounded px-2.5 py-1.5 text-[12px] text-[#E8ECF4] outline-none focus:border-[#3B9EFF]/40">
                        <option v-for="opt in FICC_EQUITY_BIAS_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
                      </select>
                    </div>
                    <textarea v-model="ficcSpecialAdvice.equityNotes" rows="3" class="w-full bg-transparent border border-[#2E3348] rounded px-3 py-2 text-[12px] text-[#B4BAC9] outline-none focus:border-[#3B9EFF]/40 resize-none"></textarea>
                  </template>
                  <div v-else class="text-[13px] text-[#B4BAC9] leading-relaxed">倾向 {{ ficcSpecialAdvice.equityBias }}；{{ ficcSpecialAdvice.equityNotes }}</div>
                </div>
                <div class="bg-[#161922] border border-[#252A3A] rounded-lg px-4 py-3 space-y-2 col-span-2">
                  <div class="text-[11px] font-mono text-[#94A3B8]">(5) 另类资产</div>
                  <template v-if="isChairman && !ficcDecisionConfirmed">
                    <textarea v-model="ficcSpecialAdvice.alternativeAdvice" rows="2" class="w-full bg-transparent border border-[#2E3348] rounded px-3 py-2 text-[12px] text-[#B4BAC9] outline-none focus:border-[#3B9EFF]/40 resize-none"></textarea>
                  </template>
                  <div v-else class="text-[13px] text-[#B4BAC9] leading-relaxed">{{ ficcSpecialAdvice.alternativeAdvice }}</div>
                </div>
              </div>
            </div>

            <!-- 最终配置指引表 (Exposure Mapping) -->
            <div class="bg-[#1A1E2B] border border-[#3B9EFF]/20 rounded-xl overflow-hidden">
              <div class="px-5 py-3 border-b border-[#3B9EFF]/15 flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <div class="w-1 h-3.5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
                  <span class="text-[13px] font-bold text-[#E8ECF4]">最终配置指引表</span>
                  <span class="text-[11px] font-mono text-[#64748B] ml-1">Exposure Mapping · 由主任委员档位实时翻译</span>
                </div>
                <span v-if="ficcDecisionConfirmed" class="text-[11px] font-mono text-[#34C759] bg-[#34C759]/10 border border-[#34C759]/20 px-2 py-1 rounded">已锁定</span>
                <span v-else class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-2 py-1 rounded">草稿</span>
              </div>
              <table class="w-full border-collapse table-fixed">
                <thead>
                  <tr class="border-b border-[#252A3A] bg-[#161922]/60">
                    <th class="px-5 py-3 text-left text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest" style="width:145px">产品名称</th>
                    <th class="px-5 py-3 text-right text-[11px] font-bold text-[#3B9EFF] uppercase tracking-widest">稳定资产仓位</th>
                    <th class="px-5 py-3 text-right text-[11px] font-bold text-[#3B9EFF] uppercase tracking-widest">久期使用率</th>
                    <th class="px-5 py-3 text-right text-[11px] font-bold text-[#3B9EFF] uppercase tracking-widest">含权使用率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in ficcGuidanceTable" :key="row.product"
                    class="border-b border-[#252A3A]/50 hover:bg-[#161922]/30 transition-colors">
                    <td class="px-5 py-4">
                      <div class="flex items-center space-x-2">
                        <div class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ backgroundColor: row.color }"></div>
                        <span class="text-[14px] font-bold text-[#E8ECF4]">{{ row.product }}</span>
                      </div>
                      <div class="text-[11px] font-mono text-[#4A5568] mt-0.5 ml-[18px]">{{ row.positionTier }}</div>
                    </td>
                    <td class="px-5 py-4 text-right">
                      <span class="text-[18px] font-mono font-bold tabular-nums text-[#3B9EFF]">{{ row.position }}</span>
                      <span class="text-[11px] font-mono text-[#64748B]"> %</span>
                    </td>
                    <td class="px-5 py-4 text-right">
                      <span class="text-[16px] font-mono font-bold tabular-nums text-[#3B9EFF]">{{ row.durationRange }}</span>
                      <div class="text-[11px] font-mono text-[#4A5568] mt-0.5">{{ row.durationTier }}</div>
                    </td>
                    <td class="px-5 py-4 text-right">
                      <span class="text-[18px] font-mono font-bold tabular-nums text-[#3B9EFF]">{{ row.equityCap }}</span>
                      <div class="text-[11px] font-mono text-[#4A5568] mt-0.5">{{ row.equityTier }}</div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <!-- Exposure Mapping 翻译规则 -->
              <div class="px-5 py-3.5 border-t border-[#252A3A] bg-[#161922]/40 space-y-2">
                <div class="text-[11px] font-mono text-[#4A5568] uppercase tracking-wider">Exposure Mapping 翻译规则</div>
                <div class="grid grid-cols-2 gap-x-6 gap-y-1.5 text-[11px] font-mono">
                  <div class="flex items-center gap-1.5">
                    <span class="text-[#3B9EFF]">稳定资产仓位</span>
                    <span class="text-[#252A3A]">·</span>
                    <span class="text-[#64748B]">低波：低配/平配/高配 = <span class="text-[#94A3B8]">70% / 75% / 80%</span></span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-[#3B9EFF]">稳定资产仓位</span>
                    <span class="text-[#252A3A]">·</span>
                    <span class="text-[#64748B]">中低波：低配/平配/高配 = <span class="text-[#94A3B8]">20% / 25% / 30%</span></span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-[#3B9EFF]">久期使用率</span>
                    <span class="text-[#252A3A]">·</span>
                    <span class="text-[#64748B]">谨慎/中性偏谨/中性/中性偏乐/乐观 = <span class="text-[#94A3B8]">20%-35% / 35%-50% / 50%-70% / 70%-90% / 90%-110%</span></span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-[#3B9EFF]">含权使用率</span>
                    <span class="text-[#252A3A]">·</span>
                    <span class="text-[#64748B]">谨慎/中性偏谨/中性/中性偏乐/乐观 = <span class="text-[#94A3B8]">0-20% / 20-40% / 40-60% / 60-80% / 80-100%</span></span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 最终配置指引明细表：资金仓位拆解 -->
            <div class="bg-[#1A1E2B] border border-[#3B9EFF]/20 rounded-xl overflow-hidden">
              <div class="px-5 py-3 border-b border-[#3B9EFF]/15 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-1 h-3.5 bg-[#3B9EFF] rounded-sm shrink-0"></div>
                  <span class="text-[13px] font-bold text-[#E8ECF4]">最终配置指引明细表</span>
                  <span class="text-[11px] font-mono text-[#64748B]">中枢仓位 + 偏离微调</span>
                </div>
                <span class="text-[11px] font-mono text-[#64748B]">统一调节用于上层直接完成敞口调整，减少 SPV 摩擦</span>
              </div>
              <table class="w-full border-collapse">
                <thead>
                  <tr class="border-b border-[#252A3A] bg-[#161922]/60">
                    <th class="px-4 py-2.5 text-left text-[11px] font-bold text-[#94A3B8]">产品</th>
                    <th class="px-4 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] font-mono">流动性</th>
                    <th class="px-4 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] font-mono">稳定资产</th>
                    <th class="px-4 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] font-mono">统一调节</th>
                    <th class="px-4 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] font-mono">恒定久期信用</th>
                    <th class="px-4 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] font-mono">主动交易</th>
                    <th class="px-4 py-2.5 text-right text-[11px] font-bold text-[#94A3B8] font-mono">含权</th>
                    <th class="px-4 py-2.5 text-right text-[11px] font-bold text-[#3B9EFF] font-mono">久期中枢→建议</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in ficcAllocationDetailRows" :key="row.key" class="border-b border-[#252A3A]/50 hover:bg-[#161922]/25">
                    <td class="px-4 py-3">
                      <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full" :style="{ backgroundColor: row.color }"></div>
                        <span class="text-[13px] font-bold text-[#E8ECF4]">{{ row.product }}</span>
                      </div>
                    </td>
                    <td class="px-4 py-3 text-right text-[13px] font-mono tabular-nums text-[#B4BAC9]">{{ fmtPct(row.liquidity) }}</td>
                    <td class="px-4 py-3 text-right text-[13px] font-mono tabular-nums text-[#3B9EFF]">
                      {{ fmtPct(row.stableAsset) }}
                      <span class="text-[11px] text-[#4A5568] ml-1">({{ row.stableDelta >= 0 ? '+' : '' }}{{ row.stableDelta.toFixed(1) }}%)</span>
                    </td>
                    <td class="px-4 py-3 text-right text-[13px] font-mono tabular-nums text-[#3B9EFF]">
                      {{ fmtPct(row.unifiedAdjustment) }}
                      <span class="text-[11px] text-[#4A5568] ml-1">{{ row.key === 'midLowVol' ? `(${row.unifiedDelta >= 0 ? '+' : ''}${row.unifiedDelta.toFixed(1)}%)` : '(-)' }}</span>
                    </td>
                    <td class="px-4 py-3 text-right text-[13px] font-mono tabular-nums text-[#B4BAC9]">{{ fmtPct(row.constantDurationCredit) }}</td>
                    <td class="px-4 py-3 text-right text-[13px] font-mono tabular-nums text-[#B4BAC9]">{{ fmtPct(row.activeTrading) }}</td>
                    <td class="px-4 py-3 text-right text-[13px] font-mono tabular-nums text-[#3B9EFF]">{{ fmtPct(row.equityUsage) }}</td>
                    <td class="px-4 py-3 text-right text-[12px] font-mono tabular-nums text-[#3B9EFF]">
                      {{ row.durationBase.toFixed(2) }} → {{ row.durationTarget.toFixed(2) }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div class="px-5 py-3 border-t border-[#252A3A] bg-[#161922]/45 space-y-1.5">
                <div class="text-[11px] font-mono text-[#4A5568] uppercase tracking-wider">偏离限制校验</div>
                <div v-if="ficcDeviationWarnings.length === 0" class="text-[11px] font-mono text-[#34C759]">全部通过：组合久期 ±5%，稳定资产 ±5%，统一调节仓位 ±1% / 久期 ±10%</div>
                <div v-for="(warn, idx) in ficcDeviationWarnings" :key="idx" class="text-[11px] font-mono text-[#F97316]">{{ warn }}</div>
              </div>
            </div>

            <!-- 正式确认并下发 -->
            <div v-if="isChairman && !ficcDecisionConfirmed" class="pt-1">
              <button
                @click="confirmFiccDecision"
                class="w-full py-3.5 rounded-xl font-bold text-[15px] transition-all duration-200 bg-gradient-to-r from-[#3B9EFF] to-[#FF6B00] text-white shadow-[0_4px_24px_rgba(255,171,0,0.3)] hover:shadow-[0_4px_36px_rgba(255,171,0,0.45)] active:scale-[0.99] flex items-center justify-center gap-2"
              >
                <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
                正式确认并下发
              </button>
            </div>
            <div v-else-if="ficcDecisionConfirmed" class="pt-1 space-y-3">
              <!-- 归档状态横幅 -->
              <div class="flex items-center justify-between px-4 py-3 rounded-xl bg-[#34C759]/8 border border-[#34C759]/20">
                <div class="flex items-center gap-2">
                  <div class="w-1.5 h-4 bg-[#00C9A7] rounded-sm shrink-0"></div>
                  <span class="text-[13px] font-bold text-[#34C759]">决议已正式确认并下发</span>
                </div>
                <span class="text-[11px] font-mono text-[#64748B]">{{ ficcLatestDecision?.confirmedAt }}</span>
              </div>
              <!-- 决议卡片摘要 (归档只读) -->
              <div class="grid grid-cols-2 gap-2.5">
                <div v-for="row in ficcGuidanceTable" :key="row.product"
                  class="bg-[#1A1E2B] border border-[#252A3A] rounded-xl px-4 py-3.5 space-y-2.5">
                  <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full shrink-0" :style="{ backgroundColor: row.color }"></div>
                    <span class="text-[13px] font-bold text-[#E8ECF4]">{{ row.product }}</span>
                  </div>
                  <div class="space-y-1.5 text-[11px] font-mono">
                    <div class="flex items-center justify-between">
                      <span class="text-[#4A5568]">稳定资产仓位</span>
                      <span class="text-[#3B9EFF] font-bold tabular-nums">{{ row.position }} %</span>
                    </div>
                    <div class="flex items-center justify-between">
                      <span class="text-[#4A5568]">久期使用率</span>
                      <span class="text-[#3B9EFF] font-bold tabular-nums">{{ row.durationRange }}</span>
                    </div>
                    <div class="flex items-center justify-between">
                      <span class="text-[#4A5568]">含权使用率</span>
                      <span class="text-[#3B9EFF] font-bold tabular-nums">≤ {{ row.equityCap }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="text-[11px] font-mono text-[#4A5568] text-center pt-0.5">
                决议已广播至全系统 · 会议状态已更新为「已归档」· 流转至 S4 纪要签发
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- ═══ 会议纪要 (原 Step 4) ═══ -->
      <div v-if="activeTab === 'minutes'" class="space-y-4 pb-4">

        <!-- ── State: DRAFT ── -->
        <template v-if="minuteState === 'draft'">
          <div class="grid grid-cols-12 gap-4">
            <!-- LEFT: 生成 AI 纪要 -->
            <div class="col-span-7 space-y-4">
              <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden shadow-lg">
                <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
                  <h3 class="am-title-l2"><div class="am-title-bar"></div>AI 纪要生成</h3>
                  <span class="text-[11px] font-mono"
                    :class="recordState === 'finished' ? 'text-[#3B9EFF]' : 'text-[#64748B]'"
                  >
                    {{ recordState === 'finished' ? '录音已就绪' : '请先在 Header 完成录音' }}
                  </span>
                </div>
                <div class="p-5">
                  <button
                    @click="generateAISummary"
                    :disabled="recordState !== 'finished'"
                    :class="cn(
                      'w-full py-3 rounded-xl text-[14px] font-bold transition-all flex items-center justify-center gap-2',
                      recordState === 'finished'
                        ? 'bg-[#3B9EFF]/10 border border-[#3B9EFF]/30 text-[#3B9EFF] hover:bg-[#3B9EFF]/18'
                        : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed'
                    )"
                  >
                    <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
                    生成 AI 纪要
                  </button>
                </div>
              </div>
              <!-- AI Summary Points -->
              <Transition name="slide-up">
                <div v-if="aiPointsVisible > 0" class="bg-[#202431] border border-[#3B9EFF]/20 rounded-xl overflow-hidden">
                  <div class="bg-gradient-to-r from-[#3B9EFF]/10 to-[#202431] border-b border-[#3B9EFF]/15 px-5 py-3 flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                      <div class="w-1.5 h-1.5 rounded-full bg-[#3B9EFF] animate-pulse"></div>
                      <h3 class="am-title-l2"><div class="am-title-bar"></div>AI 提炼 · 领导指示要点</h3>
                    </div>
                    <button @click="applyAIToInstruction" class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/20 px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 shrink-0">
                      一键同步至纪要草稿 <div class="w-0.5 h-3 bg-current rounded-sm shrink-0"></div>
                    </button>
                  </div>
                  <div class="p-5 space-y-2.5">
                    <Transition v-for="(point, i) in FICC_AI_SUMMARY_POINTS" :key="i" name="slide-up">
                      <div v-if="i < aiPointsVisible" class="flex items-start space-x-3 bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3">
                        <span class="text-[11px] font-bold font-mono text-[#3B9EFF]/60 mt-0.5 shrink-0 w-4">{{ i + 1 }}.</span>
                        <p class="text-[13px] text-[#B4BAC9] leading-relaxed">{{ point }}</p>
                      </div>
                    </Transition>
                  </div>
                </div>
              </Transition>
            </div>

            <!-- RIGHT: 纪要预览 (Draft) -->
            <div class="col-span-5">
              <div class="bg-[#202431] border border-[#252A3A] rounded-xl overflow-hidden h-full">
                <div class="bg-gradient-to-r from-[#252A3A] to-[#202431] border-b border-[#252A3A] px-5 py-3.5 flex items-center justify-between">
                  <h3 class="am-title-l2"><div class="am-title-bar"></div>纪要草稿预览</h3>
                  <span class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/20 px-2 py-1 rounded">草稿</span>
                </div>
                <div class="p-5 space-y-3">
                  <div class="text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest">FICC 策略决策</div>
                  <div v-for="group in FICC_CONSENSUS_TABLE" :key="group.asset" class="flex items-center justify-between bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-3 py-2">
                    <div class="flex items-center space-x-2">
                      <div class="w-2 h-2 rounded-sm shrink-0" :style="{ backgroundColor: group.color }"></div>
                      <span class="text-xs text-[#E8ECF4]">{{ group.asset }}</span>
                    </div>
                    <span class="text-[11px] font-mono px-2 py-1 rounded border text-[#3B9EFF] border-[#3B9EFF]/25 bg-[#3B9EFF]/10">[待主任核定]</span>
                  </div>
                  <textarea v-model="chairmanInstruction" rows="6" class="w-full bg-[#1A1E2B] border border-[#2E3348] rounded-lg px-4 py-3 text-[13px] text-[#E8ECF4] placeholder-[#3A4555] outline-none focus:border-[#3B9EFF]/40 transition-all resize-none leading-relaxed font-mono" placeholder="AI 提炼要点将同步至此处，也可手动输入补充指示..."></textarea>
                  <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3 space-y-1.5">
                    <div class="text-[11px] font-mono text-[#64748B] uppercase tracking-wider">结构化总结（自动）</div>
                    <div v-for="(line, idx) in [...ficcDecisionPointSummary, ...ficcSpecialAdviceSummary]" :key="idx" class="text-[11px] font-mono text-[#94A3B8] leading-relaxed">{{ line }}</div>
                  </div>
                  <div class="flex justify-end">
                    <button @click="minuteState = 'pending'" :disabled="!chairmanInstruction.trim()" :class="cn('px-4 py-2 rounded-lg text-[13px] font-bold transition-all', chairmanInstruction.trim() ? 'bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 text-[#3B9EFF] hover:bg-[#3B9EFF]/25' : 'bg-[#1A1E2B] border border-[#252A3A] text-[#4A5568] cursor-not-allowed')">提交主任委员核定</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── State: PENDING ── -->
        <template v-else-if="minuteState === 'pending'">
          <div class="bg-[#202431] border border-[#3B9EFF]/20 rounded-xl overflow-hidden">
            <div class="bg-gradient-to-r from-[#3B9EFF]/10 to-[#202431] border-b border-[#3B9EFF]/15 px-6 py-5 text-center space-y-4">
              <div class="flex justify-center"><div class="w-2 h-12 bg-[#3B9EFF] rounded-sm mx-auto animate-pulse"></div></div>
              <div>
                <h3 class="text-base font-bold text-[#3B9EFF]">等待主任委员 OA 核定中...</h3>
                <p class="text-xs font-mono text-[#94A3B8] mt-1">FICC 纪要草稿已提交至主任委员 OA 审批队列 · 等待签章确认</p>
              </div>
              <div class="flex justify-center pt-2">
                <button @click="minuteState = 'ready'" class="text-[11px] font-mono text-[#3B9EFF] bg-[#3B9EFF]/10 border border-[#3B9EFF]/25 hover:bg-[#3B9EFF]/20 px-4 py-2 rounded-lg transition-all">[Mock] 模拟主任审批通过</button>
              </div>
            </div>
          </div>
        </template>

        <!-- ── State: READY ── -->
        <template v-else-if="minuteState === 'ready'">
          <div class="bg-[#202431] border border-[#34C759]/20 rounded-xl overflow-hidden">
            <div class="bg-gradient-to-r from-[#34C759]/10 to-[#202431] border-b border-[#34C759]/15 px-6 py-4 flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-1.5 h-8 bg-[#00C9A7] rounded-sm shrink-0"></div>
                <div>
                  <h3 class="text-[15px] font-bold text-[#34C759]">主任委员已核定</h3>
                  <p class="text-[11px] font-mono text-[#94A3B8] mt-0.5">FICC 纪要终稿已确认 · 可签发下达</p>
                </div>
              </div>
              <span class="text-[11px] font-mono text-[#34C759] bg-[#34C759]/10 border border-[#34C759]/20 px-2 py-1 rounded">审批通过</span>
            </div>
            <div class="p-6 space-y-3">
              <div class="text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest">确认 FICC 策略决策</div>
              <div v-for="group in FICC_CONSENSUS_TABLE" :key="group.asset" class="flex items-center justify-between bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-2.5">
                <div class="flex items-center space-x-2">
                  <div class="w-2 h-2 rounded-sm shrink-0" :style="{ backgroundColor: group.color }"></div>
                  <span class="text-[13px] text-[#E8ECF4] font-medium">{{ group.asset }}</span>
                </div>
                <span :class="cn('text-xs font-bold font-mono', consensusTextColor(group.rows[0].consensusType))">
                  {{ group.rows[0].consensus || '—' }}
                </span>
              </div>
              <div v-if="chairmanInstruction.trim()" class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3 text-[13px] text-[#B4BAC9] leading-relaxed">{{ chairmanInstruction }}</div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3 space-y-1.5">
                <div class="text-[11px] font-mono text-[#64748B] uppercase tracking-wider">结构化纪要摘要</div>
                <div v-for="(line, idx) in [...ficcDecisionPointSummary, ...ficcSpecialAdviceSummary]" :key="idx" class="text-[11px] font-mono text-[#94A3B8] leading-relaxed">{{ line }}</div>
              </div>
              <div class="pt-2">
                <button @click="handleIssue" :disabled="isIssued || issuingLoading" :class="cn('w-full py-4 rounded-xl font-bold text-[15px] tracking-widest transition-all duration-300 flex items-center justify-center space-x-3 border', isIssued ? 'bg-[#34C759]/10 border-[#34C759]/30 text-[#34C759] cursor-not-allowed' : issuingLoading ? 'bg-[#3B9EFF]/10 border-[#3B9EFF]/30 text-[#3B9EFF] cursor-wait' : 'bg-gradient-to-r from-[#3B9EFF] to-[#2563EB] border-transparent text-white shadow-[0_4px_30px_rgba(59,158,255,0.28)] hover:shadow-[0_4px_40px_rgba(59,158,255,0.45)] active:scale-[0.99]')">
                  <div v-if="!issuingLoading" class="w-1.5 h-5 bg-current rounded-sm shrink-0"></div>
                  <div v-else class="w-1.5 h-5 bg-current rounded-sm shrink-0 animate-pulse"></div>
                  <span>{{ isIssued ? 'FICC 决议已签发，会议纪要已生成并全系统同步' : issuingLoading ? '正在生成 FICC 会议纪要...' : '签发终稿并全系统下达' }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- PDF Preview -->
          <Transition name="slide-up">
            <div v-if="isIssued" class="bg-[#1A1E2B] border border-[#34C759]/20 rounded-xl overflow-hidden shadow-[0_0_40px_rgba(52,199,89,0.06)]">
              <div class="bg-gradient-to-r from-[#34C759]/10 to-[#1A1E2B] border-b border-[#34C759]/15 px-6 py-4 flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-1.5 h-5 bg-[#00C9A7] rounded-sm shrink-0"></div>
                  <div>
                    <div class="text-[15px] font-bold text-white">FICC 会议纪要 · 预览</div>
                    <div class="text-[11px] font-mono text-[#94A3B8] mt-0.5">FICC-2026-Q2-04.pdf · 2026.04.15 生成</div>
                  </div>
                </div>
                <div class="flex items-center space-x-2"><div class="w-2 h-2 rounded-full bg-[#34C759]"></div><span class="text-[11px] font-mono text-[#34C759]">已签发存档</span></div>
              </div>
              <div class="p-6 font-mono text-xs space-y-4 text-[#B4BAC9] leading-relaxed">
                <div class="text-center space-y-1 pb-4 border-b border-[#252A3A]">
                  <div class="text-base font-bold text-white tracking-wider">FICC 投资委员会 · 2026 年第二季度</div>
                  <div class="text-[15px] font-bold text-[#E8ECF4]">第 4 次会议纪要</div>
                  <div class="text-[11px] text-[#94A3B8] mt-1">FICC INVESTMENT COMMITTEE MINUTES · FICC-2026-Q2-04</div>
                </div>
                <div class="grid grid-cols-3 gap-x-4 gap-y-1.5 py-3 border-b border-[#252A3A] text-[11px]">
                  <div><span class="text-[#6B7280]">会议日期：</span><span class="text-[#E8ECF4]">2026.04.15</span></div>
                  <div><span class="text-[#6B7280]">地点：</span><span class="text-[#E8ECF4]">总部 3 楼 FICC 会议室</span></div>
                  <div><span class="text-[#6B7280]">决议编号：</span><span class="text-[#3B9EFF]">FICC-2026-Q2-04</span></div>
                </div>
                <div class="space-y-2">
                  <div class="text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest">FICC 策略决策聚合</div>
                  <table class="w-full text-[11px] border-collapse">
                    <thead>
                      <tr class="border-b border-[#252A3A]">
                        <th class="text-left py-1.5 text-[#6B7280] font-normal w-24">资产</th>
                        <th class="text-left py-1.5 text-[#6B7280] font-normal w-40">共识结论</th>
                        <th class="text-left py-1.5 text-[#6B7280] font-normal">点位预测</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="group in FICC_CONSENSUS_TABLE" :key="group.asset" class="border-b border-[#1A1E2B]">
                        <td class="py-1.5 text-[#E8ECF4]">{{ group.asset }}</td>
                        <td class="py-1.5" :class="consensusTextColor(group.rows[0].consensusType)">{{ group.rows[0].consensus || '—' }}</td>
                        <td class="py-1.5 text-[#3B9EFF]">{{ group.rows.find(r => r.forecast)?.forecast || '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-if="chairmanInstruction.trim()" class="space-y-1 pt-2 border-t border-[#252A3A]">
                  <div class="text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest">主任指示要点</div>
                  <div class="whitespace-pre-line text-[#B4BAC9] text-[11px]">{{ chairmanInstruction }}</div>
                </div>
                <div class="space-y-1 pt-2 border-t border-[#252A3A]">
                  <div class="text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest">结构化总结（三项决策点 + 五项专项建议）</div>
                  <div v-for="(line, idx) in [...ficcDecisionPointSummary, ...ficcSpecialAdviceSummary]" :key="idx" class="text-[11px] text-[#B4BAC9]">{{ line }}</div>
                </div>
                <div class="pt-3 border-t border-[#252A3A]">
                  <div class="text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest mb-1">签发信息</div>
                  <div class="grid grid-cols-2 gap-1 text-[11px]">
                    <div><span class="text-[#6B7280]">签发人：</span><span class="text-[#E8ECF4]">王XX（固收主任委员）</span></div>
                    <div><span class="text-[#6B7280]">签发时间：</span><span class="text-[#E8ECF4]">2026.04.15 {{ issuedTime }}</span></div>
                  </div>
                </div>
              </div>
              <div class="px-6 py-3.5 bg-[#161922] border-t border-[#252A3A]">
                <div class="flex items-center space-x-3">
                  <div class="w-2 h-2 rounded-full bg-[#34C759] shrink-0 animate-pulse"></div>
                  <span class="text-[11px] font-mono text-[#34C759]">已自动同步分发至固收部 / 货币市场部 / 跨境投资部 · 已存入 OA 系统</span>
                </div>
              </div>
            </div>
          </Transition>
        </template>

      </div>
      </div>
      <!-- end MAIN CONTENT -->
    </div>
    <!-- end SIDEBAR + CONTENT ROW -->

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
        v-if="isChairman && activeTab === 'decision' && !ficcDecisionConfirmed"
        class="fixed bottom-6 right-6 z-[8000]"
      >
        <button
          @click="confirmFiccDecision"
          class="px-8 py-4 rounded-2xl font-bold text-[16px] tracking-wide transition-all duration-200 flex items-center gap-3 bg-gradient-to-r from-[#3B9EFF] to-[#FF6B00] text-white shadow-[0_8px_32px_rgba(255,171,0,0.35)] hover:shadow-[0_12px_48px_rgba(255,171,0,0.5)] hover:scale-[1.02] active:scale-[0.98] backdrop-blur-xl"
        >
          <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
          </div>
          <span>确认本期最终决议并全系统下发</span>
        </button>
      </div>
      <div
        v-else-if="isChairman && activeTab === 'decision' && ficcDecisionConfirmed"
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
          :disabled="issuingLoading"
          :class="cn(
            'px-8 py-4 rounded-2xl font-bold text-[16px] tracking-wide transition-all duration-200 flex items-center gap-3',
            !issuingLoading
              ? 'bg-gradient-to-r from-[#3B9EFF] to-[#2563EB] text-white shadow-[0_8px_32px_rgba(59,158,255,0.35)] hover:shadow-[0_12px_48px_rgba(59,158,255,0.5)] hover:scale-[1.02] active:scale-[0.98] backdrop-blur-xl'
              : 'bg-[#252A3A]/80 text-[#6B7280] cursor-not-allowed backdrop-blur-xl'
          )"
        >
          <div v-if="issuingLoading" class="w-1.5 h-5 bg-current rounded-sm shrink-0 animate-pulse"></div>
          <div v-else class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <div class="w-1.5 h-4 bg-current rounded-sm shrink-0"></div>
          </div>
          <span>{{ issuingLoading ? '正在签发...' : '确认签发会议纪要并归档' }}</span>
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

    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 scale-[0.97]"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-[0.97]"
      >
        <div v-if="showSAASandbox" class="fixed inset-0 z-[9999] bg-[#161922]">
          <SAASimulator embedded @close="showSAASandbox = false" />
        </div>
      </Transition>
    </Teleport>

    </template>

    <!-- ═══ FICC 投票确认对话框 ═══ -->
    <Teleport to="body">
      <div v-if="showFiccVoteConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showFiccVoteConfirm = false">
        <div class="bg-[#202431] border border-[#2E3348] rounded-2xl w-full max-w-lg shadow-[0_8px_48px_rgba(0,0,0,0.6)]">
          <div class="bg-gradient-to-r from-[#3B9EFF]/10 to-[#202431] border-b border-[#252A3A] px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-[#3B9EFF]/15 border border-[#3B9EFF]/30 flex items-center justify-center">
                <div class="w-1.5 h-4 bg-[#3B9EFF] rounded-sm shrink-0"></div>
              </div>
              <div>
                <h3 class="text-[15px] font-bold text-white">确认提交观点与材料</h3>
                <p class="text-xs text-[#94A3B8] mt-0.5 font-mono">提交后数据将锁定</p>
              </div>
            </div>
            <button @click="showFiccVoteConfirm = false" class="w-7 h-7 rounded-lg border border-[#252A3A] flex items-center justify-center text-[#6B7280] hover:text-white hover:border-[#3B9EFF]/30 transition-colors">
              <div class="w-0.5 h-3.5 bg-current rounded-full shrink-0"></div>
            </button>
          </div>
          <div class="px-6 py-4 space-y-4 max-h-[50vh] overflow-y-auto no-scrollbar">
            <div>
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">核心观点摘要</div>
              <div class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-4 py-3 text-[13px] text-[#B4BAC9] leading-relaxed">{{ ficcSummaryDraft }}</div>
              <div class="text-right mt-1"><span class="text-[11px] font-mono text-[#4A5568]">{{ ficcSummaryDraft.length }} 字</span></div>
            </div>
            <div v-if="Object.keys(ficcSelfScores).length">
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">策略评分摘要</div>
              <div class="grid grid-cols-2 gap-2">
                <div v-for="(score, asset) in ficcSelfScores" :key="asset" class="bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-3 py-2 flex items-center justify-between">
                  <span class="text-xs text-[#B4BAC9] truncate">{{ asset }}</span>
                  <span :class="cn('text-xs font-bold font-mono', FICC_SCORE_COLORS[score] || 'text-[#94A3B8]')">{{ score }} · {{ FICC_SCORE_LABELS[score] || '-' }}</span>
                </div>
              </div>
            </div>
            <div v-if="ficcUploadedFiles.length">
              <div class="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">附件 ({{ ficcUploadedFiles.length }} 份)</div>
              <div class="space-y-1">
                <div v-for="(f, i) in ficcUploadedFiles" :key="i" class="flex items-center gap-2 bg-[#1A1E2B] border border-[#252A3A] rounded-lg px-3 py-2">
                  <div class="w-1 h-3 bg-[#64748B] rounded-sm shrink-0"></div>
                  <span class="text-xs text-[#B4BAC9] flex-1 truncate">{{ f.name }}</span>
                  <span class="text-[11px] font-mono text-[#64748B]">{{ f.size }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-[#252A3A] flex items-center gap-3">
            <button @click="showFiccVoteConfirm = false" class="flex-1 py-2.5 rounded-lg border border-[#252A3A] text-[#94A3B8] hover:border-[#2E3348] hover:text-white transition-colors text-[13px]">返回修改</button>
            <button @click="showFiccVoteConfirm = false; submitFiccSummary()" class="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-[#3B9EFF] to-[#3B9EFF] text-white font-bold text-[13px] shadow-[0_4px_16px_rgba(59,158,255,0.3)] hover:shadow-[0_4px_24px_rgba(59,158,255,0.45)] active:scale-[0.99] transition-all">确认提交</button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import SAASimulator from './SAASimulator.vue';
import { activeRole, isGlobalMock, toggleGlobalMock, FICC_ASSET_LIST, MIXED_ASSET_LIST, FICC_QUARTERLY_ASSET_LIST, calcTargetRange, FICC_COMMITTEE_MEMBERS, submitVote } from '@/store/demoStore';
import { useFiccAllocationEngine, type FiccProductDecision } from '@/useFiccAllocationEngine';

function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

const isFiccMember = computed(() => ['班子', '部门长', '投资经理', 'FICC投资委员会委员'].includes(activeRole.value));
const isSecretary = computed(() => activeRole.value === 'FICC投资委员会秘书' || activeRole.value === '投管');
const isChairman = computed(() => activeRole.value === 'FICC投资委员会主任委员');
const decisionSubmitted = computed(() => ficcDecisionConfirmed.value);
const canViewFullS3Board = computed(() => decisionSubmitted.value || isChairman.value || isSecretary.value);
const isMemberPrivateS3 = computed(
  () => isFiccMember.value && !isChairman.value && !isSecretary.value && !decisionSubmitted.value,
);

const ROLE_BADGE_CLASSES: Record<string, string> = {
  '班子': 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]',
  '部门长': 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]',
  '投资经理': 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]',
  'FICC投资委员会秘书': 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]',
  'FICC投资委员会委员': 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]',
  'FICC投资委员会主任委员': 'bg-[#3B9EFF]/15 border-[#3B9EFF]/30 text-[#3B9EFF]',
};

// ── Portal & Meeting ─────────────────────────────────────────────
const currentMeetingId = ref<number | null>(null);
interface FiccMeeting {
  id: number;
  name: string;
  date: string;
  time: string;
  location: string;
  status: string;
}
let ficcMeetingIdCounter = 100;
const ficcMeetingList = reactive<FiccMeeting[]>([
  { id: 1, name: 'FICC投委会 2025 Q4 配置决策会议', date: '2025.10.15', time: '14:00-16:00', location: '总部5楼FICC会议室', status: '已归档' },
  { id: 2, name: 'FICC投委会 2026 Q1 配置决策会议', date: '2026.01.20', time: '14:00-16:00', location: '总部5楼FICC会议室', status: '已结束' },
  { id: 3, name: 'FICC投委会 2026 Q2 配置决策会议', date: '2026.04.15', time: '14:00-16:00', location: '总部5楼FICC会议室', status: '进行中' },
]);
const currentMeeting = computed(() => currentMeetingId.value != null ? ficcMeetingList.find(m => m.id === currentMeetingId.value) : null);
const isViewingArchived = computed(() => currentMeeting.value?.status === '已归档' || currentMeeting.value?.status === '已结束');
const isReadOnly = computed(() => !isChairman.value || isViewingArchived.value);

function enterMeeting(id: number) {
  currentMeetingId.value = id;
  activeTab.value = 'materials';
}
function backToList() { currentMeetingId.value = null; }

/** 会议中心门户：仅秘书可删除「进行中」会议（本地列表；与混合投委会删除规则对齐） */
function deleteFiccMeeting(id: number) {
  if (!isSecretary.value) return;
  const target = ficcMeetingList.find(m => m.id === id);
  if (!target || target.status !== '进行中') return;
  if (!window.confirm('确定删除该「进行中」会议？此操作不可撤销。')) return;
  const idx = ficcMeetingList.findIndex(m => m.id === id);
  if (idx !== -1) ficcMeetingList.splice(idx, 1);
  if (currentMeetingId.value === id) currentMeetingId.value = null;
}

function quickCreateFiccMeeting() {
  const now = new Date();
  const m = now.getMonth() + 1;
  const year = now.getFullYear();
  let title: string;
  if (m === 12 || m <= 2) {
    title = `${m === 12 ? year : year - 1}年度配置决策会议`;
  } else if (m <= 5) {
    title = `${year} Q1 配置决策会议`;
  } else if (m <= 8) {
    title = `${year} Q2 配置决策会议`;
  } else {
    title = `${year} Q3 配置决策会议`;
  }
  const dateStr = now.toLocaleDateString('zh-CN').replace(/\//g, '.');
  ficcMeetingList.unshift({
    id: ficcMeetingIdCounter++,
    name: `FICC投委会 ${title}`,
    date: dateStr, time: '14:00-16:00', location: '总部5楼FICC会议室', status: '筹备中',
  });
}
function handleQuickCreateAndEnter() {
  quickCreateFiccMeeting();
  if (ficcMeetingList.length > 0) enterMeeting(ficcMeetingList[0].id);
}

// ── Stepper ─────────────────────────────────────────────────────
type FiccTab = 'materials' | 'anchors' | 'decision' | 'minutes';
const activeTab = ref<FiccTab>('materials');
const FICC_TAB_ITEMS: { key: FiccTab; icon: string; label: string; step: string }[] = [
  { key: 'materials', icon: '📚', label: '委员观点', step: 'S0' },
  { key: 'anchors', icon: '📊', label: '市场及产品表现回顾', step: 'S1' },
  { key: 'decision', icon: '⚖️', label: '配置指引', step: 'S2' },
  { key: 'minutes', icon: '📝', label: '会议纪要', step: 'S3' },
];

function markMaterialsCollected() {
  void 0;
}

/** S2：量化模型锚点（FICC 久期 / 宏观 / 风险权） */
const showModelAnchors = ref(true);
const showSAASandbox = ref(false);

function openFiccModelCenter() {
  const url = new URL('model-center', window.location.href);
  window.open(url.href, '_blank', 'noopener,noreferrer');
}

const FICC_MODEL_OUTPUTS = [
  {
    name: 'SAA 蒙特卡洛',
    badge: 'MC-SIM',
    color: '#3B9EFF',
    desc: '久期-收益有效前沿 · 多路径利率随机模拟，输出组合久期上沿',
    anchorLabel: '建议久期使用率',
    anchorValue: '85%',
    anchorHint: '有效前沿切点 等效 3.2Y',
    showSandbox: true,
    highlight: false,
  },
  {
    name: 'BL 模型',
    badge: 'BLACK-LIT',
    color: '#3B9EFF',
    desc: '在基准久期上叠加宏观观点，给出中枢偏移与置信带',
    anchorLabel: '久期中枢偏移（相对基准）',
    anchorValue: '+12 bp',
    anchorHint: '基准中枢 2.8Y · 委员观点已融合',
    showSandbox: false,
    highlight: true,
  },
  {
    name: '风险平价',
    badge: 'RP-IR-CR',
    color: '#3B9EFF',
    desc: '利率子账与信用子账的波动率目标下风险权重',
    anchorLabel: '利率 : 信用 风险权',
    anchorValue: '52% : 48%',
    anchorHint: '等风险贡献约束',
    showSandbox: false,
    highlight: false,
  },
];

// ── FICC Members (7 人) ─────────────────────────────────────────
const FICC_MEMBERS = [
  { id: 'f1', name: '王XX', role: '固收主任' },
  { id: 'f2', name: '张XX', role: '利率策略' },
  { id: 'f3', name: '李XX', role: '信用策略' },
  { id: 'f4', name: '王XX', role: '货币市场' },
  { id: 'f5', name: '赵XX', role: '跨境固收' },
  { id: 'f6', name: '刘XX', role: '量化固收' },
  { id: 'f7', name: '周XX', role: '固收研究' },
];

// ── Step 0: 材料提交进度 ────────────────────────────────────────
interface FiccMaterial { summary: string; submittedAt: string; }
const ficcMaterials = reactive<Record<string, FiccMaterial>>({
  'f1': { summary: '短端利率已基本触底，建议现金管理维持中性久期。信用利差处于历史低位，信用策略需严选资质，谨慎下沉。', submittedAt: '09:15' },
  'f2': { summary: '10Y国债收益率仍有下行空间，建议债券组合适度拉长久期至1-3Y。海外美债在高利率环境下维持谨慎，关注美联储政策转向信号。', submittedAt: '09:38' },
  'f3': { summary: '信用利差收窄趋势明显，但已接近历史低位，需警惕尾部风险。含权方向建议以转债为主，关注低价转债机会。', submittedAt: '10:02' },
  'f4': { summary: '货币市场流动性充裕，R007中枢预计维持1.7%-1.8%区间。稳定类维持平配，关注存单利率节奏。', submittedAt: '10:24' },
});
const ficcMaterialCount = computed(() => Object.keys(ficcMaterials).length);
const ficcSentReminders = reactive(new Set<string>());
function sendFiccReminder(id: string) { ficcSentReminders.add(id); }
function sendAllFiccReminders() { FICC_MEMBERS.forEach(m => { if (!ficcMaterials[m.id]) ficcSentReminders.add(m.id); }); }

const FICC_MEMBER_ATTACHMENTS: Record<string, { name: string; size: string; type: string }[]> = {
  'f1': [{ name: '2026Q2_利率走势展望.pdf', size: '2.4 MB', type: 'pdf' }],
  'f2': [{ name: '10Y国债预测模型.xlsx', size: '856 KB', type: 'excel' }, { name: '海外固收月报_202604.pdf', size: '1.8 MB', type: 'pdf' }],
  'f3': [{ name: '信用利差跟踪_202604.xlsx', size: '1.2 MB', type: 'excel' }],
  'f4': [{ name: '货币市场流动性分析.pdf', size: '3.1 MB', type: 'pdf' }],
};

const FICC_SELF_ID = computed(() => {
  const map: Record<string, string> = { '班子': 'f1', '部门长': 'f2', '投资经理': 'f3' };
  return map[activeRole.value] ?? 'f3';
});
const ficcSelfMaterial = computed(() => ficcMaterials[FICC_SELF_ID.value] ?? null);
const ficcSummaryDraft = ref('');

// ── FICC 资产 1-5 档投票（统一观点字典驱动） ───────────────────
/** 快速查找 FICC_ASSET_LIST 配置项，以 细分策略 为键 */
const FICC_VOTE_CONFIG_MAP = new Map(FICC_ASSET_LIST.map(i => [i.细分策略, i]));
const FICC_ASSET_NAMES = FICC_ASSET_LIST.map(i => i.细分策略);

/** 快速查找 FICC_QUARTERLY_ASSET_LIST */
const FICC_Q_VOTE_CONFIG_MAP = new Map(FICC_QUARTERLY_ASSET_LIST.map(i => [i.细分策略, i]));

// ─── 维度切换 ─────────────────────────────────────────────────────────────────
/** Tab 1 填报维度 */
const ficcVoteDimension = ref<'monthly' | 'quarterly'>('monthly');
/** Tab 3 看板维度 */
const ficcDecisionDimension = ref<'monthly' | 'quarterly'>('monthly');

const FICC_SCORE_LABELS: Record<number, string> = { 1: '谨慎', 2: '中性偏谨慎', 3: '中性', 4: '中性偏乐观', 5: '乐观' };
const FICC_SCORE_COLORS: Record<number, string> = {
  1: 'bg-[#00C9A7]/15 border-[#00C9A7]/40 text-[#00C9A7]',    // 谨慎 — 绿
  2: 'bg-[#3B9EFF]/8  border-[#3B9EFF]/25  text-[#3B9EFF]/70', // 中性偏谨慎 — 淡蓝过渡
  3: 'bg-[#3B9EFF]/15 border-[#3B9EFF]/40 text-[#3B9EFF]',    // 中性 — 蓝
  4: 'bg-[#F04864]/8  border-[#F04864]/25  text-[#F04864]/70', // 中性偏乐观 — 淡红过渡
  5: 'bg-[#F04864]/15 border-[#F04864]/40 text-[#F04864]',    // 乐观 — 红
};
const FICC_SCORE_INACTIVE = 'bg-[#202431] border-[#2E3348] text-[#6B7280] hover:text-[#94A3B8]';

/** 当前委员在 Tab 1 填报的 1-5 档评分 */
const ficcSelfScores = reactive<Record<string, number>>(Object.fromEntries(FICC_ASSET_LIST.map(i => [i.细分策略, 3])));
/** 创新高标记（Tab 1 卡片右上角） */
const ficcNewHighFlags = reactive<Record<string, boolean>>(Object.fromEntries(FICC_ASSET_LIST.map(i => [i.细分策略, false])));

// ─── 季度评分状态 ──────────────────────────────────────────────────────────────
/** 当前委员季度自填评分（实时联动 Tab 3 季度看板） */
const ficcSelfQScores = reactive<Record<string, number>>(
  Object.fromEntries(FICC_QUARTERLY_ASSET_LIST.map(i => [i.细分策略, 3])),
);
/** 季度创新高标记 */
const ficcQNewHighFlags = reactive<Record<string, boolean>>(
  Object.fromEntries(FICC_QUARTERLY_ASSET_LIST.map(i => [i.细分策略, false])),
);
/** 季度委员评分 Mock（key = 委员id, value = 各季度资产评分） */
const ficcQMemberScores = reactive<Record<string, Record<string, number>>>({
  f1: { '存单(季)': 3, '信用(季)': 3, '利率10Y(季)': 4, '利率30Y(季)': 4, '转债(季)': 3, '二级债基(季)': 3, '红利(季)': 4, '恒生科技(季)': 3, 'REITs(季)': 3, '黄金(季)': 4, '原油(季)': 2 },
  f2: { '存单(季)': 2, '信用(季)': 3, '利率10Y(季)': 5, '利率30Y(季)': 5, '转债(季)': 3, '二级债基(季)': 2, '红利(季)': 3, '恒生科技(季)': 4, 'REITs(季)': 3, '黄金(季)': 5, '原油(季)': 2 },
  f3: { '存单(季)': 3, '信用(季)': 4, '利率10Y(季)': 3, '利率30Y(季)': 3, '转债(季)': 4, '二级债基(季)': 4, '红利(季)': 4, '恒生科技(季)': 3, 'REITs(季)': 4, '黄金(季)': 3, '原油(季)': 3 },
  f4: { '存单(季)': 3, '信用(季)': 3, '利率10Y(季)': 3, '利率30Y(季)': 3, '转债(季)': 3, '二级债基(季)': 3, '红利(季)': 3, '恒生科技(季)': 3, 'REITs(季)': 3, '黄金(季)': 3, '原油(季)': 3 },
  f5: { '存单(季)': 2, '信用(季)': 2, '利率10Y(季)': 4, '利率30Y(季)': 5, '转债(季)': 3, '二级债基(季)': 3, '红利(季)': 4, '恒生科技(季)': 4, 'REITs(季)': 3, '黄金(季)': 4, '原油(季)': 2 },
  f6: { '存单(季)': 3, '信用(季)': 3, '利率10Y(季)': 4, '利率30Y(季)': 4, '转债(季)': 4, '二级债基(季)': 4, '红利(季)': 3, '恒生科技(季)': 4, 'REITs(季)': 3, '黄金(季)': 4, '原油(季)': 3 },
});
const ficcQScoreSubmitted = computed(() => !!ficcQMemberScores[FICC_SELF_ID.value + '_q']);
function submitFiccQScores() {
  ficcQMemberScores[FICC_SELF_ID.value + '_q'] = { ...ficcSelfQScores };
}

/** 季度资产按大类分组，驱动 Tab 1 季度填报和 Tab 3 季度表格 */
const FICC_QUARTERLY_ASSET_GROUPS = computed(() => {
  const orderMap = new Map<string, typeof FICC_QUARTERLY_ASSET_LIST[number][]>();
  const order: string[] = [];
  for (const item of FICC_QUARTERLY_ASSET_LIST) {
    if (!orderMap.has(item.大类)) { order.push(item.大类); orderMap.set(item.大类, []); }
    orderMap.get(item.大类)!.push(item);
  }
  return order.map(大类 => ({ 大类, items: orderMap.get(大类)! }));
});

/** 季度观点幅度文本 */
function getFiccQAmplitudeText(name: string, score: number): string {
  const cfg = FICC_Q_VOTE_CONFIG_MAP.get(name);
  if (!cfg) return '—';
  const label = FICC_SCORE_LABELS[score] as keyof typeof cfg.amplitude;
  return cfg.amplitude[label] ?? '—';
}
/** 季度预期点位区间文本 */
function getFiccQTargetRangeText(name: string, score: number): string {
  const cfg = FICC_Q_VOTE_CONFIG_MAP.get(name);
  if (!cfg) return '—';
  const amp = getFiccQAmplitudeText(name, score);
  const r = calcTargetRange(cfg.当前点位, amp);
  if (r.low === null && r.high !== null) return `≤ ${r.high}`;
  if (r.high === null && r.low !== null) return `≥ ${r.low}`;
  if (r.low !== null && r.high !== null) return `${r.low} — ${r.high}`;
  return '—';
}

/** 季度投票分布矩阵（含本人实时联动） */
const FICC_QUARTERLY_DIST_ROWS = computed(() => {
  const LABELS = ['谨慎', '中性偏谨慎', '中性', '中性偏乐观', '乐观'] as const;
  const selfQId = FICC_SELF_ID.value + '_q';
  const selfHasSubmitted = !!ficcQMemberScores[selfQId];

  const groupOrder: string[] = [];
  const groupMap = new Map<string, typeof FICC_QUARTERLY_ASSET_LIST[number][]>();
  for (const cfg of FICC_QUARTERLY_ASSET_LIST) {
    if (!groupMap.has(cfg.大类)) { groupOrder.push(cfg.大类); groupMap.set(cfg.大类, []); }
    groupMap.get(cfg.大类)!.push(cfg);
  }
  return groupOrder.flatMap(大类 => {
    const items = groupMap.get(大类)!;
    return items.map((cfg, i) => {
      const dist = [0, 0, 0, 0, 0];
      for (const m of FICC_MEMBERS) {
        const s = ficcQMemberScores[m.id]?.[cfg.细分策略];
        if (s >= 1 && s <= 5) dist[s - 1]++;
      }
      if (!selfHasSubmitted) {
        const s = ficcSelfQScores[cfg.细分策略];
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

/** 按大类分组，驱动 Tab 1 树状填报 */
const FICC_ASSET_GROUPS = computed(() => {
  const orderMap = new Map<string, typeof FICC_ASSET_LIST[number][]>();
  const order: string[] = [];
  for (const item of FICC_ASSET_LIST) {
    if (!orderMap.has(item.大类)) { order.push(item.大类); orderMap.set(item.大类, []); }
    orderMap.get(item.大类)!.push(item);
  }
  return order.map(大类 => ({ 大类, items: orderMap.get(大类)! }));
});

/** 按钮内短标签 */
const FICC_SCORE_LABELS_SHORT: Record<number, string> = { 1: '谨慎', 2: '偏谨慎', 3: '中性', 4: '偏乐观', 5: '乐观' };

/** 大类标题配色 */
const FICC_GROUP_HEADER_STYLE: Record<string, string> = {
  '固收': 'border-[#3B9EFF]/30 bg-[#3B9EFF]/8',
  '含权': 'border-[#3B9EFF]/30 bg-[#3B9EFF]/8',
  '另类': 'border-[#3B9EFF]/30 bg-[#3B9EFF]/8',
};
const FICC_GROUP_TEXT_COLOR: Record<string, string> = {
  '固收': 'text-[#3B9EFF]',
  '含权': 'text-[#3B9EFF]',
  '另类': 'text-[#3B9EFF]',
};
/** 已提交的委员评分 Mock（key=委员id, value=各资产评分map） */
const ficcMemberScores = reactive<Record<string, Record<string, number>>>({
  'f1': { '存单': 3, '信用': 3, '利率(10Y)': 4, '利率(30Y)': 4, '转债': 3, '二级债基': 3 },
  'f2': { '存单': 2, '信用': 3, '利率(10Y)': 5, '利率(30Y)': 5, '转债': 3, '二级债基': 2 },
  'f3': { '存单': 3, '信用': 4, '利率(10Y)': 3, '利率(30Y)': 3, '转债': 4, '二级债基': 4 },
  'f4': { '存单': 3, '信用': 3, '利率(10Y)': 3, '利率(30Y)': 3, '转债': 3, '二级债基': 3 },
  'f5': { '存单': 2, '信用': 2, '利率(10Y)': 4, '利率(30Y)': 5, '转债': 3, '二级债基': 3 },
  'f6': { '存单': 3, '信用': 3, '利率(10Y)': 4, '利率(30Y)': 4, '转债': 4, '二级债基': 4 },
});
const ficcScoreSubmitted = computed(() => !!ficcMemberScores[FICC_SELF_ID.value]);

function submitFiccScores() {
  ficcMemberScores[FICC_SELF_ID.value] = { ...ficcSelfScores };
}

// ── FICC 秘书 RPA 代填工作台 ─────────────────────────────────────────────────
const ficcSecretaryView = ref<'progress' | 'proxy'>('progress');
const ficcProxyTargetId = ref('');
const ficcProxyScores = reactive<Record<string, number>>({});
const ficcProxyNewHighFlags = reactive<Record<string, boolean>>({});
const ficcProxySubmitDone = ref(false);

const ficcProxyTargetMember = computed(() =>
  FICC_COMMITTEE_MEMBERS.find(m => m.id === ficcProxyTargetId.value) ?? null,
);

function resetFiccProxyForm() {
  ficcProxyTargetId.value = '';
  for (const k of Object.keys(ficcProxyScores)) delete ficcProxyScores[k];
  for (const k of Object.keys(ficcProxyNewHighFlags)) delete ficcProxyNewHighFlags[k];
  ficcProxySubmitDone.value = false;
}

async function submitFiccProxyScores() {
  if (!ficcProxyTargetId.value) return;
  try {
    const payload = { votes: { ...ficcProxyScores } };
    const sub = await submitVote(0, payload, ficcProxyTargetId.value);
    ficcMemberScores[ficcProxyTargetId.value] = { ...ficcProxyScores };
    console.info('[FICC] 代填完成:', ficcProxyTargetId.value, sub.isProxy);
    ficcProxySubmitDone.value = true;
    setTimeout(resetFiccProxyForm, 2500);
  } catch (err) {
    console.error('[FICC] 代填提交失败:', err);
    alert('代填提交失败，请检查后端服务是否正常运行');
  }
}

const FICC_SCORE_COL_AVG = computed(() => {
  const selfId = FICC_SELF_ID.value;
  const selfHasSubmitted = !!ficcMemberScores[selfId];
  const result: Record<string, number> = {};
  for (const name of FICC_ASSET_NAMES) {
    const vals = FICC_MEMBERS
      .filter(m => ficcMemberScores[m.id])
      .map(m => ficcMemberScores[m.id][name] ?? 3);
    if (!selfHasSubmitted) {
      vals.push(ficcSelfScores[name] ?? 3);
    }
    result[name] = vals.length ? Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10) / 10 : 3;
  }
  return result;
});

// ── 投票分布汇总矩阵（FICC 视角） ────────────────────────────────────────────

/** 5档底色高亮（谨慎→乐观，索引 0-4） */
const VOTE_DIST_HL_BG = ['bg-[#00C9A7]/15', 'bg-[#3B9EFF]/8', 'bg-[#3B9EFF]/12', 'bg-[#F04864]/8', 'bg-[#F04864]/14'] as const;
const VOTE_DIST_HL_TEXT = ['text-[#00C9A7]', 'text-[#3B9EFF]/70', 'text-[#3B9EFF]', 'text-[#F04864]/70', 'text-[#F04864]'] as const;
const VOTE_CONSENSUS_STYLE: Record<string, string> = {
  '谨慎':     'border-[#00C9A7]/40 bg-[#00C9A7]/10 text-[#00C9A7]',
  '中性偏谨慎': 'border-[#3B9EFF]/25 bg-[#3B9EFF]/6  text-[#3B9EFF]/70',
  '中性':     'border-[#3B9EFF]/40 bg-[#3B9EFF]/8  text-[#3B9EFF]',
  '中性偏乐观': 'border-[#F04864]/25 bg-[#F04864]/6  text-[#F04864]/70',
  '乐观':     'border-[#F04864]/40 bg-[#F04864]/10 text-[#F04864]',
};

const FICC_DIST_ROWS = computed(() => {
  const LABELS = ['谨慎', '中性偏谨慎', '中性', '中性偏乐观', '乐观'] as const;
  const selfId = FICC_SELF_ID.value;
  const selfHasSubmitted = !!ficcMemberScores[selfId];

  const groupOrder: string[] = [];
  const groupMap = new Map<string, typeof FICC_ASSET_LIST[number][]>();
  for (const cfg of FICC_ASSET_LIST) {
    if (!groupMap.has(cfg.大类)) { groupOrder.push(cfg.大类); groupMap.set(cfg.大类, []); }
    groupMap.get(cfg.大类)!.push(cfg);
  }

  return groupOrder.flatMap(大类 => {
    const items = groupMap.get(大类)!;
    return items.map((cfg, i) => {
      const dist = [0, 0, 0, 0, 0];
      for (const m of FICC_MEMBERS) {
        const s = ficcMemberScores[m.id]?.[cfg.细分策略];
        if (s >= 1 && s <= 5) dist[s - 1]++;
      }
      // 实时同步：本人尚未提交时，将当前 ficcSelfScores 计入分布
      if (!selfHasSubmitted) {
        const s = ficcSelfScores[cfg.细分策略];
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

// ═══════════════════════════════════════════════════════════════════════
// 跨委员会共识参考（FICC 视角）
// ═══════════════════════════════════════════════════════════════════════

const showFiccCrossPanel = ref(false);

/** 混合投委会对其6个资产的本期投票均值 Mock（供 FICC 投委会交叉印证） */
const CROSS_MIXED_MOCK: Record<string, number> = {
  '红利': 3.3, '偏股混': 2.8, '恒生科技': 3.4, '黄金': 3.7, '利率(10Y)': 3.7, '利率(30Y)': 3.8,
};

const MIXED_VOTE_CONFIG_MAP_CROSS = new Map(MIXED_ASSET_LIST.map(i => [i.细分策略, i]));
const FICC_SHARED_NAMES = new Set(['利率(10Y)', '利率(30Y)']);

function calcFiccRangeStr(cfg: { 当前点位: number; amplitude: Record<string, string> }, avg: number): string {
  const grade = Math.round(avg);
  const lm: Record<number, string> = { 1: '谨慎', 2: '中性偏谨慎', 3: '中性', 4: '中性偏乐观', 5: '乐观' };
  const amp = cfg.amplitude[lm[grade] as keyof typeof cfg.amplitude] ?? '—';
  const r = calcTargetRange(cfg.当前点位, amp);
  if (r.low === null && r.high !== null) return `≤${r.high}`;
  if (r.high === null && r.low !== null) return `≥${r.low}`;
  if (r.low !== null && r.high !== null) return `${r.low}~${r.high}`;
  return '—';
}

/** 获取 FICC 自身投票均值（用于跨委员会差异对比） */
function getCrossFiccDiff(assetName: string): number {
  return FICC_SCORE_COL_AVG.value[assetName] ?? 3;
}

/** Table B：全局合并统计（FICC均值 ⊕ 混合均值） */
const FICC_CROSS_GLOBAL_ITEMS = computed(() => {
  const scoreLabels: Record<number, string> = { 1: '谨慎', 2: '中性偏谨慎', 3: '中性', 4: '中性偏乐观', 5: '乐观' };
  const items: Array<{
    name: string; 大类: string; source: string;
    ownAvg: number | null; crossAvg: number | null; globalAvg: number;
    globalLabel: string; globalRange: string;
  }> = [];

  for (const cfg of FICC_ASSET_LIST) {
    const ownAvg = FICC_SCORE_COL_AVG.value[cfg.细分策略] ?? null;
    const crossAvg = CROSS_MIXED_MOCK[cfg.细分策略] ?? null;
    const globalAvg = ownAvg !== null && crossAvg !== null
      ? Math.round(((ownAvg + crossAvg) / 2) * 10) / 10
      : (ownAvg ?? crossAvg ?? 3);
    items.push({
      name: cfg.细分策略, 大类: cfg.大类,
      source: crossAvg !== null ? '⚡共享' : 'FICC',
      ownAvg: ownAvg !== null ? Math.round(ownAvg * 10) / 10 : null,
      crossAvg,
      globalAvg,
      globalLabel: scoreLabels[Math.round(globalAvg)] ?? '中性',
      globalRange: calcFiccRangeStr(cfg, globalAvg),
    });
  }

  for (const cfg of MIXED_ASSET_LIST) {
    if (FICC_SHARED_NAMES.has(cfg.细分策略)) continue;
    const crossAvg = CROSS_MIXED_MOCK[cfg.细分策略] ?? null;
    if (crossAvg === null) continue;
    items.push({
      name: cfg.细分策略, 大类: cfg.大类,
      source: '混合',
      ownAvg: null,
      crossAvg,
      globalAvg: crossAvg,
      globalLabel: scoreLabels[Math.round(crossAvg)] ?? '中性',
      globalRange: calcFiccRangeStr(cfg, crossAvg),
    });
  }
  return items;
});

// ════════════════════════════════════════════════════════════════════════

/** 获取 FICC 资产在指定评分档的观点幅度文本 */
function getFiccAmplitudeText(name: string, score: number): string {
  const cfg = FICC_VOTE_CONFIG_MAP.get(name);
  if (!cfg) return '—';
  const label = FICC_SCORE_LABELS[score] as keyof typeof cfg.amplitude;
  return cfg.amplitude[label] ?? '—';
}

/** 计算并格式化 FICC 预期点位区间字符串 */
function getFiccTargetRangeText(name: string, score: number): string {
  const cfg = FICC_VOTE_CONFIG_MAP.get(name);
  if (!cfg) return '—';
  const amp = getFiccAmplitudeText(name, score);
  const r = calcTargetRange(cfg.当前点位, amp);
  if (r.low === null && r.high !== null) return `≤ ${r.high}`;
  if (r.high === null && r.low !== null) return `≥ ${r.low}`;
  if (r.low !== null && r.high !== null) return `${r.low} — ${r.high}`;
  return '—';
}

/** 根据列均值四舍五入后档位计算 FICC 共识点位区间 */
function getFiccConsensusRangeText(name: string, avgScore: number): string {
  return getFiccTargetRangeText(name, Math.round(avgScore));
}

const FICC_SCORE_COL_EXTREMES = computed(() => {
  const result: Record<string, { max: number; min: number }> = {};
  for (const name of FICC_ASSET_NAMES) {
    const vals = FICC_MEMBERS
      .filter(m => ficcMemberScores[m.id])
      .map(m => ficcMemberScores[m.id][name] ?? 3);
    result[name] = { max: vals.length ? Math.max(...vals) : 3, min: vals.length ? Math.min(...vals) : 3 };
  }
  return result;
});
function submitFiccSummary() {
  if (!ficcSummaryDraft.value.trim()) return;
  ficcMaterials[FICC_SELF_ID.value] = {
    summary: ficcSummaryDraft.value,
    submittedAt: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  };
}

interface UploadedFile { name: string; size: string; type: string; }
const ficcUploadedFiles = reactive<UploadedFile[]>([]);
const FICC_MOCK_FILES: UploadedFile[] = [
  { name: '2026Q2_利率走势展望.pdf', size: '2.4 MB', type: 'pdf' },
  { name: '信用利差跟踪_202604.xlsx', size: '856 KB', type: 'excel' },
  { name: '境外债市月报_202604.pdf', size: '1.8 MB', type: 'pdf' },
];
function addMockFile() {
  const pool = FICC_MOCK_FILES.filter(f => !ficcUploadedFiles.some(u => u.name === f.name));
  if (pool.length) ficcUploadedFiles.push({ ...pool[Math.floor(Math.random() * pool.length)] });
}
function removeMockFile(idx: number) { ficcUploadedFiles.splice(idx, 1); }

const showFiccHistory = ref(false);
const showFiccVoteConfirm = ref(false);
const FICC_HISTORY_OPINIONS = [
  { meeting: 'FICC-2026-Q2-03', date: '2026-03-15', opinions: [
    { author: '王XX', role: '固收主任', content: '利率短端已触底，信用利差处于历史低位，需严选资质。' },
    { author: '张XX', role: '利率策略', content: '10Y国债有下行空间，建议组合久期拉至1-3Y。' },
  ]},
  { meeting: 'FICC-2026-Q2-02', date: '2026-03-01', opinions: [
    { author: '李XX', role: '信用策略', content: '信用尾部风险加大，含权方向以转债为主。' },
    { author: '王XX', role: '货币市场', content: 'R007中枢维持1.7%-1.8%，稳定类维持平配。' },
  ]},
  { meeting: 'FICC-2026-Q2-01', date: '2026-02-15', opinions: [
    { author: '赵XX', role: '跨境固收', content: '美债仍有上行压力，跨境固收维持低配。' },
    { author: '王XX', role: '固收主任', content: '现金管理中性久期，关注存单利率节奏。' },
  ]},
];

// ── 上期决议胜率复盘（Mock 数据：FICC 投委会 2026 Q1） ─────────────────────────

const FICC_PREV_PERIOD_REVIEW = [
  { asset: '存单',      prevView: '中性偏谨慎', prevPoint: 1.55,   currPoint: 1.4825, amplitudeType: 'bp'  as const },
  { asset: '信用',      prevView: '中性偏乐观', prevPoint: 1.88,   currPoint: 1.7814, amplitudeType: 'bp'  as const },
  { asset: '利率(10Y)', prevView: '中性偏乐观', prevPoint: 1.95,   currPoint: 1.79,   amplitudeType: 'bp'  as const },
  { asset: '利率(30Y)', prevView: '乐观',       prevPoint: 2.48,   currPoint: 2.281,  amplitudeType: 'bp'  as const },
  { asset: '转债',      prevView: '中性偏谨慎', prevPoint: 548.20, currPoint: 502.65, amplitudeType: 'pct' as const },
  { asset: '二级债基',  prevView: '乐观',       prevPoint: 4868,   currPoint: 5224.57, amplitudeType: 'pct' as const },
] as const;

type FiccPrevReviewItem = typeof FICC_PREV_PERIOD_REVIEW[number];

function calcFiccReviewRow(item: FiccPrevReviewItem) {
  const BULLISH = new Set<string>(['乐观', '中性偏乐观']);
  const BEARISH = new Set<string>(['谨慎', '中性偏谨慎']);
  const { prevView, prevPoint, currPoint, amplitudeType } = item;

  const changeVal = amplitudeType === 'bp'
    ? parseFloat(((currPoint - prevPoint) * 100).toFixed(2))
    : parseFloat(((currPoint - prevPoint) / prevPoint * 100).toFixed(2));
  const changeStr = amplitudeType === 'bp'
    ? `${changeVal > 0 ? '+' : ''}${changeVal}bp`
    : `${changeVal > 0 ? '+' : ''}${changeVal}%`;

  let verdict: 'correct' | 'wrong' | 'neutral_ok' | 'neutral_fail';
  if (BULLISH.has(prevView)) {
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

const FICC_PREV_REVIEW_ROWS = computed(() => FICC_PREV_PERIOD_REVIEW.map(calcFiccReviewRow));

const FICC_PREV_REVIEW_SUMMARY = computed(() => {
  const rows = FICC_PREV_REVIEW_ROWS.value;
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

// ── Step 1: FICC 归因数据 ───────────────────────────────────────
const FICC_ATTRIBUTION_DATA = [
  { name: '纯债 1 号', timing: 8.5, selection: 12.3 },
  { name: '固收+增强', timing: -2.1, selection: 9.8 },
  { name: '短债精选', timing: 5.4, selection: 6.7 },
  { name: '可转债策略', timing: 14.2, selection: -1.8 },
  { name: '货币增强', timing: 3.6, selection: 4.5 },
];
const FICC_TOP_STRATEGIES = [
  { name: '利率债骑乘策略', type: '纯债', return: '+3.8%', sharpe: '3.12' },
  { name: '信用挖掘增强', type: '信用债', return: '+3.2%', sharpe: '2.74' },
  { name: '转债双低策略', type: '可转债', return: '+2.9%', sharpe: '1.98' },
  { name: '货币增强', type: '货币市场', return: '+2.1%', sharpe: '4.52' },
  { name: '固收+稳健', type: '固收+', return: '+1.8%', sharpe: '2.33' },
];
const FICC_BOTTOM_STRATEGIES = [
  { name: '高收益信用', issue: '信用利差走阔 · 持仓集中', return: '-1.8%', maxdd: '-4.2%' },
  { name: '长久期利率', issue: '久期择时失误 · 方向反转', return: '-1.2%', maxdd: '-3.6%' },
  { name: '跨境高收益', issue: '汇率损耗 · 流动性不足', return: '-0.9%', maxdd: '-5.1%' },
];

// ── Step 3: FICC 投票表单 (6模块) ──────────────────────────────
const ficcForm = reactive({
  q1Duration: '', q1Leverage: '', q1R007: null as number | null, q1CD1Y: null as number | null,
  q2Position: '', q2Deposit1Y: null as number | null,
  q3Trend: '', q3Term: '', q3CreditSpread: '', q3Quant: '', q3Bond10Y: null as number | null, q3BondA3Y: null as number | null,
  q4Trend: '', q4Structure: [] as string[], q4CB: null as number | null,
  q5Position: '',
  q6Trend: '', q6Term: '', q6CreditSpread: '', q6USD2Y: null as number | null, q6USD10Y: null as number | null, q6USDCNY: null as number | null,
  comment: '',
});
function toggleFiccQ4Structure(opt: string) {
  const idx = ficcForm.q4Structure.indexOf(opt);
  if (idx >= 0) ficcForm.q4Structure.splice(idx, 1); else ficcForm.q4Structure.push(opt);
}

const FICC_DIM_KEYS = ['position', 'duration', 'equity'] as const;
const FICC_DIM_LABELS: Record<string, string> = { position: '稳定资产仓位', duration: '久期使用率', equity: '含权使用率' };
const FICC_DIM_COLORS: Record<string, string> = { position: '#3B9EFF', duration: '#3B9EFF', equity: '#3B9EFF' };

type DimForm = typeof ficcForm;
function calculateDimensionScores(f: DimForm): { position: number; duration: number; equity: number } {
  const ternary = (val: string, hi: string, mid: string, lo: string) => val === hi ? 100 : val === mid ? 50 : val === lo ? 0 : 50;
  const positionItems: number[] = [];
  const durationItems: number[] = [];
  const equityItems: number[] = [];
  positionItems.push(ternary(f.q2Position, '超配', '平配', '低配'));
  positionItems.push(ternary(f.q3Quant, '超配', '平配', '低配'));
  positionItems.push(ternary(f.q5Position, '超配', '平配', '低配'));
  durationItems.push(ternary(f.q1Duration, '乐观', '中性', '谨慎'));
  durationItems.push(ternary(f.q3Term, '3-5Y', '1-3Y', '1Y内'));
  durationItems.push(ternary(f.q6Term, '10Y', '5Y', '2Y'));
  equityItems.push(ternary(f.q4Trend, '上涨', '震荡', '下跌'));
  equityItems.push(f.q4Structure.includes('转债') ? 80 : f.q4Structure.length > 0 ? 40 : 50);
  equityItems.push(ternary(f.q3CreditSpread, '收窄', '稳定', '走阔'));
  const avg = (arr: number[]) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 50;
  return { position: avg(positionItems), duration: avg(durationItems), equity: avg(equityItems) };
}

interface FiccBallotData extends ReturnType<typeof calculateDimensionScores> { submittedAt: string; }
const ficcBallots = reactive<Record<string, FiccBallotData>>({
  'f1': { position: 72, duration: 78, equity: 18, submittedAt: '14:22' },
  'f2': { position: 67, duration: 82, equity: 25, submittedAt: '14:35' },
  'f3': { position: 55, duration: 60, equity: 35, submittedAt: '14:48' },
  'f4': { position: 50, duration: 48, equity: 12, submittedAt: '15:01' },
  'f5': { position: 45, duration: 55, equity: 40, submittedAt: '15:12' },
  'f6': { position: 80, duration: 90, equity: 22, submittedAt: '15:25' },
});
const ficcVoteCount = computed(() => Object.keys(ficcBallots).length);
const ficcSelfVoteSubmitted = computed(() => ficcBallots[FICC_SELF_BALLOT_ID.value] ?? null);

function submitFiccVote() {
  const scores = calculateDimensionScores(ficcForm);
  ficcBallots[FICC_SELF_BALLOT_ID.value] = {
    ...scores,
    submittedAt: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  };
}

const ficcVoteMeans = computed(() => {
  const ids = Object.keys(ficcBallots);
  if (!ids.length) return { position: 0, duration: 0, equity: 0 };
  const sum = { position: 0, duration: 0, equity: 0 };
  ids.forEach(id => { sum.position += ficcBallots[id].position; sum.duration += ficcBallots[id].duration; sum.equity += ficcBallots[id].equity; });
  return { position: Math.round(sum.position / ids.length), duration: Math.round(sum.duration / ids.length), equity: Math.round(sum.equity / ids.length) };
});

function ficcVoteExtremes(key: string): { min: number; max: number } {
  const vals = Object.values(ficcBallots).map(v => v[key as keyof FiccBallotData] as number);
  return vals.length ? { min: Math.min(...vals), max: Math.max(...vals) } : { min: 0, max: 0 };
}
function ficcVoteCellStyle(key: string, val: number): string {
  const { min, max } = ficcVoteExtremes(key);
  if (val === max && max !== min) return 'text-[#34C759] font-bold';
  if (val === min && max !== min) return 'text-[#FF3B30] font-bold';
  return 'text-[#B4BAC9]';
}

const FICC_SELF_BALLOT_ID = computed(() => {
  const map: Record<string, string> = { '班子': 'f1', '部门长': 'f2', '投资经理': 'f7' };
  return map[activeRole.value] ?? 'f7';
});

const ficcDraftScores = computed(() => calculateDimensionScores(ficcForm));

const FICC_PRODUCT_KEYS = ['lowVol', 'midLowVol'] as const;
const FICC_PRODUCT_LABELS: Record<'lowVol' | 'midLowVol', string> = { lowVol: '固收低波', midLowVol: '固收中低波' };
const FICC_PRODUCT_COLORS: Record<'lowVol' | 'midLowVol', string> = { lowVol: '#3B9EFF', midLowVol: '#3B9EFF' };
const ficcProductDecisions = reactive<Record<'lowVol' | 'midLowVol', FiccProductDecision>>({
  lowVol: { position: '', duration: '', equity: '' },
  midLowVol: { position: '', duration: '', equity: '' },
});
const ficcDecisionConfirmed = ref(false);

const FICC_TENOR_OPTIONS = ['短久期', '中短久期', '中长久期'] as const;
const FICC_CREDIT_BIAS_OPTIONS = ['信用', '利率'] as const;
const FICC_EQUITY_BIAS_OPTIONS = ['转债', '二级债基'] as const;

const ficcSpecialAdvice = reactive({
  stableStructure: 'QD > 结存 > 摊余基金 > 存款',
  tenorStructure: '中短久期',
  creditBias: '信用',
  creditOpportunities: '城投产业债与高等级二永债具备票息优势，区域上关注长三角与粤港澳核心产业链融资主体。',
  equityBias: '转债',
  equityNotes: '优先低价转债与高YTM品种，二级债基保持防御性底仓。',
  alternativeAdvice: '可择机配置黄金套利与 REITs 现金流资产，作为波动对冲与流动性补位。',
});

const {
  FICC_POSITION_TIERS,
  FICC_DURATION_TIERS,
  FICC_EQUITY_TIERS,
  FICC_DIM_TIERS,
  ficcTierForScore,
  ficcDecisionHint,
  selfVoteSuggestion,
  ficcGuidanceTable,
  ficcAllocationDetailRows,
  ficcDeviationWarnings,
  fmtPct,
} = useFiccAllocationEngine({
  ficcProductDecisions,
  ficcSelfVoteSubmitted,
  ficcDraftScores,
  FICC_PRODUCT_LABELS,
  FICC_PRODUCT_COLORS,
});

watch(ficcVoteMeans, (means) => {
  if (!ficcDecisionConfirmed.value) {
    const posTier = ficcTierForScore('position', means.position);
    const durTier = ficcTierForScore('duration', means.duration);
    const eqTier = ficcTierForScore('equity', means.equity);
    ficcProductDecisions.lowVol = { position: posTier, duration: durTier, equity: eqTier };
    ficcProductDecisions.midLowVol = { position: posTier, duration: durTier, equity: eqTier };
  }
}, { immediate: true });

const ficcGaugeData = computed(() => FICC_DIM_KEYS.map(dim => {
  const val = ficcVoteMeans[dim];
  return { dim, label: FICC_DIM_LABELS[dim], color: FICC_DIM_COLORS[dim], value: val, tier: ficcTierForScore(dim, val) };
}));

function confirmFiccDecision() {
  ficcDecisionConfirmed.value = true;
  const meeting = currentMeeting.value;
  if (meeting) meeting.status = '已归档';
  ficcLatestDecision.value = {
    meetingCode: meeting?.name || 'FICC-2026-Q2-04',
    confirmedAt: new Date().toLocaleString('zh-CN'),
    products: ficcGuidanceTable.value.map(r => ({
      name: r.product,
      position: `${r.position}% (${r.positionTier})`,
      durationRange: r.durationRange,
      equityCap: r.equityCap,
    })),
  };
}

// ── Step 3: 共识聚合表 (S4 引用) ──────────────────────────────
interface ConsensusRow { dim: string; consensus?: string; consensusType?: 'bull' | 'bear' | 'neutral'; forecast?: string; }
interface ConsensusGroup { asset: string; color: string; rows: ConsensusRow[]; }

const FICC_CONSENSUS_TABLE: ConsensusGroup[] = [
  {
    asset: '现金', color: '#94A3B8',
    rows: [
      { dim: '久期 / 杠杆', consensus: '中性 (5票)', consensusType: 'neutral' },
      { dim: 'R007 月均预测', forecast: '均值: 1.72%' },
      { dim: '1Y 存单月末', forecast: '均值: 1.85%' },
    ],
  },
  {
    asset: '稳定', color: '#3B9EFF',
    rows: [
      { dim: '配置仓位', consensus: '平配 (4票)', consensusType: 'neutral' },
      { dim: '1Y 定存平均', forecast: '均值: 1.30%' },
    ],
  },
  {
    asset: '债券', color: '#3B9EFF',
    rows: [
      { dim: '走势 (收益率口径)', consensus: '看下 (4票)', consensusType: 'bull' },
      { dim: '期限', consensus: '1-3Y (4票)', consensusType: 'neutral' },
      { dim: '信用利差', consensus: '稳定 (5票)', consensusType: 'neutral' },
      { dim: '量化配置仓位', consensus: '超配 (5票)', consensusType: 'bull' },
      { dim: '10Y 国债月末', forecast: '均值: 2.15%' },
      { dim: '3Y A++ 月末', forecast: '均值: 2.38%' },
    ],
  },
  {
    asset: '含权', color: '#3B9EFF',
    rows: [
      { dim: '走势', consensus: '震荡 (4票)', consensusType: 'neutral' },
      { dim: '结构偏好', consensus: '转债 (5票)', consensusType: 'neutral' },
      { dim: '转债等权月度预测', forecast: '均值: +1.2%' },
    ],
  },
  {
    asset: '创新', color: '#F97316',
    rows: [
      { dim: '配置仓位', consensus: '平配 (5票)', consensusType: 'neutral' },
      { dim: '中证 REITs 月度预测', forecast: '均值: +0.8%' },
    ],
  },
  {
    asset: '跨境固收', color: '#3B9EFF',
    rows: [
      { dim: '美债走势 (收益率口径)', consensus: '看上 (4票)', consensusType: 'bear' },
      { dim: '期限偏好', consensus: '10Y (4票)', consensusType: 'neutral' },
      { dim: '信用利差', consensus: '稳定 (4票)', consensusType: 'neutral' },
      { dim: '2Y 美债月末', forecast: '均值: 4.52%' },
      { dim: '10Y 美债月末', forecast: '均值: 4.38%' },
      { dim: '人民币汇率月末', forecast: '均值: 7.280' },
    ],
  },
];

const expandedConsensus = reactive(new Set<string>(['债券', '现金']));
function toggleConsensusGroup(asset: string) {
  expandedConsensus.has(asset) ? expandedConsensus.delete(asset) : expandedConsensus.add(asset);
}

function consensusColor(type?: string) {
  if (type === 'bull') return 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]';
  if (type === 'bear') return 'bg-[#FF3B30]/10 border-[#FF3B30]/25 text-[#FF3B30]';
  return 'bg-[#3B9EFF]/10 border-[#3B9EFF]/25 text-[#3B9EFF]';
}
function consensusTextColor(type?: string) {
  if (type === 'bull') return 'text-[#3B9EFF]';
  if (type === 'bear') return 'text-[#FF3B30]';
  return 'text-[#3B9EFF]';
}

// ── Step 4: 录音 & 签发 ─────────────────────────────────────────
type MinuteState = 'draft' | 'pending' | 'ready';
const minuteState = ref<MinuteState>('draft');

const WAVE_COUNT = 30;
const waveformBars = ref<number[]>(Array.from({ length: WAVE_COUNT }, () => Math.random() * 32 + 6));
type RecordState = 'idle' | 'recording' | 'paused' | 'finished';
const recordState = ref<RecordState>('idle');
const isRecording = computed(() => recordState.value === 'recording');
const recordingStopped = computed(() => recordState.value === 'finished');
const recordingSeconds = ref(0);
const recordingInterval = ref<ReturnType<typeof setInterval> | null>(null);
const recordingTimeDisplay = computed(() => {
  const m = Math.floor(recordingSeconds.value / 60).toString().padStart(2, '0');
  const s = (recordingSeconds.value % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
});

function startRecording() {
  recordState.value = 'recording';
  recordingSeconds.value = 0;
  aiPointsVisible.value = 0;
  if (recordingInterval.value) clearInterval(recordingInterval.value);
  recordingInterval.value = setInterval(() => {
    recordingSeconds.value++;
    waveformBars.value = Array.from({ length: WAVE_COUNT }, () => Math.random() * 36 + 6);
  }, 1000);
}
function pauseRecording() {
  recordState.value = 'paused';
  if (recordingInterval.value) { clearInterval(recordingInterval.value); recordingInterval.value = null; }
}
function resumeRecording() {
  recordState.value = 'recording';
  recordingInterval.value = setInterval(() => {
    recordingSeconds.value++;
    waveformBars.value = Array.from({ length: WAVE_COUNT }, () => Math.random() * 36 + 6);
  }, 1000);
}

function stopRecording() {
  recordState.value = 'finished';
  if (recordingInterval.value) { clearInterval(recordingInterval.value); recordingInterval.value = null; }
  waveformBars.value = Array.from({ length: WAVE_COUNT }, () => Math.random() * 20 + 8);
}

const aiPointsVisible = ref(0);
const ficcDecisionPointSummary = computed(() => [
  `决策点1-稳定资产仓位：低波 ${ficcProductDecisions.lowVol.position || '待定'}（${ficcGuidanceTable.value.find(r => r.key === 'lowVol')?.position ?? '-'}%），中低波 ${ficcProductDecisions.midLowVol.position || '待定'}（${ficcGuidanceTable.value.find(r => r.key === 'midLowVol')?.position ?? '-'}%）`,
  `决策点2-久期使用率：低波 ${ficcProductDecisions.lowVol.duration || '待定'}（${ficcGuidanceTable.value.find(r => r.key === 'lowVol')?.durationRange ?? '—'}），中低波 ${ficcProductDecisions.midLowVol.duration || '待定'}（${ficcGuidanceTable.value.find(r => r.key === 'midLowVol')?.durationRange ?? '—'}）`,
  `决策点3-含权使用率：低波 ${ficcProductDecisions.lowVol.equity || '待定'}（${ficcGuidanceTable.value.find(r => r.key === 'lowVol')?.equityCap ?? '—'}），中低波 ${ficcProductDecisions.midLowVol.equity || '待定'}（${ficcGuidanceTable.value.find(r => r.key === 'midLowVol')?.equityCap ?? '—'}）`,
]);

const ficcSpecialAdviceSummary = computed(() => [
  `专项建议1-稳定资产结构：${ficcSpecialAdvice.stableStructure || '待补充'}`,
  `专项建议2-期限结构：${ficcSpecialAdvice.tenorStructure || '待补充'}`,
  `专项建议3-信用利差：倾向${ficcSpecialAdvice.creditBias || '待定'}；${ficcSpecialAdvice.creditOpportunities || '待补充'}`,
  `专项建议4-含权结构：倾向${ficcSpecialAdvice.equityBias || '待定'}；${ficcSpecialAdvice.equityNotes || '待补充'}`,
  `专项建议5-另类资产：${ficcSpecialAdvice.alternativeAdvice || '待补充'}`,
]);

const FICC_AI_SUMMARY_POINTS = computed(() => [
  '【三项决策点分档】',
  ...ficcDecisionPointSummary.value,
  '【子委员会专项投资建议】',
  ...ficcSpecialAdviceSummary.value,
]);

function generateAISummary() {
  if (recordState.value !== 'finished') return;
  aiPointsVisible.value = 0;
  let idx = 0;
  const iv = setInterval(() => {
    if (idx < FICC_AI_SUMMARY_POINTS.value.length) { aiPointsVisible.value = idx + 1; idx++; }
    else clearInterval(iv);
  }, 600);
}

const chairmanInstruction = ref('');
const isIssued = ref(false);
const issuingLoading = ref(false);
const issuedTime = ref('');

function applyAIToInstruction() {
  const points = FICC_AI_SUMMARY_POINTS.value.slice(0, aiPointsVisible.value);
  if (points.length === 0) return;
  const suffix = points.map((p, i) => `${i + 1}. ${p}`).join('\n');
  chairmanInstruction.value = chairmanInstruction.value
    ? chairmanInstruction.value + '\n\n' + suffix
    : suffix;
}

function handleIssue() {
  if (isIssued.value || issuingLoading.value) return;
  issuingLoading.value = true;
  setTimeout(() => {
    issuingLoading.value = false;
    isIssued.value = true;
    issuedTime.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  }, 2000);
}

onMounted(() => {
  const activeMeeting = ficcMeetingList.find(m => m.status === '进行中');
  if (activeMeeting) currentMeetingId.value = activeMeeting.id;
});
onUnmounted(() => { if (recordingInterval.value) clearInterval(recordingInterval.value); });
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
