#!/usr/bin/env python3
"""Detect deterministic residual model-writing tells in edited prose.

Input is UTF-8 text from stdin, or from --text-file. Output is one JSON object.
Exit 0 means no deterministic residual was found, exit 1 means findings remain,
and exit 2 means the invocation or input was invalid.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


# These patterns are deliberately high-precision. Broader semantic judgments stay
# in the SKILL.md catalog scan instead of turning this gate into a noisy linter.
PATTERNS: dict[str, tuple[tuple[str, re.Pattern[str]], ...]] = {
    "negative-parallelism": (
        (
            "korean-negative-frame",
            re.compile(r"뿐\s*(?:만\s*)?아니라|아니라|(?:추측|고민|번거로움)\s*없이"),
        ),
        (
            "english-negative-frame",
            re.compile(r"\bnot\s+(?:just|only)\b|\bno\s+(?:guessing|guesswork)\b", re.I),
        ),
    ),
    "copula-avoidance": (
        (
            "korean-role-predicate",
            re.compile(r"역할을\s*(?:합니다|한다|하다|수행)|로\s*자리(?:합니다|한다|하다)"),
        ),
        (
            "english-role-predicate",
            re.compile(r"\b(?:serves|stands|acts|functions)\s+as\b", re.I),
        ),
    ),
    "fit-assertion": (
        (
            "korean-fit-predicate",
            re.compile(r"(?:자연스럽게|잘|딱)\s*맞(?:습니다|는다|다)"),
        ),
        ("english-fit-predicate", re.compile(r"\bnatural\s+fit\b", re.I)),
    ),
    "significance-inflation": (
        (
            "korean-significance-inflation",
            re.compile(r"중요한|중대한|획기적|전환점|중요성을\s*(?:보여|강조)"),
        ),
        (
            "english-significance-inflation",
            re.compile(
                r"\b(?:pivotal|groundbreaking)\b|\bturning\s+point\b|"
                r"\bmarks?\s+(?:a\s+)?(?:major|pivotal)\b|\bunderscores?\s+(?:its\s+)?importance\b",
                re.I,
            ),
        ),
    ),
    "ing-tail": (
        (
            "korean-ing-tail",
            re.compile(r"(?:보장|강조|반영|보여주)(?:하며|하면서)"),
        ),
        (
            "english-ing-tail",
            re.compile(r",\s*(?:ensuring|highlighting|reflecting|underscoring)\b", re.I),
        ),
    ),
    "corporate-softener": (
        (
            "korean-corporate-softener",
            re.compile(r"양해\s*부탁드립니다|미리\s*감사합니다|혹시\s*괜찮으시다면"),
        ),
        (
            "english-corporate-softener",
            re.compile(r"\b(?:feel free to|i(?:'d| would) be happy to|at your convenience)\b", re.I),
        ),
    ),
    "signposting": (
        (
            "korean-signposting",
            re.compile(r"자,?\s*그럼|여기서\s*알아둘\s*점은|본격적으로\s*살펴보"),
        ),
        (
            "english-signposting",
            re.compile(r"\b(?:let(?:'s| us) dive in|here(?:'s| is) what you need to know|without further ado)\b", re.I),
        ),
    ),
}


def _finding(
    *, category: str, pattern_id: str, line_number: int, match: str
) -> dict[str, object]:
    return {
        "category": category,
        "pattern": pattern_id,
        "line": line_number,
        "match": match,
    }


def _regex_findings(
    text: str, categories: tuple[str, ...]
) -> Iterable[dict[str, object]]:
    for line_number, line in enumerate(text.splitlines(), start=1):
        for category in categories:
            specs = PATTERNS.get(category, ())
            for pattern_id, pattern in specs:
                for match in pattern.finditer(line):
                    yield _finding(
                        category=category,
                        pattern_id=pattern_id,
                        line_number=line_number,
                        match=match.group(0),
                    )


def _rule_of_three_findings(text: str) -> Iterable[dict[str, object]]:
    for line_number, line in enumerate(text.splitlines(), start=1):
        # Three repeated comparative markers are a high-precision Korean triad.
        if len(re.findall(r"(?:^|[\s,])더\s+[^\s,.;]+", line)) >= 3:
            yield _finding(
                category="rule-of-three",
                pattern_id="korean-repeated-comparative-triad",
                line_number=line_number,
                match=line.strip(),
            )

        english_triad = re.search(
            r"\b[^,.;]{1,40},\s*[^,.;]{1,40},?\s+(?:and|or)\s+[^,.;]{1,40}",
            line,
            re.I,
        )
        if english_triad:
            yield _finding(
                category="rule-of-three",
                pattern_id="english-three-part-list",
                line_number=line_number,
                match=english_triad.group(0),
            )


def scan(text: str, categories: tuple[str, ...] | None = None) -> list[dict[str, object]]:
    selected = categories if categories is not None else (*PATTERNS.keys(), "rule-of-three")
    findings = [*_regex_findings(text, selected)]
    if "rule-of-three" in selected:
        findings.extend(_rule_of_three_findings(text))
    return sorted(
        findings,
        key=lambda item: (
            int(item["line"]),
            str(item["category"]),
            str(item["pattern"]),
            str(item["match"]),
        ),
    )


def _result(text: str, categories: tuple[str, ...]) -> dict[str, object]:
    findings = scan(text, categories)
    return {
        "status": "fail" if findings else "pass",
        "checked_categories": list(categories),
        "finding_count": len(findings),
        "findings": findings,
    }


def _run_self_test() -> int:
    cases = (
        ("clean-korean", "이번 업데이트로 작업 속도와 안정성이 좋아졌습니다.", False, None),
        ("significance", "이번 업데이트는 중요한 전환점입니다.", True, None),
        ("negative-parallelism", "속도뿐 아니라 안정성도 좋아졌습니다.", True, None),
        ("rule-of-three", "더 빠르고, 더 간단하며, 더 안정적입니다.", True, None),
        ("copula-avoidance", "이 기능은 핵심 역할을 합니다.", True, None),
        ("ing-tail", "일관성을 보장하며 누구나 쓸 수 있습니다.", True, None),
        (
            "category-scoping",
            "중요한 설정입니다.",
            False,
            ("negative-parallelism",),
        ),
    )
    failures = []
    for name, text, expected_finding, categories in cases:
        actual_finding = bool(scan(text, categories))
        if actual_finding != expected_finding:
            failures.append(
                {
                    "case": name,
                    "expected_finding": expected_finding,
                    "actual_finding": actual_finding,
                }
            )

    payload = {
        "status": "pass" if not failures else "fail",
        "tests": len(cases),
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


def _read_text(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot read --text-file {path!r}: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect high-confidence residual frontier-model writing tells."
    )
    parser.add_argument("--text-file", help="Read UTF-8 text from this file instead of stdin.")
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        help="Triggered category to check; repeat for multiple categories. Use 'none' alone when no deterministic category was triggered.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in regression cases.")
    args = parser.parse_args()

    if args.self_test:
        return _run_self_test()

    requested_categories = tuple(dict.fromkeys(args.category))
    known_categories = {*PATTERNS.keys(), "rule-of-three"}
    if requested_categories == ("none",):
        selected_categories: tuple[str, ...] = ()
    else:
        unknown_categories = sorted(set(requested_categories) - known_categories)
        if not requested_categories or unknown_categories or "none" in requested_categories:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "pass one or more known --category values, or pass --category none alone",
                        "unknown_categories": unknown_categories,
                        "known_categories": sorted(known_categories),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 2
        selected_categories = requested_categories

    try:
        text = _read_text(args.text_file)
    except ValueError as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False))
        return 2

    if not text.strip():
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": "input text is empty; pipe EDITED_TEXT to stdin or pass --text-file",
                },
                ensure_ascii=False,
            )
        )
        return 2

    result = _result(text, selected_categories)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
