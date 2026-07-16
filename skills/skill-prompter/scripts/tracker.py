#!/usr/bin/env python3
"""
Skill Improvement Tracker CLI

Manages persistent JSON tracking for skill improvement sessions.
Enforces strict column rules so LLMs don't need to manage JSON manually.

Usage:
  python3 tracker.py init --skill NAME --original PATH
  python3 tracker.py analyze --skill NAME --total-steps N [options]
  python3 tracker.py weakpoints --skill NAME --high "1,2" --medium "3" --low "4,5"
  python3 tracker.py record --skill NAME --phase PHASE --changes TEXT --files-modified TEXT
                              [--scenario TEXT]
                              [--signal-fired pass|fail]
                              [--signal-tool-call-exact pass|fail]
                              [--signal-verify pass|fail]
                              [--signal-escape pass|fail|na]
                              [--signal-model-lanes pass|fail]
  python3 tracker.py audit --skill NAME --passed-steps "S1,S2" --failed-steps "S3" --notes TEXT
  python3 tracker.py finalize --skill NAME --status STATUS --summary TEXT [--force]
  python3 tracker.py show --skill NAME [--section SECTION]
  python3 tracker.py list [--status STATUS]

Gate behavior:
  `finalize --status completed` REJECTS if the skill has no
  `record --phase dryrun` (or `prompt-dryrun`) entry. The gate also
  rejects when the latest dryrun record carries structured `signals`
  with any `False` value (failing fired / tool_call_exact / verify_signal
  / escape_used / model_lanes). Pass `--force` to override (the override
  reason MUST be written into `--summary`).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Data directory next to this script's parent
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "improvements.json"


def load_data() -> dict:
    """Load the improvements database."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"skills": {}, "version": 1}


