"""Dense real least-squares teaching solvers. Residual convention: model - data.

These are intentionally small, unconstrained algorithms, not SciPy replacements.
All costs are 0.5 * r.T @ r. A termination flag is not a global optimum proof.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class Result:
    x: np.ndarray
    cost: float
    success: bool
    status: str
    history: list


def _vector(value, name):
    value = np.asarray(value, dtype=float)
    if value.ndim != 1 or value.size == 0 or not np.all(np.isfinite(value)):
        raise ValueError(f'{name} must be a finite nonempty 1-D vector')
    return value


def _symmetric(a):
    scale = np.max(np.abs(a))
    return bool(scale > 0 and np.max(np.abs(a/scale-a.T/scale)) <= 1e-10)


def _small_step(h, x, xtol):
    return bool(np.max(np.abs(h)/np.maximum(1., np.abs(x))) <= xtol)


def finite_difference(fun, x, relative_step=None):
    """Central differences with per-coordinate steps; smooth real functions only."""
    x = _vector(x, 'x')
    r = _vector(fun(x), 'residual')
    step = np.cbrt(np.finfo(float).eps) if relative_step is None else relative_step
    if not np.isfinite(step) or step <= 0:
        raise ValueError('relative_step must be positive')
    j = np.empty((len(r), len(x)))
    for k in range(len(x)):
        h = step * max(1., abs(x[k]))
        xp, xm = x.copy(), x.copy()
        xp[k] += h; xm[k] -= h
        rp, rm = _vector(fun(xp), 'residual'), _vector(fun(xm), 'residual')
        if rp.shape != r.shape or rm.shape != r.shape:
            raise ValueError('residual dimension changed')
        j[:, k] = (rp - rm) / (2*h)
    return j


def whiten(a, y, covariance):
    """For C=L L.T return L^-1 A, L^-1 y, using solves, never C^-1."""
    a, y, c = np.asarray(a, float), _vector(y, 'y'), np.asarray(covariance, float)
    if a.ndim != 2 or a.shape[0] != len(y) or c.shape != (len(y), len(y)):
        raise ValueError('incompatible design/data/covariance shapes')
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(c)):
        raise ValueError('all inputs must be finite')
    if not _symmetric(c):
        raise ValueError('covariance must be symmetric')
    try:
        l = np.linalg.cholesky(c)
    except np.linalg.LinAlgError as exc:
        raise ValueError('covariance must be positive definite') from exc
    return np.linalg.solve(l, a), np.linalg.solve(l, y)


def linearized_covariance(jacobian, active_mask=None):
    """Known absolute noise, already whitened J; no active bounds or null directions."""
    j = np.asarray(jacobian, float)
    if j.ndim != 2 or not all(j.shape) or not np.all(np.isfinite(j)):
        raise ValueError('Jacobian must be a finite nonempty matrix')
    m, n = j.shape
    if active_mask is not None:
        active_mask = np.asarray(active_mask)
        if active_mask.shape != (n,) or np.any(active_mask != 0):
            raise ValueError('unconstrained covariance unavailable at active bounds')
    if m < n:
        raise ValueError('parameter covariance unavailable: fewer observations than parameters')
    _, s, vt = np.linalg.svd(j, full_matrices=False)
    threshold = np.finfo(float).eps*max(m, n)*s[0]
    if s[0] == 0 or s[-1] <= threshold:
        raise ValueError('parameter covariance unavailable: Jacobian is numerically rank deficient')
    return (vt.T/(s*s))@vt


def _evaluate(fun, jac, x):
    r = _vector(fun(x), 'residual')
    j = np.asarray(jac(x), float)
    if j.shape != (len(r), len(x)) or not np.all(np.isfinite(j)):
        raise ValueError('Jacobian must be finite with shape (m, n)')
    cost = float(.5 * (r @ r))
    if not np.isfinite(cost):
        raise ValueError('residual norm overflowed')
    return r, j, cost


def _trial(fun, x, expected_size):
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        r = np.asarray(fun(x), float)
    if r.shape != (expected_size,):
        raise ValueError('residual dimension changed')
    return float(.5*(r@r)) if np.all(np.isfinite(r)) else np.inf


def _start(fun, jac, x0, max_iter, gtol, xtol):
    x = _vector(x0, 'x0').copy()
    if not isinstance(max_iter, (int, np.integer)) or max_iter < 1:
        raise ValueError('max_iter must be a positive integer')
    if not np.isfinite(gtol) or gtol <= 0 or not np.isfinite(xtol) or xtol <= 0:
        raise ValueError('tolerances must be finite and positive')
    r, j, cost = _evaluate(fun, jac, x)
    history = [dict(iteration=0, x=x.copy(), cost=cost, accepted=True,
                    step_norm=0., control=0.)]
    return x, r, j, cost, history


def _finish(x, cost, status, history):
    return Result(x.copy(), cost, status == 'gradient', status, history)


def _budget_finish(x, r, j, cost, gtol, history):
    status = 'gradient' if np.linalg.norm(j.T@r, np.inf) <= gtol else 'max_iter'
    return _finish(x, cost, status, history)


def gauss_newton(fun, jac, x0, max_iter=150, gtol=1e-9, xtol=1e-10):
    """Minimum-norm GN steps, safeguarded by Armijo backtracking."""
    x, r, j, cost, history = _start(fun, jac, x0, max_iter, gtol, xtol)
    for k in range(max_iter):
        g = j.T @ r
        if np.linalg.norm(g, np.inf) <= gtol:
            return _finish(x, cost, 'gradient', history)
        h = np.linalg.lstsq(j, -r, rcond=None)[0]
        if _small_step(h, x, xtol):
            return _finish(x, cost, 'stalled', history)
        alpha = 1.
        while alpha >= 2.**-30:
            trial_cost = _trial(fun, x+alpha*h, len(r))
            if trial_cost <= cost + 1e-4*alpha*(g@h):
                break
            alpha *= .5
        if alpha < 2.**-30:
            return _finish(x, cost, 'line_search_failed', history)
        x = x+alpha*h
        r, j, cost = _evaluate(fun, jac, x)
        history.append(dict(iteration=k+1, x=x.copy(), cost=cost, accepted=True,
                            step_norm=float(np.linalg.norm(alpha*h)), control=alpha))
    return _budget_finish(x, r, j, cost, gtol, history)


def levenberg_marquardt(fun, jac, x0, max_iter=150, gtol=1e-9, xtol=1e-10,
                       initial_damping=1e-3):
    """LM with Nielsen-style gain-ratio update and stable augmented LS steps.

    Solves min_h ||[J; sqrt(mu) I] h + [r; 0]||, not normal equations.
    Rejected trial points are recorded but never replace the current point.
    """
    x, r, j, cost, history = _start(fun, jac, x0, max_iter, gtol, xtol)
    if not np.isfinite(initial_damping) or initial_damping <= 0:
        raise ValueError('initial_damping must be positive')
    mu = initial_damping * max(1., np.max(np.sum(j*j, axis=0)))
    nu = 2.
    for k in range(max_iter):
        g = j.T @ r
        if np.linalg.norm(g, np.inf) <= gtol:
            return _finish(x, cost, 'gradient', history)
        a = np.vstack((j, np.sqrt(mu)*np.eye(len(x))))
        b = np.r_[-r, np.zeros(len(x))]
        h = np.linalg.lstsq(a, b, rcond=None)[0]
        if _small_step(h, x, xtol):
            # Damping can itself cause tiny steps: do not claim convergence.
            return _finish(x, cost, 'stalled', history)
        prediction = -float(g@h) - .5*float((j@h)@(j@h))
        trial_cost = _trial(fun, x+h, len(r))
        rho = (cost-trial_cost)/prediction if prediction > 0 else -np.inf
        accepted = bool(rho > 0 and np.isfinite(trial_cost))
        if accepted:
            x = x+h
            r, j, cost = _evaluate(fun, jac, x)
        history.append(dict(iteration=k+1, x=x.copy(), cost=cost, accepted=accepted,
                            step_norm=float(np.linalg.norm(h)), control=float(mu)))
        if accepted:
            mu *= max(1/3, 1-(2*rho-1)**3)
            mu = max(mu, np.finfo(float).tiny)
            nu = 2.
        else:
            mu *= nu
            nu *= 2.
            if not np.isfinite(mu) or not np.isfinite(nu):
                return _finish(x, cost, 'stalled', history)
    return _budget_finish(x, r, j, cost, gtol, history)


def dogleg(fun, jac, x0, max_iter=150, gtol=1e-9, xtol=1e-10,
           initial_radius=1.):
    """GN trust-region dogleg, with positive model-decrease prediction."""
    x, r, j, cost, history = _start(fun, jac, x0, max_iter, gtol, xtol)
    if not np.isfinite(initial_radius) or initial_radius <= 0:
        raise ValueError('initial_radius must be positive')
    radius = float(initial_radius)
    for k in range(max_iter):
        g = j.T@r
        if np.linalg.norm(g, np.inf) <= gtol:
            return _finish(x, cost, 'gradient', history)
        hn = np.linalg.lstsq(j, -r, rcond=None)[0]
        jg = j@g
        if np.linalg.norm(hn) <= radius:
            h = hn
        else:
            hs = -(g@g)/(jg@jg)*g
            if np.linalg.norm(hs) >= radius:
                h = -radius*g/np.linalg.norm(g)
            else:
                v = hn-hs
                av, bv, cv = v@v, 2*(hs@v), hs@hs-radius**2
                t = (-bv+np.sqrt(max(0., bv*bv-4*av*cv)))/(2*av)
                h = hs+t*v
        if _small_step(h, x, xtol):
            return _finish(x, cost, 'stalled', history)
        prediction = -float(g@h)-.5*float((j@h)@(j@h))
        trial_cost = _trial(fun, x+h, len(r))
        rho = (cost-trial_cost)/prediction if prediction > 0 else -np.inf
        accepted = bool(rho > .1 and np.isfinite(trial_cost))
        old_radius = radius
        if rho < .25:
            radius *= .25
        elif rho > .75 and np.linalg.norm(h) >= .99*radius:
            radius = min(2*radius, 1e6)
        if accepted:
            x = x+h
            r, j, cost = _evaluate(fun, jac, x)
        history.append(dict(iteration=k+1, x=x.copy(), cost=cost, accepted=accepted,
                            step_norm=float(np.linalg.norm(h)), control=old_radius))
    return _budget_finish(x, r, j, cost, gtol, history)


def recursive_update(beta, p, phi, y, forgetting=1.):
    """One RLS update. P is inverse information, not noise-scaled covariance."""
    beta, phi = _vector(beta, 'beta'), _vector(phi, 'phi')
    p = np.asarray(p, float)
    if phi.shape != beta.shape or p.shape != (len(beta), len(beta)):
        raise ValueError('incompatible RLS dimensions')
    if (not np.all(np.isfinite(p)) or not _symmetric(p) or
            not np.isfinite(y) or not np.isfinite(forgetting) or not 0 < forgetting <= 1):
        raise ValueError('invalid RLS inputs or forgetting factor')
    try:
        np.linalg.cholesky(p)
    except np.linalg.LinAlgError as exc:
        raise ValueError('P must be positive definite') from exc
    v = p@phi
    gain = v/(forgetting+phi@v)
    beta_new = beta+gain*(y-phi@beta)
    # Joseph form avoids catastrophic cancellation for diffuse initial P.
    contraction = np.eye(len(beta))-np.outer(gain, phi)
    p_new = contraction@(p/forgetting)@contraction.T+np.outer(gain, gain)
    return beta_new, .5*(p_new+p_new.T)
