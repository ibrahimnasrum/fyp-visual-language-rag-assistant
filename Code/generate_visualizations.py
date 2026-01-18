"""
Generate Advanced Metrics Visualizations from Test Results
Generates confusion matrix and latency distribution plots for FYP documentation
"""

import json
from pathlib import Path
from evaluation_metrics import EvaluationMetrics

# Load the latest test results
results_file = Path(__file__).parent / 'test_results_20260117_043810.json'
with open(results_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Initialize metrics collector
metrics = EvaluationMetrics()

# Add all results to the metrics collector
for result in data['results']:
    if result.get('status') != 'ERROR':
        metrics.add_result({
            'response_time': result.get('response_time'),
            'preferred_route': result.get('preferred_route'),
            'actual_route': result.get('actual_route'),
            'quality_score': result.get('quality_score'),
            'status': result.get('status'),
            'category': result.get('id', '')[:1] if result.get('id') else 'UNKNOWN'
        })

print("📊 Computing and displaying all metrics...\n")

# Compute all metrics
all_metrics = metrics.compute_all_metrics()

# Print comprehensive metrics
metrics.print_all_metrics()

# Generate visualizations
print("\n📈 Generating visualizations...")

# Get classification metrics first for confusion matrix
classification_metrics = metrics.compute_classification_metrics()

print("   1. Confusion matrix heatmap...")
confusion_matrix_path = metrics.generate_confusion_matrix_plot(
    classification_metrics['confusion_matrix'],
    classification_metrics['labels'],
    'confusion_matrix_fyp.png'
)
print(f"      ✅ Saved: {confusion_matrix_path}")

print("   2. Latency distribution histogram...")
try:
    latency_dist_path = metrics.generate_latency_distribution(
        'latency_distribution_fyp.png'
    )
    print(f"      ✅ Saved: {latency_dist_path}")
except Exception as e:
    print(f"      ⚠️  Could not generate latency plot: {e}")
    print(f"      Note: Latency metrics are available in the text report above")

print("\n✅ All visualizations generated successfully!")
print("\n📋 Summary:")
print(f"   Total tests: {data['total_tests']}")
print(f"   Perfect: {data['perfect']}")
print(f"   Acceptable: {data['acceptable']}")
print(f"   Failed: {data['failed']}")
print(f"   User Satisfaction Rate: {data['user_satisfaction_rate']*100:.1f}%")
