"""
Black-Litterman 资产配置模型 v3
================================
更新内容：
  - w_mkt 改为 SAA + 风险平价（带相关性）
  - 流动性单独处理，不进 BL
  - 单大类权重约束做成配置项（层面B：总组合占比）
  - 大类内部风险平价自动从 Σ 子矩阵计算
  - 日期改为滚动窗口：每次只需改 meeting_date
    hist_start / hist_end 自动计算

每月使用说明：
  投委会开会当天，只需修改两处：
    1. DATE_CONFIG["meeting_date"] = "本次开会日期"
    2. VOTES_CONFIG = {录入本次投票结果}
  其他配置不动，直接运行即可
"""

# ═══════════════════════════════════════════════════════════
#  SECTION 0：依赖
# ═══════════════════════════════════════════════════════════
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ═══════════════════════════════════════════════════════════
#  SECTION 1：全局配置
# ═══════════════════════════════════════════════════════════

# ── 1.1 日期配置 ────────────────────────────────────────────
# 每月开会前只需修改 meeting_date 这一行
# hist_start / hist_end 由 resolve_dates() 自动推算
DATE_CONFIG = {
    "meeting_date": "20250507",   # ← 每月只改这一行
    "window_years": 3,            # 滚动窗口长度（年），一般不动
}

# ── 1.2 模型超参数 ───────────────────────────────────────────
MODEL_CONFIG = {
    "lambda_":      2.5,
    "tau":          None,    # None = 自动用 1/T
    "weight_lower": 0.0,     # 全局默认下限（被单资产约束覆盖）
    "weight_upper": 1.0,     # 全局默认上限（被单资产约束覆盖）
}

# ── 1.3 报告配置 ────────────────────────────────────────────
REPORT_CONFIG = {
    # 增配/减配阈值：w* 相对 w_mkt 的变化比例超过该值即标记
    # 例：0.50 表示权重涨幅 ≥50% 为增配，跌幅 ≥50% 为减配
    "action_threshold": 0.50,
}

# ── 1.3 流动性配置 ──────────────────────────────────────────
# 流动性不进 BL，直接锁定，其余部分归一化后进 BL
LIQUIDITY_CONFIG = {
    "weight": 0.06,          # 流动性占总组合比例
    "name":   "流动性",
}

# ── 1.4 SAA 配置 ────────────────────────────────────────────
# 定义每个 SAA 分组的总权重
# 注意：这里的权重是扣除流动性之后的总组合占比
# 所有分组加总 = 1 - 流动性权重 = 0.94
SAA_CONFIG = {
    "固收":     0.898,   # 固收四个子类共享
    "权益-红利": 0.0175,  # 含权-红利独占
    "权益-港股": 0.0105,  # 含权-恒生科技独占
    "其他权益":  0.007,   # 含权-转债、含权-二级债基、含权-偏股混共享
    "另类-黄金": 0.007,   # 另类-黄金独占
}
# 验证：0.898+0.0175+0.0105+0.007+0.007 = 0.94 ✅

# ── 1.5 资产池配置 ──────────────────────────────────────────
# saa_group:    对应 SAA_CONFIG 的分组名
# asset_type:   fixed_income / equity / alternative
# duration_method: constant / wind（仅 fixed_income）
ASSET_CONFIG = {
    "固收-存单": {
        "index_code":      "H11155.CSI",
        "saa_group":       "固收",
        "asset_type":      "fixed_income",
        "duration_method": "constant",
        "duration_value":  1.0,
    },
    "固收-信用": {
        "index_code":      "CBA05641.CS",
        "saa_group":       "固收",
        "asset_type":      "fixed_income",
        "duration_method": "wind",
        "wind_code":       "CBA05641.CS",
    },
    "固收-利率10Y": {
        "index_code":      "H11006.CSI",
        "saa_group":       "固收",
        "asset_type":      "fixed_income",
        "duration_method": "wind",
        "wind_code":       "H11006.CSI",
    },
    "固收-利率30Y": {
        "index_code":      "H11008.CSI",
        "saa_group":       "固收",
        "asset_type":      "fixed_income",
        "duration_method": "wind",
        "wind_code":       "H11008.CSI",
    },
    "含权-转债": {
        "index_code":      "000832.CSI",
        "saa_group":       "其他权益",
        "asset_type":      "equity",
    },
    "含权-二级债基": {
        "index_code":      "885007.WI",
        "saa_group":       "其他权益",
        "asset_type":      "equity",
    },
    "含权-红利": {
        "index_code":      "000961.CSI",
        "saa_group":       "权益-红利",
        "asset_type":      "equity",
    },
    "含权-偏股混": {
        "index_code":      "885001.WI",
        "saa_group":       "其他权益",
        "asset_type":      "equity",
    },
    "含权-恒生科技": {
        "index_code":      "513310.SH",
        "saa_group":       "权益-港股",
        "asset_type":      "equity",
    },
    "另类-黄金": {
        "index_code":      "518880.SH",
        "saa_group":       "另类-黄金",
        "asset_type":      "alternative",
    },
}

