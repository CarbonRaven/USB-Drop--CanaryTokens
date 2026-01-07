"""RickRoll Landing Page Server.

This server provides multiple themed landing pages that log visitor info
before redirecting to the configured destination (default: YouTube RickRoll).
"""

import logging
import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

# Configuration
REDIRECT_URL = os.environ.get(
    "REDIRECT_URL", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
)
LOG_WEBHOOK = os.environ.get("LOG_WEBHOOK")  # Optional webhook for logging
DEFAULT_THEME = os.environ.get("DEFAULT_THEME", "corporate")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def log_visit(theme: str):
    """Log visitor information."""
    visit_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "theme": theme,
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent"),
        "referer": request.headers.get("Referer"),
        "path": request.path,
        "query": dict(request.args),
    }

    logger.info(f"Visit: {visit_data}")

    # Send to webhook if configured
    if LOG_WEBHOOK:
        try:
            import requests

            requests.post(LOG_WEBHOOK, json=visit_data, timeout=5)
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    return visit_data


@app.route("/")
def index():
    """Default landing page."""
    return redirect_with_log(DEFAULT_THEME)


@app.route("/corporate")
def corporate():
    """Corporate/business themed page."""
    return redirect_with_log("corporate")


@app.route("/login")
def login():
    """Fake login page."""
    return redirect_with_log("login")


@app.route("/maintenance")
def maintenance():
    """Maintenance/under construction page."""
    return redirect_with_log("maintenance")


@app.route("/direct")
def direct():
    """Direct redirect (no page shown)."""
    log_visit("direct")
    return redirect(REDIRECT_URL, code=302)


@app.route("/document")
def document():
    """Document viewer page."""
    return redirect_with_log("document")


@app.route("/survey")
def survey():
    """Survey/feedback page."""
    return redirect_with_log("survey")


@app.route("/onlyfans")
@app.route("/creator")
@app.route("/exclusive")
def onlyfans():
    """OnlyFans/creator content themed page."""
    return redirect_with_log("onlyfans")


@app.route("/helpdesk")
@app.route("/support")
@app.route("/it")
def helpdesk():
    """IT Help Desk themed page."""
    return redirect_with_log("helpdesk")


@app.route("/hr")
@app.route("/payroll")
@app.route("/hrportal")
def hrportal():
    """HR/Payroll portal themed page."""
    return redirect_with_log("hrportal")


@app.route("/fileshare")
@app.route("/files")
@app.route("/share")
@app.route("/download")
def fileshare():
    """File share/download themed page."""
    return redirect_with_log("fileshare")


@app.route("/training")
@app.route("/compliance")
@app.route("/learn")
def training():
    """Training/compliance themed page."""
    return redirect_with_log("training")


@app.route("/banking")
@app.route("/bank")
@app.route("/secure")
def banking():
    """Banking/financial themed page."""
    return redirect_with_log("banking")


def redirect_with_log(theme: str):
    """Render themed page and log visit."""
    log_visit(theme)
    # Get delay from query parameter, default to 3 seconds
    try:
        delay = int(request.args.get("delay", 3))
        delay = max(1, min(delay, 30))  # Clamp between 1-30 seconds
    except (ValueError, TypeError):
        delay = 3
    return render_template(
        f"{theme}.html",
        redirect_url=REDIRECT_URL,
        redirect_delay=delay,
    )


# Preview routes - show landing pages without logging or redirecting
AVAILABLE_THEMES = [
    "corporate", "login", "maintenance", "helpdesk", "hrportal",
    "fileshare", "training", "banking", "document", "survey", "onlyfans"
]


@app.route("/preview")
def preview_list():
    """List all available themes for preview."""
    base_url = request.host_url.rstrip("/")
    themes = [
        {"id": theme, "preview_url": f"{base_url}/preview/{theme}"}
        for theme in AVAILABLE_THEMES
    ]
    return jsonify({"themes": themes})


@app.route("/preview/<theme>")
def preview_theme(theme):
    """Preview a landing page without logging or redirecting."""
    if theme not in AVAILABLE_THEMES:
        return jsonify({"error": f"Unknown theme: {theme}"}), 404

    # Render template in preview mode (no redirect)
    return render_template(
        f"{theme}.html",
        redirect_url="#",  # Don't redirect
        redirect_delay=999999,  # Effectively disable auto-redirect
        preview_mode=True,
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "redirect_url": REDIRECT_URL})


@app.route("/api/log", methods=["POST"])
def log_endpoint():
    """Manual logging endpoint for JavaScript-based tracking."""
    data = request.get_json() or {}
    data["ip"] = request.headers.get("X-Forwarded-For", request.remote_addr)
    data["user_agent"] = request.headers.get("User-Agent")
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    logger.info(f"API Log: {data}")
    return jsonify({"status": "logged"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
