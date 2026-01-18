"""
Advanced Evaluation Metrics Module for Visual Language RAG Assistant

This module provides comprehensive evaluation metrics for analyzing the 
two-tier evaluation framework's performance across multiple dimensions:
- Latency analysis (P50/P75/P90/P95/P99 percentiles)
- Classification metrics (Precision, Recall, F1-score, confusion matrix)
- Category-wise performance breakdown
- Quality-routing correlation analysis
- Statistical visualization (confusion matrix heatmap, latency distribution)

Author: FYP Visual Language RAG Assistant Team
Date: January 2026
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import (
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
    accuracy_score
)
from scipy import stats


class EvaluationMetrics:
    """
    Comprehensive metrics computation for two-tier evaluation framework.
    
    Provides methods for:
    1. Latency performance analysis (percentiles, SLA monitoring)
    2. Classification metrics (precision, recall, F1)
    3. Per-category breakdowns
    4. Quality-routing correlation analysis
    5. Statistical visualization
    """
    
    def __init__(self):
        """Initialize the evaluation metrics calculator."""
        self.results = []
        self.response_times = []
        self.routing_pairs = []  # (expected, actual) tuples
        self.quality_scores = []
        self.categories = defaultdict(list)
        
    def add_result(self, result: Dict[str, Any]):
        """
        Add a single test result for metrics computation.
        
        Args:
            result: Dictionary containing test result with keys:
                - response_time: float (seconds)
                - preferred_route: str
                - actual_route: str
                - quality_score: float (0-1)
                - status: str (PERFECT/ACCEPTABLE/FAILED)
                - category: str (optional)
        """
        self.results.append(result)
        
        if 'response_time' in result:
            self.response_times.append(result['response_time'])
            
        if 'preferred_route' in result and 'actual_route' in result:
            self.routing_pairs.append((result['preferred_route'], result['actual_route']))
            
        if 'quality_score' in result:
            self.quality_scores.append(result['quality_score'])
            
        if 'category' in result:
            category = result['category']
            self.categories[category].append(result)
    
    def compute_latency_metrics(self, response_times: List[float] = None) -> Dict[str, float]:
        """
        Compute latency performance metrics including percentiles.
        
        Args:
            response_times: List of response times in seconds. 
                          If None, uses internally stored times.
        
        Returns:
            Dictionary with keys:
                - mean: Average response time
                - median (P50): 50th percentile
                - p75: 75th percentile
                - p90: 90th percentile
                - p95: 95th percentile
                - p99: 99th percentile
                - min: Minimum response time
                - max: Maximum response time
                - std: Standard deviation
        """
        times = response_times if response_times is not None else self.response_times
        
        if not times:
            return {
                'mean': 0.0, 'median': 0.0, 'p75': 0.0, 'p90': 0.0,
                'p95': 0.0, 'p99': 0.0, 'min': 0.0, 'max': 0.0, 'std': 0.0
            }
        
        times_array = np.array(times)
        
        return {
            'mean': float(np.mean(times_array)),
            'median': float(np.percentile(times_array, 50)),
            'p75': float(np.percentile(times_array, 75)),
            'p90': float(np.percentile(times_array, 90)),
            'p95': float(np.percentile(times_array, 95)),
            'p99': float(np.percentile(times_array, 99)),
            'min': float(np.min(times_array)),
            'max': float(np.max(times_array)),
            'std': float(np.std(times_array))
        }
    
    def compute_classification_metrics(self, 
                                       routing_pairs: List[Tuple[str, str]] = None,
                                       labels: List[str] = None) -> Dict[str, Any]:
        """
        Compute classification metrics for routing accuracy.
        
        Args:
            routing_pairs: List of (expected, actual) route tuples.
                          If None, uses internally stored pairs.
            labels: List of unique route labels for confusion matrix ordering.
                   If None, infers from data.
        
        Returns:
            Dictionary with keys:
                - accuracy: Overall accuracy (0-1)
                - precision: Per-class precision scores
                - recall: Per-class recall scores
                - f1_score: Per-class F1 scores
                - macro_f1: Macro-averaged F1 score
                - weighted_f1: Weighted F1 score
                - confusion_matrix: 2D numpy array
                - classification_report: Detailed sklearn report string
                - labels: List of route labels (order matches confusion matrix)
        """
        pairs = routing_pairs if routing_pairs is not None else self.routing_pairs
        
        if not pairs:
            return {
                'accuracy': 0.0, 'precision': [], 'recall': [], 'f1_score': [],
                'macro_f1': 0.0, 'weighted_f1': 0.0, 'confusion_matrix': np.array([]),
                'classification_report': 'No data available', 'labels': []
            }
        
        y_true = [pair[0] for pair in pairs]
        y_pred = [pair[1] for pair in pairs]
        
        # Infer labels if not provided
        if labels is None:
            labels = sorted(list(set(y_true + y_pred)))
        
        # Compute metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, average=None, zero_division=0
        )
        macro_f1 = np.mean(f1)
        
        # Weighted F1 (by support)
        _, _, weighted_f1_array, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, average='weighted', zero_division=0
        )
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        # Classification report
        report = classification_report(y_true, y_pred, labels=labels, zero_division=0)
        
        return {
            'accuracy': float(accuracy),
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'f1_score': f1.tolist(),
            'macro_f1': float(macro_f1),
            'weighted_f1': float(weighted_f1_array),
            'confusion_matrix': cm,
            'classification_report': report,
            'labels': labels,
            'support': support.tolist()
        }
    
    def compute_category_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """
        Compute performance metrics broken down by test category.
        
        Returns:
            Dictionary mapping category names to metrics:
                - total: Number of tests in category
                - perfect: Count of PERFECT status
                - acceptable: Count of ACCEPTABLE status
                - failed: Count of FAILED status
                - avg_quality_score: Average quality score
                - avg_response_time: Average response time
                - success_rate: (perfect + acceptable) / total
        """
        breakdown = {}
        
        for category, results in self.categories.items():
            if not results:
                continue
                
            total = len(results)
            perfect = sum(1 for r in results if r.get('status') == 'PERFECT')
            acceptable = sum(1 for r in results if r.get('status') == 'ACCEPTABLE')
            failed = sum(1 for r in results if r.get('status') == 'FAILED')
            
            quality_scores = [r.get('quality_score', 0) for r in results if 'quality_score' in r]
            avg_quality = np.mean(quality_scores) if quality_scores else 0.0
            
            response_times = [r.get('response_time', 0) for r in results if 'response_time' in r]
            avg_time = np.mean(response_times) if response_times else 0.0
            
            success_rate = (perfect + acceptable) / total if total > 0 else 0.0
            
            breakdown[category] = {
                'total': total,
                'perfect': perfect,
                'acceptable': acceptable,
                'failed': failed,
                'avg_quality_score': float(avg_quality),
                'avg_response_time': float(avg_time),
                'success_rate': float(success_rate)
            }
        
        return breakdown
    
    def compute_quality_routing_correlation(self) -> Dict[str, Any]:
        """
        Analyze correlation between routing accuracy and answer quality.
        
        Returns:
            Dictionary with:
                - correlation: Pearson correlation coefficient
                - p_value: Statistical significance
                - route_perfect_avg_quality: Avg quality when route is perfect
                - route_wrong_avg_quality: Avg quality when route is wrong
                - quality_saves_routing: Count where quality ≥0.7 despite wrong route
        """
        if not self.results:
            return {
                'correlation': 0.0, 'p_value': 1.0,
                'route_perfect_avg_quality': 0.0, 'route_wrong_avg_quality': 0.0,
                'quality_saves_routing': 0
            }
        
        # Extract routing accuracy (1 for correct, 0 for incorrect)
        routing_correct = []
        quality_scores = []
        
        route_perfect_qualities = []
        route_wrong_qualities = []
        quality_saves = 0
        
        for result in self.results:
            if 'preferred_route' not in result or 'actual_route' not in result:
                continue
            if 'quality_score' not in result:
                continue
            
            is_correct = result['preferred_route'] == result['actual_route']
            quality = result['quality_score']
            
            routing_correct.append(1 if is_correct else 0)
            quality_scores.append(quality)
            
            if is_correct:
                route_perfect_qualities.append(quality)
            else:
                route_wrong_qualities.append(quality)
                if quality >= 0.7:  # Acceptable threshold
                    quality_saves += 1
        
        # Compute correlation
        correlation, p_value = stats.pearsonr(routing_correct, quality_scores) if len(routing_correct) > 1 else (0.0, 1.0)
        
        return {
            'correlation': float(correlation),
            'p_value': float(p_value),
            'route_perfect_avg_quality': float(np.mean(route_perfect_qualities)) if route_perfect_qualities else 0.0,
            'route_wrong_avg_quality': float(np.mean(route_wrong_qualities)) if route_wrong_qualities else 0.0,
            'quality_saves_routing': quality_saves,
            'n_samples': len(routing_correct)
        }
    
    def generate_confusion_matrix_plot(self, 
                                       confusion_matrix: np.ndarray, 
                                       labels: List[str],
                                       save_path: str = 'confusion_matrix.png',
                                       figsize: Tuple[int, int] = (10, 8)) -> str:
        """
        Generate and save confusion matrix heatmap visualization.
        
        Uses standard matplotlib styling without seaborn themes.
        
        Args:
            confusion_matrix: 2D numpy array from compute_classification_metrics
            labels: List of route labels (from compute_classification_metrics)
            save_path: Path to save the PNG file
            figsize: Figure size (width, height) in inches
        
        Returns:
            Path to saved figure
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create heatmap manually without seaborn
        im = ax.imshow(confusion_matrix, cmap='Blues', aspect='auto')
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(labels)))
        ax.set_yticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_yticklabels(labels)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Count', rotation=270, labelpad=20)
        
        # Add text annotations
        for i in range(len(labels)):
            for j in range(len(labels)):
                text = ax.text(j, i, int(confusion_matrix[i, j]),
                             ha="center", va="center", 
                             color="white" if confusion_matrix[i, j] > confusion_matrix.max()/2 else "black",
                             fontweight='bold')
        
        # Labels and title
        ax.set_xlabel('Predicted Route', fontsize=12, fontweight='bold')
        ax.set_ylabel('Expected Route', fontsize=12, fontweight='bold')
        ax.set_title('Routing Confusion Matrix\nTwo-Tier Evaluation Framework', 
                     fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def generate_latency_distribution(self,
                                      response_times: List[float] = None,
                                      save_path: str = 'latency_distribution.png',
                                      figsize: Tuple[int, int] = (12, 6)) -> str:
        """
        Generate and save latency distribution histogram with percentile markers.
        
        Uses standard matplotlib styling.
        
        Args:
            response_times: List of response times in seconds. If None, uses stored times.
            save_path: Path to save the PNG file
            figsize: Figure size (width, height) in inches
        
        Returns:
            Path to saved figure
        """
        times = response_times if response_times is not None else self.response_times
        
        if not times:
            print("No response time data available for plotting.")
            return ""
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create histogram
        n, bins, patches = ax.hist(times, bins=30, color='steelblue', 
                                   alpha=0.7, edgecolor='black', linewidth=0.5)
        
        # Compute percentiles
        metrics = self.compute_latency_metrics(times)
        percentiles = {
            'P50 (Median)': metrics['median'],
            'P75': metrics['p75'],
            'P90': metrics['p90'],
            'P95': metrics['p95'],
            'P99': metrics['p99']
        }
        
        # Add percentile lines
        colors = ['green', 'orange', 'red', 'darkred', 'purple']
        for (label, value), color in zip(percentiles.items(), colors):
            ax.axvline(value, color=color, linestyle='--', linewidth=2, label=f'{label}: {value:.2f}s')
        
        # Labels and title
        ax.set_xlabel('Response Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title('Response Time Distribution with Percentile Markers\nTwo-Tier Evaluation Framework',
                     fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
        
        # Add statistics text box
        stats_text = f'Mean: {metrics["mean"]:.2f}s\nStd: {metrics["std"]:.2f}s\nN: {len(times)}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def compute_all_metrics(self) -> Dict[str, Any]:
        """
        Compute all available metrics in one call.
        
        Returns:
            Dictionary containing:
                - latency: Latency metrics dict
                - classification: Classification metrics dict
                - category_breakdown: Per-category metrics dict
                - quality_routing_correlation: Correlation analysis dict
        """
        return {
            'latency': self.compute_latency_metrics(),
            'classification': self.compute_classification_metrics(),
            'category_breakdown': self.compute_category_breakdown(),
            'quality_routing_correlation': self.compute_quality_routing_correlation()
        }
    
    def print_all_metrics(self, metrics: Dict[str, Any] = None):
        """
        Print all metrics in a formatted, human-readable way.
        
        Args:
            metrics: Dictionary from compute_all_metrics(). If None, computes fresh.
        """
        if metrics is None:
            metrics = self.compute_all_metrics()
        
        print("\n" + "="*80)
        print("ADVANCED EVALUATION METRICS REPORT")
        print("="*80)
        
        # Latency Metrics
        print("\n📊 LATENCY PERFORMANCE ANALYSIS")
        print("-" * 80)
        latency = metrics['latency']
        print(f"  Mean Response Time:     {latency['mean']:.3f}s")
        print(f"  Median (P50):           {latency['median']:.3f}s")
        print(f"  P75 (75th percentile):  {latency['p75']:.3f}s")
        print(f"  P90 (90th percentile):  {latency['p90']:.3f}s")
        print(f"  P95 (95th percentile):  {latency['p95']:.3f}s ⚠️  [SLA Target]")
        print(f"  P99 (99th percentile):  {latency['p99']:.3f}s")
        print(f"  Min / Max:              {latency['min']:.3f}s / {latency['max']:.3f}s")
        print(f"  Std Deviation:          {latency['std']:.3f}s")
        
        # Classification Metrics
        print("\n🎯 ROUTING CLASSIFICATION METRICS")
        print("-" * 80)
        classification = metrics['classification']
        print(f"  Overall Accuracy:       {classification['accuracy']:.2%}")
        print(f"  Macro F1-Score:         {classification['macro_f1']:.3f}")
        print(f"  Weighted F1-Score:      {classification['weighted_f1']:.3f}")
        
        if classification['labels']:
            print("\n  Per-Route Performance:")
            for i, label in enumerate(classification['labels']):
                print(f"    {label:15s} - P: {classification['precision'][i]:.3f}  "
                      f"R: {classification['recall'][i]:.3f}  "
                      f"F1: {classification['f1_score'][i]:.3f}  "
                      f"(n={classification['support'][i]})")
        
        # Quality-Routing Correlation
        print("\n🔗 QUALITY-ROUTING CORRELATION ANALYSIS")
        print("-" * 80)
        correlation = metrics['quality_routing_correlation']
        print(f"  Pearson Correlation:    {correlation['correlation']:.3f} (p={correlation['p_value']:.4f})")
        print(f"  Avg Quality (Route Perfect): {correlation['route_perfect_avg_quality']:.3f}")
        print(f"  Avg Quality (Route Wrong):   {correlation['route_wrong_avg_quality']:.3f}")
        print(f"  Quality Saves Routing:       {correlation['quality_saves_routing']} cases")
        print(f"    → {correlation['quality_saves_routing']/correlation['n_samples']*100:.1f}% of wrong routes still acceptable due to quality")
        
        # Category Breakdown
        print("\n📁 PER-CATEGORY PERFORMANCE BREAKDOWN")
        print("-" * 80)
        breakdown = metrics['category_breakdown']
        if breakdown:
            for category, stats in sorted(breakdown.items()):
                print(f"\n  {category}:")
                print(f"    Total Tests:        {stats['total']}")
                print(f"    Perfect:            {stats['perfect']} ({stats['perfect']/stats['total']*100:.1f}%)")
                print(f"    Acceptable:         {stats['acceptable']} ({stats['acceptable']/stats['total']*100:.1f}%)")
                print(f"    Failed:             {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
                print(f"    Success Rate:       {stats['success_rate']:.2%}")
                print(f"    Avg Quality Score:  {stats['avg_quality_score']:.3f}")
                print(f"    Avg Response Time:  {stats['avg_response_time']:.3f}s")
        else:
            print("  No category data available.")
        
        print("\n" + "="*80)


# Standalone demo
if __name__ == "__main__":
    print("Evaluation Metrics Module - Demo")
    print("="*80)
    
    # Create sample data
    metrics = EvaluationMetrics()
    
    # Add sample results
    sample_results = [
        {'response_time': 2.5, 'preferred_route': 'hr_kpi', 'actual_route': 'hr_kpi', 
         'quality_score': 0.95, 'status': 'PERFECT', 'category': 'HR_KPI'},
        {'response_time': 3.2, 'preferred_route': 'sales_kpi', 'actual_route': 'rag_docs', 
         'quality_score': 0.75, 'status': 'ACCEPTABLE', 'category': 'SALES_KPI'},
        {'response_time': 1.8, 'preferred_route': 'rag_docs', 'actual_route': 'rag_docs', 
         'quality_score': 0.88, 'status': 'PERFECT', 'category': 'RAG_DOCS'},
        {'response_time': 4.1, 'preferred_route': 'hr_kpi', 'actual_route': 'sales_kpi', 
         'quality_score': 0.45, 'status': 'FAILED', 'category': 'HR_KPI'},
        {'response_time': 2.9, 'preferred_route': 'sales_kpi', 'actual_route': 'sales_kpi', 
         'quality_score': 0.92, 'status': 'PERFECT', 'category': 'SALES_KPI'},
    ]
    
    for result in sample_results:
        metrics.add_result(result)
    
    # Compute and print all metrics
    all_metrics = metrics.compute_all_metrics()
    metrics.print_all_metrics(all_metrics)
    
    # Generate visualizations
    print("\n📈 Generating visualizations...")
    classification = all_metrics['classification']
    
    if len(classification['confusion_matrix']) > 0:
        cm_path = metrics.generate_confusion_matrix_plot(
            classification['confusion_matrix'],
            classification['labels'],
            'demo_confusion_matrix.png'
        )
        print(f"  ✓ Confusion matrix saved: {cm_path}")
    
    latency_path = metrics.generate_latency_distribution(
        save_path='demo_latency_distribution.png'
    )
    print(f"  ✓ Latency distribution saved: {latency_path}")
    
    print("\n✅ Demo complete!")
