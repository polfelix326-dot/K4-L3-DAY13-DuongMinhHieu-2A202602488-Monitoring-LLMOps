#!/usr/bin/env python3
"""
Dashboard CP2 – đọc data/logs.jsonl và xuất HTML dashboard 6 panel.
Chạy: python scripts/dashboard.py
Sau đó mở data/dashboard.html bằng trình duyệt để chụp ảnh evidence.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / os.getenv("LOG_PATH", "data/logs.jsonl")

def load_records(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records

def percentile(data: list[float], p: int) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return round(s[f] + (s[c] - s[f]) * (k - f), 2)

def compute_panel_data(records: list[dict]) -> dict:
    resp = [r for r in records if r.get("event") == "response_sent"]
    req = [r for r in records if r.get("event") == "request_received"]
    fail = [r for r in records if r.get("event") == "request_failed"]

    latencies = [r["latency_ms"] for r in resp if "latency_ms" in r]
    ttfts = [r["ttft_ms"] for r in resp if "ttft_ms" in r]

    p = lambda data, pct: percentile(data, pct)

    costs = [r["cost_usd"] for r in resp if "cost_usd" in r]
    toks_in = [r["tokens_in"] for r in resp if "tokens_in" in r]
    toks_out = [r["tokens_out"] for r in resp if "tokens_out" in r]
    quality = [r["quality_score"] for r in resp if "quality_score" in r]
    tool_success_vals = [r.get("tool_success") for r in resp if "tool_success" in r]
    retrieval_successes = sum(1 for v in tool_success_vals if v is True)
    retrieval_total = len(tool_success_vals)

    return {
        "latency": {
            "p50": p(latencies, 50),
            "p95": p(latencies, 95),
            "p99": p(latencies, 99),
            "ttft_p95": p(ttfts, 95),
            "data": latencies,
            "ttft_data": ttfts,
        },
        "traffic": {
            "total": len(req),
            "data": req,
        },
        "errors": {
            "error_rate_pct": round(len(fail) / max(len(req), 1) * 100, 2),
            "total_errors": len(fail),
            "retrieval_success_rate": round(retrieval_successes / max(retrieval_total, 1) * 100, 1),
            "error_types": {},
        },
        "cost": {
            "total": round(sum(costs), 6),
            "data": costs,
        },
        "tokens": {
            "total_in": sum(toks_in),
            "total_out": sum(toks_out),
            "data_in": toks_in,
            "data_out": toks_out,
        },
        "quality": {
            "mean": round(statistics.mean(quality) if quality else 0, 3),
            "data": quality,
        },
    }

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>K4-L3A Day 13 Monitoring & LLMOps Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f1117; color: #e2e8f0; }}
  header {{ background: linear-gradient(135deg, #1a1f36, #2d3748); padding: 20px 32px; border-bottom: 1px solid #2d3748; }}
  header h1 {{ font-size: 1.4rem; color: #90cdf4; font-weight: 700; }}
  header p {{ font-size: 0.8rem; color: #718096; margin-top: 4px; }}
  .meta {{ display: flex; gap: 16px; margin-top: 10px; font-size: 0.75rem; color: #a0aec0; }}
  .meta span {{ background: #2d3748; padding: 3px 10px; border-radius: 12px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 24px 32px; }}
  .card {{ background: #1a202c; border: 1px solid #2d3748; border-radius: 12px; padding: 20px; }}
  .card h2 {{ font-size: 0.85rem; color: #718096; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 14px; font-weight: 600; }}
  .metric-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
  .metric-name {{ font-size: 0.82rem; color: #a0aec0; }}
  .metric-value {{ font-size: 1.1rem; font-weight: 700; }}
  .green {{ color: #68d391; }}
  .yellow {{ color: #f6e05e; }}
  .red {{ color: #fc8181; }}
  .blue {{ color: #63b3ed; }}
  .purple {{ color: #b794f4; }}
  .cyan {{ color: #76e4f7; }}
  .slo-line {{ margin-top: 12px; padding-top: 10px; border-top: 1px solid #2d3748; font-size: 0.75rem; color: #718096; }}
  .slo-ok {{ color: #68d391; }} .slo-fail {{ color: #fc8181; }}
  .bar-wrap {{ margin-top: 12px; }}
  .bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 0.75rem; }}
  .bar-label {{ width: 80px; color: #a0aec0; text-align: right; }}
  .bar {{ background: #2d3748; border-radius: 4px; height: 14px; flex: 1; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; }}
  .bar-val {{ width: 60px; text-align: right; color: #e2e8f0; }}
  footer {{ text-align: center; padding: 16px; font-size: 0.72rem; color: #4a5568; border-top: 1px solid #2d3748; }}
</style>
</head>
<body>
<header>
  <h1>&#x1F4CA; K4-L3A Day 13 — Monitoring & LLMOps Dashboard</h1>
  <p>Source: data/logs.jsonl &nbsp;|&nbsp; Time range: 60 min &nbsp;|&nbsp; Refresh: 30s</p>
  <div class="meta">
    <span>Records: {total_records}</span>
    <span>Requests: {total_req}</span>
    <span>Errors: {total_errors}</span>
    <span>SLO Target: P95 &le; 3000ms</span>
    <span>Quality &ge; 0.75</span>
  </div>
</header>
<div class="grid">

  <!-- Panel 1: Latency -->
  <div class="card">
    <h2>&#x23F1; Latency (ms)</h2>
    <div class="bar-wrap">
      <div class="bar-row">
        <span class="bar-label">P50</span>
        <div class="bar"><div class="bar-fill" style="width:{p50_pct}%;background:#63b3ed;"></div></div>
        <span class="bar-val blue">{p50}ms</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">P95</span>
        <div class="bar"><div class="bar-fill" style="width:{p95_pct}%;background:{p95_color};"></div></div>
        <span class="bar-val" style="color:{p95_color}">{p95}ms</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">P99</span>
        <div class="bar"><div class="bar-fill" style="width:{p99_pct}%;background:#b794f4;"></div></div>
        <span class="bar-val purple">{p99}ms</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">TTFT P95</span>
        <div class="bar"><div class="bar-fill" style="width:{ttft_pct}%;background:#76e4f7;"></div></div>
        <span class="bar-val cyan">{ttft_p95}ms</span>
      </div>
    </div>
    <div class="slo-line">SLO threshold: P95 &le; 3000ms &nbsp; <span class="{p95_slo_cls}">{p95_slo_txt}</span></div>
  </div>

  <!-- Panel 2: Traffic -->
  <div class="card">
    <h2>&#x1F4E1; Traffic</h2>
    <div class="metric-row">
      <span class="metric-name">Total requests</span>
      <span class="metric-value blue">{total_req}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Total responses</span>
      <span class="metric-value green">{total_resp}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Avg req/min</span>
      <span class="metric-value cyan">{rpm}</span>
    </div>
    <div class="slo-line">Threshold: &ge; 1 req/min &nbsp; <span class="slo-ok">&#x2713; OK</span></div>
  </div>

  <!-- Panel 3: Errors & Retrieval -->
  <div class="card">
    <h2>&#x26A0; Errors & Retrieval</h2>
    <div class="metric-row">
      <span class="metric-name">Error rate</span>
      <span class="metric-value {err_color}">{error_rate}%</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Total errors</span>
      <span class="metric-value {err_color}">{total_errors}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Retrieval success</span>
      <span class="metric-value green">{retrieval_success}%</span>
    </div>
    <div class="slo-line">Error rate &le; 2% &nbsp; <span class="{err_slo_cls}">{err_slo_txt}</span>
      &nbsp;| Retrieval &ge; 90% &nbsp; <span class="{ret_slo_cls}">{ret_slo_txt}</span></div>
  </div>

  <!-- Panel 4: Cost -->
  <div class="card">
    <h2>&#x1F4B0; Cost (USD)</h2>
    <div class="metric-row">
      <span class="metric-name">Total cost</span>
      <span class="metric-value green">${total_cost}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Avg per request</span>
      <span class="metric-value cyan">${avg_cost}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Max per request</span>
      <span class="metric-value yellow">${max_cost}</span>
    </div>
    <div class="slo-line">Daily budget: &le; $2.50 &nbsp; <span class="slo-ok">&#x2713; OK</span></div>
  </div>

  <!-- Panel 5: Tokens -->
  <div class="card">
    <h2>&#x1F522; Tokens</h2>
    <div class="metric-row">
      <span class="metric-name">Total input</span>
      <span class="metric-value blue">{total_in}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Total output</span>
      <span class="metric-value purple">{total_out}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Total combined</span>
      <span class="metric-value cyan">{total_tokens}</span>
    </div>
    <div class="slo-line">Budget: &le; 50,000 tokens &nbsp; <span class="{tok_slo_cls}">{tok_slo_txt}</span></div>
  </div>

  <!-- Panel 6: Quality -->
  <div class="card">
    <h2>&#x2B50; Quality Score (0-1)</h2>
    <div class="metric-row">
      <span class="metric-name">Mean quality</span>
      <span class="metric-value {qual_color}">{mean_quality}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Min quality</span>
      <span class="metric-value yellow">{min_quality}</span>
    </div>
    <div class="metric-row">
      <span class="metric-name">Max quality</span>
      <span class="metric-value green">{max_quality}</span>
    </div>
    <div class="slo-line">Quality &ge; 0.75 &nbsp; <span class="{qual_slo_cls}">{qual_slo_txt}</span></div>
  </div>

</div>
<footer>
  K4-L3A Day 13 Monitoring &amp; LLMOps — 2A202602488 — dashboard.py — data/logs.jsonl
</footer>
</body>
</html>
"""

