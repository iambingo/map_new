import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { CommitteeItem } from '@esm/types/domain';
import { fetchCommitteeItems } from '@esm/api/committee';

export const useCommitteeStore = defineStore('committee', () => {
  const committeeItems = ref<CommitteeItem[]>([]);
  const activeCommittee = ref<CommitteeItem | null>(null);
  const statusFilter = ref('全部');

  const filteredCommitteeItems = computed(() =>
    committeeItems.value.filter(item => {
      if (statusFilter.value === '全部') return true;
      if (statusFilter.value === 'pending') return item.status !== '已通过';
      return item.status === statusFilter.value;
    }),
  );

  const committeeDetails = (() => {
    if (!activeCommittee.value) return [];
    const item = activeCommittee.value;
    const index = committeeItems.value.indexOf(item);
    return [
      { label: '提交部门', value: item.department },
      { label: '提交人', value: item.submitter },
      { label: '风险评级', value: item.riskLevel, isStatus: true },
      { label: '推荐结论', value: item.recommendation },
      { label: '审批状态', value: item.status, isStatus: true },
      { label: '会议日期', value: item.meetingDate },
      { label: '投票结果', value: item.voteResult },
      { label: '拟配置额度', value: index === 0 ? '初始 20 亿，观察期 6 个月' : '按投委会决议执行' },
    ];
  });

  function showDetail(index: number) {
    activeCommittee.value = committeeItems.value[index];
  }

  function showDetailItem(item: CommitteeItem) {
    activeCommittee.value = item;
  }

  function closeDetail() {
    activeCommittee.value = null;
  }

  async function load() {
    committeeItems.value = await fetchCommitteeItems();
  }

  return { committeeItems, filteredCommitteeItems, statusFilter, activeCommittee, committeeDetails, showDetail, showDetailItem, closeDetail, load };
});

