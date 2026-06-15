import type { Manager } from '@esm/types/domain';

export const mockManagers: Manager[] = [
  { name: '华衡基金', orgType: '公募', coreStrategy: '信用债高等级增强', aum: '2,860亿', cooperation: '核心合作', rating: 'A', peopleStability: '高', riskControl: '强', performance: '稳健领先', capacity: '180亿', lastDueDiligence: '2026-05-10', hasRiskEvent: '否' },
  { name: '曜石量化', orgType: '私募', coreStrategy: '中性策略 / 指数增强', aum: '420亿', cooperation: '观察池', rating: 'B', peopleStability: '中', riskControl: '较强', performance: '近一年修复', capacity: '80亿', lastDueDiligence: '2026-04-22', hasRiskEvent: '否' },
  { name: '国都资管', orgType: '券商资管', coreStrategy: '转债增强', aum: '1,120亿', cooperation: '核心合作', rating: 'A', peopleStability: '高', riskControl: '强', performance: '长期稳定', capacity: '90亿', lastDueDiligence: '2026-05-02', hasRiskEvent: '否' },
  { name: '鼎泽资产', orgType: '私募', coreStrategy: 'CTA', aum: '160亿', cooperation: '战术使用', rating: 'C', peopleStability: '中', riskControl: '中', performance: '波动偏高', capacity: '35亿', lastDueDiligence: '2026-03-18', hasRiskEvent: '否' },
  { name: 'EverBridge Capital', orgType: '海外机构', coreStrategy: '海外固收', aum: '780亿', cooperation: '暂停新增', rating: 'C', peopleStability: '低', riskControl: '较强', performance: '阶段承压', capacity: '70亿', lastDueDiligence: '2026-02-28', hasRiskEvent: '是' },
  { name: '泰安保险资管', orgType: '保险资管', coreStrategy: 'REITs', aum: '1,950亿', cooperation: '观察池', rating: 'B', peopleStability: '高', riskControl: '强', performance: '稳健', capacity: '45亿', lastDueDiligence: '2026-04-12', hasRiskEvent: '否' },
  { name: '澜峰投资', orgType: '私募', coreStrategy: '可转债波动率套利', aum: '90亿', cooperation: '淘汰', rating: 'D', peopleStability: '低', riskControl: '弱', performance: '低于基准', capacity: '25亿', lastDueDiligence: '2026-01-08', hasRiskEvent: '是' },
];

