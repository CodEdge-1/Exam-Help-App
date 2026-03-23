# ✏️ Custom Prompts Guide - Make the AI Do What YOU Want

Custom prompts let you teach the AI to do specific tasks when it looks at your screen.

---

## 🤔 What Are Prompts?

A **prompt** is like giving instructions to the AI. It tells the AI what to do when it looks at your screen capture.

**Example:**
- **Without a prompt:** AI just describes what it sees
- **With a prompt:** AI translates text, extracts data, checks grammar, or answers questions

---

## 📚 Built-In Prompts (Already Available)

When you open the **Prompts** page in the dashboard, you'll see 6 ready-to-use prompts:

| Prompt | Icon | What it does |
|--------|------|--------------|
| **Answer Question** | ? | Finds any question on screen and answers it |
| **Summarize** | S | Creates bullet points of the main content |
| **Translate** | T | Translates foreign text to English |
| **Explain Simply** | E | Explains complex content in simple words |
| **Extract Data** | D | Pulls out numbers, facts, and dates |
| **Proofread** | P | Checks for grammar and spelling errors |

**To use one:**
1. Go to the **Prompts** page
2. Click on the prompt you want
3. It lights up with a blue border — it's now active!
4. Press Ctrl+shift+x to capture — the AI uses that prompt

---

## ➕ How to Add Your Own Custom Prompt

### Step 1: Go to Prompts Page
Click **"Prompts"** in the left sidebar of the dashboard.

### Step 2: Scroll Down to the Form
You'll see a section called **"+ Add Custom Prompt"** with 4 boxes:

### Step 3: Fill in the Boxes

**Box 1: Name**
- What you want to call this prompt
- Examples: "Code Review", "Meeting Notes", "Recipe Extractor"

**Box 2: Icon**
- A single letter or emoji that represents it
- Examples: "C" for Code, "📝" for Notes, "🍳" for Recipe

**Box 3: Description (optional)**
- A short explanation of what it does
- Example: "Reviews code and suggests improvements"

**Box 4: Prompt Instructions**
- This is the MOST IMPORTANT box!
- Write exactly what you want the AI to do
- Be specific and clear

### Step 4: Click "Save Prompt"
Your new prompt appears in the grid above! ✅

---

## 💡 Examples of Custom Prompts You Can Create

### Example 1: Meeting Notes
**Name:** Meeting Notes  
**Icon:** 📝  
**Description:** Extracts action items and decisions from meetings  
**Prompt:**
```
Look at this screen capture and extract:
1. All action items (tasks assigned to people)
2. All decisions that were made
3. Key discussion points

Format as:
ACTION ITEMS:
- [Person]: [Task]

DECISIONS:
- [What was decided]

DISCUSSION:
- [Main points]

Ignore the UI, taskbar, and timestamps.
```

### Example 2: Code Review
**Name:** Code Review  
**Icon:** C  
**Description:** Reviews code and suggests improvements  
**Prompt:**
```
Review the code visible on this screen.

Check for:
1. Bugs or errors
2. Performance issues
3. Better ways to write it
4. Security problems

Be specific about line numbers if you can see them.
Explain suggestions in simple terms.
```

### Example 3: Recipe Extractor
**Name:** Recipe Extractor  
**Icon:** 🍳  
**Description:** Pulls recipe ingredients and steps from any source  
**Prompt:**
```
Extract the recipe from this screen.

Format as:
INGREDIENTS:
- [list each ingredient with quantity]

INSTRUCTIONS:
1. [Step 1]
2. [Step 2]
etc.

If cooking time or servings are shown, include them.
Ignore ads, comments, and website UI.
```

### Example 4: Email Draft Helper
**Name:** Email Draft  
**Icon:** 📧  
**Description:** Turns messy notes into a polished email  
**Prompt:**
```
Look at the notes/text on this screen and turn them into a professional email.

Include:
- A clear subject line
- Proper greeting
- Well-organized paragraphs
- Professional tone
- Appropriate closing

Make it concise but complete.
```

### Example 5: Study Helper
**Name:** Study Helper  
**Icon:** 📖  
**Description:** Creates study questions from lecture slides  
**Prompt:**
```
Based on the content on this screen, create 5 study questions that would help someone learn this material.

For each question, also provide the answer.

Format:
Q1: [Question]
A1: [Answer]

Q2: [Question]
A2: [Answer]

etc.
```

