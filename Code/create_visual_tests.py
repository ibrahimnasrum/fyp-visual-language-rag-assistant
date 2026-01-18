"""
Phase 3: Create Visual Test Images

Generates test images from your retail sales data for visual model testing.

Usage:
    python create_visual_tests.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import numpy as np

# Output directory
TEST_IMAGES_DIR = Path(__file__).parent / 'test_images'
TEST_IMAGES_DIR.mkdir(exist_ok=True)

# Try to load data
DATA_FILE = Path(__file__).parent.parent / 'data' / 'MY_Retail_Sales_2024H1.csv'

print("="*80)
print("CREATING VISUAL TEST IMAGES - FYP Objective 1 Validation")
print("="*80)
print()

# Check if data file exists
if not DATA_FILE.exists():
    print(f"⚠️  Warning: {DATA_FILE} not found")
    print("   Creating synthetic test images instead...")
    
    # Create synthetic data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    sales = [450000, 520000, 480000, 610000, 580000, 650000]
    products = ['Laptop', 'Smartphone', 'Tablet', 'Monitor', 'Keyboard']
    product_sales = [250000, 380000, 150000, 120000, 95000]
    categories = ['Electronics', 'Accessories', 'Furniture', 'Software']
    category_sales = [650000, 280000, 190000, 125000]
    regions = ['North', 'South', 'East', 'West', 'Central']
    region_pct = [25, 22, 18, 20, 15]
    
else:
    print(f"✅ Loading data from: {DATA_FILE.name}")
    df = pd.read_csv(DATA_FILE)
    
    # Extract real data
    months = df['Month'].unique()[:6]
    sales = [df[df['Month'] == m]['Total_Sales'].sum() for m in months]
    
    top_products = df.groupby('Product')['Total_Sales'].sum().nlargest(5)
    products = top_products.index.tolist()
    product_sales = top_products.values.tolist()
    
    # Use synthetic for missing fields
    categories = ['Electronics', 'Accessories', 'Furniture', 'Software']
    category_sales = [650000, 280000, 190000, 125000]
    regions = ['North', 'South', 'East', 'West', 'Central']
    region_pct = [25, 22, 18, 20, 15]

print()

# V01: Sales Trend Line Chart
print("📊 Creating V01: Sales Trend Chart...")
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(months, sales, marker='o', linewidth=3, markersize=10, color='#2ca02c')
ax.set_title('Monthly Sales Trend (Jan-Jun 2024)', size=16, weight='bold')
ax.set_xlabel('Month', size=12, weight='bold')
ax.set_ylabel('Sales (RM)', size=12, weight='bold')
ax.grid(True, alpha=0.3)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'RM {x/1000:.0f}K'))
for i, (m, s) in enumerate(zip(months, sales)):
    ax.text(i, s + 15000, f'RM {s/1000:.0f}K', ha='center', va='bottom', size=10)
plt.tight_layout()
plt.savefig(TEST_IMAGES_DIR / 'V01_sales_trend.png', dpi=150)
plt.close()
print(f"   ✅ Saved: V01_sales_trend.png")

# V02: Product Table
print("📊 Creating V02: Product Sales Table...")
fig, ax = plt.subplots(figsize=(9, 4))
ax.axis('tight')
ax.axis('off')

table_data = [[f'{i+1}. {prod}', f'RM {sales:,.2f}'] 
              for i, (prod, sales) in enumerate(zip(products, product_sales))]

table = ax.table(cellText=table_data, 
                colLabels=['Product', 'Total Sales (H1 2024)'],
                loc='center', cellLoc='left',
                colWidths=[0.6, 0.4])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

# Style header
for i in range(2):
    table[(0, i)].set_facecolor('#4CAF50')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Alternate row colors
for i in range(1, len(products) + 1):
    color = '#f0f0f0' if i % 2 == 0 else 'white'
    for j in range(2):
        table[(i, j)].set_facecolor(color)

ax.set_title('Top 5 Products by Sales Value', size=14, weight='bold', pad=20)
plt.tight_layout()
plt.savefig(TEST_IMAGES_DIR / 'V02_product_table.png', dpi=150)
plt.close()
print(f"   ✅ Saved: V02_product_table.png")

# V03: Category Bar Chart
print("📊 Creating V03: Category Bar Chart...")
fig, ax = plt.subplots(figsize=(10, 6))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
bars = ax.bar(categories, category_sales, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
ax.set_title('Sales by Product Category (H1 2024)', size=16, weight='bold')
ax.set_xlabel('Category', size=12, weight='bold')
ax.set_ylabel('Total Sales (RM)', size=12, weight='bold')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'RM {x/1000:.0f}K'))
ax.grid(axis='y', alpha=0.3)

for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 10000,
           f'RM {height/1000:.0f}K', ha='center', va='bottom', size=11, weight='bold')

plt.tight_layout()
plt.savefig(TEST_IMAGES_DIR / 'V03_category_bar.png', dpi=150)
plt.close()
print(f"   ✅ Saved: V03_category_bar.png")

# V04: Region Pie Chart
print("📊 Creating V04: Regional Sales Pie Chart...")
fig, ax = plt.subplots(figsize=(10, 8))
colors_pie = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
wedges, texts, autotexts = ax.pie(region_pct, labels=regions, autopct='%1.1f%%',
                                    colors=colors_pie, startangle=90,
                                    textprops={'size': 12, 'weight': 'bold'})
ax.set_title('Sales Distribution by Region (H1 2024)', size=16, weight='bold', pad=20)

# Make percentage text more visible
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontsize(11)
    autotext.set_weight('bold')

plt.tight_layout()
plt.savefig(TEST_IMAGES_DIR / 'V04_region_pie.png', dpi=150)
plt.close()
print(f"   ✅ Saved: V04_region_pie.png")

# V05: Multilingual Document (Text + Chart)
print("📊 Creating V05: Multilingual Document...")
fig = plt.figure(figsize=(12, 8))

# Title
fig.text(0.5, 0.95, 'Laporan Jualan / Sales Report / 销售报告', 
         ha='center', va='top', size=18, weight='bold')

# Multilingual content
content = """
ENGLISH: Total sales for Q1-Q2 2024 reached RM 3.2 million, 
representing a 15% increase year-over-year.

