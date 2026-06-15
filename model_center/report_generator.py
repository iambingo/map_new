import os
import numpy as np
from datetime import datetime


def _score_direction(q_val, asset_name, asset_type, score_range_config, durations):
    """根据观点收益判断方向标签（阈值来自 SCORE_RANGE_CONFIG 票型3区间）"""
    ranges = score_range_config.get(asset_name)
    if ranges and 3 in ranges:
        lo_raw, hi_raw = ranges[3]
        if asset_type == "fixed_income":
            # 利率变动转价格收益率：Q = -duration × Δrate；duration 来自 bl_claude.py 算好的 durations dict
            dur = durations.get(asset_name, 1.0)
            lo = -dur * hi_raw   # 注意符号：利率上行(正) → 价格下跌(负)
            hi = -dur * lo_raw
        else:
            lo, hi = lo_raw, hi_raw
    else:
        # 兜底阈值
        lo, hi = (-0.0005, 0.0005) if asset_type == "fixed_income" else (-0.01, 0.01)

    if q_val > hi:
        return "看多", "#e05252", "▲"
    elif q_val < lo:
        return "看空", "#3dba7e", "▼"
    else:
        return "中性", "#7a8caa", "—"


def _vote_bar_html(vote_dict):
    """生成投票分布色块"""
    total = sum(vote_dict.values())
    colors = {1: "#16a34a", 2: "#86efac", 3: "#d1d5db", 4: "#fca5a5", 5: "#dc2626"}
    labels = {1: "强烈谨慎", 2: "谨慎", 3: "中性", 4: "乐观", 5: "强烈乐观"}
    parts = []
    tooltip_parts = []
    for score in sorted(vote_dict.keys()):
        cnt = vote_dict[score]
        pct = cnt / total * 100
        label = labels.get(score, str(score))
        tooltip_parts.append(f"{label}({score}分): {cnt}票")
        parts.append(
            f'<span style="display:inline-block;width:{pct:.0f}%;height:10px;'
            f'background:{colors.get(score,"#ccc")};"></span>'
        )
    combined_tooltip = " | ".join(tooltip_parts)
    return f'<div title="{combined_tooltip}" style="display:flex;width:140px;border-radius:2px;overflow:hidden;cursor:default">{"".join(parts)}</div>'


