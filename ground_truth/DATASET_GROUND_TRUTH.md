# Dataset Ground Truth - MY Retail Sales 2024 H1

**Purpose**: Quick reference for testing and validation of the CEO chatbot system. Use this to verify query results are accurate and not hallucinated.

**Dataset**: `data/MY_Retail_Sales_2024H1.csv`  
**Period**: January 1, 2024 - June 30, 2024  
**Total Transactions**: 29,635  
**Total Revenue**: RM 596,989.31

---

## 1. Products (7 Total)

| # | Product Name | Transactions | Total Revenue | % of Total Revenue |
|---|--------------|--------------|---------------|-------------------|
| 1 | Beef Burger | 4,732 | RM 120,876.44 | 20.2% |
| 2 | Cheese Burger | 4,153 | RM 114,734.72 | 19.2% |
| 3 | Chicken Burger | 5,313 | RM 115,084.95 | 19.3% |
| 4 | Fries | 5,896 | RM 69,232.53 | 11.6% |
| 5 | Soft Drink | 4,149 | RM 32,228.50 | 5.4% |
| 6 | Spicy Burger | 2,982 | RM 88,502.16 | 14.8% |
| 7 | Veggie Burger | 2,410 | RM 56,330.01 | 9.4% |

**Notes**:
- Top revenue product: **Beef Burger** (RM 120,876.44)
- Most transactions: **Fries** (5,896 transactions)
- Lowest revenue: **Soft Drink** (RM 32,228.50)

---

## 2. States (6 Total)

| # | State | Transactions | Total Revenue | % of Total Revenue |
|---|-------|--------------|---------------|-------------------|
| 1 | Johor | 4,749 | RM 95,965.59 | 16.1% |
| 2 | Kuala Lumpur | 4,908 | RM 99,084.66 | 16.6% |
| 3 | Penang | 5,114 | RM 102,375.37 | 17.1% |
| 4 | Sabah | 4,938 | RM 98,935.37 | 16.6% |
| 5 | Sarawak | 5,107 | RM 103,795.95 | 17.4% |
| 6 | Selangor | 4,819 | RM 96,832.37 | 16.2% |

**Notes**:
- Top revenue state: **Sarawak** (RM 103,795.95)
- Most transactions: **Penang** (5,114 transactions)
- Revenue is fairly balanced across all states (16-17% each)

---

## 3. Cities (6 Total)

1. **Bukit Bintang** (Kuala Lumpur)
2. **George Town** (Penang)
3. **Johor Bahru** (Johor)
4. **Kota Kinabalu** (Sabah)
5. **Kuching** (Sarawak)
6. **Shah Alam** (Selangor)

---

## 4. Branches (12 Total)

Each city has 2 branches:

| State | City | Branches |
|-------|------|----------|
| Kuala Lumpur | Bukit Bintang | Bukit Bintang Branch 1, Bukit Bintang Branch 2 |
| Penang | George Town | George Town Branch 1, George Town Branch 2 |
| Johor | Johor Bahru | Johor Bahru Branch 1, Johor Bahru Branch 2 |
| Sabah | Kota Kinabalu | Kota Kinabalu Branch 1, Kota Kinabalu Branch 2 |
| Sarawak | Kuching | Kuching Branch 1, Kuching Branch 2 |
| Selangor | Shah Alam | Shah Alam Branch 1, Shah Alam Branch 2 |

---

## 5. Regions (6 Total)

Regions match the state names:
1. Johor
2. Kuala Lumpur
3. Penang
4. Sabah
5. Sarawak
6. Selangor

---

## 6. Employees (12 Total)

1. SalesRep_01
2. SalesRep_02
3. SalesRep_03
4. SalesRep_04
5. SalesRep_05
6. SalesRep_06
7. SalesRep_07
8. SalesRep_08
9. SalesRep_09
10. SalesRep_10
11. SalesRep_11
12. SalesRep_12

---

## 7. Sales Channels (3 Total)

| # | Channel | Transactions | Total Revenue | % of Total Revenue |
|---|---------|--------------|---------------|-------------------|
| 1 | Delivery | 4,473 | RM 91,417.72 | 15.3% |
| 2 | Dine-in | 14,685 | RM 296,276.47 | 49.6% |
| 3 | Takeaway | 10,477 | RM 209,295.12 | 35.1% |

**Notes**:
- **Dine-in** is the dominant channel (49.6% of revenue, 49.5% of transactions)
- Takeaway is second (35.1% of revenue)
- Delivery is smallest but still significant (15.3%)

---

## 8. Payment Methods (3 Total)

| # | Payment Method | Transactions | % of Transactions |
|---|----------------|--------------|-------------------|
| 1 | Card | 10,386 | 35.0% |
| 2 | Cash | 5,989 | 20.2% |
| 3 | eWallet | 13,260 | 44.7% |

**Notes**:
- **eWallet** is most popular (44.7% of transactions)
- Card is second (35.0%)
- Cash is least used (20.2%)

---

## 9. Testing Quick Reference

### Common Test Queries

**Product Queries**:
- "Top 5 products by revenue" → Should show Beef Burger, Chicken Burger, Cheese Burger, Spicy Burger, Fries
- "Which product has the lowest revenue?" → Soft Drink (RM 32,228.50)
- "Total revenue for Veggie Burger" → RM 56,330.01

**State Queries**:
- "Top 3 states by revenue" → Sarawak, Penang, Kuala Lumpur
- "Total revenue for Selangor" → RM 96,832.37
- "Which state has the most transactions?" → Penang (5,114)

**Channel Queries**:
- "Dine-in revenue" → RM 296,276.47 (49.6% of total)
- "Compare Delivery vs Takeaway" → Takeaway: RM 209,295.12, Delivery: RM 91,417.72

**Date Range Queries**:
- "January 2024 revenue" → Filter to 2024-01
- "June 2024 products" → Filter to 2024-06
- "Q1 2024" → January-March 2024

### Expected Behavior

✅ **Correct Results**:
- Products: Exactly 7 products (including Veggie Burger and Soft Drink)
- States: Exactly 6 states (no other regions)
- Branches: Exactly 12 branches (2 per city)
- Employees: Exactly 12 sales reps

❌ **Hallucination Indicators**:
- Products not in the list above
- States beyond the 6 listed
- Revenue values that don't match ground truth
- Dates outside 2024-01-01 to 2024-06-30

### Filter Inheritance Tests

**Test Case 1**: Context preservation with month
```
Q1: "Top 5 products in January 2024"
Q2: "Break down by state"
Expected: Should maintain January 2024 filter
```

**Test Case 2**: Smart filter inheritance
```
Q1: "Total revenue for Beef Burger in Selangor"
Q2: "Which states contributed most?"
Expected: Should NOT inherit Product filter (asking about states)
```

**Test Case 3**: Dimension switching
```
Q1: "Top products in Selangor"
Q2: "Which products drove the performance?"
Expected: Should keep State filter, show product breakdown
```

---

## 10. Data Quality Notes

- **No missing values** in critical dimensions (Product, State, Channel)
- **Balanced distribution** across states (each ~16-17% of total)
- **Date range**: Complete 6 months (H1 2024)
- **Transaction IDs**: Sequential from TXN0000001 to TXN0029635
- **Pricing**:
  - Beef Burger: RM 12.9
  - Chicken Burger: RM 10.9
  - Cheese Burger: RM 13.9
  - Spicy Burger: RM 14.9
  - Fries: RM 5.9
  - Veggie Burger: RM 11.9
  - Soft Drink: RM 3.9

---

**Last Updated**: Generated from actual dataset analysis  
**Validation**: Use this document to verify chatbot responses are accurate
