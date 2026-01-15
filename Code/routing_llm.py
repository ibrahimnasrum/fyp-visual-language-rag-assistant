"""
LLM Routing - FYP Experiment 1
Uses Ollama LLM for intent classification

Method:
1. Send query + classification prompt to LLM
2. Parse LLM response (hr_kpi, sales_kpi, or rag_docs)
3. Return classified intent

Expected Performance:
- Routing accuracy: 80-95% (highest accuracy)
- Latency overhead: ~3000ms per query (SLOW - not practical)
- Memory: Uses Ollama mistral:latest already loaded

Trade-off Analysis:
- Pros: Highest accuracy, handles nuanced queries, natural language understanding
- Cons: 150x slower than keyword, 100x slower than semantic, cost if using API
- Conclusion: Good for research comparison, not for production
"""

from typing import Optional, List
import requests
import json
import re


class LLMRouter:
    """LLM-based routing using Ollama mistral for classification"""
    
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "mistral:latest"
    
    CLASSIFICATION_PROMPT = """You are a query classifier for a retail company chatbot.

Classify the following user query into exactly ONE category:
- hr_kpi: Questions about employees, staff, HR, workforce, headcount, payroll, managers, tenure, age
- sales_kpi: Questions about sales, revenue, products, branches, performance, quantity, pricing
- rag_docs: Questions about company information, mission, values, leadership, structure, history

USER QUERY: {query}

IMPORTANT: Respond with ONLY ONE WORD - either "hr_kpi", "sales_kpi", or "rag_docs". No explanation.

CATEGORY:"""
    
    def __init__(self):
        """Initialize LLM router"""
        print("🔄 Initializing LLMRouter...")
        
        # Test Ollama connection
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print("✅ LLMRouter ready (Ollama connected)")
            else:
                print("⚠️ LLMRouter: Ollama connection issue")
        except Exception as e:
            print(f"⚠️ LLMRouter: Ollama not accessible ({e})")
    
    def detect_intent(self, text: str, has_image: bool, conversation_history: Optional[List] = None) -> str:
        """
        Detect intent using LLM classification
        
        Args:
            text: User query
            has_image: Whether image uploaded (takes priority)
            conversation_history: Previous exchanges (unused for now)
        
        Returns:
            Intent: 'visual', 'hr_kpi', 'sales_kpi', or 'rag_docs'
        """
        # Priority 1: Image queries
        if has_image:
            return 'visual'
        
        # Priority 2: Empty or very short queries
        if not text or len(text.strip()) < 3:
            return 'rag_docs'
        
        # Build classification prompt
        prompt = self.CLASSIFICATION_PROMPT.format(query=text)
        
        try:
            # Call Ollama API
            payload = {
                "model": self.MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0,  # Deterministic
                "max_tokens": 10   # Just need one word
            }
            
            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"⚠️ LLM routing failed: HTTP {response.status_code}")
                return 'rag_docs'
            
            result = response.json()
            llm_response = result.get('response', '').strip().lower()
            
            # Parse LLM response
            if 'hr_kpi' in llm_response or 'hr' in llm_response:
                return 'hr_kpi'
            elif 'sales_kpi' in llm_response or 'sales' in llm_response:
                return 'sales_kpi'
            elif 'rag_docs' in llm_response or 'rag' in llm_response:
                return 'rag_docs'
            else:
                # Fallback: try to extract any valid category
                if any(word in llm_response for word in ['employee', 'staff', 'hr', 'payroll', 'manager']):
                    return 'hr_kpi'
                elif any(word in llm_response for word in ['sales', 'revenue', 'product', 'branch']):
                    return 'sales_kpi'
                else:
                    return 'rag_docs'
        
        except requests.Timeout:
            print("⚠️ LLM routing timeout (30s)")
            return 'rag_docs'
        
        except Exception as e:
            print(f"⚠️ LLM routing error: {e}")
            return 'rag_docs'
    
    def get_routing_explanation(self, text: str) -> dict:
        """
        Get LLM's reasoning for classification (for debugging)
        
        Args:
            text: User query
        
        Returns:
            Dict with 'category' and 'explanation'
        """
        explain_prompt = f"""Classify this query and explain your reasoning in 1 sentence:

Query: {text}

Categories: hr_kpi (employees/staff), sales_kpi (sales/products), rag_docs (company info)

Format: CATEGORY: <category>
REASON: <one sentence>"""
        
        try:
            payload = {
                "model": self.MODEL,
                "prompt": explain_prompt,
                "stream": False,
                "temperature": 0,
                "max_tokens": 50
            }
            
            response = requests.post(self.OLLAMA_URL, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '')
                
                # Parse response
                category_match = re.search(r'CATEGORY:\s*(\w+)', llm_response, re.IGNORECASE)
                reason_match = re.search(r'REASON:\s*(.+)', llm_response, re.IGNORECASE)
                
                return {
                    'category': category_match.group(1) if category_match else 'unknown',
                    'explanation': reason_match.group(1).strip() if reason_match else llm_response[:100]
                }
        
        except Exception as e:
            return {'category': 'error', 'explanation': str(e)}


if __name__ == "__main__":
    # Test LLM router
    print("Testing LLMRouter...\n")
    
    router = LLMRouter()
    
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
        print(f"Query: {query}")
        intent = router.detect_intent(query, has_image=False)
        explanation = router.get_routing_explanation(query)
        
        status = "✅" if intent == expected else "❌"
        print(f"{status} Predicted: {intent}, Expected: {expected}")
        print(f"   Explanation: {explanation}")
        print()
        
        if intent == expected:
            correct += 1
    
    accuracy = (correct / len(test_queries)) * 100
    print(f"Test Accuracy: {accuracy:.1f}% ({correct}/{len(test_queries)})")
    print("⚠️ Note: LLM routing is SLOW (~3s per query) - for research only")
