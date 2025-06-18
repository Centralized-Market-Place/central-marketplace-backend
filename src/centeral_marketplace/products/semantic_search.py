import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import datetime

logger = logging.getLogger(__name__)

class SemanticSearchService:
    _instance = None
    _model = None
    _initialized = False
    _model_loaded = False
    
    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if self._initialized:
            return
            
        self.model_name = model_name
        self._initialized = True

    def initialize_model(self):
        if self._model_loaded:
            logger.info("Semantic search model already loaded")
            return
            
        try:
            logger.info(f"Loading semantic search model during startup: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self._model_loaded = True
            logger.info(f"Successfully loaded semantic search model: {self.model_name}")
        except ImportError as e:
            logger.error(f"Missing dependencies for semantic search model: {e}")
            self._model = None
            self._model_loaded = False
        except Exception as e:
            logger.error(f"Failed to load semantic search model '{self.model_name}': {e}")
            logger.error(f"Model loading error type: {type(e).__name__}")
            self._model = None
            self._model_loaded = False

    @property
    def model(self):
        return self._model

    @property
    def is_available(self) -> bool:
        return self._model is not None and self._model_loaded

    @property
    def is_model_loaded(self) -> bool:
        return self._model_loaded

    def encode_query(self, query: str) -> Optional[List[float]]:
        if not self._model:
            if not self._model_loaded:
                logger.warning("Semantic search model has not been initialized yet")
            else:
                logger.warning("Semantic search model is not available")
            return None
            
        if not query or not query.strip():
            return None
        
        try:
            return self._model.encode(query).tolist()
        except Exception as e:
            logger.error(f"Failed to encode query '{query}': {e}")
            return None

    def create_semantic_search_stage(self, query_vector: List[float], k: int = 100) -> dict:
        return {
            "$search": {
                "index": "default",
                "knnBeta": {
                    "vector": query_vector,
                    "path": "embedding",
                    "k": k
                }
            }
        }

    def create_score_projection_stage(self) -> dict:
        return {
            "$addFields": {
                "search_score": {"$meta": "searchScore"}
            }
        }

    def calculate_relevance_score(self, doc: dict) -> float:
        base_score = doc.get("search_score", 0)
        
        recency_score = self._calculate_recency_boost(doc.get("created_at"))
        
        engagement_score = self._calculate_engagement_boost(
            doc.get("forwards", 0),
            doc.get("views", 0), 
            doc.get("reactions", [])
        )
        
        return base_score + recency_score + engagement_score

    def _calculate_recency_boost(self, created_at) -> float:
        if not created_at:
            return 0
        
        try:
            if isinstance(created_at, str):
                try:
                    date = datetime.datetime.fromisoformat(created_at)
                except ValueError:
                    from dateutil import parser
                    date = parser.parse(created_at)
            else:
                date = created_at
                
            if date.tzinfo is None:
                date = date.replace(tzinfo=datetime.timezone.utc)
            
            days_old = (datetime.datetime.now(datetime.timezone.utc) - date).days
            return 1.0 if days_old < 7 else 0.5
        except Exception as e:
            logger.warning(f"Error calculating recency boost: {e}")
            return 0

    def _calculate_engagement_boost(self, forwards: int, views: int, reactions: list) -> float:
        try:
            reaction_count = sum(count for _, count in reactions) if reactions else 0
            return (forwards * 0.2 + views * 0.1 + reaction_count * 0.1)
        except Exception as e:
            logger.warning(f"Error calculating engagement boost: {e}")
            return 0


def get_semantic_search_service(model_name: str = "all-MiniLM-L6-v2") -> SemanticSearchService:
    return SemanticSearchService(model_name=model_name)

def initialize_semantic_search_model():
    service = get_semantic_search_service()
    service.initialize_model()
    return service 