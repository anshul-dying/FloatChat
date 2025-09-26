from flask import Blueprint, request, jsonify
import re
from src.llm.rag_pipeline import setup_rag, run_rag_query_with_results
from src.data_ingestion.metadata_extractor import extract_metadata
from src.utils.logging import get_logger
import os
import yaml

chat_bp = Blueprint("chat", __name__)
logger = get_logger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open("config/config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def sanitize_response_for_user_mode(text: str) -> str:
    """Remove any SQL-looking content from the response for non-developer users.

    Strips fenced SQL code blocks and obvious SQL statements to avoid leaking SQL.
    """
    if not text:
        return text
    cleaned = text
    # Remove fenced ```sql ... ``` blocks
    cleaned = re.sub(r"```\s*sql[\s\S]*?```", "", cleaned, flags=re.IGNORECASE)
    # Remove any fenced code blocks that start with SELECT/INSERT/UPDATE/DELETE
    cleaned = re.sub(r"```[\s\S]*?(select|insert|update|delete)[\s\S]*?```", "", cleaned, flags=re.IGNORECASE)
    # Remove standalone lines that look like SQL statements
    cleaned = re.sub(r"^\s*(select|insert|update|delete)\b[\s\S]*?$", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
    # Collapse excessive blank lines introduced by removals
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

@chat_bp.route("/chat", methods=["POST"])
def chat_query():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "")
    profession = body.get("profession", "researcher")
    lat = body.get("lat")
    lon = body.get("lon")
    developer_mode = bool(body.get("developerMode", False))

    logger.info(f"Received chat query: {text}")
    logger.info(f"Profession: {profession}, Lat: {lat}, Lon: {lon}")
    
    try:
        # Get LLM type from config.yaml or environment
        config = load_config()
        llm_type = os.getenv("LLM_TYPE") or config.get("llm", {}).get("model", "mock")
        
        # Map config model names to our LLM types
        api_key = config.get("llm", {}).get("api_key", "")
        if api_key.startswith("sk-or-"):
            llm_type = "openrouter"
        elif api_key.startswith("hf_"):
            llm_type = "huggingface"
        elif "openrouter" in llm_type.lower() or "deepseek" in llm_type.lower():
            llm_type = "openrouter"
        elif "huggingface" in llm_type.lower() or "hf_" in llm_type.lower():
            llm_type = "huggingface"
        elif "openai" in llm_type.lower() and not api_key.startswith("hf_"):
            llm_type = "openai"
        elif "anthropic" in llm_type.lower():
            llm_type = "anthropic"
        else:
            llm_type = "mock"
        
        logger.info(f"Using LLM type: {llm_type}")
        
        metadata = extract_metadata()
        rag_chain = setup_rag(metadata, llm_type=llm_type)
        # Adjust prompt behavior based on developer mode
        if developer_mode:
            mode_prefix = (
                "You are in developer mode. Prefer precise answers and include an executable SQL query for Postgres (table argo_data) when relevant. "
                "Ensure queries target PostgreSQL, not parquet."
            )
        else:
            mode_prefix = (
                "You are in user mode for non-developers. Do NOT generate or mention SQL or code. "
                "Explain findings in friendly language and summarize insights succinctly."
            )

        text_with_mode = f"{mode_prefix}\n\nUser query: {text}"

        result = run_rag_query_with_results(rag_chain, text_with_mode)
        
        logger.info(f"Query completed successfully. Response length: {len(result.get('response', ''))}")
        
        response_text = result.get("response")
        if not developer_mode:
            response_text = sanitize_response_for_user_mode(response_text)

        return jsonify({
            "response": response_text,
            "sql_query": result.get("sql_query") if developer_mode else None,
            "query_results": result.get("query_results"),
            "result_count": result.get("result_count"),
            "execution_error": result.get("execution_error"),
        })
    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}")
        
        # If there's an authentication error, fall back to mock LLM
        if "401" in str(e) or "User not found" in str(e) or "authentication" in str(e).lower():
            logger.info("Authentication error detected, falling back to mock LLM")
            try:
                metadata = extract_metadata()
                rag_chain = setup_rag(metadata, llm_type="mock")
                result = run_rag_query_with_results(rag_chain, text_with_mode)
                
                response_text = result.get("response")
                if not developer_mode:
                    response_text = sanitize_response_for_user_mode(response_text)

                return jsonify({
                    "response": response_text,
                    "sql_query": result.get("sql_query") if developer_mode else None,
                    "query_results": result.get("query_results"),
                    "result_count": result.get("result_count"),
                    "execution_error": result.get("execution_error"),
                })
            except Exception as fallback_error:
                logger.error(f"Fallback to mock LLM also failed: {str(fallback_error)}")
                return jsonify({
                    "response": f"Error processing your query: {str(fallback_error)}",
                    "sql_query": None,
                    "query_results": None,
                    "result_count": 0,
                    "execution_error": str(fallback_error),
                }), 500
        else:
            return jsonify({
                "response": f"Error processing your query: {str(e)}",
                "sql_query": None,
                "query_results": None,
                "result_count": 0,
                "execution_error": str(e),
            }), 500