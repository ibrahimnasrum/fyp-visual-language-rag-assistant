"""
Generate all PNG figures for FYP Chapter 4
Creates professional publication-quality visualizations
Output directory: ../images/fyp_figures/
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'DejaVu Sans'

# Create output directory
output_dir = Path("../images/fyp_figures")
output_dir.mkdir(parents=True, exist_ok=True)

print("🎨 Generating FYP Chapter 4 Figures...")
print(f"📁 Output directory: {output_dir.absolute()}\n")

# Data
models = ['llama3:latest', 'phi3:mini', 'qwen2.5:7b', 'mistral:7b']
models_short = ['llama3', 'phi3', 'qwen', 'mistral']
satisfaction = [88, 82, 82, 78]
routing_acc = [76, 70, 76, 68]
quality_scores = [0.709, 0.695, 0.700, 0.697]

# Response time data
response_times = {
    'llama3': {'min': 0.87, 'q1': 1.25, 'median': 1.36, 'q3': 30.75, 'max': 69.42, 'p95': 54.27},
    'phi3': {'min': 0.61, 'q1': 0.95, 'median': 1.01, 'q3': 12.50, 'max': 34.25, 'p95': 23.88},
    'qwen': {'min': 0.76, 'q1': 1.10, 'median': 1.34, 'q3': 16.33, 'max': 43.94, 'p95': 32.02},
    'mistral': {'min': 0.81, 'q1': 1.20, 'median': 1.51, 'q3': 28.40, 'max': 72.83, 'p95': 64.12}
}

# Quality components
quality_components = {
    'llama3': {'semantic': 0.820, 'completeness': 0.750, 'accuracy': 0.780, 'presentation': 0.900},
    'phi3': {'semantic': 0.800, 'completeness': 0.650, 'accuracy': 0.720, 'presentation': 0.850},
    'qwen': {'semantic': 0.810, 'completeness': 0.680, 'accuracy': 0.740, 'presentation': 0.880},
    'mistral': {'semantic': 0.805, 'completeness': 0.660, 'accuracy': 0.730, 'presentation': 0.870}
}

# Statistical significance
ci_data = {
    'llama3': {'sat': 88, 'lower': 75.7, 'upper': 95.5},
    'phi3': {'sat': 82, 'lower': 68.6, 'upper': 91.4},
    'qwen': {'sat': 82, 'lower': 68.6, 'upper': 91.4},
    'mistral': {'sat': 78, 'lower': 63.9, 'upper': 88.5}
}

# =============================================================================
# FIGURE 4.1: Grouped Bar Chart (Satisfaction + Routing)
# =============================================================================
print("📊 Generating Figure 4.1: Grouped Bar Chart...")

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(models_short))
width = 0.35

bars1 = ax.bar(x - width/2, satisfaction, width, label='Satisfaction Rate (%)', 
               color='#3498db', edgecolor='black', linewidth=1.2)
bars2 = ax.bar(x + width/2, routing_acc, width, label='Routing Accuracy (%)', 
               color='#2ecc71', edgecolor='black', linewidth=1.2)

# Highlight llama3
bars1[0].set_edgecolor('gold')
bars1[0].set_linewidth(3)
bars2[0].set_edgecolor('gold')
bars2[0].set_linewidth(3)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_xlabel('Model', fontsize=12, fontweight='bold')
ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
ax.set_title('Figure 4.1: Overall Model Performance Comparison', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(models_short)
ax.legend(loc='upper right', frameon=True, shadow=True)
ax.set_ylim(0, 100)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig(output_dir / 'figure_4_1_grouped_bar_satisfaction_routing.png', bbox_inches='tight')
plt.close()
print(f"   ✅ Saved: figure_4_1_grouped_bar_satisfaction_routing.png")

# =============================================================================
# FIGURE 4.2: Comprehensive Comparison (Bars + Line)
# =============================================================================
print("📊 Generating Figure 4.2: Comprehensive Comparison...")

fig, ax1 = plt.subplots(figsize=(12, 7))
x = np.arange(len(models_short))
width = 0.6

# Color bars by routing accuracy
colors = []
for acc in routing_acc:
    if acc >= 76:
        colors.append('#2ecc71')  # Green
    elif acc >= 70:
        colors.append('#f39c12')  # Yellow
    else:
        colors.append('#e74c3c')  # Red

bars = ax1.bar(x, satisfaction, width, color=colors, edgecolor='black', 
               linewidth=1.5, alpha=0.8, label='Satisfaction Rate (%)')

# Add satisfaction labels
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{int(height)}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    # Add routing accuracy label inside bar
    ax1.text(bar.get_x() + bar.get_width()/2., height - 5,
            f'Routing: {routing_acc[i]}%', ha='center', va='top', 
            fontsize=9, color='white', fontweight='bold')

ax1.set_xlabel('Model', fontsize=13, fontweight='bold')
ax1.set_ylabel('Satisfaction Rate (%)', fontsize=13, fontweight='bold', color='black')
ax1.set_xticks(x)
ax1.set_xticklabels(models_short, fontsize=11)
ax1.set_ylim(0, 100)
ax1.tick_params(axis='y', labelcolor='black')
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Secondary y-axis for quality score
ax2 = ax1.twinx()
line = ax2.plot(x, quality_scores, color='#9b59b6', marker='D', markersize=10, 
                linewidth=3, label='Quality Score', linestyle='-', markeredgecolor='black', 
                markeredgewidth=1.5)

# Add quality score labels
for i, score in enumerate(quality_scores):
    ax2.text(x[i], score + 0.003, f'{score:.3f}', ha='center', va='bottom', 
            fontsize=10, fontweight='bold', color='#9b59b6')

ax2.set_ylabel('Quality Score (0-1)', fontsize=13, fontweight='bold', color='#9b59b6')
ax2.set_ylim(0.68, 0.72)
ax2.tick_params(axis='y', labelcolor='#9b59b6')

# Legend
green_patch = mpatches.Patch(color='#2ecc71', label='Routing ≥76% (Excellent)')
yellow_patch = mpatches.Patch(color='#f39c12', label='Routing 70-75% (Good)')
red_patch = mpatches.Patch(color='#e74c3c', label='Routing <70% (Poor)')
line_patch = mpatches.Patch(color='#9b59b6', label='Quality Score')

ax1.legend(handles=[green_patch, yellow_patch, red_patch, line_patch], 
          loc='lower left', frameon=True, shadow=True, fontsize=10)

plt.title('Figure 4.2: Model Performance with Quality Scores & Routing', 
         fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(output_dir / 'figure_4_2_comprehensive_comparison.png', bbox_inches='tight')
plt.close()
print(f"   ✅ Saved: figure_4_2_comprehensive_comparison.png")

# =============================================================================
# FIGURE 4.3: Box Plot (Response Time Distribution)
# =============================================================================
print("📊 Generating Figure 4.3: Box Plot...")

fig, ax = plt.subplots(figsize=(12, 7))

# Prepare data for box plot
box_data = []
for model in models_short:
    data = response_times[model]
    # Create distribution data from quartiles
    box_data.append([data['min'], data['q1'], data['median'], data['q3'], data['max']])

positions = np.arange(1, len(models_short) + 1)
bp = ax.boxplot(box_data, positions=positions, widths=0.6, patch_artist=True,
                showfliers=True, notch=False,
                boxprops=dict(facecolor='lightblue', edgecolor='black', linewidth=1.5),
                medianprops=dict(color='red', linewidth=2),
                whiskerprops=dict(color='black', linewidth=1.5),
                capprops=dict(color='black', linewidth=1.5))

# Color code boxes
box_colors = ['#f39c12', '#2ecc71', '#3498db', '#e74c3c']  # llama3, phi3, qwen, mistral
for patch, color in zip(bp['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Add P95 markers
for i, model in enumerate(models_short):
    p95 = response_times[model]['p95']
    ax.plot(i + 1, p95, 'D', color='red', markersize=12, markeredgecolor='black', 
           markeredgewidth=1.5, label='P95' if i == 0 else '', zorder=5)
    ax.text(i + 1, p95 + 3, f'P95: {p95:.1f}s', ha='center', va='bottom', 
           fontsize=9, fontweight='bold', color='darkred')

# Add median labels
for i, model in enumerate(models_short):
    median = response_times[model]['median']
    ax.text(i + 1, median, f'{median:.2f}s', ha='center', va='center', 
           fontsize=9, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.set_xlabel('Model', fontsize=13, fontweight='bold')
ax.set_ylabel('Response Time (seconds)', fontsize=13, fontweight='bold')
ax.set_title('Figure 4.3: Response Time Distribution with P95 Latency', 
            fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(positions)
ax.set_xticklabels(models_short)
ax.set_ylim(0, 75)
ax.legend(loc='upper right', frameon=True, shadow=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add annotations
ax.text(2, 70, 'phi3: Consistent & Fast', fontsize=10, color='#2ecc71', 
       fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
ax.text(4, 70, 'mistral: High Variance', fontsize=10, color='#e74c3c', 
       fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

plt.tight_layout()
plt.savefig(output_dir / 'figure_4_3_boxplot_response_time.png', bbox_inches='tight')
plt.close()
print(f"   ✅ Saved: figure_4_3_boxplot_response_time.png")

# =============================================================================
# FIGURE 4.24: Quality Component Breakdown (Stacked Bar)
# =============================================================================
print("📊 Generating Figure 4.24: Quality Component Breakdown...")

fig, ax = plt.subplots(figsize=(12, 7))

# Prepare data
components = ['semantic', 'completeness', 'accuracy', 'presentation']
component_labels = ['Semantic', 'Completeness', 'Accuracy', 'Presentation']
colors = ['#3498db', '#2ecc71', '#f39c12', '#9b59b6']

x = np.arange(len(models_short))
width = 0.6

# Create stacked bars
bottom = np.zeros(len(models_short))
for i, comp in enumerate(components):
    values = [quality_components[model][comp] for model in models_short]
    bars = ax.bar(x, values, width, label=component_labels[i], 
                  color=colors[i], edgecolor='black', linewidth=1.2, bottom=bottom)
    
    # Add value labels
    for j, (bar, val) in enumerate(zip(bars, values)):
        if val > 0.05:  # Only show label if segment is large enough
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., bottom[j] + height/2,
                   f'{val:.3f}', ha='center', va='center', fontsize=9, 
                   fontweight='bold', color='white' if val > 0.7 else 'black')
    
    bottom += values

ax.set_xlabel('Model', fontsize=13, fontweight='bold')
ax.set_ylabel('Quality Score (0-1)', fontsize=13, fontweight='bold')
ax.set_title('Figure 4.24: Quality Component Breakdown by Model', 
            fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(models_short)
ax.set_ylim(0, max(bottom) * 1.1)
ax.legend(loc='upper right', frameon=True, shadow=True, ncol=2)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add total score on top
for i, model in enumerate(models_short):
    total = sum(quality_components[model].values()) / 4  # Average
    ax.text(i, bottom[i] + 0.05, f'Avg: {total:.3f}', ha='center', va='bottom', 
           fontsize=10, fontweight='bold', color='darkblue',
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

plt.tight_layout()
plt.savefig(output_dir / 'figure_4_24_quality_components_stacked.png', bbox_inches='tight')
plt.close()
print(f"   ✅ Saved: figure_4_24_quality_components_stacked.png")

# =============================================================================
# FIGURE 4.25: Latency Waterfall Chart
# =============================================================================
print("📊 Generating Figure 4.25: Latency Waterfall...")

fig, ax = plt.subplots(figsize=(12, 8))

# Data
components = ['Base API\nOverhead', 'Routing\n(LLM)', 'FAISS\nRetrieval', 
             'Context\nPrep', 'LLM\nInference', 'Post-\nProcessing']
times = [0.2, 0.5, 1.8, 0.8, 24.5, 0.5]
cumulative = np.cumsum([0] + times)

# Colors (highlight bottleneck in red)
colors_waterfall = ['gray', 'gray', 'orange', 'gray', 'red', 'gray']

x = np.arange(len(components))
bars = ax.bar(x, times, bottom=cumulative[:-1], color=colors_waterfall, 
             edgecolor='black', linewidth=1.5, alpha=0.8, width=0.7)

# Add time labels and percentages
for i, (bar, time) in enumerate(zip(bars, times)):
    height = bar.get_height()
    percentage = (time / sum(times)) * 100
    # Time label
    ax.text(bar.get_x() + bar.get_width()/2., cumulative[i] + height/2,
           f'{time:.1f}s', ha='center', va='center', fontsize=11, 
           fontweight='bold', color='white' if time > 5 else 'black')
    # Percentage label
    ax.text(bar.get_x() + bar.get_width()/2., cumulative[i] + height + 0.5,
           f'{percentage:.1f}%', ha='center', va='bottom', fontsize=9, 
           fontweight='bold', color=colors_waterfall[i])

# Add cumulative line
ax.plot(x, cumulative[1:], 'ko-', linewidth=2, markersize=8, label='Cumulative Time')

# Final total
ax.text(len(components) - 0.5, cumulative[-1] + 1, 
       f'Total: {sum(times):.1f}s', ha='center', va='bottom', 
       fontsize=12, fontweight='bold', color='darkgreen',
       bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

ax.set_xlabel('Latency Component', fontsize=13, fontweight='bold')
ax.set_ylabel('Time (seconds)', fontsize=13, fontweight='bold')
ax.set_title('Figure 4.25: Latency Component Waterfall (RAG Queries - llama3)', 
            fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(components, fontsize=10)
ax.set_ylim(0, 32)
ax.legend(loc='upper left', frameon=True, shadow=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add bottleneck annotation
ax.annotate('Primary Bottleneck\n(87% of total time)', 
           xy=(4, cumulative[4] + times[4]/2), xytext=(5.5, 20),
           arrowprops=dict(arrowstyle='->', color='red', lw=2),
           fontsize=11, fontweight='bold', color='red',
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

plt.tight_layout()
plt.savefig(output_dir / 'figure_4_25_latency_waterfall.png', bbox_inches='tight')
plt.close()
print(f"   ✅ Saved: figure_4_25_latency_waterfall.png")

# =============================================================================
# FIGURE 4.26: Statistical Significance (Error Bars)
# =============================================================================
print("📊 Generating Figure 4.26: Statistical Significance...")

fig, ax = plt.subplots(figsize=(12, 7))

x = np.arange(len(models_short))
sats = [ci_data[model]['sat'] for model in models_short]
lowers = [ci_data[model]['sat'] - ci_data[model]['lower'] for model in models_short]
uppers = [ci_data[model]['upper'] - ci_data[model]['sat'] for model in models_short]

# Color code bars
bar_colors = ['gold', 'silver', 'silver', 'gray']
bars = ax.bar(x, sats, width=0.6, color=bar_colors, edgecolor='black', 
             linewidth=1.5, alpha=0.8, yerr=[lowers, uppers], 
             capsize=10, error_kw={'linewidth': 2, 'ecolor': 'black'})

# Add value labels
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
           f'{int(height)}%', ha='center', va='bottom', fontsize=12, fontweight='bold')
    # Add CI range
    lower_val = ci_data[models_short[i]]['lower']
    upper_val = ci_data[models_short[i]]['upper']
    ax.text(bar.get_x() + bar.get_width()/2., 55,
           f'95% CI:\n[{lower_val:.1f}%, {upper_val:.1f}%]', 
           ha='center', va='center', fontsize=8, style='italic')

# Add significance markers
ax.text(1.5, 100, 'p = 0.157 (NS)', fontsize=10, ha='center', 
       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
ax.text(0.5, 95, '* p = 0.045', fontsize=10, ha='center', color='red', fontweight='bold',
       bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

# Draw overlap region
ax.axhspan(68.6, 91.4, alpha=0.2, color='orange', label='Overlapping CI Region')

ax.set_xlabel('Model', fontsize=13, fontweight='bold')
ax.set_ylabel('Satisfaction Rate (%)', fontsize=13, fontweight='bold')
ax.set_title('Figure 4.26: Statistical Significance with 95% Confidence Intervals', 
            fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(models_short)
ax.set_ylim(50, 105)
ax.legend(loc='lower right', frameon=True, shadow=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add interpretation note
ax.text(0.5, 0.02, 'Note: * = Significant at α=0.05; NS = Not Significant', 
       transform=ax.transAxes, fontsize=9, style='italic',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig(output_dir / 'figure_4_26_statistical_significance.png', bbox_inches='tight')
plt.close()
print(f"   ✅ Saved: figure_4_26_statistical_significance.png")

# =============================================================================
# FIGURE 4.4: Adaptive Routing Flowchart (Simplified)
# =============================================================================
print("📊 Generating Figure 4.4: Adaptive Routing Strategy...")

fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Title
ax.text(5, 9.5, 'Figure 4.4: Adaptive Hybrid Routing Strategy', 
       fontsize=16, fontweight='bold', ha='center')

# Input box
input_box = FancyBboxPatch((4, 8.5), 2, 0.5, boxstyle="round,pad=0.1", 
                          edgecolor='black', facecolor='lightblue', linewidth=2)
ax.add_patch(input_box)
ax.text(5, 8.75, 'Query Input', ha='center', va='center', fontsize=11, fontweight='bold')

# Arrow down
ax.annotate('', xy=(5, 8.0), xytext=(5, 8.5), 
           arrowprops=dict(arrowstyle='->', lw=2, color='black'))

# Category classification
cat_box = FancyBboxPatch((3.5, 7.2), 3, 0.6, boxstyle="round,pad=0.1", 
                         edgecolor='black', facecolor='lightyellow', linewidth=2)
ax.add_patch(cat_box)
ax.text(5, 7.5, 'Category Classification', ha='center', va='center', 
       fontsize=11, fontweight='bold')

# Four routes
routes = [
    {'x': 0.5, 'label': 'Sales KPI\n(15 queries)', 'model': 'qwen2.5:7b', 
     'stat': 'Fastest: 1.11s\n93.3% success', 'color': '#2ecc71'},
    {'x': 2.5, 'label': 'HR KPI\n(10 queries)', 'model': 'llama3:latest', 
     'stat': 'Perfect: 100%\n16.1s avg', 'color': '#3498db'},
    {'x': 5.5, 'label': 'RAG Docs\n(16 queries)', 'model': 'llama3:latest', 
     'stat': 'Best: 81.2%\n28.8s avg', 'color': '#9b59b6'},
    {'x': 7.5, 'label': 'Robustness\n(9 queries)', 'model': 'qwen2.5:7b', 
     'stat': 'Edge cases: 88.9%\n9.4s avg', 'color': '#f39c12'}
]

for i, route in enumerate(routes):
    # Arrow from classification to route
    ax.annotate('', xy=(route['x']+0.75, 6.5), xytext=(5, 7.2), 
               arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
    
    # Route category box
    route_box = FancyBboxPatch((route['x'], 5.8), 1.5, 0.7, boxstyle="round,pad=0.05", 
                              edgecolor='black', facecolor='lightgray', linewidth=1.5)
    ax.add_patch(route_box)
    ax.text(route['x']+0.75, 6.15, route['label'], ha='center', va='center', 
           fontsize=9, fontweight='bold')
    
    # Model selection box
    model_box = FancyBboxPatch((route['x'], 4.5), 1.5, 1.0, boxstyle="round,pad=0.05", 
                              edgecolor='black', facecolor=route['color'], linewidth=2, alpha=0.7)
    ax.add_patch(model_box)
    ax.text(route['x']+0.75, 5.2, f"[{route['model']}]", ha='center', va='center', 
           fontsize=8, fontweight='bold', color='white')
    ax.text(route['x']+0.75, 4.8, route['stat'], ha='center', va='center', 
           fontsize=7, color='white', style='italic')
    
    # Arrow to confidence check
    ax.annotate('', xy=(5, 3.8), xytext=(route['x']+0.75, 4.5), 
               arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))

# Confidence check box
conf_box = FancyBboxPatch((3.5, 3.3), 3, 0.5, boxstyle="round,pad=0.1", 
                         edgecolor='red', facecolor='lightcoral', linewidth=2)
ax.add_patch(conf_box)
ax.text(5, 3.55, 'Confidence Check (< 0.7?)', ha='center', va='center', 
       fontsize=10, fontweight='bold')

# YES/NO branches
ax.annotate('', xy=(3.5, 2.5), xytext=(4, 3.3), 
           arrowprops=dict(arrowstyle='->', lw=2, color='red'))
ax.text(3.5, 2.9, 'YES', fontsize=9, fontweight='bold', color='red')

ax.annotate('', xy=(6.5, 2.5), xytext=(6, 3.3), 
           arrowprops=dict(arrowstyle='->', lw=2, color='green'))
ax.text(6.5, 2.9, 'NO', fontsize=9, fontweight='bold', color='green')

# Fallback box
fallback_box = FancyBboxPatch((2, 1.8), 2.5, 0.7, boxstyle="round,pad=0.05", 
                             edgecolor='red', facecolor='gold', linewidth=2)
ax.add_patch(fallback_box)
ax.text(3.25, 2.3, 'Fallback: llama3:latest', ha='center', va='center', 
       fontsize=10, fontweight='bold')
ax.text(3.25, 1.95, '(Quality Assurance)', ha='center', va='center', 
       fontsize=8, style='italic')

# Execute box
exec_box = FancyBboxPatch((5.5, 1.8), 2, 0.7, boxstyle="round,pad=0.05", 
                         edgecolor='green', facecolor='lightgreen', linewidth=2)
ax.add_patch(exec_box)
ax.text(6.5, 2.15, 'Execute Query', ha='center', va='center', 
       fontsize=10, fontweight='bold')

# Arrows to quality check
ax.annotate('', xy=(5, 1.0), xytext=(3.25, 1.8), 
           arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
ax.annotate('', xy=(5, 1.0), xytext=(6.5, 1.8), 
           arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

# Quality check
qual_box = FancyBboxPatch((3.5, 0.5), 3, 0.5, boxstyle="round,pad=0.05", 
                         edgecolor='blue', facecolor='lightblue', linewidth=2)
ax.add_patch(qual_box)
ax.text(5, 0.75, 'Quality Check (< 0.70?)', ha='center', va='center', 
       fontsize=10, fontweight='bold')

# Legend
legend_items = [
    mpatches.Patch(color='#2ecc71', label='qwen (Fast KPI)'),
    mpatches.Patch(color='#3498db', label='llama3 (High Quality)'),
    mpatches.Patch(color='#f39c12', label='qwen (Robustness)'),
    mpatches.Patch(color='gold', label='llama3 Fallback')
]
ax.legend(handles=legend_items, loc='lower right', frameon=True, shadow=True)

# Performance note
ax.text(5, 0.1, 'Expected: 90-92% satisfaction | 11-13s avg | $630/month', 
       ha='center', fontsize=9, style='italic', fontweight='bold',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

plt.tight_layout()
plt.savefig(output_dir / 'figure_4_4_adaptive_routing_flowchart.png', bbox_inches='tight')
plt.close()
print(f"   ✅ Saved: figure_4_4_adaptive_routing_flowchart.png")

# =============================================================================
# Summary
# =============================================================================
print("\n" + "="*80)
print("✅ ALL FIGURES GENERATED SUCCESSFULLY!")
print("="*80)
print(f"\n📁 Output location: {output_dir.absolute()}")
print("\n📊 Generated files:")
print("   1. figure_4_1_grouped_bar_satisfaction_routing.png")
print("   2. figure_4_2_comprehensive_comparison.png")
print("   3. figure_4_3_boxplot_response_time.png")
print("   4. figure_4_4_adaptive_routing_flowchart.png")
print("   5. figure_4_24_quality_components_stacked.png")
print("   6. figure_4_25_latency_waterfall.png")
print("   7. figure_4_26_statistical_significance.png")
print("\n💡 All figures are publication-quality (300 DPI) PNG files")
print("   Ready to insert into your FYP Chapter 4!")
print("\n" + "="*80)
