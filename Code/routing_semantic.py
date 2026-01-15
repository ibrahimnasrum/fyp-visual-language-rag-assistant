"""
Semantic Routing - FYP Experiment 1
Uses sentence embeddings + cosine similarity for intent classification

Method:
1. Pre-compute embeddings for domain examples (HR KPI, Sales KPI, RAG docs)
2. Embed user query
3. Calculate cosine similarity to each domain
4. Route to highest similarity domain (if above threshold)

Expected Performance:
- Routing accuracy: 75-90%
- Latency overhead: ~20ms per query
- Memory: +100MB for embedder
"""

from typing import Optional, List
import numpy as np
from sentence_transformers import SentenceTransformer
import torch


class SemanticRouter:
    """Semantic similarity-based routing using sentence embeddings"""
    
    # Domain example queries for embedding
    DOMAIN_EXAMPLES = {
        'hr_kpi': [
            "How many employees work in the kitchen?",
            "What is the average tenure of our staff?",
            "Show me the total monthly payroll",
            "Which branch has the most managers?",
            "What's the age distribution of our workforce?",
            "How many employees have been here for 5 years?",
            "List all supervisors in the company",
            "What's the employee count by department?"
        ],
        'sales_kpi': [
            "What are the total sales for this month?",
            "Which product generates the most revenue?",
            "Show me sales by branch",
            "What's the highest selling product?",
            "Compare sales between branches",
            "What's the total quantity sold?",
            "Which branch has the lowest revenue?",
            "Show me product performance rankings"
        ],
        'rag_docs': [
            "What is the company's mission?",
            "Tell me about the leadership team",
            "What are the company values?",
            "Explain the organizational structure",
            "What's the company history?",
            "Describe the strategic goals",
            "What are the core competencies?",
            "Tell me about recent achievements"
        ]
    }
    
    SIMILARITY_THRESHOLD = 0.5  # Minimum confidence to route
    
    def __init__(self):
        """Initialize semantic router with embedder and domain embeddings"""
        print("🔄 Initializing SemanticRouter...")
        
        # Use same embedder as RAG for consistency
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        
        # Pre-compute domain embeddings (average of example embeddings)
        self.domain_embeddings = {}
        for domain, examples in self.DOMAIN_EXAMPLES.items():
            embeddings = self.embedder.encode(examples, convert_to_numpy=True)
            # Use centroid (average) as domain representation
            centroid = np.mean(embeddings, axis=0)
            # Normalize for cosine similarity
            centroid = centroid / np.linalg.norm(centroid)
            self.domain_embeddings[domain] = centroid
        
        print(f"✅ SemanticRouter ready ({len(self.domain_embeddings)} domains)")
    
    def detect_intent(self, text: str, has_image: bool, conversation_history: Optional[List] = None) -> str:
        """
        Detect intent using semantic similarity
        
        Args:
            text: User query
            has_image: Whether image uploaded (takes priority)
            conversation_history: Previous exchanges (for context)
        
        Returns:
            Intent: 'visual', 'hr_kpi', 'sales_kpi', or 'rag_docs'
        """
        # Priority 1: Image queries
        if has_image:
            return 'visual'
        
        # Priority 2: Empty or very short queries
        if not text or len(text.strip()) < 3:
            return 'rag_docs'
        
        # Embed query
        query_embedding = self.embedder.encode(text, convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Calculate cosine similarity to each domain
        similarities = {}
        for domain, domain_emb in self.domain_embeddings.items():
            similarity = np.dot(query_embedding, domain_emb)
            similarities[domain] = similarity
        
        # Get highest similarity
        best_domain = max(similarities, key=similarities.get)
        best_score = similarities[best_domain]
        
        # If below threshold, default to RAG
        if best_score < self.SIMILARITY_THRESHOLD:
            return 'rag_docs'
        
        return best_domain
    
    def get_routing_scores(self, text: str) -> dict:
        """
        Get similarity scores for all domains (for debugging)
        
        Args:
            text: User query
        
        Returns:
            Dict mapping domain -> similarity score
        """
        query_embedding = self.embedder.encode(text, convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        similarities = {}
        for domain, domain_emb in self.domain_embeddings.items():
            similarity = np.dot(query_embedding, domain_emb)
            similarities[domain] = float(similarity)
        
        return similarities


if __name__ == "__main__":
    # Test semantic router
    print("Testing SemanticRouter...\n")
    
    router = SemanticRouter()
    
    test_queries = [
        ("How many employees work in the kitchen?", "hr_kpi"),
        ("What are the total sales last month?", "sales_kpi"),
        ("Tell me about the company mission", "rag_docs"),
        ("Show me the average employee age", "hr_kpi"),
        ("Which product sells the most?", "sales_kpi"),
        ("What is the leadership structure?", "rag_docs"),
    ]
    
    correct = 0
    for query, expected in test_queries:
        intent = router.detect_intent(query, has_image=False)
        scores = router.get_routing_scores(query)
        
        status = "✅" if intent == expected else "❌"
        print(f"{status} Query: {query}")
        print(f"   Predicted: {intent}, Expected: {expected}")
        print(f"   Scores: {scores}")
        print()
        
        if intent == expected:
            correct += 1
    
    accuracy = (correct / len(test_queries)) * 100
    print(f"Test Accuracy: {accuracy:.1f}% ({correct}/{len(test_queries)})")
