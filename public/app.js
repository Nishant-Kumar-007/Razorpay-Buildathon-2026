// Recovery Agent — Live Interactive Web Application Logic

const AppState = {
    metrics: {},
    records: [],
    vectors: {},
    ruleset: [],
    activeVector: 'all',
    searchQuery: ''
};

// Initialize application on load
document.addEventListener('DOMContentLoaded', () => {
    initMinimalLongTrail();
    fetchInitialData();
    setupEventListeners();
});

// Fetch batch data from local server API with auto-retries & static host fallback
async function fetchInitialData(retries = 2) {
    try {
        let res = await fetch('/api/data');
        if (!res.ok) {
            // Fallback for static deployment environments (e.g. GitHub Pages)
            res = await fetch('./data.json');
        }
        if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
        const data = await res.json();
        
        AppState.metrics = data.metrics;
        AppState.records = data.records;
        AppState.vectors = data.vectors;
        AppState.ruleset = data.ruleset;
        
        renderAll();
    } catch (err) {
        console.warn('Initial data fetch attempt failed:', err);
        if (retries > 0) {
            setTimeout(() => fetchInitialData(retries - 1), 400);
        }
    }
}

// Render all components
function renderAll() {
    renderHero();
    renderBarChart();
    renderPolicyTable();
    renderBreakdown();
    renderAuditTrail();
    renderFunnel();
}

// -----------------------------------------------------------------------------
// 1. HERO SECTION & CIRCULAR GAUGE ANIMATION
// -----------------------------------------------------------------------------

function renderHero() {
    const totalRec = AppState.metrics.total_recovered || 0;
    const totalRisk = AppState.metrics.total_at_risk || 0;
    const rate = AppState.metrics.recovery_rate_pct || 0;
    const totalTxns = AppState.metrics.total_transactions || 0;
    
    // Animate hero counter (easeOutExpo)
    animateHeroCounter(totalRec);
    
    // Subtext
    const subtextEl = document.getElementById('heroSubtext');
    if (subtextEl) {
        subtextEl.innerHTML = `Recovered <span class="gold-text">₹${totalRec.toLocaleString('en-IN')}</span> of ₹${totalRisk.toLocaleString('en-IN')} at risk — a ${rate}% recovery rate across ${totalTxns} multi-vector events.`;
    }
    
    // Animate Circular Gauge
    const gaugeCircle = document.getElementById('gaugeCircle');
    const gaugeRateText = document.getElementById('gaugeRateText');
    if (gaugeCircle && gaugeRateText) {
        const circumference = 2 * Math.PI * 58; // ~364.4
        const offset = circumference - (rate / 100) * circumference;
        gaugeCircle.style.strokeDasharray = `${circumference}`;
        gaugeCircle.style.strokeDashoffset = `${offset}`;
        gaugeRateText.textContent = `${rate}%`;
    }
    
    // Vector mini strip
    const stripEl = document.getElementById('heroVectorsStrip');
    if (stripEl && AppState.metrics.vector_breakdown) {
        stripEl.innerHTML = AppState.metrics.vector_breakdown.map(v => `
            <div class="tilt-card vector-mini-card">
                <div class="vector-mini-title">${v.label}</div>
                <div class="vector-mini-recovered">₹${v.amount_recovered.toLocaleString('en-IN')}</div>
                <div class="vector-mini-meta">${v.recovered_count}/${v.total_count} won · ${v.recovery_rate_pct}%</div>
            </div>
        `).join('');
    }
}

function animateHeroCounter(targetValue) {
    const counterEl = document.getElementById('heroRecovered');
    if (!counterEl) return;
    
    const duration = 1200;
    let startTime = null;
    
    function easeOutExpo(t) {
        return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
    }
    
    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(easeOutExpo(progress) * targetValue);
        
        counterEl.textContent = '₹' + current.toLocaleString('en-IN');
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            counterEl.textContent = '₹' + targetValue.toLocaleString('en-IN');
        }
    }
    
    window.requestAnimationFrame(step);
}

// -----------------------------------------------------------------------------
// 2. 3D BAR CHART CANVAS (RECOVERED SUCCESS VS UNRECOVERED DEFICIT)
// -----------------------------------------------------------------------------

