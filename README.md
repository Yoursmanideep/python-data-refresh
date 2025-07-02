# Automated Python Data Pipeline with GitHub Actions & MySQL

Welcome to the Automated Python Data Pipeline — a slick, hands-off solution that fetches, processes, and stores data in a MySQL database, all powered by GitHub Actions. This setup runs like clockwork every day at 8:00 AM IST (2:30 AM UTC), keeping your data fresh without you lifting a finger. 🌟

---

## 📁 Project Structure

Here’s how the project is laid out — clean and simple:

![image](https://github.com/user-attachments/assets/8199ff64-af91-463d-85ae-dc928a4a9ab8)

---

## ⚙️ What’s the Point?

This pipeline’s got one job — and it does it well:

- ✅ Automates Everything: Runs three Python scripts back-to-back
- 📦 Updates Your Data: Plugs fresh info into MySQL daily
- ⏰ Set It and Forget It: Scheduled to run at 8:00 AM IST
- 🔐 Stays Secure: Uses GitHub Actions + Secrets for safe, cloud-based automation

---

## 🚀 How It All Comes Together

### 🔄 GitHub Actions: The Brains of the Operation

The workflow lives at .github/workflows/run-python.yml. Here’s what it does:

#### 🔁 When it Runs:
- Automatically every day at 2:30 AM UTC (8:00 AM IST)
- Manually on demand via the GitHub Actions tab

#### ⚙️ What it Does:
1. Checks out your repository
2. Sets up Python 3.10
3. Installs dependencies from requirements.txt
4. Runs:
   - script1.py
   - script2.py
   - script3.py

---

## 📥 What You’ll Need (Dependencies)

All required libraries live in requirements.txt, including:

- pandas — Data wrangling champ
- requests — For grabbing data from APIs
- mysql-connector-python — MySQL’s best friend
- yfinance — For financial data (optional)

These get installed fresh on every workflow run.

---

## 🔐 Keeping MySQL Safe

No hardcoded credentials here! We use GitHub Secrets to lock things down:

- DB_HOST – Where your database lives
- DB_USER – Who’s logging in
- DB_PASS – The password
- DB_NAME – Which database to hit

Your scripts use these safely like this:

import os
import mysql.connector

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME")
)

Note: You’ll need a MySQL database hosted somewhere accessible (e.g., AWS RDS, Google Cloud SQL, or a local server with a public IP). GitHub Actions runs in the cloud, so your DB must be reachable!

---

## 🧪 Test It Yourself

Want to kick the tires? Here’s how to run it manually:

1. Go to your GitHub repo
2. Click the Actions tab
3. Choose "Run Python Scripts Daily"
4. Click Run workflow

Boom — instant refresh, perfect for testing or quick reruns.

---

## 📊 What You Get

This pipeline handles it all:

- Fetch: Pulls data from APIs, files, or other sources
- Process: Cleans and transforms that data
- Store: Inserts or updates data into your MySQL database

Track it all via the workflow logs in the Actions tab.

![image](https://github.com/user-attachments/assets/e82c1934-0d18-416b-a6e6-63ace8487cf0)


---

## 📌 Quick Links

Replace yourusername with your GitHub username:

- script1.py: https://github.com/yoursmanideep/python-data-refresh/blob/main/script1.py
- script2.py: https://github.com/yoursmanideep/python-data-refresh/blob/main/script2.py
- script3.py: https://github.comyoursmanideep/python-data-refresh/blob/main/script3.py
- Workflow: https://github.com/yoursmanideep/python-data-refresh/blob/main/.github/workflows/run-python.yml

---

## ✅ Project Status

- ✅ Scripts are locked and loaded
- ✅ MySQL integration secured with GitHub Secrets
- ✅ Daily automation is active
- ✅ Logs available for monitoring/debugging
- ✅ Manual execution enabled

---

## 🤝 Got Ideas?

Maintained by Manideep.  
Feel free to fork, clone, star, or open a pull request if you’d like to contribute.

---

## 📅 What’s Next?

- Daily Runs: ✅ Complete
- Error Handling: 🔄 In progress
- Email/Slack Alerts: 🔄 Upcoming
- PostgreSQL Support: ⏳ Maybe later

---

## 📋 How to Get Started

1. Clone this repo or use it directly on GitHub
2. Drop your scripts (script1.py, script2.py, script3.py) in the root
3. Add required libraries to requirements.txt
4. Set these GitHub Secrets:
   - DB_HOST
   - DB_USER
   - DB_PASS
   - DB_NAME
5. Double-check .github/workflows/run-python.yml for accuracy
6. Watch the workflow go in the Actions tab

---

## 💡 Pro Tips

- Keep scripts small and modular
- Never hardcode secrets — always use environment variables
- Check logs often to catch issues early
- Manually test before relying solely on scheduling
- Troubleshooting: If the workflow fails, verify your MySQL server is online and the Secrets match your DB credentials!

---

## 📞 Let’s Chat

Got questions or want to collaborate?  
📧 Email: manideepagoodboy@gmail.com

---
