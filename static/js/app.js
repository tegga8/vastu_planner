// ==================== APP ====================
const App = {
    data: null,
    currentTab: 'design',

    init() {
        this.bindNav();
        this.bindGenerate();
        this.bindExamples();
        this.bindDownload();
        this.checkAIStatus();
        this.loadGuide();
    },

    bindNav() {
        document.querySelectorAll('.nav-item').forEach(el => {
            el.addEventListener('click', () => this.switchTab(el.dataset.tab));
        });
    },

    switchTab(tab) {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const ni = document.querySelector(`.nav-item[data-tab="${tab}"]`);
        if (ni) ni.classList.add('active');
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        const tc = document.getElementById(`tab-${tab}`);
        if (tc) tc.classList.add('active');
        this.currentTab = tab;
    },

    bindGenerate() {
        document.getElementById('generate-btn').addEventListener('click', () => this.generate());
        document.getElementById('prompt-input').addEventListener('keydown', e => {
            if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault();
                this.generate();
            }
        });
    },

    bindExamples() {
        document.querySelectorAll('.example-chip').forEach(el => {
            el.addEventListener('click', () => {
                document.getElementById('prompt-input').value = el.dataset.prompt;
                this.generate();
            });
        });
    },

    bindDownload() {
        document.getElementById('download-svg').addEventListener('click', () => {
            if (!this.data?.svg) return;
            const blob = new Blob([this.data.svg], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'Vastu_Floor_Plan.svg';
            document.body.appendChild(a); a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    },

    async generate() {
        const prompt = document.getElementById('prompt-input').value.trim();
        if (!prompt) {
            document.getElementById('prompt-input').focus();
            document.getElementById('prompt-input').style.borderColor = '#E17055';
            setTimeout(() => document.getElementById('prompt-input').style.borderColor = '', 1500);
            return;
        }

        // Show loading
        document.getElementById('design-loading').style.display = 'flex';
        document.getElementById('generate-btn').disabled = true;
        document.getElementById('generate-btn').textContent = '⏳ Generating...';

        this._showStep('step-parse');

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });
            const data = await res.json();

            this._showStep('step-layout');
            await sleep(300);
            this._showStep('step-render');
            await sleep(300);
            this._showStep('step-image');

            this.data = data;
            this.displayResults(data);

            document.getElementById('design-loading').style.display = 'none';
            document.getElementById('generate-btn').disabled = false;
            document.getElementById('generate-btn').innerHTML = '<span class="btn-icon">✨</span> Generate Plan';

            // Show badge and switch to floorplan
            document.getElementById('plan-badge').style.display = 'flex';
            setTimeout(() => this.switchTab('floorplan'), 800);

        } catch (err) {
            document.getElementById('design-loading').style.display = 'none';
            document.getElementById('generate-btn').disabled = false;
            document.getElementById('generate-btn').innerHTML = '<span class="btn-icon">✨</span> Generate Plan';
            this.toast('⚠️ Error generating plan. Is the server running?');
        }
    },

    displayResults(data) {
        // Floor plan
        if (data.svg) {
            document.getElementById('fp-svg').innerHTML = data.svg;
            document.getElementById('fp-content').style.display = 'block';
            document.getElementById('fp-empty').style.display = 'none';
            document.getElementById('fp-loading').style.display = 'none';
            document.getElementById('fp-subtitle').textContent =
                `Source: ${data.source || 'algorithmic'} · ${data.rooms_list?.length || 0} rooms · Score: ${data.overall_score}/10`;
            document.getElementById('download-svg').disabled = false;
        }

        // Elevation
        if (data.elevation_svg) {
            document.getElementById('elev-svg').innerHTML = data.elevation_svg;
            document.getElementById('elev-content').style.display = 'block';
            document.getElementById('elev-empty').style.display = 'none';
        }

        // Image
        if (data.house_image_html) {
            document.getElementById('img-container').innerHTML = data.house_image_html;
            document.getElementById('img-content').style.display = 'block';
            document.getElementById('img-empty').style.display = 'none';
        }

        // Analysis
        this.showAnalysis(data);
    },

    showAnalysis(data) {
        const r = data;
        document.getElementById('overall-score').textContent = r.overall_score || 0;
        const ratingEl = document.getElementById('score-rating');
        ratingEl.textContent = r.rating || '—';
        ratingEl.style.color = (r.overall_score || 0) >= 8 ? '#00B894' : (r.overall_score || 0) >= 6 ? '#FDCB6E' : '#E17055';

        const layout = r.layout || {};
        document.getElementById('score-detail').textContent =
            `Site: ${layout.site_length || '?'}' × ${layout.site_width || '?'}' · Facing: ${(layout.facing || 'north').toUpperCase()}`;
        document.getElementById('score-source').textContent =
            `Source: ${r.source || 'algorithmic'} · ${r.rooms_list?.length || 0} rooms`;

        // Room score cards
        const grid = document.getElementById('room-scores');
        grid.innerHTML = '';
        (r.room_scores || []).forEach(s => {
            const c = document.createElement('div');
            c.className = 'room-score-card';
            const col = s.score >= 8 ? '#00B894' : s.score >= 5 ? '#FDCB6E' : '#E17055';
            c.innerHTML = `
                <div class="rsc-header"><span class="rsc-name">${s.room}</span><span class="rsc-score" style="background:${col}">${s.score}/10</span></div>
                <div class="rsc-detail">📍 ${s.zone_label} · ${s.element}</div>
                <div class="rsc-bar"><div class="rsc-fill" style="width:${s.score*10}%;background:${col}"></div></div>
                <div class="rsc-reason">${s.reason}</div>`;
            grid.appendChild(c);
        });

        // Suggestions
        const list = document.getElementById('suggestions-list');
        list.innerHTML = '';
        (r.suggestions || []).forEach(s => {
            const d = document.createElement('div');
            d.className = 'suggestion-item';
            d.innerHTML = `<div class="suggestion-text"><strong>${s.room}</strong> — ${s.suggestion}</div>`;
            list.appendChild(d);
        });

        // Layout table
        const tbody = document.getElementById('layout-table-body');
        tbody.innerHTML = '';
        (layout.rooms || []).forEach(rm => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${rm.name}</strong></td>
                <td>${(rm.x || 0).toFixed(1)}'</td>
                <td>${(rm.y || 0).toFixed(1)}'</td>
                <td>${(rm.width || 0).toFixed(1)}'</td>
                <td>${(rm.height || 0).toFixed(1)}'</td>
                <td>${((rm.width || 0) * (rm.height || 0)).toFixed(0)} ft²</td>
                <td>${(rm.zone || '—').toUpperCase()}</td>
                <td style="font-weight:700;color:${(rm.score || 0) >= 8 ? '#00B894' : (rm.score || 0) >= 5 ? '#FDCB6E' : '#E17055'}">${rm.score || 0}/10</td>`;
            tbody.appendChild(tr);
        });

        document.getElementById('analysis-content').style.display = 'block';
        document.getElementById('analysis-empty').style.display = 'none';
    },

    _showStep(id) {
        document.querySelectorAll('.loading-steps span').forEach(el => el.style.opacity = '0.4');
        const el = document.getElementById(id);
        if (el) {
            el.style.opacity = '1';
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    },

    async checkAIStatus() {
        try {
            const res = await fetch('/api/ai/status');
            const d = await res.json();
            document.getElementById('ai-services').textContent = (d.configured_services || ['None']).join(' · ');
            if (d.gemini_available) {
                document.getElementById('ai-status-text').textContent = 'Gemini AI + SVG';
                document.getElementById('ai-services').style.color = '#A29BFE';
            }
        } catch (e) {}
    },

    async loadGuide() {
        try {
            const [zRes, rRes] = await Promise.all([
                fetch('/api/vastu/zones'),
                fetch('/api/vastu/rooms')
            ]);
            const zones = await zRes.json();
            const rooms = await rRes.json();

            const zc = document.getElementById('zone-cards');
            zc.innerHTML = '';
            Object.entries(zones).forEach(([k, z]) => {
                const card = document.createElement('div');
                card.className = 'zone-card';
                card.style.borderLeft = `4px solid ${z.border || '#ddd'}`;
                card.innerHTML = `<div class="zc-header"><span class="zc-name">${z.label}</span><span class="zc-element">${z.element}</span></div>
                    <div class="zc-desc">${(z.suitable || []).join(', ')}</div>
                    <div class="zc-unsuitable"><strong>Avoid:</strong> ${(z.unsuitable || []).join(', ')}</div>`;
                zc.appendChild(card);
            });

            const tb = document.getElementById('guide-room-body');
            tb.innerHTML = '';
            rooms.forEach(r => {
                tb.innerHTML += `<tr><td><strong>${r.name}</strong></td><td>${(r.primary_zone || '').toUpperCase()}</td>
                    <td>${(r.alt_zones || []).map(a => a.toUpperCase()).join(', ') || '—'}</td>
                    <td>${(r.avoid_zones || []).map(a => a.toUpperCase()).join(', ') || '—'}</td>
                    <td>${r.ideal_size || '—'}</td></tr>`;
            });

            // Switch to vastu tab listener
            document.querySelector('.nav-item[data-tab="vastu"]').addEventListener('click', () => {
                setTimeout(() => this.loadGuide(), 100);
            }, { once: true });

        } catch (e) {}
    },

    toast(msg) {
        const el = document.getElementById('toast');
        el.textContent = msg;
        el.classList.add('show');
        setTimeout(() => el.classList.remove('show'), 3000);
    }
};

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// Bootstrap
document.addEventListener('DOMContentLoaded', () => App.init());
