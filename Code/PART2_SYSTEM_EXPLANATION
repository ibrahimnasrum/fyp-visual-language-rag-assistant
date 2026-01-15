# 4. Ground Truth - Where Answers Come From

## 4.1 Overview: Three Types of Ground Truth

Your system uses **three distinct ground truth sources** depending on question type:

| Question Type | Ground Truth Source | Verification Method | Hallucination Risk |
|---------------|---------------------|---------------------|-------------------|
| **Sales KPI** | `data/sales.csv` (29,635 rows) | Exact number match | ❌ **ZERO** (deterministic) |
| **HR KPI** | `data/hr.csv` (820 rows) | Exact number match | ❌ **ZERO** (deterministic) |
| **Policy/RAG** | `docs/` folder (31 files) | Source citation check | ⚠️ **MEDIUM** (LLM-based) |

---

## 4.2 Sales Ground Truth - CSV Data Structure

### **File:** `data/sales.csv`

**Size:** 29,635 transactions (January 2024 - July 2024)

**Schema:**
```
Date,State,ProductName,Quantity,UnitPrice,TotalPrice,Channel,PaymentMethod
2024-06-01,Selangor,Cheese Burger,2,15.90,31.80,Dine-in,Cash
2024-06-01,Kuala Lumpur,Fries,3,5.50,16.50,Delivery,Card
2024-06-02,Penang,Beef Burger,1,18.90,18.90,Dine-in,E-wallet
2024-06-02,Johor,Sundae,2,8.00,16.00,Takeaway,Cash
...
```

**Column Details:**

| Column | Type | Description | Example Values |
|--------|------|-------------|----------------|
| `Date` | DATE | Transaction date | 2024-01-01 to 2024-07-31 |
| `State` | STRING | Branch location | Selangor, KL, Penang, Johor, Perak, Kedah, Melaka |
| `ProductName` | STRING | Product sold | Cheese Burger, Fries, Nuggets, Sundae, Beef Burger |
| `Quantity` | INTEGER | Units sold | 1-5 |
| `UnitPrice` | DECIMAL | Price per unit | RM 5.50 - RM 18.90 |
| `TotalPrice` | DECIMAL | Revenue (Qty × Price) | RM 5.50 - RM 94.50 |
| `Channel` | STRING | Sales channel | Dine-in, Delivery, Takeaway |
| `PaymentMethod` | STRING | Payment type | Cash, Card, E-wallet |

### **4.2.1 Example Ground Truth Calculation**

**Question:** "sales bulan 2024-06 berapa?"

**Ground Truth Calculation (SQL equivalent):**
```sql
SELECT SUM(TotalPrice) as TotalRevenue,
       SUM(Quantity) as TotalQuantity,
       COUNT(*) as NumTransactions
FROM sales
WHERE YEAR(Date) = 2024 AND MONTH(Date) = 6;
```

**Pandas Implementation:**
```python
# Filter to June 2024
df_june = df_sales[df_sales['YearMonth'] == pd.Period('2024-06', freq='M')]

# Calculate ground truth
ground_truth_revenue = df_june['TotalPrice'].sum()  # e.g., RM 456,789.12
ground_truth_qty = df_june['Quantity'].sum()        # e.g., 8,456 units
ground_truth_trans = len(df_june)                   # e.g., 4,123 transactions
```

**System Answer (must match exactly):**
```
Total sales for 2024-06: RM 456,789.12
Total quantity sold: 8,456 units
Number of transactions: 4,123
```

**Test Verification:**
```python
# automated_tester_csv.py verification logic
expected = 456789.12
actual = extract_number_from_answer(system_answer)  # Parse "RM 456,789.12" → 456789.12

tolerance = 0.01  # Allow RM 0.01 rounding difference
if abs(actual - expected) <= tolerance:
    result = "PASS"
else:
    result = "ANSWER_FAIL"  # Numbers don't match!
```

### **4.2.2 Complex Ground Truth Example: Top 3 Products**

**Question:** "top 3 product bulan 2024-06"

