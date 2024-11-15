import os

import streamlit as st
from streamlit_ace import st_ace


from typing import Callable, Dict, Sequence
from sqlglot import parse_one
from sqlglot.expressions import Select
from sqlglot.optimizer import RULES, optimize
from sqlfmt.api import Mode, format_string

RULE_MAPPING: Dict[str, Callable] = {rule.__name__: rule for rule in RULES}

SAMPLE_QUERY: str = """WITH users AS (
    SELECT *
    FROM users_table),
orders AS (
    SELECT *
    FROM orders_table),
combined AS (
    SELECT users.id, users.name, orders.order_id, orders.total
    FROM users
    JOIN orders ON users.id = orders.user_id)
SELECT combined.id, combined.name, combined.order_id, combined.total
FROM combined
"""


def apply_optimizations(query: str, rules: Sequence[Callable] = RULES, remove_ctes: bool = False) -> Select:
    return optimize(ast=parse_one(query) , rules=rules, leave_tables_isolated=not(remove_ctes))


def format_sql_with_sqlfmt(query: str) -> str:
    return format_string(query, mode = Mode())


st.set_page_config(layout="wide")


# Set custom CSS
st.markdown(
    """
# Optimize and lint SQL using [sqlglot](https://github.com/tobymao/sqlglot) and [sqlfmt](http://sqlfmt.com/)
 
<style>
body {
    background-color: black;
    color: white;
}
</style>
""",
    unsafe_allow_html=True,
)

left, right = st.columns(2)

# Add rule selector
selected_rules = st.multiselect(
    'Optimization [rules](https://github.com/tobymao/sqlglot/blob/main/sqlglot/optimizer/optimizer.py). Drop "canonicalize" rule to prevent quoting.',
    list(RULE_MAPPING.keys()),
    default=list(RULE_MAPPING.keys()),
)

# Add checkboxes and button
cols = [col for col in st.columns(12)]
remove_ctes = cols[0].checkbox("Remove CTEs", on_change=None)
format_with_sqlfmt = cols[1].checkbox("Lint w/ sqlfmt", on_change=None)
optimize_button = st.button("Optimize SQL")

# Initialize session state
if "new_query" not in st.session_state:
    st.session_state.new_query = ""

if "state" not in st.session_state:
    st.session_state.state = 0


# Add input editor
def _generate_editor_widget(value: str, **kwargs) -> str:
    return st_ace(
        value=value,
        height=os.getenv("EDITOR_HEIGHT", 400),
        theme="monokai",
        language="sql",
        font_size=os.getenv("FONT_SIZE", 14),
        wrap=True,
        auto_update=True,
        **kwargs,
    )


with left:
    sql_input = _generate_editor_widget(SAMPLE_QUERY)

# Optimize and lint query
if optimize_button:
    try:
        rules = [RULE_MAPPING[rule] for rule in selected_rules]
        new_query = apply_optimizations(sql_input, rules, remove_ctes).sql(pretty=True)
        if format_with_sqlfmt:
            new_query = format_sql_with_sqlfmt(new_query)
        st.session_state.new_query = new_query
        st.session_state.state += 1
    except Exception as e:
        st.error(f"Error: {e}")

# Add output editor
with right:
    _generate_editor_widget(
        st.session_state.new_query, readonly=True, key=f"ace-{st.session_state.state}"
    )

st.markdown(
    f"""
    <a href="{os.getenv('GITHUB_REPO')}" target="_blank">
    <img src="{os.getenv('STAR_BADGE_URL')}" alt="Star on GitHub"></a>
    """,
    unsafe_allow_html=True,
)
