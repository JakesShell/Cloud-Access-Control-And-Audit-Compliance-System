from pathlib import Path

LOG_FILE = Path("logs/access_log.txt")
REPORT_FILE = Path("reports/audit_summary.txt")


def generate_audit_summary():
    if not LOG_FILE.exists():
        print("No logs found. Run access_control.py first.")
        return

    total_events = 0
    denied_attempts = 0
    successful_events = 0
    violation_events = []

    with LOG_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            total_events += 1

            if "DENIED" in line:
                denied_attempts += 1
                violation_events.append(line.strip())

            if "SUCCESS" in line:
                successful_events += 1

    lines = []
    lines.append("Cloud Access Control Audit Summary")
    lines.append("=" * 44)
    lines.append(f"Total Events: {total_events}")
    lines.append(f"Successful Access Events: {successful_events}")
    lines.append(f"Denied Access Attempts: {denied_attempts}")
    lines.append("")
    lines.append("Compliance Review")
    lines.append("-" * 44)
    lines.append("Access activity was reviewed for policy violations and unauthorized attempts.")
    lines.append("Denied events should be reviewed by support or security operations teams.")
    lines.append("")
    lines.append("Denied Event Details")
    lines.append("-" * 44)

    if violation_events:
        lines.extend(violation_events)
    else:
        lines.append("No denied access attempts detected.")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print("")
    print(f"Audit summary saved to: {REPORT_FILE}")


if __name__ == "__main__":
    generate_audit_summary()