**Ground Truth Calculation:**
```python
# Group by product, sum revenue, get top 3
top3_ground_truth = (df_june.groupby('ProductName')['TotalPrice']
                     .sum()
                     .nlargest(3)
                     .to_dict())

# Result (example):
# {'Cheese Burger': 125678.90,
#  'Beef Burger': 98234.50,
#  'Fries': 76543.20}
```

**System Answer (must match ranking & numbers):**
```
| Rank | Product       | Revenue       |
|------|---------------|---------------|
| 1    | Cheese Burger | RM 125,678.90 |
| 2    | Beef Burger   | RM 98,234.50  |
| 3    | Fries         | RM 76,543.20  |
```

**Test Verification:**
```python
# Check ranking order
expected_ranking = ['Cheese Burger', 'Beef Burger', 'Fries']
actual_ranking = extract_ranking_from_answer(system_answer)

# Check revenue numbers
for i, product in enumerate(expected_ranking):
    expected_revenue = top3_ground_truth[product]
    actual_revenue = extract_product_revenue(system_answer, product)
    
    if abs(actual_revenue - expected_revenue) > 0.01:
        return "ANSWER_FAIL"  # Revenue mismatch
    
    if actual_ranking[i] != expected_ranking[i]:
        return "ANSWER_FAIL"  # Ranking wrong

return "PASS"  # All checks passed
```

---

## 4.3 HR Ground Truth - CSV Data Structure

### **File:** `data/hr.csv`

**Size:** 820 employees (current snapshot)

**Schema:**
```
EmpID,Age,Gender,JobRole,MonthlyIncome,YearsAtCompany,Attrition,State,Department
E001,34,Male,Sales Executive,4500,5,No,Selangor,Sales
E002,28,Female,Kitchen Staff,3200,2,Yes,Kuala Lumpur,Operations
E003,42,Male,Branch Manager,7800,10,No,Penang,Management
E004,31,Female,Cashier,3500,3,No,Johor,Operations
...
```

**Column Details:**

| Column | Type | Description | Example Values |
|--------|------|-------------|----------------|
| `EmpID` | STRING | Employee ID | E001, E002, ... E820 |
| `Age` | INTEGER | Employee age | 22-60 |
| `Gender` | STRING | Gender | Male, Female |
| `JobRole` | STRING | Position | Sales Executive, Kitchen Staff, Manager, Cashier |
| `MonthlyIncome` | DECIMAL | Salary (RM) | RM 2,800 - RM 12,000 |
| `YearsAtCompany` | INTEGER | Tenure (years) | 0-25 |
| `Attrition` | STRING | Has left company? | Yes, No |
| `State` | STRING | Work location | Selangor, KL, Penang, Johor, Perak, Kedah, Melaka |
| `Department` | STRING | Department | Sales, Operations, Management, HR, Finance |

### **4.3.1 Example Ground Truth Calculation: Headcount**

**Question:** "headcount ikut state"

**Ground Truth Calculation:**
```python
# Group by state and count
ground_truth_headcount = df_hr.groupby('State').size().to_dict()

# Result (example):
# {'Selangor': 234,
#  'Kuala Lumpur': 187,
#  'Penang': 156,
#  'Johor': 123,
#  'Perak': 78,
#  'Kedah': 42,
#  'Melaka': 0}  # No employees in Melaka
```

**System Answer (must match exactly):**
```
| State         | Headcount |
|---------------|-----------|
| Selangor      | 234       |
| Kuala Lumpur  | 187       |
| Penang        | 156       |
| Johor         | 123       |
| Perak         | 78        |
| Kedah         | 42        |

Total: 820 employees
```

**Test Verification:**
```python
# Check each state count
for state, expected_count in ground_truth_headcount.items():
    actual_count = extract_state_headcount(system_answer, state)
    
    if actual_count != expected_count:
        return "ANSWER_FAIL"  # Count mismatch

# Check total
expected_total = sum(ground_truth_headcount.values())
actual_total = extract_total_from_answer(system_answer)

if actual_total != expected_total:
    return "ANSWER_FAIL"  # Total wrong

return "PASS"
```

### **4.3.2 Complex Ground Truth Example: Attrition Rate**

**Question:** "which age group has highest attrition?"

