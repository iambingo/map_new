import type { Strategy, RatingRule } from '@esm/types/domain';
import type { AdmissionCheck, AdmissionStage, StrategyKPI, PerformancePoint, AttributionItem, AuditLog } from '@esm/types/domain';

// 四层准入检查项模板
const admissionTemplate: AdmissionStage[] = [
  {
    stage: '白名单准入',
    status: '已通过',
    checks: [
      { name: '牌照合规', status: '已通过', date: '2026-05-10', operator: '李婧' },
      { name: '历史业绩', status: '已通过', date: '2026-05-10', operator: '李婧' },
      { name: '合规审查', status: '已通过', date: '2026-05-11', operator: '张伟' },
      { name: '托管安排', status: '已通过', date: '2026-05-11', operator: '李婧' },
      { name: '法律文件', status: '已通过', date: '2026-05-12', operator: '张伟' },
    ],
  },
  {
    stage: '策略准入',
    status: '已通过',
    checks: [
      { name: '收益来源穿透', status: '已通过', date: '2026-05-13', operator: '李婧' },
      { name: '波动率评估', status: '已通过', date: '2026-05-13', operator: '李婧' },
      { name: '最大回撤分析', status: '已通过', date: '2026-05-14', operator: '王磊' },
      { name: '流动性评估', status: '已通过', date: '2026-05-14', operator: '李婧' },
      { name: '杠杆限制', status: '已通过', date: '2026-05-15', operator: '王磊' },
      { name: '估值透明度', status: '已通过', date: '2026-05-15', operator: '李婧' },
      { name: '穿透性验证', status: '已通过', date: '2026-05-16', operator: '王磊' },
    ],
  },
  {
    stage: '产品准入',
    status: '已通过',
    checks: [
      { name: '历史业绩验证', status: '已通过', date: '2026-05-17', operator: '李婧' },
      { name: '组合结构分析', status: '已通过', date: '2026-05-17', operator: '王磊' },
      { name: '集中度检查', status: '已通过', date: '2026-05-18', operator: '李婧' },
      { name: '风险暴露评估', status: '已通过', date: '2026-05-18', operator: '王磊' },
      { name: '运作稳定性', status: '已通过', date: '2026-05-19', operator: '李婧' },
    ],
  },
  {
    stage: '额度准入',
    status: '已通过',
    checks: [
      { name: '初始额度设定', status: '已通过', date: '2026-05-20', result: '20亿' },
      { name: '单一管理人上限', status: '已通过', date: '2026-05-20', result: '50亿' },
      { name: '单一策略上限', status: '已通过', date: '2026-05-20', result: '30%' },
      { name: '止损线设定', status: '已通过', date: '2026-05-21', result: '-8%' },
      { name: '观察名单触发条件', status: '已通过', date: '2026-05-21' },
    ],
  },
];

function passedAdmission(): AdmissionStage[] {
  return JSON.parse(JSON.stringify(admissionTemplate));
}

function partialAdmission(completedStages: number): AdmissionStage[] {
  const stages = JSON.parse(JSON.stringify(admissionTemplate)) as AdmissionStage[];
  for (let i = 0; i < stages.length; i++) {
    if (i < completedStages) {
      stages[i].status = '已通过';
      stages[i].checks.forEach(c => { c.status = '已通过'; });
    } else if (i === completedStages) {
      stages[i].status = '进行中';
      const halfDone = Math.floor(stages[i].checks.length / 2);
      stages[i].checks.forEach((c, j) => {
        if (j < halfDone) { c.status = '已通过'; c.date = '2026-05-20'; c.operator = '李婧'; }
        else { c.status = '未开始'; }
      });
    } else {
      stages[i].status = '未开始';
      stages[i].checks.forEach(c => { c.status = '未开始'; });
    }
  }
  return stages;
}

function emptyAdmission(): AdmissionStage[] {
  return admissionTemplate.map(s => ({
    stage: s.stage,
    status: '未开始' as const,
    checks: s.checks.map(c => ({ name: c.name, status: '未开始' as const })),
  }));
}

