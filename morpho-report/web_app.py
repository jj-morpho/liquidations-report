#!/usr/bin/env python3
"""
Morpho Risk Report — Self-Service Web Tool
============================================
A Flask web application that lets team members generate
the Morpho Weekly Risk Report PDF on demand.

Usage:
    pip install flask
    python web_app.py

Then visit http://localhost:5001
"""
import os
import sys
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, send_file, jsonify, url_for

# Add this directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Store generation jobs
jobs = {}
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ─── HTML Template ───────────────────────────────────────────────────

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morpho Risk Report Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f7f8fa;
            color: #222;
            min-height: 100vh;
        }

        .header {
            background: white;
            border-bottom: 1px solid #e5e7eb;
            padding: 20px 40px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header h1 {
            font-size: 20px;
            font-weight: 700;
            color: #111;
        }

        .header .tag {
            font-size: 11px;
            background: #eef2ff;
            color: #4A7CBA;
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: 600;
        }

        .container {
            max-width: 700px;
            margin: 40px auto;
            padding: 0 20px;
        }

        .card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 24px;
        }

        .card h2 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 6px;
            color: #111;
        }

        .card .desc {
            font-size: 13px;
            color: #666;
            margin-bottom: 20px;
            line-height: 1.5;
        }

        .form-group {
            margin-bottom: 18px;
        }

        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #333;
            margin-bottom: 6px;
        }

        .form-group .hint {
            font-size: 12px;
            color: #888;
            margin-top: 4px;
        }

        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 10px 14px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus, input[type="password"]:focus {
            border-color: #4A7CBA;
            box-shadow: 0 0 0 3px rgba(74, 124, 186, 0.1);
        }

        .toggle-row {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 0;
        }

        .toggle {
            position: relative;
            width: 44px;
            height: 24px;
            cursor: pointer;
        }

        .toggle input { display: none; }

        .toggle .slider {
            position: absolute;
            inset: 0;
            background: #d1d5db;
            border-radius: 24px;
            transition: background 0.2s;
        }

        .toggle .slider::before {
            content: '';
            position: absolute;
            width: 18px;
            height: 18px;
            left: 3px;
            top: 3px;
            background: white;
            border-radius: 50%;
            transition: transform 0.2s;
        }

        .toggle input:checked + .slider {
            background: #4A7CBA;
        }

        .toggle input:checked + .slider::before {
            transform: translateX(20px);
        }

        .toggle-label {
            font-size: 14px;
            color: #333;
        }

        .vault-section {
            margin-top: 8px;
        }

        .vault-section h3 {
            font-size: 13px;
            font-weight: 600;
            color: #555;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .vault-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 14px;
        }

        .vault-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
        }

        .vault-item:hover {
            background: #eef2ff;
            border-color: #c7d2fe;
        }

        .vault-item input[type="checkbox"] {
            width: 16px;
            height: 16px;
            accent-color: #4A7CBA;
        }

        .vault-item .name {
            font-size: 14px;
            font-weight: 500;
        }

        .vault-item .chain {
            font-size: 11px;
            color: #888;
            margin-left: auto;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 14px 24px;
            font-size: 15px;
            font-weight: 600;
            color: white;
            background: #4A7CBA;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn:hover { background: #3a6ba8; }
        .btn:disabled {
            background: #94a3b8;
            cursor: not-allowed;
        }

        .btn.secondary {
            background: white;
            color: #4A7CBA;
            border: 1px solid #4A7CBA;
        }

        .btn.secondary:hover {
            background: #eef2ff;
        }

        .progress-area {
            display: none;
            text-align: center;
            padding: 20px 0;
        }

        .progress-area.active { display: block; }

        .spinner {
            width: 36px;
            height: 36px;
            border: 3px solid #e5e7eb;
            border-top-color: #4A7CBA;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 14px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .progress-text {
            font-size: 14px;
            color: #555;
        }

        .result-area {
            display: none;
            text-align: center;
            padding: 16px 0;
        }

        .result-area.active { display: block; }

        .result-area .success-icon {
            width: 48px;
            height: 48px;
            background: #d1fae5;
            color: #059669;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 12px;
        }

        .result-area .error-icon {
            width: 48px;
            height: 48px;
            background: #fee2e2;
            color: #dc2626;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 12px;
        }

        .result-area h3 {
            font-size: 16px;
            margin-bottom: 6px;
        }

        .result-area p {
            font-size: 13px;
            color: #666;
            margin-bottom: 16px;
        }

        .footer {
            text-align: center;
            padding: 20px;
            font-size: 12px;
            color: #aaa;
        }
    </style>
</head>
<body>

<div class="header">
    <h1>Morpho Risk Report</h1>
    <span class="tag">Generator</span>
</div>

<div class="container">

    <!-- Data Source -->
    <div class="card">
        <h2>Data Source</h2>
        <p class="desc">Choose whether to pull live data from Dune Analytics or use sample data for testing.</p>

        <div class="toggle-row">
            <label class="toggle">
                <input type="checkbox" id="useSample" checked>
                <span class="slider"></span>
            </label>
            <span class="toggle-label" id="sampleLabel">Using sample data (no API key needed)</span>
        </div>

        <div class="form-group" id="apiKeyGroup" style="display: none;">
            <label>Dune API Key</label>
            <input type="password" id="apiKey" placeholder="Enter your Dune API key">
            <div class="hint">Required for live data. Get one at dune.com/settings/api</div>
        </div>
    </div>

    <!-- Vault Selection -->
    <div class="card">
        <h2>Vault Selection</h2>
        <p class="desc">Select which vaults to include in the liquidity section of the report.</p>

        <div class="vault-section">
            <h3>Bluechip Vaults</h3>
            <div class="vault-list">
                <label class="vault-item">
                    <input type="checkbox" name="vault" value="Gauntlet USDC Prime" checked>
                    <span class="name">Gauntlet USDC Prime</span>
                    <span class="chain">Ethereum</span>
                </label>
                <label class="vault-item">
                    <input type="checkbox" name="vault" value="Steakhouse USDCV" checked>
                    <span class="name">Steakhouse USDCV</span>
                    <span class="chain">Ethereum</span>
                </label>
            </div>
        </div>

        <div class="vault-section">
            <h3>Long-Tail Vaults</h3>
            <div class="vault-list">
                <label class="vault-item">
                    <input type="checkbox" name="vault" value="Gauntlet USDC RWA" checked>
                    <span class="name">Gauntlet USDC RWA</span>
                    <span class="chain">Ethereum</span>
                </label>
                <label class="vault-item">
                    <input type="checkbox" name="vault" value="Smokehouse USDC" checked>
                    <span class="name">Smokehouse USDC</span>
                    <span class="chain">Ethereum</span>
                </label>
            </div>
        </div>
    </div>

    <!-- Generate -->
    <div class="card" id="generateCard">
        <button class="btn" id="generateBtn" onclick="generateReport()">
            Generate Report
        </button>

        <div class="progress-area" id="progressArea">
            <div class="spinner"></div>
            <div class="progress-text" id="progressText">Fetching data and generating charts...</div>
        </div>

        <div class="result-area" id="resultArea"></div>
    </div>

</div>

<div class="footer">
    Morpho Risk Report Generator &middot; Data sourced from Dune Analytics
</div>

<script>
    const useSampleToggle = document.getElementById('useSample');
    const apiKeyGroup = document.getElementById('apiKeyGroup');
    const sampleLabel = document.getElementById('sampleLabel');

    useSampleToggle.addEventListener('change', () => {
        if (useSampleToggle.checked) {
            apiKeyGroup.style.display = 'none';
            sampleLabel.textContent = 'Using sample data (no API key needed)';
        } else {
            apiKeyGroup.style.display = 'block';
            sampleLabel.textContent = 'Using live Dune API data';
        }
    });

    async function generateReport() {
        const btn = document.getElementById('generateBtn');
        const progress = document.getElementById('progressArea');
        const result = document.getElementById('resultArea');

        // Collect selected vaults
        const vaultCheckboxes = document.querySelectorAll('input[name="vault"]:checked');
        const selectedVaults = Array.from(vaultCheckboxes).map(cb => cb.value);

        if (selectedVaults.length === 0) {
            alert('Please select at least one vault.');
            return;
        }

        const useSample = useSampleToggle.checked;
        const apiKey = document.getElementById('apiKey').value;

        if (!useSample && !apiKey) {
            alert('Please enter a Dune API key or switch to sample data.');
            return;
        }

        // Show progress
        btn.style.display = 'none';
        progress.classList.add('active');
        result.classList.remove('active');

        try {
            const resp = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    use_sample: useSample,
                    api_key: apiKey,
                    vaults: selectedVaults
                })
            });

            const data = await resp.json();

            if (data.status === 'started') {
                pollJob(data.job_id);
            } else {
                showError(data.error || 'Unknown error');
            }
        } catch (e) {
            showError('Failed to connect to server: ' + e.message);
        }
    }

    async function pollJob(jobId) {
        const progressText = document.getElementById('progressText');

        const poll = async () => {
            try {
                const resp = await fetch('/api/status/' + jobId);
                const data = await resp.json();

                if (data.status === 'running') {
                    progressText.textContent = data.message || 'Generating report...';
                    setTimeout(poll, 1500);
                } else if (data.status === 'done') {
                    showSuccess(data.filename, data.size);
                } else if (data.status === 'error') {
                    showError(data.error);
                } else {
                    setTimeout(poll, 1500);
                }
            } catch (e) {
                setTimeout(poll, 2000);
            }
        };

        poll();
    }

    function showSuccess(filename, size) {
        const progress = document.getElementById('progressArea');
        const result = document.getElementById('resultArea');
        const btn = document.getElementById('generateBtn');

        progress.classList.remove('active');
        result.classList.add('active');
        result.innerHTML = `
            <div class="success-icon">&#10003;</div>
            <h3>Report Generated</h3>
            <p>${filename} &middot; ${size}</p>
            <a href="/download/${filename}" class="btn" style="text-decoration:none; margin-bottom:10px;">
                Download PDF
            </a>
            <br><br>
            <button class="btn secondary" onclick="resetForm()" style="margin-top:8px;">
                Generate Another
            </button>
        `;
    }

    function showError(message) {
        const progress = document.getElementById('progressArea');
        const result = document.getElementById('resultArea');

        progress.classList.remove('active');
        result.classList.add('active');
        result.innerHTML = `
            <div class="error-icon">&#10007;</div>
            <h3>Generation Failed</h3>
            <p>${message}</p>
            <button class="btn secondary" onclick="resetForm()">
                Try Again
            </button>
        `;
    }

    function resetForm() {
        const btn = document.getElementById('generateBtn');
        const progress = document.getElementById('progressArea');
        const result = document.getElementById('resultArea');

        btn.style.display = 'flex';
        progress.classList.remove('active');
        result.classList.remove('active');
    }
