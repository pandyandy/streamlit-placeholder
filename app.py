import os

import streamlit as st
from keboola_streamlit import KeboolaStreamlit

TABLE_ID = "in.c-archive.archive1"
BUCKET_ID, TABLE_NAME = TABLE_ID.rsplit(".", 1)
QUERY = f'SELECT * FROM "{BUCKET_ID}"."{TABLE_NAME}"'

st.set_page_config(page_title="Streamlit Placeholder", page_icon="🧪", layout="wide")

# KBC_URL is injected by the data-app runtime. With Storage Access enabled the
# runtime also injects KBC_TOKEN, which can use the app's workspace; fall back to
# the bucket-scoped STORAGE_API_TOKEN secret otherwise.
token_name = "KBC_TOKEN" if os.environ.get("KBC_TOKEN") else "STORAGE_API_TOKEN"
keboola = KeboolaStreamlit(root_url=os.environ["KBC_URL"], token=os.environ[token_name])


@st.cache_data(ttl=600, show_spinner="Querying Keboola Query Service…")
def run_query(query: str):
    return keboola.query_service_execute_query(query, raise_on_error=True)


st.title("🧪 Streamlit Placeholder")
st.caption(f"Table: `{TABLE_ID}` via Query Service · token: `{token_name}`")
st.code(QUERY, language="sql")

with st.expander("Runtime environment"):
    for var in ["KBC_URL", "KBC_TOKEN", "QUERY_SERVICE_URL", "BRANCH_ID", "WORKSPACE_ID", "KBC_WORKSPACE_MANIFEST_PATH"]:
        st.write(f"`{var}`: {'set' if os.environ.get(var) else 'not set'}")

try:
    df = run_query(QUERY)
except Exception as e:
    st.error(f"Query failed: {e}")
    st.stop()

st.write(f"{len(df):,} rows × {len(df.columns)} columns")
st.dataframe(df, width="stretch")
