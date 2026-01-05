import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect, text
import urllib.parse
import os

# Page config
st.set_page_config(page_title="Database Visualizer", layout="wide")

st.title("Database Visualizer 🔍")

# --- Connection Manager ---
def get_connection_string(db_type, host, port, user, password, db_name):
    """Constructs the SQLAlchemy connection string."""
    if db_type == "SQLite":
        return f"sqlite:///{db_name}"
    
    # Handle special characters in password
    if password:
        password = urllib.parse.quote_plus(password)
        
    if db_type == "PostgreSQL":
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    elif db_type == "MySQL":
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    elif db_type == "Microsoft SQL Server":
        # Requires pyodbc or similar, using generic default for now
        driver = "ODBC Driver 17 for SQL Server"
        return f"mssql+pyodbc://{user}:{password}@{host}:{port}/{db_name}?driver={urllib.parse.quote_plus(driver)}"
    return None

def main():
    # --- Sidebar: Connection Settings ---
    st.sidebar.header("🔌 Connection Settings")
    
    db_type = st.sidebar.selectbox(
        "Database Type",
        ["SQLite", "PostgreSQL", "MySQL"]
    )

    db_name = ""
    connection_string = ""
    
    if db_type == "SQLite":
        input_method = st.sidebar.radio("Select Database", ["Enter Path", "Browse Files"])
        
        if input_method == "Enter Path":
            db_name = st.sidebar.text_input("Database File Path", value="example.db")
        else:
            # File Browser Logic
            if 'cwd' not in st.session_state:
                st.session_state.cwd = os.getcwd()
            
            st.sidebar.markdown(f"**Current Dir:** `{st.session_state.cwd}`")
            
            # Navigation
            col1, col2 = st.sidebar.columns([1, 4])
            if col1.button("⬆️"):
                st.session_state.cwd = os.path.dirname(st.session_state.cwd)
                st.rerun()

            try:
                items = os.listdir(st.session_state.cwd)
                dirs = [d for d in items if os.path.isdir(os.path.join(st.session_state.cwd, d))]
                files = [f for f in items if os.path.isfile(os.path.join(st.session_state.cwd, f))]
                
                # Navigate directories
                selected_dir = st.sidebar.selectbox("Go to folder", ["Select folder..."] + sorted(dirs))
                if selected_dir != "Select folder...":
                    st.session_state.cwd = os.path.join(st.session_state.cwd, selected_dir)
                    st.rerun()

                # Select file
                db_extensions = ['.db', '.sqlite', '.sqlite3', '.sql']
                db_files = [f for f in files if any(f.lower().endswith(ext) for ext in db_extensions)]
                selected_file = st.sidebar.selectbox("Select Database File", ["Select file..."] + sorted(db_files))
                
                if selected_file != "Select file...":
                    db_name = os.path.join(st.session_state.cwd, selected_file)
            except PermissionError:
                st.error("Permission denied accessing this folder.")
        
        if db_name:
            connection_string = get_connection_string("SQLite", None, None, None, None, db_name)
    else:
        host = st.sidebar.text_input("Host", value="localhost")
        port_default = "5432" if db_type == "PostgreSQL" else "3306"
        port = st.sidebar.text_input("Port", value=port_default)
        user = st.sidebar.text_input("Username", value="root")
        password = st.sidebar.text_input("Password", type="password")
        db_name = st.sidebar.text_input("Database Name")
        
        if st.sidebar.button("Connect"):
            connection_string = get_connection_string(db_type, host, port, user, password, db_name)
    
    # Store connection string in session state to persist across reruns
    if connection_string:
        st.session_state['connection_string'] = connection_string

    # --- Main Area ---
    if 'connection_string' in st.session_state:
        try:
            engine = create_engine(st.session_state['connection_string'])
            inspector = inspect(engine)
            
            st.success(f"Connected to {db_type} database: {db_name}")
            
            # Get table names
            table_names = inspector.get_table_names()
            
            if not table_names:
                st.warning("No tables found in this database.")
                return

            # --- Table Explorer ---
            st.subheader("📂 Schema Explorer")
            selected_table = st.selectbox("Select a Table", table_names)
            
            if selected_table:
                # Columns Info
                columns = inspector.get_columns(selected_table)
                col_df = pd.DataFrame(columns)
                if not col_df.empty:
                    # Select relevant columns for schema view
                    display_cols = ['name', 'type', 'primary_key', 'nullable']
                    # Some drivers might not return all keys, check intersection
                    display_cols = [c for c in display_cols if c in col_df.columns]
                    
                    with st.expander("Show Schema details"):
                        st.dataframe(col_df[display_cols])

                # Data View
                st.subheader(f"📊 Data: {selected_table}")
                
                # Simple LIMIT query to avoid crashing with huge tables
                limit = st.slider("Rows to fetch", min_value=10, max_value=1000, value=100)
                
                try:
                    # Use text() for safe SQL execution
                    query = text(f"SELECT * FROM {selected_table} LIMIT :limit")
                    with engine.connect() as conn:
                        df = pd.read_sql(query, conn, params={"limit": limit})
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"Error reading data: {e}")

        except Exception as e:
            st.error(f"Failed to connect: {e}")
    else:
        st.info("Please configure the connection in the sidebar.")

if __name__ == "__main__":
    main()
