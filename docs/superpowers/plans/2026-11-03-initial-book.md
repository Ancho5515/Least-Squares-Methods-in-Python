# Least Squares Chinese Notebook Book Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. User authorized autonomous inline execution.

**Goal:** Deliver all 16 chapters and four appendices as executable Chinese notebooks and one locally compiled review PDF, with original reference sources in Git.

**Architecture:** Per-chapter notebooks are authoritative; lsq/ holds tested numerical helpers. A local builder executes isolated kernels, exports their actual code/results/images through Pandoc and XeLaTeX, and writes a validation record.

**Tech Stack:** Python 3.11+ (validated on 3.12), NumPy, SciPy, Matplotlib, nbformat, nbclient, ipykernel, Pandoc, XeLaTeX.

**Spec:** docs/design.md

## Global Constraints

- No GitHub Actions or Artifact; all review deliverables and data committed to ordinary Git.
- Every phase and bug fix has its own commit.
- Source/derived quantities and physical assumptions are explicit. Examples use reproducible synthetic data.
- Source notebooks run independently from a fresh kernel. PDF includes real code outputs.
- Original reference sources are preserved, including their licenses and audit records.

## Review Focus

- Rank-deficient and badly scaled systems: stable least squares and honest uniqueness/uncertainty statements.
- Nonfinite inputs and unreachable nonlinear targets: explicit termination rather than false convergence.
- Covariance whitening orientation: GLS equals the directly solved weighted normal equations.
- Fresh checkout and offline build: no hidden local path or undeclared dependency, no network used by notebooks.
- Chinese PDF and multi-page code: no missing glyphs, clipped formulas, broken links, unrendered math or hidden outputs.

## Task 1: Reference archive and reproducible design

Files: references/nonlinear-least-squares/, docs/design.md, README.md.

- [ ] Extract the supplied ZIP without path traversal; keep every source and audit file.
- [ ] Record separate SHA256 identities of supplied PDFs and project PDF; verify original.pdf matches.
- [ ] Commit archive and agreed specification.

## Task 2: Numerical helpers with meaningful tests

Files: lsq/__init__.py, lsq/solvers.py, tests/test_solvers.py.

Interfaces: finite_difference(fun,x), whiten(A,y,cov), gauss_newton(fun,jac,x0), levenberg_marquardt(fun,jac,x0), dogleg(fun,jac,x0), recursive_update(beta,P,phi,y,forgetting=1).

- [ ] Write/run failing tests: analytic derivatives, GLS equivalence, Rosenbrock/exponential convergence, accepted cost descent, rank deficiency, invalid inputs, RLS=batch.
- [ ] Implement stable solves without explicit matrix inversion; return x/cost/status/history.
- [ ] Run full helper tests; commit.

## Task 3: Foundations 00–06

Files: notebooks/00*.ipynb through 06*.ipynb, data/, docs/outline.md.

- [ ] Write complete narrative, derivations, experiments and worked exercises for each chapter.
- [ ] Execute each notebook in a separate kernel and check its numeric assertions.
- [ ] Commit executed chapters and source data.

## Task 4: Nonlinear methods 07–12

Files: notebooks/07*.ipynb through 12*.ipynb.

- [ ] Show readable iterations and compare helpers to SciPy; expose initial-value sensitivity and rejection history.
- [ ] Explain Jacobian signs, gain ratio, stopping and robust/bounded method restrictions.
- [ ] Execute all six fresh; commit.

## Task 5: Applications and appendices

Files: notebooks/13*.ipynb through 15*.ipynb, notebooks/A*.ipynb through D*.ipynb.

- [ ] Add recursive estimation, complete synthetic calibration, and monotone quantized PWM simulation with unreachable-target handling.
- [ ] Add math reference, method choice, separable/low-rank methods and original source/errata mapping.
- [ ] Execute all seven fresh; commit.

## Task 6: Book build, visual QA and review release

Files: tools/build.py, tools/book-template.tex, tests/test_build.py, requirements.txt, README.md, pdf/, docs/validation.json.

- [ ] Write/run builder tests for manifest order, missing/error outputs, safe image export and reference integrity.
- [ ] Build from executed notebooks using Pandoc + XeLaTeX locally; verify text, bookmarks, links and every page rendering.
- [ ] Independently review numerical and build behavior, fix meaningful defects with regression tests and separate commits.
- [ ] Execute full suite and all notebooks; rebuild PDF; write honest validation/limits and commit.
- [ ] Push full staged history to the repository and verify remote head and file identities.
