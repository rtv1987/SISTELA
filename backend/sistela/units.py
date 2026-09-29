"""Compatibility is separate from an explicitly requested Decimal conversion."""

from decimal import Decimal

from .parsers.common import normalize_unit

SCALES = {("m", "100m"): Decimal("0.01"), ("100m", "m"): Decimal("100")}


def unit_compatibility(source: str, target: str) -> dict:
    source, target = normalize_unit(source), normalize_unit(target)
    status = (
        "UNKNOWN"
        if not source or not target
        else "IDENTICAL"
        if source == target
        else "CONVERTIBLE"
        if (source, target) in SCALES
        else "INCOMPATIBLE"
    )
    return {
        "status": status,
        "source": source,
        "target": target,
        "factor": str(SCALES[(source, target)]) if status == "CONVERTIBLE" else None,
    }


def convert_quantity(quantity: Decimal, source: str, target: str) -> Decimal:
    if not isinstance(quantity, Decimal) or not quantity.is_finite() or quantity < 0:
        raise ValueError("A finite nonnegative Decimal quantity is required")
    compatibility = unit_compatibility(source, target)
    if compatibility["status"] == "IDENTICAL":
        return quantity
    if compatibility["status"] != "CONVERTIBLE":
        raise ValueError("No explicit conversion rule")
    return quantity * Decimal(compatibility["factor"])
