"""
OptiVox DB - Complete Streamlit Frontend
Advanced AI Database Assistant Interface
Single file implementation for easy deployment
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8000"

OPERATION_MODES = {
    "assistant": {
        "name": "Assistant",
        "icon": "🤖",
        "description": "General-purpose AI database assistant"
    },
    "query": {
        "name": "Query Mode",
        "icon": "🔍",
        "description": "Natural language to SQL conversion"
    },
    "teaching": {
        "name": "Teaching Mode",
        "icon": "📚",
        "description": "Learn database concepts interactively"
    },
    "debug": {
        "name": "Debug Mode",
        "icon": "🐛",
        "description": "Troubleshoot and fix SQL issues"
    },
    "optimization": {
        "name": "Optimization",
        "icon": "⚡",
        "description": "Optimize query performance"
    },
    "search": {
        "name": "Search",
        "icon": "🔎",
        "description": "Search database schema"
    }
}

DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]


# ============================================================================
# API CLIENT CLASS
# ============================================================================

class APIClient:
    """Client for OptiVox DB API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            raise

    def health_check(self) -> Dict[str, Any]:
        return self._make_request("GET", "/api/health")

    def get_system_info(self) -> Dict[str, Any]:
        return self._make_request("GET", "/api/info")

    def chat(self, message: str, connection: Dict[str, Any], session_id: Optional[str] = None,
             mode: str = "assistant", allow_destructive: bool = False, confirm: bool = False) -> Dict[str, Any]:
        payload = {
            "message": message,
            "connection": connection,
            "session_id": session_id,
            "mode": mode,
            "allow_destructive": allow_destructive,
            "confirm": confirm,
            "stream": False
        }
        return self._make_request("POST", "/api/chat", json=payload)

    def natural_query(self, prompt: str, connection: Dict[str, Any],
                      session_id: Optional[str] = None, allow_destructive: bool = False) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "connection": connection,
            "session_id": session_id,
            "allow_destructive": allow_destructive,
            "confirm": False
        }
        return self._make_request("POST", "/api/query/natural", json=payload)

    def execute_sql(self, sql: str, connection: Dict[str, Any], allow_destructive: bool = False) -> Dict[str, Any]:
        params = {"sql": sql, "connection": connection, "allow_destructive": allow_destructive}
        return self._make_request("POST", "/api/query/execute", json=params)

    def get_schema(self, connection: Dict[str, Any], force_refresh: bool = False) -> Dict[str, Any]:
        payload = {**connection, "force_refresh": force_refresh}
        return self._make_request("POST", "/api/schema/info", json=payload)

    def analyze_schema(self, connection: Dict[str, Any], include_recommendations: bool = True) -> Dict[str, Any]:
        payload = {
            "connection": connection,
            "include_recommendations": include_recommendations,
            "analyze_relationships": True
        }
        return self._make_request("POST", "/api/schema/analyze", json=payload)

    def optimize_query(self, sql: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"connection": connection, "sql": sql, "analyze_indexes": True, "suggest_rewrites": True}
        return self._make_request("POST", "/api/query/optimize", json=payload)

    def debug_query(self, sql: str, error_message: Optional[str] = None,
                    connection: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"sql": sql, "error_message": error_message, "connection": connection}
        return self._make_request("POST", "/api/query/debug", json=payload)

    def explain_concept(self, topic: str, difficulty: str = "Beginner",
                        include_examples: bool = True) -> Dict[str, Any]:
        payload = {"topic": topic, "difficulty": difficulty,
                   "include_examples": include_examples, "include_exercises": True}
        return self._make_request("POST", "/api/learn/explain", json=payload)

    def get_learning_topics(self) -> Dict[str, Any]:
        return self._make_request("GET", "/api/learn/topics")

    def get_sessions(self) -> Dict[str, Any]:
        return self._make_request("GET", "/api/sessions")


# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(API_BASE_URL)

    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Chat Assistant"

    if "connection_config" not in st.session_state:
        st.session_state.connection_config = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "backend_health" not in st.session_state:
        st.session_state.backend_health = None

    if "schema_data" not in st.session_state:
        st.session_state.schema_data = None


# ============================================================================
# SIDEBAR COMPONENT
# ============================================================================