# ── 1.6 单大类权重约束（层面B：总组合占比）──────────────────
# 控制 BL 最终输出 w* 里每个大类的总组合占比
# lower/upper 均为总组合的绝对权重
# 不填则使用 MODEL_CONFIG 里的全局默认值
# [可替换] 后续需要调整直接改这里，不用动任何函数
WEIGHT_CONSTRAINTS = {
    "固收-存单":     {"lower": 0.00, "upper": 0.50},
    "固收-信用":     {"lower": 0.00, "upper": 0.40},
    "固收-利率10Y":  {"lower": 0.00, "upper": 0.35},
    "固收-利率30Y":  {"lower": 0.00, "upper": 0.20},
    "含权-转债":     {"lower": 0.00, "upper": 0.10},
    "含权-二级债基": {"lower": 0.00, "upper": 0.10},
    "含权-红利":     {"lower": 0.00, "upper": 0.05},
    "含权-偏股混":   {"lower": 0.00, "upper": 0.05},
    "含权-恒生科技": {"lower": 0.00, "upper": 0.05},
    "另类-黄金":     {"lower": 0.00, "upper": 0.03},
}

# ── 1.7 观点幅度配置 ─────────────────────────────────────────
SCORE_RANGE_CONFIG = {
    "固收-存单": {
        1: (+0.0015, +0.0015),
        2: (+0.0005, +0.0015),
        3: (-0.0005, +0.0005),
        4: (-0.0015, -0.0005),
        5: (-0.0015, -0.0015),
    },
    "固收-信用": {
        1: (+0.0020, +0.0020),
        2: (+0.0005, +0.0020),
        3: (-0.0005, +0.0005),
        4: (-0.0020, -0.0005),
        5: (-0.0020, -0.0020),
    },
    "固收-利率10Y": {
        1: (+0.0015, +0.0015),
        2: (+0.0005, +0.0015),
        3: (-0.0005, +0.0005),
        4: (-0.0015, -0.0005),
        5: (-0.0015, -0.0015),
    },
    "固收-利率30Y": {
        1: (+0.0020, +0.0020),
        2: (+0.0005, +0.0020),
        3: (-0.0005, +0.0005),
        4: (-0.0020, -0.0005),
        5: (-0.0020, -0.0020),
    },
    "含权-转债": {
        1: (-0.10, -0.10),
        2: (-0.10, -0.03),
        3: (-0.03, +0.03),
        4: (+0.03, +0.10),
        5: (+0.10, +0.10),
    },
    "含权-二级债基": {
        1: (-0.05, -0.05),
        2: (-0.05, -0.02),
        3: (-0.02, +0.02),
        4: (+0.02, +0.05),
        5: (+0.05, +0.05),
    },
    "含权-红利": {
        1: (-0.10, -0.10),
        2: (-0.10, -0.03),
        3: (-0.03, +0.03),
        4: (+0.03, +0.10),
        5: (+0.10, +0.10),
    },
    "含权-偏股混": {
        1: (-0.10, -0.10),
        2: (-0.10, -0.03),
        3: (-0.03, +0.03),
        4: (+0.03, +0.10),
        5: (+0.10, +0.10),
    },
    "含权-恒生科技": {
        1: (-0.10, -0.10),
        2: (-0.10, -0.03),
        3: (-0.03, +0.03),
        4: (+0.03, +0.10),
        5: (+0.10, +0.10),
    },
    "另类-黄金": {
        1: (-0.10, -0.10),
        2: (-0.10, -0.03),
        3: (-0.03, +0.03),
        4: (+0.03, +0.10),
        5: (+0.10, +0.10),
    },
}

# ── 1.8 本次投委会投票 ───────────────────────────────────────
VOTES_CONFIG = {
    "固收-存单":     {2: 8, 4: 1},
    "固收-信用":     {3: 6, 4: 3},
    "固收-利率10Y":  {3: 8, 4: 1},
    "固收-利率30Y":  {3: 7, 4: 2, 5: 1},
    "含权-转债":     {2: 1, 3: 5, 4: 3},
    "含权-二级债基": {3: 8, 4: 2},
    "含权-红利":     {3: 6, 4: 4},
    "含权-偏股混":   {2: 1, 3: 5, 4: 3},
    # "含权-恒生科技": {2: 2, 3: 2, 4: 6},   # 本期无投票，依赖先验
    "另类-黄金":     {3: 2, 4: 8},
}


