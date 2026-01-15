"""
Router Factory - FYP Experiment 1: Routing Methods Comparison
Provides pluggable routing architecture for testing different methods

Methods Available:
- keyword: Current word-boundary keyword matching (baseline)
- semantic: Embedding-based similarity routing
- llm: LLM classification routing (slow but accurate)
- hybrid: Keyword fast path + semantic fallback

Usage:
    router = RouterFactory.get_router('semantic')
    intent = router.detect_intent(query, has_image, conversation_history)
"""

from typing import Optional, List, Tuple
import sys
from pathlib import Path

# Import available routers
try:
    from routing_semantic import SemanticRouter
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    print("⚠️ SemanticRouter not available")

try:
    from routing_llm import LLMRouter
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️ LLMRouter not available")

try:
    from routing_hybrid import HybridRouter
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False
    print("⚠️ HybridRouter not available")


class RouterFactory:
    """Factory for creating different routing implementations"""
    
    _routers = {}
    _current_router = 'keyword'
    
    @classmethod
    def get_router(cls, method: str = 'keyword'):
        """
        Get router instance by method name
        
        Args:
            method: 'keyword', 'semantic', 'llm', or 'hybrid'
        
        Returns:
            Router instance with detect_intent() method
        """
        if method in cls._routers:
            return cls._routers[method]
        
        if method == 'keyword':
            # Return None - caller will use original detect_intent from bot
            return None
        
        elif method == 'semantic':
            if not SEMANTIC_AVAILABLE:
                raise ValueError("SemanticRouter not available - ensure routing_semantic.py exists")
            router = SemanticRouter()
            cls._routers[method] = router
            return router
        
        elif method == 'llm':
            if not LLM_AVAILABLE:
                raise ValueError("LLMRouter not available - ensure routing_llm.py exists")
            router = LLMRouter()
            cls._routers[method] = router
            return router
        
        elif method == 'hybrid':
            if not HYBRID_AVAILABLE:
                raise ValueError("HybridRouter not available - ensure routing_hybrid.py exists")
            router = HybridRouter()
            cls._routers[method] = router
            return router
        
        else:
            raise ValueError(f"Unknown routing method: {method}. Choose from: keyword, semantic, llm, hybrid")
    
    @classmethod
    def set_current_router(cls, method: str):
        """Set the current router method globally"""
        cls._current_router = method
    
    @classmethod
    def get_current_router(cls):
        """Get the current router method name"""
        return cls._current_router


class BaseRouter:
    """Base class for all routers"""
    
    def detect_intent(self, text: str, has_image: bool, conversation_history: Optional[List] = None) -> str:
        """
        Detect user intent from query
        
        Args:
            text: User query text
            has_image: Whether image is uploaded
            conversation_history: Previous conversation exchanges
        
        Returns:
            Intent string: 'visual', 'hr_kpi', 'sales_kpi', or 'rag_docs'
        """
        raise NotImplementedError("Subclass must implement detect_intent()")


if __name__ == "__main__":
    # Test factory
    print("Testing RouterFactory...")
    
    # Test keyword (returns None - use original function)
    router = RouterFactory.get_router('keyword')
    print(f"✅ Keyword router: {router}")
    
    # Test semantic
    if SEMANTIC_AVAILABLE:
        router = RouterFactory.get_router('semantic')
        print(f"✅ Semantic router: {router}")
    
    # Test LLM
    if LLM_AVAILABLE:
        router = RouterFactory.get_router('llm')
        print(f"✅ LLM router: {router}")
    
    # Test hybrid
    if HYBRID_AVAILABLE:
        router = RouterFactory.get_router('hybrid')
        print(f"✅ Hybrid router: {router}")
    
    print("\n✅ RouterFactory test complete")
