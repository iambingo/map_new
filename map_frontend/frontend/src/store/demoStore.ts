import { ref, computed } from 'vue';
import axios from 'axios';
import { http } from '@/api/request';

/**
 * 方案 A：为 true 时不请求 portal-snapshot / committee/page-context，仅用前端 Mock，避免后端 500 等打断联调。
 * 在 frontend/.env 设置：VITE_COMMITTEE_OFFLINE_MOCK=true（改后需重启 Vite）。
 */
export function isCommitteeOfflineMock(): boolean {
  const v = import.meta.env.VITE_COMMITTEE_OFFLINE_MOCK;
  return v === 'true' || v === '1';
}

// ═══════════════════════════════════════════════════════════════════════════
// 0-B. 全局 Mock 切换（运行时可切换，持久化到 localStorage）
// ═══════════════════════════════════════════════════════════════════════════

export const isGlobalMock = ref(localStorage.getItem('MAP_GLOBAL_MOCK') !== 'false');

export function toggleGlobalMock(val: boolean) {
  isGlobalMock.value = val;
  localStorage.setItem('MAP_GLOBAL_MOCK', val ? 'true' : 'false');
  localStorage.setItem('MAP_ACTIVE_ROLE', activeRole.value);
  window.location.reload();
}

/** 与 useApi 一致：全局 Mock 或离线 env 开启时不走 BFF / committee HTTP */
export function skipCommitteeHttp(): boolean {
  return isCommitteeOfflineMock() || isGlobalMock.value;
}