# ═══════════════════════════════════════════════════════════
#  SECTION 1.9：日期推算函数
# ═══════════════════════════════════════════════════════════

def resolve_dates(date_config: dict) -> tuple:
    """
    根据 meeting_date 和 window_years 自动推算 hist_start / hist_end。

    规则：
      hist_end   = meeting_date（开会当天，数据截止到前一天收盘）
      hist_start = meeting_date 往前推 window_years 年

    返回：hist_start, hist_end（字符串，格式 YYYYMMDD）

    示例：
      meeting_date = "20250507", window_years = 3
      → hist_start = "20220507"
      → hist_end   = "20250507"
    """
    meeting = datetime.strptime(date_config["meeting_date"], "%Y%m%d")
    hist_end   = meeting
    hist_start = meeting - relativedelta(years=date_config["window_years"])
    return hist_start.strftime("%Y%m%d"), hist_end.strftime("%Y%m%d")


# ═══════════════════════════════════════════════════════════
#  SECTION 2：数据获取函数
# ═══════════════════════════════════════════════════════════

# [可替换] 替换为 Tushare/Wind 真实拉取
def fetch_price_data(asset_config: dict,
                     hist_start: str,
                     hist_end: str) -> pd.DataFrame:
    """
    拉取各资产历史收盘价。
    返回 DataFrame，index=日期，columns=资产名称。

    [可替换]
    当前：模拟数据
    替换为：
        pro = ts.pro_api(token)
        df  = pro.index_daily(ts_code=code,
                              start_date=hist_start,
                              end_date=hist_end)
    """
    print("[数据] 拉取历史价格（当前为模拟数据）...")
    np.random.seed(42)
    dates = pd.bdate_range(hist_start, hist_end)
    n     = len(dates)

    sim_params = {
        "固收-存单":     {"mu": 0.023, "vol": 0.008},
        "固收-信用":     {"mu": 0.031, "vol": 0.016},
        "固收-利率10Y":  {"mu": 0.042, "vol": 0.031},
        "固收-利率30Y":  {"mu": 0.052, "vol": 0.049},
        "含权-转债":     {"mu": 0.061, "vol": 0.063},
        "含权-二级债基": {"mu": 0.058, "vol": 0.052},
        "含权-红利":     {"mu": 0.082, "vol": 0.182},
        "含权-偏股混":   {"mu": 0.093, "vol": 0.213},
        "含权-恒生科技": {"mu": 0.112, "vol": 0.301},
        "另类-黄金":     {"mu": 0.152, "vol": 0.152},
    }

    prices = {}
    for name in asset_config.keys():
        p         = sim_params[name]
        daily_mu  = p["mu"]  / 252
        daily_vol = p["vol"] / np.sqrt(252)
        shocks    = np.random.normal(daily_mu, daily_vol, n)
        prices[name] = 100 * np.cumprod(1 + shocks)

    df = pd.DataFrame(prices, index=dates)
    print(f"  → {len(df)} 个交易日，{len(df.columns)} 个资产")
    return df


# [可替换] 替换为 Wind 实时拉取
def fetch_durations(asset_config: dict,
                    meeting_date: str) -> dict:
    """
    获取固收资产的修正久期。

    [可替换]
    duration_method == "wind" 时替换为：
        import WindPy as w
        w.start()
        data = w.wsd(wind_code, "modifiedDuration",
                     meeting_date, meeting_date)
        duration = data.Data[0][0]
    """
    print("[数据] 拉取修正久期...")

    simulated = {
        "固收-信用":    2.76,
        "固收-利率10Y": 8.73,
        "固收-利率30Y": 16.82,
    }

    durations = {}
    for name, cfg in asset_config.items():
        if cfg["asset_type"] != "fixed_income":
            continue
        if cfg["duration_method"] == "constant":
            durations[name] = cfg["duration_value"]
            print(f"  {name}: {cfg['duration_value']:.2f}年（配置固定值）")
        elif cfg["duration_method"] == "wind":
            d = simulated.get(name, 3.0)
            durations[name] = d
            print(f"  {name}: {d:.2f}年（模拟，请替换为Wind调用）")

    return durations


