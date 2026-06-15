import type { CommitteeItem } from '@esm/types/domain';

export const mockCommitteeItems: CommitteeItem[] = [
  { title: '转债增强稳健一号策略准入', department: '固收投资部', submitter: '李婧', riskLevel: '中', recommendation: '建议通过，初始额度 20 亿', status: '待上会', meetingDate: '2026-05-30', voteResult: '未投票' },
  { title: '曜石量化管理人准入', department: '外部策略团队', submitter: '周凯', riskLevel: '中高', recommendation: '建议纳入观察池', status: '材料复核', meetingDate: '2026-06-06', voteResult: '未投票' },
  { title: '华衡基金额度上调', department: '现金部', submitter: '陈默', riskLevel: '低', recommendation: '从 120 亿上调至 160 亿', status: '已通过', meetingDate: '2026-05-18', voteResult: '7 票同意 / 0 票反对' },
  { title: 'EverBridge 风险复核', department: '交易投管部', submitter: '王晨', riskLevel: '高', recommendation: '暂停新增并压降 20%', status: '待上会', meetingDate: '2026-05-30', voteResult: '未投票' },
  { title: '澜峰投资退出决策', department: '外部策略团队', submitter: '林若', riskLevel: '高', recommendation: '建议退出并封存评级', status: '已通过', meetingDate: '2026-05-12', voteResult: '6 票同意 / 1 票弃权' },
];