def save_data(data: dict):
    """Save the improvements database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_init(args):
    data = load_data()
    skill = args.skill

    if skill in data["skills"]:
        print(f"Warning: '{skill}' already tracked. Resetting.")

    data["skills"][skill] = {
        "original_path": args.original,
        "status": "in_progress",
        "started_at": now_iso(),
        "analysis": None,
        "weakpoints": None,
        "records": [],
        "audits": [],
        "finalized_at": None,
        "summary": None,
    }
    save_data(data)
    print(f"initialized: {skill}")
    print(f"  original: {args.original}")
    print(f"  status: in_progress")


def cmd_analyze(args):
    data = load_data()
    skill = args.skill

    if skill not in data["skills"]:
        print(f"Error: '{skill}' not initialized. Run 'init' first.", file=sys.stderr)
        sys.exit(1)

    analysis = {
        "total_steps": args.total_steps,
        "has_tool_calls": args.has_tool_calls == "true",
        "has_checkpoints": args.has_checkpoints == "true",
        "has_rfc2119": args.has_rfc2119 == "true",
        "has_subagent_delegation": args.has_subagent_delegation == "true",
        "has_decision_tables": args.has_decision_tables == "true",
        "vague_steps": [s.strip() for s in args.vague_steps.split(",") if s.strip()] if args.vague_steps else [],
        "notes": args.notes or "",
        "analyzed_at": now_iso(),
    }

    data["skills"][skill]["analysis"] = analysis
    save_data(data)

    print(f"Analysis for '{skill}':")
    print(f"  Total steps: {analysis['total_steps']}")
    print(f"  Tool calls: {'YES' if analysis['has_tool_calls'] else 'NO'}")
    print(f"  Checkpoints: {'YES' if analysis['has_checkpoints'] else 'NO'}")
    print(f"  RFC 2119: {'YES' if analysis['has_rfc2119'] else 'NO'}")
    print(f"  Subagent delegation: {'YES' if analysis['has_subagent_delegation'] else 'NO'}")
    print(f"  Decision tables: {'YES' if analysis['has_decision_tables'] else 'NO'}")
    if analysis["vague_steps"]:
        print(f"  Vague steps: {', '.join(analysis['vague_steps'])}")
    if analysis["notes"]:
        print(f"  Notes: {analysis['notes']}")


def cmd_weakpoints(args):
    data = load_data()
    skill = args.skill

    if skill not in data["skills"]:
        print(f"Error: '{skill}' not initialized.", file=sys.stderr)
        sys.exit(1)

    def parse_list(s):
        return [x.strip() for x in s.split(",") if x.strip()] if s else []

    wp = {
        "high": parse_list(args.high),
        "medium": parse_list(args.medium),
        "low": parse_list(args.low),
        "recorded_at": now_iso(),
    }

    data["skills"][skill]["weakpoints"] = wp
    save_data(data)

    total = len(wp["high"]) + len(wp["medium"]) + len(wp["low"])
    print(f"Weakpoints for '{skill}' ({total} steps classified):")
    print(f"  HIGH risk ({len(wp['high'])}): {', '.join(wp['high']) or 'none'}")
    print(f"  MEDIUM risk ({len(wp['medium'])}): {', '.join(wp['medium']) or 'none'}")
    print(f"  LOW risk ({len(wp['low'])}): {', '.join(wp['low']) or 'none'}")


DRYRUN_PHASES = ("dryrun", "prompt-dryrun")


def cmd_record(args):
    data = load_data()
    skill = args.skill

    if skill not in data["skills"]:
        print(f"Error: '{skill}' not initialized.", file=sys.stderr)
        sys.exit(1)

    record = {
        "phase": args.phase,
        "changes": args.changes,
        "files_modified": [f.strip() for f in args.files_modified.split(",") if f.strip()],
        "recorded_at": now_iso(),
    }

    # Structured dryrun signals (Phase 8 of skill-prompter / dry-run verification of skill-manager).
    # We only attach the `signals` block when this record is a dryrun phase AND the caller
    # actually passed at least one signal flag. This preserves backward compatibility with
    # legacy `record --phase dryrun ...` calls that don't supply signal flags.
    if args.phase in DRYRUN_PHASES:
        if args.scenario:
            record["scenario"] = args.scenario
        signals = {}
        signal_map = {
            "fired": args.signal_fired,
            "tool_call_exact": args.signal_tool_call_exact,
            "verify_signal": args.signal_verify,
            "escape_used": args.signal_escape,
            "model_lanes": args.signal_model_lanes,
        }
        for key, raw in signal_map.items():
            if raw is None:
                continue
            if raw == "pass":
                signals[key] = True
            elif raw == "fail":
                signals[key] = False
            elif raw == "na":
                signals[key] = None  # explicit not-applicable
        if signals:
            record["signals"] = signals

    data["skills"][skill]["records"].append(record)
    save_data(data)

    print(f"Record saved for '{skill}':")
    print(f"  Phase: {record['phase']}")
    print(f"  Changes: {record['changes'][:100]}...")
    print(f"  Files: {len(record['files_modified'])}")
    if record.get("signals"):
        print(f"  Signals: {record['signals']}")
        failing = [k for k, v in record["signals"].items() if v is False]
        if failing:
            print(f"  WARNING: failing signals -> {failing}. finalize will reject until fixed.")


def cmd_audit(args):
    data = load_data()
    skill = args.skill

    if skill not in data["skills"]:
        print(f"Error: '{skill}' not initialized.", file=sys.stderr)
        sys.exit(1)

    def parse_list(s):
        return [x.strip() for x in s.split(",") if x.strip()] if s else []

    audit = {
        "passed_steps": parse_list(args.passed_steps),
        "failed_steps": parse_list(args.failed_steps),
        "notes": args.notes or "",
        "audited_at": now_iso(),
    }

    data["skills"][skill]["audits"].append(audit)
    save_data(data)

    passed = len(audit["passed_steps"])
    failed = len(audit["failed_steps"])
    total = passed + failed
    pct = (passed / total * 100) if total > 0 else 0

    print(f"Audit for '{skill}':")
    print(f"  Passed: {passed}/{total} ({pct:.0f}%)")
    if audit["failed_steps"]:
        print(f"  Failed: {', '.join(audit['failed_steps'])}")
    if audit["notes"]:
        print(f"  Notes: {audit['notes'][:200]}")

    if failed > 0:
        print(f"\n  ACTION REQUIRED: Fix {failed} failed steps, then re-audit.")
    else:
        print(f"\n  STATIC AUDIT PASSED (Phase 7).")
        print(f"  NEXT: run Phase 8 dry-run before finalize. finalize will REJECT")
        print(f"        a 'completed' status without a dryrun record. Example:")
        print(f"          tracker.py record --skill {skill} --phase dryrun \\")
        print(f"            --scenario '<one-line scenario>' \\")
        print(f"            --signal-fired pass --signal-tool-call-exact pass \\")
        print(f"            --signal-verify pass --signal-escape na \\")
        print(f"            --signal-model-lanes pass \\")
        print(f"            --changes '<summary>' --files-modified ''")


def _check_dryrun_gate(skill_entry: dict) -> tuple[bool, str]:
    """Return (allowed, reason). Allowed only when at least one dryrun record exists
    and the LATEST dryrun record has no failing structured signals.
    Legacy dryrun records without `signals` are accepted (presence-only gate)
    so old workflows keep finalizing; new gated workflows attach signals."""
    records = skill_entry.get("records", [])
    dryrun_records = [r for r in records if r.get("phase") in DRYRUN_PHASES]
    if not dryrun_records:
        return False, "no dryrun record found"
    latest = dryrun_records[-1]
    signals = latest.get("signals")
    if signals:
        failing = [k for k, v in signals.items() if v is False]
        if failing:
            return False, f"latest dryrun has failing signals: {failing}"
    return True, "ok"


def cmd_finalize(args):
    data = load_data()
    skill = args.skill

    if skill not in data["skills"]:
        print(f"Error: '{skill}' not initialized.", file=sys.stderr)
        sys.exit(1)

    if args.status == "completed" and not args.force:
        allowed, reason = _check_dryrun_gate(data["skills"][skill])
        if not allowed:
            print(
                f"Error: cannot finalize '{skill}' as 'completed' — {reason}.\n"
                "  Required: run Phase 8 dry-run, then\n"
                "    tracker.py record --skill {skill} --phase dryrun \\\n"
                "      --scenario '<one-line scenario>' \\\n"
                "      --signal-fired pass --signal-tool-call-exact pass \\\n"
                "      --signal-verify pass --signal-escape na \\\n"
                "      --signal-model-lanes pass \\\n"
                "      --changes '<summary>' --files-modified ''\n"
                "  Override: pass --force AND document the reason in --summary.".replace(
                    "{skill}", skill
                ),
                file=sys.stderr,
            )
            sys.exit(2)

    data["skills"][skill]["status"] = args.status
    data["skills"][skill]["finalized_at"] = now_iso()
    data["skills"][skill]["summary"] = args.summary
    if args.force:
        data["skills"][skill]["force_finalized"] = True
    save_data(data)

    print(f"Finalized '{skill}':")
    print(f"  Status: {args.status}")
    print(f"  Summary: {args.summary[:200]}")
    if args.force:
        print(f"  WARNING: --force used. Dryrun gate bypassed.")


def cmd_show(args):
    data = load_data()
    skill = args.skill

    if skill not in data["skills"]:
        print(f"Error: '{skill}' not found.", file=sys.stderr)
        sys.exit(1)

    entry = data["skills"][skill]
    section = args.section

    if section == "all" or section is None:
        print(f"Skill: {skill}")
        print(f"  Status: {entry['status']}")
        print(f"  Started: {entry['started_at']}")
        print(f"  Original: {entry['original_path']}")

        if entry["analysis"]:
            a = entry["analysis"]
            print(f"  Analysis: {a['total_steps']} steps, vague={len(a.get('vague_steps', []))}")

        if entry["weakpoints"]:
            w = entry["weakpoints"]
            print(f"  Weakpoints: H={len(w['high'])} M={len(w['medium'])} L={len(w['low'])}")

        print(f"  Records: {len(entry['records'])}")
        print(f"  Audits: {len(entry['audits'])}")
        dryruns = [r for r in entry["records"] if r.get("phase") in DRYRUN_PHASES]
        print(f"  Dryruns: {len(dryruns)}")
        if dryruns:
            latest = dryruns[-1]
            sig = latest.get("signals")
            if sig:
                failing = [k for k, v in sig.items() if v is False]
                state = "FAIL" if failing else "PASS"
                print(f"    Latest signals: {state} ({sig})")
            else:
                print(f"    Latest signals: legacy (no structured signals)")

        if entry["finalized_at"]:
            print(f"  Finalized: {entry['finalized_at']}")
            print(f"  Summary: {entry.get('summary', 'N/A')[:100]}")
    elif section == "analysis":
        if entry["analysis"]:
            for k, v in entry["analysis"].items():
                print(f"  {k}: {v}")
        else:
            print("  No analysis recorded yet.")
    elif section == "weakpoints":
        if entry["weakpoints"]:
            for k, v in entry["weakpoints"].items():
                print(f"  {k}: {v}")
        else:
            print("  No weakpoints recorded yet.")
    elif section == "records":
        for i, r in enumerate(entry["records"]):
            print(f"  [{i}] {r['phase']} @ {r['recorded_at'][:19]}: {r['changes'][:80]}")
    elif section == "audits":
        for i, a in enumerate(entry["audits"]):
            p = len(a["passed_steps"])
            f = len(a["failed_steps"])
            print(f"  [{i}] {p} passed, {f} failed @ {a['audited_at'][:19]}")
    else:
        print(f"Unknown section: {section}. Use: all, analysis, weakpoints, records, audits")


def cmd_list(args):
    data = load_data()
    skills = data.get("skills", {})

    if not skills:
        print("No skills tracked yet.")
        return

    status_filter = args.status

    print(f"{'Skill':<30} {'Status':<15} {'Started':<20} {'Steps':<8}")
    print("-" * 75)

    for name, entry in skills.items():
        if status_filter and entry["status"] != status_filter:
            continue
        steps = entry["analysis"]["total_steps"] if entry.get("analysis") else "?"
        started = entry["started_at"][:19] if entry.get("started_at") else "?"
        print(f"{name:<30} {entry['status']:<15} {started:<20} {steps:<8}")


def main():
    parser = argparse.ArgumentParser(description="Skill Improvement Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p = sub.add_parser("init", help="Initialize tracking for a skill")
    p.add_argument("--skill", required=True)
    p.add_argument("--original", required=True)

    # analyze
    p = sub.add_parser("analyze", help="Record analysis of original skill")
    p.add_argument("--skill", required=True)
    p.add_argument("--total-steps", type=int, required=True)
    p.add_argument("--has-tool-calls", default="false")
    p.add_argument("--has-checkpoints", default="false")
    p.add_argument("--has-rfc2119", default="false")
    p.add_argument("--has-subagent-delegation", default="false")
    p.add_argument("--has-decision-tables", default="false")
    p.add_argument("--vague-steps", default="")
    p.add_argument("--notes", default="")

    # weakpoints
    p = sub.add_parser("weakpoints", help="Classify steps by compliance risk")
    p.add_argument("--skill", required=True)
    p.add_argument("--high", default="")
    p.add_argument("--medium", default="")
    p.add_argument("--low", default="")

    # record
    p = sub.add_parser("record", help="Record a phase completion")
    p.add_argument("--skill", required=True)
    p.add_argument("--phase", required=True)
    p.add_argument("--changes", required=True)
    p.add_argument("--files-modified", required=True)
    p.add_argument("--scenario", default=None,
                   help="(dryrun phases only) one-line scenario description")
    p.add_argument("--signal-fired", choices=["pass", "fail"], default=None,
                   help="(dryrun phases only) every step fired without silent skip")
    p.add_argument("--signal-tool-call-exact", choices=["pass", "fail"], default=None,
                   help="(dryrun phases only) every step used the exact named tool")
    p.add_argument("--signal-verify", choices=["pass", "fail"], default=None,
                   help="(dryrun phases only) every VERIFY gate produced a signal")
    p.add_argument("--signal-escape", choices=["pass", "fail", "na"], default=None,
                   help="(dryrun phases only) escape hatches rerouted correctly, or na if none triggered")
    p.add_argument("--signal-model-lanes", choices=["pass", "fail"], default=None,
                   help="(dryrun phases only) required low-cost and frontier validation lanes ran black-box")

    # audit
    p = sub.add_parser("audit", help="Record audit results")
    p.add_argument("--skill", required=True)
    p.add_argument("--passed-steps", default="")
    p.add_argument("--failed-steps", default="")
    p.add_argument("--notes", default="")

    # finalize
    p = sub.add_parser("finalize", help="Finalize improvement")
    p.add_argument("--skill", required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--force", action="store_true",
                   help="Bypass the dryrun gate. Document the reason inside --summary.")

    # show
    p = sub.add_parser("show", help="Show tracking data")
    p.add_argument("--skill", required=True)
    p.add_argument("--section", default=None, help="all, analysis, weakpoints, records, audits")

    # list
    p = sub.add_parser("list", help="List all tracked skills")
    p.add_argument("--status", default=None)

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "analyze": cmd_analyze,
        "weakpoints": cmd_weakpoints,
        "record": cmd_record,
        "audit": cmd_audit,
        "finalize": cmd_finalize,
        "show": cmd_show,
        "list": cmd_list,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
