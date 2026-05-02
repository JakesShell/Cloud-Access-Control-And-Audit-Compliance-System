import json
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("data/users.json")
LOG_FILE = Path("logs/access_log.txt")
DOCUMENT_FILE = Path("files/sample_document.txt")

ROLE_PERMISSIONS = {
    "admin": ["READ", "WRITE"],
    "analyst": ["READ"],
    "guest": []
}


def load_users():
    with DATA_FILE.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def classify_event(status):
    if status == "SUCCESS":
        return "AUTHORIZED_ACTIVITY"

    return "ACCESS_POLICY_VIOLATION"


def log_access(username, role, action, filename, status):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    event_type = classify_event(status)
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"{timestamp} | {username} | {role} | {action} | {filename} | {status} | {event_type}"

    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(line + "\n")


def access_file(username, role, action, filename):
    allowed_actions = ROLE_PERMISSIONS.get(role, [])

    if action in allowed_actions:
        status = "SUCCESS"
    else:
        status = "DENIED"

    log_access(username, role, action, filename, status)

    print(
        f"{username} | Role: {role} | Action: {action} | "
        f"File: {filename} | Status: {status}"
    )


def simulate_session(user):
    username = user["username"]
    role = user["role"]

    print("")
    print(f"--- Session Start: {username} ({role}) ---")

    actions = ["READ", "WRITE"]

    for action in actions:
        access_file(username, role, action, "sample_document.txt")

    print(f"--- Session End: {username} ---")
    print("")


def main():
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    print("Cloud Access Control And Audit Compliance System")
    print("=" * 56)
    print("Simulating user sessions and access attempts...")

    users = load_users()

    for user in users:
        simulate_session(user)

    print(f"Structured audit log saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