# [可替换] 替换为 Wind 实时拉取 YTM + 历史收益率均值
def fetch_expected_returns(asset_config: dict,
                           prices_df: pd.DataFrame) -> dict:
    """
    计算各资产预期年化收益率：
      - 固收类（fixed_income）：使用当前 YTM（到期收益率）
      - 其他类：使用 prices_df 覆盖窗口（3年）的历史收益率年化均值

    返回：dict {资产名: 预期年化收益率（小数）}

    [可替换]
    固收 YTM 替换为：
        import WindPy as w
        w.start()
        data = w.wss(wind_code, "ytm", f"tradeDate={meeting_date}")
        ytm = data.Data[0][0] / 100   # Wind 返回百分比
    """
    print("[数据] 计算预期年化收益率...")

    # ── Mock YTM（固收，后续替换为 Wind 实时数据）
    mock_ytm = {
        "固收-存单":    0.018,   # 1年期存单 ~1.8%
        "固收-信用":    0.025,   # 信用债 ~2.5%
        "固收-利率10Y": 0.022,   # 10年国债 ~2.2%
        "固收-利率30Y": 0.024,   # 30年国债 ~2.4%
    }

    # ── 历史收益率均值（含权/另类，基于 prices_df 窗口）
    returns   = prices_df.pct_change().dropna()
    mu_hist   = (returns.mean() * 252).to_dict()   # 年化均值

    exp_ret = {}
    for name, cfg in asset_config.items():
        if cfg["asset_type"] == "fixed_income":
            ytm = mock_ytm.get(name, 0.02)
            exp_ret[name] = ytm
            print(f"  {name:<15} YTM  = {ytm*100:.2f}%（mock，请替换为Wind）")
        else:
            mu = mu_hist.get(name, 0.05)
            exp_ret[name] = mu
            print(f"  {name:<15} 均值 = {mu*100:.2f}%（{len(returns)}个交易日均值）")

    return exp_ret


# ═══════════════════════════════════════════════════════════
#  SECTION 3：核心计算函数
# ═══════════════════════════════════════════════════════════

def calc_covariance(prices_df: pd.DataFrame) -> tuple:
    """
    Ledoit-Wolf 收缩估计年化协方差矩阵 Σ。

    返回：Sigma, mu_hist, T

    [可替换] 替换为样本协方差、EWMA 等
    """
    print("\n[Step 1] 计算协方差矩阵 Σ（Ledoit-Wolf）")
    returns = prices_df.pct_change().dropna()
    T       = len(returns)

    lw      = LedoitWolf().fit(returns)
    Sigma   = lw.covariance_ * 252
    mu_hist = returns.mean() * 252

    print(f"  样本数量 T = {T} 个交易日")
    print("  年化波动率：")
    for name, vol in zip(returns.columns, np.sqrt(np.diag(Sigma))):
        print(f"    {name}: {vol*100:.2f}%")

    return Sigma, mu_hist, T


def calc_risk_parity_weights(Sigma: np.ndarray,
                             names: list,
                             group_name: str) -> np.ndarray:
    """
    给定子类的协方差矩阵，求风险平价权重（带相关性）。

    目标：最小化各子类风险贡献的方差
    约束：权重加总为1，各权重 > 0

    返回：子类内部权重向量（加总为1）
    """
    n = len(names)
    if n == 1:
        return np.array([1.0])

    def risk_contributions(w):
        port_vol = np.sqrt(w @ Sigma @ w)
        mrc      = Sigma @ w / port_vol   # 边际风险贡献
        rc       = w * mrc                # 风险贡献
        return rc

    def objective(w):
        rc = risk_contributions(w)
        return np.sum((rc - rc.mean()) ** 2)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds      = [(0.001, 0.999)] * n
    w0          = np.ones(n) / n

    result = minimize(
        objective, w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000}
    )

    w_rp = result.x

    # 打印风险贡献验证
    rc       = risk_contributions(w_rp)
    port_vol = np.sqrt(w_rp @ Sigma @ w_rp)
    print(f"\n  [{group_name}] 风险平价结果（带相关性）：")
    print(f"  {'子类':<15} {'内部权重':>8} {'风险贡献':>10} {'占组合波动%':>12}")
    print(f"  {'-'*48}")
    for name, w, r in zip(names, w_rp, rc):
        print(f"  {name:<15} {w*100:>7.1f}%  {r*100:>9.3f}%  {r/port_vol*100:>10.1f}%")

    return w_rp