**Ground Truth Calculation:**
```python
# Create age groups
df_hr['AgeGroup'] = pd.cut(df_hr['Age'], 
                            bins=[0, 30, 40, 50, 100],
                            labels=['<30', '30-40', '40-50', '50+'])

# Calculate attrition rate per age group
attrition_by_age = (df_hr[df_hr['Attrition'] == 'Yes']
                    .groupby('AgeGroup')
                    .size() / 
                    df_hr.groupby('AgeGroup').size() * 100)

# Result (example):
# {'<30': 22.5%,      ← Highest
#  '30-40': 15.3%,
#  '40-50': 10.8%,
#  '50+': 8.2%}

ground_truth_highest_group = '<30'
ground_truth_highest_rate = 22.5
```

**System Answer (must identify correct group):**
```
Attrition rate by age group:

| Age Group | Attrition Rate |
|-----------|----------------|
| <30       | 22.5%          | ← Highest
| 30-40     | 15.3%          |
| 40-50     | 10.8%          |
| 50+       | 8.2%           |

The <30 age group has the highest attrition rate at 22.5%.
```

**Test Verification:**
```python
# Check if system correctly identified highest group
actual_highest_group = extract_highest_attrition_group(system_answer)

if actual_highest_group == ground_truth_highest_group:
    return "PASS"
else:
    return "ANSWER_FAIL"  # Wrong group identified
```

---

## 4.4 Policy Ground Truth - Document Files

### **Folder:** `docs/` (31 text files)

**File Structure:**
```
docs/
├── leave_policy.txt              (Annual leave, sick leave, emergency leave)
├── refund_policy.txt             (Customer refund procedures)
├── complaint_sop.txt             (Customer complaint handling)
├── branch_info.txt               (Branch addresses, managers, hours)
├── company_profile.txt           (Company history, mission, branches count)
├── product_catalog.txt           (Menu items, descriptions, prices)
├── attendance_policy.txt         (Clock-in/out rules, tardiness)
├── performance_review_sop.txt    (Annual review process)
├── hiring_process.txt            (Recruitment steps)
├── onboarding_process.txt        (New employee orientation)
├── exit_process.txt              (Resignation/termination procedures)
├── incident_escalation.txt       (Security incident reporting)
├── uniform_policy.txt            (Dress code requirements)
├── food_safety_sop.txt           (Kitchen hygiene standards)
├── cash_handling_sop.txt         (Cashier procedures)
├── ... (16 more policy files)
```

### **4.4.1 Example Policy File Content**

**File:** `docs/leave_policy.txt`

```
LEAVE POLICY - MyRetailChain Sdn Bhd
Effective Date: January 1, 2024

1. ANNUAL LEAVE ENTITLEMENT
- Permanent staff: 14 days per year
- Probation staff: 7 days per year
- Leave accrues monthly (1.17 days/month for permanent staff)

2. SICK LEAVE ENTITLEMENT
- Outpatient (with MC): 14 days per year
- Hospitalization: 60 days per year
- Medical certificate (MC) must be submitted within 2 working days

3. EMERGENCY LEAVE
- Definition: Unexpected family emergencies (death, serious illness, accident)
- Entitlement: 3 days per year
- Approval: Must notify manager immediately, submit supporting documents within 3 days

4. MATERNITY LEAVE
- Entitlement: 90 days (consecutive)
- Eligibility: Female employees who have worked ≥9 months
- Pay: Full salary for 90 days
- Application: Submit 30 days before expected delivery date

5. LEAVE APPLICATION PROCESS
- Apply via HR portal 7 days in advance (non-emergency)
- Manager approval required
- HR will notify approval status within 2 working days
- Cannot carry forward more than 7 days to next year

6. LEAVE RESTRICTIONS
- Cannot take leave during blackout periods: Chinese New Year (2 weeks), Hari Raya (1 week), year-end (Dec 20-31)
- Minimum 2 staff must be present per shift
- Kitchen staff leave must be approved by Kitchen Manager first

Contact HR for exceptions: hr@myretailchain.com.my
```

### **4.4.2 Ground Truth for Policy Questions**

**Question:** "What is the annual leave entitlement per year?"

**Ground Truth (from leave_policy.txt):**
```
Answer: 14 days per year for permanent staff, 7 days per year for probation staff.
Source: leave_policy.txt, Section 1 "ANNUAL LEAVE ENTITLEMENT"
```

