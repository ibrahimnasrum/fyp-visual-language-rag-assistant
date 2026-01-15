# Strategic CEO Questions - Final Question Set
## Generated: 2026-01-15
## Based on: CEO_QUESTION_RESEARCH.md hypothesis tree

---

## Category 1: GROWTH & PERFORMANCE TRENDS (6 questions)

### C1.1 - Revenue Growth Analysis
**Q:** "Show me monthly revenue growth from January to June 2024"
**Expected Route:** sales_kpi
**Expected Answer:** Month-over-month revenue with growth rates
**Business Value:** Understand trajectory - are we growing or declining?

### C1.2 - Peak Performance Identification
**Q:** "Which month had the highest sales in 2024?"
**Expected Route:** sales_kpi
**Expected Answer:** Peak month with comparative context
**Business Value:** Identify success patterns to replicate

### C1.3 - Growth Driver Analysis
**Q:** "What drove our revenue change from May to June?"
**Expected Route:** sales_kpi (complex - requires breakdown)
**Expected Answer:** Product/state/channel contributors to growth
**Business Value:** Understand what's working

### C1.4 - Quarter Comparison
**Q:** "Compare Q1 vs Q2 2024 total sales"
**Expected Route:** sales_kpi
**Expected Answer:** Q1 (Jan-Mar) vs Q2 (Apr-Jun) revenue
**Business Value:** Strategic period comparison

### C1.5 - Velocity Trends
**Q:** "Are we growing or declining overall from Jan to June?"
**Expected Route:** sales_kpi
**Expected Answer:** Overall trend direction + magnitude
**Business Value:** Executive-level status check

### C1.6 - Acceleration Detection
**Q:** "Which product is growing fastest in recent months?"
**Expected Route:** sales_kpi
**Expected Answer:** Product with highest growth rate
**Business Value:** Identify momentum opportunities

---

## Category 2: EFFICIENCY & PRODUCTIVITY (5 questions)

### C2.1 - Employee Productivity
**Q:** "What's the average sales per employee?"
**Expected Route:** sales_kpi or hr_kpi (complex - may need clarification)
**Expected Answer:** Total sales / employee count or per-employee breakdown
**Business Value:** Workforce productivity metric

### C2.2 - Top Performer Identification
**Q:** "Who is our top performing employee by revenue?"
**Expected Route:** sales_kpi
**Expected Answer:** Employee name/ID + revenue generated
**Business Value:** Recognize and reward high performers

### C2.3 - Branch Productivity
**Q:** "Which branch generates most revenue per staff member?"
**Expected Route:** sales_kpi (complex - requires joining Sales + HR)
**Expected Answer:** Branch with highest revenue/headcount ratio
**Business Value:** Operational efficiency benchmark

### C2.4 - Utilization Patterns
**Q:** "How many employees work overtime by department?"
**Expected Route:** hr_kpi
**Expected Answer:** Overtime count per department
**Business Value:** Identify overworked teams

### C2.5 - Staff Allocation
**Q:** "Which branch has the most employees?"
**Expected Route:** hr_kpi
**Expected Answer:** Branch with highest headcount
**Business Value:** Resource distribution check

---

## Category 3: RISK IDENTIFICATION (5 questions)

### C3.1 - Declining Product Detection
**Q:** "Which products are declining in sales from Q1 to Q2?"
**Expected Route:** sales_kpi
**Expected Answer:** Products with negative growth rates
**Business Value:** Early warning for product issues

### C3.2 - Underperformers
**Q:** "Show me bottom 3 branches by revenue"
**Expected Route:** sales_kpi
**Expected Answer:** Lowest 3 branches with revenue
**Business Value:** Identify improvement opportunities

### C3.3 - Attrition Hotspots
**Q:** "Which department has the highest attrition rate?"
**Expected Route:** hr_kpi
**Expected Answer:** Department with most attrition flags
**Business Value:** HR retention risk

