# CEO Question Research - Hypothesis Tree
## Generated: 2026-01-15

## Research Goal
Identify strategic CEO-level questions that:
1. Can be answered by the system (Sales/HR/Docs data 2024-01 to 2024-06)
2. Represent real executive information needs
3. Go beyond basic KPI queries to strategic analysis

---

## System Capabilities Analysis

### Available Data
**Sales Data (MY_Retail_Sales_2024H1.csv):**
- Dimensions: Date, State, Branch, Product, Employee, Channel, PaymentMethod
- Metrics: Quantity, Unit Price, Total Sale
- Time Range: 2024-01 to 2024-06 (6 months)
- Entities: ~12 branches across Malaysia (Selangor, KL, Penang, Johor, etc.)
- Products: Burgers (Beef, Chicken, Cheese, Spicy), Fries, Drinks, etc.
- Channels: Dine-in, Takeout, Delivery

**HR Data (MY_Retail_HR_Employees.csv):**
- Dimensions: State, Branch, Department, JobRole, AgeGroup
- Metrics: MonthlyIncome, YearsAtCompany, Age
- Flags: OverTime, Attrition
- Departments: Kitchen, Service, Management, etc.

**Document Sources:**
- Company_Profile_MY.txt
- FAQ_MY.txt
- HR_Policy_MY.txt
- Sales_SOP_MY.txt
- Ops_Incident_Report_MY.txt
- Performance_Drivers_Analysis.txt
- State_Operations_KL.txt / Penang.txt / Selangor.txt

### AI Prompt Focus
The system is designed to:
- Provide **executive-level analysis** with business impact
- Identify **risks** (declining performance, high attrition)
- Detect **opportunities** (growth areas, top performers)
- Give **actionable recommendations**

---

## Hypothesis Tree: What CEOs Actually Ask

### H1: Growth & Performance Trends (Confidence: HIGH)
**CEOs need to understand trajectory, not just snapshots**

**Sub-hypotheses:**
- H1.1: Month-over-month growth analysis (revenue, units, avg transaction)
- H1.2: Quarter-over-quarter comparisons (Q1 2024 vs Q2 2024)
- H1.3: Trend identification (improving/declining/stable)
- H1.4: Growth drivers (which products/states/channels driving growth?)

**Testable Questions:**
- "Show me monthly revenue growth from January to June 2024"
- "Which month had the highest growth rate?"
- "Are we growing or declining overall?"
- "What drove our revenue change from Q1 to Q2?"
- "Show me sales velocity trends"

**System Can Answer:** ✅ YES - Has 6 months of daily sales data

---

### H2: Profitability & Unit Economics (Confidence: MEDIUM)
**CEOs care about margins, not just top-line revenue**

**Sub-hypotheses:**
- H2.1: Average transaction value trends
- H2.2: Product pricing effectiveness
- H2.3: Channel profitability comparison
- H2.4: High-value vs low-value customer behavior

**Testable Questions:**
- "What's our average transaction value by channel?"
- "Which products have the highest unit price?"
- "Compare average order value: dine-in vs delivery"
- "Show me revenue per transaction trend"
- "Which channel generates most revenue per order?"

**System Can Answer:** ✅ YES - Has Unit Price, Quantity, Total Sale, Channel

---

### H3: Efficiency & Productivity (Confidence: HIGH)
**CEOs want to maximize output per resource**

**Sub-hypotheses:**
- H3.1: Sales per employee (productivity metric)
- H3.2: Branch productivity comparison
- H3.3: Staff utilization (overtime patterns)
- H3.4: Revenue per branch efficiency

**Testable Questions:**
- "Which employee is our top revenue generator?"
- "What's the average sales per employee?"
- "Which branch is most productive (revenue per staff)?"
- "Show me employee performance ranking"
- "How many staff are working overtime by department?"

**System Can Answer:** ✅ YES - Can join Sales (Employee) with HR (Employee, OverTime)

---

### H4: Risk Identification (Confidence: HIGH)
**CEOs need early warning signals**

**Sub-hypotheses:**
- H4.1: Declining performance detection (products/branches/states)
- H4.2: Attrition hotspots (high turnover departments/branches)
- H4.3: Underperforming assets (bottom performers)
- H4.4: Concentration risk (over-reliance on few products/channels)

**Testable Questions:**
- "Which products are declining in sales?"
- "Show me bottom 3 branches by revenue"
- "Which department has highest attrition?"
- "What percentage of revenue comes from top 3 products?" (concentration)
- "Are we losing staff in critical roles?"

**System Can Answer:** ✅ YES - Has comparative data + attrition flags

---

### H5: Market Mix & Portfolio (Confidence: HIGH)
**CEOs want to understand business composition**

**Sub-hypotheses:**
- H5.1: Channel mix analysis (% of sales by channel)
- H5.2: Product portfolio balance (revenue distribution)
- H5.3: Geographic concentration (state-level breakdown %)
- H5.4: Payment method preferences

**Testable Questions:**
- "What percentage of sales come from delivery?"
- "Show me product mix: which products contribute most?"
- "What's our channel distribution?"
- "Which state contributes most to overall revenue?"
- "What's our payment method breakdown?"

**System Can Answer:** ✅ YES - Has all dimensions for percentage calculations

---

