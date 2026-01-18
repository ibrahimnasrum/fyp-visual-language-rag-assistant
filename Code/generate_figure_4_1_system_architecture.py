import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, ArrowStyle

fig, ax = plt.subplots(figsize=(10, 5))
ax.axis('off')

# Draw main blocks
blocks = [
    ("User Query\n(Text/Image)", (0.05, 0.5)),
    ("Query Classifier", (0.22, 0.5)),
    ("Text Route", (0.39, 0.7)),
    ("Visual Route", (0.39, 0.3)),
    ("MiniLM\nEmbedding", (0.56, 0.7)),
    ("llava:latest\n(Vision-Language)", (0.56, 0.3)),
    ("FAISS\nRetriever", (0.73, 0.7)),
    ("OCR\nExtraction", (0.73, 0.3)),
    ("LLM\n(Llama3/Qwen/Phi3)", (0.87, 0.7)),
    ("Answer\nSynthesis", (0.87, 0.5)),
    ("Gradio UI\nDisplay", (0.87, 0.3)),
]

for label, (x, y) in blocks:
    ax.add_patch(FancyBboxPatch((x, y-0.08), 0.13, 0.16, boxstyle="round,pad=0.02", linewidth=1.5, edgecolor="#333", facecolor="#e0e7ef"))
    ax.text(x+0.065, y, label, ha='center', va='center', fontsize=10, weight='bold')

# Draw arrows
arrowprops = dict(arrowstyle=ArrowStyle("->", head_length=6, head_width=3), color="#333", lw=1.5)

def arrow(ax, start, end):
    ax.annotate('', xy=end, xytext=start, arrowprops=arrowprops)

# User Query to Classifier
arrow(ax, (0.18, 0.5), (0.22, 0.5))
# Classifier to Text/Visual
arrow(ax, (0.35, 0.5), (0.39, 0.7))
arrow(ax, (0.35, 0.5), (0.39, 0.3))
# Text Route
arrow(ax, (0.52, 0.7), (0.56, 0.7))
arrow(ax, (0.69, 0.7), (0.73, 0.7))
arrow(ax, (0.81, 0.7), (0.87, 0.7))
arrow(ax, (0.87, 0.7), (0.87, 0.55))
# Visual Route
arrow(ax, (0.52, 0.3), (0.56, 0.3))
arrow(ax, (0.69, 0.3), (0.73, 0.3))
arrow(ax, (0.81, 0.3), (0.87, 0.3))
arrow(ax, (0.87, 0.3), (0.87, 0.45))
# Answer Synthesis to UI
arrow(ax, (0.87, 0.5), (0.87, 0.38))

plt.title("Figure 4.1: System Architecture of the VL-RAG Assistant", fontsize=13, pad=18)
plt.tight_layout()
plt.savefig("../images/fyp_figures/figure_4_1_system_architecture.png", dpi=300)
plt.close()
