"""
Time Sensitivity Classifier - FYP Version
Determines if a query requires timeframe information.
Simplified for academic research (50 lines).
"""
import re
from typing import Dict, List, Optional

class TimeClassifier:
    """Classifies queries by time sensitivity."""
    
    # Keywords indicating time-sensitive queries
    TIME_SENSITIVE_KEYWORDS = [
        'revenue', 'profit', 'total', 'sum', 'amount',
        'sold', 'transactions', 'orders', 'performance',
        'top', 'best', 'worst', 'compare', 'trend'
    ]
    
    # Static/metadata queries that don't need timeframes
    STATIC_KEYWORDS = [
        'how many', 'how much', 'count', 'number of',
        'list', 'show', 'what are', 'which', 'available',
        'branch', 'state', 'product', 'channel', 'payment'
    ]
    
    # Metadata counting patterns (never need time period)
    METADATA_PATTERNS = [
        r'how many (products?|states?|branches?|channels?|categories?|employees?|staff)',
        r'how much (employees?|staff)',
        r'count (of )?(products?|states?|branches?|employees?|staff)',
        r'number of (products?|states?|branches?|employees?|staff)',
        r'(products?|states?|branches?|employees?) (in|available)',
        r'total (employees?|staff|headcount)',
    ]
    
    # Month patterns
    MONTH_PATTERNS = [
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
        r'\b\d{4}[-/]\d{1,2}\b',  # 2024-01 or 2024/1
        r'\b(H1|H2)\b',  # Half-year
        r'\b(Q1|Q2|Q3|Q4)\b'  # Quarters
    ]
    
    def classify(self, query: str) -> Dict[str, any]:
        """
        Classify query time sensitivity.
        
        Returns:
            dict: {
                'is_time_sensitive': bool,
                'needs_clarification': bool,
                'explicit_timeframe': Optional[str],
                'classification': str  # 'static', 'dynamic', 'hybrid'
            }
        """
        query_lower = query.lower()
        
        # Check for metadata counting patterns (HIGHEST PRIORITY - never time-sensitive)
        for pattern in self.METADATA_PATTERNS:
            if re.search(pattern, query_lower):
                return {
                    'is_time_sensitive': False,
                    'needs_clarification': False,
                    'explicit_timeframe': None,
                    'classification': 'static'
                }
        
        # Check for explicit timeframe
        explicit_timeframe = self._extract_timeframe(query_lower)
        
        # Check for time-sensitive keywords
        has_time_keywords = any(kw in query_lower for kw in self.TIME_SENSITIVE_KEYWORDS)
        
        # Check for static keywords
        has_static_keywords = any(kw in query_lower for kw in self.STATIC_KEYWORDS)
        
        # Classification logic
        if explicit_timeframe:
            classification = 'dynamic'
            is_time_sensitive = True
            needs_clarification = False
        elif has_time_keywords and not has_static_keywords:
            classification = 'dynamic'
            is_time_sensitive = True
            needs_clarification = True  # Need to ask for timeframe
        elif has_static_keywords and not has_time_keywords:
            classification = 'static'
            is_time_sensitive = False
            needs_clarification = False
        else:
            # Hybrid or ambiguous
            classification = 'hybrid'
            is_time_sensitive = has_time_keywords
            needs_clarification = has_time_keywords and not explicit_timeframe
        
        return {
            'is_time_sensitive': is_time_sensitive,
            'needs_clarification': needs_clarification,
            'explicit_timeframe': explicit_timeframe,
            'classification': classification
        }
    
    def _extract_timeframe(self, query: str) -> Optional[str]:
        """Extract explicit timeframe from query."""
        for pattern in self.MONTH_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
