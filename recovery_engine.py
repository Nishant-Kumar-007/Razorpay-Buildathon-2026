"""
Recovery Engine — Multi-Vector Autonomous Revenue Recovery Core
Razorpay Buildathon 2026: AI Revenue Recovery Track

Covers all 4 core revenue leakage vectors:
1. Payment Degradation (Soft declines, switch timeouts, insufficient balance)
2. Checkout Drop-off (Cart abandonment with timed decay & Hinglish nudges)
3. Failed Subscriptions (UPI AutoPay & recurring card mandate sequencer)
4. B2B Receivables & Invoices (Overdue invoices with Promise-to-Pay PTP tracker)
"""

import json
import random
import sys
from datetime import datetime, timedelta

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 1. EXPANDED SYNTHETIC DATA GENERATOR (ALL 4 REVENUE VECTORS)
# -----------------------------------------------------------------------------

REVENUE_VECTORS = {
    "payment_failure": "Payment Degradation",
    "checkout_abandonment": "Checkout Drop-off",
    "subscription_failure": "Failed Subscriptions",
    "b2b_receivables": "B2B Receivables & Invoices",
    "fraud_risk": "Risk & Velocity Anomaly"
}

FAILURE_CONFIG = {
    # Vector 1: Payment Degradation
    "issuer_decline_soft": {
        "vector": "payment_failure",
        "diagnosis": "Temporary Bank Network Flap / Switch Drop",
        "confidence": "high",
        "is_retriable": True,
        "detail": "Customer issuer bank responded with soft decline (Error 05/91). Retriable with CBS recovery window."
    },
    "network_timeout": {
        "vector": "payment_failure",
        "diagnosis": "Gateway / NPCI Hop Latency Timeout",
        "confidence": "high",
        "is_retriable": True,
        "detail": "TCP socket timeout during 3DS / NPCI switch handshake. Transaction dropped in transit before settlement."
    },
    "insufficient_funds": {
        "vector": "payment_failure",
        "diagnosis": "Authorization Balance Deficit",
        "confidence": "high",
        "is_retriable": True,
        "detail": "Issuer declined due to lack of funds (Error 51). Retriable after 24h salary / account replenishment."
    },
    "issuer_decline_hard": {
        "vector": "payment_failure",
        "diagnosis": "Terminal Card Restriction / Fraud Blacklist",
        "confidence": "high",
        "is_retriable": False,
        "detail": "Card reported lost/stolen, KYC blocked, or canceled. Retries strictly prohibited by card networks."
    },
    # Vector 2: Checkout Abandonment
    "checkout_abandoned_fresh": {
        "vector": "checkout_abandonment",
        "diagnosis": "Pre-Authorization Drop-off (Within 24 Hours)",
        "confidence": "high",
        "is_retriable": True,
        "detail": "High-intent buyer dropped off at 2FA prompt. Fresh intent; eligible for dynamic 10% Hinglish nudge."
    },
    "checkout_abandoned_aged": {
        "vector": "checkout_abandonment",
        "diagnosis": "Dormant Checkout Drop-off (>48 Hours)",
        "confidence": "high",
        "is_retriable": True,
        "detail": "Cart abandoned over 48 hours ago. Intent degraded; standard payment link dispatch without urgency."
    },
    # Vector 3: Failed Subscriptions
    "upi_mandate_expired": {
        "vector": "subscription_failure",
        "diagnosis": "UPI AutoPay Mandate Token Expired",
        "confidence": "high",
        "is_retriable": True,
        "detail": "Pre-debit notification rejected by NPCI due to expired UMN mandate token. Needs 1-click re-auth link."
    },
    "card_recurring_token_revoked": {
        "vector": "subscription_failure",
        "diagnosis": "Recurring Card Tokenization Desync",
        "confidence": "high",
        "is_retriable": True,
        "detail": "RBI CoF token expired or card replaced. Customer must re-authenticate card with ₹2 verification debit."
    },
    # Vector 4: B2B Receivables & Invoices
    "invoice_overdue_30d": {
        "vector": "b2b_receivables",
        "diagnosis": "B2B Net-30 Grace Period Expiration",
        "confidence": "high",
        "is_retriable": True,
        "detail": "Commercial invoice unpaid 15-30 days past due. Dispatches automated receivables reminder with PTP options."
    },
    "invoice_overdue_60d_ptp_active": {
        "vector": "b2b_receivables",
        "diagnosis": "Active Debtor Promise-to-Pay (PTP) Commitment",
        "confidence": "high",
        "is_retriable": True,
        "detail": "Debtor logged verified Promise-to-Pay date within 7 days. Automated recovery paused per compliance rules."
    },
    "invoice_overdue_90d_default": {
        "vector": "b2b_receivables",
        "diagnosis": "Chronic Delinquency (>60 Days Past Due)",
        "confidence": "high",
        "is_retriable": False,
        "detail": "Exceeded all dunning cycles without payment or PTP. Escalated to Merchant Finance Legal & Recovery Ops."
    },
    # Risk & Velocity
    "duplicate_suspicious_pattern": {
        "vector": "fraud_risk",
        "diagnosis": "Card Testing / Rapid Velocity Bot Pattern",
        "confidence": "high",
        "is_retriable": False,
        "detail": "3+ sequential declines detected in 10 minutes across single device fingerprint. Quarantined for AML review."
    }
}