### Example 6: Price Comparison
**Name:** Price Check  
**Icon:** 💰  
**Description:** Extracts prices and compares products  
**Prompt:**
```
Extract all products and prices visible on this screen.

Format as a table:
Product | Price | Features

Then tell me which is the best value and why.
```

---

## Tips for Writing Good Prompts

### DO:
- **Be specific** about what you want
- **Use examples** of the format you want
- **Tell it what to ignore** (like UI, ads, taskbar)
- **Use simple, clear language**
- **Test and refine** — if it doesn't work, rewrite it

### DON'T:
- Don't be vague ("tell me about this")
- Don't ask it to access files or browse the web
- Don't expect it to remember previous captures
- Don't write super long prompts (keep under 500 words)

---

##  How to Edit or Delete a Custom Prompt

### To Delete:
1. Find your custom prompt in the Prompts page
2. Look for the small **X** button in the bottom-right corner
3. Click it
4. Confirm deletion

### To Edit:
- You can't edit existing prompts directly
- Instead: Delete the old one and create a new one with the changes

---

## Using Custom Prompts on Mobile

1. Open the mobile client: `http://YOUR_IP:8000/mobile`
2. Scroll horizontally through the prompt chips at the top
3. Tap the prompt you want to use
4. It lights up blue — now active!
5. Press "Request Capture" button
6. The AI uses that prompt for the capture

---

## Real-World Use Cases

### For Students:
- "Homework Helper" — Explains difficult concepts
- "Citation Generator" — Extracts bibliography info
- "Study Guide Creator" — Makes flashcards from notes

### For Work:
- "Meeting Minutes" — Extracts decisions and action items
- "Email Responder" — Drafts replies to emails on screen
- "Data Entry Helper" — Extracts form data into organized lists

### For Personal:
- "Recipe Saver" — Extracts recipes from websites
- "Shopping List" — Creates organized shopping lists
- "Travel Planner" — Extracts flight/hotel details

---

## How to Test Your Custom Prompt

1. Create the prompt
2. Click on it to activate it (blue border appears)
3. Open a test document or webpage
4. Press QQ
5. Check if the answer is what you wanted
6. If not — delete and recreate with better instructions

---

## Sample Prompts You Can Copy & Paste

### SQL Query Explainer
```
Explain the SQL query visible on this screen in plain English.
Break down what each part does.
If there are any inefficiencies, suggest improvements.
```

### Social Media Caption Writer
```
Based on the image or content on this screen, write 3 different social media captions:
1. Professional/Business tone
2. Casual/Friendly tone
3. Funny/Entertaining tone

Keep each under 280 characters.
```

### Debugging Assistant
```
Look at the code and error message on this screen.
1. Identify what's causing the error
2. Explain why it's happening
3. Provide the corrected code
4. Explain what you changed

Use simple language.
```

### Design Feedback
```
Analyze the design/layout visible on this screen.
Comment on:
- Color scheme
- Typography
- Layout and spacing
- User experience
- Accessibility

Give 3 specific suggestions for improvement.
```

---

## Advanced Tips

### Chaining Tasks
You can ask the AI to do multiple things in one prompt:
```
1. Translate this text to English
2. Then summarize it in 3 bullet points
3. Then suggest a catchy title
```

### Conditional Instructions
```
If this is a code file: review it for bugs
If this is text: check grammar
If this is data: create a summary table
```

### Format Control
```
Return your response ONLY as a JSON object with these fields:
{
  "summary": "...",
  "key_points": ["...", "..."],
  "action_needed": true/false
}
```

---

## Common Questions

**Q: How many custom prompts can I create?**  
A: Unlimited! Create as many as you need.

**Q: Can I share prompts with others?**  
A: Yes! Just copy the text from the "Prompt Instructions" box and share it.

**Q: Do prompts use more API credits?**  
A: No, all prompts cost the same (~$0.01-0.05 per capture).

**Q: Can prompts access the internet?**  
A: No, they only see what's on your screen.

**Q: Can I have multiple active prompts?**  
A: No, only one prompt is active at a time. Click to switch.

---

## You're Now a Prompt Expert!

Go create some custom prompts that make your workflow easier!

**Remember:** The better your instructions, the better the AI's output. Don't be afraid to experiment!
