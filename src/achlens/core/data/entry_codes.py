"""Code-only metadata used by entry-detail validation."""

TRANSACTION_CODES = frozenset(
    {
        22,
        23,
        24,
        27,
        28,
        29,
        32,
        33,
        34,
        37,
        38,
        39,
        42,
        43,
        44,
        47,
        48,
        49,
        52,
        53,
        54,
        55,
    }
)
CREDIT_CODES = frozenset({22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54})
DEBIT_CODES = frozenset({27, 28, 29, 37, 38, 39, 47, 48, 49, 55})
PRENOTE_CODES = frozenset({23, 28, 33, 38, 43, 48})
ZERO_DOLLAR_CODES = frozenset({24, 29, 34, 39, 44, 49, 54})

# Nacha documents R/S meanings for recurring/single entries and also permits
# originator-significance values without a standardized interpretation.
WEB_PAYMENT_TYPE_CODES = frozenset({"R", "S"})