**System Answer (must cite source):**
```
**Answer:** 
Annual leave entitlement is 14 days per year for permanent staff and 7 days per year for probation staff. 
Leave accrues monthly at 1.17 days per month for permanent employees.

**Evidence:** 
[DOC:leave_policy.txt] — "Permanent staff: 14 days per year, Probation staff: 7 days per year"

**Confidence:** High (direct quote from policy document)
```

**Test Verification:**
```python
# Check if answer contains correct numbers
if "14 days" in system_answer and "permanent" in system_answer.lower():
    number_check = "PASS"
else:
    number_check = "FAIL"

# Check if source is cited
if "[DOC:leave_policy.txt]" in system_answer or "leave_policy" in system_answer:
    citation_check = "PASS"
else:
    citation_check = "FAIL"  # LLM didn't cite source (hallucination risk!)

# Overall result
if number_check == "PASS" and citation_check == "PASS":
    return "PASS"
else:
    return "ANSWER_FAIL"
```

### **4.4.3 Complex Policy Question Example**

**Question:** "how to request emergency leave"

**Ground Truth (from leave_policy.txt, Section 3):**
```
1. Notify manager immediately (phone/WhatsApp)
2. Submit supporting documents within 3 days (death certificate, hospital admission letter, etc.)
3. Maximum 3 days per year
4. Definition: Unexpected family emergencies only (death, serious illness, accident)
```

**System Answer (must capture process steps):**
```
**Answer:**
To request emergency leave:
1. Notify your manager immediately by phone or WhatsApp
2. Submit supporting documents within 3 days (e.g., death certificate, hospital admission letter)
3. Emergency leave is limited to 3 days per year
4. Only for unexpected family emergencies: death, serious illness, or accidents

**Evidence:**
[DOC:leave_policy.txt] — "Emergency leave: Must notify manager immediately, submit supporting documents within 3 days. Entitlement: 3 days per year."

**Confidence:** High
```

**Test Verification:**
```python
# Check if key steps are mentioned
required_elements = [
    "notify manager",
    "immediately",
    "supporting documents",
    "3 days"  # Both "within 3 days" and "3 days per year"
]

missing_elements = []
for element in required_elements:
    if element not in system_answer.lower():
        missing_elements.append(element)

# Check source citation
if "[DOC:leave_policy.txt]" not in system_answer:
    return "ANSWER_FAIL"  # No source citation

# Overall result
if len(missing_elements) == 0:
    return "PASS"
elif len(missing_elements) <= 1:
    return "PARTIAL"  # Minor detail missing
else:
    return "ANSWER_FAIL"  # Major steps missing
```

---

## 4.5 Ground Truth Verification Methods

### **4.5.1 Quantitative Questions (Sales/HR KPI)**

**Verification Strategy: Exact Number Matching**

```python
def verify_quantitative_answer(question, system_answer, ground_truth_value):
    """
    Verify answers for sales/HR questions
    Ground truth is EXACT - no interpretation needed
    """
    
    # Extract number from system answer
    # Example: "Total sales: RM 456,789.12" → 456789.12
    actual_value = extract_number_from_answer(system_answer)
    
    if actual_value is None:
        return "ANSWER_FAIL", "No number found in answer"
    
    # Allow small tolerance for floating point rounding
    tolerance = 0.01  # RM 0.01
    difference = abs(actual_value - ground_truth_value)
    
    if difference <= tolerance:
        return "PASS", f"Correct (diff: RM {difference:.2f})"
    else:
        return "ANSWER_FAIL", f"Wrong number: expected {ground_truth_value}, got {actual_value}"
```

**Example Test Cases:**

| Question | Ground Truth | System Answer | Result | Reason |
|----------|--------------|---------------|--------|--------|
| "sales June 2024" | 456789.12 | "RM 456,789.12" | ✅ PASS | Exact match |
| "sales June 2024" | 456789.12 | "RM 456,789.11" | ✅ PASS | Within tolerance (RM 0.01) |
| "sales June 2024" | 456789.12 | "RM 450,000" | ❌ FAIL | Off by RM 6,789 |
| "sales June 2024" | 456789.12 | "Around RM 450K" | ❌ FAIL | Not exact number |

