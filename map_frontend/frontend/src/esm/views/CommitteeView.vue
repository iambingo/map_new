<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">投委会管理 Investment Committee</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">集中处理策略准入、管理人准入、额度审批、风险复核与退出决策。</p>
  </div>
  <TerminalSection title="投委审批队列">
    <template #actions>
      <span class="status-tag blue">IC Review</span>
    </template>
    <div class="toolbar">
      <div class="filters">
        <select v-model="store.statusFilter" class="select">
          <option v-for="option in committeeStatusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </div>
      <span class="status-tag blue">当前显示 {{ store.filteredCommitteeItems.length }} 项</span>
    </div>
    <div class="table-wrap">
      <table class="fin-table esm-table dense-fin-table committee-fin-table">
        <thead>
          <tr>
            <th>事项名称</th>
            <th>提交部门</th>
            <th>提交人</th>
            <th>风险评级</th>
            <th>推荐结论</th>
            <th>审批状态</th>
            <th>会议日期</th>
            <th>投票结果</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.filteredCommitteeItems" :key="item.title">
            <td><strong>{{ item.title }}</strong></td>
            <td>{{ item.department }}</td>
            <td>{{ item.submitter }}</td>
            <td><StatusTag :value="item.riskLevel" /></td>
            <td>{{ item.recommendation }}</td>
            <td><StatusTag :value="item.status" /></td>
            <td class="num-cell">{{ item.meetingDate }}</td>
            <td>{{ item.voteResult }}</td>
            <td>
              <button class="text-btn" type="button" @click="store.showDetailItem(item)">详情</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </TerminalSection>

  <CommitteeDetailModal
    :item="store.activeCommittee"
    :details="store.committeeDetails()"
    @close="store.closeDetail()"
  />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import TerminalSection from '@esm/components/TerminalSection.vue';
import StatusTag from '@esm/components/StatusTag.vue';
import CommitteeDetailModal from '@esm/components/CommitteeDetailModal.vue';
import { useCommitteeStore } from '@esm/store/committeeStore';

const route = useRoute();
const store = useCommitteeStore();

const committeeStatusOptions = [
  { label: '全部', value: '全部' },
  { label: '待处理', value: 'pending' },
  { label: '待上会', value: '待上会' },
  { label: '材料复核', value: '材料复核' },
  { label: '已通过', value: '已通过' },
];

onMounted(() => {
  store.load();
  if (route.query.status) store.statusFilter = route.query.status as string;
});
</script>