def generate_synthetic_dataset(seed=42):
    random.seed(seed)
    base_time = datetime(2026, 9, 5, 8, 30, 0)
    
    # 60 transactions with heavy representation of recoverable actions
    distribution = (
        ["issuer_decline_soft"] * 12 +
        ["network_timeout"] * 10 +
        ["insufficient_funds"] * 6 +
        ["checkout_abandoned_fresh"] * 12 +
        ["checkout_abandoned_aged"] * 4 +
        ["upi_mandate_expired"] * 6 +
        ["card_recurring_token_revoked"] * 3 +
        ["invoice_overdue_30d"] * 4 +
        ["invoice_overdue_60d_ptp_active"] * 1 +
        ["invoice_overdue_90d_default"] * 1 +
        ["issuer_decline_hard"] * 1 +
        ["duplicate_suspicious_pattern"] * 1
    )
    random.shuffle(distribution)
    
    customer_segments = ["SaaS Enterprise", "D2C Brand", "SMB Merchant", "High-Volume B2B", "B2C Consumer", "Fintech Pro"]
    customers = ["Reliance Retail", "Zomato Partner", "Flipkart Seller", "Urban Company", "Lenskart VIP", "Nykaa Merchant", "Zepto Depot", "Swiggy Instamart"]
    
    records = []
    for idx, ftype in enumerate(distribution, start=1):
        txn_id = f"txn_2026_{idx:03d}"
        cfg = FAILURE_CONFIG[ftype]
        vector = cfg["vector"]
        
        # Realistic high-recovery amounts
        if vector == "b2b_receivables":
            amount = random.choice([45000, 68000, 95000, 135000, 180000])
        elif vector == "checkout_abandonment":
            amount = random.choice([3999, 5499, 7999, 12999, 18500])
        elif vector == "subscription_failure":
            amount = random.choice([1999, 3499, 4999, 8999, 14999])
        elif vector == "fraud_risk":
            amount = random.choice([12000, 18000])
        elif ftype == "issuer_decline_hard":
            amount = random.choice([4200, 8900])
        else:
            amount = random.choice([3800, 6200, 11500, 18500, 24500])
            
        # Retries & metadata
        if vector == "b2b_receivables":
            retry_count = 0 if "30d" in ftype else (1 if "60d" in ftype else 3)
            recent_failures = retry_count
            cart_age_hours = 0.0
            ptp_date = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d") if "ptp_active" in ftype else None
            ptp_status = "active" if "ptp_active" in ftype else ("none" if "30d" in ftype else "breached")
        elif vector == "checkout_abandonment":
            retry_count = 0
            recent_failures = 1
            cart_age_hours = round(random.uniform(1.5, 18.0), 1) if "fresh" in ftype else round(random.uniform(50.0, 72.0), 1)
            ptp_date = None
            ptp_status = "none"
        elif vector == "fraud_risk":
            retry_count = 2
            recent_failures = 4
            cart_age_hours = 0.0
            ptp_date = None
            ptp_status = "none"
        else:
            retry_count = random.choice([0, 0, 0, 1])
            recent_failures = retry_count + 1
            cart_age_hours = 0.0
            ptp_date = None
            ptp_status = "none"
            
        time_offset = timedelta(minutes=idx * 7 + random.randint(1, 5))
        timestamp = (base_time + time_offset).strftime("%Y-%m-%d %H:%M:%S")
        
        records.append({
            "transaction_id": txn_id,
            "amount": amount,
            "failure_type": ftype,
            "vector": vector,
            "vector_label": REVENUE_VECTORS[vector],
            "timestamp": timestamp,
            "retry_count_so_far": retry_count,
            "recent_failure_count": recent_failures,
            "cart_age_hours": cart_age_hours,
            "ptp_status": ptp_status,
            "ptp_date": ptp_date,
            "customer_name": random.choice(customers),
            "customer_segment": random.choice(customer_segments)
        })
        
    return records

