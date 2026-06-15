// ── 通用 ──
export type Trend = 'up' | 'down' | 'flat';

export interface MetricCard {
  id: string;
  label: string;
  value: string;
  unit?: string;
  delta?: string;
  trend: Trend;
}

export interface WorkbenchRow {
  id: string;
  module: string;
  owner: string;
  status: '正常' | '关注' | '阻塞';
  progressPct: number;
  updatedAt: string;
}

// ── 策略库 ──
export type StrategyStatus = '研究中' | '准入评估中' | '待投委审批' | '观察池' | '已准入' | '已驳回' | '暂停' | '退出';
export type StrategyRating = 'A' | 'B' | 'C' | 'D';
export type CheckStatus = '未开始' | '进行中' | '已通过' | '驳回' | '补充材料';

export interface Strategy {
  id: string;
  name: string;
  primaryClass: string;
  secondaryClass: string;
  source: string;
  risk: string;
  volatility: string;
  drawdown: string;
  liquidity: string;
  capacity: string;
  productFit: string;
  createdAt: string;
  status: StrategyStatus;
  rating?: StrategyRating;
  managerName?: string;
  admission: AdmissionStage[];
  quota?: QuotaInfo;
  kpiHistory: StrategyKPI[];
  committeeIds: string[];
  performanceData: PerformancePoint[];
  attribution: AttributionItem[];
  auditLog: AuditLog[];
}

export interface StrategyFilter {
  searchQuery?: string;
  category?: string;
  status?: string;
  createdMonth?: string;
}

export interface AdmissionCheck {
  name: string;
  status: CheckStatus;
  result?: string;
  operator?: string;
  date?: string;
}

export interface AdmissionStage {
  stage: string;
  checks: AdmissionCheck[];
  status: CheckStatus;
}

export interface StrategyKPI {
  period: string;
  scores: number[];
  totalScore: number;
  grade: StrategyRating;
  evaluator?: string;
}

export interface QuotaInfo {
  used: number;
  limit: number;
  unit: string;
}

export interface RatingRule {
  grade: StrategyRating;
  label: string;
  desc: string;
  quotaLimit: number;
  reviewCycle: string;
  riskRequirement: string;
}

export interface PerformancePoint {
  date: string;
  nav: number;
  benchmark: number;
}

export interface AttributionItem {
  factor: string;
  contribution: number;
}

export interface AuditLog {
  timestamp: string;
  operator: string;
  action: string;
  detail: string;
}

// ── 管理人库 ──
export interface Manager {
  name: string;
  orgType: string;
  coreStrategy: string;
  aum: string;
  cooperation: string;
  rating: string;
  peopleStability: string;
  riskControl: string;
  performance: string;
  capacity: string;
  lastDueDiligence: string;
  hasRiskEvent: string;
}

// ── 投委会 ──
export interface CommitteeItem {
  title: string;
  department: string;
  submitter: string;
  riskLevel: string;
  recommendation: string;
  status: string;
  meetingDate: string;
  voteResult: string;
}

// ── 风险事件 ──
export interface RiskEvent {
  target: string;
  strategyClass: string;
  level: string;
  reason: string;
  exitStatus: string;
  triggerDate: string;
}

// ── KPI 评估 ──
export interface KpiDimension {
  name: string;
  weight: number;
  items: string[];
}

// ── 准入流程 ──
export interface WorkflowStage {
  name: string;
  checks: string[];
}

// ── 评级 ──
export interface RatingLevel {
  name: string;
  desc: string;
  count: string;
  quota: string;
  risk: string;
}

// ── Dashboard ──
export interface DashboardMetric {
  id?: string;
  label: string;
  value: string;
  unit?: string;
  desc?: string;
  delta?: string;
  trend?: Trend;
}

export interface DashboardMetricGroup {
  id: string;
  title: string;
  columns: 3 | 4;
  items: DashboardMetric[];
}

export interface DistributionItem {
  name: string;
  count: number;
}

// ── SPV 策略池 ──
export type SpvStrategyTag = '固收增强含权' | '固收增强' | '量化策略' | '权益策略' | '另类策略' | '海外策略';
export type SpvRiskLevel = '低' | '中' | '高';
export type SpvStatus = '在投' | '待审批' | '冻结' | '已退出';

export interface SPVLinkedProduct {
  name: string;
  amount: string;
}

export interface SPVPerformance {
  annualReturn: string;
  maxDrawdown: string;
  sharpeRatio: string;
  volatility: string;
}

export interface SPV {
  code: string;
  name: string;
  managerName: string;
  strategyTag: SpvStrategyTag;
  aum: number;
  riskLevel: SpvRiskLevel;
  inceptionDate: string;
  maturityDate: string;
  status: SpvStatus;
  linkedProducts: SPVLinkedProduct[];
  performance: SPVPerformance;
}

export interface StrategyPool {
  strategyName: string;
  spvCount: number;
  totalAum: string;
  riskLevel: SpvRiskLevel;
  metricLabel: string;
  metricValue: string;
}

export interface SPVFilter {
  searchQuery?: string;
  strategy?: string;
  status?: string;
  riskLevel?: string;
}

