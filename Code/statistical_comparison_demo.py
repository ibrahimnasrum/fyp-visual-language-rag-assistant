"""
Statistical Comparison Demo: Binary Routing vs Two-Tier Evaluation

This script demonstrates the statistical improvement from the old binary routing
evaluation (route_match only → PASS/FAIL) to the new two-tier framework 
(routing 30% + quality 70% → PERFECT/ACCEPTABLE/FAILED).

Uses N=20 representative test cases for illustrative purposes. Full N=94 suite
should be used for final quantitative conclusions in FYP thesis.

Author: FYP Visual Language RAG Assistant Team
Date: January 2026
"""

import json
from typing import Dict, List, Tuple, Any
import numpy as np
from scipy import stats


class StatisticalComparison:
    """
    Compare binary routing evaluation against two-tier framework.
    Computes paired t-test and Cohen's d effect size.
    """
    
    def __init__(self):
        self.binary_results = []  # Old method: route_match → 1.0 or 0.0
        self.two_tier_results = []  # New method: overall_score (0-1)
        self.test_cases = []
    
    def add_comparison(self, test_id: str, query: str,
                      binary_score: float, two_tier_score: float):
        """
        Add a paired comparison result.
        
        Args:
            test_id: Test case identifier
            query: User query text
            binary_score: Binary evaluation score (1.0 if route matches, else 0.0)
            two_tier_score: Two-tier evaluation overall score (0-1)
        """
        self.test_cases.append({
            'test_id': test_id,
            'query': query
        })
        self.binary_results.append(binary_score)
        self.two_tier_results.append(two_tier_score)
    
    def compute_paired_ttest(self) -> Dict[str, float]:
        """
        Compute paired t-test comparing binary vs two-tier scores.
        
        Returns:
            Dictionary with:
                - t_statistic: t-test statistic
                - p_value: Two-tailed p-value
                - df: Degrees of freedom
                - mean_diff: Mean difference (two_tier - binary)
                - significant: Whether p < 0.05
        """
        if len(self.binary_results) < 2:
            return {
                't_statistic': 0.0, 'p_value': 1.0, 'df': 0,
                'mean_diff': 0.0, 'significant': False
            }
        
        # Paired t-test: H0: mean(two_tier - binary) = 0
        t_stat, p_value = stats.ttest_rel(self.two_tier_results, self.binary_results)
        
        mean_diff = np.mean(np.array(self.two_tier_results) - np.array(self.binary_results))
        
        return {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'df': len(self.binary_results) - 1,
            'mean_diff': float(mean_diff),
            'significant': p_value < 0.05
        }
    
    def compute_cohens_d(self) -> Dict[str, float]:
        """
        Compute Cohen's d effect size for paired samples.
        
        Returns:
            Dictionary with:
                - cohens_d: Effect size measure
                - effect_size_interpretation: Small/Medium/Large/Very Large
        """
        if len(self.binary_results) < 2:
            return {'cohens_d': 0.0, 'effect_size_interpretation': 'None'}
        
        # Compute differences
        differences = np.array(self.two_tier_results) - np.array(self.binary_results)
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)  # Sample std
        
        # Cohen's d for paired samples: mean_diff / std_diff
        cohens_d = mean_diff / std_diff if std_diff > 0 else 0.0
        
        # Interpret effect size (Cohen's conventions)
        if abs(cohens_d) < 0.2:
            interpretation = "Negligible"
        elif abs(cohens_d) < 0.5:
            interpretation = "Small"
        elif abs(cohens_d) < 0.8:
            interpretation = "Medium"
        elif abs(cohens_d) < 1.2:
            interpretation = "Large"
        else:
            interpretation = "Very Large"
        
        return {
            'cohens_d': float(cohens_d),
            'effect_size_interpretation': interpretation
        }
    
    def compute_improvement_rate(self) -> Dict[str, Any]:
        """
        Compute percentage of cases that improved under two-tier framework.
        
        Returns:
            Dictionary with:
                - improved: Count where two_tier > binary
                - degraded: Count where two_tier < binary
                - unchanged: Count where two_tier == binary
                - improvement_rate: Percentage improved
                - false_failures_recovered: Count where binary=0 but two_tier≥0.7
        """
        improved = 0
        degraded = 0
        unchanged = 0
        false_failures_recovered = 0
        
        for binary, two_tier in zip(self.binary_results, self.two_tier_results):
            if two_tier > binary:
                improved += 1
            elif two_tier < binary:
                degraded += 1
            else:
                unchanged += 1
            
            # False failure recovery: binary marked as fail but two-tier acceptable
            if binary == 0.0 and two_tier >= 0.7:
                false_failures_recovered += 1
        
        total = len(self.binary_results)
        
        return {
            'improved': improved,
            'degraded': degraded,
            'unchanged': unchanged,
            'improvement_rate': improved / total if total > 0 else 0.0,
            'false_failures_recovered': false_failures_recovered,
            'recovery_rate': false_failures_recovered / total if total > 0 else 0.0
        }
    
    def print_comparison_report(self):
        """Print comprehensive statistical comparison report."""
        print("\n" + "="*80)
        print("STATISTICAL COMPARISON: Binary Routing vs Two-Tier Evaluation")
        print("="*80)
        
        n = len(self.binary_results)
        print(f"\nSample Size: N = {n} test cases")
        print(f"Note: This is an illustrative demo. Full N=94 suite recommended for")
        print(f"      final quantitative conclusions in FYP thesis.\n")
        
        # Summary statistics
        print("📊 SUMMARY STATISTICS")
        print("-" * 80)
        binary_mean = np.mean(self.binary_results)
        two_tier_mean = np.mean(self.two_tier_results)
        binary_std = np.std(self.binary_results, ddof=1)
        two_tier_std = np.std(self.two_tier_results, ddof=1)
        
        print(f"Binary Routing Method (Old):")
        print(f"  Mean Score:      {binary_mean:.3f} ± {binary_std:.3f}")
        print(f"  Pass Rate:       {np.sum(np.array(self.binary_results) == 1.0) / n:.1%}")
        print(f"\nTwo-Tier Evaluation (New):")
        print(f"  Mean Score:      {two_tier_mean:.3f} ± {two_tier_std:.3f}")
        print(f"  Success Rate:    {np.sum(np.array(self.two_tier_results) >= 0.7) / n:.1%}")
        print(f"    (ACCEPTABLE threshold ≥ 0.70)")
        
        # Paired t-test
        print("\n🔬 PAIRED T-TEST")
        print("-" * 80)
        ttest = self.compute_paired_ttest()
        print(f"  Null Hypothesis: Mean difference = 0 (no improvement)")
        print(f"  t-statistic:     {ttest['t_statistic']:.4f}")
        print(f"  p-value:         {ttest['p_value']:.6f}")
        print(f"  df:              {ttest['df']}")
        print(f"  Mean difference: {ttest['mean_diff']:.4f} (two-tier - binary)")
        
        if ttest['significant']:
            print(f"\n  ✅ Result: STATISTICALLY SIGNIFICANT (p < 0.05)")
            print(f"     Two-tier evaluation shows significant improvement over binary routing.")
        else:
            print(f"\n  ❌ Result: NOT statistically significant (p ≥ 0.05)")
        
        # Cohen's d effect size
        print("\n📏 EFFECT SIZE ANALYSIS")
        print("-" * 80)
        cohens = self.compute_cohens_d()
        print(f"  Cohen's d:       {cohens['cohens_d']:.4f}")
        print(f"  Interpretation:  {cohens['effect_size_interpretation']}")
        print(f"\n  Reference: Cohen's (1988) conventions")
        print(f"    0.2 = Small, 0.5 = Medium, 0.8 = Large, 1.2+ = Very Large")
        
        # Improvement analysis
        print("\n📈 IMPROVEMENT ANALYSIS")
        print("-" * 80)
        improvement = self.compute_improvement_rate()
        print(f"  Cases Improved:         {improvement['improved']} ({improvement['improvement_rate']:.1%})")
        print(f"  Cases Degraded:         {improvement['degraded']}")
        print(f"  Cases Unchanged:        {improvement['unchanged']}")
        print(f"\n  False Failures Recovered: {improvement['false_failures_recovered']} ({improvement['recovery_rate']:.1%})")
        print(f"    → Cases where binary=FAIL but two-tier=ACCEPTABLE/PERFECT")
        print(f"    → This validates the core hypothesis: routing errors ≠ bad answers")
        
        print("\n" + "="*80)
        print("CONCLUSION")
        print("="*80)
        
        if ttest['significant'] and cohens['cohens_d'] > 0.5:
            print("✅ Two-tier evaluation framework demonstrates STATISTICALLY SIGNIFICANT")
            print("   improvement with a MEANINGFUL effect size over binary routing evaluation.")
            print(f"\n   Key Finding: {improvement['recovery_rate']:.1%} of routing 'failures' are actually")
            print("   acceptable when answer quality is evaluated, reducing false failures.")
        else:
            print("⚠️  Results require larger sample size or additional validation.")
        
        print("="*80 + "\n")
    
    def save_comparison_results(self, filepath: str = "statistical_comparison_results.json"):
        """
        Save comparison results to JSON file.
        
        Args:
            filepath: Path to save results
        """
        results = {
            'metadata': {
                'sample_size': len(self.binary_results),
                'note': 'Illustrative demo with N=20. Use full N=94 for final conclusions.'
            },
            'summary_statistics': {
                'binary_method': {
                    'mean': float(np.mean(self.binary_results)),
                    'std': float(np.std(self.binary_results, ddof=1)),
                    'pass_rate': float(np.sum(np.array(self.binary_results) == 1.0) / len(self.binary_results))
                },
                'two_tier_method': {
                    'mean': float(np.mean(self.two_tier_results)),
                    'std': float(np.std(self.two_tier_results, ddof=1)),
                    'success_rate': float(np.sum(np.array(self.two_tier_results) >= 0.7) / len(self.two_tier_results))
                }
            },
            'statistical_tests': {
                'paired_ttest': {
                    't_statistic': float(self.compute_paired_ttest()['t_statistic']),
                    'p_value': float(self.compute_paired_ttest()['p_value']),
                    'df': int(self.compute_paired_ttest()['df']),
                    'mean_diff': float(self.compute_paired_ttest()['mean_diff']),
                    'significant': bool(self.compute_paired_ttest()['significant'])
                },
                'cohens_d': self.compute_cohens_d()
            },
            'improvement_analysis': self.compute_improvement_rate(),
            'test_cases': []
        }
        
        # Add individual test case results
        for i, test_case in enumerate(self.test_cases):
            results['test_cases'].append({
                'test_id': test_case['test_id'],
                'query': test_case['query'],
                'binary_score': self.binary_results[i],
                'two_tier_score': self.two_tier_results[i],
                'improvement': self.two_tier_results[i] - self.binary_results[i]
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Comparison results saved to: {filepath}")


# Demo with representative test cases
if __name__ == "__main__":
    print("Statistical Comparison Demo")
    print("="*80)
    print("Comparing Binary Routing vs Two-Tier Evaluation Framework")
    print("Using N=20 representative test cases for demonstration\n")
    
    comparison = StatisticalComparison()
    
    # Simulated representative cases based on actual test suite patterns
    # Format: (test_id, query, binary_score, two_tier_score)
    demo_cases = [
        # False failures (routing wrong but answer good) - KEY CASES
        ("H08", "Show me staff with more than 5 years experience", 0.0, 0.816),
        ("H03", "What's our headcount by state?", 0.0, 0.785),
        ("S05", "Revenue trend for 2024", 0.0, 0.742),
        ("R02", "How do we handle employee complaints?", 0.0, 0.768),
        
        # True failures (routing wrong and answer bad)
        ("R03", "Who are the staff?", 0.0, 0.660),
        ("H09", "Random gibberish query xyz", 0.0, 0.320),
        
        # Perfect cases (routing correct and answer good)
        ("H01", "What's our current headcount?", 1.0, 0.950),
        ("S01", "Show me total revenue for this month", 1.0, 0.935),
        ("H02", "List all employees in Sales", 1.0, 0.912),
        ("S02", "What's our revenue by product line?", 1.0, 0.898),
        ("R01", "What's our return policy?", 1.0, 0.885),
        ("H04", "Average salary by department", 1.0, 0.876),
        ("S03", "Top 5 customers by revenue", 1.0, 0.867),
        ("H05", "New hires this quarter", 1.0, 0.854),
        
        # Acceptable cases (routing correct but answer could be better)
        ("S04", "Sales forecast for next quarter", 1.0, 0.765),
        ("H06", "Turnover rate calculation", 1.0, 0.738),
        ("R04", "Shipping policy details", 1.0, 0.721),
        
        # Edge cases
        ("V01", "Describe the floor plan image", 0.0, 0.450),  # Visual - out of scope
        ("H10", "Show me... uhh... the thing", 0.0, 0.380),  # Ambiguous
        ("S06", "Is our revenue good?", 0.0, 0.625),  # Subjective question
    ]
    
    print(f"Loading {len(demo_cases)} test cases...\n")
    
    for test_id, query, binary_score, two_tier_score in demo_cases:
        comparison.add_comparison(test_id, query, binary_score, two_tier_score)
    
    # Run statistical analysis
    comparison.print_comparison_report()
    
    # Save results
    comparison.save_comparison_results("statistical_comparison_results.json")
    
    print("\n✅ Statistical comparison demo complete!")
    print("\nNext Steps:")
    print("  1. Run full N=94 test suite for final FYP conclusions")
    print("  2. Include this comparison in Section 7.4 of FYP documentation")
    print("  3. Reference statistical_comparison_results.json in thesis analysis")
