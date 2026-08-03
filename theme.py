"""Master Electronics brand styling for Streamlit.

Colors and font pairing come straight from the ME Brand Identity Manual
(Feb 2020) / the Master Electronics Design System project. Roboto Condensed
Bold + Roboto are the manual's own designated "substitute" fonts for system
contexts (PPT/email/web apps) where the real brand fonts (Vinyl, Hey August)
aren't practical.
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@700&family=Roboto:wght@400;500;700&display=swap');

:root {
  --me-blue: #0068B3;
  --me-black: #000000;
  --me-red: #E01B37;
  --me-light-gray: #E6E6E6;
  --me-gray: #838D95;
  --me-green: #06B95A;
  --me-bg-2: #F5F7FA;
  --me-fg: #14161A;
  --me-fg-2: #3C434C;
  --me-border: #D7DCE2;
}

html, body, [class*="css"] { font-family: 'Roboto', system-ui, sans-serif; }

h1, h2, h3 {
  font-family: 'Roboto Condensed', 'Arial Narrow', sans-serif !important;
  font-weight: 700 !important;
  color: var(--me-fg) !important;
  text-transform: uppercase;
  letter-spacing: -0.01em;
}

.me-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 3px solid var(--me-blue);
}
.me-header .me-mark {
  width: 40px; height: 40px; border-radius: 8px;
  background: var(--me-blue);
  color: #FFFFFF;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Roboto Condensed', sans-serif;
  font-weight: 700; font-size: 22px;
  flex-shrink: 0;
}
.me-header .me-word {
  font-family: 'Roboto Condensed', sans-serif;
  font-weight: 700;
  color: var(--me-blue);
  font-size: 15px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  line-height: 1.1;
}
.me-header .me-word small {
  display: block;
  font-family: 'Roboto', sans-serif;
  font-weight: 400;
  color: var(--me-gray);
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

[data-testid="stMetric"] {
  background: var(--me-bg-2);
  border: 1px solid var(--me-border);
  border-radius: 8px;
  padding: 12px 16px;
}
[data-testid="stMetricLabel"] {
  color: var(--me-gray) !important;
  font-family: 'Roboto', sans-serif !important;
  text-transform: uppercase;
  font-size: 0.75rem !important;
  letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
  color: var(--me-fg) !important;
  font-family: 'Roboto Condensed', sans-serif !important;
  font-weight: 700 !important;
}

.stButton > button[kind="primary"] {
  background: var(--me-blue);
  border-color: var(--me-blue);
  font-family: 'Roboto', sans-serif;
  font-weight: 700;
  border-radius: 6px;
}
.stButton > button[kind="primary"]:hover {
  background: #004F89;
  border-color: #004F89;
}

div[data-testid="stAlertContentSuccess"] { color: #0A5B31; }
div[data-baseweb="notification"]:has(div[data-testid="stAlertContentSuccess"]) {
  background: #E6F8EE; border-left: 4px solid var(--me-green);
}
div[data-baseweb="notification"]:has(div[data-testid="stAlertContentError"]) {
  border-left: 4px solid var(--me-red);
}
div[data-baseweb="notification"]:has(div[data-testid="stAlertContentWarning"]) {
  border-left: 4px solid #F5A623;
}
</style>
"""

HEADER_HTML = """
<div class="me-header">
  <div class="me-mark">M</div>
  <div class="me-word">Master Electronics<small>Datecode Finder</small></div>
</div>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(HEADER_HTML, unsafe_allow_html=True)
