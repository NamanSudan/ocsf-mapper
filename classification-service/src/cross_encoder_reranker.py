from typing import List, Dict, Any
import logging
from sentence_transformers import CrossEncoder
import torch

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    """
    Implements cross-encoder based reranking for classification results
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CrossEncoder(model_name, device=self.device)
        logger.info(f"Initialized CrossEncoder with model {model_name} on {self.device}")

    async def rerank(self, query: str, candidates: List[Dict[str, Any]], 
                    top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Rerank candidate classifications using cross-encoder
        """
        try:
            # Prepare pairs for cross-encoder
            pairs = [(query, cand.get("content", "")) for cand in candidates]
            
            # Get scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Combine scores with candidates
            scored_candidates = []
            for score, candidate in zip(scores, candidates):
                scored_candidates.append({
                    **candidate,
                    "cross_encoder_score": float(score)
                })
            
            # Sort by cross-encoder score and return top_k
            reranked = sorted(
                scored_candidates, 
                key=lambda x: x["cross_encoder_score"], 
                reverse=True
            )[:top_k]
            
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking error: {str(e)}")
            return candidates[:top_k]  # Return original order if reranking fails 