def render_sidebar():
    """Render sidebar with navigation and configuration."""
    with st.sidebar:
        st.title("⚙️ OptiVox DB")

        # Navigation
        st.header("📍 Navigation")
        pages = ["Chat Assistant", "Query Builder", "Schema Explorer", "Learning Hub", "Debugger"]

        selected_page = st.radio("Go to:", pages, index=pages.index(st.session_state.current_page))

        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()

        st.divider()

        # Database Configuration
        st.header("🗄️ Database Connection")

        with st.form("db_config_form"):
            host = st.text_input("Host", value="localhost")
            port = st.number_input("Port", value=3306, min_value=1, max_value=65535)
            database = st.text_input("Database", value="")
            user = st.text_input("User", value="root")
            password = st.text_input("Password", type="password", value="")

            submit_button = st.form_submit_button("💾 Save Connection", use_container_width=True)

            if submit_button:
                if not all([host, database, user]):
                    st.error("Please fill in all required fields!")
                else:
                    st.session_state.connection_config = {
                        "host": host,
                        "port": int(port),
                        "database": database,
                        "user": user,
                        "password": password
                    }
                    st.success("✅ Connection saved!")
                    st.rerun()

        # Connection Status
        if st.session_state.connection_config:
            st.success("🟢 Connection Configured")
            config = st.session_state.connection_config
            st.caption(f"**Database:** {config['database']}")
            st.caption(f"**Host:** {config['host']}:{config['port']}")
        else:
            st.warning("🔴 No Connection Configured")

        st.divider()

        # Backend Status
        st.header("📊 Status")
        if st.button("🔄 Check Backend", use_container_width=True):
            try:
                health = st.session_state.api_client.health_check()
                st.session_state.backend_health = health
                st.success("🟢 Backend Healthy")
            except:
                st.error("🔴 Backend Offline")

        if st.session_state.backend_health:
            health = st.session_state.backend_health
            if health.get("status") == "healthy":
                services = health.get("services", {})
                st.caption(f"AI: {'✅' if services.get('ai') else '❌'}")
                st.caption(f"DB: {'✅' if services.get('database') else '❌'}")

        st.divider()

        # Session Info
        st.caption(f"**Session:** {st.session_state.session_id[:12]}...")

        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
            st.session_state.chat_history = []
            st.success("New session created!")
            st.rerun()


# ============================================================================
# CHAT ASSISTANT PAGE
# ============================================================================

def render_chat_assistant():
    """Render chat assistant page."""
    st.header("💬 Chat Assistant")

    if not st.session_state.connection_config:
        st.warning("⚠️ Please configure database connection in the sidebar first.")
        return

    # Mode Selection
    col1, col2 = st.columns([3, 1])

    with col1:
        mode_options = {k: f"{v['icon']} {v['name']}" for k, v in OPERATION_MODES.items()}
        selected_mode = st.selectbox(
            "Operation Mode",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x]
        )

    with col2:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Mode Description
    mode_info = OPERATION_MODES[selected_mode]
    st.info(f"**{mode_info['icon']} {mode_info['name']}:** {mode_info['description']}")

    # Chat History
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])

                    # Show SQL
                    if msg.get("sql"):
                        with st.expander("📝 Generated SQL"):
                            st.code(msg["sql"], language="sql")

                    # Show Results
                    if msg.get("result") and msg["result"].get("success"):
                        result = msg["result"]
                        if result.get("data"):
                            with st.expander("📊 Query Results"):
                                df = pd.DataFrame(result["data"])
                                st.dataframe(df, use_container_width=True)
                                st.caption(f"Rows: {len(result['data'])}")
    else:
        st.info("👋 Start a conversation! Ask me anything about your database.")

    # Chat Input
    st.divider()

    user_input = st.text_area(
        "Your message:",
        placeholder="Ask me anything about your database...",
        height=100,
        key="chat_input"
    )

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        send_button = st.button("📤 Send", use_container_width=True, type="primary")

    with col2:
        allow_destructive = st.checkbox("Destructive", value=False)

    with col3:
        confirm = st.checkbox("Confirm", value=False)

    if send_button and user_input:
        # Add user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })

        with st.spinner("🤔 Thinking..."):
            try:
                response = st.session_state.api_client.chat(
                    message=user_input,
                    connection=st.session_state.connection_config,
                    session_id=st.session_state.session_id,
                    mode=selected_mode,
                    allow_destructive=allow_destructive,
                    confirm=confirm
                )

                # Add assistant response
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.get("response", "No response"),
                    "sql": response.get("sql"),
                    "result": response.get("result")
                })

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# ============================================================================
# QUERY BUILDER PAGE
# ============================================================================

