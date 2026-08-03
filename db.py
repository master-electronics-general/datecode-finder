"""Databricks SQL access for the Datecode Finder.

Connection is configured via environment variables (see .env.example):
  DATABRICKS_SERVER_HOSTNAME  - workspace hostname, e.g. dbc-xxxx.cloud.databricks.com
  DATABRICKS_HTTP_PATH        - SQL warehouse HTTP path, e.g. /sql/1.0/warehouses/xxxx
  DATABRICKS_TOKEN            - optional personal access token; if unset, falls
                                 back to the Databricks CLI's own cached OAuth
                                 login (run `databricks auth login` once), so
                                 each user authenticates as themselves without
                                 a browser prompt on every run.
  DATABRICKS_CONFIG_PROFILE  - CLI profile to use (default: DEFAULT)
"""

import os
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config
from dotenv import load_dotenv

load_dotenv()

CATALOG = "me_prod"


def _open_connection():
    server_hostname = os.environ["DATABRICKS_SERVER_HOSTNAME"]
    http_path = os.environ["DATABRICKS_HTTP_PATH"]
    token = os.environ.get("DATABRICKS_TOKEN")

    if token:
        return sql.connect(server_hostname=server_hostname, http_path=http_path, access_token=token)

    cfg = Config(profile=os.environ.get("DATABRICKS_CONFIG_PROFILE", "DEFAULT"))
    return sql.connect(server_hostname=server_hostname, http_path=http_path, credentials_provider=lambda: cfg.authenticate)


def get_connection():
    """One connection per browser session, reused across queries.

    Each Streamlit session gets its own entry in st.session_state, so every
    user authenticates once (as themselves, via OAuth) and nobody shares
    another user's identity or login. Opening a fresh connection per query
    would mean a fresh OAuth handshake per query, which races against itself.
    """
    if st.session_state.get("db_conn") is None:
        st.session_state["db_conn"] = _open_connection()
    return st.session_state["db_conn"]


def _query(sql_text, params=None):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql_text, params or {})
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def search_product_codes(part_number):
    rows = _query(
        f"""
        SELECT DISTINCT product_code
        FROM {CATALOG}.gold_products.inventory
        WHERE part_number = %(part_number)s
        ORDER BY product_code
        """,
        {"part_number": part_number},
    )
    return [row["product_code"] for row in rows]


def get_locations(product_code, part_number):
    rows = _query(
        f"""
        SELECT DISTINCT LocationCode AS location_code
        FROM {CATALOG}.silver_merp.m1binloc
        WHERE ProductCode = %(product_code)s
          AND PartNumber = %(part_number)s
          AND is_active = '1'
          AND QuantityOnHand > 0
        ORDER BY location_code
        """,
        {"product_code": product_code, "part_number": part_number},
    )
    return [row["location_code"] for row in rows]


def get_lots(product_code, part_number, location_code):
    rows = _query(
        f"""
        SELECT DateCode AS datecode,
               QuantityOnHand AS qty,
               InventoryTrackingNumber AS itn,
               BinLocation AS bin_location,
               ReceivedTimestamp AS received_at
        FROM {CATALOG}.silver_merp.m1binloc
        WHERE ProductCode = %(product_code)s
          AND PartNumber = %(part_number)s
          AND LocationCode = %(location_code)s
          AND is_active = '1'
          AND QuantityOnHand > 0
        ORDER BY ReceivedTimestamp DESC
        """,
        {"product_code": product_code, "part_number": part_number, "location_code": location_code},
    )
    return rows


def get_open_backlog(product_code, part_number, location_code):
    """Open (unshipped) sales order lines competing for this item's stock.

    ship_date is the line's best-known promise date (revised if set, else
    original); it's null for lines that haven't been scheduled at all.
    """
    return _query(
        f"""
        SELECT open_quantity AS qty,
               COALESCE(revised_ship_date, original_ship_date) AS ship_date,
               control_number,
               line_number
        FROM {CATALOG}.gold_sales.backlog_detail
        WHERE product_code = %(product_code)s
          AND part_number = %(part_number)s
          AND location_code = %(location_code)s
          AND open_quantity > 0
        ORDER BY ship_date
        """,
        {"product_code": product_code, "part_number": part_number, "location_code": location_code},
    )
