#!/usr/bin/env python3
"""Structural checks; these do not replace translation or visual review."""
from pathlib import Path
import collections
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = [
    "01-introduction.tex", "02-descent-methods.tex", "03a-foundations.tex",
    "03b-lm-dogleg.tex", "03c-hybrid.tex", "03d-secant-final.tex",
    "appendix-and-references.tex",
]


def verify():
    errors = []
    texts = [(ROOT / "chapters" / name).read_text(encoding="utf-8") for name in NAMES]
    body = "\n".join(re.sub(r"(?<!\\)%[^\n]*", "", text) for text in texts)
    main = (ROOT / "main.tex").read_text(encoding="utf-8")
    pages = collections.Counter(map(int, re.findall(r"\\sourcepage\{(\d+)\}", body)))
    if set(pages) != set(range(1, 59)) or any(v != 1 for v in pages.values()):
        errors.append("Source-page markers must cover 1–58 once each.")
    source = json.loads((ROOT / "audit/source-object-inventory.json").read_text())
    expected = {tag for page in source for tag in page["right_margin_equation_tags"]}
    tags = collections.Counter(re.findall(r"\\tag\{([^}]+)\}", body))
    if set(tags) != expected:
        errors.append(f"Equation tags: missing={sorted(expected-set(tags))}; extra={sorted(set(tags)-expected)}")
    if any(v != 1 for v in tags.values()):
        errors.append("Duplicate equation tags.")
    examples = re.findall(r"\\begin\{example\}\{([^}]+)\}", body)
    wanted_examples = ["1.1", "2.1"] + [f"3.{i}" for i in range(1, 20)]
    if collections.Counter(examples) != collections.Counter(wanted_examples):
        errors.append("Examples do not match the source's complete 21-example set.")
    algorithms = re.findall(r"\\begin\{algorithmbox\}\{([^}]+)\}", body)
    if collections.Counter(algorithms) != collections.Counter(["2.4", "3.16", "3.21", "3.25", "3.34", "A.4"]):
        errors.append("The six numbered algorithms are incomplete or duplicated.")
    for function in ["3.26", "3.27"]:
        if not re.search(r"\\begin\{statement\}\{函数\s*" + re.escape(function), body):
            errors.append(f"Missing auxiliary function {function}.")
    for banned in ["\\originalequation", "\\originalalgorithm", "原书第", "中文内容梳理"]:
        if banned in body:
            errors.append(f"Disallowed body text/macro: {banned}")
    labels = collections.Counter(re.findall(r"\\label\{([^}]+)\}", body + main))
    labels.update({f"src:{n}": 1 for n in pages})
    refs = set(re.findall(r"\\(?:eqref|ref|pageref|autoref)\{([^}]+)\}", body + main))
    missing_refs = refs - set(labels)
    if missing_refs:
        errors.append(f"Unresolved source references: {sorted(missing_refs)}")
    duplicate_labels = [name for name, n in labels.items() if n > 1]
    if duplicate_labels:
        errors.append(f"Duplicate labels: {duplicate_labels}")
    figure_paths = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)
    if len(figure_paths) != 10 or len(set(figure_paths)) != 10:
        errors.append("Expected exactly 10 distinct source figure panels.")
    for name in figure_paths:
        if not (ROOT / name).is_file():
            errors.append(f"Missing figure asset: {name}")
    log_path = ROOT / "main.log"
    if log_path.exists():
        log = log_path.read_text(errors="replace")
        for pattern in [r"Overfull \\[hv]box", "Missing character:", "There were undefined references", "multiply defined", "! LaTeX Error"]:
            if re.search(pattern, log):
                errors.append(f"Build log contains: {pattern}")
    summary = {
        "source_pages": len(pages), "numbered_equation_components": len(tags),
        "examples": len(examples), "algorithms": len(algorithms),
        "auxiliary_functions": 2, "figure_panels": len(figure_paths),
        "errors": errors,
        "scope": "Structural checks only; human text and rendered-page review is recorded separately.",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == "__main__":
    sys.exit(verify())