def render_query_builder():
    """Render query builder page."""
    st.header("🔍 Query Builder")

    if not st.session_state.connection_config:
        st.warning("⚠️ Please configure database connection in the sidebar first.")
        return

    tab1, tab2 = st.tabs(["📝 Natural Language", "💻 Raw SQL"])

    # Natural Language Tab
    with tab1:
        st.subheader("Natural Language to SQL")

        nl_query = st.text_area(
            "Describe what you want to query:",
            placeholder="e.g., Show all users who registered in the last 30 days",
            height=100
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔮 Generate SQL", use_container_width=True, type="primary"):
                if nl_query:
                    with st.spinner("Generating SQL..."):
                        try:
                            response = st.session_state.api_client.natural_query(
                                prompt=nl_query,
                                connection=st.session_state.connection_config,
                                session_id=st.session_state.session_id
                            )

                            if response.get("success"):
                                st.success("✅ Query generated successfully!")
                                st.code(response.get("sql", ""), language="sql")

                                if response.get("data"):
                                    st.subheader("📊 Results")
                                    df = pd.DataFrame(response["data"])
                                    st.dataframe(df, use_container_width=True)

                                    # Download button
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        "📥 Download CSV",
                                        csv,
                                        "query_results.csv",
                                        "text/csv"
                                    )
                            else:
                                st.error(f"❌ {response.get('message', 'Query failed')}")

                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

    # Raw SQL Tab
    with tab2:
        st.subheader("Execute Raw SQL")

        sql_query = st.text_area(
            "SQL Query:",
            placeholder="SELECT * FROM users LIMIT 10;",
            height=150,
            key="raw_sql"
        )

        allow_destructive = st.checkbox("Allow Destructive Operations (DELETE, UPDATE, DROP)")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("▶️ Execute Query", use_container_width=True, type="primary"):
                if sql_query:
                    with st.spinner("Executing query..."):
                        try:
                            response = st.session_state.api_client.execute_sql(
                                sql=sql_query,
                                connection=st.session_state.connection_config,
                                allow_destructive=allow_destructive
                            )

                            if response.get("success"):
                                st.success("✅ Query executed successfully!")

                                if response.get("data"):
                                    df = pd.DataFrame(response["data"])
                                    st.dataframe(df, use_container_width=True)
                                    st.caption(f"Rows returned: {len(response['data'])}")
                                elif response.get("rows_affected") is not None:
                                    st.info(f"Rows affected: {response['rows_affected']}")
                            else:
                                st.error(f"❌ {response.get('error', 'Query failed')}")

                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

        with col2:
            if st.button("⚡ Optimize Query", use_container_width=True):
                if sql_query:
                    with st.spinner("Analyzing query..."):
                        try:
                            response = st.session_state.api_client.optimize_query(
                                sql=sql_query,
                                connection=st.session_state.connection_config
                            )

                            if response.get("success"):
                                st.subheader("🚀 Optimization Analysis")
                                st.markdown(response["data"]["optimization"])

                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")


# ============================================================================
# SCHEMA EXPLORER PAGE
# ============================================================================

