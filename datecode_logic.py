"""Datecode allocation logic.

Two different consumption directions are in play, and mixing them up gives a
customer the wrong datecode:

1. Reservations (open sales order backlog, not yet shipped) claim stock off
   the NEWEST lots first — last in, first reserved. Whatever's left unclaimed
   after that walk-down is what's actually free for a new order.
2. A new order shipping today draws from the OLDEST unclaimed stock first —
   rotating aging inventory out before touching anything newer that might
   still get reserved. It only reaches into newer lots once older ones run
   out, which is exactly when a single order ends up spanning datecodes.
"""


def compute_availability(lots, reserved_qty):
    """Walk lots newest-to-oldest, consuming reserved_qty off the top.

    Args:
        lots: list of dicts, each with at least 'datecode' and 'qty', already
            sorted newest-received first.
        reserved_qty: total quantity allocated to open orders for this item
            at this location, not yet shipped.

    Returns:
        dict with per-lot breakdown (each lot annotated with reserved_consumed
        and available_qty) and summary fields.
    """
    remaining_reserved = float(reserved_qty or 0)
    breakdown = []

    for lot in lots:
        qty = float(lot["qty"] or 0)
        consumed = min(qty, remaining_reserved)
        available = qty - consumed
        remaining_reserved -= consumed
        breakdown.append({**lot, "qty": qty, "reserved_consumed": consumed, "available_qty": available})

    return {
        "lots": breakdown,
        "total_on_hand": sum(row["qty"] for row in breakdown),
        "total_reserved": float(reserved_qty or 0),
        "total_available": sum(row["available_qty"] for row in breakdown),
        "unmatched_reserved": remaining_reserved,
    }


def allocate_order(lots_with_availability, order_qty):
    """Walk unclaimed stock oldest-to-newest, drawing enough to fill order_qty.

    lots_with_availability is newest-first (compute_availability's output
    order); this consumes it in reverse so aging stock rotates out before
    newer lots are touched. A single order can span multiple datecodes if
    it's bigger than what's left in the oldest available lot alone.

    Returns dict with 'breakdown' (list of {datecode, qty} pulled, oldest
    contributing datecode first) and 'shortfall' (unmet qty if total
    available stock is less than order_qty).
    """
    remaining = float(order_qty or 0)
    by_datecode = {}
    order = []

    for lot in reversed(lots_with_availability):
        if remaining <= 0:
            break
        available = lot["available_qty"]
        if available <= 0:
            continue
        take = min(available, remaining)
        datecode = lot["datecode"]
        if datecode not in by_datecode:
            by_datecode[datecode] = 0.0
            order.append(datecode)
        by_datecode[datecode] += take
        remaining -= take

    breakdown = [{"datecode": dc, "qty": by_datecode[dc]} for dc in order]
    return {"breakdown": breakdown, "shortfall": remaining}
