"""Ordinary least squares with ordinary or Newey-West (HAC) standard errors, written out in numpy/scipy."""
import numpy as np
from scipy import stats

def ols(x, y, nw_lag=None):
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(y)
    X = np.column_stack([np.ones(n), x])
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    df = n - 2
    if nw_lag is None:
        s2 = e @ e / df
        V = s2 * XtXi
    else:  # Newey-West with Bartlett weights, small-sample factor n/(n-k)
        S = (X * e[:, None]).T @ (X * e[:, None])
        for L in range(1, nw_lag + 1):
            w = 1 - L / (nw_lag + 1)
            G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None])
            S += w * (G + G.T)
        V = XtXi @ S @ XtXi * n / df
    se = np.sqrt(V[1, 1]); t = b[1] / se
    p = 2 * stats.t.sf(abs(t), df); tc = stats.t.ppf(0.975, df)
    r2 = 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))
    dw = np.sum(np.diff(e) ** 2) / (e @ e)
    return dict(slope=b[1], lo=b[1] - tc * se, hi=b[1] + tc * se, p=p, r2=r2, n=n, se=se, dw=dw, intercept=b[0])
