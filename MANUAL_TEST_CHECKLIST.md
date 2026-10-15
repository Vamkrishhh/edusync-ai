# EduSync AI - Manual Browser Test Checklist

## Application URL
**`http://localhost:8502`**

The application is running and accessible. A browser screenshot has been saved to `app_screenshot.png` for reference.

---

## Priority 1: Critical User Workflows (Must Test)

### 1. PDF Upload and Indexing
**Steps:**
1. Navigate to **📚 Document Library**
2. Scroll to "Add Course Document" section
3. Click file upload widget
4. Select a PDF file from your computer
5. Click "Index Document" button

**Expected:**
- Upload progress appears
- Success message: "Indexed '[filename]' (X passages ready)"
- Document appears in "Indexed Course Documents" section
- Document shows filename, page count, chunk count

**Verify:**
- [ ] Upload works without errors
- [ ] Document appears in list immediately
- [ ] Re-uploading same file doesn't create duplicate

---

### 2. Document Search
**Steps:**
1. Stay on **📚 Document Library**
2. Type "normalization" in search box
3. Click "Search Notes" button

**Expected:**
- Search results appear below
- Shows "Found X matching passage(s)"
- Each result shows source document and page number
- Text highlights are visible

**Verify:**
- [ ] Search executes quickly (< 2 seconds)
- [ ] Results are relevant
- [ ] "Ask AI Tutor About This" button appears

---

### 3. AI Tutor Multiple Queries
**Steps:**
1. Navigate to **🤖 AI Study Assistant**
2. Click "What should I study today?" button
3. Wait for response
4. Click "Explain normalization from my notes" button
5. Wait for second response

**Expected:**
- First query appears in UI
- "Supervisor Response" card displays answer
- "Agent Activity" section shows tools used
- Second query appears BELOW first (not replacing it)
- Each query has its own separate response

**Verify:**
- [ ] Queries don't replace each other
- [ ] Each response is unique to its query
- [ ] Traces show correct tool calls
- [ ] No stale/cached responses

---

### 4. Quiz Generation and Submission
**Steps:**
1. Navigate to **📝 Quiz Generator**
2. Select topic: "Indexing & Storage"
3. Select difficulty: "medium"
4. Set questions: 3
5. Click "Generate Topic Assessment"
6. Answer all questions (select any options)
7. Click "Submit Assessment"

**Expected:**
- Quiz questions appear with radio buttons
- All questions display properly
- Submit button is accessible
- After submit: score appears (X/3)
- Percentage calculation is correct
- "Question Breakdown" shows each answer with explanation

**Verify:**
- [ ] Quiz generates without errors
- [ ] Radio buttons are clickable
- [ ] Submit button works
- [ ] Score matches answers
- [ ] Can't submit twice (no duplicate attempts)

---

### 5. Performance Metrics Display
**Steps:**
1. Navigate to **📈 Performance Analyzer**
2. Scroll through the page

**Expected:**
- "Overall Accuracy" metric shows percentage
- "Total Assessments" count matches quiz history
- "Topic Mastery" section lists topics with progress bars
- Each topic shows percentage and classification badge
- "Learning Diagnosis" provides recommendations

**Verify:**
- [ ] Metrics match actual quiz attempts
- [ ] Percentages are accurate
- [ ] Classification thresholds correct (≥80% Strong, 60-79% Developing, <60% Needs Attention)
- [ ] Empty state shown if no quizzes taken

---

### 6. Study Plan Generation
**Steps:**
1. Navigate to **📅 Study Planner**
2. In form at bottom:
   - Subject: "Database Management Systems"
   - Exam Date: Select a date 5 days in the future
   - Topics: Select 3 topics
   - Daily Study Hours: 4
3. Click "Generate Study Plan"

**Expected:**
- Success message appears
- Active plan displays at top
- Shows exam date and days remaining
- Day-by-day schedule appears
- Tasks have checkboxes

**Verify:**
- [ ] Plan generates successfully
- [ ] Date validation works (rejects past dates)
- [ ] Hour validation works (rejects 0, negative, >16)
- [ ] Tasks appear grouped by day
- [ ] Task checkboxes are clickable

---

