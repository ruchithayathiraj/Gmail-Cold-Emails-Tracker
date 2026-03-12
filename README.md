# 📧 Gmail Cold Email Tracker + Follow-up Drafter
### Python Automation Tool | Personal Portfolio Project

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Gmail API](https://img.shields.io/badge/Gmail-API-red)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Author](https://img.shields.io/badge/Author-Ruchitha%20Yathirajulu-teal)

---

## 📌 What This Tool Does

A Python automation script that connects to your **real Gmail account** and:

1. 📬 **Scans your Sent folder** for cold recruiter/job outreach emails
2. 🔍 **Checks every thread** for replies — did they respond?
3. 🚨 **Flags emails with no reply** after 3 days
4. ✉️ **Auto-drafts follow-up emails** saved directly to your Gmail Drafts
5. 📊 **Prints a summary report** — total sent, replied, pending, drafted

---

## 💡 Why I Built This

As a job seeker sending dozens of cold emails to hiring managers/recruiters, manually tracking replies and writing follow-ups is time consuming. This tool automates the entire process which saves time and ensures no opportunity slips through the cracks.

> I started actively to use this tool in my own job search. 🎯

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.4+ |
| Gmail Integration | Gmail API (Google Cloud) |
| Authentication | OAuth 2.0 |
| Email Parsing | Python `email`, `base64`, `re` |
| Date Handling | Python `datetime` |

---

## 📂 Project Structure

```
Gmail-Cold-Email-Tracker/
├── gmail_tracker.py       ← Main script
├── requirements.txt       ← Python dependencies
├── .gitignore             ← Keeps credentials off GitHub
└── README.md              ← You are here
```

> ⚠️ `credentials.json` and `token.json` are NOT included — see setup instructions below.

---

## ⚙️ Setup Instructions

### Step 1 — Clone the repo
```bash
git clone https://github.com/ruchithayathiraj/Gmail-Cold-Email-Tracker
cd Gmail-Cold-Email-Tracker
```
### Step 3 - Check for pyton version (If you see Python 3.8+ you're good, or else download from python.org)
```bash
python --version
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Enable Gmail API (one-time setup)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project → name it `gmail-tracker`
3. Go to **APIs & Services → Search `Gmail API` → **Enable**
4. Go to **APIs & Services → OAuth consent screen**
   - Choose **External** → fill App name + your email → Save
   - Scroll to **Test Users** → add your Gmail → Save
5. Go to **Credentials → + Create Credentials → OAuth 2.0 Client ID**
   - Type: **Desktop App** → Download JSON
   - Rename downloaded file to `credentials.json`
   - Place it in the project folder

### Step 4 — Run the script
```bash
python gmail_tracker.py
```

**First run:** Browser opens → log in → click Allow → done!
**Future runs:** Runs automatically using saved `token.json`

---

## 📊 Sample Output

```
═══════════════════════════════════════════════════════
  Gmail Cold Email Tracker + Follow-up Drafter
  by Ruchitha Yathirajulu
═══════════════════════════════════════════════════════

✅ Gmail authenticated successfully

📬 Scanning your Sent folder for recruiter emails...
   Found 12 recruiter/job emails in Sent folder

🔍 Checking for replies...
   ✅ Replied:          4
   ⏳ Awaiting reply:   5
   🚨 Need follow-up:  3 (no reply after 7+ days)

✉️  Creating 3 follow-up draft(s) in Gmail...
  ✅ Draft created → Application Interest - BA Role at RBC...
  ✅ Draft created → Application Interest - Data Analyst at TD...
  ✅ Draft created → Application Interest - Project Analyst...

═══════════════════════════════════════════════════════
  📊 COLD EMAIL CAMPAIGN SUMMARY
═══════════════════════════════════════════════════════
  Total recruiter emails sent  : 12
  ✅ Received a reply          : 4 (33.3% reply rate)
  ⏳ Awaiting reply (<7 days)  : 5
  🚨 Need follow-up (7+ days)  : 3
  ✉️  Follow-up drafts created  : 3
═══════════════════════════════════════════════════════
```

---

## 🔧 Customisation

Open `gmail_tracker.py` and edit these settings at the top:

```python
# Change follow-up delay (default: 7 days)
FOLLOWUP_AFTER_DAYS = 3

# Add your own subject line keywords
RECRUITER_SUBJECT_KEYWORDS = [
    "application interest",
    "application interest -",
    "job", "hiring", "role" ...
]

# Update your name and signature
YOUR_NAME = "Your Name"
```

---

## 🔒 Privacy & Security

- **No data is stored** — emails are read in memory only, never saved to disk
- **credentials.json and token.json are excluded** from GitHub via `.gitignore`
- **OAuth 2.0** means your Gmail password is never accessed or stored by this script
- Revoke access anytime at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## 👩‍💻 About the Author

**Ruchitha Yathirajulu** — Business Analyst | Data Analyst | Project Analyst

- 🎓 M.Eng. ECE — University of Ottawa
- 💼 Former BSA Intern — Alberta Investment Management Corporation (AIMCo)
- 📜 PMP (In Progress) | PL-300 | SQL Associate | Alteryx Core
- 📍 Ottawa, Canada — Open to relocate
- 🔗 [LinkedIn](https://www.linkedin.com/in/ruchitha-yathirajulu-b87555191/)
- 🌐 [Portfolio](https://ruchithayathiraj.github.io)
- 📧 yathirajuluruchitha@gmail.com

---

*Personal portfolio project — built to solve a real job-hunting problem.*
