from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import json
from pathlib import Path

app = Flask(__name__)
app.secret_key = "cloud-secure-document-command-center"

DATA_DIR = Path("data")
LOG_DIR = Path("logs")
REPORT_DIR = Path("reports")

USERS_FILE = DATA_DIR / "portal_users.json"
DOCUMENTS_FILE = DATA_DIR / "documents.json"
AUDIT_LOG_FILE = LOG_DIR / "document_access_audit.log"
REPORT_FILE = REPORT_DIR / "access_compliance_report.json"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)


def seed_data():
    USERS_FILE.write_text(
        json.dumps(
            [
                {
                    "username": "admin",
                    "password": "admin123",
                    "role": "Security Admin"
                },
                {
                    "username": "analyst",
                    "password": "analyst123",
                    "role": "Support Analyst"
                },
                {
                    "username": "viewer",
                    "password": "viewer123",
                    "role": "Read Only"
                }
            ],
            indent=2
        ),
        encoding="utf-8"
    )

    DOCUMENTS_FILE.write_text(
        json.dumps(
            [
                {
                    "doc_id": "DOC-001",
                    "title": "Customer Data Handling Policy",
                    "classification": "Restricted",
                    "owner": "Security Team",
                    "required_role": "Security Admin"
                },
                {
                    "doc_id": "DOC-002",
                    "title": "Cloud Incident Response Playbook",
                    "classification": "Confidential",
                    "owner": "Operations Team",
                    "required_role": "Support Analyst"
                },
                {
                    "doc_id": "DOC-003",
                    "title": "Public Service Status Notes",
                    "classification": "Internal",
                    "owner": "Support Team",
                    "required_role": "Read Only"
                },
                {
                    "doc_id": "DOC-004",
                    "title": "Vendor Access Review Notes",
                    "classification": "Confidential",
                    "owner": "Compliance Team",
                    "required_role": "Support Analyst"
                }
            ],
            indent=2
        ),
        encoding="utf-8"
    )


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def append_audit_event(username, role, document, action, result, risk_level, compliance_status):
    event = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "username": username,
        "role": role,
        "document": document["title"],
        "classification": document["classification"],
        "action": action,
        "result": result,
        "risk_level": risk_level,
        "compliance_status": compliance_status
    }

    with AUDIT_LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(event) + "\n")


def load_audit_events():
    if not AUDIT_LOG_FILE.exists():
        return []

    events = []

    with AUDIT_LOG_FILE.open("r", encoding="utf-8") as log:
        for line in log:
            if line.strip():
                events.append(json.loads(line))

    return list(reversed(events))


def role_rank(role):
    ranks = {
        "Read Only": 1,
        "Support Analyst": 2,
        "Security Admin": 3
    }

    return ranks.get(role, 0)


def can_access(user_role, required_role):
    return role_rank(user_role) >= role_rank(required_role)


def classify_risk(result, classification):
    if result == "DENIED" and classification == "Restricted":
        return "HIGH", "FAILED"

    if result == "DENIED":
        return "MEDIUM", "REVIEW REQUIRED"

    return "LOW", "PASS"


def build_metrics(events, documents):
    denied = sum(1 for event in events if event["result"] == "DENIED")
    granted = sum(1 for event in events if event["result"] == "GRANTED")
    high_risk = sum(1 for event in events if event["risk_level"] == "HIGH")
    failed = sum(1 for event in events if event["compliance_status"] == "FAILED")

    return {
        "total_documents": len(documents),
        "access_attempts": len(events),
        "granted_attempts": granted,
        "denied_attempts": denied,
        "high_risk_events": high_risk,
        "failed_compliance": failed
    }


def write_compliance_report(events, documents):
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_documents": len(documents),
        "total_access_events": len(events),
        "granted_attempts": sum(1 for event in events if event["result"] == "GRANTED"),
        "denied_attempts": sum(1 for event in events if event["result"] == "DENIED"),
        "high_risk_events": sum(1 for event in events if event["risk_level"] == "HIGH"),
        "compliance_failures": sum(1 for event in events if event["compliance_status"] == "FAILED"),
        "events": events
    }

    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")


@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    seed_data()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_json(USERS_FILE)
        user = next(
            (
                user_record
                for user_record in users
                if user_record["username"] == username and user_record["password"] == password
            ),
            None
        )

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        flash("Invalid login details. Try admin / admin123.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    seed_data()

    documents = load_json(DOCUMENTS_FILE)
    events = load_audit_events()
    metrics = build_metrics(events, documents)

    write_compliance_report(events, documents)

    return render_template(
        "dashboard.html",
        documents=documents,
        events=events[:12],
        metrics=metrics,
        username=session["username"],
        role=session["role"]
    )


@app.route("/access/<doc_id>", methods=["POST"])
def access_document(doc_id):
    if "username" not in session:
        return redirect(url_for("login"))

    documents = load_json(DOCUMENTS_FILE)
    document = next((doc for doc in documents if doc["doc_id"] == doc_id), None)

    if not document:
        flash("Document not found.", "error")
        return redirect(url_for("dashboard"))

    allowed = can_access(session["role"], document["required_role"])
    result = "GRANTED" if allowed else "DENIED"
    risk_level, compliance_status = classify_risk(result, document["classification"])

    append_audit_event(
        session["username"],
        session["role"],
        document,
        "VIEW",
        result,
        risk_level,
        compliance_status
    )

    if allowed:
        flash(f"Access granted: {document['title']}", "success")
    else:
        flash(f"Access denied: {document['title']} requires {document['required_role']}.", "error")

    return redirect(url_for("dashboard"))


@app.route("/report")
def report():
    if "username" not in session:
        return redirect(url_for("login"))

    events = load_audit_events()
    documents = load_json(DOCUMENTS_FILE)

    write_compliance_report(events, documents)

    return REPORT_FILE.read_text(encoding="utf-8"), 200, {"Content-Type": "application/json"}


if __name__ == "__main__":
    seed_data()
    app.run(debug=True)