中文: 2024年上半年总销售额达到320万令吉，
同比增长15%。

BAHASA MALAYSIA: Jumlah jualan bagi separuh pertama 2024 
mencecah RM 3.2 juta, meningkat 15% berbanding tahun sebelumnya.

KEY HIGHLIGHTS:
• Electronics category leads with 52% market share
• Northern region shows strongest growth (+22%)
• Top product: Smartphones (RM 380K revenue)
"""

fig.text(0.1, 0.7, content, ha='left', va='top', size=11, 
         family='monospace', wrap=True)

# Small embedded chart
ax = fig.add_subplot(2, 2, 3)
ax.bar(['Q1', 'Q2'], [1500000, 1700000], color=['#1f77b4', '#ff7f0e'])
ax.set_title('Quarterly Comparison', size=10, weight='bold')
ax.set_ylabel('Sales (RM)', size=9)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))

# Small pie chart
ax2 = fig.add_subplot(2, 2, 4)
ax2.pie([52, 22, 15, 11], labels=['Electronics', 'Accessories', 'Furniture', 'Software'],
        autopct='%1.0f%%', textprops={'size': 8})
ax2.set_title('Category Split', size=10, weight='bold')

plt.tight_layout()
plt.savefig(TEST_IMAGES_DIR / 'V05_multilingual.png', dpi=150)
plt.close()
print(f"   ✅ Saved: V05_multilingual.png")

print()
print("="*80)
print(f"✅ ALL 5 VISUAL TEST IMAGES CREATED")
print("="*80)
print(f"\n📁 Location: {TEST_IMAGES_DIR}")
print("\nGenerated images:")
for img in sorted(TEST_IMAGES_DIR.glob('V*.png')):
    print(f"   - {img.name}")

print("\n📝 Next step: Run visual model tests")
print("   python test_visual_models.py")
print()