### H6: Operational Patterns (Confidence: MEDIUM)
**CEOs want to understand business rhythms**

**Sub-hypotheses:**
- H6.1: Peak vs non-peak periods
- H6.2: Seasonal patterns (though only 6 months available)
- H6.3: Product demand patterns
- H6.4: Channel preference shifts

**Testable Questions:**
- "Which month is our peak sales period?"
- "When did we have our best week?"
- "Are weekends stronger than weekdays?" (need Date analysis)
- "Show me monthly sales pattern"
- "Which products sell better in which months?"

**System Can Answer:** ⚠️ PARTIAL - Has monthly data, limited seasonal insight

---

### H7: Team Performance & HR Analytics (Confidence: HIGH)
**CEOs need workforce insights**

**Sub-hypotheses:**
- H7.1: Compensation benchmarking (by role/department)
- H7.2: Tenure analysis (employee retention patterns)
- H7.3: Age diversity (workforce demographics)
- H7.4: Department-level headcount efficiency

**Testable Questions:**
- "What's the average salary by department?"
- "Show me salary range for kitchen staff"
- "How many employees have been here 5+ years?"
- "Which age group has most employees?"
- "What's average tenure by department?"

**System Can Answer:** ✅ YES - Has MonthlyIncome, YearsAtCompany, Age, Department

---

### H8: Strategic Planning Questions (Confidence: MEDIUM-HIGH)
**CEOs ask "what if" and "should we" questions**

**Sub-hypotheses:**
- H8.1: Resource allocation (should we invest in X state/product?)
- H8.2: Expansion opportunities (which states/products to focus?)
- H8.3: Cost optimization (high-cost areas)
- H8.4: Strategic pivots (channel strategy)

**Testable Questions:**
- "Which state has most growth potential?" (highest growth rate)
- "Should we focus more on delivery or dine-in?" (channel performance)
- "Which product category should we expand?"
- "Where should we open next branch?" (underserved high-growth states)
- "Which branches need improvement?" (lowest performers)

**System Can Answer:** ✅ YES - Can provide data for decision support

---

### H9: Benchmark & Comparison Questions (Confidence: HIGH)
**CEOs want context: how do we compare?**

**Sub-hypotheses:**
- H9.1: Internal benchmarking (branch vs branch, state vs state)
- H9.2: Period comparisons (this month vs last month)
- H9.3: Top vs bottom performer gaps
- H9.4: Above/below average analysis

**Testable Questions:**
- "Which branches outperform the average?"
- "Compare Selangor performance vs Penang"
- "Show me gap between best and worst branch"
- "Which products exceed average sales?"
- "Compare June 2024 vs May 2024 across all metrics"

**System Can Answer:** ✅ YES - Has comparative capabilities built-in

---

### H10: Policy & Compliance Questions (Confidence: MEDIUM)
**CEOs need to verify operational compliance**

**Sub-hypotheses:**
- H10.1: Policy awareness (do procedures exist?)
- H10.2: Process clarity (what are the steps?)
- H10.3: Escalation paths (who handles issues?)
- H10.4: Performance management procedures

**Testable Questions:**
- "What's our process for handling underperforming staff?"
- "How do we evaluate employee performance?"
- "What's the escalation process for operational issues?"
- "What are our customer complaint handling procedures?"
- "What's our policy on overtime?"

**System Can Answer:** ✅ YES - Documents contain policies/SOPs

---

## Gap Analysis: Current Test Coverage vs CEO Needs

### Well-Covered Areas ✅
- Basic totals (sales, headcount)
- Simple rankings (top products, top branches)
- State/product breakdowns
- Policy lookups

### Missing CEO-Level Questions ❌
1. **Growth Analysis**: No trend/growth rate questions
2. **Efficiency Metrics**: No productivity (sales per employee) questions
3. **Risk Detection**: No declining trend or attrition questions
4. **Portfolio Mix**: No percentage/composition questions
5. **Profitability**: No unit economics or avg transaction value questions
6. **Strategic Benchmarks**: No "above average" or gap analysis questions
7. **Workforce Analytics**: No salary analysis or tenure questions
8. **Actionable Insights**: No "should we" or recommendation questions

---

## Confidence Assessment

**HIGH Confidence (Can definitely answer):**
- Growth trends (H1) ✅
- Efficiency metrics (H3) ✅
- Risk identification (H4) ✅
- Portfolio mix (H5) ✅
- HR analytics (H7) ✅
- Benchmarking (H9) ✅

**MEDIUM Confidence (Partial answers possible):**
- Profitability (H2) - has data but may need calculation guidance
- Operational patterns (H6) - limited to 6 months
- Strategic planning (H8) - can provide data, AI must make recommendations
- Policy questions (H10) - depends on document completeness

**LOW Confidence (May struggle):**
- External comparisons (competitors) - NO DATA
- Predictive questions (future forecasts) - NO FORECASTING MODEL
- Cost analysis beyond salaries - NO DETAILED COST DATA

---

## Next Steps

1. **Design Question Set**: Create 25-30 strategic CEO questions based on HIGH confidence hypotheses
2. **Validate Answerability**: Test a sample against actual data structure
3. **Add to Test Suite**: Integrate into automated_tester_csv.py
4. **Run Evaluation**: Assess how well AI handles strategic queries vs simple lookups
