"""Tiny, dependency-free stats helpers -- avoids pulling in scipy just for
a Spearman correlation over 6 data points."""


def _rank(values: list) -> list:
    """Average (fractional) ranks, ties get the mean rank -- standard
    Spearman tie handling."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman(a: list, b: list) -> float:
    assert len(a) == len(b) and len(a) > 1
    ra, rb = _rank(a), _rank(b)
    n = len(a)
    mean_ra = sum(ra) / n
    mean_rb = sum(rb) / n
    cov = sum((x - mean_ra) * (y - mean_rb) for x, y in zip(ra, rb))
    var_a = sum((x - mean_ra) ** 2 for x in ra)
    var_b = sum((y - mean_rb) ** 2 for y in rb)
    if var_a == 0 or var_b == 0:
        return 0.0
    return cov / (var_a ** 0.5 * var_b ** 0.5)


def mae(a: list, b: list) -> float:
    assert len(a) == len(b)
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)