function renderBarChart() {
    const canvas = document.getElementById('barChartCanvas');
    if (!canvas || !AppState.metrics.vector_breakdown) return;
    
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    canvas.width = rect.width * dpr;
    canvas.height = 250 * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = 250;
    
    ctx.clearRect(0, 0, width, height);
    
    const data = AppState.metrics.vector_breakdown;
    const maxVal = Math.max(...data.map(d => Math.max(d.amount_recovered, d.amount_at_risk - d.amount_recovered)), 1);
    
    const paddingLeft = 45;
    const paddingBottom = 45;
    const chartWidth = width - paddingLeft - 20;
    const chartHeight = height - paddingBottom - 20;
    
    const barGroupWidth = chartWidth / data.length;
    const barWidth = Math.min(28, barGroupWidth * 0.32);
    
    // Draw Grid Lines
    ctx.strokeStyle = 'rgba(224, 169, 109, 0.08)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = 20 + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(paddingLeft, y);
        ctx.lineTo(width - 20, y);
        ctx.stroke();
    }
    
    // Draw Bars (Green Success Dominates Red Deficit)
    data.forEach((item, index) => {
        const xCenter = paddingLeft + (index + 0.5) * barGroupWidth;
        const unrecovered = Math.max(item.amount_at_risk - item.amount_recovered, 0);
        const recovered = item.amount_recovered;
        
        // 1. RECOVERED GREEN BAR (TALL & DOMINANT)
        const recH = (recovered / maxVal) * chartHeight;
        const recY = 20 + (chartHeight - recH);
        const recX = xCenter - barWidth - 4;
        
        const gradGreen = ctx.createLinearGradient(0, recY, 0, recY + recH);
        gradGreen.addColorStop(0, '#34D399');
        gradGreen.addColorStop(0.3, '#10B981');
        gradGreen.addColorStop(1, '#065F46');
        
        ctx.shadowColor = 'rgba(16, 185, 129, 0.5)';
        ctx.shadowBlur = 10;
        ctx.fillStyle = gradGreen;
        ctx.beginPath();
        ctx.roundRect(recX, recY, barWidth, recH, [6, 6, 0, 0]);
        ctx.fill();
        ctx.shadowBlur = 0;
        
        ctx.strokeStyle = '#6EE7B7';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        
        // 2. UNRECOVERED RED BAR (SHORTER RESIDUAL DEFICIT)
        const riskH = (unrecovered / maxVal) * chartHeight;
        const riskY = 20 + (chartHeight - riskH);
        const riskX = xCenter + 4;
        
        const gradRed = ctx.createLinearGradient(0, riskY, 0, riskY + riskH);
        gradRed.addColorStop(0, '#F87171');
        gradRed.addColorStop(1, '#7F1D1D');
        
        ctx.fillStyle = gradRed;
        ctx.beginPath();
        ctx.roundRect(riskX, riskY, barWidth, riskH, [4, 4, 0, 0]);
        ctx.fill();
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Labels
        ctx.fillStyle = '#C9B29B';
        ctx.font = '600 11px Inter, sans-serif';
        ctx.textAlign = 'center';
        
        const shortName = item.label.split(' ')[0];
        ctx.fillText(shortName, xCenter, height - 16);
    });
}

// -----------------------------------------------------------------------------
// 3. FUNNEL & STATS
// -----------------------------------------------------------------------------

function renderFunnel() {
    const riskEl = document.getElementById('funnelRisk');
    const eventsEl = document.getElementById('funnelEvents');
    const actionsEl = document.getElementById('funnelActions');
    const recEl = document.getElementById('funnelRecovered');
    
    if (riskEl && AppState.metrics.total_at_risk) {
        riskEl.textContent = `₹${AppState.metrics.total_at_risk.toLocaleString('en-IN')}`;
    }
    if (eventsEl && AppState.metrics.total_transactions) {
        eventsEl.textContent = `${AppState.metrics.total_transactions} Events`;
    }
    if (actionsEl && AppState.records) {
        const attempted = AppState.records.filter(r => ['recovered', 'attempted_unsettled'].includes(r.execution_status)).length;
        actionsEl.textContent = `${attempted} Dispatched`;
    }
    if (recEl && AppState.metrics.total_recovered) {
        recEl.textContent = `₹${AppState.metrics.total_recovered.toLocaleString('en-IN')}`;
    }
}

