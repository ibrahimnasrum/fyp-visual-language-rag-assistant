"""
Data Availability Validator - FYP Version
Validates data availability before query execution.
Simplified for academic research (60 lines).
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

class DataValidator:
    """Validates data availability for queries."""
    
    def __init__(self, sales_csv_path: str):
        """Initialize with sales data path."""
        self.sales_csv_path = sales_csv_path
        self._available_months = None
        self._load_available_months()
    
    def _load_available_months(self):
        """Load available months from sales data."""
        try:
            df = pd.read_csv(self.sales_csv_path, parse_dates=['Date'])
            df['YearMonth'] = df['Date'].dt.to_period('M')
            self._available_months = sorted(df['YearMonth'].unique())
        except Exception as e:
            print(f"Error loading data: {e}")
            self._available_months = []
    
    def validate(self, month_str: Optional[str]) -> Dict[str, any]:
        """
        Validate if data is available for the requested month.
        
        Args:
            month_str: Month string (e.g., "2024-01", "January 2024", "H1")
        
        Returns:
            dict: {
                'available': bool,
                'message': str,
                'alternatives': List[str],
                'suggestion': str
            }
        """
        if not month_str:
            # No month specified, return all available
            return {
                'available': True,
                'message': 'No specific month requested. Using all available data.',
                'alternatives': [str(m) for m in self._available_months],
                'suggestion': f"Available months: {', '.join([str(m) for m in self._available_months[:3]])}..."
            }
        
        # Parse month string
        requested_period = self._parse_month(month_str)
        
        if not requested_period:
            return {
                'available': False,
                'message': f"Could not parse month: {month_str}",
                'alternatives': [str(m) for m in self._available_months],
                'suggestion': f"Try: {', '.join([str(m) for m in self._available_months[:3]])}"
            }
        
        # Check availability
        if requested_period in self._available_months:
            return {
                'available': True,
                'message': f"Data available for {requested_period}",
                'alternatives': [],
                'suggestion': ''
            }
        else:
            # Not available, suggest alternatives
            closest = self._find_closest_month(requested_period)
            return {
                'available': False,
                'message': f"Data not available for {requested_period}",
                'alternatives': [str(m) for m in self._available_months],
                'suggestion': f"Available months: {', '.join([str(m) for m in self._available_months])}. Did you mean {closest}?"
            }
    
    def _parse_month(self, month_str: str) -> Optional[pd.Period]:
        """Parse month string to Period - enhanced with month name support."""
        if not month_str:
            return None
            
        month_str = month_str.strip().lower()
        
        # Month name aliases (sync with main bot)
        MONTH_ALIASES = {
            "jan": 1, "january": 1, "januari": 1,
            "feb": 2, "february": 2, "februari": 2,
            "mar": 3, "march": 3, "mac": 3,
            "apr": 4, "april": 4,
            "may": 5, "mei": 5,
            "jun": 6, "june": 6,
            "jul": 7, "july": 7, "julai": 7,
            "aug": 8, "august": 8, "ogos": 8,
            "sep": 9, "sept": 9, "september": 9,
            "oct": 10, "october": 10, "okt": 10, "oktober": 10,
            "nov": 11, "november": 11,
            "dec": 12, "december": 12, "dis": 12, "disember": 12,
        }
        
        try:
            # Try standard formats first
            for fmt in ['%Y-%m', '%Y/%m', '%B %Y', '%b %Y']:
                try:
                    dt = datetime.strptime(month_str, fmt)
                    return pd.Period(dt, freq='M')
                except:
                    continue
            
            # Try month name only (use latest year from available data)
            if month_str in MONTH_ALIASES:
                month_num = MONTH_ALIASES[month_str]
                # Get year from latest available month
                if self._available_months:
                    year = int(str(self._available_months[-1])[:4])
                else:
                    year = datetime.now().year
                return pd.Period(f"{year:04d}-{month_num:02d}", freq='M')
            
            # Try "month YYYY" format (e.g., "june 2024")
            import re
            m = re.search(r'([a-z]+)\s+(20\d{2})', month_str)
            if m:
                month_name, year = m.groups()
                if month_name in MONTH_ALIASES:
                    month_num = MONTH_ALIASES[month_name]
                    return pd.Period(f"{year}-{month_num:02d}", freq='M')
            
            return None
        except Exception as e:
            print(f"⚠️ Month parsing error: {e}")
            return None
    
    def _find_closest_month(self, target: pd.Period) -> str:
        """Find closest available month."""
        if not self._available_months:
            return "N/A"
        closest = min(self._available_months, key=lambda x: abs((x - target).n))
        return str(closest)
    
    def get_available_months(self) -> List[str]:
        """Get list of available months."""
        return [str(m) for m in self._available_months]
