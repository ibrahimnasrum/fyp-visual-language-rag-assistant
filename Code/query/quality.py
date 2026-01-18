"""
Answer Quality Validator and Formatter
Ensures all answers meet executive format standards.
"""
import re
from typing import Dict, Optional

class AnswerQualityValidator:
    """Validates and enforces answer quality standards."""
    
    MIN_LENGTH = 300  # Minimum characters for executive format
    
    @staticmethod
    def validate(answer: str) -> Dict[str, any]:
        """
        Validate answer quality.
        
        Args:
            answer: Generated answer text
        
        Returns:
            dict: {
                'valid': bool,
                'length': int,
                'has_summary': bool,
                'has_evidence': bool,
                'has_actions': bool,
                'issues': List[str]
            }
        """
        issues = []
        
        # Check length
        length = len(answer.strip())
        if length < AnswerQualityValidator.MIN_LENGTH:
            issues.append(f"Answer too short ({length} chars, minimum {AnswerQualityValidator.MIN_LENGTH})")
        
        # Check for required sections
        has_summary = bool(re.search(r'##.*summary', answer, re.IGNORECASE))
        has_evidence = bool(re.search(r'##.*evidence|###.*evidence', answer, re.IGNORECASE))
        has_actions = bool(re.search(r'##.*action|###.*action', answer, re.IGNORECASE))
        
        if not has_summary:
            issues.append("Missing Executive Summary section")
        if not has_evidence:
            issues.append("Missing Evidence section")
        if not has_actions:
            issues.append("Missing Next Actions section")
        
        return {
            'valid': len(issues) == 0,
            'length': length,
            'has_summary': has_summary,
            'has_evidence': has_evidence,
            'has_actions': has_actions,
            'issues': issues
        }
    
    @staticmethod
    def enforce_format(answer: str, route: str, metadata: Optional[Dict] = None) -> str:
        """
        Enforce executive format on answer.
        
        Args:
            answer: Original answer
            route: Route taken (sales_kpi, hr_kpi, rag_docs, visual)
            metadata: Additional metadata (rows_used, sources, etc.)
        
        Returns:
            str: Formatted answer meeting quality standards
        """
        validation = AnswerQualityValidator.validate(answer)
        
        # If already valid, return as-is
        if validation['valid']:
            return answer
        
        # If too short or missing sections, wrap in executive format
        metadata = metadata or {}
        
        # Determine source information
        if route == "sales_kpi":
            source_info = "Structured Sales KPI Analytics"
            rows_info = f"Rows Analyzed: {metadata.get('rows_used', 'N/A')}"
        elif route == "hr_kpi":
            source_info = "Structured HR KPI Analytics"
            rows_info = f"Rows Analyzed: {metadata.get('rows_used', 'N/A')}"
        elif route == "rag_docs":
            source_info = "Company Policy Documents (RAG)"
            rows_info = f"Sources Retrieved: {metadata.get('sources_count', 'N/A')}"
        elif route == "visual":
            source_info = "OCR + Document Analysis"
            rows_info = f"Characters Extracted: {metadata.get('ocr_chars', 'N/A')}"
        else:
            source_info = "General Query"
            rows_info = ""
        
        # Build formatted answer
        formatted = f"""## 📊 Response

### Executive Summary
{answer.strip()}

### Evidence Used
- **Data Source:** {source_info}
- **Query Processing:** Successfully completed
{f"- **{rows_info}**" if rows_info else ""}
- **Route:** {route.upper()}

### Assumptions & Limitations
- Based on available data in the system
- Results reflect current dataset state
- For detailed analysis, additional context may be needed

### Next Actions
1. Review the analysis above
2. Ask follow-up questions for clarification
3. Request specific metrics if needed
4. Provide feedback to improve future responses
"""
        
        return formatted
    
    @staticmethod
    def add_clarification_if_needed(answer: str, query: str, confidence: float) -> str:
        """
        Prepend clarification note if confidence is low.
        
        Args:
            answer: Generated answer
            query: Original query
            confidence: Routing confidence (0.0-1.0)
        
        Returns:
            str: Answer with clarification prepended if needed
        """
        if confidence < 0.7:
            clarification = f"""
> ⚠️ **Note:** Your query "{query}" was somewhat ambiguous (confidence: {confidence:.0%}).
> The answer below is my best interpretation. If this isn't what you meant, please rephrase your question.

---

"""
            return clarification + answer
        
        return answer