function rejectedAdmission(): AdmissionStage[] {
  const stages = JSON.parse(JSON.stringify(admissionTemplate)) as AdmissionStage[];
  stages[0].status = '已通过';
  stages[0].checks.forEach(c => { c.status = '已通过'; });
  stages[1].status = '驳回';
  stages[1].checks[0].status = '已通过';
  stages[1].checks[1].status = '已通过';
  stages[1].checks[2] = { name: '最大回撤分析', status: '驳回', result: '回撤超限，需补充压力测试报告', date: '2026-05-20', operator: '王磊' };
  stages[1].checks.slice(3).forEach(c => { c.status = '未开始'; });
  stages[2].status = '未开始';
  stages[2].checks.forEach(c => { c.status = '未开始'; });
  stages[3].status = '未开始';
  stages[3].checks.forEach(c => { c.status = '未开始'; });
  return stages;
}

const kpiQ2: StrategyKPI = { period: '2026Q2', scores: [86, 82, 88, 79, 84], totalScore: 83.8, grade: 'B', evaluator: '王磊' };
const kpiQ1: StrategyKPI = { period: '2026Q1', scores: [84, 80, 85, 77, 82], totalScore: 81.6, grade: 'B', evaluator: '王磊' };
const kpiAQ2: StrategyKPI = { period: '2026Q2', scores: [92, 88, 90, 85, 87], totalScore: 89.0, grade: 'A', evaluator: '王磊' };
const kpiCQ2: StrategyKPI = { period: '2026Q2', scores: [68, 72, 65, 70, 66], totalScore: 68.6, grade: 'C', evaluator: '王磊' };

function generatePerformance(months: number, annualReturn: number, vol: number): PerformancePoint[] {
  const points: PerformancePoint[] = [];
  let nav = 1.0, bm = 1.0;
  const startDate = new Date('2025-07-01');
  for (let i = 0; i < months; i++) {
    const d = new Date(startDate);
    d.setMonth(d.getMonth() + i);
    const date = d.toISOString().slice(0, 7);
    const r = annualReturn / 12 + (Math.random() - 0.5) * vol / Math.sqrt(12);
    const b = annualReturn * 0.4 / 12 + (Math.random() - 0.5) * vol * 0.5 / Math.sqrt(12);
    nav *= (1 + r);
    bm *= (1 + b);
    points.push({ date, nav: Math.round(nav * 10000) / 10000, benchmark: Math.round(bm * 10000) / 10000 });
  }
  return points;
}

const defaultAttribution: AttributionItem[] = [
  { factor: '市场Beta', contribution: 0.45 },
  { factor: '因子Alpha', contribution: 0.25 },
  { factor: '择时贡献', contribution: 0.12 },
  { factor: '行业配置', contribution: 0.10 },
  { factor: '残差', contribution: 0.08 },
];

function generateAuditLog(strategyName: string): AuditLog[] {
  return [
    { timestamp: '2026-06-01 14:30', operator: '王磊', action: 'KPI评分', detail: `${strategyName} 2026Q2 评分完成，等级 B` },
    { timestamp: '2026-05-21 10:15', operator: '李婧', action: '额度变更', detail: `${strategyName} 额度从 10亿 调整为 20亿` },
    { timestamp: '2026-05-20 09:00', operator: '张伟', action: '状态变更', detail: `${strategyName} 状态从「待投委审批」变更为「已准入」` },
    { timestamp: '2026-05-15 16:45', operator: '王磊', action: '准入操作', detail: `${strategyName} 额度准入检查通过` },
    { timestamp: '2026-05-12 11:30', operator: '李婧', action: '准入操作', detail: `${strategyName} 白名单准入检查通过` },
    { timestamp: '2026-03-15 09:00', operator: '张伟', action: '创建策略', detail: `${strategyName} 创建并初始化` },
  ];
}

