import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize
from datetime import datetime
from dateutil.relativedelta import relativedelta
from config import *

class BlackLittermanModel():
    def __init__(self, meeting_date):
        self.date_config =  {"meeting_date": meeting_date,                       # ← 每月只改这一行
                             "window_years": DATE_CONFIG['window_years']         # 滚动窗口长度（年），一般不动
                            }
        self.asset_config = ASSET_CONFIG
        self.score_range_config = SCORE_RANGE_CONFIG
        self.votes_config = VOTES_CONFIG
        self.model_config = MODEL_CONFIG
        self.saa_config = SAA_CONFIG
        self.weight_constraints = WEIGHT_CONSTRAINTS
        self.group_constraints = GROUP_CONSTRAINTS
        self.liquidity_config = LIQUIDITY_CONFIG

        self.lambda_ = self.model_config["lambda_"]


    def resolve_dates(self, date_config):
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
        hist_end = meeting
        hist_start = meeting - relativedelta(years=date_config["window_years"])
        return hist_start.strftime("%Y%m%d"), hist_end.strftime("%Y%m%d")


    def fetch_price_data(self, asset_config, hist_start, hist_end):
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
        n = len(dates)

        # sim_params = {
        #     "固收-存单": {"mu": 0.023, "vol": 0.008},
        #     "固收-信用": {"mu": 0.031, "vol": 0.016},
        #     "固收-利率10Y": {"mu": 0.042, "vol": 0.031},
        #     "固收-利率30Y": {"mu": 0.052, "vol": 0.049},
        #     "含权-转债": {"mu": 0.061, "vol": 0.063},
        #     "含权-二级债基": {"mu": 0.058, "vol": 0.052},
        #     "含权-红利": {"mu": 0.082, "vol": 0.182},
        #     "含权-偏股混": {"mu": 0.093, "vol": 0.213},
        #     "含权-恒生科技": {"mu": 0.112, "vol": 0.301},
        #     "另类-黄金": {"mu": 0.152, "vol": 0.152},
        # }


        sim_params = {
            "固收-存单": {"mu": 0.031, "vol": 0.016},
            "固收-信用": {"mu": 0.031, "vol": 0.016},
            "固收-利率10Y": {"mu": 0.042, "vol": 0.031},
            "固收-利率30Y": {"mu": 0.052, "vol": 0.049},
            "含权-转债": {"mu": 0.061, "vol": 0.063},
            "含权-二级债基": {"mu": 0.058, "vol": 0.052},
            "含权-红利": {"mu": 0.082, "vol": 0.182},
            "含权-偏股混": {"mu": 0.093, "vol": 0.213},
            "含权-恒生科技": {"mu": 0.112, "vol": 0.301},
            "另类-黄金": {"mu": 0.152, "vol": 0.152},
        }


        prices = {}
        for name in asset_config.keys():
            p = sim_params[name]
            daily_mu = p["mu"] / 252
            daily_vol = p["vol"] / np.sqrt(252)
            shocks = np.random.normal(daily_mu, daily_vol, n)
            prices[name] = 100 * np.cumprod(1 + shocks)

        df = pd.DataFrame(prices, index=dates)
        print(f"  → {len(df)} 个交易日，{len(df.columns)} 个资产")
        return df

    # [可替换] 替换为 Wind 实时拉取
    def fetch_durations(self, asset_config: dict, meeting_date: str) -> dict:
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
            "固收-信用": 2.76,
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

    def calc_covariance(self, prices_df: pd.DataFrame, model_config) -> tuple:
        """
        Ledoit-Wolf 收缩估计年化协方差矩阵 Σ。

        返回：Sigma, mu_hist, T

        [可替换] 替换为样本协方差、EWMA 等
        """
        print("\n[Step 1] 计算协方差矩阵 Σ（Ledoit-Wolf）")
        returns = prices_df.pct_change().dropna()
        T = len(returns)

        lw = LedoitWolf().fit(returns)
        Sigma = lw.covariance_ * 252
        mu_hist = returns.mean() * 252
        tau = model_config["tau"] if model_config["tau"] is not None else (1.0 / T)

        print(f"  样本数量 T = {T} 个交易日")
        print("  年化波动率：")
        for name, vol in zip(returns.columns, np.sqrt(np.diag(Sigma))):
            print(f"    {name}: {vol * 100:.2f}%")
        print(f"\n  tau = {tau:.6f}（{'配置值' if model_config['tau'] else '自动 1/T'}）")

        return Sigma, mu_hist, T, tau

    def calc_risk_parity_weights(self,
                                 Sigma: np.ndarray,
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
            mrc = Sigma @ w / port_vol  # 边际风险贡献
            rc = w * mrc  # 风险贡献
            return rc

        def objective(w):
            rc = risk_contributions(w)
            return np.sum((rc - rc.mean()) ** 2)

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0.001, 0.999)] * n
        w0 = np.ones(n) / n

        result = minimize(
            objective, w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000}
        )

        w_rp = result.x

        # 打印风险贡献验证
        rc = risk_contributions(w_rp)
        port_vol = np.sqrt(w_rp @ Sigma @ w_rp)
        print(f"\n  [{group_name}] 风险平价结果（带相关性）：")
        print(f"  {'子类':<15} {'内部权重':>8} {'风险贡献':>10} {'占组合波动%':>12}")
        print(f"  {'-' * 48}")
        for name, w, r in zip(names, w_rp, rc):
            print(f"  {name:<15} {w * 100:>7.1f}%  {r * 100:>9.3f}%  {r / port_vol * 100:>10.1f}%")

        return w_rp


    def calc_market_weights(self,
                            asset_config: dict,
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

        names = list(asset_config.keys())
        N = len(names)
        w_mkt = np.zeros(N)

        # 按 saa_group 分组
        groups = {}
        for i, (name, cfg) in enumerate(asset_config.items()):
            g = cfg["saa_group"]
            if g not in groups:
                groups[g] = []
            groups[g].append((i, name))

        # 逐组计算
        for group_name, members in groups.items():
            saa_w = saa_config[group_name]
            indices = [m[0] for m in members]
            memnames = [m[1] for m in members]

            if len(members) == 1:
                # 单资产：直接用 SAA 权重
                w_mkt[indices[0]] = saa_w
                print(f"\n  [{group_name}] 单资产，直接用 SAA 权重")
                print(f"  {memnames[0]}: {saa_w * 100:.3f}%")
            else:
                # 多资产：风险平价
                Sigma_sub = Sigma[np.ix_(indices, indices)]
                w_rp = self.calc_risk_parity_weights(Sigma_sub, memnames, group_name)
                for idx, w in zip(indices, w_rp):
                    w_mkt[idx] = saa_w * w

                print(f"  → 总组合权重：", end="")
                for name, w in zip(memnames, w_rp):
                    print(f"{name} {saa_w * w * 100:.2f}%  ", end="")
                print()

        print(f"\n  w_mkt 汇总（BL 优化范围，合计={w_mkt.sum() * 100:.1f}%）：")
        print(f"  {'大类':<15} {'w_mkt':>8}")
        print(f"  {'-' * 26}")
        for name, w in zip(names, w_mkt):
            print(f"  {name:<15} {w * 100:.3f}%")
        print(f"\n  流动性（不进BL）: {liquidity_weight * 100:.1f}%")
        print(f"  合计: {(w_mkt.sum() + liquidity_weight) * 100:.1f}%")

        return w_mkt

    def calc_equilibrium(self,
                         Sigma: np.ndarray,
                         w_mkt: np.ndarray,
                         lambda_: float,
                         asset_config: dict) -> np.ndarray:
        """
        计算均衡隐含收益 Π = λ · Σ · w_mkt

        [可替换] 加入无风险利率调整等
        """
        print("\n[Step 3] 计算均衡隐含收益 Π = λ · Σ · w_mkt")
        Pi = lambda_ * Sigma @ w_mkt
        names = list(asset_config.keys())
        print(f"  {'大类':<15} {'Π':>8}")
        print(f"  {'-' * 26}")
        for name, pi in zip(names, Pi):
            print(f"  {name:<15} {pi * 100:>7.2f}%")
        return Pi

    def calc_Q_and_Omega(self,
                         asset_config: dict,
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

        names = list(asset_config.keys())
        N = len(names)
        P = np.eye(N)
        Q_list = []
        std_list = []

        for name in names:
            cfg = asset_config[name]
            vote_dict = votes_config[name]
            ranges = score_range_config[name]
            total_votes = sum(vote_dict.values())

            # 加权平均原始变动值
            raw_values = []
            weighted_sum = 0.0
            for score, count in vote_dict.items():
                lo, hi = ranges[score]
                mid = (lo + hi) / 2
                weighted_sum += mid * count
                raw_values.extend([mid] * count)
            avg_raw = weighted_sum / total_votes

            # 固收：乘以久期转价格
            if cfg["asset_type"] == "fixed_income":
                duration = durations[name]
                Q_val = -duration * avg_raw
                ret_arr = np.array([-duration * v for v in raw_values])
                print(f"  {name}")
                print(f"    投票: {vote_dict}（{total_votes}票）"
                      f"  加权利率变动: {avg_raw * 10000:.1f}bp"
                      f"  久期: {duration:.2f}年"
                      f"  Q = {Q_val * 100:.3f}%")
            else:
                Q_val = avg_raw
                ret_arr = np.array(raw_values)
                print(f"  {name}")
                print(f"    投票: {vote_dict}（{total_votes}票）"
                      f"  Q = {Q_val * 100:.3f}%")

            std_val = np.std(ret_arr)
            print(f"    委员分歧std = {std_val:.4f}")
            Q_list.append(Q_val)
            std_list.append(std_val)

        Q_vec = np.array(Q_list)
        std_arr = np.array(std_list)

        # Ω：He-Litterman 基础 × 分歧调整
        Omega_base = tau * np.diag(P @ Sigma @ P.T)
        disagreement_scale = 1 + std_arr / (np.abs(Q_vec) + 1e-6)
        Omega = np.diag(Omega_base * disagreement_scale)

        print(f"\n  Ω 对角线（越大=越不信任）：")
        for name, om in zip(names, np.diag(Omega)):
            print(f"    {name}: {om:.6f}")

        return P, Q_vec, Omega

    def calc_mu_BL(self,
                   Pi: np.ndarray,
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
        view_prec = P.T @ np.linalg.inv(Omega) @ P
        M = prior_prec + view_prec
        Sigma_BL = np.linalg.inv(M)
        mu_BL = Sigma_BL @ (
                prior_prec @ Pi + P.T @ np.linalg.inv(Omega) @ Q
        )

        names = list(asset_config.keys())
        print(f"\n  {'大类':<15} {'均衡Π':>9} {'观点Q':>9} {'后验μ_BL':>10}")
        print(f"  {'-' * 46}")
        for i, name in enumerate(names):
            print(f"  {name:<15} "
                  f"{Pi[i] * 100:>8.2f}%  "
                  f"{Q[i] * 100:>8.2f}%  "
                  f"{mu_BL[i] * 100:>8.2f}%")

        return mu_BL, Sigma_BL

    def optimize_portfolio(self, mu_BL, Sigma, lambda_,
                           asset_config, weight_constraints,
                           model_config, liquidity_weight=0.0,
                           group_constraints=None):

        names = list(asset_config.keys())
        N = len(names)

        # 单资产边界（原有逻辑不变）
        bounds = []
        for name in names:
            if name in weight_constraints:
                lo = weight_constraints[name].get(
                    "lower", model_config["weight_lower"])
                hi = weight_constraints[name].get(
                    "upper", model_config["weight_upper"])
            else:
                lo = model_config["weight_lower"]
                hi = model_config["weight_upper"]
            bounds.append((lo, hi))

        bl_total = 1.0 - liquidity_weight
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - bl_total}
        ]

        # 组合约束：用 category 自动查找资产下标
        if group_constraints:
            for group_name, cfg in group_constraints.items():
                category = cfg.get("category")
                group_upper = cfg.get("upper", None)
                group_lower = cfg.get("lower", None)

                # 自动找到该 category 的所有资产下标
                group_idx = [
                    i for i, name in enumerate(names)
                    if asset_config[name].get("category") == category
                ]

                if not group_idx:
                    print(f"  [警告] category={category} 没有找到任何资产")
                    continue

                matched = [names[i] for i in group_idx]
                print(f"\n  [组合约束] {group_name}"
                      f"（category={category}）")
                print(f"  覆盖资产：{matched}")

                if group_upper is not None:
                    constraints.append({
                        "type": "ineq",
                        "fun": (lambda w, idx=group_idx, ub=group_upper:
                                ub - np.sum(w[idx]))
                    })
                    print(f"  加总上限：≤ {group_upper * 100:.0f}%")

                if group_lower is not None:
                    constraints.append({
                        "type": "ineq",
                        "fun": (lambda w, idx=group_idx, lb=group_lower:
                                np.sum(w[idx]) - lb)
                    })
                    print(f"  加总下限：≥ {group_lower * 100:.0f}%")

        def neg_utility(w):
            ret = w @ mu_BL
            risk = w @ Sigma @ w
            return -(ret - (lambda_ / 2) * risk)

        result = minimize(
            neg_utility,
            np.ones(N) / N * bl_total,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000}
        )

        if not result.success:
            print(f"  [警告] 优化未完全收敛：{result.message}")

        return result.x

    def print_results(self,
                      w_star: np.ndarray,
                      w_mkt: np.ndarray,
                      mu_BL: np.ndarray,
                      Sigma: np.ndarray,
                      asset_config: dict,
                      liquidity_config: dict) -> pd.DataFrame:
        """
        打印最终结果，返回结果 DataFrame。
        包含流动性行，总组合加总为100%。
        """
        names = list(asset_config.keys())
        port_ret = w_star @ mu_BL
        port_vol = np.sqrt(w_star @ Sigma @ w_star)
        sharpe = port_ret / port_vol

        print("\n" + "═" * 66)
        print("  BL 最终结果（含流动性）")
        print("═" * 66)
        print(f"  {'大类':<15} {'w_mkt':>8} {'w*':>8} {'变动':>8} {'方向':>4}")
        print(f"  {'-' * 52}")

        rows = []
        for i, name in enumerate(names):
            delta = w_star[i] - w_mkt[i]
            arrow = "↑" if delta > 0.002 else ("↓" if delta < -0.002 else "→")
            print(f"  {name:<15} "
                  f"{w_mkt[i] * 100:>7.3f}%  "
                  f"{w_star[i] * 100:>7.3f}%  "
                  f"{delta * 100:>+7.3f}%  {arrow}")
            rows.append({
                "大类": name,
                "w_mkt": round(w_mkt[i], 5),
                "w_star": round(w_star[i], 5),
                "delta": round(delta, 5),
                "mu_BL": round(mu_BL[i], 5),
            })

        # 流动性行
        liq_w = liquidity_config["weight"]
        liq_n = liquidity_config["name"]
        print(f"  {liq_n:<15} {liq_w * 100:>7.1f}%  {liq_w * 100:>7.1f}%  {'0.000%':>8}  →")
        rows.append({
            "大类": liq_n,
            "w_mkt": liq_w,
            "w_star": liq_w,
            "delta": 0.0,
            "mu_BL": None,
        })

        grand_total = w_star.sum() + liq_w
        print(f"  {'-' * 52}")
        print(f"  {'合计':<15} {'100.0%':>8}  {grand_total * 100:>5.1f}%")
        print(f"\n  组合预期年化收益（不含流动性）：{port_ret * 100:.2f}%")
        print(f"  组合预期年化波动（不含流动性）：{port_vol * 100:.2f}%")
        print(f"  组合夏普比率：                  {sharpe:.3f}")
        print("═" * 66)

        return pd.DataFrame(rows)


    def main(self):
        # ── 自动推算历史数据窗口
        hist_start, hist_end = self.resolve_dates(self.date_config)

        # ── 数据获取(日行情)
        prices_df = self.fetch_price_data(self.asset_config, hist_start, hist_end)

        # ── 数据获取(久期)
        durations = self.fetch_durations(self.asset_config, self.date_config["meeting_date"])

        # ── 模型计算(Step 1：协方差矩阵）
        Sigma, mu_hist, T, tau = self.calc_covariance(prices_df, self.model_config)

        # ── 模型计算(Step 2：w_mkt（SAA + 风险平价）)
        w_mkt = self.calc_market_weights(self.asset_config, self.saa_config, Sigma, self.liquidity_config["weight"])

        # ── 模型计算(Step 3：均衡先验 Π）
        Pi = self.calc_equilibrium(Sigma, w_mkt, self.lambda_, self.asset_config)

        # ── 模型计算(Step 4：观点 P / Q / Ω)
        P, Q, Omega = self.calc_Q_and_Omega(self.asset_config, self.score_range_config, self.votes_config, durations, Sigma, tau)

        # ── 模型计算(Step 5：贝叶斯混合)
        mu_BL, Sigma_BL = self.calc_mu_BL(Pi, P, Q, Omega, Sigma, tau, self.asset_config)

        # ── 模型计算(Step 6：优化)
        w_star = self.optimize_portfolio(mu_BL, Sigma, self.lambda_, self.asset_config, self.weight_constraints, self.model_config, liquidity_weight=self.liquidity_config["weight"], group_constraints=self.group_constraints)

        # ── 输出
        result_df = self.print_results(w_star, w_mkt, mu_BL, Sigma, self.asset_config, self.liquidity_config)



if __name__ == '__main__':
    meeting_date = "20260507"
    model = BlackLittermanModel(meeting_date)
    model.main()