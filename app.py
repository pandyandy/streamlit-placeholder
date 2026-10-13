import os

import streamlit as st
from keboola_streamlit import KeboolaStreamlit

TABLE_ID = "in.c-CSAS_JS.KS_SOURCE_TABLE"

st.set_page_config(page_title="Streamlit Placeholder", page_icon="🧪", layout="wide")

# KBC_URL is injected by the data-app runtime; STORAGE_API_TOKEN is an app secret
keboola = KeboolaStreamlit(root_url=os.environ["KBC_URL"], token=os.environ["STORAGE_API_TOKEN"])


@st.cache_data(ttl=600, show_spinner="Loading table from Keboola Storage…")
def load_table(table_id: str):
    return keboola.read_table(table_id=table_id)


st.title("🧪 Streamlit Placeholder")
st.caption(f"Table: `{TABLE_ID}`")

df = load_table(TABLE_ID)
st.write(f"{len(df):,} rows × {len(df.columns)} columns")
st.dataframe(df, width="stretch")