export const mockStrategies: Strategy[] = [
  {
    id: 'STR-001',
    name: '转债增强稳健一号',
    primaryClass: '固收增强含权',
    secondaryClass: '转债增强',
    source: '票息+转债弹性+择券',
    risk: '权益回撤敏感',
    volatility: '6.8%',
    drawdown: '4.2%',
    liquidity: 'T+5',
    capacity: '80亿',
    productFit: '固收+、混合估值',
    createdAt: '2026-03-15',
    status: '已准入',
    rating: 'B',
    managerName: '华衡基金',
    admission: passedAdmission(),
    quota: { used: 15, limit: 20, unit: '亿' },
    kpiHistory: [kpiQ2, kpiQ1],
    committeeIds: ['CMT-001'],
    performanceData: generatePerformance(11, 0.08, 0.068),
    attribution: defaultAttribution,
    auditLog: generateAuditLog('转债增强稳健一号'),
  },
  {
    id: 'STR-002',
    name: '中性阿尔法精选',
    primaryClass: '量化策略',
    secondaryClass: '中性策略',
    source: '股票多空 alpha',
    risk: '模型拥挤与基差',
    volatility: '5.1%',
    drawdown: '3.6%',
    liquidity: 'T+10',
    capacity: '50亿',
    productFit: '绝对收益、MOM',
    createdAt: '2026-04-20',
    status: '观察池',
    rating: 'B',
    managerName: '曜石投资',
    admission: passedAdmission(),
    quota: { used: 5, limit: 10, unit: '亿' },
    kpiHistory: [kpiQ2],
    committeeIds: [],
    performanceData: generatePerformance(7, 0.06, 0.051),
    attribution: defaultAttribution,
    auditLog: generateAuditLog('中性阿尔法精选'),
  },
  {
    id: 'STR-003',
    name: 'CTA 趋势复合',
    primaryClass: '另类策略',
    secondaryClass: 'CTA',
    source: '商品/股指/债券趋势',
    risk: '震荡市磨损',
    volatility: '8.9%',
    drawdown: '6.8%',
    liquidity: 'T+7',
    capacity: '35亿',
    productFit: 'FOF、另类配置',
    createdAt: '2026-05-10',
    status: '准入评估中',
    admission: partialAdmission(1),
    quota: { used: 0, limit: 0, unit: '亿' },
    kpiHistory: [],
    committeeIds: [],
    performanceData: [],
    attribution: [],
    auditLog: generateAuditLog('CTA 趋势复合'),
  },
  {
    id: 'STR-004',
    name: 'REITs 收益增强',
    primaryClass: '另类策略',
    secondaryClass: 'REITs',
    source: '分红+折溢价修复',
    risk: '利率与流动性',
    volatility: '7.4%',
    drawdown: '5.9%',
    liquidity: 'T+3',
    capacity: '45亿',
    productFit: '固收增强、现金替代',
    createdAt: '2026-02-10',
    status: '已准入',
    rating: 'A',
    managerName: '泰安资产',
    admission: passedAdmission(),
    quota: { used: 25, limit: 35, unit: '亿' },
    kpiHistory: [kpiAQ2],
    committeeIds: ['CMT-004'],
    performanceData: generatePerformance(16, 0.12, 0.074),
    attribution: defaultAttribution,
    auditLog: generateAuditLog('REITs 收益增强'),
  },
  {
    id: 'STR-005',
    name: '海外固收对冲',
    primaryClass: '海外策略',
    secondaryClass: '海外固收',
    source: '美元债 carry+汇率对冲',
    risk: '汇率与信用迁移',
    volatility: '4.7%',
    drawdown: '2.8%',
    liquidity: 'T+8',
    capacity: '70亿',
    productFit: '跨境理财、QDII',
    createdAt: '2026-01-15',
    status: '暂停',
    rating: 'C',
    managerName: 'EverBridge Capital',
    admission: passedAdmission(),
    quota: { used: 12, limit: 10, unit: '亿' },
    kpiHistory: [kpiCQ2, { period: '2026Q1', scores: [72, 75, 70, 68, 71], totalScore: 71.4, grade: 'C', evaluator: '王磊' }],
    committeeIds: [],
    performanceData: generatePerformance(17, 0.03, 0.047),
    attribution: defaultAttribution,
    auditLog: [
      { timestamp: '2026-05-24 15:00', operator: '王磊', action: '风险处置', detail: '海外固收对冲暂停新增投资，触发业绩低于基准' },
      { timestamp: '2026-06-01 14:30', operator: '王磊', action: 'KPI评分', detail: '海外固收对冲 2026Q2 评分完成，等级 C' },
      ...generateAuditLog('海外固收对冲').slice(2),
    ],
  },
  {
    id: 'STR-006',
    name: '指数增强 500',
    primaryClass: '权益策略',
    secondaryClass: '指数增强',
    source: '因子 alpha+打新',
    risk: '风格暴露',
    volatility: '12.2%',
    drawdown: '9.5%',
    liquidity: 'T+5',
    capacity: '60亿',
    productFit: '权益 FOF、专户',
    createdAt: '2026-05-20',
    status: '待投委审批',
    admission: passedAdmission(),
    quota: { used: 0, limit: 0, unit: '亿' },
    kpiHistory: [],
    committeeIds: ['CMT-005'],
    performanceData: [],
    attribution: [],
    auditLog: generateAuditLog('指数增强 500'),
  },
  {
    id: 'STR-007',
    name: '信用债高等级增强',
    primaryClass: '固收增强',
    secondaryClass: '量化增强',
    source: '信用利差+久期轮动',
    risk: '信用下沉约束',
    volatility: '2.9%',
    drawdown: '1.4%',
    liquidity: 'T+2',
    capacity: '180亿',
    productFit: '现金管理、固收类',
    createdAt: '2026-01-05',
    status: '已准入',
    rating: 'A',
    managerName: '华衡基金',
    admission: passedAdmission(),
    quota: { used: 42, limit: 50, unit: '亿' },
    kpiHistory: [kpiAQ2, { period: '2026Q1', scores: [90, 86, 88, 83, 85], totalScore: 87.2, grade: 'A', evaluator: '王磊' }],
    committeeIds: ['CMT-002'],
    performanceData: generatePerformance(17, 0.05, 0.029),
    attribution: defaultAttribution,
    auditLog: generateAuditLog('信用债高等级增强'),
  },
  {
    id: 'STR-008',
    name: '可转债波动率套利',
    primaryClass: '固收增强含权',
    secondaryClass: '转债增强',
    source: '波动率+条款博弈',
    risk: '尾部波动较高',
    volatility: '9.6%',
    drawdown: '7.2%',
    liquidity: 'T+10',
    capacity: '25亿',
    productFit: '高风险固收+',
    createdAt: '2026-03-18',
    status: '退出',
    rating: 'D',
    managerName: '澜峰投资',
    admission: passedAdmission(),
    quota: { used: 0, limit: 0, unit: '亿' },
    kpiHistory: [{ period: '2026Q2', scores: [45, 52, 48, 55, 50], totalScore: 48.4, grade: 'D', evaluator: '王磊' }],
    committeeIds: [],
    performanceData: generatePerformance(11, -0.04, 0.096),
    attribution: defaultAttribution,
    auditLog: [
      { timestamp: '2026-05-11 10:00', operator: '王磊', action: '风险处置', detail: '可转债波动率套利启动退出流程，核心人员离职' },
      { timestamp: '2026-06-01 14:30', operator: '王磊', action: 'KPI评分', detail: '可转债波动率套利 2026Q2 评分完成，等级 D' },
      ...generateAuditLog('可转债波动率套利').slice(2),
    ],
  },
];

export const ratingRules: RatingRule[] = [
  { grade: 'A', label: '核心合作', desc: '长期业绩稳健、风控强、信息披露透明', quotaLimit: 50, reviewCycle: '季度', riskRequirement: '季度复核，重大事项 T+1 上报' },
  { grade: 'B', label: '观察合作', desc: '策略有价值但仍需验证', quotaLimit: 20, reviewCycle: '月度', riskRequirement: '月度跟踪，触发指标加密复核' },
  { grade: 'C', label: '战术使用', desc: '适合阶段性机会', quotaLimit: 10, reviewCycle: '周度', riskRequirement: '周度监测，严格止损与到期复盘' },
  { grade: 'D', label: '淘汰', desc: '存在重大风险事件或持续低于基准', quotaLimit: 0, reviewCycle: '—', riskRequirement: '退出报告归档，限制重新准入' },
];

