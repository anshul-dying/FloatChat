import streamlit as st
import requests
from src.utils.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="FloatChat - ARGO Data Explorer",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 FloatChat - ARGO Ocean Data Assistant")
st.markdown("**AI-Powered Conversational Interface for ARGO Ocean Data Discovery**")
st.markdown("Ask questions about ARGO float data using natural language! This system specializes in Indian Ocean ARGO data analysis.")

# Example queries from the problem statement
st.subheader("💡 Example Queries")
example_queries = [
    "Show me all ARGO floats in the database",
    "What is the temperature data for platform 2901506?", 
    "Find salinity profiles from March 2023",
    "Show me floats near the equator (latitude between -5 and 5)",
    "What are the pressure levels available in the data?",
    "Compare temperature data from different platforms"
]

col1, col2 = st.columns(2)
for i, query in enumerate(example_queries):
    with col1 if i % 2 == 0 else col2:
        if st.button(f"💬 {query}", key=f"example_{query}"):
            st.session_state.user_input = query

st.divider()

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about ARGO data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Show progress indicator for query processing
        with st.spinner("🔍 Processing your query and generating SQL..."):
            response = requests.post("http://localhost:8000/chat", json={"text": prompt}).json()
        
        with st.chat_message("assistant"):
            st.markdown(response["response"])
            
            # Display SQL query if available
            if response.get("sql_query"):
                with st.expander("🔍 Generated SQL Query", expanded=False):
                    st.code(response["sql_query"], language="sql")
            
            # Display query results if available
            if response.get("query_results") and len(response["query_results"]) > 0:
                st.subheader("📊 Query Results")
                st.write(f"Found {response.get('result_count', 0)} records")
                
                # Convert to DataFrame for better display
                import pandas as pd
                df_results = pd.DataFrame(response["query_results"])
                
                # Display as table
                st.dataframe(df_results, use_container_width=True)
                
                # Add download button
                csv = df_results.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name=f"argo_query_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            elif response.get("sql_query"):
                st.info("💡 SQL query generated but not executed. You can copy and run it manually in your database client.")
            
            # Display execution error if any
            if response.get("execution_error"):
                st.error(f"⚠️ Query Execution Error: {response['execution_error']}")
        
        st.session_state.messages.append({"role": "assistant", "content": response["response"]})
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Error connecting to API: {e}")
            st.info("Make sure the API server is running: `python src/api/main.py`")

# Sidebar with additional info
with st.sidebar:
    st.header("📊 Quick Stats")
    st.info("""
    **Current Dataset:**
    - Indian Ocean ARGO floats
    - Temperature, Salinity, Pressure data
    - Interactive visualizations available
    """)
    
    st.header("🔗 Navigation")
    if st.button("📈 Go to Dashboard"):
        st.switch_page("pages/dashboard.py")
    
    st.header("ℹ️ About FloatChat")
    st.markdown("""
    FloatChat is an AI-powered system that:
    - Processes ARGO NetCDF data
    - Provides natural language querying
    - Offers interactive visualizations
    - Supports data export capabilities
    
    **Built for:** Ministry of Earth Sciences (MoES)
    **Organization:** INCOIS
    """)