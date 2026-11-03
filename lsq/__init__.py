"""Small, inspectable teaching implementations; see notebooks for derivations."""
from .solvers import (Result, finite_difference, whiten, gauss_newton,
                      levenberg_marquardt, dogleg, recursive_update)

__all__ = ['Result', 'finite_difference', 'whiten', 'gauss_newton',
           'levenberg_marquardt', 'dogleg', 'recursive_update']
