from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever, Document
from pydantic import Field
from src.database.vector_db import init_vector_db
from src.llm.models import get_llm
from src.database.query_engine import execute_sql_query
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChromaRetriever(BaseRetriever):
    """Custom retriever that directly uses ChromaDB collection"""
    
    collection: object = Field(exclude=True)  # Exclude from serialization
    
    def get_relevant_documents(self, query: str):
        """Retrieve relevant documents from ChromaDB"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            
            documents = []
            if results['documents'] and results['documents'][0]:
                for doc in results['documents'][0]:
                    documents.append(Document(page_content=doc))
            
            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []


def setup_rag(metadata, llm_type="mock"):
    # Step 1: Initialize ChromaDB collection
    collection = init_vector_db(metadata)

    # Step 2: Create custom retriever
    retriever = ChromaRetriever(collection=collection)

    # Step 3: Get LLM instance
    llm = get_llm(model_type=llm_type)

    # Step 4: Define enhanced prompt template for ARGO data queries with SQL generation
    prompt_template = """
    You are FloatChat, an AI-powered ocean data assistant specializing in ARGO float data analysis for the Indian Ocean region.
    You help users discover, query, and visualize oceanographic data through natural language.

    ARGO Float Context:
    {context}

    User Question: {question}

    Instructions for answering ocean data queries:
    
    For location-based queries (e.g., "near the equator", "Arabian Sea"):
    - Identify relevant latitude/longitude ranges from the context
    - List specific float IDs in those regions
    - Provide geographic context (e.g., "Arabian Sea region: 10°N-25°N, 50°E-80°E")
    
    For temporal queries (e.g., "March 2023", "last 6 months"):
    - Extract time ranges from the context
    - Identify floats active during those periods
    - Provide specific date ranges when available
    
    For parameter queries (e.g., "salinity profiles", "temperature", "BGC parameters"):
    - Explain what parameters are available (TEMP, PSAL, PRES)
    - Note that BGC parameters may not be available in current dataset
    - Suggest visualization approaches
    
    For comparison queries (e.g., "compare", "nearest floats"):
    - Identify relevant floats for comparison
    - Suggest specific float IDs and their characteristics
    - Recommend using the dashboard for detailed comparisons
    
    Always:
    - Be specific with float IDs, coordinates, and time ranges
    - Suggest using the dashboard for detailed visualizations
    - Mention data limitations when relevant
    - Provide actionable next steps for data exploration

    Additionally, generate a SQL query that would retrieve the relevant data from the actual ARGO database.
    The database schema is:
    - Database: floatchat
    - Table: argo_data
    - Columns: id, source_file, profile_index, platform_number, cycle_number, juld, latitude, longitude, level_index, pressure_dbar, temperature_c, salinity_psu, pres_qc, temp_qc, psal_qc, pres_variable, temp_variable, psal_variable, created_at
    
    IMPORTANT SQL RULES:
    - QC columns (pres_qc, temp_qc, psal_qc) are VARCHAR, so use string comparisons: psal_qc = '1' not psal_qc = 1
    - Do NOT include comments in SQL queries (no -- or /* */)
    - Use proper data types for comparisons
    - ALWAYS include LIMIT clause for large datasets (e.g., LIMIT 50)
    - Use specific WHERE conditions to reduce data scope
    - Prefer COUNT(*) for counting instead of SELECT * for large tables
    - Use DISTINCT when looking for unique values
    - Keep queries simple and focused - avoid complex joins or subqueries
    - Use ORDER BY sparingly - it can be slow on large datasets
    
    Format your response as:
    
    **SQL Query:**
    ```sql
    [Your generated SQL query here]
    ```
    
    **Answer:**
    [Your detailed response here]

    Answer:
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["question", "context"]
    )

    # Step 5: Build RetrievalQA chain
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt}
    )

    return chain