### C3.4 - Weak States
**Q:** "Which state has the lowest sales performance?"
**Expected Route:** sales_kpi
**Expected Answer:** State with minimum revenue
**Business Value:** Geographic risk identification

### C3.5 - Critical Role Turnover
**Q:** "How many managers have left the company?"
**Expected Route:** hr_kpi
**Expected Answer:** Count of managers with Attrition=Yes
**Business Value:** Leadership stability check

---

## Category 4: PORTFOLIO MIX & COMPOSITION (5 questions)

### C4.1 - Channel Distribution
**Q:** "What percentage of our sales come from delivery?"
**Expected Route:** sales_kpi
**Expected Answer:** Delivery % of total revenue
**Business Value:** Channel strategy validation

### C4.2 - Product Concentration
**Q:** "What percentage of revenue comes from our top 3 products?"
**Expected Route:** sales_kpi (complex - requires top-N + percentage)
**Expected Answer:** Concentration risk metric (e.g., 65%)
**Business Value:** Portfolio diversification risk

### C4.3 - Geographic Mix
**Q:** "Show me revenue breakdown by state as percentages"
**Expected Route:** sales_kpi
**Expected Answer:** Each state's % of total revenue
**Business Value:** Market distribution understanding

### C4.4 - Payment Preferences
**Q:** "What's our payment method distribution?"
**Expected Route:** sales_kpi
**Expected Answer:** % breakdown of Cash/Card/E-wallet
**Business Value:** Payment infrastructure planning

### C4.5 - Channel Shift Detection
**Q:** "Is delivery growing faster than dine-in?"
**Expected Route:** sales_kpi (complex - requires trend comparison)
**Expected Answer:** Comparative growth rates by channel
**Business Value:** Strategic channel focus

---

## Category 5: PROFITABILITY & UNIT ECONOMICS (4 questions)

### C5.1 - Transaction Value
**Q:** "What's our average transaction value by channel?"
**Expected Route:** sales_kpi
**Expected Answer:** Avg order value: Dine-in vs Takeout vs Delivery
**Business Value:** Revenue quality metric

### C5.2 - Premium Products
**Q:** "Which products have the highest unit price?"
**Expected Route:** sales_kpi
**Expected Answer:** Top 3 products by price
**Business Value:** Premium positioning opportunities

### C5.3 - Value Driver
**Q:** "Which channel generates the highest revenue per transaction?"
**Expected Route:** sales_kpi
**Expected Answer:** Channel with max avg order value
**Business Value:** Focus high-value channels

### C5.4 - Price Points
**Q:** "Show me average unit price trends from Jan to June"
**Expected Route:** sales_kpi
**Expected Answer:** Monthly avg price (pricing strategy check)
**Business Value:** Pricing power analysis

---

## Category 6: HR ANALYTICS & WORKFORCE (5 questions)

### C6.1 - Compensation Benchmarking
**Q:** "What's the average salary by department?"
**Expected Route:** hr_kpi
**Expected Answer:** Mean MonthlyIncome per department
**Business Value:** Pay equity and budget planning

### C6.2 - Salary Range
**Q:** "Show me salary range for kitchen staff"
**Expected Route:** hr_kpi
**Expected Answer:** Min/Max MonthlyIncome for Kitchen dept
**Business Value:** Compensation structure review

### C6.3 - Retention Analysis
**Q:** "How many employees have been here for 5+ years?"
**Expected Route:** hr_kpi
**Expected Answer:** Count of employees with YearsAtCompany >= 5
**Business Value:** Loyalty and retention metric

### C6.4 - Workforce Demographics
**Q:** "What's the age distribution of our workforce?"
**Expected Route:** hr_kpi
**Expected Answer:** Breakdown by AgeGroup
**Business Value:** Succession planning insights

### C6.5 - Tenure by Role
**Q:** "What's the average tenure for managers?"
**Expected Route:** hr_kpi
**Expected Answer:** Avg YearsAtCompany for JobRole=Manager
**Business Value:** Leadership stability