def generate_report(report_data: dict, output_dir: str = "reports") -> str:
    os.makedirs(output_dir, exist_ok=True)

    meeting_date = report_data["meeting_date"]
    hist_start   = report_data["hist_start"]
    hist_end     = report_data["hist_end"]
    names        = report_data["names"]
    asset_config = report_data["asset_config"]
    w_mkt        = report_data["w_mkt"]
    Pi           = report_data["Pi"]
    Q            = report_data["Q"]
    mu_BL        = report_data["mu_BL"]
    w_star       = report_data["w_star"]
    votes_config = report_data["votes_config"]
    dynamic_constraints = report_data["dynamic_constraints"]
    group_constraints   = report_data.get("group_constraints", {})
    fixed_income_band   = report_data.get("fixed_income_band", 0.5)
    port_ret     = report_data["port_ret"]
    port_vol     = report_data["port_vol"]
    sharpe       = report_data["sharpe"]
    exp_ret      = report_data.get("exp_ret", {})
    rf           = report_data.get("rf", 0.018)
    exp_port_ret    = report_data.get("exp_port_ret") or port_ret
    exp_port_vol    = report_data.get("exp_port_vol") or port_vol
    exp_port_sharpe = report_data.get("exp_port_sharpe") or sharpe
    max_drawdown    = report_data.get("max_drawdown", 0.0)
    liquidity_config = report_data.get("liquidity_config", {"name": "流动性", "weight": 0.06})

    # 建立 name -> Q 映射（从 P 矩阵推导，无投票资产不在映射中）
    P = report_data.get("P")
    view_q_map = {}
    if P is not None and len(Q) > 0:
        P_arr = np.array(P)
        for k in range(len(Q)):
            asset_idx = int(np.argmax(P_arr[k]))
            view_q_map[names[asset_idx]] = float(Q[k])
    else:
        for i, name in enumerate(names):
            if i < len(Q):
                view_q_map[name] = float(Q[i])

    # ── 生成配置结论摘要
    bullish_assets = []
    bearish_assets = []
    neutral_assets = []
    big_increase = []   # 相对 w_mkt 增加 ≥50% 且绝对变动 ≥1%
    big_decrease = []   # 相对 w_mkt 减少 ≥50% 且绝对变动 ≥1%

    score_range_config = report_data.get("score_range_config", {})
    durations = report_data.get("durations", {})
    report_config = report_data.get("report_config", {})
    ACTION_THRESHOLD = report_config.get("action_threshold", 0.50)

    for i, name in enumerate(names):
        cfg = asset_config.get(name, {})
        asset_type = cfg.get("asset_type", "equity")
        q_val = view_q_map.get(name, 0.0)
        direction, _, _ = _score_direction(q_val, name, asset_type, score_range_config, durations)
        wm = float(w_mkt[i])
        ws = float(w_star[i])
        delta = ws - wm
        if direction == "看多":
            bullish_assets.append(name)
        elif direction == "看空":
            bearish_assets.append(name)
        else:
            neutral_assets.append(name)
        if wm > 0:
            rel_change = delta / wm
            if rel_change >= ACTION_THRESHOLD:
                big_increase.append(name)
            elif rel_change <= -ACTION_THRESHOLD:
                big_decrease.append(name)

    # 组装摘要 — 每种方向各占一行
    tag_lines = []
    if bullish_assets:
        tag_lines.append(f'<span class="sum-tag sum-tag-bull" style="white-space:nowrap;font-size:12px">🔺 看多 &nbsp;{"&nbsp;·&nbsp;".join(bullish_assets)}</span>')
    if neutral_assets:
        tag_lines.append(f'<span class="sum-tag sum-tag-neu" style="white-space:nowrap;font-size:12px">— 中性 &nbsp;{"&nbsp;·&nbsp;".join(neutral_assets)}</span>')
    if bearish_assets:
        tag_lines.append(f'<span class="sum-tag sum-tag-bear" style="white-space:nowrap;font-size:12px">🔻 审慎 &nbsp;{"&nbsp;·&nbsp;".join(bearish_assets)}</span>')
    tags_html = "&nbsp;&nbsp;".join(tag_lines)

    # 增配/减配 tag 行（资产名可点击，跳转并高亮权重表格对应行）
    def _clickable_assets(asset_list, color):
        links = []
        for n in asset_list:
            rid = f"wrow-{n.replace('-','_').replace(' ','_')}"
            links.append(
                f'<a href="javascript:void(0)" onclick="highlightRow(\'{rid}\')" '
                f'style="color:{color};text-decoration:underline dotted;cursor:pointer;font-size:13px">{n}</a>'
            )
        return "&nbsp;·&nbsp;".join(links)

    # 增配行：每个资产做成一个带箭头的小卡片
    def _action_card(asset_name, is_increase):
        rid = f"wrow-{asset_name.replace('-','_').replace(' ','_')}"
        if is_increase:
            bg      = "rgba(224,82,82,0.12)"
            border  = "rgba(224,82,82,0.5)"
            arrow   = "▲"
            label   = "增配"
            clr     = "#e05252"
            glow    = "rgba(224,82,82,0.15)"
        else:
            bg      = "rgba(61,186,126,0.12)"
            border  = "rgba(61,186,126,0.5)"
            arrow   = "▼"
            label   = "减配"
            clr     = "#3dba7e"
            glow    = "rgba(61,186,126,0.15)"
        return (
            f'<div onclick="highlightRow(\'{rid}\')" style="cursor:pointer;display:inline-flex;align-items:center;gap:6px;'
            f'background:{bg};border:1px solid {border};border-radius:8px;padding:6px 12px;'
            f'box-shadow:0 0 8px {glow};transition:opacity .15s" '
            f'onmouseover="this.style.opacity=.75" onmouseout="this.style.opacity=1">'
            f'<span style="font-size:15px;font-weight:800;color:{clr}">{arrow}</span>'
            f'<span style="font-size:12px;font-weight:700;color:{clr}">{label}</span>'
            f'<span style="width:1px;height:14px;background:{border};margin:0 2px"></span>'
            f'<span style="font-size:12px;color:#c8d8f0">{asset_name}</span>'
            f'</div>'
        )

    action_cards = []
    for n in big_increase:
        action_cards.append(_action_card(n, True))
    for n in big_decrease:
        action_cards.append(_action_card(n, False))

    if action_cards:
        cards_html = f'<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">{"".join(action_cards)}</div>'
        hint_html  = '<div style="margin-top:6px;font-size:11px;color:#4a607c">↑ 点击资产名可跳转至权重明细</div>'
        action_html = cards_html
    else:
        action_html = '<span style="color:#5a7090;font-size:12px">本期无显著增减配（变动幅度均在阈值以内）</span>'

    summary_html = f'''<div>
  <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px">
    <div class="sum-label">本期配置动作</div>
    <div style="font-size:10px;color:#4a607c">（相对均衡权重变动 ≥{int(ACTION_THRESHOLD*100)}% 触发）</div>
  </div>
  <div style="margin-bottom:14px">{action_html}</div>
  <div style="height:1px;background:linear-gradient(90deg,#1e3254 60%,transparent);margin-bottom:10px"></div>
  <div class="sum-label" style="margin-bottom:6px">本期观点方向</div>
  <div class="sum-banner" style="margin-bottom:0;display:flex;flex-wrap:nowrap;gap:6px;overflow-x:auto">{tags_html}</div>
</div>'''

    # ── 投委会观点表格行（紧凑版）
    vote_rows = ""
    for name in names:
        cfg = asset_config.get(name, {})
        asset_type = cfg.get("asset_type", "equity")
        vote_dict = votes_config.get(name, {})
        q_val = view_q_map.get(name, 0.0)
        direction, color, arrow = _score_direction(q_val, name, asset_type, score_range_config, durations)

        if not vote_dict:
            vote_rows += f'''<tr>
              <td class="an">{name}</td>
              <td style="color:#9ca3af;font-style:italic">无投票</td>
              <td style="color:#9ca3af">—</td>
              <td style="color:#9ca3af">—</td>
              <td style="color:#9ca3af;font-size:11px;font-style:italic">完全依赖先验</td>
            </tr>'''
            continue

        total = sum(vote_dict.values())
        weighted_score = sum(s * c for s, c in vote_dict.items()) / total
        vote_bar = _vote_bar_html(vote_dict)
        vote_detail = " ".join([f"{s}×{c}" for s, c in sorted(vote_dict.items())])

        # 看多=红, 看空=绿, 中性=灰（中国市场惯例）
        if direction == "看多":
            badge_cls = "bu"    # 红底
            badge_color = "#e05252"
        elif direction == "看空":
            badge_cls = "bd2"   # 绿底
            badge_color = "#3dba7e"
        else:
            badge_cls = "bn"    # 灰底
            badge_color = "#7a8caa"

        vote_rows += f"""<tr>
          <td class="an">{name}</td>
          <td>{vote_bar}<span class="tiny">{vote_detail}</span></td>
          <td style="font-weight:600">{weighted_score:.2f}</td>
          <td><span class="bd {badge_cls}">{arrow} {direction}</span></td>
          <td style="font-weight:600;color:{badge_color}">{q_val*100:+.3f}%</td>
        </tr>"""

    # ── 权重对比表格行（紧凑版）
    weight_rows = ""
    for i, name in enumerate(names):
        wm = float(w_mkt[i])
        ws = float(w_star[i])
        delta = ws - wm
        if delta > 0.002:
            arrow = "↑"
            direction_label = "看多"
            dir_color = "#e05252"   # 看多红
            delta_color = "#e05252"
        elif delta < -0.002:
            arrow = "↓"
            direction_label = "看空"
            dir_color = "#3dba7e"   # 看空绿
            delta_color = "#3dba7e"
        else:
            arrow = "→"
            direction_label = "中性"
            dir_color = "#7a8caa"
            delta_color = "#7a8caa"
        if name in dynamic_constraints:
            lo = dynamic_constraints[name].get("lower", 0)
            hi = dynamic_constraints[name].get("upper", 1)
            cstr = f"{lo*100:.0f}~{hi*100:.0f}%"
        else:
            cstr = "—"
        dir_bg = "rgba(224,82,82,0.12)" if direction_label == "看多" else ("rgba(61,186,126,0.12)" if direction_label == "看空" else "rgba(122,140,170,0.10)")
        delta_abs = abs(delta * 100)
        row_id = f"wrow-{name.replace('-','_').replace(' ','_')}"
        weight_rows += f"""<tr id="{row_id}">
          <td class="an">{name}</td>
          <td style="color:#8a9bb5">{wm*100:.2f}%</td>
          <td>{ws*100:.2f}%</td>
          <td style="color:{delta_color};font-weight:600;font-size:12px">{delta_abs:.2f}% {arrow}</td>
          <td><span class="bd" style="background:{dir_bg};color:{dir_color};padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600">{direction_label}</span></td>
          <td style="color:#6b7a99;font-size:12px">{cstr}</td>
        </tr>"""

    liq_w = liquidity_config["weight"]
    liq_n = liquidity_config["name"]
    weight_rows += f'<tr><td class="an" style="color:#6b7a99">{liq_n}（锁定）</td><td style="color:#6b7a99">{liq_w*100:.1f}%</td><td style="color:#6b7a99">{liq_w*100:.1f}%</td><td style="color:#6b7a99">— →</td><td style="color:#6b7a99">—</td><td style="color:#6b7a99;font-size:11px">固定</td></tr>'

    # ── 收益对比表格行（紧凑版）
    return_rows = ""
    for i, name in enumerate(names):
        pi_v  = float(Pi[i]) if i < len(Pi) else 0.0
        q_v   = float(Q[i]) if i < len(Q) else 0.0
        mu_v  = float(mu_BL[i]) if i < len(mu_BL) else 0.0
        diff  = mu_v - pi_v
        diff_color = "#dc2626" if diff > 0.001 else ("#16a34a" if diff < -0.001 else "#6b7280")
        diff_arrow = "↑" if diff > 0.001 else ("↓" if diff < -0.001 else "→")
        return_rows += f"""<tr>
          <td class="an">{name}</td>
          <td style="text-align:right">{pi_v*100:.3f}%</td>
          <td style="text-align:right">{q_v*100:+.3f}%</td>
          <td style="text-align:right;font-weight:600">{mu_v*100:.3f}%</td>
          <td style="text-align:right;color:{diff_color};font-weight:600">{diff*100:+.3f}% {diff_arrow}</td>
        </tr>"""

    # ── 约束说明行
    constraint_rows = ""
    for name, c in dynamic_constraints.items():
        lo = c.get("lower", 0)
        hi = c.get("upper", 1)
        constraint_rows += f'<tr><td class="an">{name}</td><td><span class="bd bn">动态</span></td><td>{lo*100:.1f}% ~ {hi*100:.1f}%</td><td class="tiny" style="color:#9ca3af">风险平价权重 ±{fixed_income_band*100:.0f}%</td></tr>'
    for gname, gc in group_constraints.items():
        lo_str = f"≥{gc['lower']*100:.0f}%" if "lower" in gc else "—"
        hi_str = f"≤{gc['upper']*100:.0f}%" if "upper" in gc else "—"
        constraint_rows += f'<tr><td class="an">{gname}</td><td><span class="bd bn">组合</span></td><td>{lo_str} {hi_str}</td><td class="tiny" style="color:#9ca3af">含权资产合计上限</td></tr>'

    # ── 纯 CSS 图表生成
    def _css_bar_chart(series_list, labels, height=220):
        """
        生成纯 CSS 分组条形图（零依赖，单文件可独立运行）
        series_list: [(name, color, values), ...]
        labels: 各组 x 轴标签
        values 单位：已转换为 %
        """
        all_vals = [v for _, _, vals in series_list for v in vals]
        max_abs = max(abs(v) for v in all_vals) if all_vals else 1
        max_val = max_abs * 1.15  # 留点顶部空间

        # Y 轴刻度
        step = max_val / 4
        yticks = [round(step * i, 3) for i in range(5)]

        bars_html = ""
        for gi, label in enumerate(labels):
            group_bars = ""
            for si, (sname, color, vals) in enumerate(series_list):
                v = vals[gi] if gi < len(vals) else 0
                bar_h = abs(v) / max_val * (height - 30)
                bar_h = max(bar_h, 1)
                tooltip = f"{label} | {sname}: {v:+.3f}%"
                # 条形宽度用 flex:1 由父容器撑开，不写死像素
                if v >= 0:
                    style = (f"flex:1;min-width:0;height:{bar_h:.1f}px;"
                             f"background:{color};border-radius:3px 3px 0 0;"
                             f"margin-top:auto;cursor:default")
                else:
                    style = (f"flex:1;min-width:0;height:{bar_h:.1f}px;"
                             f"background:{color};border-radius:0 0 3px 3px;"
                             f"opacity:0.7;cursor:default")
                group_bars += f'<div title="{tooltip}" style="{style}"></div>'

            short_label = label if len(label) <= 6 else label[:5] + "…"
            # 每个分组 flex:1，等宽铺满容器
            bars_html += f'''<div style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:stretch;gap:2px">
              <div style="display:flex;align-items:flex-end;gap:2px;height:{height-30}px">{group_bars}</div>
              <div style="font-size:9px;color:#7a8caa;text-align:center;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">{short_label}</div>
            </div>'''

        # 图例
        legend_html = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:11px;color:#9ca3af">'
            f'<span style="display:inline-block;width:10px;height:10px;background:{color};border-radius:2px"></span>{sname}</span>'
            for sname, color, _ in series_list
        )

        return f'''<div style="padding:8px 0">
          <div style="display:flex;gap:4px;justify-content:center;margin-bottom:8px">{legend_html}</div>
          <div style="display:flex;align-items:flex-end;gap:6px;padding:0 8px;height:{height}px">
            {bars_html}
          </div>
        </div>'''

    # 权重图数据
    w_mkt_pct  = [round(float(v)*100, 3) for v in w_mkt]
    w_star_pct = [round(float(v)*100, 3) for v in w_star]
    Pi_pct     = [round(float(v)*100, 3) for v in Pi]
    Q_pct      = [round(float(v)*100, 3) for v in Q]
    mu_pct     = [round(float(v)*100, 3) for v in mu_BL]

    return_chart_html = _css_bar_chart(
        [("均衡收益 Π",  "rgba(99,130,230,0.85)",  Pi_pct),
         ("观点 Q",      "rgba(52,199,150,0.85)",   Q_pct),
         ("后验 μ_BL",   "rgba(248,113,56,0.85)",   mu_pct)],
        names, height=260
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BL 报告 — {meeting_date}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{min-height:100%;overflow:auto}}
body{{
  font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
  background:#1e2535;
  color:#d4d8e2;
  font-size:13px;
  line-height:1.5;
}}