def run_rag_query_with_results(chain, question):
    """Run RAG query and return both response and query results"""
    result = chain.invoke({"query": question})
    
    # Extract SQL query from the response
    response_text = result["result"]
    sql_query = extract_sql_query(response_text)
    
    query_results = None
    result_count = 0
    execution_error = None

    # If no SQL was extracted, try simple heuristics to generate a safe fallback query
    ql = (question or "").lower()
    is_count_rows = False
    is_count_floats = False
    is_count_profiles = False
    if not sql_query:
        if "how many rows" in ql or ("rows" in ql and "how many" in ql) or "rows in database" in ql:
            sql_query = "SELECT COUNT(*) AS count FROM argo_data"
            is_count_rows = True
        elif "how many floats" in ql or ("floats" in ql and "how many" in ql):
            sql_query = "SELECT COUNT(DISTINCT platform_number) AS count FROM argo_data"
            is_count_floats = True
        elif "how many profiles" in ql or ("profiles" in ql and "how many" in ql):
            sql_query = "SELECT COUNT(DISTINCT profile_index) AS count FROM argo_data"
            is_count_profiles = True

    # If we now have SQL, execute it against PostgreSQL and include results
    if sql_query:
        try:
            logger.info("=" * 80)
            logger.info("🔍 GENERATED SQL QUERY:")
            logger.info("=" * 80)
            logger.info(sql_query)
            logger.info("=" * 80)
            df = execute_sql_query(sql_query, timeout=15, max_rows=200)
            query_results = df.to_dict(orient="records") if df is not None else []
            result_count = len(query_results)
            logger.info(f"✅ SQL executed, returned {result_count} rows from Postgres")

            # If this was a COUNT query, result_count is number of rows returned (likely 1),
            # so extract the actual count value for clarity
            if query_results and isinstance(query_results[0], dict):
                try:
                    # Try common key 'count' first, otherwise pick the first numeric value
                    count_value = query_results[0].get("count")
                    if count_value is None:
                        for v in query_results[0].values():
                            if isinstance(v, (int, float)):
                                count_value = v
                                break
                    if count_value is not None:
                        actual_count = int(count_value)
                        # If the user's intent was a count question, provide a clear authoritative answer
                        if is_count_rows:
                            response_text = f"There are {actual_count} rows in the database."
                        elif is_count_floats:
                            response_text = f"There are {actual_count} distinct ARGO floats in the database."
                        elif is_count_profiles:
                            response_text = f"There are {actual_count} distinct profiles in the database."
                        else:
                            # Otherwise, append a concise data-backed line
                            response_text = f"{response_text}\n\nData check: The database reports {actual_count} records for this request."
                except Exception:
                    pass
        except Exception as e:
            execution_error = str(e)
            logger.error(f"❌ SQL execution failed: {execution_error}")
    else:
        logger.info("⚠️  No SQL query generated for this question")

    logger.info(f"RAG question: {question}")
    logger.info(f"RAG response: {response_text}")
    
    return {
        "response": response_text,
        "sql_query": sql_query,
        "query_results": query_results,
        "result_count": result_count,
        "execution_error": execution_error
    }


def run_rag_query(chain, question):
    """Run RAG query and return just the response text (backward compatibility)"""
    result = run_rag_query_with_results(chain, question)
    return result["response"]


def extract_sql_query(response_text):
    """Extract SQL query from the LLM response"""
    import re
    
    # Look for SQL query in code blocks
    sql_pattern = r'```sql\s*(.*?)\s*```'
    match = re.search(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)
    
    if match:
        sql_query = match.group(1).strip()
        sql_query = clean_sql_query(sql_query)
        return optimize_sql_query(sql_query)
    
    # Look for SQL query after "SQL Query:" marker
    sql_pattern2 = r'\*\*SQL Query:\*\*\s*```sql\s*(.*?)\s*```'
    match2 = re.search(sql_pattern2, response_text, re.DOTALL | re.IGNORECASE)
    
    if match2:
        sql_query = match2.group(1).strip()
        sql_query = clean_sql_query(sql_query)
        return optimize_sql_query(sql_query)
    
    return None


def clean_sql_query(sql_query):
    """Clean SQL query by removing comments and fixing common issues"""
    import re
    
    # Remove single-line comments (-- comments)
    sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    
    # Remove multi-line comments (/* */ comments)
    sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
    
    # Fix common QC column comparisons (integer to string)
    sql_query = re.sub(r'\bpsal_qc\s*=\s*(\d+)\b', r"psal_qc = '\1'", sql_query)
    sql_query = re.sub(r'\btemp_qc\s*=\s*(\d+)\b', r"temp_qc = '\1'", sql_query)
    sql_query = re.sub(r'\bpres_qc\s*=\s*(\d+)\b', r"pres_qc = '\1'", sql_query)
    
    # Clean up extra whitespace
    sql_query = re.sub(r'\s+', ' ', sql_query).strip()
    
    return sql_query


def optimize_sql_query(sql_query):
    """Analyze and optimize SQL query for better performance"""
    import re
    
    # Convert to uppercase for analysis
    query_upper = sql_query.upper()
    
    # Check if query is likely to be slow
    slow_patterns = [
        r'SELECT\s+\*\s+FROM',  # SELECT * FROM
        r'ORDER\s+BY.*LIMIT',   # ORDER BY without LIMIT
        r'WHERE.*LIKE.*%',      # LIKE with wildcards
    ]
    
    optimizations = []
    
    # Add LIMIT if missing and query could return many rows
    if 'SELECT' in query_upper and 'FROM' in query_upper:
        if 'LIMIT' not in query_upper and 'COUNT' not in query_upper:
            if not any(word in query_upper for word in ['GROUP BY', 'HAVING', 'DISTINCT']):
                sql_query = f"{sql_query.rstrip(';')} LIMIT 50"
                optimizations.append("Added LIMIT 50 for performance")
    
    # Suggest using COUNT for counting queries
    if re.search(r'SELECT\s+\*\s+FROM.*WHERE', query_upper):
        if 'count' in sql_query.lower() or 'how many' in sql_query.lower():
            sql_query = re.sub(r'SELECT\s+\*\s+FROM', 'SELECT COUNT(*) FROM', sql_query, flags=re.IGNORECASE)
            optimizations.append("Optimized to COUNT(*) for counting")
    
    # Log optimizations
    if optimizations:
        logger.info(f"SQL optimizations applied: {', '.join(optimizations)}")
    
    return sql_query