---

## Category 7: BENCHMARKING & COMPARISONS (4 questions)

### C7.1 - Above-Average Performers
**Q:** "Which branches perform above the average?"
**Expected Route:** sales_kpi (complex - requires avg calculation)
**Expected Answer:** Branches with revenue > overall average
**Business Value:** Success model identification

### C7.2 - State Comparison
**Q:** "Compare Selangor vs Penang total sales"
**Expected Route:** sales_kpi
**Expected Answer:** Side-by-side state revenue comparison
**Business Value:** Regional strategy

### C7.3 - Performance Gap
**Q:** "What's the revenue gap between best and worst branch?"
**Expected Route:** sales_kpi
**Expected Answer:** Max branch revenue - Min branch revenue
**Business Value:** Performance variance analysis

### C7.4 - Month-over-Month All Metrics
**Q:** "Compare all key metrics: June vs May 2024"
**Expected Route:** sales_kpi
**Expected Answer:** Revenue, units, avg price, top products side-by-side
**Business Value:** Comprehensive period comparison

---

## Category 8: STRATEGIC PLANNING & DECISIONS (3 questions)

### C8.1 - Growth Opportunity
**Q:** "Which state shows the highest growth rate?"
**Expected Route:** sales_kpi
**Expected Answer:** State with best month-over-month growth
**Business Value:** Expansion prioritization

### C8.2 - Channel Strategy
**Q:** "Should we focus more on delivery or dine-in based on performance?"
**Expected Route:** sales_kpi (requires interpretation)
**Expected Answer:** Channel comparison + recommendation
**Business Value:** Strategic resource allocation

### C8.3 - Product Focus
**Q:** "Which product category should we expand?"
**Expected Route:** sales_kpi
**Expected Answer:** Best-performing product category
**Business Value:** Product development priorities

---

## Summary Statistics

**Total Questions:** 42 strategic CEO-level questions
**By Category:**
- Growth & Trends: 6
- Efficiency: 5
- Risk: 5
- Portfolio Mix: 5
- Profitability: 4
- HR Analytics: 5
- Benchmarking: 4
- Strategic Planning: 3
- Policy (existing): 5 (already in test suite)

**Complexity Distribution:**
- Simple (single metric): 18 questions
- Medium (requires calculation): 15 questions
- Complex (multi-step analysis): 9 questions

**Expected Routes:**
- sales_kpi: 30 questions
- hr_kpi: 10 questions
- rag_docs: 2 questions (policy-related)

**Business Value Themes:**
- Performance monitoring: 15 questions
- Risk management: 8 questions
- Strategic decisions: 10 questions
- Operational efficiency: 9 questions

---

## Implementation Plan

1. **Add to automated_tester_csv.py** as "CEO_STRATEGIC" category
2. **Test subset first** (10 questions) to validate routing
3. **Analyze failure patterns** - which complex questions fail?
4. **Refine based on results** - adjust question wording if needed
5. **Full test** - run all 42 questions
6. **Document insights** - which CEO questions work best vs struggle?

---

## Expected Challenges

**Complex Calculations:**
- "Revenue per employee" (requires joining Sales + HR)
- "Percentage of sales" (requires total + subset calculation)
- "Growth rates" (requires period comparison math)

**Multi-Step Logic:**
- "Which products are declining" (requires trend analysis)
- "Should we focus on X vs Y" (requires recommendation logic)
- "Above average performers" (requires average + comparison)

**Interpretation Needed:**
- Strategic recommendations ("should we expand X?")
- Root cause analysis ("what drove the change?")
- Forward-looking insights ("growth potential")

**Mitigation:**
The AI system prompt has:
- Chain-of-thought reasoning structure
- Computational support (can calculate)
- Business context awareness
- Recommendation capability

These questions will stress-test the AI's strategic analysis abilities beyond simple lookups.
