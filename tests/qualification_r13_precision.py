"""Isolation policy for all deterministic QUAL-R1.3 property/reference suites.

Use a local, documented high-precision Decimal context to evaluate independently
calculated oracles. Do not mutate getcontext() globally or quietly loosen
financial comparison tolerances because of unittest import order.
"""
from __future__ import annotations

from decimal import localcontext
from functools import wraps


def independent_decimal_precision(method):
    @wraps(method)
    def isolated(*args, **kwargs):
        with localcontext() as ctx:
            ctx.prec = 70
            return method(*args, **kwargs)
    return isolated