# -----------------------------------------------------------------------------
# 2. DETERMINISTIC POLICY ENGINE MATRIX
# -----------------------------------------------------------------------------

POLICY_RULES = [
    {
        "rule_id": "R-STOP-MAX-RETRY",
        "condition": "retry_count_so_far >= 2 and vector != 'b2b_receivables'",
        "allowed_action": "escalate_to_human_review",
        "human_readable_reason": "Anti-fatigue & network fee cap: 2 prior automated payment retries already executed. Further auto-retries cause cardholder complaints and incur scheme penalty fees.",
        "stopping_rule": "TERMINAL: Auto-retry execution halted; dossier forwarded to Merchant Ops queue."
    },
    {
        "rule_id": "R-STOP-HARD-DECLINE",
        "condition": "failure_type == 'issuer_decline_hard'",
        "allowed_action": "do_not_retry_flag_unrecoverable",
        "human_readable_reason": "Compliance stopping rule: Card reported lost, stolen, or blocked by issuer. Visa/Mastercard network mandates zero automated re-attempts.",
        "stopping_rule": "TERMINAL: Card fingerprint permanently suppressed from recovery pipeline."
    },
    {
        "rule_id": "R-FRAUD-VELOCITY",
        "condition": "failure_type == 'duplicate_suspicious_pattern'",
        "allowed_action": "escalate_to_human_review",
        "human_readable_reason": "Risk mitigation rule: High-frequency velocity anomaly (>3 rapid failures) detected across single fingerprint. Potential card testing bot.",
        "stopping_rule": "HALTED: Immediate quarantine; bypasses automated recovery to protect chargeback ratio."
    },
    {
        "rule_id": "R-NET-IMMEDIATE",
        "condition": "failure_type == 'network_timeout' and retry_count_so_far < 2",
        "allowed_action": "auto_retry_now",
        "human_readable_reason": "Transient network switch timeout. Automatically route through secondary banking route (HDFC/Axis) and re-attempt authorization immediately.",
        "stopping_rule": "Max 1 immediate retry; abort if unacknowledged."
    },
    {
        "rule_id": "R-SOFT-DELAY-1H",
        "condition": "failure_type == 'issuer_decline_soft' and retry_count_so_far < 2",
        "allowed_action": "auto_retry_delayed_1hr",
        "human_readable_reason": "Temporary issuer bank switch drop (Error 91). Queue automated retry for 1 hour to allow Core Banking Solution (CBS) recovery.",
        "stopping_rule": "Schedule 1 delayed run; abort if retry_count >= 2."
    },
    {
        "rule_id": "R-FUNDS-DELAY-24H",
        "condition": "failure_type == 'insufficient_funds' and retry_count_so_far < 1",
        "allowed_action": "auto_retry_delayed_24hr",
        "human_readable_reason": "Insufficient balance at debit. Schedule 24-hour delayed retry window to align with daily salary/account reload cycles.",
        "stopping_rule": "Single delayed window only; escalate if balance remains insufficient."
    },
    {
        "rule_id": "R-ABANDON-NUDGE",
        "condition": "failure_type == 'checkout_abandoned_fresh'",
        "allowed_action": "send_hinglish_nudge_with_discount",
        "human_readable_reason": "High-intent checkout drop within 24 hours. Dispatch dynamic Razorpay Payment Link paired with personalized 10% Hinglish WhatsApp nudge.",
        "stopping_rule": "Single nudge policy; no follow-up spam allowed."
    },
    {
        "rule_id": "R-ABANDON-STANDARD",
        "condition": "failure_type == 'checkout_abandoned_aged'",
        "allowed_action": "send_recovery_link_standard",
        "human_readable_reason": "Checkout drop over 48 hours old. Dispatch standard Razorpay payment link preserving cart items without urgency wording.",
        "stopping_rule": "Standard link lifetime 7 days."
    },
    {
        "rule_id": "R-MANDATE-RENEW",
        "condition": "failure_type == 'upi_mandate_expired'",
        "allowed_action": "send_mandate_renewal_link",
        "human_readable_reason": "UPI AutoPay mandate token lapsed. Issue Razorpay mandate re-auth link via WhatsApp/SMS to refresh mandate token in 1 click.",
        "stopping_rule": "Link expires in 72h; fallback to invoice cancellation if unfulfilled."
    },
    {
        "rule_id": "R-CARD-TOKEN-REAUTH",
        "condition": "failure_type == 'card_recurring_token_revoked'",
        "allowed_action": "send_card_reauth_link",
        "human_readable_reason": "RBI CoF recurring card token desynced. Send ₹2 verification re-auth link to establish fresh tokenization under RBI guidelines.",
        "stopping_rule": "Link lifetime 48 hours."
    },
    {
        "rule_id": "R-B2B-PTP-PAUSE",
        "condition": "failure_type == 'invoice_overdue_60d_ptp_active' or ptp_status == 'active'",
        "allowed_action": "pause_recovery_ptp_active",
        "human_readable_reason": "Compliance rule: Debtor has active verified Promise-to-Pay commitment. System strictly pauses automated dunning to honor agreement.",
        "stopping_rule": "PAUSED: Automatic dunning suppressed until commitment date passes."
    },
    {
        "rule_id": "R-B2B-CHASER-30D",
        "condition": "failure_type == 'invoice_overdue_30d'",
        "allowed_action": "send_b2b_receivables_chaser",
        "human_readable_reason": "Net-30 invoice overdue. Dispatch multi-channel receivables notice with 1-click Razorpay payment link and Promise-to-Pay capture portal.",
        "stopping_rule": "Dunning cycle 1 of 3."
    },
    {
        "rule_id": "R-B2B-LEGAL-ESCALATE",
        "condition": "failure_type == 'invoice_overdue_90d_default'",
        "allowed_action": "escalate_to_finance_collections",
        "human_readable_reason": "Chronic delinquency (>60 days past due). Dunning sequence exhausted; escalated to Commercial Collections & Finance Legal Ops.",
        "stopping_rule": "TERMINAL: Automated actions halted; legal collections initiated."
    }
]

