"""
Recovery Agent — Standalone Report Generator & CLI Runner
Generates self-contained recovery_report.html covering all 4 revenue recovery vectors.
"""

import json
import sys
from datetime import datetime

from recovery_engine import (
    FAILURE_CONFIG,
    POLICY_RULES,
    REVENUE_VECTORS,
    run_pipeline,
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def generate_multi_vector_html_report(records, metrics, output_filename="recovery_report.html"):
    total_recovered = metrics["total_recovered"]
    total_at_risk = metrics["total_at_risk"]
    recovery_rate = metrics["recovery_rate_pct"]
    total_txns = metrics["total_transactions"]
    
    # Sort breakdown by amount recovered
    sorted_breakdown = sorted(metrics["vector_breakdown"], key=lambda x: x["amount_recovered"], reverse=True)
    max_risk = max(b["amount_at_risk"] for b in sorted_breakdown) if sorted_breakdown else 1
    
    breakdown_rows = []
    for b in sorted_breakdown:
        label = b["label"]
        at_risk = b["amount_at_risk"]
        recovered = b["amount_recovered"]
        rate = b["recovery_rate_pct"]
        total_c = b["total_count"]
        rec_c = b["recovered_count"]
        at_risk_bar_pct = round((at_risk / max_risk) * 100)
        recovered_bar_pct = round((recovered / at_risk) * 100) if at_risk > 0 else 0
        
        breakdown_rows.append(f"""
        <div class="breakdown-row">
            <div class="breakdown-info">
                <span class="breakdown-label">{label}</span>
                <span class="breakdown-meta">{rec_c}/{total_c} won · ₹{at_risk:,} at risk · {rate}% rate</span>
            </div>
            <div class="breakdown-bar-container">
                <div class="bar-track" style="width: {at_risk_bar_pct}%;">
                    <div class="bar-fill" style="width: {recovered_bar_pct}%;"></div>
                </div>
            </div>
            <div class="breakdown-amount font-tabular">
                ₹{recovered:,}
            </div>
        </div>
        """)
    breakdown_html = "\n".join(breakdown_rows)
    
    # Vector mini cards
    mini_cards_html = "".join([
        f"""
        <div class="vector-mini-card">
            <div class="vector-mini-title">{v['label']}</div>
            <div class="vector-mini-recovered">₹{v['amount_recovered']:,}</div>
            <div class="vector-mini-meta">{v['recovered_count']}/{v['total_count']} won · {v['recovery_rate_pct']}%</div>
        </div>
        """ for v in sorted_breakdown
    ])
    
    # Policy table
    policy_rows = [
        f"""
        <tr>
            <td class="font-mono" style="color: var(--text-muted);">{r['rule_id']}</td>
            <td><code class="code-inline">{r['condition']}</code></td>
            <td class="font-mono">{r['allowed_action']}</td>
            <td style="color: var(--text-muted);">{r['stopping_rule']}</td>
        </tr>
        """ for r in POLICY_RULES
    ]
    policy_html = "\n".join(policy_rows)
    
    # Audit trail
    audit_rows = []
    for r in records:
        status = r["execution_status"]
        if status == "recovered":
            badge_class = "badge-sage"
        elif status == "escalated":
            badge_class = "badge-rust"
        elif status == "unrecoverable":
            badge_class = "badge-grey"
        elif status == "execution_failed":
            badge_class = "badge-rust-outline"
        elif status == "ptp_paused":
            badge_class = "badge-gold"
        else:
            badge_class = "badge-muted"
            
        req_json = json.dumps(r["simulated_request"], indent=2)
        resp_json = json.dumps(r["simulated_response"], indent=2)
        vern = r.get("vernacular", {})
        vern_copy = vern.get("whatsapp_copy", "")
        
        audit_rows.append(f"""
        <tr>
            <td class="font-mono txn-cell">{r['transaction_id']}</td>
            <td class="text-muted" style="white-space:nowrap;">{r.get('customer_name', 'Customer')}</td>
            <td class="font-tabular font-bold">₹{r['amount']:,}</td>
            <td>
                <div>{r['diagnosis']}</div>
                <div style="font-size:11px; color:var(--text-muted);">{r['vector_label']}</div>
            </td>
            <td class="font-mono rule-cell">{r['rule_id']}</td>
            <td class="action-cell">{r['policy_action']}</td>
            <td><span class="badge {badge_class}">{r['status_badge']}</span></td>
            <td>
                <details class="json-details">
                    <summary>View Payload & Intervention</summary>
                    <div class="json-box">
                        <div class="json-label">Simulated WhatsApp / Script</div>
                        <div style="font-size:11px; color:#E2DFD2; margin-bottom:6px;">{vern_copy}</div>
                        <div class="json-label">Simulated Request</div>
                        <pre><code>{req_json}</code></pre>
                        <div class="json-label" style="margin-top: 8px;">Simulated Response (Test Mode)</div>
                        <pre><code>{resp_json}</code></pre>
                    </div>
                </details>
            </td>
        </tr>
        """)
    audit_html = "\n".join(audit_rows)
    
    # Honest list
    honest_records = [r for r in records if r["execution_status"] in ["escalated", "unrecoverable", "execution_failed"]]
    honest_rows = []
    for r in honest_records:
        status = r["execution_status"]
        if status == "execution_failed":
            badge_class = "badge-rust-outline"
        elif status == "escalated":
            badge_class = "badge-rust"
        else:
            badge_class = "badge-grey"
        reason = r["graceful_summary"] if status == "execution_failed" else r["policy_reason"]
        
        honest_rows.append(f"""
        <tr>
            <td class="font-mono txn-cell">{r['transaction_id']}</td>
            <td class="font-tabular" style="color: var(--rust);">₹{r['amount']:,}</td>
            <td><span class="badge {badge_class}">{r['status_badge']}</span></td>
            <td class="font-mono rule-cell">{r['rule_id']}</td>
            <td>{reason}</td>
        </tr>
        """)
    honest_html = "\n".join(honest_rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recovery Agent — Multi-Vector Revenue Recovery Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;600&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
</head>
<body>

<div class="report-wrapper">
    <header class="report-header">
        <div class="report-brand">
            <div class="brand-title">Recovery Agent — Multi-Vector Revenue Recovery Audit</div>
            <div class="brand-meta">Batch 2026-Q3 · Deterministic Policy v2.0 · Live Web Server at http://localhost:8000</div>
        </div>
        <div class="header-actions">
            <a href="http://localhost:8000" class="btn-primary" target="_blank" style="text-decoration:none;">Open Live Interactive Demo</a>
        </div>
    </header>

    <section class="hero-section">
        <div class="hero-label">Total revenue recovered</div>
        <div class="hero-recovered" id="heroRecovered">₹0</div>
        <div class="hero-subtext">
            Recovered <span class="gold-text">₹{total_recovered:,}</span> of ₹{total_at_risk:,} at risk — a {recovery_rate}% recovery rate across {total_txns} multi-vector events.
        </div>
        <div class="hero-vectors-strip">
            {mini_cards_html}
        </div>
    </section>

    <section>
        <div class="section-header">
            <div>
                <h2>The policy</h2>
                <p class="section-intro">Every action below traces to one of these rules — nothing here is a black-box decision.</p>
            </div>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Rule ID</th>
                        <th>Condition</th>
                        <th>Action</th>
                        <th>Stopping rule</th>
                    </tr>
                </thead>
                <tbody>
                    {policy_html}
                </tbody>
            </table>
        </div>
    </section>

    <section>
        <div class="section-header">
            <div>
                <h2>Breakdown by failure vector</h2>
                <p class="section-intro">Capital recovered across all 4 revenue loss channels. Green bars indicate recovered funds, while figures in gold denote net recovered capital.</p>
            </div>
        </div>
        <div class="breakdown-list">
            {breakdown_html}
        </div>
    </section>

    <section>
        <div class="section-header">
            <div>
                <h2>Audit trail</h2>
                <p class="section-intro">Dense ledger of batch transactions across all 4 vectors paired with simulated Razorpay-shaped test envelopes and Hinglish recovery messages.</p>
            </div>
        </div>
        <div class="audit-container">
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>Transaction ID</th>
                        <th>Merchant</th>
                        <th>Amount</th>
                        <th>Diagnosis & Vector</th>
                        <th>Rule ID</th>
                        <th>Action</th>
                        <th>Status</th>
                        <th>Simulated Payload</th>
                    </tr>
                </thead>
                <tbody>
                    {audit_html}
                </tbody>
            </table>
        </div>
    </section>

    <section>
        <div class="section-header">
            <div>
                <h2>The honest list</h2>
                <p class="section-intro">These couldn't be recovered automatically, and the system correctly stopped rather than guess.</p>
            </div>
        </div>

        <div class="graceful-callout">
            <div class="graceful-callout-title">Handled gracefully: Upstream gateway timeout on txn_2026_015</div>
            <p>
                During automated retry execution, transaction <code class="code-inline">txn_2026_015</code> encountered an upstream banking switch 504 Gateway Timeout. Rather than blindly retrying and risking duplicate debits or card association rate-limits, the Recovery Agent immediately halted execution, quarantined the record, logged an audit dossier, and scheduled an asynchronous reconciliation check.
            </p>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Transaction ID</th>
                        <th>Exposure</th>
                        <th>Status</th>
                        <th>Rule Triggered</th>
                        <th>Audit Rationale</th>
                    </tr>
                </thead>
                <tbody>
                    {honest_html}
                </tbody>
            </table>
        </div>
    </section>

    <footer class="footer-note">
        <div>Razorpay Buildathon 2026 · AI Revenue Recovery Track · Live Prototype</div>
        <div>All payloads marked <span class="code-inline">SIMULATED (test-mode shape)</span></div>
    </footer>
</div>

<script>
    (function() {{
        const targetValue = {total_recovered};
        const duration = 1200;
        const counterEl = document.getElementById('heroRecovered');
        let startTime = null;

        function easeOutExpo(t) {{
            return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
        }}

        function step(timestamp) {{
            if (!startTime) startTime = timestamp;
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutExpo(progress);
            const currentValue = Math.floor(easedProgress * targetValue);

            counterEl.textContent = '₹' + currentValue.toLocaleString('en-IN');

            if (progress < 1) {{
                window.requestAnimationFrame(step);
            }} else {{
                counterEl.textContent = '₹' + targetValue.toLocaleString('en-IN');
            }}
        }}

        window.requestAnimationFrame(step);
    }})();
</script>

</body>
</html>
"""
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html)
    return output_filename

if __name__ == "__main__":
    records, metrics = run_pipeline(seed=42)
    out = generate_multi_vector_html_report(records, metrics, "recovery_report.html")
    print("=" * 60)
    print("RECOVERY AGENT — MULTI-VECTOR REPORT GENERATED")
    print("=" * 60)
    print(f"Total Transactions : {metrics['total_transactions']}")
    print(f"Total Revenue At Risk : ₹{metrics['total_at_risk']:,}")
    print(f"Total Recovered       : ₹{metrics['total_recovered']:,}")
    print(f"Aggregate Recovery Rate: {metrics['recovery_rate_pct']}%")
    print(f"Generated File         : {out}")
    print("Live Server            : http://localhost:8000")
    print("=" * 60)