### **4.5.2 Qualitative Questions (Policy/RAG)**

**Verification Strategy: Source Citation + Key Information Check**

```python
def verify_qualitative_answer(question, system_answer, expected_source, key_points):
    """
    Verify answers for policy questions
    Ground truth is in documents - check citation and key info
    """
    
    # Check 1: Source citation present
    if f"[DOC:{expected_source}]" not in system_answer and expected_source not in system_answer:
        return "ANSWER_FAIL", "No source citation (hallucination risk)"
    
    # Check 2: Key information present
    missing_points = []
    for point in key_points:
        if point.lower() not in system_answer.lower():
            missing_points.append(point)
    
    if len(missing_points) == 0:
        return "PASS", "All key points covered with source citation"
    elif len(missing_points) <= 1 and len(key_points) > 3:
        return "PARTIAL", f"Minor detail missing: {missing_points[0]}"
    else:
        return "ANSWER_FAIL", f"Missing key info: {', '.join(missing_points)}"
```

**Example Test Cases:**

| Question | Expected Source | Key Points | System Answer | Result |
|----------|----------------|------------|---------------|--------|
| "annual leave entitlement" | leave_policy.txt | ["14 days", "permanent staff"] | "14 days for permanent staff [DOC:leave_policy.txt]" | ✅ PASS |
| "annual leave entitlement" | leave_policy.txt | ["14 days", "permanent staff"] | "14 days for permanent staff" | ❌ FAIL (no citation) |
| "annual leave entitlement" | leave_policy.txt | ["14 days", "permanent staff"] | "Employees get leave [DOC:leave_policy.txt]" | ❌ FAIL (missing key info) |

### **4.5.3 Ranking Questions (Top N, Best/Worst)**

**Verification Strategy: Ranking Order + Number Accuracy**

```python
def verify_ranking_answer(question, system_answer, ground_truth_ranking):
    """
    Verify answers for "top 3", "best", "worst" questions
    Both order and numbers must be correct
    """
    
    # Extract ranking from system answer
    # Example: "1. Cheese Burger: RM 125K\n2. Beef Burger: RM 98K"
    actual_ranking = extract_ranking_from_answer(system_answer)
    
    # Check 1: Ranking order correct
    order_correct = True
    for i, expected_item in enumerate(ground_truth_ranking):
        if i >= len(actual_ranking) or actual_ranking[i]['name'] != expected_item['name']:
            order_correct = False
            break
    
    if not order_correct:
        return "ANSWER_FAIL", f"Ranking order wrong: expected {ground_truth_ranking}, got {actual_ranking}"
    
    # Check 2: Numbers correct (for each item)
    for i, expected_item in enumerate(ground_truth_ranking):
        actual_value = actual_ranking[i]['value']
        expected_value = expected_item['value']
        
        if abs(actual_value - expected_value) > 0.01:
            return "ANSWER_FAIL", f"Wrong value for {expected_item['name']}: expected {expected_value}, got {actual_value}"
    
    return "PASS", "Ranking order and values correct"
```

**Example Test Cases:**