def evaluate_policy(txn):
    ftype = txn["failure_type"]
    retry_count = txn["retry_count_so_far"]
    vector = txn["vector"]
    ptp_status = txn.get("ptp_status", "none")
    
    # 1. PTP Active Pause rule (B2B)
    if ptp_status == "active" or ftype == "invoice_overdue_60d_ptp_active":
        return POLICY_RULES[10]
        
    # 2. Hard stops
    if retry_count >= 2 and vector != "b2b_receivables":
        return POLICY_RULES[0]
    if ftype == "issuer_decline_hard":
        return POLICY_RULES[1]
    if ftype == "duplicate_suspicious_pattern":
        return POLICY_RULES[2]
        
    # 3. Vector-specific rules
    if ftype == "network_timeout":
        return POLICY_RULES[3]
    if ftype == "issuer_decline_soft":
        return POLICY_RULES[4]
    if ftype == "insufficient_funds":
        if retry_count < 1:
            return POLICY_RULES[5]
        return POLICY_RULES[0] # Escalate if already retried
        
    if ftype == "checkout_abandoned_fresh":
        return POLICY_RULES[6]
    if ftype == "checkout_abandoned_aged":
        return POLICY_RULES[7]
        
    if ftype == "upi_mandate_expired":
        return POLICY_RULES[8]
    if ftype == "card_recurring_token_revoked":
        return POLICY_RULES[9]
        
    if ftype == "invoice_overdue_30d":
        return POLICY_RULES[11]
    if ftype == "invoice_overdue_90d_default":
        return POLICY_RULES[12]
        
    # Default fallback
    return {
        "rule_id": "R-DEFAULT-TRIAGE",
        "condition": "unmatched_exception",
        "allowed_action": "escalate_to_human_review",
        "human_readable_reason": "Unmatched transaction profile. Escalated to triage queue.",
        "stopping_rule": "Manual review."
    }

# -----------------------------------------------------------------------------
# 3. VERNACULAR HINGLISH & VOICE SCRIPT GENERATOR
# -----------------------------------------------------------------------------

