from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryInput(BaseModel):
    text: str
    profession: Optional[str] = "researcher"
    lat: Optional[float] = None
    lon: Optional[float] = None

class QueryResponse(BaseModel):
    response: str
    sql_query: Optional[str] = None
    query_results: Optional[List[Dict[str, Any]]] = None
    result_count: Optional[int] = None
    execution_error: Optional[str] = None