def calc_market_weights(asset_config: dict,
                        saa_config: dict,
                        Sigma: np.ndarray,
                        liquidity_weight: float) -> np.ndarray:
    """
    计算 w_mkt：SAA 大类约束 + 大类内部风险平价（带相关性）。

    流程：
      1. 按 saa_group 把资产分组
      2. 单资产分组：直接用 SAA 权重
      3. 多资产分组：从 Σ 取子矩阵，跑风险平价，乘以 SAA 权重
      4. 所有权重加总 = 1 - liquidity_weight

    [可替换]
    替换为实际持仓权重或其他方法：
    只需替换这一个函数，其他步骤不受影响
    """
    print("\n[Step 2] 计算市场权重 w_mkt（SAA + 风险平价）")

    names     = list(asset_config.keys())
    N         = len(names)
    w_mkt     = np.zeros(N)

    # 按 saa_group 分组
    groups = {}
    for i, (name, cfg) in enumerate(asset_config.items()):
        g = cfg["saa_group"]
        if g not in groups:
            groups[g] = []
        groups[g].append((i, name))

    # 逐组计算
    for group_name, members in groups.items():
        saa_w    = saa_config[group_name]
        indices  = [m[0] for m in members]
        memnames = [m[1] for m in members]

        if len(members) == 1:
            # 单资产：直接用 SAA 权重
            w_mkt[indices[0]] = saa_w
            print(f"\n  [{group_name}] 单资产，直接用 SAA 权重")
            print(f"  {memnames[0]}: {saa_w*100:.3f}%")
        else:
            # 多资产：风险平价
            Sigma_sub = Sigma[np.ix_(indices, indices)]
            w_rp      = calc_risk_parity_weights(
                Sigma_sub, memnames, group_name
            )
            for idx, w in zip(indices, w_rp):
                w_mkt[idx] = saa_w * w

            print(f"  → 总组合权重：", end="")
            for name, w in zip(memnames, w_rp):
                print(f"{name} {saa_w*w*100:.2f}%  ", end="")
            print()

    print(f"\n  w_mkt 汇总（BL 优化范围，合计={w_mkt.sum()*100:.1f}%）：")
    print(f"  {'大类':<15} {'w_mkt':>8}")
    print(f"  {'-'*26}")
    for name, w in zip(names, w_mkt):
        print(f"  {name:<15} {w*100:.3f}%")
    print(f"\n  流动性（不进BL）: {liquidity_weight*100:.1f}%")
    print(f"  合计: {(w_mkt.sum() + liquidity_weight)*100:.1f}%")

    return w_mkt


def calc_equilibrium(Sigma: np.ndarray,
                     w_mkt: np.ndarray,
                     lambda_: float,
                     asset_config: dict) -> np.ndarray:
    """
    计算均衡隐含收益 Π = λ · Σ · w_mkt

    [可替换] 加入无风险利率调整等
    """
    print("\n[Step 3] 计算均衡隐含收益 Π = λ · Σ · w_mkt")
    Pi    = lambda_ * Sigma @ w_mkt
    names = list(asset_config.keys())
    print(f"  {'大类':<15} {'Π':>8}")
    print(f"  {'-'*26}")
    for name, pi in zip(names, Pi):
        print(f"  {name:<15} {pi*100:>7.2f}%")
    return Pi


def calc_Q_and_Omega(asset_config: dict,
                     score_range_config: dict,
                     votes_config: dict,
                     durations: dict,
                     Sigma: np.ndarray,
                     tau: float) -> tuple:
    """
    投委会投票 → P / Q / Ω

    固收类：加权平均利率变动 × (-久期) → 价格收益率
    含权/另类：加权平均价格涨跌幅

    Ω = He-Litterman 基础值 × 委员分歧调整

    [可替换]
    Q：当前用区间中点加权平均，可换众数、中位数
    Ω：可换纯主观填写
    """
    print("\n[Step 4] 投委会投票 → P / Q / Ω")

    names        = list(asset_config.keys())
    N            = len(names)
    P_rows       = []   # 只包含有投票的资产行
    Q_list       = []
    std_list     = []
    voted_indices = []

    for i, name in enumerate(names):
        cfg       = asset_config[name]
        vote_dict = votes_config.get(name, {})

        if not vote_dict:
            print(f"  {name}: 无投票，完全依赖先验")
            continue

        ranges      = score_range_config[name]
        total_votes = sum(vote_dict.values())

        raw_values   = []
        weighted_sum = 0.0
        for score, count in vote_dict.items():
            lo, hi = ranges[score]
            mid    = (lo + hi) / 2
            weighted_sum += mid * count
            raw_values.extend([mid] * count)
        avg_raw = weighted_sum / total_votes

        if cfg["asset_type"] == "fixed_income":
            duration = durations[name]
            Q_val    = -duration * avg_raw
            ret_arr  = np.array([-duration * v for v in raw_values])
            print(f"  {name}")
            print(f"    投票: {vote_dict}（{total_votes}票）"
                  f"  加权利率变动: {avg_raw*10000:.1f}bp"
                  f"  久期: {duration:.2f}年"
                  f"  Q = {Q_val*100:.3f}%")
        else:
            Q_val   = avg_raw
            ret_arr = np.array(raw_values)
            print(f"  {name}")
            print(f"    投票: {vote_dict}（{total_votes}票）"
                  f"  Q = {Q_val*100:.3f}%")

        std_val = np.std(ret_arr)
        print(f"    委员分歧std = {std_val:.4f}")

        p_row = np.zeros(N)
        p_row[i] = 1.0
        P_rows.append(p_row)
        Q_list.append(Q_val)
        std_list.append(std_val)
        voted_indices.append(i)

    P       = np.array(P_rows)          # shape: (K, N)，K = 有投票资产数
    Q_vec   = np.array(Q_list)
    std_arr = np.array(std_list)

    # Ω：He-Litterman 基础 × 分歧调整
    Omega_base        = tau * np.diag(P @ Sigma @ P.T)
    disagreement_scale= 1 + std_arr / (np.abs(Q_vec) + 1e-6)
    Omega             = np.diag(Omega_base * disagreement_scale)

    print(f"\n  Ω 对角线（越大=越不信任）：")
    for idx, om in zip(voted_indices, np.diag(Omega)):
        print(f"    {names[idx]}: {om:.6f}")

    return P, Q_vec, Omega