def generate_vernacular_intervention(txn, action):
    name = txn.get("customer_name", "Customer")
    amount = txn["amount"]
    amt_str = f"₹{amount:,}"
    txn_id = txn["transaction_id"]
    
    if action == "send_hinglish_nudge_with_discount":
        return {
            "channel": "WhatsApp + Voice IVR",
            "language": "Hinglish (Hindi + English)",
            "whatsapp_copy": f"Namaste {name} ji! 🙏 Aapka {amt_str} ka order cart me hold par hai. Abhi complete karein aur payein FLAT 10% instant savings! ⚡ Link: https://rzp.io/i/rec_{txn_id[-6:]} (Expires in 2 hrs)",
            "voice_script": f"Namaste! Yeh phone call aapke pending order ke baare me hai. Aapka {amt_str} ka cart ready hai. 1 dabaiye agar aap abhi 10% discount ke sath pay karna chahte hain, ya 2 dabaiye link WhatsApp par paane ke liye.",
            "ivr_intent": "high_intent_instant_checkout"
        }
    elif action == "send_mandate_renewal_link":
        return {
            "channel": "WhatsApp + SMS",
            "language": "Hinglish / English",
            "whatsapp_copy": f"Alert: Aapka recurring subscription payment ({amt_str}) mandate expire hone ki wajah se pause ho gaya hai. Service bina rukawat continue rakhne ke liye yahan se 1-click me re-authorize karein: https://rzp.io/m/rec_{txn_id[-6:]}",
            "voice_script": f"Namaste {name}. Aapka subscription auto-debit expire ho gaya hai. Kripya hamare WhatsApp message par diye gaye link par jakar UPI AutoPay dobara verify karein.",
            "ivr_intent": "subscription_mandate_reauth"
        }
    elif action == "send_b2b_receivables_chaser":
        return {
            "channel": "Email + Commercial WhatsApp",
            "language": "Professional English + Hindi Assist",
            "whatsapp_copy": f"Dear {name} Accounts Team, Invoice #{txn_id} for {amt_str} is currently 30 days overdue. Please settle via instant Razorpay B2B portal: https://rzp.io/inv/{txn_id[-6:]} or reply with your Promise-to-Pay (PTP) date.",
            "voice_script": f"Hello, this is Razorpay Automated Accounts Receivables calling for {name}. Your invoice {txn_id} of {amt_str} is due. Press 1 to pay via link, press 2 to record a Promise to Pay date.",
            "ivr_intent": "b2b_ptp_negotiation"
        }
    elif action == "pause_recovery_ptp_active":
        ptp_date = txn.get("ptp_date", "upcoming date")
        return {
            "channel": "System Hold",
            "language": "Internal Ops Note",
            "whatsapp_copy": f"Automated notices paused. Debtor promised settlement by {ptp_date}. System monitoring escrow account.",
            "voice_script": "No outbound calls permitted during active Promise-to-Pay window.",
            "ivr_intent": "ptp_moratorium_active"
        }
    else:
        return {
            "channel": "Standard System",
            "language": "English",
            "whatsapp_copy": f"Payment update for {txn_id}: Status {action}.",
            "voice_script": "Automated system notification.",
            "ivr_intent": "standard_system_event"
        }

# -----------------------------------------------------------------------------
# 4. SIMULATED RAZORPAY EXECUTION LAYER
# -----------------------------------------------------------------------------

SUCCESS_RATES = {
    "auto_retry_now": 0.88,
    "auto_retry_delayed_1hr": 0.82,
    "auto_retry_delayed_24hr": 0.75,
    "send_hinglish_nudge_with_discount": 0.84,
    "send_recovery_link_standard": 0.68,
    "send_mandate_renewal_link": 0.80,
    "send_card_reauth_link": 0.76,
    "send_b2b_receivables_chaser": 0.78,
    "pause_recovery_ptp_active": 0.0, # Paused, not recovered yet
    "escalate_to_human_review": 0.0,
    "escalate_to_finance_collections": 0.0,
    "do_not_retry_flag_unrecoverable": 0.0
}

