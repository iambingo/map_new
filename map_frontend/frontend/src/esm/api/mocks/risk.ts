import type { RiskEvent } from '@esm/types/domain';

export const mockRiskEvents: RiskEvent[] = [
  { target: 'EverBridge 海外固收', strategyClass: '海外策略', level: '高', reason: '业绩连续 3 个月低于基准，美元信用利差扩大', exitStatus: '暂停新增', triggerDate: '2026-05-24' },
  { target: '澜峰投资', strategyClass: '固收增强含权', level: '高', reason: '核心投研负责人离职，估值偏离异常', exitStatus: '退出', triggerDate: '2026-05-11' },
  { target: '鼎泽 CTA', strategyClass: '另类策略', level: '中', reason: '震荡市回撤接近阈值 80%', exitStatus: '观察', triggerDate: '2026-05-20' },
  { target: '曜石量化', strategyClass: '量化策略', level: '中', reason: '风格因子暴露偏离策略说明书', exitStatus: '观察', triggerDate: '2026-05-16' },
  { target: '转债增强稳健一号', strategyClass: '固收增强含权', level: '低', reason: '单周波动升高，未触及止损', exitStatus: '正常', triggerDate: '2026-05-22' },
];