def calc_mu_BL(Pi: np.ndarray,
               P: np.ndarray,
               Q: np.ndarray,
               Omega: np.ndarray,
               Sigma: np.ndarray,
               tau: float,
               asset_config: dict) -> tuple:
    """
    贝叶斯混合：Π（均衡先验）+ Q（投委会观点）→ μ_BL

    公式：
      M      = (τΣ)⁻¹ + P'Ω⁻¹P
      μ_BL   = M⁻¹ · [(τΣ)⁻¹Π + P'Ω⁻¹Q]
      Σ_BL   = Σ + M⁻¹

    [可替换] 标准 He-Litterman 贝叶斯公式
    """
    print("\n[Step 5] 贝叶斯混合 → μ_BL")

    prior_prec = np.linalg.inv(tau * Sigma)
    view_prec  = P.T @ np.linalg.inv(Omega) @ P
    M          = prior_prec + view_prec
    Sigma_BL   = np.linalg.inv(M)
    mu_BL      = Sigma_BL @ (
        prior_prec @ Pi + P.T @ np.linalg.inv(Omega) @ Q
    )

    names = list(asset_config.keys())
    N = len(names)
    # 建立 name -> Q 映射（P 只含有投票资产的行）
    q_map = {}
    for k in range(len(Q)):
        asset_idx = int(np.argmax(P[k]))
        q_map[names[asset_idx]] = Q[k]

    print(f"\n  {'大类':<15} {'均衡Π':>9} {'观点Q':>9} {'后验μ_BL':>10}")
    print(f"  {'-'*46}")
    for i, name in enumerate(names):
        q_display = q_map[name] * 100 if name in q_map else float('nan')
        q_str = f"{q_display:>8.2f}%" if name in q_map else f"{'先验':>9}"
        print(f"  {name:<15} "
              f"{Pi[i]*100:>8.2f}%  "
              f"{q_str}  "
              f"{mu_BL[i]*100:>8.2f}%")

    return mu_BL, Sigma_BL


def optimize_portfolio(mu_BL: np.ndarray,
                       Sigma: np.ndarray,
                       lambda_: float,
                       asset_config: dict,
                       weight_constraints: dict,
                       model_config: dict,
                       liquidity_weight: float = 0.0) -> np.ndarray:
    """
    均值方差优化，求最优权重 w*。

    目标：max  w'μ_BL - (λ/2) · w'Σw
    约束：Σwᵢ = 1 - liquidity_weight（BL 可优化的总量）
    边界：每个资产使用 WEIGHT_CONSTRAINTS 里的个性化约束
          未配置的资产使用 MODEL_CONFIG 的全局默认值

    [可替换]
    当前：scipy SLSQP
    替换为：cvxpy（支持更复杂约束、换手率限制等）
    """
    print("\n[Step 6] 均值方差优化 → w*")

    names  = list(asset_config.keys())
    N      = len(names)

    # 构建每个资产的边界
    bounds = []
    for name in names:
        if name in weight_constraints:
            lo = weight_constraints[name].get(
                "lower", model_config["weight_lower"]
            )
            hi = weight_constraints[name].get(
                "upper", model_config["weight_upper"]
            )
        else:
            lo = model_config["weight_lower"]
            hi = model_config["weight_upper"]
        bounds.append((lo, hi))

    def neg_utility(w):
        ret  = w @ mu_BL
        risk = w @ Sigma @ w
        return -(ret - (lambda_ / 2) * risk)

    # 权重加总 = 1 - 流动性，即 BL 可优化的总量
    bl_total    = 1.0 - liquidity_weight
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - bl_total}]
    w0          = np.ones(N) / N * bl_total

    result = minimize(
        neg_utility, w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000}
    )

    if not result.success:
        print(f"  [警告] 优化未完全收敛：{result.message}")

    return result.x


