import datetime as dt

import pandas as pd
import streamlit as st

import theme
from datecode_logic import allocate_order, compute_availability
from db import get_lots, get_locations, get_open_backlog, search_product_codes


def render_scenario(title, caption, alloc):
    st.markdown(f"##### {title}")
    st.caption(caption)
    if not alloc["breakdown"]:
        st.error("Fully allocated — no stock left for this scenario.")
        return
    if len(alloc["breakdown"]) == 1:
        row = alloc["breakdown"][0]
        st.success(f"**{row['datecode']}**  ({row['qty']:,.0f} units)")
    else:
        parts = ", ".join(f"{row['qty']:,.0f} @ {row['datecode']}" for row in alloc["breakdown"])
        st.warning(f"**Mixed datecodes:** {parts}")
    if alloc["shortfall"] > 0:
        st.error(f"Short {alloc['shortfall']:,.0f} units — not enough tracked stock to fill this order.")

st.set_page_config(page_title="Datecode Finder", page_icon=":calendar:", layout="centered")
theme.apply()

st.caption(
    "Master Electronics ships LIFO. This shows the datecode a customer would "
    "actually receive, depending on when their order ships."
)

st.warning(
    "**Important:** If a customer requires a newer date code, a Global Note must be "
    "added to the order or customer account. Date code requests entered through the "
    "portal will not be recognized unless a Global Note is already applied to the account."
)

part_number = st.text_input("Part Number", placeholder="e.g. 1TL1-1").strip().upper()

if part_number:
    try:
        product_codes = search_product_codes(part_number)
    except Exception as exc:
        st.error(f"Could not reach the database: {exc}")
        st.stop()

    if not product_codes:
        st.warning("No item found with that part number.")
        st.stop()

    product_code = (
        product_codes[0]
        if len(product_codes) == 1
        else st.selectbox("Brand / Product Code", product_codes)
    )

    locations = get_locations(product_code, part_number)
    if not locations:
        st.warning("No active inventory lots found for this item.")
        st.stop()

    location_code = st.selectbox("Warehouse", locations)
    order_qty = st.number_input("Order Quantity", min_value=1, value=1, step=1)

    if st.button("Find Datecode", type="primary"):
        lots = get_lots(product_code, part_number, location_code)
        backlog = get_open_backlog(product_code, part_number, location_code)

        today = dt.date.today()
        due_today_qty = sum(
            row["qty"] for row in backlog if row["ship_date"] is None or row["ship_date"] <= today
        )
        total_backlog_qty = sum(row["qty"] for row in backlog)

        result_today = compute_availability(lots, due_today_qty)
        result_after = compute_availability(lots, total_backlog_qty)
        alloc_today = allocate_order(result_today["lots"], order_qty)
        alloc_after = allocate_order(result_after["lots"], order_qty)

        st.metric("On Hand", f"{result_today['total_on_hand']:,.0f}")

        col1, col2 = st.columns(2)
        with col1:
            render_scenario(
                "If it ships today",
                "Nets out only backlog already due on or before today.",
                alloc_today,
            )
        with col2:
            render_scenario(
                "After the current backlog clears",
                "Conservative: assumes every open order ships first, even undated backorders.",
                alloc_after,
            )

        if result_after["unmatched_reserved"] > 0:
            st.warning(
                f"Total open backlog exceeds tracked on-hand lots by "
                f"{result_after['unmatched_reserved']:,.0f} units — some orders are backordered "
                f"awaiting future receipts."
            )

        st.subheader("Lot detail (newest first)")
        st.caption(
            f"Reserved-consumed columns below use the conservative "
            f"'after backlog clears' scenario ({total_backlog_qty:,.0f} units of open demand)."
        )
        df = pd.DataFrame(result_after["lots"])[
            ["datecode", "qty", "reserved_consumed", "available_qty", "received_at", "itn", "bin_location"]
        ]
        df.columns = [
            "Datecode",
            "Lot Qty",
            "Consumed by Backlog",
            "Available",
            "Received",
            "Tracking #",
            "Bin",
        ]
        st.dataframe(df, width="stretch", hide_index=True)

        if backlog:
            st.subheader("Open backlog for this item")
            backlog_df = pd.DataFrame(backlog)[["control_number", "line_number", "qty", "ship_date"]]
            backlog_df.columns = ["Order #", "Line", "Open Qty", "Ship Date"]
            st.dataframe(backlog_df, width="stretch", hide_index=True)