### 7. Task Completion Toggle
**Steps:**
1. Stay on **📅 Study Planner**
2. Click checkbox next to first task
3. Navigate to **📊 Dashboard**
4. Navigate back to **📅 Study Planner**

**Expected:**
- Checkbox toggles checked state
- Task text shows strikethrough when complete
- Completion persists across navigation
- Progress percentage updates

**Verify:**
- [ ] Checkbox responds to click
- [ ] Visual feedback immediate
- [ ] State persists across pages
- [ ] Can toggle back to uncompleted

---

## Priority 2: Navigation & State (Important)

### 8. Page Navigation
**Steps:**
1. Click through all 7 pages in sidebar:
   - 📊 Dashboard
   - 📚 Document Library  
   - 🤖 AI Study Assistant
   - 📝 Quiz Generator
   - 📈 Performance Analyzer
   - 📅 Study Planner
   - 🎯 Progress Tracker

**Verify:**
- [ ] All pages load without errors
- [ ] No white screens or "Streamlit encountered an error"
- [ ] Sidebar stays visible
- [ ] Selected page is highlighted
- [ ] Browser back button works

---

### 9. Cross-Page Navigation Buttons
**Steps:**
1. On **📊 Dashboard**, click "Practice Indexing & Storage" button
2. Should navigate to **📝 Quiz Generator**
3. Complete a quiz
4. Click "Review Notes" button
5. Should navigate to **📚 Document Library**

**Verify:**
- [ ] Navigation buttons work
- [ ] State preserved when navigating
- [ ] No reload loops

---

### 10. Progress Tracker Display
**Steps:**
1. Navigate to **🎯 Progress Tracker**
2. Review all sections

**Verify:**
- [ ] Shows task completion count
- [ ] Shows quiz attempt count
- [ ] Topic mastery matches Performance Analyzer
- [ ] Recent activity displays quiz history
- [ ] Progress insights are visible

---

## Priority 3: Edge Cases (Nice to Have)

### 11. Empty State Handling
**Steps:**
1. Reset database (use "Reset Workspace" button in sidebar)
2. Visit each page

**Verify:**
- [ ] Dashboard shows zero metrics
- [ ] Document Library shows "No Course Material" message
- [ ] Performance Analyzer shows "No Assessment Data"
- [ ] Study Planner shows "No Active Study Plan"
- [ ] No crashes or null errors

---

### 12. Duplicate Prevention
**Steps:**
1. Upload same PDF twice
2. Take same quiz twice (same topic, same answers)
3. Generate study plan twice (same parameters)

**Verify:**
- [ ] Document not duplicated in list
- [ ] Quiz attempt not duplicated in history
- [ ] Study plan replaces previous (doesn't duplicate)

---

### 13. Form Validation
**Steps:**
1. Study Planner: Try to create plan with past exam date
2. Study Planner: Try 0 hours per day
3. Study Planner: Try 20 hours per day

**Verify:**
- [ ] Error message for past date
- [ ] Error message for 0 hours
- [ ] Error message for excessive hours (>16)
- [ ] Clear error messages displayed

---

### 14. Browser Console Check
**Steps:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Navigate through all pages

**Verify:**
- [ ] No JavaScript errors (red text)
- [ ] No broken image/resource 404s
- [ ] Warnings are acceptable (ignore Streamlit hydration warnings)

---

### 15. Mobile Responsiveness (Optional)
**Steps:**
1. Open DevTools (F12)
2. Toggle device toolbar (mobile view)
3. Test iPad and iPhone sizes

**Verify:**
- [ ] Layout doesn't break
- [ ] Sidebar is accessible
- [ ] Buttons are clickable
- [ ] Text is readable

---

## Testing Notes

- **Time Required**: 15-20 minutes for Priority 1, 5 minutes for Priority 2, 5 minutes for Priority 3
- **Browser**: Test primarily in Chrome or Edge (modern Chromium-based)
- **Database**: Sample data is already loaded (2 documents, 2 quiz attempts)
- **Screenshot**: Check `app_screenshot.png` for initial visual state

## Issue Reporting Format

If you find an issue:

```
Page: [Page Name]
Action: [What you clicked/typed]
Expected: [What should happen]
Actual: [What actually happened]
Console errors: [Any red errors in F12 console]
```

