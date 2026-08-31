"""Tests for common/stats.py -- the dependency-free MAE + Spearman the eval
reports rest on. Values checked against hand computation / scipy references."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.stats import mae, spearman, _rank


def test_mae_zero_when_identical():
    assert mae([1, 2, 3], [1, 2, 3]) == 0.0


def test_mae_known_value():
    assert mae([0, 0, 0], [1, 2, 3]) == 2.0
    assert mae([10, 20], [12, 26]) == 4.0


def test_spearman_perfect_positive():
    assert abs(spearman([1, 2, 3, 4, 5], [10, 20, 30, 40, 50]) - 1.0) < 1e-9


def test_spearman_perfect_negative():
    assert abs(spearman([1, 2, 3, 4, 5], [50, 40, 30, 20, 10]) - (-1.0)) < 1e-9


def test_spearman_with_ties_is_finite_and_in_range():
    rho = spearman([1, 1, 2, 3], [2, 2, 1, 4])
    assert -1.0 <= rho <= 1.0


def test_spearman_matches_hand_computed_value():
    # d = [-1,1,-1,1,-1,1], sum(d^2) = 6, n = 6
    # rho = 1 - 6*sum(d^2) / (n*(n^2-1)) = 1 - 36/210 = 0.82857142857
    rho = spearman([1, 2, 3, 4, 5, 6], [2, 1, 4, 3, 6, 5])
    assert abs(rho - 0.8285714285714286) < 1e-9


def test_spearman_zero_variance_returns_zero():
    assert spearman([5, 5, 5], [1, 2, 3]) == 0.0


def test_rank_assigns_average_rank_to_ties():
    # values 10,10,20 -> ranks 1.5,1.5,3
    assert _rank([10, 10, 20]) == [1.5, 1.5, 3.0]