</script>

</body>
</html>
"""


# ─── API Routes ──────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Start a report generation job."""
    data = request.get_json()
    use_sample = data.get("use_sample", True)
    api_key = data.get("api_key", "")
    selected_vaults = data.get("vaults", [])

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "message": "Initializing..."}

    # Run generation in background thread
    thread = threading.Thread(
        target=_run_generation,
        args=(job_id, use_sample, api_key, selected_vaults),
        daemon=True,
    )
    thread.start()

    return jsonify({"status": "started", "job_id": job_id})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    """Check status of a generation job."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "error", "error": "Job not found"}), 404
    return jsonify(job)


@app.route("/download/<filename>")
def download(filename):
    """Download a generated report."""
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath, as_attachment=True, download_name=filename)


# ─── Background Generation ──────────────────────────────────────────

def _run_generation(job_id, use_sample, api_key, selected_vaults):
    """Run the full report generation pipeline in background."""
    try:
        from config import BLUECHIP_VAULTS, LONGTAIL_VAULTS, ALL_TRACKED_VAULTS

        # Filter vaults based on selection
        active_vaults = [v for v in ALL_TRACKED_VAULTS if v["name"] in selected_vaults]

        # Step 1: Fetch data
        jobs[job_id]["message"] = "Fetching data..."
        if use_sample:
            from data_fetcher import generate_sample_data
            report_data = generate_sample_data()
            # Filter vault liquidity data to selected vaults only
            report_data["vault_liquidity"] = {
                k: v for k, v in report_data["vault_liquidity"].items()
                if k in selected_vaults
            }
        else:
            if api_key:
                os.environ["DUNE_API_KEY"] = api_key
            from data_fetcher import DuneDataFetcher
            fetcher = DuneDataFetcher(api_key=api_key if api_key else None)

            # Temporarily override tracked vaults
            import config
            original_vaults = config.ALL_TRACKED_VAULTS
            config.ALL_TRACKED_VAULTS = active_vaults
            try:
                report_data = fetcher.fetch_all_report_data()
            finally:
                config.ALL_TRACKED_VAULTS = original_vaults

        # Step 2: Generate charts
        jobs[job_id]["message"] = "Generating charts..."
        from chart_generator import generate_all_charts
        charts = generate_all_charts(report_data, output_dir=REPORTS_DIR)

        # Step 3: Generate PDF
        jobs[job_id]["message"] = "Building PDF..."
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"morpho_risk_report_{date_str}.pdf"
        output_path = os.path.join(REPORTS_DIR, filename)

        from pdf_generator import generate_report
        generate_report(report_data, charts, output_path)

        size_kb = os.path.getsize(output_path) / 1024
        size_str = f"{size_kb:.0f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"

        jobs[job_id] = {
            "status": "done",
            "filename": filename,
            "size": size_str,
            "path": output_path,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        jobs[job_id] = {
            "status": "error",
            "error": str(e),
        }


# ─── Main ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  MORPHO RISK REPORT — WEB TOOL")
    print("=" * 50)
    print("  Visit: http://localhost:5001")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=False)
