"""
Enhanced Query Router with Fuzzy Matching and Ambiguity Handling
"""
from typing import Optional, Dict, Tuple
from .validator import DataValidator

class QueryRouter:
    """Routes queries to appropriate handlers with typo tolerance."""
    
    # Keyword definitions
    SALES_KEYWORDS = [
        "sales", "revenue", "product", "branch", "state", "customer",
        "payment", "channel", "quantity", "price", "total", "sale",
        "jualan", "hasil", "produk", "cawangan", "negeri"
    ]
    
    HR_KEYWORDS = [
        "staff", "employee", "headcount", "attrition", "turnover",
        "overtime", "salary", "income", "department", "jobrole",
        "age", "agegroup", "hire", "resign", "pekerja", "kakitangan",
        "jabatan", "gaji", "pendapatan", "umur"
    ]
    
    POLICY_KEYWORDS = [
        "policy", "leave", "claim", "allowance", "benefit", "sop",
        "procedure", "process", "guideline", "rule", "regulation",
        "dasar", "cuti", "tuntutan", "elaun", "faedah", "prosedur"
    ]
    
    @staticmethod
    def route(query: str, has_image: bool = False) -> Tuple[str, str, Dict]:
        """
        Route query to appropriate handler.
        
        Args:
            query: User query (raw or normalized)
            has_image: Whether image was uploaded
        
        Returns:
            tuple: (route, normalized_query, metadata)
                route: 'sales_kpi', 'hr_kpi', 'rag_docs', or 'visual'
                normalized_query: Cleaned query string
                metadata: Additional routing information
        """
        # Normalize query first
        normalized = DataValidator.normalize_query(query)
        query_lower = normalized.lower()
        
        metadata = {
            "original_query": query,
            "normalized_query": normalized,
            "has_image": has_image,
            "confidence": 0.0,
            "reason": ""
        }
        
        # Priority 1: Visual route if image uploaded
        if has_image:
            metadata["confidence"] = 1.0
            metadata["reason"] = "Image uploaded"
            return "visual", normalized, metadata
        
        # Check for ambiguous single-word queries
        words = query_lower.split()
        if len(words) <= 2 and any(w in ["staff", "employee", "headcount", "sales", "revenue"] for w in words):
            # These need clarification but route to most likely handler
            if DataValidator.contains_fuzzy_keyword(query_lower, QueryRouter.HR_KEYWORDS):
                metadata["confidence"] = 0.6
                metadata["reason"] = "Ambiguous HR query - needs clarification"
                return "hr_kpi", normalized, metadata
            elif DataValidator.contains_fuzzy_keyword(query_lower, QueryRouter.SALES_KEYWORDS):
                metadata["confidence"] = 0.6
                metadata["reason"] = "Ambiguous sales query - needs clarification"
                return "sales_kpi", normalized, metadata
        
        # Priority 2: HR KPI route (with fuzzy matching)
        if DataValidator.contains_fuzzy_keyword(query_lower, QueryRouter.HR_KEYWORDS, threshold=0.7):
            metadata["confidence"] = 0.95
            metadata["reason"] = "HR keywords detected (fuzzy match)"
            return "hr_kpi", normalized, metadata
        
        # Priority 3: Sales KPI route (with fuzzy matching)
        if DataValidator.contains_fuzzy_keyword(query_lower, QueryRouter.SALES_KEYWORDS, threshold=0.7):
            metadata["confidence"] = 0.95
            metadata["reason"] = "Sales keywords detected (fuzzy match)"
            return "sales_kpi", normalized, metadata
        
        # Priority 4: Policy/SOP route
        if DataValidator.contains_fuzzy_keyword(query_lower, QueryRouter.POLICY_KEYWORDS, threshold=0.75):
            metadata["confidence"] = 0.9
            metadata["reason"] = "Policy keywords detected"
            return "rag_docs", normalized, metadata
        
        # Default: RAG docs (catch-all)
        metadata["confidence"] = 0.5
        metadata["reason"] = "Default route - no specific keywords matched"
        return "rag_docs", normalized, metadata
    
    @staticmethod
    def get_clarification_prompt(query: str, route: str, confidence: float) -> Optional[str]:
        """
        Generate clarification prompt for ambiguous queries.
        
        Args:
            query: User query
            route: Detected route
            confidence: Routing confidence score
        
        Returns:
            str: Clarification prompt if needed, None otherwise
        """
        if confidence > 0.7:
            return None  # High confidence, no clarification needed
        
        words = query.lower().split()
        if len(words) > 2:
            return None  # Multi-word query, likely clear enough
        
        # Generate clarification for ambiguous queries
        if route == "hr_kpi":
            return f"""## 🤔 Clarification Needed

Your query "**{query}**" is a bit vague. Here are some specific questions I can answer:

**HR Analytics:**
- Total headcount across all branches?
- Headcount by department or state?
- Employee attrition rate?
- Average salary by department?

**Suggested queries:**
- "total headcount"
- "headcount by department"
- "headcount by state"
- "attrition rate by age group"
- "average salary by department"

Please provide more details for a specific answer.
"""
        
        elif route == "sales_kpi":
            return f"""## 🤔 Clarification Needed

Your query "**{query}**" is a bit vague. Here are some specific questions I can answer:

**Sales Analytics:**
- Total sales for a specific month?
- Sales by state or branch?
- Top selling products?
- Sales comparison between months?

**Suggested queries:**
- "total sales for June 2024"
- "sales by state for June 2024"
- "top 5 products in June 2024"
- "compare sales June vs May 2024"

Please provide more details for a specific answer.
"""
        
        return None