def render_schema_explorer():
    """Render schema explorer page."""
    st.header("🗂️ Schema Explorer")

    if not st.session_state.connection_config:
        st.warning("⚠️ Please configure database connection in the sidebar first.")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔄 Load Schema", use_container_width=True, type="primary"):
            with st.spinner("Loading schema..."):
                try:
                    response = st.session_state.api_client.get_schema(
                        connection=st.session_state.connection_config,
                        force_refresh=True
                    )

                    if response.get("success"):
                        st.session_state.schema_data = response["data"]
                        st.success("✅ Schema loaded successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with col2:
        if st.button("🔬 Analyze Schema", use_container_width=True):
            with st.spinner("Analyzing schema..."):
                try:
                    response = st.session_state.api_client.analyze_schema(
                        connection=st.session_state.connection_config
                    )

                    if response.get("success"):
                        st.subheader("📊 Schema Analysis")
                        st.markdown(response["data"]["analysis"])
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Display Schema
    if st.session_state.schema_data:
        schema = st.session_state.schema_data
        tables = schema.get("tables", {})

        st.divider()
        st.subheader(f"📊 Database Tables ({len(tables)})")

        # Search
        search = st.text_input("🔍 Search tables...", "")

        # Display tables
        for table_name, table_info in tables.items():
            if search.lower() in table_name.lower():
                with st.expander(f"📋 {table_name}"):
                    columns = table_info.get("columns", [])

                    # Columns table
                    col_data = []
                    for col in columns:
                        col_data.append({
                            "Column": col["name"],
                            "Type": col["type"],
                            "Nullable": "Yes" if col["nullable"] else "No",
                            "Primary Key": "Yes" if col.get("primary_key") else "No"
                        })

                    if col_data:
                        df = pd.DataFrame(col_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    # Indexes
                    indexes = table_info.get("indexes", [])
                    if indexes:
                        st.caption(f"**Indexes:** {len(indexes)}")
                        for idx in indexes:
                            st.caption(f"  • {idx.get('name', 'unnamed')}")

                    # Foreign Keys
                    fks = table_info.get("foreign_keys", [])
                    if fks:
                        st.caption(f"**Foreign Keys:** {len(fks)}")
                        for fk in fks:
                            st.caption(f"  • → {fk.get('referred_table', 'unknown')}")


# ============================================================================
# LEARNING HUB PAGE
# ============================================================================

def render_learning_hub():
    """Render learning hub page."""
    st.header("📚 Learning Hub")

    tab1, tab2 = st.tabs(["📖 Learn Concept", "📋 Browse Topics"])

    with tab1:
        st.subheader("Learn a Database Concept")

        topic = st.text_input("What would you like to learn?", placeholder="e.g., SQL Joins, Indexes, Normalization")

        difficulty = st.select_slider("Difficulty Level", options=DIFFICULTY_LEVELS)

        col1, col2 = st.columns(2)
        with col1:
            include_examples = st.checkbox("Include Examples", value=True)
        with col2:
            include_exercises = st.checkbox("Include Exercises", value=True)

        if st.button("🎓 Learn", use_container_width=True, type="primary"):
            if topic:
                with st.spinner("Preparing lesson..."):
                    try:
                        response = st.session_state.api_client.explain_concept(
                            topic=topic,
                            difficulty=difficulty,
                            include_examples=include_examples
                        )

                        if response.get("success"):
                            st.divider()
                            st.markdown(response["data"]["explanation"])

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    with tab2:
        st.subheader("Available Topics")

        try:
            response = st.session_state.api_client.get_learning_topics()

            if response.get("success"):
                topics = response["data"]

                for level, topic_list in topics.items():
                    with st.expander(f"📌 {level.capitalize()}"):
                        for topic in topic_list:
                            if st.button(f"📖 {topic}", key=f"topic_{level}_{topic}"):
                                # Trigger learning for this topic
                                st.session_state.selected_topic = topic
                                st.session_state.current_page = "Learning Hub"
                                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


# ============================================================================
# DEBUGGER PAGE
# ============================================================================

def render_debugger():
    """Render SQL debugger page."""
    st.header("🐛 SQL Debugger")

    st.subheader("Debug Your SQL Query")

    sql_query = st.text_area(
        "SQL Query:",
        placeholder="Paste your problematic SQL query here...",
        height=150
    )

    error_message = st.text_area(
        "Error Message (optional):",
        placeholder="Paste any error message you received...",
        height=100
    )

    if st.button("🔍 Debug Query", use_container_width=True, type="primary"):
        if sql_query:
            with st.spinner("Analyzing query..."):
                try:
                    response = st.session_state.api_client.debug_query(
                        sql=sql_query,
                        error_message=error_message if error_message else None,
                        connection=st.session_state.connection_config
                    )

                    if response.get("success"):
                        st.divider()
                        st.subheader("🔬 Debug Analysis")
                        st.markdown(response["data"]["debug_analysis"])

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""

    # Page config
    st.set_page_config(
        page_title="OptiVox DB - AI Database Assistant",
        page_icon="🗄️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
        }
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(120deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Route to appropriate page
    page = st.session_state.current_page

    if page == "Chat Assistant":
        render_chat_assistant()
    elif page == "Query Builder":
        render_query_builder()
    elif page == "Schema Explorer":
        render_schema_explorer()
    elif page == "Learning Hub":
        render_learning_hub()
    elif page == "Debugger":
        render_debugger()

    # Footer
    st.divider()
    st.caption("OptiVox DB v2.0 | AI-Powered Database Assistant | Founder Kishore Ram M")


if __name__ == "__main__":
    main()