# ═══════════════════════════════════════════════════════════
#  SECTION 4：输出函数
# ═══════════════════════════════════════════════════════════

def print_results(w_star: np.ndarray,
                  w_mkt: np.ndarray,
                  mu_BL: np.ndarray,
                  Sigma: np.ndarray,
                  asset_config: dict,
                  liquidity_config: dict) -> pd.DataFrame:
    """
    打印最终结果，返回结果 DataFrame。
    包含流动性行，总组合加总为100%。
    """
    names    = list(asset_config.keys())
    port_ret = w_star @ mu_BL
    port_vol = np.sqrt(w_star @ Sigma @ w_star)
    sharpe   = port_ret / port_vol

    print("\n" + "═" * 66)
    print("  BL 最终结果（含流动性）")
    print("═" * 66)
    print(f"  {'大类':<15} {'w_mkt':>8} {'w*':>8} {'变动':>8} {'方向':>4}")
    print(f"  {'-'*52}")

    rows = []
    for i, name in enumerate(names):
        delta = w_star[i] - w_mkt[i]
        arrow = "↑" if delta > 0.002 else ("↓" if delta < -0.002 else "→")
        print(f"  {name:<15} "
              f"{w_mkt[i]*100:>7.3f}%  "
              f"{w_star[i]*100:>7.3f}%  "
              f"{delta*100:>+7.3f}%  {arrow}")
        rows.append({
            "大类":    name,
            "w_mkt":  round(w_mkt[i], 5),
            "w_star": round(w_star[i], 5),
            "delta":  round(delta, 5),
            "mu_BL":  round(mu_BL[i], 5),
        })

    # 流动性行
    liq_w = liquidity_config["weight"]
    liq_n = liquidity_config["name"]
    print(f"  {liq_n:<15} {liq_w*100:>7.1f}%  {liq_w*100:>7.1f}%  {'0.000%':>8}  →")
    rows.append({
        "大类":    liq_n,
        "w_mkt":  liq_w,
        "w_star": liq_w,
        "delta":  0.0,
        "mu_BL":  None,
    })

    grand_total = w_star.sum() + liq_w
    print(f"  {'-'*52}")
    print(f"  {'合计':<15} {'100.0%':>8}  {grand_total*100:>5.1f}%")
    print(f"\n  组合预期年化收益（不含流动性）：{port_ret*100:.2f}%")
    print(f"  组合预期年化波动（不含流动性）：{port_vol*100:.2f}%")
    print(f"  组合夏普比率：                  {sharpe:.3f}")
    print("═" * 66)

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════
#  SECTION 5：主流程
# ═══════════════════════════════════════════════════════════

