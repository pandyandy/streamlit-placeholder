import os

import pandas as pd
import streamlit as st
from keboola_streamlit import KeboolaStreamlit

TABLE_ID = "in.c-archive.archive1"
BUCKET_ID, TABLE_NAME = TABLE_ID.rsplit(".", 1)
TABLE_REF = f'"{BUCKET_ID}"."{TABLE_NAME}"'
QUERY = f"SELECT * FROM {TABLE_REF}"

st.set_page_config(page_title="Streamlit Placeholder", page_icon="🧪", layout="wide")

# KBC_URL is injected by the data-app runtime. With Storage Access enabled the
# runtime also injects KBC_TOKEN, which can use the app's workspace; fall back to
# the bucket-scoped STORAGE_API_TOKEN secret otherwise.
token_name = "KBC_TOKEN" if os.environ.get("KBC_TOKEN") else "STORAGE_API_TOKEN"
keboola = KeboolaStreamlit(root_url=os.environ["KBC_URL"], token=os.environ[token_name])


@st.cache_data(ttl=600, show_spinner="Querying Keboola Query Service…")
def run_query(query: str) -> pd.DataFrame:
    # Keep values as the exact strings Storage holds, so they can be matched in WHERE clauses
    df = keboola.query_service_execute_query(query, coerce_numeric=False, raise_on_error=True)
    # Storage's internal column is managed by Keboola, not the user
    return df.drop(columns=["_timestamp"], errors="ignore").reset_index(drop=True)


def sql_value(value) -> str:
    """Render a cell as a SQL string literal (Query Service has no bind parameters)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        value = ""
    return "'" + str(value).replace("'", "''") + "'"


def row_condition(row: pd.Series) -> str:
    # The table has no primary key, so a row is identified by all its original values
    return " AND ".join(f'"{col}" = {sql_value(row[col])}' for col in row.index)


def build_statements(df: pd.DataFrame, changes: dict) -> list[str]:
    statements = []
    for idx, edits in changes.get("edited_rows", {}).items():
        assignments = ", ".join(f'"{col}" = {sql_value(val)}' for col, val in edits.items())
        statements.append(f"UPDATE {TABLE_REF} SET {assignments} WHERE {row_condition(df.iloc[int(idx)])}")
    for idx in changes.get("deleted_rows", []):
        statements.append(f"DELETE FROM {TABLE_REF} WHERE {row_condition(df.iloc[int(idx)])}")
    for row in changes.get("added_rows", []):
        cols = ", ".join(f'"{col}"' for col in df.columns)
        values = ", ".join(sql_value(row.get(col)) for col in df.columns)
        statements.append(f"INSERT INTO {TABLE_REF} ({cols}) VALUES ({values})")
    return statements


st.title("🧪 Streamlit Placeholder")
st.caption(f"Table: `{TABLE_ID}` via Query Service · token: `{token_name}`")

with st.expander("Runtime environment"):
    for var in ["KBC_URL", "KBC_TOKEN", "QUERY_SERVICE_URL", "BRANCH_ID", "WORKSPACE_ID", "KBC_WORKSPACE_MANIFEST_PATH"]:
        st.write(f"`{var}`: {'set' if os.environ.get(var) else 'not set'}")

try:
    df = run_query(QUERY)
except Exception as e:
    st.error(f"Query failed: {e}")
    st.stop()

if "saved_message" in st.session_state:
    st.success(st.session_state.pop("saved_message"))
    with st.expander("Result of each statement", expanded=True):
        for statement, result in st.session_state.pop("save_results", []):
            st.code(statement, language="sql")
            st.dataframe(result, hide_index=True)

st.write(f"{len(df):,} rows × {len(df.columns)} columns · edit cells, add rows at the bottom, or select rows and delete them")

# A new key after each save resets the editor to the freshly queried data
editor_key = f"editor_{st.session_state.get('editor_version', 0)}"
st.data_editor(df, key=editor_key, num_rows="dynamic", hide_index=True, width="stretch")

statements = build_statements(df, st.session_state.get(editor_key, {}))

if statements:
    with st.expander(f"Pending changes: {len(statements)} SQL statement(s)", expanded=True):
        st.code(";\n".join(statements) + ";", language="sql")

save_col, discard_col = st.columns([1, 6])
if save_col.button("Save changes", type="primary", disabled=not statements):
    try:
        with st.spinner("Saving through Query Service…"):
            results = keboola.query_service_execute_query(
                statements, transactional=True, coerce_numeric=False, raise_on_error=True
            )
    except Exception as e:
        st.error(f"Save failed, nothing was changed: {e}")
    else:
        # Snowflake answers each DML statement with a row count ("number of rows updated", ...)
        st.session_state["save_results"] = list(zip(statements, results))
        st.session_state["saved_message"] = f"Query Service ran {len(statements)} statement(s)."
        st.session_state["editor_version"] = st.session_state.get("editor_version", 0) + 1
        run_query.clear()
        st.rerun()
if discard_col.button("Discard", disabled=not statements):
    st.session_state["editor_version"] = st.session_state.get("editor_version", 0) + 1
    st.rerun()