def execute_recovery_action(txn, policy, idx):
    action = policy["allowed_action"]
    txn_id = txn["transaction_id"]
    amt_paisa = txn["amount"] * 100
    vernacular = generate_vernacular_intervention(txn, action)
    
    # REQUIREMENT: Exactly 1 deliberate execution failure handled gracefully
    if txn_id == "txn_2026_015" or (idx == 15 and action.startswith("auto_retry")):
        return {
            "execution_status": "execution_failed",
            "status_badge": "Execution Failed",
            "simulated_request": {
                "method": "POST",
                "endpoint": f"/v1/payments/{txn_id}/retry",
                "payload": {"gateway_route": "secondary_hdfc", "notes": {"agent": "recovery_agent"}}
            },
            "simulated_response": {
                "error": {
                    "code": "GATEWAY_TIMEOUT",
                    "description": "504 Gateway Timeout: Bank switch ACK dropped after 30000ms. Ambiguous authorization state.",
                    "source": "gateway",
                    "step": "payment_retry",
                    "reason": "upstream_partner_timeout"
                },
                "_audit_note": "SIMULATED (test-mode shape)"
            },
            "vernacular": vernacular,
            "recovered": False,
            "recovered_amount": 0,
            "graceful_summary": "Caught 504 Gateway Timeout. Policy stopping rule strictly enforced: blind re-attempts suppressed to prevent duplicate customer debits. Quarantined for async reconciliation."
        }
        
    # Escalations
    if action in ["escalate_to_human_review", "escalate_to_finance_collections"]:
        is_legal = action == "escalate_to_finance_collections"
        return {
            "execution_status": "escalated",
            "status_badge": "Escalated",
            "simulated_request": {
                "system_channel": "finance_legal_ops" if is_legal else "merchant_ops_queue",
                "action": "open_recovery_dossier",
                "payload": {"transaction_id": txn_id, "amount_inr": txn["amount"], "reason": policy["human_readable_reason"]}
            },
            "simulated_response": {
                "ticket_id": f"esc_{txn_id[-6:]}",
                "queue": "commercial_collections_tier1" if is_legal else "merchant_ops_priority",
                "status": "assigned_specialist",
                "sla_hours": 24 if is_legal else 2,
                "_audit_note": "SIMULATED (test-mode shape)"
            },
            "vernacular": vernacular,
            "recovered": False,
            "recovered_amount": 0,
            "graceful_summary": "Halted automated processing per policy stopping boundary. Human specialist intervention initiated."
        }
        
    # Unrecoverable / hard decline blocks
    if action == "do_not_retry_flag_unrecoverable":
        return {
            "execution_status": "unrecoverable",
            "status_badge": "Unrecoverable",
            "simulated_request": {
                "system_channel": "risk_engine",
                "action": "suppress_retries",
                "payload": {"transaction_id": txn_id, "category": "hard_decline_block"}
            },
            "simulated_response": {
                "suppression_id": f"sup_{txn_id[-6:]}",
                "status": "permanently_halted",
                "network_compliance": "visa_mastercard_mandate_enforced",
                "_audit_note": "SIMULATED (test-mode shape)"
            },
            "vernacular": vernacular,
            "recovered": False,
            "recovered_amount": 0,
            "graceful_summary": "Permanent stop applied. Retries suppressed to avoid merchant scheme penalties."
        }
        
    # PTP Active Moratorium
    if action == "pause_recovery_ptp_active":
        return {
            "execution_status": "ptp_paused",
            "status_badge": "PTP Active",
            "simulated_request": {
                "system_channel": "receivables_ledger",
                "action": "apply_ptp_moratorium",
                "payload": {"invoice_id": txn_id, "ptp_date": txn.get("ptp_date"), "status": "active"}
            },
            "simulated_response": {
                "moratorium_id": f"ptp_mor_{txn_id[-6:]}",
                "status": "dunning_suppressed",
                "hold_until": txn.get("ptp_date"),
                "_audit_note": "SIMULATED (test-mode shape)"
            },
            "vernacular": vernacular,
            "recovered": False,
            "recovered_amount": 0,
            "graceful_summary": "Automated dunning paused. Debtor commitment active; escrow monitoring active."
        }
        
    # Standard Recovery Actions
    p_success = SUCCESS_RATES.get(action, 0.35)
    is_success = random.random() < p_success
    
    if action in ["auto_retry_now", "auto_retry_delayed_1hr", "auto_retry_delayed_24hr"]:
        req = {
            "method": "POST",
            "endpoint": f"/v1/payments/{txn_id}/retry",
            "payload": {"amount": amt_paisa, "currency": "INR", "schedule": action.replace("auto_retry_", "")}
        }
        resp = {
            "id": f"pay_sim_{txn_id[-6:]}_{random.randint(100, 999)}",
            "entity": "payment",
            "amount": amt_paisa,
            "currency": "INR",
            "status": "captured" if is_success else "failed",
            "method": "card",
            "captured": is_success,
            "_audit_note": "SIMULATED (test-mode shape)"
        }
    elif "nudge" in action or "standard" in action:
        has_disc = "discount" in action
        req = {
            "method": "POST",
            "endpoint": "/v1/payment_links",
            "payload": {
                "amount": int(amt_paisa * 0.9) if has_disc else amt_paisa,
                "currency": "INR",
                "description": f"Checkout recovery for {txn_id}" + (" (10% Hinglish VIP Nudge)" if has_disc else ""),
                "customer": {"name": txn.get("customer_name", "Customer"), "contact": "+919876543210"}
            }
        }
        resp = {
            "id": f"plink_sim_{txn_id[-6:]}",
            "entity": "payment_link",
            "short_url": f"https://rzp.io/i/rec_{txn_id[-6:]}",
            "status": "paid" if is_success else "created",
            "amount_paid": txn["amount"] if is_success else 0,
            "_audit_note": "SIMULATED (test-mode shape)"
        }
    elif action == "send_mandate_renewal_link":
        req = {
            "method": "POST",
            "endpoint": "/v1/subscriptions/mandate_auth",
            "payload": {"customer_id": f"cust_{txn_id[-4:]}", "amount": amt_paisa, "auth_type": "upi_autopay"}
        }
        resp = {
            "id": f"mandate_sim_{txn_id[-6:]}",
            "entity": "subscription_mandate",
            "short_url": f"https://rzp.io/m/rec_{txn_id[-6:]}",
            "status": "authenticated" if is_success else "issued",
            "mandate_token": f"tok_upi_{random.randint(1000, 9999)}" if is_success else None,
            "_audit_note": "SIMULATED (test-mode shape)"
        }
    elif action == "send_card_reauth_link":
        req = {
            "method": "POST",
            "endpoint": "/v1/tokens/card/reauth",
            "payload": {"customer_id": f"cust_{txn_id[-4:]}", "auth_amount": 200, "currency": "INR"}
        }
        resp = {
            "id": f"tok_sim_{txn_id[-6:]}",
            "entity": "card_token",
            "status": "active" if is_success else "pending_customer_auth",
            "rbi_compliance": "tokenized_consent_verified",
            "_audit_note": "SIMULATED (test-mode shape)"
        }
    elif action == "send_b2b_receivables_chaser":
        req = {
            "method": "POST",
            "endpoint": f"/v1/invoices/{txn_id}/chase",
            "payload": {"amount": amt_paisa, "dunning_cycle": 1, "ptp_portal_enabled": True}
        }
        resp = {
            "id": f"inv_sim_{txn_id[-6:]}",
            "entity": "b2b_invoice",
            "short_url": f"https://rzp.io/inv/{txn_id[-6:]}",
            "status": "paid" if is_success else "dispatched_awaiting_remittance",
            "amount_settled": txn["amount"] if is_success else 0,
            "_audit_note": "SIMULATED (test-mode shape)"
        }
    else:
        req = {"action": action}
        resp = {"status": "unhandled", "_audit_note": "SIMULATED (test-mode shape)"}
        
    return {
        "execution_status": "recovered" if is_success else "attempted_unsettled",
        "status_badge": "Recovered" if is_success else "Unsettled",
        "simulated_request": req,
        "simulated_response": resp,
        "vernacular": vernacular,
        "recovered": is_success,
        "recovered_amount": txn["amount"] if is_success else 0,
        "graceful_summary": "Simulated Razorpay API test envelope executed."
    }

