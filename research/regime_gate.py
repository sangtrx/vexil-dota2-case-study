#!/usr/bin/env python3
"""Single predeclared, non-learned convex shrinkage of M1 toward M0 by minute."""
from __future__ import annotations

import numpy as np


def weight(minute):
    t=np.asarray(minute,dtype=float)
    if np.any(~np.isfinite(t)) or np.any(t<0):
        raise ValueError("minute must be finite and nonnegative")
    # Exactly 1 through minute 10, linear to zero at minute 20.
    w=np.clip((20.-t)/10.,0.,1.)
    return w


def gate(prob_m1,prob_m0,minute):
    m1=np.asarray(prob_m1,dtype=float)
    m0=np.asarray(prob_m0,dtype=float)
    w=weight(minute)
    if np.any(~np.isfinite(m1)) or np.any(~np.isfinite(m0)):
        raise ValueError("nonfinite input forecast")
    if np.any((m1<0)|(m1>1)|(m0<0)|(m0>1)):
        raise ValueError("probability outside [0,1]")
    result=w*m1+(1-w)*m0
    if not np.all(np.isfinite(result)) or np.any((result<0)|(result>1)):
        raise AssertionError("convex forecast invariant broken")
    return result