| Question | Ground Truth | System Answer | Result | Reason |
|----------|--------------|---------------|--------|--------|
| "top 3 products June" | [Cheese: 125K, Beef: 98K, Fries: 76K] | "1. Cheese: 125K\n2. Beef: 98K\n3. Fries: 76K" | ✅ PASS | Order & numbers correct |
| "top 3 products June" | [Cheese: 125K, Beef: 98K, Fries: 76K] | "1. Beef: 98K\n2. Cheese: 125K\n3. Fries: 76K" | ❌ FAIL | Order wrong (Cheese should be #1) |
| "top 3 products June" | [Cheese: 125K, Beef: 98K, Fries: 76K] | "1. Cheese: 120K\n2. Beef: 98K\n3. Fries: 76K" | ❌ FAIL | Number wrong for Cheese |

---

## 4.6 Why Ground Truth Matters (Anti-Hallucination)

### **4.6.1 The Hallucination Problem**

**Without ground truth verification:**
```
CEO asks: "sales bulan June berapa?"
LLM generates: "Based on analysis, sales were approximately RM 450,000."

Problem:
- "approximately" → Not exact
- "based on analysis" → LLM might be guessing
- No source citation → Can't verify
- Actual ground truth: RM 456,789.12 → LLM was WRONG by RM 6,789!
```

**With ground truth verification:**
```
CEO asks: "sales bulan June berapa?"
System calculates: df_june['TotalPrice'].sum() = 456789.12
System answers: "Total sales for 2024-06: RM 456,789.12"

Test verifies:
- Expected: 456789.12
- Actual: 456789.12
- Result: ✅ PASS (numbers match exactly)
```

### **4.6.2 Deterministic vs Non-Deterministic Handlers**

| Handler | Type | Ground Truth | Hallucination Risk | Why? |
|---------|------|--------------|-------------------|------|
| **Sales KPI** | Deterministic | CSV exact values | ❌ **ZERO** | Direct pandas calculation, no LLM |
| **HR KPI** | Deterministic | CSV exact values | ❌ **ZERO** | Direct pandas calculation, no LLM |
| **RAG Docs** | Non-Deterministic | Document text | ⚠️ **MEDIUM** | LLM can paraphrase or invent if not constrained |

**Why Sales/HR handlers have zero hallucination risk:**
```python
# Sales handler (deterministic)
def answer_sales(query, df):
    month = extract_month(query)           # Parse user input
    df_filtered = df[df['YearMonth'] == month]  # Filter CSV
    total = df_filtered['TotalPrice'].sum()     # Calculate (pure math)
    return f"Total: RM {total:,.2f}"            # Format result

# No LLM involved → Answer is ALWAYS exact CSV value
# Impossible to hallucinate when you're just summing numbers!
```

**Why RAG handler has medium hallucination risk:**
```python
# RAG handler (non-deterministic)
def answer_with_rag(query, retriever, llm):
    docs = retriever.get_relevant_documents(query)  # Retrieve docs
    context = "\n".join([doc.page_content for doc in docs])
    prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
    answer = llm.generate(prompt)  # ← LLM can paraphrase/invent here!
    return answer

# LLM might:
# 1. Paraphrase incorrectly (change meaning)
# 2. Add information not in docs (hallucinate)
# 3. Miss key details (incomplete answer)
# 4. Forget to cite source (no traceability)
```

**Mitigation strategies for RAG hallucination:**
1. **System prompt constraints:** "Only use provided context, cite sources"
2. **Source citation requirement:** Must include [DOC:filename]
3. **Fail-closed behavior:** If no docs found, say "not available" instead of guessing
4. **Verification layer:** Second LLM pass to check facts (optional, adds latency)

---

## 4.7 Ground Truth Data Quality Checks

### **4.7.1 Sales CSV Data Quality**

**Automated checks before testing:**
```python
def validate_sales_csv(df_sales):
    """
    Ensure sales.csv is clean and complete
    Run before starting test suite
    """
    
    issues = []
    
    # Check 1: No missing values in critical columns
    critical_cols = ['Date', 'State', 'ProductName', 'TotalPrice']
    for col in critical_cols:
        if df_sales[col].isnull().any():
            issues.append(f"Missing values in {col}")
    
    # Check 2: Date range complete (no gaps)
    date_range = pd.date_range(start='2024-01-01', end='2024-07-31', freq='D')
    actual_dates = df_sales['Date'].unique()
    missing_dates = set(date_range) - set(actual_dates)
    if len(missing_dates) > 0:
        issues.append(f"Missing dates: {len(missing_dates)} days have no transactions")
    
    # Check 3: TotalPrice = Quantity × UnitPrice (consistency check)
    df_sales['CalculatedTotal'] = df_sales['Quantity'] * df_sales['UnitPrice']
    price_mismatch = df_sales[abs(df_sales['TotalPrice'] - df_sales['CalculatedTotal']) > 0.01]
    if len(price_mismatch) > 0:
        issues.append(f"Price calculation errors: {len(price_mismatch)} rows")
    
    # Check 4: Reasonable value ranges
    if df_sales['TotalPrice'].min() < 0:
        issues.append("Negative prices found")
    if df_sales['Quantity'].min() < 1:
        issues.append("Zero or negative quantities found")
    
    # Report
    if len(issues) == 0:
        print("✅ Sales CSV quality: PASS")
        return True
    else:
        print("❌ Sales CSV quality: FAIL")
        for issue in issues:
            print(f"   - {issue}")
        return False
```

### **4.7.2 HR CSV Data Quality**

**Automated checks before testing:**
```python
def validate_hr_csv(df_hr):
    """
    Ensure hr.csv is clean and complete
    Run before starting test suite
    """
    
    issues = []
    
    # Check 1: No duplicate employee IDs
    if df_hr['EmpID'].duplicated().any():
        issues.append("Duplicate employee IDs found")
    
    # Check 2: Attrition values valid
    if not df_hr['Attrition'].isin(['Yes', 'No']).all():
        issues.append("Invalid attrition values (must be Yes/No)")
    
    # Check 3: Age reasonable range
    if df_hr['Age'].min() < 18 or df_hr['Age'].max() > 70:
        issues.append("Unreasonable age values")
    
    # Check 4: Salary ranges by job role
    role_salary_ranges = {
        'Kitchen Staff': (2500, 4500),
        'Cashier': (2800, 4000),
        'Sales Executive': (3500, 6000),
        'Manager': (6000, 12000)
    }
    for role, (min_sal, max_sal) in role_salary_ranges.items():
        role_data = df_hr[df_hr['JobRole'] == role]
        if len(role_data) > 0:
            if role_data['MonthlyIncome'].min() < min_sal or role_data['MonthlyIncome'].max() > max_sal:
                issues.append(f"Unreasonable salary for {role}")
    
    # Report
    if len(issues) == 0:
        print("✅ HR CSV quality: PASS")
        return True
    else:
        print("❌ HR CSV quality: FAIL")
        for issue in issues:
            print(f"   - {issue}")
        return False
```

### **4.7.3 Document Folder Quality**

**Automated checks before testing:**
```python
def validate_docs_folder(docs_path='docs/'):
    """
    Ensure all policy documents exist and are not empty
    Run before starting test suite
    """
    
    # Expected documents (from test_questions_master.csv)
    expected_docs = [
        'leave_policy.txt',
        'refund_policy.txt',
        'complaint_sop.txt',
        'branch_info.txt',
        'company_profile.txt',
        'product_catalog.txt',
        'attendance_policy.txt',
        'performance_review_sop.txt',
        'hiring_process.txt',
        'onboarding_process.txt',
        'exit_process.txt',
        'incident_escalation.txt'
    ]
    
    issues = []
    
    for doc in expected_docs:
        filepath = os.path.join(docs_path, doc)
        
        # Check 1: File exists
        if not os.path.exists(filepath):
            issues.append(f"Missing: {doc}")
            continue
        
        # Check 2: File not empty
        if os.path.getsize(filepath) == 0:
            issues.append(f"Empty file: {doc}")
            continue
        
        # Check 3: File is readable text
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) < 100:  # Suspiciously short
                    issues.append(f"Suspiciously short: {doc} ({len(content)} chars)")
        except Exception as e:
            issues.append(f"Cannot read: {doc} - {str(e)}")
    
    # Report
    if len(issues) == 0:
        print(f"✅ Document quality: PASS ({len(expected_docs)} files)")
        return True
    else:
        print("❌ Document quality: FAIL")
        for issue in issues:
            print(f"   - {issue}")
        return False
```

---

**CHECKPOINT: Documentation 65% Complete**

**What's done:**
- ✅ Part 1: System Overview
- ✅ Part 2: Test Questions Explained
- ✅ Part 3: System Architecture
- ✅ Part 4: Ground Truth Sources (COMPLETE)
  - Sales CSV structure & examples
  - HR CSV structure & examples
  - Policy documents structure & examples
  - Verification methods for all types
  - Anti-hallucination rationale
  - Data quality checks

**What's next:**
- Part 5: Failure Modes & Debugging
- Part 6: Limitations & Improvements
- Part 7: Development Process (For FYP Report)
- Part 8: Summary

**Estimated remaining:** 35%

**Continue to Part 5? (Failure Modes & Debugging)**