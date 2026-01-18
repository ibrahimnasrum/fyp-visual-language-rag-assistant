import matplotlib.pyplot as plt
import seaborn as sns

# Data for Figure 4.27
categories = [
    "Sales Tables",
    "HR Charts",
    "Sales Charts",
    "Income/Dept"
]
success_counts = [5, 5, 4, 1]
total_counts = [5, 5, 4, 1]
success_rates = [s/t*100 for s, t in zip(success_counts, total_counts)]

fig, ax = plt.subplots(figsize=(7, 3.5))
sns.set_theme(style="whitegrid", font_scale=1.1)

bars = ax.barh(categories, success_rates, color="#4CAF50", edgecolor="black")

# Annotate bars
for bar, rate, count, total in zip(bars, success_rates, success_counts, total_counts):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f"{int(rate)}% ({count}/{total})", va='center', fontsize=11)

ax.set_xlim(0, 110)
ax.set_xlabel("OCR Success Rate (%)", fontsize=12)
ax.set_title("Figure 4.27: OCR Extraction Success Rate by Image Type", fontsize=13, pad=12)
plt.tight_layout()

# Save figure
plt.savefig("../images/fyp_figures/figure_4_27_ocr_success_rate.png", dpi=300)
plt.close()