// -----------------------------------------------------------------------------
// 4. THE POLICY RULES TABLE
// -----------------------------------------------------------------------------

function renderPolicyTable() {
    const tbody = document.getElementById('policyTableBody');
    if (!tbody || !AppState.ruleset) return;
    
    tbody.innerHTML = AppState.ruleset.map(r => `
        <tr>
            <td class="font-mono" style="color: var(--desert-sand-muted); font-weight:600;">${r.rule_id}</td>
            <td><code class="code-inline">${escapeHtml(r.condition)}</code></td>
            <td class="font-mono">${escapeHtml(r.allowed_action)}</td>
            <td style="color: var(--desert-sand-muted);">${escapeHtml(r.stopping_rule)}</td>
        </tr>
    `).join('');
}

// -----------------------------------------------------------------------------
// 5. BREAKDOWN BY VECTOR
// -----------------------------------------------------------------------------

function renderBreakdown() {
    const container = document.getElementById('breakdownList');
    if (!container || !AppState.metrics.vector_breakdown) return;
    
    const sorted = [...AppState.metrics.vector_breakdown].sort((a, b) => b.amount_recovered - a.amount_recovered);
    const maxRisk = Math.max(...sorted.map(s => s.amount_at_risk), 1);
    
    container.innerHTML = sorted.map(v => {
        const atRiskBar = Math.round((v.amount_at_risk / maxRisk) * 100);
        const fillBar = v.amount_at_risk > 0 ? Math.round((v.amount_recovered / v.amount_at_risk) * 100) : 0;
        
        return `
            <div class="tilt-card breakdown-row">
                <div class="breakdown-info">
                    <span class="breakdown-label" style="font-weight:600;">${v.label}</span>
                    <span class="breakdown-meta">${v.recovered_count}/${v.total_count} won · ₹${v.amount_at_risk.toLocaleString('en-IN')} at risk · ${v.recovery_rate_pct}% rate</span>
                </div>
                <div class="breakdown-bar-container">
                    <div class="bar-track" style="width: ${atRiskBar}%;">
                        <div class="bar-fill" style="width: ${fillBar}%;"></div>
                    </div>
                </div>
                <div class="breakdown-amount">
                    ₹${v.amount_recovered.toLocaleString('en-IN')}
                </div>
            </div>
        `;
    }).join('');
}

// -----------------------------------------------------------------------------
// 6. AUDIT TRAIL
// -----------------------------------------------------------------------------

function renderAuditTrail() {
    const tbody = document.getElementById('auditTableBody');
    if (!tbody) return;
    
    let filtered = AppState.records;
    
    if (AppState.activeVector !== 'all') {
        filtered = filtered.filter(r => r.vector === AppState.activeVector);
    }
    
    if (AppState.searchQuery.trim()) {
        const q = AppState.searchQuery.toLowerCase();
        filtered = filtered.filter(r => 
            r.transaction_id.toLowerCase().includes(q) ||
            (r.customer_name && r.customer_name.toLowerCase().includes(q)) ||
            r.diagnosis.toLowerCase().includes(q) ||
            r.rule_id.toLowerCase().includes(q) ||
            r.status_badge.toLowerCase().includes(q)
        );
    }
    
    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 32px; color: var(--desert-sand-muted);">No records found matching criteria.</td></tr>`;
        return;
    }
    
    tbody.innerHTML = filtered.map(r => {
        const badgeClass = getBadgeClass(r.execution_status);
        const reqJson = JSON.stringify(r.simulated_request, null, 2);
        const respJson = JSON.stringify(r.simulated_response, null, 2);
        
        let ptpActionHtml = '';
        if (r.vector === 'b2b_receivables') {
            if (r.ptp_status === 'active') {
                ptpActionHtml = `<button class="btn-audio" onclick="simulatePtpBreach('${r.transaction_id}')" style="margin-top:4px; font-size:10px; padding:3px 8px;">Simulate Breach</button>`;
            } else if (r.ptp_status !== 'breached') {
                ptpActionHtml = `<button class="btn-audio" onclick="logPtpCommitment('${r.transaction_id}')" style="margin-top:4px; font-size:10px; padding:3px 8px;">Log PTP (7d)</button>`;
            }
        }
        
        return `
            <tr>
                <td class="font-mono txn-cell">${r.transaction_id}</td>
                <td class="text-muted" style="white-space:nowrap;">${escapeHtml(r.customer_name || 'Merchant Partner')}</td>
                <td class="font-tabular font-bold">₹${r.amount.toLocaleString('en-IN')}</td>
                <td>
                    <div>${escapeHtml(r.diagnosis)}</div>
                    <div style="font-size:11px; color:var(--desert-sand-muted);">${r.vector_label}</div>
                </td>
                <td class="font-mono rule-cell" style="color:var(--gold);">${r.rule_id}</td>
                <td class="action-cell">
                    <div>${escapeHtml(r.policy_action)}</div>
                    ${ptpActionHtml}
                </td>
                <td><span class="badge ${badgeClass}">${r.status_badge}</span></td>
                <td>
                    <details class="json-details">
                        <summary>View Envelope</summary>
                        <div class="json-box">
                            <div class="json-label">Request</div>
                            <pre><code>${escapeHtml(reqJson)}</code></pre>
                            <div class="json-label" style="margin-top: 8px;">Response</div>
                            <pre><code>${escapeHtml(respJson)}</code></pre>
                        </div>
                    </details>
                </td>
            </tr>
        `;
    }).join('');
}

