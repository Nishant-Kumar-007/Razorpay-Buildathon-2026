"""
Recovery Agent — Live Web Application Server
Serves the interactive web app UI and dynamic REST APIs.
Port: 8000
"""

import http.server
import json
import os
import socketserver
import sys
from urllib.parse import parse_qs, urlparse

from recovery_engine import (
    FAILURE_CONFIG,
    POLICY_RULES,
    REVENUE_VECTORS,
    run_pipeline,
    simulate_custom_transaction,
)

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# In-memory active batch state
CURRENT_RECORDS, CURRENT_METRICS = run_pipeline(seed=42)

class RecoveryApiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            
            if parsed.path == "/api/data":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                data = {
                    "metrics": CURRENT_METRICS,
                    "records": CURRENT_RECORDS,
                    "vectors": REVENUE_VECTORS,
                    "failure_configs": FAILURE_CONFIG,
                    "ruleset": POLICY_RULES
                }
                self.wfile.write(json.dumps(data).encode("utf-8"))
                return
                
            elif parsed.path == "/api/rules":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(POLICY_RULES).encode("utf-8"))
                return
                
            # Fallback to serving static files from public/
            return super().do_GET()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_POST(self):
        try:
            global CURRENT_RECORDS, CURRENT_METRICS
            parsed = urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            
            try:
                payload = json.loads(body) if body else {}
            except Exception:
                payload = {}

            if parsed.path == "/api/run-batch":
                seed = payload.get("seed", 42)
                CURRENT_RECORDS, CURRENT_METRICS = run_pipeline(seed=seed)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "metrics": CURRENT_METRICS,
                    "records": CURRENT_RECORDS
                }).encode("utf-8"))
                return

            elif parsed.path == "/api/simulate":
                sim_record = simulate_custom_transaction(payload)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "result": sim_record
                }).encode("utf-8"))
                return

            elif parsed.path == "/api/ptp/log":
                txn_id = payload.get("transaction_id")
                ptp_status = payload.get("ptp_status", "active")
                ptp_date = payload.get("ptp_date")
                
                # Find and update record in current batch if exists
                updated = None
                for r in CURRENT_RECORDS:
                    if r["transaction_id"] == txn_id:
                        r["ptp_status"] = ptp_status
                        r["ptp_date"] = ptp_date
                        if ptp_status == "active":
                            r["execution_status"] = "ptp_paused"
                            r["status_badge"] = "PTP Active"
                            r["policy_action"] = "pause_recovery_ptp_active"
                            r["rule_id"] = "R-B2B-PTP-PAUSE"
                            r["graceful_summary"] = f"Automated dunning paused. Debtor commitment active until {ptp_date}."
                        elif ptp_status == "breached":
                            r["execution_status"] = "escalated"
                            r["status_badge"] = "Escalated"
                            r["policy_action"] = "escalate_to_finance_collections"
                            r["rule_id"] = "R-B2B-LEGAL-ESCALATE"
                            r["graceful_summary"] = "Debtor breached promised commitment date. Auto-escalated to Collections Ops."
                        updated = r
                        break
                        
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "updated_record": updated
                }).encode("utf-8"))
                return

            self.send_error(404, "Endpoint not found")
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

class ReusableThreadingServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        # Suppress noisy client disconnection errors (WinError 10053, BrokenPipe)
        exc_type, exc_val = sys.exc_info()[:2]
        if exc_type in (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return
        super().handle_error(request, client_address)

def run_server():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with ReusableThreadingServer(("", PORT), RecoveryApiHandler) as httpd:
        print(f"Recovery Agent Web Server running at http://localhost:{PORT}")
        print(f"Serving UI from {PUBLIC_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()

