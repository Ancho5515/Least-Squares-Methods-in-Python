import unittest
import numpy as np
from numpy.testing import assert_allclose
from lsq import (finite_difference, whiten, gauss_newton,
                 levenberg_marquardt, dogleg, recursive_update)


class SolverTests(unittest.TestCase):
    def test_central_difference_matches_analytic(self):
        fun = lambda x: np.array([x[0]**2 + x[1], np.sin(x[0]*x[1])])
        x = np.array([2., .3])
        j = np.array([[4, 1], [.3*np.cos(.6), 2*np.cos(.6)]])
        assert_allclose(finite_difference(fun, x), j, rtol=1e-7, atol=1e-9)

    def test_correlated_whitening_matches_gls(self):
        a = np.array([[1., 0], [1, 1], [1, 2]])
        y = np.array([1., 3, 4])
        c = np.array([[2., .4, .2], [.4, 1, .3], [.2, .3, 1.5]])
        aw, yw = whiten(a, y, c)
        expected = np.linalg.solve(a.T@np.linalg.solve(c, a), a.T@np.linalg.solve(c, y))
        assert_allclose(np.linalg.lstsq(aw, yw, rcond=None)[0], expected)

    def test_whitening_rejects_nonsymmetric_covariance(self):
        with self.assertRaises(ValueError):
            whiten(np.ones((2, 1)), np.ones(2), np.array([[1., .4], [0, 1]]))

    def test_whitening_rejects_nonpositive_covariance(self):
        with self.assertRaises(ValueError):
            whiten(np.ones((2, 1)), np.ones(2), np.diag([1., -1]))

    def test_rosenbrock_and_accepted_descent(self):
        fun = lambda x: np.array([10*(x[1]-x[0]**2), 1-x[0]])
        jac = lambda x: np.array([[-20*x[0], 10.], [-1., 0.]])
        for solver in (gauss_newton, levenberg_marquardt, dogleg):
            with self.subTest(solver=solver.__name__):
                result = solver(fun, jac, [-1.2, 1.], max_iter=300)
                self.assertTrue(result.success, result.status)
                assert_allclose(result.x, [1, 1], atol=2e-5)
                costs = [h['cost'] for h in result.history if h['accepted']]
                self.assertTrue(np.all(np.diff(costs) <= 1e-12))

    def test_nonzero_residual_linear_problem(self):
        a = np.array([[1., 0], [1, 1], [1, 2], [1, 3]])
        y = np.array([0., 2, 2, 5])
        for solver in (gauss_newton, levenberg_marquardt, dogleg):
            r = solver(lambda x: a@x-y, lambda x: a, [0., 0.])
            assert_allclose(r.x, np.linalg.lstsq(a, y, rcond=None)[0], atol=1e-6)
            self.assertGreater(r.cost, 0)

    def test_stationary_start_is_detected(self):
        for solver in (gauss_newton, levenberg_marquardt, dogleg):
            r = solver(lambda x: np.array([x[0]]), lambda x: np.ones((1, 1)), [0.])
            self.assertTrue(r.success)
            self.assertEqual(r.status, 'gradient')

    def test_rank_deficient_step_is_finite(self):
        a = np.ones((3, 2));y = np.array([1., 2., 3.])
        for solver in (gauss_newton, levenberg_marquardt, dogleg):
            r = solver(lambda x: a@x-y, lambda x: a, [0., 0.])
            assert_allclose(a@r.x, 2., atol=1e-6)

    def test_invalid_inputs_are_explicit(self):
        for solver in (gauss_newton, levenberg_marquardt, dogleg):
            with self.subTest(solver=solver.__name__):
                with self.assertRaises(ValueError):
                    solver(lambda x: np.array([np.nan]), lambda x: np.ones((1, 1)), [0.])
                with self.assertRaises(ValueError):
                    solver(lambda x: x, lambda x: np.ones((2, 2)), [0.])
                with self.assertRaises(ValueError):
                    solver(lambda x: x, lambda x: np.eye(1), [0.], max_iter=0)

    def test_budget_exhaustion_is_not_success(self):
        r = levenberg_marquardt(lambda x: np.array([x[0]**2-2]),
                                lambda x: np.array([[2*x[0]]]), [10.], max_iter=1)
        self.assertFalse(r.success)
        self.assertEqual(r.status, 'max_iter')

    def test_rls_matches_regularized_batch(self):
        rng=np.random.default_rng(13);a=rng.normal(size=(30, 3));y=rng.normal(size=30)
        beta=np.zeros(3);p=100*np.eye(3)
        for phi, yi in zip(a, y):
            beta, p = recursive_update(beta, p, phi, yi)
        expected=np.linalg.solve(a.T@a+.01*np.eye(3), a.T@y)
        assert_allclose(beta, expected, atol=1e-11)

    def test_rls_forgetting_matches_weighted_batch(self):
        rng=np.random.default_rng(3);a=rng.normal(size=(20, 2));y=rng.normal(size=20)
        beta=np.zeros(2);p=100*np.eye(2);lam=.95
        for phi, yi in zip(a, y): beta,p=recursive_update(beta,p,phi,yi,forgetting=lam)
        w=lam**np.arange(19,-1,-1)
        expected=np.linalg.solve(a.T@(w[:,None]*a)+lam**20*.01*np.eye(2), a.T@(w*y))
        assert_allclose(beta,expected,atol=1e-10)

    def test_rls_rejects_invalid_forgetting(self):
        for lam in (0, -1, 1.1, np.nan):
            with self.assertRaises(ValueError):recursive_update(np.zeros(2),np.eye(2),[1,2],1,lam)


if __name__ == '__main__': unittest.main()