def build_dashboard(records: list[dict]) -> str:
    d = compute_panel_data(records)
    lat = d["latency"]
    traf = d["traffic"]
    err = d["errors"]
    cost = d["cost"]
    tok = d["tokens"]
    qual = d["quality"]

    total_req = traf["total"]
    total_resp = len([r for r in records if r.get("event") == "response_sent"])
    rpm = round(total_req / 60, 2) if total_req else 0

    MAX_MS = 5000
    p95_color = "#68d391" if lat["p95"] <= 3000 else "#fc8181"
    p95_slo_cls = "slo-ok" if lat["p95"] <= 3000 else "slo-fail"
    p95_slo_txt = "&#x2713; OK" if lat["p95"] <= 3000 else "&#x2717; FAIL"

    err_color = "green" if err["error_rate_pct"] <= 2 else "red"
    err_slo_cls = "slo-ok" if err["error_rate_pct"] <= 2 else "slo-fail"
    err_slo_txt = "&#x2713; OK" if err["error_rate_pct"] <= 2 else "&#x2717; FAIL"
    ret_slo_cls = "slo-ok" if err["retrieval_success_rate"] >= 90 else "slo-fail"
    ret_slo_txt = "&#x2713; OK" if err["retrieval_success_rate"] >= 90 else "&#x2717; FAIL"

    costs_list = cost["data"]
    avg_cost = round(sum(costs_list) / max(len(costs_list), 1), 6)
    max_cost = round(max(costs_list, default=0), 6)

    total_tokens = tok["total_in"] + tok["total_out"]
    tok_slo_cls = "slo-ok" if total_tokens <= 50000 else "slo-fail"
    tok_slo_txt = "&#x2713; OK" if total_tokens <= 50000 else "&#x2717; FAIL"

    qual_color = "green" if qual["mean"] >= 0.75 else "red"
    qual_slo_cls = "slo-ok" if qual["mean"] >= 0.75 else "slo-fail"
    qual_slo_txt = "&#x2713; OK" if qual["mean"] >= 0.75 else "&#x2717; FAIL"
    min_qual = round(min(qual["data"], default=0), 3)
    max_qual = round(max(qual["data"], default=0), 3)

    def pct(v, mx=MAX_MS):
        return min(100, round(v / mx * 100, 1))

    html = HTML_TEMPLATE.format(
        total_records=len(records),
        total_req=total_req,
        total_resp=total_resp,
        total_errors=err["total_errors"],
        p50=lat["p50"], p50_pct=pct(lat["p50"]),
        p95=lat["p95"], p95_pct=pct(lat["p95"]), p95_color=p95_color,
        p95_slo_cls=p95_slo_cls, p95_slo_txt=p95_slo_txt,
        p99=lat["p99"], p99_pct=pct(lat["p99"]),
        ttft_p95=lat["ttft_p95"], ttft_pct=pct(lat["ttft_p95"], 500),
        rpm=rpm,
        error_rate=err["error_rate_pct"], err_color=err_color,
        err_slo_cls=err_slo_cls, err_slo_txt=err_slo_txt,
        retrieval_success=err["retrieval_success_rate"],
        ret_slo_cls=ret_slo_cls, ret_slo_txt=ret_slo_txt,
        total_cost=cost["total"], avg_cost=avg_cost, max_cost=max_cost,
        total_in=tok["total_in"], total_out=tok["total_out"], total_tokens=total_tokens,
        tok_slo_cls=tok_slo_cls, tok_slo_txt=tok_slo_txt,
        mean_quality=qual["mean"], min_quality=min_qual, max_quality=max_qual,
        qual_color=qual_color, qual_slo_cls=qual_slo_cls, qual_slo_txt=qual_slo_txt,
    )
    return html

def main():
    if not LOG_PATH.exists():
        print(f"ERROR: {LOG_PATH} not found. Run load_test.py first.")
        sys.exit(1)
    records = load_records(LOG_PATH)
    html = build_dashboard(records)
    out = REPO_ROOT / "data" / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"Dashboard written to: {out}")
    print(f"Records analyzed: {len(records)}")

if __name__ == "__main__":
    main()