// -----------------------------------------------------------------------------
// 7. THE HONEST LIST
// -----------------------------------------------------------------------------

function renderHonestList() {
    const tbody = document.getElementById('honestTableBody');
    if (!tbody) return;
    
    const honestRecords = AppState.records.filter(r => 
        ['escalated', 'unrecoverable', 'execution_failed'].includes(r.execution_status)
    );
    
    tbody.innerHTML = honestRecords.map(r => {
        const badgeClass = getBadgeClass(r.execution_status);
        const reason = r.execution_status === 'execution_failed' ? r.graceful_summary : r.policy_reason;
        
        return `
            <tr>
                <td class="font-mono txn-cell">${r.transaction_id}</td>
                <td class="font-tabular" style="color: var(--rust);">₹${r.amount.toLocaleString('en-IN')}</td>
                <td><span class="badge ${badgeClass}">${r.status_badge}</span></td>
                <td class="font-mono rule-cell">${r.rule_id}</td>
                <td>${escapeHtml(reason)}</td>
            </tr>
        `;
    }).join('');
}

function getBadgeClass(status) {
    if (status === 'recovered') return 'badge-sage';
    if (status === 'escalated') return 'badge-rust';
    if (status === 'unrecoverable') return 'badge-grey';
    if (status === 'execution_failed') return 'badge-rust-outline';
    if (status === 'ptp_paused') return 'badge-gold';
    return 'badge-muted';
}

// -----------------------------------------------------------------------------
// 8. MINIMAL LONG PARTICLES TRAIL ENGINE
// -----------------------------------------------------------------------------

