"""
Hybrid Routing - FYP Experiment 1
Combines keyword matching (fast path) with semantic similarity (fallback)

Method:
1. Try keyword matching first
2. If high confidence (2+ keyword matches) → route immediately
3. If low confidence (<2 matches) → fallback to semantic similarity
4. Combines speed of keyword with intelligence of semantic

Expected Performance:
- Routing accuracy: 80-92% (best of both worlds)
- Latency overhead: ~10ms average (fast for clear, smart for ambiguous)
- Memory: +100MB for semantic embedder

Decision Criteria:
- High confidence: ≥2 keyword matches (keyword wins)
- Low confidence: <2 keyword matches (semantic fallback)

This should be the WINNER - balances accuracy, speed, and cost.
"""

from typing import Optional, List, Set
import re
import numpy as np
from sentence_transformers import SentenceTransformer
import torch


class HybridRouter:
    """Hybrid routing: keyword fast path + semantic fallback"""
    
    # Keyword patterns (from original detect_intent)
    HR_KEYWORDS = [
        'employee', 'employees', 'staff', 'workforce', 'headcount',
        'hr', 'human resource', 'payroll', 'salary', 'salaries',
        'manager', 'managers', 'supervisor', 'supervisors',
        'tenure', 'age', 'department', 'kitchen', 'role'
    ]
    
    SALES_KEYWORDS = [
        'sales', 'sale', 'revenue', 'revenues', 'profit', 'profits',
        'product', 'products', 'branch', 'branches', 'store', 'stores',
        'quantity', 'quantities', 'sold', 'price', 'prices', 'pricing',
        'highest', 'lowest', 'best', 'worst', 'top', 'bottom',
        'most', 'least', 'performance', 'ranking'
    ]
    
    DOC_KEYWORDS = [
        'mission', 'vision', 'value', 'values', 'culture',
        'ceo', 'leadership', 'management team', 'organization',
        'history', 'background', 'about', 'strategy', 'strategic',
        'goal', 'goals', 'objective', 'objectives'
    ]
    
    # Semantic domain examples (from routing_semantic.py)
    DOMAIN_EXAMPLES = {
        'hr_kpi': [
            "How many employees work in the kitchen?",
            "What is the average tenure of our staff?",
            "Show me the total monthly payroll",
            "Which branch has the most managers?",
            "What's the age distribution of our workforce?"
        ],
        'sales_kpi': [
            "What are the total sales for this month?",
            "Which product generates the most revenue?",
            "Show me sales by branch",
            "What's the highest selling product?",
            "Compare sales between branches"
        ],
        'rag_docs': [
            "What is the company's mission?",
            "Tell me about the leadership team",
            "What are the company values?",
            "Explain the organizational structure",
            "What's the company history?"
        ]
    }
    
    KEYWORD_CONFIDENCE_THRESHOLD = 2  # Need 2+ keywords for high confidence
    SEMANTIC_SIMILARITY_THRESHOLD = 0.5
    
    def __init__(self):
        """Initialize hybrid router with keyword patterns and semantic embedder"""
        print("🔄 Initializing HybridRouter...")
        
        # Initialize semantic embedder (for fallback)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        
        # Pre-compute domain embeddings for semantic fallback
        self.domain_embeddings = {}
        for domain, examples in self.DOMAIN_EXAMPLES.items():
            embeddings = self.embedder.encode(examples, convert_to_numpy=True)
            centroid = np.mean(embeddings, axis=0)
            centroid = centroid / np.linalg.norm(centroid)
            self.domain_embeddings[domain] = centroid
        
        print(f"✅ HybridRouter ready (keyword + semantic)")
    
    def keyword_match(self, text: str, word: str) -> bool:
        """
        Check if word appears in text with word boundaries
        (From original oneclick_my_retailchain_v8.2)
        """
        text_lower = text.lower()
        word_lower = word.lower()
        
        # For single words: use word boundary
        if ' ' not in word_lower:
            pattern = r'\b' + re.escape(word_lower) + r'\b'
            return bool(re.search(pattern, text_lower))
        else:
            # For phrases: substring match
            return word_lower in text_lower
    
    def keyword_routing(self, text: str) -> tuple:
        """
        Try keyword-based routing first
        
        Returns:
            (intent, confidence_score, matched_keywords)
        """
        text_lower = text.lower()
        
        # Count keyword matches per domain
        hr_matches = set()
        sales_matches = set()
        doc_matches = set()
        
        for kw in self.HR_KEYWORDS:
            if self.keyword_match(text, kw):
                hr_matches.add(kw)
        
        for kw in self.SALES_KEYWORDS:
            if self.keyword_match(text, kw):
                sales_matches.add(kw)
        
        for kw in self.DOC_KEYWORDS:
            if self.keyword_match(text, kw):
                doc_matches.add(kw)
        
        # Priority-based routing (from original detect_intent)
        # Priority 1: HR KPIs
        if len(hr_matches) >= 1:
            return ('hr_kpi', len(hr_matches), hr_matches)
        
        # Priority 2: Sales KPIs
        if len(sales_matches) >= 1:
            return ('sales_kpi', len(sales_matches), sales_matches)
        
        # Priority 3: Doc queries
        if len(doc_matches) >= 1:
            return ('rag_docs', len(doc_matches), doc_matches)
        
        # No matches
        return (None, 0, set())
    
    def semantic_routing(self, text: str) -> tuple:
        """
        Semantic similarity fallback
        
        Returns:
            (intent, similarity_score)
        """
        # Embed query
        query_embedding = self.embedder.encode(text, convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Calculate similarities
        similarities = {}
        for domain, domain_emb in self.domain_embeddings.items():
            similarity = np.dot(query_embedding, domain_emb)
            similarities[domain] = similarity
        
        best_domain = max(similarities, key=similarities.get)
        best_score = similarities[best_domain]
        
        return (best_domain, best_score)
    
    def detect_intent(self, text: str, has_image: bool, conversation_history: Optional[List] = None) -> str:
        """
        Hybrid routing: keyword first, semantic fallback
        
        Args:
            text: User query
            has_image: Whether image uploaded
            conversation_history: Previous exchanges
        
        Returns:
            Intent: 'visual', 'hr_kpi', 'sales_kpi', or 'rag_docs'
        """
        # Priority 1: Image queries
        if has_image:
            return 'visual'
        
        # Priority 2: Empty or very short queries
        if not text or len(text.strip()) < 3:
            return 'rag_docs'
        
        # Try keyword routing first
        kw_intent, kw_confidence, kw_matches = self.keyword_routing(text)
        
        # High confidence: use keyword result
        if kw_confidence >= self.KEYWORD_CONFIDENCE_THRESHOLD:
            return kw_intent
        
        # Low confidence: fallback to semantic
        sem_intent, sem_score = self.semantic_routing(text)
        
        # If semantic also low confidence, prefer keyword if any
        if sem_score < self.SEMANTIC_SIMILARITY_THRESHOLD:
            if kw_intent:
                return kw_intent
            else:
                return 'rag_docs'
        
        # Use semantic result
        return sem_intent
    
    def get_routing_details(self, text: str) -> dict:
        """
        Get detailed routing information (for debugging)
        
        Returns:
            Dict with keyword and semantic results
        """
        kw_intent, kw_confidence, kw_matches = self.keyword_routing(text)
        sem_intent, sem_score = self.semantic_routing(text)
        
        return {
            'keyword': {
                'intent': kw_intent,
                'confidence': kw_confidence,
                'matches': list(kw_matches)
            },
            'semantic': {
                'intent': sem_intent,
                'score': float(sem_score)
            },
            'final_intent': self.detect_intent(text, has_image=False),
            'method_used': 'keyword' if kw_confidence >= self.KEYWORD_CONFIDENCE_THRESHOLD else 'semantic'
        }


if __name__ == "__main__":
    # Test hybrid router
    print("Testing HybridRouter...\n")
    
    router = HybridRouter()
    
    test_queries = [
        ("How many employees work in the kitchen?", "hr_kpi"),
        ("What are the total sales last month?", "sales_kpi"),
        ("Tell me about the company mission", "rag_docs"),
        ("Show me the average employee age", "hr_kpi"),
        ("Which product sells the most?", "sales_kpi"),
        ("What is the leadership structure?", "rag_docs"),
        ("How many staff members?", "hr_kpi"),  # Ambiguous - tests fallback
        ("What about revenue performance?", "sales_kpi"),  # Ambiguous
    ]
    
    correct = 0
    for query, expected in test_queries:
        intent = router.detect_intent(query, has_image=False)
        details = router.get_routing_details(query)
        
        status = "✅" if intent == expected else "❌"
        print(f"{status} Query: {query}")
        print(f"   Predicted: {intent}, Expected: {expected}")
        print(f"   Method: {details['method_used']}")
        print(f"   Keyword: {details['keyword']}")
        print(f"   Semantic: {details['semantic']}")
        print()
        
        if intent == expected:
            correct += 1
    
    accuracy = (correct / len(test_queries)) * 100
    print(f"Test Accuracy: {accuracy:.1f}% ({correct}/{len(test_queries)})")
    print("\n✅ Hybrid routing combines best of keyword (speed) + semantic (accuracy)")
