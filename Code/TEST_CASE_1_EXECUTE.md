# 🚀 EXECUTE NOW: Test Case 1

**Application Status:** ✅ Gradio Running  
**Terminal Window:** Keep visible to see logging output  

---

## Test Case 1: Filter Persistence (H4.2)

### Step 1: Type First Query

In the Gradio chatbox, type:
```
Total revenue for Selangor in January 2024
```

### Step 2: Watch Terminal for These Logs

You should see:
```
🔀 ROUTE: 'Total revenue for Selangor...' → sales_kpi (matched: ['revenue'])

🔍 FILTER EXTRACTION: 'Total revenue for Selangor in January 2024'
   State: Selangor
   Branch: None
   Product: None
   Employee: None
   Channel: None
   Metric: revenue
```

✅ **Record:** State = Selangor ✓

---

### Step 3: Type Follow-up Query

After getting the answer, type:
```
How about Samsung products?
```

### Step 4: Watch Terminal - CRITICAL OBSERVATION

Look for:
```
🔀 ROUTE: 'How about Samsung products?' → ??? 

🔍 FILTER EXTRACTION: 'How about Samsung products?'
   State: ???  ← CRITICAL: Should be Selangor, probably None
   Product: Samsung
   ...

📝 FOLLOW-UP GENERATION:
   Extracted context: {state: ???}
   
📊 CONVERSATION_HISTORY (2 turns):
   [0] user: Total revenue for Selangor...
   [1] assistant: ...
```

---

## 🎯 What We're Testing

**HYPOTHESIS H4.2:** State filter will be LOST  
**Expected Bug:** State: None (Selangor was forgotten)  
**If Bug Exists:** Answer will show ALL states, not just Selangor  

---

## 📋 Copy & Paste These Logs

After both queries, paste in chat:
1. All lines with 🔀 🔍 📝 📊 emojis
2. The two answers you received

This gives us empirical evidence!

---

## ⏭️ What's Next

After Test Case 1, we'll run 4 more test cases (~20 min total)  
Then analyze all logs and implement fixes

**Ready? Type the first query now! →**