function initMinimalLongTrail() {
    const canvas = document.getElementById('trailCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    
    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });
    
    const particles = [];
    const colors = ['#E0A96D', '#FFB703', '#D48139', '#10B981'];
    
    let lastScrollY = window.scrollY;
    
    // Spawn only 1-2 minimal long-lived particles on scroll
    window.addEventListener('scroll', () => {
        const delta = Math.abs(window.scrollY - lastScrollY);
        lastScrollY = window.scrollY;
        
        if (delta > 8 && particles.length < 25) {
            particles.push({
                x: Math.random() * width,
                y: height * 0.95 + Math.random() * 20,
                vx: (Math.random() - 0.5) * 0.6,
                vy: -(Math.random() * 1.2 + 0.8),
                size: Math.random() * 2 + 1,
                color: colors[Math.floor(Math.random() * colors.length)],
                alpha: 0.8,
                decay: 0.0035 // Long, slow graceful fade
            });
        }
    }, { passive: true });
    
    function animate() {
        ctx.clearRect(0, 0, width, height);
        
        for (let i = particles.length - 1; i >= 0; i--) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.alpha -= p.decay;
            
            if (p.alpha <= 0 || p.y < -10) {
                particles.splice(i, 1);
                continue;
            }
            
            ctx.save();
            ctx.globalAlpha = p.alpha;
            ctx.fillStyle = p.color;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

// -----------------------------------------------------------------------------
// 9. EVENT LISTENERS & INDIAN VOICE SPEECH
// -----------------------------------------------------------------------------

function setupEventListeners() {
    // Vector Filter Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            AppState.activeVector = e.target.getAttribute('data-vector');
            renderAuditTrail();
        });
    });
    
    // Search input
    const searchInput = document.getElementById('auditSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            AppState.searchQuery = e.target.value;
            renderAuditTrail();
        });
    }
    
    // Main dedicated Indian Voice Button
    const mainVoiceBtn = document.getElementById('btnMainVoicePlay');
    if (mainVoiceBtn) {
        mainVoiceBtn.addEventListener('click', () => {
            const script = `Namaste! Yeh phone call aapke pending order ke baare me hai. Aapka 14,500 rupees ka cart ready hai. 1 dabaiye agar aap abhi 10% discount ke sath pay karna chahte hain, ya 2 dabaiye link WhatsApp par paane ke liye.`;
            playIndianVoiceSpeech(script);
        });
    }
    
    // Run new batch button
    const runBatchBtn = document.getElementById('btnRunBatch');
    if (runBatchBtn) {
        runBatchBtn.addEventListener('click', async () => {
            runBatchBtn.disabled = true;
            runBatchBtn.textContent = 'Processing Batch...';
            try {
                const randomSeed = Math.floor(Math.random() * 10000);
                const res = await fetch('/api/run-batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ seed: randomSeed })
                });
                const data = await res.json();
                AppState.metrics = data.metrics;
                AppState.records = data.records;
                renderAll();
            } catch (err) {
                console.error('Batch run error:', err);
            } finally {
                runBatchBtn.disabled = false;
                runBatchBtn.textContent = 'Run Live Batch';
            }
        });
    }
    
    // Simulator Form
    const simForm = document.getElementById('sandboxForm');
    if (simForm) {
        simForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('btnSimulateSubmit');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Evaluating Policy...';
            
            const payload = {
                failure_type: document.getElementById('simFailureType').value,
                amount: parseInt(document.getElementById('simAmount').value, 10),
                retry_count: parseInt(document.getElementById('simRetryCount').value, 10),
                customer_name: document.getElementById('simCustomerName').value || 'Apex Enterprises',
                customer_segment: document.getElementById('simSegment').value
            };
            
            try {
                const res = await fetch('/api/simulate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                displaySimulationResult(data.result);
                
                // Prepend to active ledger
                AppState.records.unshift(data.result);
                renderAuditTrail();
            } catch (err) {
                console.error('Simulation error:', err);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '⚡ Execute Recovery';
            }
        });
    }
}

function displaySimulationResult(res) {
    const panel = document.getElementById('sandboxOutputPanel');
    if (!panel) return;
    panel.style.display = 'block';
    
    document.getElementById('resTxnId').textContent = res.transaction_id;
    document.getElementById('resDiagnosis').textContent = res.diagnosis;
    document.getElementById('resRuleId').textContent = res.rule_id;
    document.getElementById('resAction').textContent = res.policy_action;
    
    const badgeEl = document.getElementById('resStatusBadge');
    badgeEl.textContent = res.status_badge;
    badgeEl.className = 'badge ' + getBadgeClass(res.execution_status);
    
    document.getElementById('resStoppingRule').textContent = res.stopping_rule;
    document.getElementById('resReqJson').textContent = JSON.stringify(res.simulated_request, null, 2);
    document.getElementById('resRespJson').textContent = JSON.stringify(res.simulated_response, null, 2);
    
    const vern = res.vernacular || {};
    const copyText = vern.whatsapp_copy || 'N/A';
    // Make simulated links clickable
    const formattedCopy = escapeHtml(copyText).replace(/(https:\/\/rzp\.io\/i\/[a-zA-Z0-9_]+)/g, `<a href="javascript:void(0)" class="sim-payment-link" onclick="openSimulatedCheckoutModal('${escapeHtml(res.transaction_id)}', ${res.amount}, '${escapeHtml(res.customer_name)}')">$1</a>`);
    document.getElementById('resWhatsappCopy').innerHTML = formattedCopy;
    document.getElementById('resVoiceScript').textContent = vern.voice_script || 'N/A';
    
    const speakBtn = document.getElementById('btnSpeakVoice');
    if (speakBtn) {
        speakBtn.onclick = () => {
            playIndianVoiceSpeech(vern.voice_script);
        };
    }
    
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// -----------------------------------------------------------------------------
// 10. AUTHENTIC INDIAN VOICE SPEECH SYNTHESIS ENGINE & TELECOM CHIME
// -----------------------------------------------------------------------------

let cachedVoices = [];
function initVoices() {
    if (!('speechSynthesis' in window)) return;
    cachedVoices = window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
        cachedVoices = window.speechSynthesis.getVoices();
    };
}
initVoices();