export async function useApi<T>(apiCall: () => Promise<any>, mockData: T): Promise<T> {
  if (isGlobalMock.value) {
    console.log(
      '%c📦 [Mock] %c命中 Mock 数据',
      'color:#22D3EE;font-weight:bold',
      'color:#34C759',
    );
    await new Promise(r => setTimeout(r, 500));
    return mockData;
  }
  try {
    const res = await apiCall();
    return res.data as T;
  } catch (err) {
    console.warn('[useApi] 接口报错，降级返回 Mock 数据:', err);
    return mockData;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 1. 用户与角色
// ═══════════════════════════════════════════════════════════════════════════

export type Role =
  | '班子'
  | '部门长'
  | '投资经理'
  | '投资助理'
  | '投管'
  | '混合投资委员会秘书'
  | '混合投资委员会委员'
  | '混合投资委员会主任委员'
  | 'FICC投资委员会秘书'
  | 'FICC投资委员会委员'
  | 'FICC投资委员会主任委员';

export const activeRole = ref<Role>((localStorage.getItem('MAP_ACTIVE_ROLE') as Role) || '投资经理');

export const ROLES: Role[] = [
  '班子',
  '部门长',
  '投资经理',
  '投资助理',
  '投管',
  '混合投资委员会秘书',
  '混合投资委员会委员',
  '混合投资委员会主任委员',
  'FICC投资委员会秘书',
  'FICC投资委员会委员',
  'FICC投资委员会主任委员',
];

// ═══════════════════════════════════════════════════════════════════════════
// 2. T+N 时间轴推演引擎
// ═══════════════════════════════════════════════════════════════════════════

export type TimelineState = 0 | 1 | 2 | 3;
export const timelineState = ref<TimelineState>(0);

// ═══════════════════════════════════════════════════════════════════════════
// 3. 通道型 SPV 嵌套穿透模式
// ═══════════════════════════════════════════════════════════════════════════

export const isPenetrationMode = ref(false);

// ═══════════════════════════════════════════════════════════════════════════
// 4. FICC 投委会决议广播
// ═══════════════════════════════════════════════════════════════════════════
export interface FiccDecisionPayload {
  meetingCode: string;
  confirmedAt: string;
  products: { name: string; position: string; durationRange: string; equityCap: string }[];
}
export const ficcLatestDecision = ref<FiccDecisionPayload | null>(null);

// ═══════════════════════════════════════════════════════════════════════════
// 4. 场景状态：建仓 / 调仓
// ═══════════════════════════════════════════════════════════════════════════

export type OperationScene = '建仓' | '调仓';
export const operationScene = ref<OperationScene>('调仓');

// ═══════════════════════════════════════════════════════════════════════════
// 5. 模型跳转缓存
// ═══════════════════════════════════════════════════════════════════════════

export const modelBackPath = ref('');

// ═══════════════════════════════════════════════════════════════════════════
// 6. 组件全屏放大状态
// ═══════════════════════════════════════════════════════════════════════════

export const maximizedComponent = ref<string | null>(null);

export function setMaximized(id: string) {
  maximizedComponent.value = id;
}

export function clearMaximized() {
  maximizedComponent.value = null;
}

// ═══════════════════════════════════════════════════════════════════════════
// 7. 再平衡跳转目标（沙盘携带任务）
// ═══════════════════════════════════════════════════════════════════════════

export interface RebalanceTarget {
  productId: string;
  gapAmount: number;
}
export const rebalanceTarget = ref<RebalanceTarget | null>(null);

// ═══════════════════════════════════════════════════════════════════════════
// 8. 持仓数据模型
// ═══════════════════════════════════════════════════════════════════════════

export interface PositionRow {
  code: string;
  name: string;
  assetClass: string;
  weightPct: number;
  mktValueWan: number;
  pnl: number;
  duration?: number;
  [key: string]: unknown;
}

export interface ProFormaRow extends PositionRow {
  _isModified: boolean;
  _amountDelta: number;
  _weightDelta: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// 9. 全局任务篮
// ═══════════════════════════════════════════════════════════════════════════

export interface TaskBasketItem {
  id: string;
  type: 'buy' | 'sell';
  assetName: string;
  assetCode: string;
  amount: number;
  source: '模型' | '手动' | '批量';
  status: 'pending' | 'confirmed' | 'executed';
  weightDelta: number;
  productId: string;
  [key: string]: unknown;
}

export type BasketInstruction = TaskBasketItem;

export const taskBasket = ref<TaskBasketItem[]>([]);

let _basketIdSeq = 0;

export function addToBasket(item: Omit<TaskBasketItem, 'id'>): string {
  const id = `bask_${++_basketIdSeq}_${Date.now()}`;
  const entry: TaskBasketItem = { ...item, id } as TaskBasketItem;
  taskBasket.value = [...taskBasket.value, entry];
  return id;
}

export function removeFromBasket(id: string) {
  taskBasket.value = taskBasket.value.filter(item => item.id !== id);
}

export function clearBasket() {
  taskBasket.value = [];
}

export const basketSummary = computed(() => {
  const items = taskBasket.value;
  const totalBuy = items.filter(i => i.type === 'buy').reduce((s, i) => s + i.amount, 0);
  const totalSell = items.filter(i => i.type === 'sell').reduce((s, i) => s + i.amount, 0);
  const netDelta = totalBuy - totalSell;
  const pendingCount = items.filter(i => i.status === 'pending').length;
  const confirmedCount = items.filter(i => i.status === 'confirmed').length;
  return { totalBuy, totalSell, netDelta, pendingCount, confirmedCount, totalCount: items.length };
});

// ═══════════════════════════════════════════════════════════════════════════
// 10. ProForma 持仓叠加引擎 (动态推演)
// ═══════════════════════════════════════════════════════════════════════════

export const isApplyingBasket = ref(false);

export const actualPositions = ref<PositionRow[]>([]);

export const proFormaData = computed<ProFormaRow[]>(() => {
  const isBuilding = operationScene.value === '建仓';

  const base: PositionRow[] = isBuilding
    ? []
    : actualPositions.value;

  if (!isApplyingBasket.value && !isBuilding) return base as ProFormaRow[];

  const instructions = taskBasket.value;
  if (instructions.length === 0 && !isBuilding) return base as ProFormaRow[];

  const codeMap = new Map<string, ProFormaRow>();

  for (const pos of base) {
    codeMap.set(pos.code, {
      ...pos,
      _isModified: false,
      _amountDelta: 0,
      _weightDelta: 0,
    });
  }

  const totalMktValue = base.reduce((s, p) => s + p.mktValueWan, 0);

  for (const inst of instructions) {
    const code = inst.assetCode;
    const deltaAmt = inst.type === 'buy' ? inst.amount : -inst.amount;

    if (codeMap.has(code)) {
      const existing = codeMap.get(code)!;
      existing._amountDelta += deltaAmt;
      existing._weightDelta += inst.weightDelta;
      existing.mktValueWan += deltaAmt;
      existing._isModified = true;
    } else {
      const row: ProFormaRow = {
        code,
        name: inst.assetName,
        assetClass: '待分类',
        weightPct: 0,
        mktValueWan: deltaAmt,
        pnl: 0,
        duration: 0,
        _isModified: true,
        _amountDelta: deltaAmt,
        _weightDelta: inst.weightDelta,
      };
      codeMap.set(code, row);
    }
  }

  const newTotalMktValue = totalMktValue
    + instructions.reduce((s, i) => s + (i.type === 'buy' ? i.amount : -i.amount), 0);

  const denominator = isBuilding
    ? Math.max(newTotalMktValue, 1)
    : Math.max(totalMktValue, 1);

  for (const row of codeMap.values()) {
    if (row.mktValueWan > 0 && denominator > 0) {
      row.weightPct = (row.mktValueWan / denominator) * 100;
    }
  }

  return Array.from(codeMap.values());
});

export const proFormaSummary = computed(() => {
  const data = proFormaData.value;
  if (data.length === 0) return { totalMktValue: 0, modifiedCount: 0, weightedDuration: 0 };

  const totalMktValue = data.reduce((s, r) => s + r.mktValueWan, 0);
  const modifiedCount = data.filter(r => r._isModified).length;
  const weightedDuration = data.reduce((s, r) => {
    const w = totalMktValue > 0 ? r.mktValueWan / totalMktValue : 0;
    return s + (r.duration ?? 0) * w;
  }, 0);

  return { totalMktValue, modifiedCount, weightedDuration };
});

// ═══════════════════════════════════════════════════════════════════════════
// 11. 投委会决议（门户 BFF 快照，替代 Committee 内硬编码 decisionTable）
// ═══════════════════════════════════════════════════════════════════════════

/** 与 CommitteeView 中决议表结构对齐，供组件直接绑定 */
export interface CommitteeDecisionChild {
  asset: string;
  sub: string;
  color: string;
  level: string;
  bubbles: string[];
  logic: string;
}

export interface CommitteeDecisionGroup {
  asset: string;
  sub: string;
  color: string;
  level: string;
  logic: string;
  children: CommitteeDecisionChild[];
}

/** 原 CommitteeView.vue 中硬编码的默认决议表（作为回退） */
const DEFAULT_COMMITTEE_DECISION_TABLE: CommitteeDecisionGroup[] = [
  {
    asset: '债券',
    sub: '固定收益',
    color: '#22D3EE',
    level: '中性偏乐观',
    logic: '利率下行趋势确立，久期可适度拉长',
    children: [
      {
        asset: '利率债',
        sub: '国债/政金债',
        color: '#22D3EE',
        level: '中性偏乐观',
        bubbles: ['利率下行趋势', '期限利差收窄'],
        logic: '长端利率仍有下行空间，增配10Y以上品种',
      },
    ],
  },
  {
    asset: '权益',
    sub: '股票/混合',
    color: '#3B9EFF',
    level: '乐观',
    logic: '估值低位，政策托底明确，结构性机会突出',
    children: [
      {
        asset: '红利',
        sub: '高股息策略',
        color: '#3B9EFF',
        level: '乐观',
        bubbles: ['防御属性', '股息率优势'],
        logic: '高股息策略在震荡市中具备确定性优势',
      },
      {
        asset: '偏股混',
        sub: '主动权益',
        color: '#3B9EFF',
        level: '中性偏乐观',
        bubbles: ['选股Alpha', '结构分化'],
        logic: '关注景气度反转行业，控制仓位',
      },
      {
        asset: '恒生科技',
        sub: '港股科技',
        color: '#3B9EFF',
        level: '中性',
        bubbles: ['估值修复', '政策风险'],
        logic: '估值处于历史低位但需关注政策不确定性',
      },
    ],
  },
  {
    asset: '另类',
    sub: '黄金/商品',
    color: '#F1C40F',
    level: '中性',
    logic: '地缘风险支撑金价，但需关注美联储政策转向',
    children: [
      {
        asset: '黄金',
        sub: '贵金属',
        color: '#F1C40F',
        level: '中性偏乐观',
        bubbles: ['避险需求', '去美元化'],
        logic: '全球央行持续增持，避险需求支撑',
      },
    ],
  },
  {
    asset: '现金',
    sub: '货币类',
    color: '#94A3B8',
    level: '中性',
    logic: '维持基础流动性，关注赎回节奏',
    children: [
      {
        asset: '现金',
        sub: '货币市场',
        color: '#94A3B8',
        level: '中性',
        bubbles: ['流动性管理', '赎回备付'],
        logic: '保持适度现金比例应对潜在赎回',
      },
    ],
  },
];

export const committeeDecisionTable = ref<CommitteeDecisionGroup[]>(
  JSON.parse(JSON.stringify(DEFAULT_COMMITTEE_DECISION_TABLE)) as CommitteeDecisionGroup[],
);

// ═══════════════════════════════════════════════════════════════════════════
// 12. 部门资配决策（投委会 Step 3 正式提交后写入，可供其他页面读取）
// ═══════════════════════════════════════════════════════════════════════════

export interface DeptAllocationDecisionProduct {
  id: string;
  name: string;
  bond: number;
  equity: number;
  alt: number;
  liquidity: number;
}

export interface DeptAllocationDecision {
  period: string;
  decidedAt: string;
  decidedBy: string;
  bondGrade: string;
  bondDuration: string;
  equityGrade: number;
  equityGradeLabel: string;
  equityMix: { 红利: number; 成长: number; 价值: number };
  altNotes: string;
  products: DeptAllocationDecisionProduct[];
}

/** 投委会正式提交的部门资产配置决策结果，供 MAP 其他页面读取 */
export const deptAllocationDecision = ref<DeptAllocationDecision | null>(null);

// ═══════════════════════════════════════════════════════════════════════════
// 13. 统一观点字典（FICC + 混合投委会大一统）
//     数据源：reference/观点模板.pdf（mock：0413 委员会数据）
// ═══════════════════════════════════════════════════════════════════════════

export type VoteLevel = '谨慎' | '中性偏谨慎' | '中性' | '中性偏乐观' | '乐观';

export interface VoteAmplitudeMap {
  谨慎: string;
  中性偏谨慎: string;
  中性: string;
  中性偏乐观: string;
  乐观: string;
}

/**
 * 统一观点配置项，FICC 与混合投委会共享同一字典。
 * amplitudeType: 'bp'  → 收益率类（绝对 bp 加减），保留 4 位小数
 * amplitudeType: 'pct' → 价格指数类（相对 % 乘除），保留 2 位小数
 */
export interface UnifiedVoteConfigItem {
  id: string;
  大类: string;
  细分策略: string;
  标的指数: string;
  当前点位: number;
  amplitudeType: 'bp' | 'pct';
  amplitude: VoteAmplitudeMap;
}

export const UNIFIED_VOTE_CONFIG: UnifiedVoteConfigItem[] = [
  {
    id: 'cd_1y_aaa',
    大类: '固收',
    细分策略: '存单',
    标的指数: '1Y AAA存单',
    当前点位: 1.4825,
    amplitudeType: 'bp',
    amplitude: {
      谨慎: '上行15bp',
      中性偏谨慎: '上行5-15bp',
      中性: '±5bp内',
      中性偏乐观: '下行5-15bp',
      乐观: '下行15bp',
    },
  },
  {
    id: 'credit_3y_aa_plus',
    大类: '固收',
    细分策略: '信用',
    标的指数: '3Y AA+中票',
    当前点位: 1.7814,
    amplitudeType: 'bp',
    amplitude: {
      谨慎: '上行15bp',
      中性偏谨慎: '上行5-15bp',
      中性: '±5bp内',
      中性偏乐观: '下行5-15bp',
      乐观: '下行15bp',
    },
  },
  {
    id: 'rate_10y',
    大类: '固收',
    细分策略: '利率(10Y)',
    标的指数: '10Y国债活跃券',
    当前点位: 1.79,
    amplitudeType: 'bp',
    amplitude: {
      谨慎: '上行15bp',
      中性偏谨慎: '上行5-15bp',
      中性: '±5bp内',
      中性偏乐观: '下行5-15bp',
      乐观: '下行15bp',
    },
  },
  {
    id: 'rate_30y',
    大类: '固收',
    细分策略: '利率(30Y)',
    标的指数: '30Y国债活跃券',
    当前点位: 2.281,
    amplitudeType: 'bp',
    amplitude: {
      谨慎: '上行15bp',
      中性偏谨慎: '上行5-15bp',
      中性: '±5bp内',
      中性偏乐观: '下行5-15bp',
      乐观: '下行15bp',
    },
  },
  {
    id: 'cb_csi_convert',
    大类: '含权',
    细分策略: '转债',
    标的指数: '中证转债',
    当前点位: 502.65,
    amplitudeType: 'pct',
    amplitude: {
      谨慎: '-10%以下',
      中性偏谨慎: '-10%到-3%',
      中性: '-3%到3%',
      中性偏乐观: '3%到10%',
      乐观: '10%以上',
    },
  },
  {
    id: 'bond_fund_885007',
    大类: '含权',
    细分策略: '二级债基',
    标的指数: '885007',
    当前点位: 5224.57,
    amplitudeType: 'pct',
    amplitude: {
      谨慎: '-5%以下',
      中性偏谨慎: '-5%到-2%',
      中性: '-2%到2%',
      中性偏乐观: '2%到5%',
      乐观: '5%以上',
    },
  },
  {
    id: 'dividend_csi_total',
    大类: '含权',
    细分策略: '红利',
    标的指数: '中证红利全收益',
    当前点位: 11945.58,
    amplitudeType: 'pct',
    amplitude: {
      谨慎: '-10%以下',
      中性偏谨慎: '-10%到-3%',
      中性: '-3%到3%',
      中性偏乐观: '3%到10%',
      乐观: '10%以上',
    },
  },
  {
    id: 'equity_mixed_885001',
    大类: '含权',
    细分策略: '偏股混',
    标的指数: '885001',
    当前点位: 7228.45,
    amplitudeType: 'pct',
    amplitude: {
      谨慎: '-10%以下',
      中性偏谨慎: '-10%到-3%',
      中性: '-3%到3%',
      中性偏乐观: '3%到10%',
      乐观: '10%以上',
    },
  },
  {
    id: 'hktech_513310',
    大类: '含权',
    细分策略: '恒生科技',
    标的指数: '513310恒生科技ETF',
    当前点位: 4986.78,
    amplitudeType: 'pct',
    amplitude: {
      谨慎: '-10%以下',
      中性偏谨慎: '-10%到-3%',
      中性: '-3%到3%',
      中性偏乐观: '3%到10%',
      乐观: '10%以上',
    },
  },
  {
    id: 'gold_518880',
    大类: '另类',
    细分策略: '黄金',
    标的指数: '518880黄金ETF',
    当前点位: 7.283,
    amplitudeType: 'pct',
    amplitude: {
      谨慎: '-10%以下',
      中性偏谨慎: '-10%到-3%',
      中性: '-3%到3%',
      中性偏乐观: '3%到10%',
      乐观: '10%以上',
    },
  },
  {
    id: 'crude_oil',
    大类: '另类',
    细分策略: '原油',
    标的指数: 'SC原油主力合约',
    当前点位: 490.0,
    amplitudeType: 'pct',
    amplitude: {
      谨慎: '-10%以下',
      中性偏谨慎: '-10%到-3%',
      中性: '-3%到3%',
      中性偏乐观: '3%到10%',
      乐观: '10%以上',
    },
  },
];

// ─── 分发策略子集 ─────────────────────────────────────────────────────────────

/** FICC 投委会资产列表：偏重固收，含存单、信用、利率、转债、二级债基 */
export const FICC_ASSET_LIST: UnifiedVoteConfigItem[] = UNIFIED_VOTE_CONFIG.filter(item =>
  ['cd_1y_aaa', 'credit_3y_aa_plus', 'rate_10y', 'rate_30y', 'cb_csi_convert', 'bond_fund_885007'].includes(item.id),
);

/**
 * 混合投委会资产列表：偏重权益，含红利、偏股混、恒生科技、黄金，
 * 附 10Y/30Y 利率债作为固收基准参考。
 */
export const MIXED_ASSET_LIST: UnifiedVoteConfigItem[] = UNIFIED_VOTE_CONFIG.filter(item =>
  ['dividend_csi_total', 'equity_mixed_885001', 'hktech_513310', 'gold_518880', 'rate_10y', 'rate_30y'].includes(item.id),
);

// ═══════════════════════════════════════════════════════════════════════════
// 季度展望配置（FICC 投委会专用）
//
// 季度视角较月度观察窗口更长，幅度档位相应拉宽：
//   bp 类（收益率）：月度 ±5/5-15/15bp → 季度 ±15/15-30/30bp
//   pct 类（宽幅，如权益/另类）：月度 ±3/3-10/10% → 季度 ±8/8-20/20%
//   pct 类（窄幅，如债基）：月度 ±2/2-5/5%  → 季度 ±5/5-12/12%
//
// 资产范围：在月度 FICC 基础上，追加红利全收益、恒生科技、黄金、REITs，
// 覆盖 PDF《观点模板》中 固收 / 含权 / 另类 三大类全量标的。
// ═══════════════════════════════════════════════════════════════════════════

export const FICC_QUARTERLY_CONFIG: UnifiedVoteConfigItem[] = [
  // ──────────────── 固收 ────────────────
  {
    id: 'q_cd_1y_aaa',
    大类: '固收',
    细分策略: '存单(季)',
    标的指数: '1Y AAA存单',
    当前点位: 1.4825,
    amplitudeType: 'bp',
    amplitude: {
      谨慎:     '上行30bp',
      中性偏谨慎: '上行15-30bp',
      中性:     '±15bp内',
      中性偏乐观: '下行15-30bp',
      乐观:     '下行30bp',
    },
  },
  {
    id: 'q_credit_3y_aa_plus',
    大类: '固收',
    细分策略: '信用(季)',
    标的指数: '3Y AA+中票',
    当前点位: 1.7814,
    amplitudeType: 'bp',
    amplitude: {
      谨慎:     '上行30bp',
      中性偏谨慎: '上行15-30bp',
      中性:     '±15bp内',
      中性偏乐观: '下行15-30bp',
      乐观:     '下行30bp',
    },
  },
  {
    id: 'q_rate_10y',
    大类: '固收',
    细分策略: '利率10Y(季)',
    标的指数: '10Y国债活跃券',
    当前点位: 1.79,
    amplitudeType: 'bp',
    amplitude: {
      谨慎:     '上行30bp',
      中性偏谨慎: '上行15-30bp',
      中性:     '±15bp内',
      中性偏乐观: '下行15-30bp',
      乐观:     '下行30bp',
    },
  },
  {
    id: 'q_rate_30y',
    大类: '固收',
    细分策略: '利率30Y(季)',
    标的指数: '30Y国债活跃券',
    当前点位: 2.281,
    amplitudeType: 'bp',
    amplitude: {
      谨慎:     '上行30bp',
      中性偏谨慎: '上行15-30bp',
      中性:     '±15bp内',
      中性偏乐观: '下行15-30bp',
      乐观:     '下行30bp',
    },
  },
  // ──────────────── 含权 ────────────────
  {
    id: 'q_cb_csi_convert',
    大类: '含权',
    细分策略: '转债(季)',
    标的指数: '中证转债',
    当前点位: 502.65,
    amplitudeType: 'pct',
    amplitude: {
      谨慎:     '-20%以下',
      中性偏谨慎: '-20%到-8%',
      中性:     '-8%到8%',
      中性偏乐观: '8%到20%',
      乐观:     '20%以上',
    },
  },
  {
    id: 'q_bond_fund_885007',
    大类: '含权',
    细分策略: '二级债基(季)',
    标的指数: '885007',
    当前点位: 5224.57,
    amplitudeType: 'pct',
    amplitude: {
      谨慎:     '-12%以下',
      中性偏谨慎: '-12%到-5%',
      中性:     '-5%到5%',
      中性偏乐观: '5%到12%',
      乐观:     '12%以上',
    },
  },
  {
    id: 'q_dividend_csi_total',
    大类: '含权',
    细分策略: '红利(季)',
    标的指数: '中证红利全收益',
    当前点位: 11945.58,
    amplitudeType: 'pct',
    amplitude: {
      谨慎:     '-20%以下',
      中性偏谨慎: '-20%到-8%',
      中性:     '-8%到8%',
      中性偏乐观: '8%到20%',
      乐观:     '20%以上',
    },
  },
  {
    id: 'q_hktech_513310',
    大类: '含权',
    细分策略: '恒生科技(季)',
    标的指数: '513310恒生科技ETF',
    当前点位: 4986.78,
    amplitudeType: 'pct',
    amplitude: {
      谨慎:     '-20%以下',
      中性偏谨慎: '-20%到-8%',
      中性:     '-8%到8%',
      中性偏乐观: '8%到20%',
      乐观:     '20%以上',
    },
  },
  {
    id: 'q_reits_csi_total',
    大类: '含权',
    细分策略: 'REITs(季)',
    标的指数: '中证REITs全收益',
    当前点位: 1018.07,
    amplitudeType: 'pct',
    amplitude: {
      谨慎:     '-20%以下',
      中性偏谨慎: '-20%到-8%',
      中性:     '-8%到8%',
      中性偏乐观: '8%到20%',
      乐观:     '20%以上',
    },
  },
  // ──────────────── 另类 ────────────────
  {
    id: 'q_gold_518880',
    大类: '另类',
    细分策略: '黄金(季)',
    标的指数: '518880黄金ETF',
    当前点位: 7.283,
    amplitudeType: 'pct',
    amplitude: {
      谨慎:     '-20%以下',
      中性偏谨慎: '-20%到-8%',
      中性:     '-8%到8%',
      中性偏乐观: '8%到20%',
      乐观:     '20%以上',
    },
  },
  {
    id: 'q_crude_oil',
    大类: '另类',
    细分策略: '原油(季)',
    标的指数: 'SC原油主力合约',
    当前点位: 490.0,
    amplitudeType: 'pct',
    amplitude: {
      谨慎:     '-20%以下',
      中性偏谨慎: '-20%到-8%',
      中性:     '-8%到8%',
      中性偏乐观: '8%到20%',
      乐观:     '20%以上',
    },
  },
];

/**
 * FICC 季度展望资产列表（供页面直接渲染）。
 * 涵盖 固收 4 项 + 含权 5 项 + 另类 2 项，合计 11 项。
 */
export const FICC_QUARTERLY_ASSET_LIST: UnifiedVoteConfigItem[] = FICC_QUARTERLY_CONFIG;

// ─── 点位区间推算引擎 ─────────────────────────────────────────────────────────

export interface TargetRange {
  low: number | null;
  high: number | null;
}

/**
 * 通用点位区间推算函数。
 *
 * bp 格式（收益率类，如"上行15bp"、"上行5-15bp"、"±5bp内"、"下行5-15bp"）：
 *   delta = bpValue / 10000 * 100，结果保留 4 位小数。
 *   上行 → 收益率升高（low ≤ high，low 为较小变动，high 为较大变动）。
 *   下行 → 收益率降低。
 *   "谨慎/乐观"单档（如"上行15bp"）视为无上界/无下界，对应端返回 null。
 *
 * pct 格式（价格指数类，如"-3%到3%"、"10%以上"、"-10%以下"）：
 *   target = currentPoint × (1 + pct/100)，结果保留 2 位小数。
 */
export function calcTargetRange(currentPoint: number, amplitudeStr: string): TargetRange {
  const s = amplitudeStr.trim();

  if (s.includes('bp')) {
    const bpToDelta = (n: number) => parseFloat((n / 10000 * 100).toFixed(4));
    const fix4 = (n: number) => parseFloat(n.toFixed(4));

    // ±xbp内
    const pmMatch = s.match(/^[±\+\-]?(\d+(?:\.\d+)?)bp内?$/);
    if (pmMatch) {
      const d = bpToDelta(parseFloat(pmMatch[1]));
      return { low: fix4(currentPoint - d), high: fix4(currentPoint + d) };
    }

    // 上行/下行 min-maxbp (range)
    const rangeMatch = s.match(/^(上行|下行)(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)bp$/);
    if (rangeMatch) {
      const dir = rangeMatch[1];
      const dMin = bpToDelta(parseFloat(rangeMatch[2]));
      const dMax = bpToDelta(parseFloat(rangeMatch[3]));
      return dir === '上行'
        ? { low: fix4(currentPoint + dMin), high: fix4(currentPoint + dMax) }
        : { low: fix4(currentPoint - dMax), high: fix4(currentPoint - dMin) };
    }

    // 上行/下行 single bp (extreme grade, one side unbounded)
    const singleMatch = s.match(/^(上行|下行)(\d+(?:\.\d+)?)bp$/);
    if (singleMatch) {
      const dir = singleMatch[1];
      const d = bpToDelta(parseFloat(singleMatch[2]));
      return dir === '上行'
        ? { low: fix4(currentPoint + d), high: null }
        : { low: null, high: fix4(currentPoint - d) };
    }

    return { low: null, high: null };
  }

  if (s.includes('%')) {
    const fix2 = (n: number) => parseFloat(n.toFixed(2));
    const scale = (pct: number) => fix2(currentPoint * (1 + pct / 100));

    // x%以上
    const aboveMatch = s.match(/^([\+\-]?\d+(?:\.\d+)?)%以上$/);
    if (aboveMatch) {
      return { low: scale(parseFloat(aboveMatch[1])), high: null };
    }

    // x%以下
    const belowMatch = s.match(/^([\+\-]?\d+(?:\.\d+)?)%以下$/);
    if (belowMatch) {
      return { low: null, high: scale(parseFloat(belowMatch[1])) };
    }

    // a%到b%
    const toMatch = s.match(/^([\+\-]?\d+(?:\.\d+)?)%到([\+\-]?\d+(?:\.\d+)?)%$/);
    if (toMatch) {
      const a = parseFloat(toMatch[1]);
      const b = parseFloat(toMatch[2]);
      return { low: scale(Math.min(a, b)), high: scale(Math.max(a, b)) };
    }
  }

  return { low: null, high: null };
}

// ─── 票数统计引擎 ─────────────────────────────────────────────────────────────

/** 委员单次提交记录：votes 是 细分策略名 → 档位 的映射 */
export interface CommitteeMemberSubmission {
  userId?: number | string;
  submittedAt?: string;
  votes: Partial<Record<string, VoteLevel>>;
  /**
   * 是否为秘书代填。当 submitVote 以 targetMemberId 调用时自动置为 true。
   */
  isProxy?: boolean;
  /**
   * 代填人的角色标识（即发起代填操作的秘书的 activeRole 值）。
   */
  proxySubmitterRole?: string;
}

/** 5档分布 + 加权均值 + 共识档位结论 */
export interface VoteDistributionResult {
  /** 每个档位获得的票数，未投票档位为 0 */
  distribution: Record<VoteLevel, number>;
  /** 参与投票总人数（过滤掉未投该资产的委员） */
  totalVotes: number;
  /**
   * 加权均值（谨慎=1 … 乐观=5），保留两位小数。
   * 无票时返回 null。
   */
  weightedMean: number | null;
  /**
   * 共识档位结论：对加权均值四舍五入后映射回档位名称。
   * 无票时返回 null。
   */
  consensusLevel: VoteLevel | null;
}

const VOTE_LEVEL_SCORE: Record<VoteLevel, number> = {
  谨慎: 1,
  中性偏谨慎: 2,
  中性: 3,
  中性偏乐观: 4,
  乐观: 5,
};

const VOTE_SCORE_LEVEL: Record<number, VoteLevel> = {
  1: '谨慎',
  2: '中性偏谨慎',
  3: '中性',
  4: '中性偏乐观',
  5: '乐观',
};

/**
 * 统计某细分策略在所有委员提交记录中的票数分布，并输出加权均值与共识档位。
 *
 * @param assetName  细分策略名称（须与 UNIFIED_VOTE_CONFIG 中的 细分策略 字段一致）
 * @param submissions 所有委员的提交记录数组
 */
export function calcVoteDistribution(
  assetName: string,
  submissions: CommitteeMemberSubmission[],
): VoteDistributionResult {
  const distribution: Record<VoteLevel, number> = {
    谨慎: 0,
    中性偏谨慎: 0,
    中性: 0,
    中性偏乐观: 0,
    乐观: 0,
  };

  for (const sub of submissions) {
    const vote = sub.votes[assetName];
    if (vote && vote in distribution) {
      distribution[vote]++;
    }
  }

  const totalVotes = (Object.values(distribution) as number[]).reduce((s, c) => s + c, 0);

  if (totalVotes === 0) {
    return { distribution, totalVotes: 0, weightedMean: null, consensusLevel: null };
  }

  const weightedSum = (Object.entries(distribution) as [VoteLevel, number][]).reduce(
    (s, [level, count]) => s + count * VOTE_LEVEL_SCORE[level],
    0,
  );

  const rawMean = weightedSum / totalVotes;
  const weightedMean = parseFloat(rawMean.toFixed(2));
  const rounded = Math.max(1, Math.min(5, Math.round(rawMean))) as 1 | 2 | 3 | 4 | 5;
  const consensusLevel = VOTE_SCORE_LEVEL[rounded];

  return { distribution, totalVotes, weightedMean, consensusLevel };
}

// ─── 委员名单 ─────────────────────────────────────────────────────────────────

/** 可遍历的委员描述，供秘书代填时选人 */
export interface CommitteeMember {
  id: string;
  name: string;
  role: string;
}

/** 混合投委会委员名单 */
export const COMMITTEE_MEMBERS: CommitteeMember[] = [
  { id: 'm0', name: '曾XX', role: '主任委员' },
  { id: 'm1', name: '陈XX', role: '班子' },
  { id: 'm2', name: '张XX', role: '部门长' },
  { id: 'm3', name: '李XX', role: '投资经理' },
  { id: 'm4', name: '王XX', role: '部门长' },
  { id: 'm5', name: '赵XX', role: '投资经理' },
  { id: 'm6', name: '刘XX', role: '风控合规总监' },
];

/** FICC 投委会委员名单 */
export const FICC_COMMITTEE_MEMBERS: CommitteeMember[] = [
  { id: 'f1', name: '王XX', role: '固收主任' },
  { id: 'f2', name: '张XX', role: '利率策略' },
  { id: 'f3', name: '李XX', role: '信用策略' },
  { id: 'f4', name: '王XX', role: '货币市场' },
  { id: 'f5', name: '赵XX', role: '跨境固收' },
  { id: 'f6', name: '刘XX', role: '量化固收' },
  { id: 'f7', name: '周XX', role: '固收研究' },
];

// ─── 代填感知的投票提交 ───────────────────────────────────────────────────────

/**
 * 向 BFF 提交一份委员问卷，支持秘书（RPA）代填模式。
 *
 * @param meetingId      目标会议 ID（由调用方通过 resolveVotingMeetingId 或类似逻辑获取）
 * @param payload        标准 submit-vote 请求体（与 /v1/committee/meetings/:id/submit-vote 的 body 保持一致）
 * @param targetMemberId 可选。若传入，本次提交绑定到该委员名下（代填），并自动加 isProxy: true。
 *                       若不传，绑定到当前 activeRole 所对应的委员（自填）。
 * @returns              归档用的 CommitteeMemberSubmission 对象，调用方可直接写入本地 reactive。
 */
export async function submitVote(
  meetingId: number,
  payload: Record<string, unknown>,
  targetMemberId?: string,
): Promise<CommitteeMemberSubmission> {
  const isProxy = !!targetMemberId;

  // 从 "m1"/"m2" 格式中提取数字 user_id 供后端使用
  const numericUserId = targetMemberId
    ? parseInt(targetMemberId.replace(/\D/g, ''), 10)
    : undefined;

  const body: Record<string, unknown> = {
    ...payload,
    ...(isProxy && !isNaN(numericUserId!) && {
      target_member_id: numericUserId,
      is_proxy: true,
      proxy_submitter_role: activeRole.value,
    }),
  };

  await useApi(() => http.post(`/v1/committee/meetings/${meetingId}/submit-vote`, body), undefined);

  const submission: CommitteeMemberSubmission = {
    userId: targetMemberId ?? activeRole.value,
    submittedAt: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    votes: (payload.votes as Partial<Record<string, VoteLevel>>) ?? {},
    ...(isProxy && {
      isProxy: true,
      proxySubmitterRole: activeRole.value,
    }),
  };

  return submission;
}

export interface PortalSnapshotChoiceResult {
  winner: string;
  vote_counts: Record<string, number>;
}

export interface PortalSnapshot {
  snapshot_at: string;
  is_stale: boolean;
  stale_reason: string | null;
  taa_guidance: {
    source_resolution: { resolution_id?: number; meeting_id?: number; published_at?: string | null } | null;
    choice_results: Record<string, PortalSnapshotChoiceResult>;
    numeric_results: Record<string, Record<string, unknown>>;
    published_at: string | null;
  };
  positions: Record<string, unknown> | null;
  deviation_analysis: Record<string, unknown>;
  rebalance_urgency: { level: string; reason: string };
  navigation_tiles: Array<Record<string, unknown>>;
}

const ROLE_QUERY: Record<Role, string> = {
  班子: 'ADMIN',
  部门长: 'COMMITTEE_MEMBER',
  投资经理: 'PM',
  投资助理: 'ANALYST',
  投管: 'PM',
  混合投资委员会秘书: 'COMMITTEE_SECRETARY',
  混合投资委员会委员: 'COMMITTEE_MEMBER',
  混合投资委员会主任委员: 'COMMITTEE_CHAIR',
  FICC投资委员会秘书: 'FICC_SECRETARY',
  FICC投资委员会委员: 'FICC_MEMBER',
  FICC投资委员会主任委员: 'FICC_CHAIR',
};

const TAA_KEY_META: Record<
  string,
  { asset: string; sub: string; color: string; childAsset: string; childSub: string }
> = {
  equity_view: {
    asset: '权益',
    sub: '股票/混合',
    color: '#3B9EFF',
    childAsset: '股票',
    childSub: '投委指引',
  },
  bond_view: {
    asset: '债券',
    sub: '固定收益',
    color: '#22D3EE',
    childAsset: '债券',
    childSub: '投委指引',
  },
  commodity_view: {
    asset: '另类',
    sub: '黄金/商品',
    color: '#F1C40F',
    childAsset: '商品',
    childSub: '投委指引',
  },
  cash_view: {
    asset: '现金',
    sub: '货币类',
    color: '#94A3B8',
    childAsset: '现金',
    childSub: '投委指引',
  },
};

function winnerToCN(w: string): string {
  const m: Record<string, string> = {
    overweight: '乐观',
    neutral: '中性',
    underweight: '谨慎',
  };
  return m[w] ?? w;
}

/** 由 choice_results（门户快照或 ic_resolutions.aggregated_taa）生成决议表行 */
function mapChoiceResultsToDecisionTable(
  cr: Record<string, PortalSnapshotChoiceResult>,
): CommitteeDecisionGroup[] {
  const keys = Object.keys(cr);
  if (keys.length === 0) return [];

  const groups: CommitteeDecisionGroup[] = [];
  for (const key of keys) {
    const meta = TAA_KEY_META[key];
    if (!meta) continue;
    const row = cr[key];
    if (!row?.winner) continue;
    const level = winnerToCN(row.winner);
    const counts = row.vote_counts ?? {};
    const bubbles = Object.entries(counts).map(([k, v]) => `${k}:${v}票`);
    const logic = `投委众数：${row.winner}（${Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${k} ${v}`)
      .join('，')}）`;
    groups.push({
      asset: meta.asset,
      sub: meta.sub,
      color: meta.color,
      level,
      logic,
      children: [
        {
          asset: meta.childAsset,
          sub: meta.childSub,
          color: meta.color,
          level,
          bubbles: bubbles.length ? bubbles : ['（无分项票数）'],
          logic,
        },
      ],
    });
  }
  return groups;
}

function mapPortalToDecisionTable(snapshot: PortalSnapshot): CommitteeDecisionGroup[] {
  return mapChoiceResultsToDecisionTable(snapshot.taa_guidance?.choice_results ?? {});
}

/** page-context 返回的 aggregated_taa 与门户结构一致时，提取 choice_results */
function choiceResultsFromAggregatedTaa(
  aggregated: Record<string, unknown> | undefined,
): Record<string, PortalSnapshotChoiceResult> | null {
  if (!aggregated || typeof aggregated !== 'object') return null;
  const raw = aggregated.choice_results;
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  return raw as Record<string, PortalSnapshotChoiceResult>;
}

export const portalSnapshot = ref<PortalSnapshot | null>(null);
export const portalSnapshotLoading = ref(false);
export const portalSnapshotError = ref<string | null>(null);

/** GET /v1/committee/page-context — 会议元数据 + 投票摘要（与门户快照并行拉取） */
export interface CommitteeVoteRowDTO {
  user_id: number;
  submitted_at: string | null;
}

export interface CommitteeMeetingSummaryDTO {
  id: number;
  meeting_code: string;
  title: string;
  type: string;
  status: string;
  scheduled_at: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface CommitteeResolutionSummaryDTO {
  id: number;
  meeting_id: number;
  aggregated_taa: Record<string, unknown>;
  ai_minutes: string | null;
  published_at: string | null;
  published_by: number | null;
  created_at: string;
}

export interface CommitteePageContextDTO {
  meeting: CommitteeMeetingSummaryDTO | null;
  resolution: CommitteeResolutionSummaryDTO | null;
  votes: CommitteeVoteRowDTO[];
}

export const committeePageContext = ref<CommitteePageContextDTO | null>(null);
export const committeeContextLoading = ref(false);
export const committeeContextError = ref<string | null>(null);

/** 离线 Mock 默认「进行中」会议，与 CommitteeView MOCK_MEETINGS id=3 对齐 */
const MOCK_ACTIVE_MEETING_SUMMARY: CommitteeMeetingSummaryDTO = {
  id: 3,
  meeting_code: 'IC-2026-Q2-04',
  title: '混合投委会 2026 Q2 投资策略与TAA目标决议',
  type: 'mixed',
  status: '进行中',
  scheduled_at: '2026-04-15T14:00:00',
  created_by: 1,
  created_at: '2026-04-01T10:00:00',
  updated_at: '2026-04-15T14:00:00',
};

export interface CommitteeMeetingListItem {
  id: number;
  status: string;
}

const MOCK_COMMITTEE_MEETING_LIST: CommitteeMeetingListItem[] = [
  { id: 1, status: '已归档' },
  { id: 2, status: '已结束' },
  { id: 3, status: '进行中' },
];

export const committeeMeetingList = ref<CommitteeMeetingListItem[]>([]);

function mapCommitteeMeetingStatus(status: string): string {
  switch (status) {
    case 'draft': return '筹备中';
    case 'voting': return '进行中';
    case 'published': return '已结束';
    default: return status;
  }
}

/** 拉取混合投委会会议列表（H5 投票页 / 会议 ID 解析兜底） */
export async function fetchCommitteeMeetingList() {
  if (skipCommitteeHttp()) {
    committeeMeetingList.value = [...MOCK_COMMITTEE_MEETING_LIST];
    return;
  }
  const items = await useApi(
    () => http.get<Array<{ id: number; status: string }>>('/v1/committee/meetings', {
      params: { type: 'mixed' },
    }),
    MOCK_COMMITTEE_MEETING_LIST,
  );
  committeeMeetingList.value = Array.isArray(items)
    ? items.map(m => ({ id: m.id, status: mapCommitteeMeetingStatus(m.status) }))
    : [...MOCK_COMMITTEE_MEETING_LIST];
}

/**
 * 解析当前可投票会议 ID（与 CommitteeView.resolveVotingMeetingId 逻辑一致）。
 * 优先级：URL meeting_id → page-context → 进行中会议 → 列表首条
 */
export function resolveVotingMeetingId(options?: { urlMeetingId?: number | null }): number | null {
  const urlId = options?.urlMeetingId;
  if (urlId != null && !Number.isNaN(urlId)) return urlId;
  const ctxId = committeePageContext.value?.meeting?.id;
  if (typeof ctxId === 'number') return ctxId;
  const active = committeeMeetingList.value.find(m => m.status === '进行中');
  if (active) return active.id;
  return committeeMeetingList.value[0]?.id ?? null;
}

function formatAxiosError(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const d = e.response?.data;
    if (typeof d === 'object' && d && 'detail' in d) {
      return String((d as { detail: unknown }).detail);
    }
    return e.message;
  }
  if (e instanceof Error) return e.message;
  return String(e);
}

/**
 * 拉取门户 BFF 快照，用后端 `taa_guidance.choice_results` 覆盖投委会决议表（有数据时）。
 * GET /api/v1/workspace/portal-snapshot（axios baseURL=/api → 路径 /v1/workspace/portal-snapshot）
 * （MAP 门户默认 Tab 使用；投委会 Tab 请用 fetchCommitteePageData）
 */
export async function fetchMeetingResolution() {
  if (skipCommitteeHttp()) {
    portalSnapshotLoading.value = false;
    portalSnapshotError.value = null;
    portalSnapshot.value = null;
    return;
  }
  portalSnapshotLoading.value = true;
  portalSnapshotError.value = null;
  const path = '/v1/workspace/portal-snapshot';
  const role = ROLE_QUERY[activeRole.value] ?? 'PM';
  try {
    const { data } = await http.get<PortalSnapshot>(path, {
      params: { role },
    });
    portalSnapshot.value = data;
    const mapped = mapPortalToDecisionTable(data);
    if (mapped.length > 0) {
      committeeDecisionTable.value = mapped;
    }
  } catch (e: unknown) {
    portalSnapshotError.value = formatAxiosError(e);
  } finally {
    portalSnapshotLoading.value = false;
  }
}

/**
 * 投委会视图专用：并行请求门户快照 + 投委会只读上下文，互不拖死（allSettled）。
 * - 决议表仍来自 portal-snapshot 的 choice_results（有则覆盖，无则保留默认 Mock 表）
 * - 会议编号 / 投票条数等来自 committee/page-context
 */
export async function fetchCommitteePageData() {
  if (skipCommitteeHttp()) {
    portalSnapshotLoading.value = false;
    committeeContextLoading.value = false;
    portalSnapshotError.value = null;
    committeeContextError.value = null;
    portalSnapshot.value = null;
    committeePageContext.value = {
      meeting: MOCK_ACTIVE_MEETING_SUMMARY,
      resolution: null,
      votes: [],
    };
    committeeMeetingList.value = [...MOCK_COMMITTEE_MEETING_LIST];
    // eslint-disable-next-line no-console
    console.log(
      '%c📴 [CommitteeView API]',
      'color:#94A3B8;font-weight:bold',
      isCommitteeOfflineMock()
        ? 'VITE_COMMITTEE_OFFLINE_MOCK 已开启：使用本地 Mock 会议上下文'
        : '全局 Mock 已开启：使用本地 Mock 会议上下文',
    );
    return;
  }
  // eslint-disable-next-line no-console
  console.log(
    '%c🚀 [CommitteeView API]',
    'color:#22D3EE;font-weight:bold',
    '开始拉取投委会页数据（portal-snapshot ∥ committee/page-context）',
  );
  portalSnapshotLoading.value = true;
  committeeContextLoading.value = true;
  portalSnapshotError.value = null;
  committeeContextError.value = null;

  const pathSnap = '/v1/workspace/portal-snapshot';
  const pathCtx = '/v1/committee/page-context';
  const role = ROLE_QUERY[activeRole.value] ?? 'PM';
  const base = http.defaults.baseURL ?? '';
  // eslint-disable-next-line no-console
  console.log(
    '%c🚀 [CommitteeView API]',
    'color:#22D3EE;font-weight:bold',
    '即将发出请求',
    { pathSnap, pathCtx, role, axiosBaseURL: base },
  );

  try {
    const [snapRes, ctxRes] = await Promise.allSettled([
      http.get<PortalSnapshot>(pathSnap, { params: { role } }),
      http.get<CommitteePageContextDTO>(pathCtx),
    ]);

    let portalMappedRows = 0;

    if (snapRes.status === 'fulfilled') {
      const data = snapRes.value.data;
      portalSnapshot.value = data;
      const mapped = mapPortalToDecisionTable(data);
      portalMappedRows = mapped.length;
      if (mapped.length > 0) {
        committeeDecisionTable.value = mapped;
      }
      // eslint-disable-next-line no-console
      console.log(
        '%c✅ [CommitteeView API]',
        'color:#34C759;font-weight:bold',
        'portal-snapshot 成功',
        {
          is_stale: data.is_stale,
          stale_reason: data.stale_reason,
          choiceKeys: Object.keys(data.taa_guidance?.choice_results ?? {}),
          mappedRows: mapped.length,
        },
      );
    } else {
      portalSnapshotError.value = formatAxiosError(snapRes.reason);
      // eslint-disable-next-line no-console
      console.error('%c❌ [CommitteeView API]', 'color:#F97316;font-weight:bold', 'portal-snapshot 失败', snapRes.reason);
    }

    if (ctxRes.status === 'fulfilled') {
      const ctx = ctxRes.value.data;
      committeePageContext.value = {
        meeting: ctx.meeting ?? null,
        resolution: ctx.resolution ?? null,
        votes: Array.isArray(ctx.votes) ? ctx.votes : [],
      };
      /** 门户快照无 choice_results 时，用 resolutions 表第一条的 aggregated_taa 填决议表 */
      if (portalMappedRows === 0 && ctx.resolution?.aggregated_taa) {
        const cr = choiceResultsFromAggregatedTaa(
          ctx.resolution.aggregated_taa as Record<string, unknown>,
        );
        if (cr) {
          const fromDb = mapChoiceResultsToDecisionTable(cr);
          if (fromDb.length > 0) {
            committeeDecisionTable.value = fromDb;
          }
        }
      }
      // eslint-disable-next-line no-console
      console.log(
        '%c✅ [CommitteeView API]',
        'color:#34C759;font-weight:bold',
        'committee/page-context 成功',
        {
          meetingCode: ctx.meeting?.meeting_code ?? null,
          voteRows: committeePageContext.value.votes.length,
          hasResolution: !!ctx.resolution,
        },
      );
    } else {
      committeeContextError.value = formatAxiosError(ctxRes.reason);
      committeePageContext.value = { meeting: null, resolution: null, votes: [] };
      // eslint-disable-next-line no-console
      console.error('%c❌ [CommitteeView API]', 'color:#F97316;font-weight:bold', 'committee/page-context 失败', ctxRes.reason);
    }
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('%c❌ [CommitteeView API]', 'color:#F97316;font-weight:bold', '未预期的同步错误', e);
  } finally {
    portalSnapshotLoading.value = false;
    committeeContextLoading.value = false;
    // eslint-disable-next-line no-console
    console.log('%c🏁 [CommitteeView API]', 'color:#94A3B8;font-weight:bold', '拉取流程结束');
  }
}