# -----------------------------------------------------------------------------
# 5. METRICS AGGREGATION ENGINE
# -----------------------------------------------------------------------------

def aggregate_batch_metrics(records):
    total_txns = len(records)
    total_at_risk = sum(r["amount"] for r in records)
    total_recovered = sum(r["recovered_amount"] for r in records)
    recovery_rate = round((total_recovered / total_at_risk * 100), 1) if total_at_risk > 0 else 0.0
    
    # Counts
    count_recovered = sum(1 for r in records if r["execution_status"] == "recovered")
    count_escalated = sum(1 for r in records if r["execution_status"] == "escalated")
    count_unrecoverable = sum(1 for r in records if r["execution_status"] == "unrecoverable")
    count_failed = sum(1 for r in records if r["execution_status"] == "execution_failed")
    count_ptp = sum(1 for r in records if r["execution_status"] == "ptp_paused")
    count_unsettled = sum(1 for r in records if r["execution_status"] == "attempted_unsettled")
    
    # Breakdown by revenue vector
    vector_breakdown = {}
    for r in records:
        vec = r["vector"]
        if vec not in vector_breakdown:
            vector_breakdown[vec] = {
                "vector": vec,
                "label": REVENUE_VECTORS.get(vec, vec),
                "total_count": 0,
                "recovered_count": 0,
                "amount_at_risk": 0,
                "amount_recovered": 0
            }
        v_entry = vector_breakdown[vec]
        v_entry["total_count"] += 1
        v_entry["amount_at_risk"] += r["amount"]
        if r["recovered"]:
            v_entry["recovered_count"] += 1
            v_entry["amount_recovered"] += r["recovered_amount"]
            
    for v_entry in vector_breakdown.values():
        at_risk = v_entry["amount_at_risk"]
        rec = v_entry["amount_recovered"]
        v_entry["recovery_rate_pct"] = round((rec / at_risk * 100), 1) if at_risk > 0 else 0.0
        
    return {
        "total_transactions": total_txns,
        "total_at_risk": total_at_risk,
        "total_recovered": total_recovered,
        "recovery_rate_pct": recovery_rate,
        "count_recovered": count_recovered,
        "count_escalated": count_escalated,
        "count_unrecoverable": count_unrecoverable,
        "count_execution_failed": count_failed,
        "count_ptp_active": count_ptp,
        "count_unsettled": count_unsettled,
        "vector_breakdown": list(vector_breakdown.values()),
        "ruleset": POLICY_RULES
    }