function playIvrChime() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const now = ctx.currentTime;
        
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gain = ctx.createGain();
        
        osc1.type = 'sine';
        osc2.type = 'sine';
        osc1.frequency.setValueAtTime(440, now);
        osc2.frequency.setValueAtTime(480, now);
        
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        
        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(ctx.destination);
        
        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 0.35);
        osc2.stop(now + 0.35);
    } catch (e) {
        // audio context fallback
    }
}

function playIndianVoiceSpeech(text) {
    if (!('speechSynthesis' in window)) {
        alert('Browser Speech Synthesis is not supported in this browser.');
        return;
    }
    
    // Play instant audible IVR telecom chime through speakers
    playIvrChime();
    
    const waveEl = document.getElementById('waveBarsVisual');
    const mainVoiceBtn = document.getElementById('btnMainVoicePlay');
    
    if (waveEl) waveEl.classList.remove('voice-wave-inactive');
    if (mainVoiceBtn) mainVoiceBtn.innerHTML = '🔊 Speaking (Hinglish IVR)...';
    
    if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
    }
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.94;
    utterance.pitch = 1.05;
    
    const voices = cachedVoices.length ? cachedVoices : window.speechSynthesis.getVoices();
    const indianVoice = voices.find(v => 
        v.lang === 'en-IN' || 
        v.lang.includes('hi') || 
        v.name.includes('India') || 
        v.name.includes('Indian') ||
        v.name.includes('Ravi') ||
        v.name.includes('Heera') ||
        v.name.includes('Neerja') ||
        v.name.includes('Prabhat')
    ) || voices.find(v => v.lang.startsWith('en')) || voices[0];
    
    if (indianVoice) {
        utterance.voice = indianVoice;
    }
    
    const resetUi = () => {
        if (waveEl) waveEl.classList.add('voice-wave-inactive');
        if (mainVoiceBtn) mainVoiceBtn.innerHTML = '🔊 Play Indian Voice Call (Hinglish IVR)';
    };
    
    utterance.onend = resetUi;
    utterance.onerror = resetUi;
    
    window.speechSynthesis.speak(utterance);
}

// -----------------------------------------------------------------------------
// 11. INTERACTIVE SIMULATED RAZORPAY CHECKOUT MODAL
// -----------------------------------------------------------------------------