def run_bl_model(
    asset_config       = ASSET_CONFIG,
    saa_config         = SAA_CONFIG,
    score_range_config = SCORE_RANGE_CONFIG,
    votes_config       = VOTES_CONFIG,
    date_config        = DATE_CONFIG,
    model_config       = MODEL_CONFIG,
    weight_constraints = WEIGHT_CONSTRAINTS,
    liquidity_config   = LIQUIDITY_CONFIG,
) -> pd.DataFrame:
    """
    BL 模型主流程。

    每月使用：
      1. 修改 DATE_CONFIG["meeting_date"] 为开会日期
      2. 修改 VOTES_CONFIG 为本次投票结果
      3. 直接运行，其他配置不动

    所有参数来自配置，方便外部替换单个模块。
    返回结果 DataFrame。
    """
    # ── 自动推算历史数据窗口
    hist_start, hist_end = resolve_dates(date_config)

    print("═" * 66)
    print("  Black-Litterman 资产配置模型 v3")
    print(f"  投委会日期：{date_config['meeting_date']}")
    print(f"  历史窗口：  {hist_start} ～ {hist_end}"
          f"（滚动 {date_config['window_years']} 年）")
    print(f"  lambda = {model_config['lambda_']}")
    print(f"  流动性 = {liquidity_config['weight']*100:.0f}%（锁定，不进BL）")
    print("═" * 66)

    lambda_ = model_config["lambda_"]

    # ── 数据获取
    prices_df = fetch_price_data(
        asset_config,
        hist_start,
        hist_end
    )
    durations = fetch_durations(asset_config, date_config["meeting_date"])

    # ── Step 1：协方差矩阵
    Sigma, mu_hist, T = calc_covariance(prices_df)

    # ── 预期年化收益率（固收用YTM，其他用历史均值）
    exp_ret = fetch_expected_returns(asset_config, prices_df)
    tau = model_config["tau"] if model_config["tau"] is not None else (1.0 / T)
    print(f"\n  tau = {tau:.6f}（{'配置值' if model_config['tau'] else '自动 1/T'}）")

    # ── Step 2：w_mkt（SAA + 风险平价）
    w_mkt = calc_market_weights(
        asset_config,
        saa_config,
        Sigma,
        liquidity_config["weight"]
    )

    # ── Step 3：均衡先验 Π
    Pi = calc_equilibrium(Sigma, w_mkt, lambda_, asset_config)

    # ── Step 4：观点 P / Q / Ω
    P, Q, Omega = calc_Q_and_Omega(
        asset_config, score_range_config, votes_config,
        durations, Sigma, tau
    )

    # ── Step 5：贝叶斯混合
    mu_BL, Sigma_BL = calc_mu_BL(Pi, P, Q, Omega, Sigma, tau, asset_config)

    # ── Step 6：优化
    w_star = optimize_portfolio(
        mu_BL, Sigma, lambda_,
        asset_config, weight_constraints, model_config,
        liquidity_weight=liquidity_config["weight"]
    )

    # ── 输出
    result_df = print_results(
        w_star, w_mkt, mu_BL, Sigma,
        asset_config, liquidity_config
    )

    # ── 生成 HTML 报告
    try:
        from model_center.report_generator import generate_report
    except ImportError:
        from report_generator import generate_report

    port_ret = float(w_star @ mu_BL)
    port_vol = float(np.sqrt(w_star @ Sigma @ w_star))
    # 无风险利率：固收-存单当前 YTM（mock，后续替换为 Wind 实时取值）
    rf       = 0.018   # [可替换] Wind: w.wsd("H11155.CSI", "ytm", meeting_date, meeting_date)
    sharpe   = (port_ret - rf) / port_vol

    # ── 最大回撤（基于历史窗口内的组合收益率序列，从1累乘得净值）
    names_list_dd = list(asset_config.keys())
    port_returns  = prices_df[names_list_dd].pct_change().dropna() @ w_star
    port_nav      = (1 + port_returns).cumprod()
    rolling_max   = port_nav.cummax()
    drawdowns     = port_nav / rolling_max - 1
    max_drawdown  = float(drawdowns.min())

    # ── 基于 exp_ret 的组合预期收益（固收用YTM，其他用历史均值）
    names_list    = list(asset_config.keys())
    exp_ret_vec   = np.array([exp_ret[n] for n in names_list])
    exp_port_ret  = float(w_star @ exp_ret_vec)
    exp_port_vol  = port_vol   # 波动率用同一个 Sigma 计算
    exp_port_sharpe = (exp_port_ret - rf) / exp_port_vol

    report_data = {
        "meeting_date":        date_config["meeting_date"],
        "hist_start":          hist_start,
        "hist_end":            hist_end,
        "names":               list(asset_config.keys()),
        "asset_config":        asset_config,
        "w_mkt":               w_mkt.tolist(),
        "Pi":                  Pi.tolist(),
        "Q":                   Q.tolist(),
        "P":                   P.tolist(),
        "mu_BL":               mu_BL.tolist(),
        "w_star":              w_star.tolist(),
        "votes_config":        votes_config,
        "dynamic_constraints": weight_constraints,
        "group_constraints":   {},
        "port_ret":            port_ret,
        "port_vol":            port_vol,
        "sharpe":              sharpe,
        "Omega":               Omega,
        "liquidity_config":    liquidity_config,
        "score_range_config":  SCORE_RANGE_CONFIG,
        "durations":           durations,
        "exp_ret":             exp_ret,
        "rf":                  rf,
        "exp_port_ret":        exp_port_ret,
        "exp_port_vol":        exp_port_vol,
        "exp_port_sharpe":     exp_port_sharpe,
        "max_drawdown":        max_drawdown,
        "report_config":       REPORT_CONFIG,
        "fixed_income_band":   0.3,
    }

    import os
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    generate_report(report_data, output_dir=report_dir)

    return result_df


# ═══════════════════════════════════════════════════════════
#  SECTION 6：入口
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    result = run_bl_model()
    print("\n结果 DataFrame：")
    print(result.to_string(index=False))