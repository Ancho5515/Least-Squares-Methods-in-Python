# Least Squares Chinese Notebook Book Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. User authorized autonomous inline execution.

**Goal:** Deliver all 16 chapters and four appendices as executable Chinese notebooks and one locally compiled review PDF, with original reference sources in Git.

**Architecture:** Per-chapter notebooks are authoritative; lsq/ holds tested numerical helpers. A local builder executes isolated IPython processes, exports their actual code/results/images through Pandoc and XeLaTeX, and writes a validation record.

**Tech Stack:** Python 3.11+ (validated on 3.12), NumPy, SciPy, Matplotlib, nbformat, IPython, matplotlib-inline, ipykernel, Pandoc, XeLaTeX.

**Spec:** docs/design.md

## Global Constraints

- No GitHub Actions or Artifact; all review deliverables and data committed to ordinary Git.
- Every phase and bug fix has its own commit.
- Source/derived quantities and physical assumptions are explicit. Examples use reproducible synthetic data.
- Source notebooks run independently; this host verifies separate socket-free IPython processes. Standard Jupyter kernel-protocol execution is not claimed here. PDF includes real code outputs.
- Original reference sources are preserved, including their licenses and audit records.

## Review Focus

- Rank-deficient and badly scaled systems: stable least squares and honest uniqueness/uncertainty statements.
- Nonfinite inputs and unreachable nonlinear targets: explicit termination rather than false convergence.
- Covariance whitening orientation: GLS equals the directly solved weighted normal equations.
- Fresh checkout and offline build: no hidden local path or undeclared dependency, no network used by notebooks.
- Chinese PDF and multi-page code: no missing glyphs, clipped formulas, broken links, unrendered math or hidden outputs.

## Task 1: Reference archive and reproducible design

Files: references/nonlinear-least-squares/, docs/design.md, README.md.

- [x] Extract the supplied ZIP without path traversal; keep every source and audit file.
- [x] Record separate SHA256 identities of supplied PDFs and project PDF; verify original.pdf matches.
- [x] Commit archive and agreed specification.

## Task 2: Numerical helpers with meaningful tests

Files: lsq/__init__.py, lsq/solvers.py, tests/test_solvers.py.

Interfaces: finite_difference(fun,x), whiten(A,y,cov), gauss_newton(fun,jac,x0), levenberg_marquardt(fun,jac,x0), dogleg(fun,jac,x0), recursive_update(beta,P,phi,y,forgetting=1).

- [x] Write/run failing tests: analytic derivatives, GLS equivalence, Rosenbrock/exponential convergence, accepted cost descent, rank deficiency, invalid inputs, RLS=batch.
- [x] Implement stable solves without explicit matrix inversion; return x/cost/status/history.
- [x] Run full helper tests; commit.

## Task 3: Foundations 00–06

Files: notebooks/00*.ipynb through 06*.ipynb, data/, docs/outline.md.

- [x] Write complete narrative, derivations, experiments and worked exercises for each chapter.
- [x] Execute each notebook in a separate IPython process and check its numeric assertions.
- [x] Commit executed chapters and source data.

## Task 4: Nonlinear methods 07–12

Files: notebooks/07*.ipynb through 12*.ipynb.

- [x] Show readable iterations and compare helpers to SciPy; expose initial-value sensitivity and rejection history.
- [x] Explain Jacobian signs, gain ratio, stopping and robust/bounded method restrictions.
- [x] Execute all six fresh; commit.

## Task 5: Applications and appendices

Files: notebooks/13*.ipynb through 15*.ipynb, notebooks/A*.ipynb through D*.ipynb.

- [x] Add recursive estimation, complete synthetic calibration, and monotone quantized PWM simulation with unreachable-target handling.
- [x] Add math reference, method choice, separable/low-rank methods and original source/errata mapping.
- [x] Execute all seven fresh; commit.

## Task 6: Book build, visual QA and review release

Files: tools/build.py, tools/book-template.tex, tests/test_build.py, requirements.txt, README.md, pdf/, docs/validation.json.

- [x] Write/run builder tests for manifest order, missing/error outputs, safe image export and reference integrity.
- [x] Build from executed notebooks using Pandoc + XeLaTeX locally; verify text, bookmarks, links and every page rendering.
- [x] Independently review numerical and build behavior, fix meaningful defects with regression tests and separate commits.
- [x] Execute full suite and all notebooks; rebuild PDF; write honest validation/limits and commit.
- [x] Push full staged history to the repository and verify remote head and file identities.

## Completion record

2026-11-03: 20 notebooks / 54 code cells executed; 36 tests passed without skips; 63-page Chinese PDF and 23 vector figures rendered and checked; 45 reference checksums verified. Command-line Git lacked write credentials, so the connected GitHub interface published all 14 phase commits, verifying each stage's exact tree SHA against the local build. The initial empty repository was initialized without replacing existing history. See docs/REVIEW.md for execution and review limits.