function openSimulatedCheckoutModal(recId, amount = 14500, customer = 'Rahul Sharma') {
    let modal = document.getElementById('simCheckoutModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'simCheckoutModal';
        modal.className = 'rzp-modal-overlay';
        document.body.appendChild(modal);
    }
    
    const discounted = Math.round(amount * 0.9);
    
    modal.innerHTML = `
        <div class="rzp-modal-card">
            <div class="rzp-modal-header">
                <div class="rzp-brand-logo">
                    <span style="color:#0C2340; font-weight:800; font-size:18px; letter-spacing:-0.5px;">Razorpay</span>
                    <span class="rzp-test-tag">SIMULATED CHECKOUT</span>
                </div>
                <button type="button" class="rzp-close-btn" onclick="closeSimulatedCheckoutModal()">&times;</button>
            </div>
            <div class="rzp-modal-body" id="rzpModalBody">
                <div class="rzp-merchant-title">Apex E-Commerce Store</div>
                <div class="rzp-order-info">Order Ref: <strong>${escapeHtml(recId)}</strong> · Customer: <strong>${escapeHtml(customer)}</strong></div>
                
                <div class="rzp-price-box">
                    <div>
                        <div class="rzp-price-label">Original Cart Value:</div>
                        <div style="text-decoration: line-through; color: #888;">₹${amount.toLocaleString('en-IN')}</div>
                    </div>
                    <div style="text-align: right;">
                        <span class="rzp-discount-badge">10% NUDGE SAVINGS</span>
                        <div class="rzp-final-price">₹${discounted.toLocaleString('en-IN')}</div>
                    </div>
                </div>

                <div class="rzp-method-selector">
                    <div class="rzp-method active">
                        <strong>⚡ Razorpay Fast UPI</strong>
                        <span style="font-size: 11px; color: #059669;">Auto-selected from failed session</span>
                    </div>
                </div>

                <button type="button" class="rzp-pay-btn" id="btnRzpConfirmPay" onclick="confirmSimulatedPayment('${escapeHtml(recId)}', ${discounted})">
                    Pay ₹${discounted.toLocaleString('en-IN')} Now
                </button>
                <div style="font-size: 11px; text-align: center; color: #888; margin-top: 10px;">
                    Simulated Sandbox Payment Flow · Razorpay Buildathon 2026
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
}

function closeSimulatedCheckoutModal() {
    const modal = document.getElementById('simCheckoutModal');
    if (modal) modal.style.display = 'none';
}

function confirmSimulatedPayment(recId, paidAmount) {
    const bodyEl = document.getElementById('rzpModalBody');
    if (!bodyEl) return;
    
    playIvrChime();
    
    bodyEl.innerHTML = `
        <div style="text-align:center; padding: 25px 10px;">
            <div class="rzp-success-checkmark">✓</div>
            <h3 style="color:#0C2340; margin: 12px 0 6px 0; font-size: 20px;">Payment Captured Successfully!</h3>
            <p style="color:#059669; font-weight: 700; font-size: 16px; margin: 0 0 10px 0;">₹${paidAmount.toLocaleString('en-IN')} Recovered</p>
            <p style="font-size: 12px; color: #666; font-family: var(--font-mono); margin-bottom: 20px;">
                Payment ID: pay_sim_${Math.random().toString(36).substring(2, 10)}<br>
                Channel: WhatsApp Hinglish Recovery Nudge<br>
                Status: Gated Policy Closed-Loop Complete
            </p>
            <button type="button" class="rzp-pay-btn" style="background:#059669;" onclick="closeSimulatedCheckoutModal()">
                Return to Dashboard
            </button>
        </div>
    `;
    
    // Animate hero counter update to reflect the newly won revenue live!
    if (AppState.metrics) {
        AppState.metrics.total_recovered = (AppState.metrics.total_recovered || 0) + paidAmount;
        const heroEl = document.getElementById('heroRecovered');
        if (heroEl) {
            heroEl.textContent = '₹' + AppState.metrics.total_recovered.toLocaleString('en-IN');
        }
    }
}

// Promise-to-Pay Actions
async function logPtpCommitment(txnId) {
    const ptpDate = prompt('Enter debtor promised settlement date (YYYY-MM-DD):', '2026-09-12');
    if (!ptpDate) return;
    
    try {
        const res = await fetch('/api/ptp/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: txnId, ptp_status: 'active', ptp_date: ptpDate })
        });
        await res.json();
        alert(`Promise-to-Pay logged for ${txnId}! Automated recovery dunning paused until ${ptpDate}.`);
        fetchInitialData();
    } catch (err) {
        console.error('Failed to log PTP:', err);
    }
}

async function simulatePtpBreach(txnId) {
    if (!confirm(`Debtor failed to remit payment by promised date. Simulate breach and trigger legal/collections escalation?`)) return;
    
    try {
        const res = await fetch('/api/ptp/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: txnId, ptp_status: 'breached' })
        });
        await res.json();
        alert(`PTP breach recorded for ${txnId}. Record escalated to Finance Collections Ops.`);
        fetchInitialData();
    } catch (err) {
        console.error('Failed to simulate PTP breach:', err);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