/* ── 顶部 header（固定高度）── */
.hdr{{
  background:linear-gradient(135deg,#0f1c3f 0%,#1a3a6e 60%,#1e4d8c 100%);
  color:white;
  padding:12px 20px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  flex-shrink:0;
  gap:16px;
}}
.hdr h1{{font-size:16px;font-weight:700;letter-spacing:0.3px;white-space:nowrap}}
.hdr .sub{{font-size:11px;opacity:0.6;margin-top:1px}}
.meta-pills{{display:flex;gap:8px;flex-shrink:0}}
.pill{{
  background:rgba(255,255,255,0.12);
  border:1px solid rgba(255,255,255,0.18);
  border-radius:6px;
  padding:4px 10px;
  font-size:11px;
  white-space:nowrap;
}}
.pill b{{font-size:13px;display:block;font-weight:700}}
.kpi-bar{{display:flex;gap:10px;flex-shrink:0}}
.kpi{{
  border-radius:8px;
  padding:8px 18px;
  text-align:center;
  white-space:nowrap;
  min-width:90px;
}}
.kpi-ret{{background:rgba(220,38,38,0.18);border:1px solid rgba(220,38,38,0.45);border-bottom:3px solid #dc2626}}
.kpi-vol{{background:rgba(99,130,230,0.18);border:1px solid rgba(99,130,230,0.45);border-bottom:3px solid #6382e6}}
.kpi-sharpe{{background:rgba(52,199,150,0.18);border:1px solid rgba(52,199,150,0.45);border-bottom:3px solid #34c796}}
.kpi .kv{{font-size:22px;font-weight:800;letter-spacing:0.5px}}
.kpi-ret .kv{{color:#f87171}}
.kpi-vol .kv{{color:#93aaf5}}
.kpi-sharpe .kv{{color:#34c796}}
.kpi .kl{{font-size:10px;opacity:0.7;margin-top:3px;letter-spacing:0.3px}}

/* ── 主体：tab导航 + 两栏 ── */
.body-wrap{{
  display:flex;
  flex-direction:column;
  padding:0;
}}

/* Tab 导航 */
.tabs{{
  display:flex;
  background:#141c2e;
  padding:6px 16px 0;
  gap:2px;
  flex-shrink:0;
}}
.tab{{
  padding:6px 16px;
  font-size:12px;
  font-weight:600;
  color:#7a8aa8;
  cursor:pointer;
  border-radius:6px 6px 0 0;
  background:#1a2540;
  border:none;
  transition:all 0.15s;
  white-space:nowrap;
}}
.tab.active{{
  background:#1e2d4a;
  color:#93c5fd;
}}
.tab:hover:not(.active){{background:#1f2e4d;color:#a8bcd8}}

/* Tab 内容区 */
.tab-content{{
  display:none;
}}
.tab-content.active{{display:block}}

/* ── 两栏布局 ── */
.two-col{{
  display:grid;
  grid-template-columns:1fr 1px 1fr;
  align-items:stretch;
  gap:0 10px;
  padding:10px 16px;
}}
.col-divider{{background:#253552;margin:10px 0}}
.col{{
  display:flex;
  flex-direction:column;
  gap:10px;
  padding-right:4px;
}}
.col>.card{{flex:1}}

/* ── 卡片 ── */
.card{{
  background:#1e2d4a;
  border-radius:8px;
  padding:12px 16px;
  box-shadow:0 2px 8px rgba(0,0,0,0.3);
  flex-shrink:0;
  border:1px solid #253552;
  box-sizing:border-box;
}}
.card.grow{{flex:1;overflow:hidden;display:flex;flex-direction:column}}
.sec-title{{
  font-size:11px;
  font-weight:700;
  color:#93c5fd;
  text-transform:uppercase;
  letter-spacing:0.8px;
  margin-bottom:8px;
  padding-bottom:6px;
  border-bottom:1.5px solid #2d3f5e;
  display:flex;
  align-items:center;
  gap:6px;
  flex-shrink:0;
}}
.sec-title .num{{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:18px;height:18px;
  background:#1d4ed8;
  color:white;
  border-radius:50%;
  font-size:10px;
  font-weight:700;
  flex-shrink:0;
}}
.desc{{color:#8aa0be;font-size:11px;margin-bottom:8px;line-height:1.5}}

/* ── 表格 ── */
.tbl-wrap{{overflow-y:auto}}
.tbl-wrap::-webkit-scrollbar{{width:3px}}
.tbl-wrap::-webkit-scrollbar-thumb{{background:#2d3f5e;border-radius:2px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
thead th{{
  background:#162236;
  color:#7a8aa8;
  font-weight:600;
  padding:4px 8px;
  text-align:left;
  border-bottom:1px solid #253552;
  white-space:nowrap;
  font-size:11px;
  position:sticky;top:0;z-index:1;
}}
tbody td{{padding:3px 8px;border-bottom:1px solid #1a2a42;vertical-align:middle;color:#c8d4e6;font-size:12px;height:36px;box-sizing:border-box}}
tbody tr:last-child td{{border-bottom:none}}
tbody tr:hover td{{background:#162236}}
.an{{font-weight:500;color:#d4e0f0;white-space:nowrap}}
.tiny{{font-size:10px;color:#5a7090}}

/* ── Badge ── */
.bd{{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600}}
.bu{{background:rgba(224,82,82,0.15);color:#e05252}}
.bd2{{background:rgba(61,186,126,0.15);color:#3dba7e}}
.bn{{background:rgba(122,140,170,0.15);color:#7a8caa}}

/* ── 指标卡组 ── */
.kpi-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px;flex-shrink:0}}
.metric{{background:#162236;border-radius:6px;padding:10px 12px;border-left:3px solid #1d4ed8}}
.metric .ml{{font-size:11px;color:#7a8aa8;margin-bottom:3px}}
.metric .mv{{font-size:20px;font-weight:700;color:#e2eaf8}}
.metric .mu{{font-size:12px;font-weight:400;color:#7a8aa8}}

/* ── 单栏布局（模型说明页）── */
.one-col{{
  padding:10px 16px;
  flex:1;
  overflow-y:auto;
  display:flex;
  flex-direction:column;
  gap:10px;
}}
.one-col::-webkit-scrollbar{{width:4px}}
.one-col::-webkit-scrollbar-thumb{{background:#2d3f5e;border-radius:2px}}
.steps-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px}}
.step{{background:#162236;border-radius:6px;padding:10px 12px;border-top:2px solid #1d4ed8}}
.step .sn{{font-size:10px;color:#93c5fd;font-weight:700;text-transform:uppercase;margin-bottom:2px}}
.step .st{{font-size:12px;font-weight:600;color:#d4e0f0;margin-bottom:2px}}
.step .sd{{font-size:11px;color:#7a8aa8;line-height:1.4}}
.design-tbl th{{background:#162236}}
.ref-list{{list-style:none;padding:0}}
.ref-list li{{padding:6px 0;border-bottom:1px solid #1a2a42;font-size:12px;color:#a8bcd8;display:flex;gap:8px;line-height:1.5}}
.ref-list li:last-child{{border-bottom:none}}
.rn{{min-width:18px;height:18px;background:#1e3a6e;color:#93c5fd;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;margin-top:2px}}
em{{color:#93c5fd;font-style:italic}}
.note{{font-size:10.5px;color:#5a7090;margin-top:6px;padding-top:6px;border-top:1px dashed #253552;flex-shrink:0}}
.sum-banner{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px}}
.sum-tag{{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;border-radius:20px;font-size:13px;font-weight:700;letter-spacing:0.3px}}
.sum-tag-bull{{background:rgba(224,82,82,0.15);border:1px solid rgba(224,82,82,0.5);color:#e05252}}
.sum-tag-bear{{background:rgba(61,186,126,0.15);border:1px solid rgba(61,186,126,0.5);color:#3dba7e}}
.sum-tag-neu{{background:rgba(122,140,170,0.15);border:1px solid rgba(122,140,170,0.4);color:#7a8caa}}
.sum-divider{{width:1px;background:#1e3254;margin:0 4px;flex-shrink:0}}
.sum-move{{margin-top:10px;padding:10px 14px;background:#111e35;border-radius:8px;border-left:3px solid #3b82f6;font-size:12.5px;color:#a8bcd8;line-height:1.8}}
.sum-move strong{{color:#93c5fd}}
.sum-label{{font-size:10px;color:#5a7090;margin-bottom:6px;text-transform:uppercase;letter-spacing:1px}}
.chart-wrap{{flex-shrink:0}}
</style>
</head>
<body>

<!-- ══ 顶部 Header ══ -->
<div class="hdr">
  <div>
    <h1>Black-Litterman 资产配置模型报告</h1>
    <div class="sub">Investment Committee · Quantitative Asset Allocation · Auto-generated</div>
  </div>
  <div class="meta-pills">
    <div class="pill"><b>{meeting_date}</b>会议日期</div>
    <div class="pill"><b>{hist_start}</b>数据起始</div>
    <div class="pill"><b>{hist_end}</b>数据截止</div>
    <div class="pill"><b>{len(names)} 个</b>参与资产</div>
  </div>
</div>

<!-- ══ Tab 导航 ══ -->
<div class="body-wrap">
  <div class="tabs">
    <button class="tab active" onclick="switchTab(0)">📊 本期配置结果</button>
    <button class="tab" onclick="switchTab(1)">📖 模型说明</button>
    <button class="tab" onclick="switchTab(2)">📈 收益融合过程</button>
    <button class="tab" onclick="switchTab(3)">🔒 约束说明</button>
  </div>

  <!-- ══ Tab 0：配置结果（两栏：投委会观点 | 权重对比）══ -->
  <div class="tab-content active">
    <!-- 配置结论摘要 -->
    <div style="padding:8px 16px 0 16px;flex-shrink:0">
      <div style="background:linear-gradient(135deg,#0d1e3d 0%,#111e38 60%,#0a1729 100%);border:1px solid #1e3254;border-radius:10px;padding:10px 16px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
          <span style="font-size:16px">🎯</span>
          <span style="font-size:13px;font-weight:700;color:#93c5fd;text-transform:uppercase;letter-spacing:1.5px">本期配置结论摘要</span>
          <span style="flex:1;height:1px;background:linear-gradient(90deg,#1e3254,transparent)"></span>
        </div>
        {summary_html}
        <div style="margin-top:14px;padding-top:12px;border-top:1px solid #1e3254;display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
          <div style="background:linear-gradient(135deg,#12203f,#0e1b35);border:1px solid rgba(248,113,113,0.35);border-radius:10px;padding:14px 18px;box-shadow:0 2px 12px rgba(248,113,113,0.08),inset 0 1px 0 rgba(248,113,113,0.12)">
            <div style="font-size:10px;font-weight:600;color:#7a8aa8;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase">预期年化收益</div>
            <div style="font-size:28px;font-weight:800;color:#f87171;letter-spacing:0.5px;line-height:1">{exp_port_ret*100:.2f}%</div>
            <div style="margin-top:8px;height:2px;background:linear-gradient(90deg,rgba(248,113,113,0.6),transparent);border-radius:1px"></div>
          </div>
          <div style="background:linear-gradient(135deg,#12203f,#0e1b35);border:1px solid rgba(147,170,245,0.35);border-radius:10px;padding:14px 18px;box-shadow:0 2px 12px rgba(147,170,245,0.08),inset 0 1px 0 rgba(147,170,245,0.12)">
            <div style="font-size:10px;font-weight:600;color:#7a8aa8;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase">预期年化波动</div>
            <div style="font-size:28px;font-weight:800;color:#93aaf5;letter-spacing:0.5px;line-height:1">{exp_port_vol*100:.2f}%</div>
            <div style="margin-top:8px;height:2px;background:linear-gradient(90deg,rgba(147,170,245,0.6),transparent);border-radius:1px"></div>
          </div>
          <div style="background:linear-gradient(135deg,#12203f,#0e1b35);border:1px solid rgba(248,180,60,0.35);border-radius:10px;padding:14px 18px;box-shadow:0 2px 12px rgba(248,180,60,0.08),inset 0 1px 0 rgba(248,180,60,0.12)">
            <div style="font-size:10px;font-weight:600;color:#7a8aa8;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase">夏普比率</div>
            <div style="font-size:28px;font-weight:800;color:#f8b43c;letter-spacing:0.5px;line-height:1">{exp_port_sharpe:.2f}</div>
            <div style="margin-top:8px;height:2px;background:linear-gradient(90deg,rgba(248,180,60,0.6),transparent);border-radius:1px"></div>
          </div>
          <div style="background:linear-gradient(135deg,#12203f,#0e1b35);border:1px solid rgba(52,199,150,0.35);border-radius:10px;padding:14px 18px;box-shadow:0 2px 12px rgba(52,199,150,0.08),inset 0 1px 0 rgba(52,199,150,0.12)">
            <div style="font-size:10px;font-weight:600;color:#7a8aa8;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase">历史最大回撤</div>
            <div style="font-size:28px;font-weight:800;color:#34c796;letter-spacing:0.5px;line-height:1">{max_drawdown*100:.2f}%</div>
            <div style="margin-top:8px;height:2px;background:linear-gradient(90deg,rgba(52,199,150,0.6),transparent);border-radius:1px"></div>
          </div>
        </div>
      </div>
    </div>
    <div class="two-col">
      <!-- 左栏：投委会观点 -->
      <div class="col">
        <div class="card">
          <div style="padding:4px 0 8px">
            <div style="font-size:11px;font-weight:700;color:#7a8aa8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">本期投委会观点汇总</div>
            <table>
              <thead>
                <tr>
                  <th>资产</th>
                  <th style="min-width:120px">投票分布</th>
                  <th>加权得分</th>
                  <th>观点方向</th>
                  <th>量化观点Q</th>
                </tr>
              </thead>
              <tbody>{vote_rows}</tbody>
            </table>
            <div class="note" style="margin-top:4px;line-height:2">
              <div>* 色块：红=看多 灰=中性 绿=看空</div>
              <div>* Q = 投票转换后年化预期收益率（固收已通过久期转换）</div>
              <div>* 票型：1-谨慎 2-中性偏谨慎 3-中性 4-中性偏乐观 5-乐观</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分隔线 -->
      <div class="col-divider"></div>

      <!-- 右栏：配置结果明细 -->
      <div class="col">
        <div class="card">
          <div style="padding:4px 0 8px">
            <div style="font-size:11px;font-weight:700;color:#7a8aa8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">配置结果明细</div>
            <table>
              <thead>
                <tr>
                  <th>资产</th>
                  <th>均衡权重</th>
                  <th>配置权重</th>
                  <th>变动</th>
                  <th>配置方向</th>
                  <th>约束范围</th>
                </tr>
              </thead>
              <tbody>{weight_rows}</tbody>
            </table>
            <div class="note" style="margin-top:4px;line-height:2">
              <div>* 组合权重基于后验收益 μ_BL 和历史协方差矩阵优化计算</div>
              <div>* <strong style="color:#e2c87a">本表核心在于相对变化（w* − w_mkt），而非 w* 的绝对数值</strong>：模型绝对权重受建模假设影响，稳定性有限；w* − w_mkt 才是本期投委会观点的净信号，决定增减方向与幅度。w* 仅作为移动目标区间的参考上限，实际执行还需结合持仓、换手成本及流动性综合判断</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ══ Tab 1：模型说明 ══ -->
  <div class="tab-content">
    <div class="one-col">
      <div class="card">
        <div class="sec-title"><span class="num">①</span>模型原理简介</div>
        <p class="desc">Black-Litterman 模型通过<strong>贝叶斯框架</strong>将市场均衡先验与投资委员会主观观点融合，解决了传统均值-方差优化对输入高度敏感的问题，输出更稳健的预期收益与配置权重。</p>
        <div class="steps-grid">
          <div class="step"><div class="sn">Step 01</div><div class="st">估计协方差矩阵</div><div class="sd">Ledoit-Wolf 收缩估计，基于近3年滚动历史，降低噪声</div></div>
          <div class="step"><div class="sn">Step 02</div><div class="st">计算均衡基准权重</div><div class="sd">SAA 大类约束 + 大类内部风险平价，得均衡权重 w_mkt</div></div>
          <div class="step"><div class="sn">Step 03</div><div class="st">推算均衡隐含收益 Π</div><div class="sd">从均衡权重反推市场隐含的预期收益率，作为贝叶斯先验</div></div>
          <div class="step"><div class="sn">Step 04</div><div class="st">汇总投委会观点 Q</div><div class="sd">将打分（1–5分）转换为量化收益预期，委员分歧影响可信度</div></div>
          <div class="step"><div class="sn">Step 05</div><div class="st">贝叶斯融合 → μ_BL</div><div class="sd">将均衡先验 Π 与观点 Q 按可信度加权融合，得后验收益</div></div>
          <div class="step"><div class="sn">Step 06</div><div class="st">均值-方差优化 → w*</div><div class="sd">在 SAA 及权重约束下，基于 μ_BL 求解最优配置权重 w*</div></div>
        </div>
      </div>
      <div class="card">
        <div class="sec-title"><span class="num">②</span>模型设计说明</div>
        <table class="design-tbl">
          <thead><tr><th style="width:18%">设计决策</th><th style="width:42%">具体做法</th><th>原因</th></tr></thead>
          <tbody>
            <tr><td class="an">均衡基准权重</td><td>SAA 规定各大类总占比，大类内部多个子资产之间用<strong>风险平价</strong>分配</td><td class="tiny">使各子资产对组合风险的贡献相等，避免高波动资产占据绝大部分风险预算</td></tr>
            <tr><td class="an">固收价格构造</td><td>中债登收益率曲线，通过 <em>价格收益率 = −久期 × 利率日变动</em> 还原</td><td class="tiny">固收无直接二级市场价格指数，需从收益率曲线还原价格波动</td></tr>
            <tr><td class="an">协方差矩阵</td><td>Ledoit-Wolf 收缩估计，近3年滚动历史（约750个交易日）年化</td><td class="tiny">样本协方差矩阵在资产较多时噪声大，收缩估计能有效降低估计误差</td></tr>
            <tr><td class="an">投委会观点</td><td>每个资产独立打分（绝对观点1–5），各档对应收益区间中点按票数加权</td><td class="tiny">绝对观点直观易操作；区间中点是保守的无偏估计</td></tr>
            <tr><td class="an">固收观点转换</td><td>固收打分对应利率变动幅度（bp），乘以负久期换算为价格收益率</td><td class="tiny">投委会习惯用利率升降描述；BL 框架需统一的价格收益率口径</td></tr>
            <tr><td class="an">观点不确定性 Ω</td><td>基础值取 He-Litterman 标准公式（τ·PΣPᵀ），再乘以委员分歧系数</td><td class="tiny">委员分歧越大，模型降低该观点可信度，更多依赖均衡先验</td></tr>
            <tr><td class="an">流动性处理</td><td>流动性资产占比 6% 直接锁定，不参与 BL 优化；其余 94% 进入模型</td><td class="tiny">流动性配置由产品流动性管理需求决定，与收益优化目标无关</td></tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <div class="sec-title"><span class="num">③</span>参考文献</div>
        <ul class="ref-list">
          <li><span class="rn">1</span><span>Black, F., &amp; Litterman, R. (1992). <em>Global Portfolio Optimization.</em> Financial Analysts Journal, 48(5), 28–43.</span></li>
          <li><span class="rn">2</span><span>He, G., &amp; Litterman, R. (1999). <em>The Intuition Behind Black-Litterman Model Portfolios.</em> Goldman Sachs Investment Management Research.</span></li>
          <li><span class="rn">3</span><span>Ledoit, O., &amp; Wolf, M. (2004). <em>A well-conditioned estimator for large-dimensional covariance matrices.</em> Journal of Multivariate Analysis, 88(2), 365–411.</span></li>
          <li><span class="rn">4</span><span>Maillard, S., Roncalli, T., &amp; Teïletche, J. (2010). <em>The Properties of Equally Weighted Risk Contribution Portfolios.</em> Journal of Portfolio Management, 36(4), 60–70.</span></li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ══ Tab 2：收益融合过程（两栏：图表 | 表格）══ -->
  <div class="tab-content">
    <div class="two-col">
      <!-- 左栏：图表 -->
      <div class="col">
        <div class="card" style="display:flex;flex-direction:column;flex:1">
          <div class="sec-title"><span class="num">2</span>均衡收益 Π / 观点 Q / 后验收益 μ_BL</div>
          <p class="desc">均衡收益 Π 是模型"出发点"（纯风险分散视角），观点 Q 是本期投委会主观判断，μ_BL 是贝叶斯融合后的最终预期收益，驱动后续优化。</p>
          {return_chart_html}
        </div>
      </div>
      <!-- 分割线 -->
      <div class="col-divider"></div>
      <!-- 右栏：表格 -->
      <div class="col">
        <div class="card" style="display:flex;flex-direction:column;flex:1;overflow:hidden">
          <div class="sec-title"><span class="num">2</span>收益融合明细</div>
          <div class="tbl-wrap">
            <table>
              <thead>
                <tr>
                  <th>资产</th>
                  <th style="text-align:right">均衡收益 Π</th>
                  <th style="text-align:right">观点 Q</th>
                  <th style="text-align:right">后验 μ_BL</th>
                  <th style="text-align:right">融合偏移</th>
                </tr>
              </thead>
              <tbody>{return_rows}</tbody>
            </table>
          </div>
          <div class="note">* 融合偏移 = μ_BL − Π，正值表示观点拉高了对该资产的收益预期</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ══ Tab 3：约束说明 ══ -->
  <div class="tab-content">
    <div class="two-col" style="align-items:stretch">
      <div class="col">
        <div class="card" style="display:flex;flex-direction:column;flex:1;overflow:hidden">
          <div class="sec-title"><span class="num">4</span>本期生效约束</div>
          <p class="desc">固收子类权重上下限基于本期风险平价权重动态生成（±{fixed_income_band*100:.0f}%），防止久期风险过度集中。含权资产合计上限 20%，流动性资产固定 6%。</p>
          <div class="tbl-wrap">
            <table>
              <thead>
                <tr>
                  <th>资产 / 分组</th>
                  <th>约束类型</th>
                  <th>本期范围</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>{constraint_rows}</tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="col-divider"></div>
      <div class="col">
        <div class="card" style="display:flex;flex-direction:column;flex:1;min-height:0">
          <div class="sec-title">约束设计原则</div>
          <table>
            <thead><tr><th>约束类型</th><th>规则</th><th>目的</th></tr></thead>
            <tbody>
              <tr><td class="an">固收动态约束</td><td>风险平价权重 × (1 ± {fixed_income_band*100:.0f}%)</td><td class="tiny">防止久期过度集中</td></tr>
              <tr><td class="an">含权合计上限</td><td>含权类资产合计 ≤ 20%</td><td class="tiny">匹配产品风险属性</td></tr>
              <tr><td class="an">流动性锁定</td><td>固定 6%，不进优化</td><td class="tiny">满足产品流动性需求</td></tr>
              <tr><td class="an">全局权重下限</td><td>各资产 ≥ 0%（做多）</td><td class="tiny">不允许做空</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

</div><!-- end body-wrap -->

<script>
function switchTab(idx) {{
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', i===idx));
  document.querySelectorAll('.tab-content').forEach((c,i) => c.classList.toggle('active', i===idx));
  // 切换到 Tab2 时渲染收益图（首次可能未渲染）
  if(idx===2) {{ setTimeout(initReturnChart, 50); }}
}}

function highlightRow(rowId) {{
  var row = document.getElementById(rowId);
  if (!row) return;
  row.scrollIntoView({{behavior:'smooth', block:'center'}});
  row.style.transition = 'background 0.2s';
  row.style.background = 'rgba(248,180,60,0.30)';
  setTimeout(function() {{
    row.style.transition = 'background 1.5s';
    row.style.background = '';
  }}, 1200);
}}
</script>
</body>
</html>"""

    output_path = os.path.join(output_dir, f"BL_report_{meeting_date}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[报告] 已生成：{output_path}")
    return output_path
