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
        """Parse month string to Period."""
        try:
            # Try standard formats
            for fmt in ['%Y-%m', '%Y/%m', '%B %Y', '%b %Y']:
                try:
                    dt = datetime.strptime(month_str, fmt)
                    return pd.Period(dt, freq='M')
                except:
                    continue
            return None
        except:
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