# -----------------------------------------------------------------------------
# 6. PIPELINE RUNNER & SINGLE SIMULATOR
# -----------------------------------------------------------------------------

def run_pipeline(seed=42):
    raw_records = generate_synthetic_dataset(seed=seed)
    processed = []
    
    for idx, txn in enumerate(raw_records, start=1):
        cfg = FAILURE_CONFIG.get(txn["failure_type"], {})
        policy = evaluate_policy(txn)
        exec_res = execute_recovery_action(txn, policy, idx)
        
        record = {
            **txn,
            "diagnosis": cfg.get("diagnosis", "Unclassified"),
            "diagnosis_detail": cfg.get("detail", ""),
            "confidence": cfg.get("confidence", "medium"),
            "rule_id": policy["rule_id"],
            "policy_action": policy["allowed_action"],
            "policy_reason": policy["human_readable_reason"],
            "stopping_rule": policy["stopping_rule"],
            "execution_status": exec_res["execution_status"],
            "status_badge": exec_res["status_badge"],
            "simulated_request": exec_res["simulated_request"],
            "simulated_response": exec_res["simulated_response"],
            "vernacular": exec_res["vernacular"],
            "recovered": exec_res["recovered"],
            "recovered_amount": exec_res["recovered_amount"],
            "graceful_summary": exec_res["graceful_summary"]
        }
        processed.append(record)
        
    metrics = aggregate_batch_metrics(processed)
    return processed, metrics

def simulate_custom_transaction(params):
    ftype = params.get("failure_type", "checkout_abandoned_fresh")
    cfg = FAILURE_CONFIG.get(ftype, FAILURE_CONFIG["checkout_abandoned_fresh"])
    amount = int(params.get("amount", 4999))
    retry_count = int(params.get("retry_count", 0))
    customer_name = params.get("customer_name", "Demo Merchant Partner")
    cart_age = float(params.get("cart_age_hours", 12.0))
    ptp_status = params.get("ptp_status", "none")
    ptp_date = params.get("ptp_date", None)
    
    txn = {
        "transaction_id": f"txn_custom_{random.randint(100, 999)}",
        "amount": amount,
        "failure_type": ftype,
        "vector": cfg["vector"],
        "vector_label": REVENUE_VECTORS[cfg["vector"]],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "retry_count_so_far": retry_count,
        "recent_failure_count": retry_count + 1,
        "cart_age_hours": cart_age,
        "ptp_status": ptp_status,
        "ptp_date": ptp_date,
        "customer_name": customer_name,
        "customer_segment": params.get("customer_segment", "SaaS Enterprise")
    }
    
    policy = evaluate_policy(txn)
    exec_res = execute_recovery_action(txn, policy, 99)
    
    return {
        **txn,
        "diagnosis": cfg["diagnosis"],
        "diagnosis_detail": cfg["detail"],
        "confidence": cfg["confidence"],
        "rule_id": policy["rule_id"],
        "policy_action": policy["allowed_action"],
        "policy_reason": policy["human_readable_reason"],
        "stopping_rule": policy["stopping_rule"],
        "execution_status": exec_res["execution_status"],
        "status_badge": exec_res["status_badge"],
        "simulated_request": exec_res["simulated_request"],
        "simulated_response": exec_res["simulated_response"],
        "vernacular": exec_res["vernacular"],
        "recovered": exec_res["recovered"],
        "recovered_amount": exec_res["recovered_amount"],
        "graceful_summary": exec_res["graceful_summary"]
    }

if __name__ == "__main__":
    records, metrics = run_pipeline()
    print("=" * 60)
    print("RECOVERY ENGINE (ALL 4 VECTORS) — SANITY CHECK")
    print("=" * 60)
    print(f"Total Transactions : {metrics['total_transactions']}")
    print(f"Total Revenue At Risk : ₹{metrics['total_at_risk']:,}")
    print(f"Total Recovered       : ₹{metrics['total_recovered']:,}")
    print(f"Recovery Rate         : {metrics['recovery_rate_pct']}%")
    print("Vector Breakdown:")
    for v in metrics["vector_breakdown"]:
        print(f" - {v['label']:25}: ₹{v['amount_recovered']:,} / ₹{v['amount_at_risk']:,} ({v['recovery_rate_pct']}%)")
    print("=" * 60)
