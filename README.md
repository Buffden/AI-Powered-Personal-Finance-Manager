# 💰 AI-Powered Personal Finance Manager

An intelligent finance web application that allows users to securely connect bank accounts, auto-categorize expenses, track budgets, receive bill reminders, and gain insightful recommendations powered by AI.

---

## 🚀 Features

### 🔐 Banking API Integration
- Link multiple bank accounts via **Plaid**.
- Fetch transaction history in real-time.

### 🧠 AI-Powered Financial Analysis
- Auto-categorize transactions with smart category detection.
- AI-powered budget suggestions based on spending patterns.
- AI chatbot for financial insights and budgeting tips.
- Receipt scanning & extraction using **ChatGPT Vision** (optional upgrade).

### 📊 Budget Tracking & Insights
- Set monthly spending limits per category.
- Smart budget suggestions based on historical spending.
- Interactive visualizations comparing budget vs. actual spending.
- Get alerts when nearing/exceeding limits.
- Visualize expenses by category & time.

### ⏰ Bill Reminders
- Set recurring bill reminders.
- UI & email-based alerts before due dates.

### 📈 Analytics & Reports
- View daily/monthly spending trends.
- Detect anomalies or spending spikes.
- Exportable transaction tables.

---

## 🧱 Tech Stack

| Layer        | Technology                      |
|--------------|----------------------------------|
| **Frontend** | Streamlit (Python), Altair (Visualizations) |
| **Backend**  | Flask REST API                   |
| **AI Layer** | OpenAI GPT (ChatGPT & Vision)    |
| **Banking**  | Plaid API                        |
| **Database** | In-memory & AWS RDS              |
| **Deployment** | Docker + GitHub Actions + EC2 (planned) |

---

## 🗂️ Project Structure

```
AI-Powered-Personal-Finance-Manager/
├── backend/
│   ├── flask_app.py
│   ├── routes/
│   │   ├── ai_routes.py
│   │   ├── bill_routes.py
│   │   └── plaid_routes.py
│   └── utils/
│       ├── budget.py
│       ├── config.py
│       └── notifications.py
├── frontend/
│   ├── streamlit_app.py
│   ├── components/
│   │   └── charts.py
│   └── views/
│       ├── Home.py
│       ├── BudgetTracker.py
│       ├── BillReminders.py
│       ├── Insights.py
│       ├── AddBankAccount.py
│       └── Chatbot.py
├── tests/
│   ├── backend/
│   │   ├── test_flask_app.py
│   │   └── routes/
│   │       ├── test_bill_routes.py
│   │       └── test_plaid_routes.py
│   ├── frontend/
│   │   ├── test_streamlit_app.py
│   │   ├── playwright/
│   │   │   └── test_navigation.py
│   │   └── views/
│   │       ├── test_add_bank_account.py
│   │       ├── test_budget_tracker.py
│   │       └── test_chatbot.py
├── .env
├── requirements.txt
├── run_tests.py
├── startup_script.sh
└── startup_script.ps1
```

---

## 🧪 How to Run Locally

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/AI-Powered-Personal-Finance-Manager.git
cd AI-Powered-Personal-Finance-Manager
```

### 2. Add API Keys to `.env`
Create a `.env` file in the project root and add the following:
```
PLAID_CLIENT_ID=your-client-id
PLAID_SECRET=your-sandbox-secret
OPENAI_API_KEY=your-api-key
```

### 3. Run the Application

#### On Windows
Use the PowerShell script:
```powershell
.\startup_script.ps1
```

#### On Linux/Mac
Use the Bash script:
```bash
bash startup_script.sh
```

Both scripts will:
1. Activate the virtual environment.
2. Install the required dependencies.
3. Start the Flask backend.
4. Start the Streamlit frontend.
5. Automatically clean up the backend process when the frontend exits.

---

## 🧪 Running Tests

### 1. Set the `PYTHONPATH`
Before running the tests, ensure the `PYTHONPATH` is set to the project root directory:
```bash
set PYTHONPATH=. # Windows
export PYTHONPATH=. # Linux/Mac
```

### 2. Run Unit Tests with Coverage
To run the tests and measure code coverage:
```bash
coverage run --source=backend,frontend run_tests.py
```

### 3. View Coverage Report
To view the coverage report in the terminal:
```bash
coverage report
```

To generate an HTML coverage report:
```bash
coverage html
```
Open the `htmlcov/index.html` file in your browser to view a detailed coverage report.

---

## 🧪 Running GUI Tests

### Prerequisites
Ensure you have Playwright installed:
```bash
playwright install
```

### Running the GUI Tests
1. Start the application using the startup script:
   ```powershell
   .\startup_script.ps1 # windows
   bash startup_script.sh # linux/mac
   ```
2. In a separate terminal, run the Playwright-based GUI tests:
   ```bash
   pytest tests/frontend/playwright/test_navigation.py
   ```

These tests will:
1. Launch a headless browser.
2. Navigate through the Streamlit app.
3. Verify navigation and UI elements on each page.

---

## 📦 Future Enhancements
- ✅ AWS EC2-based deployment.
- ✅ PostgreSQL/AWS RDS for persistent storage.
- ✅ OAuth integration for secure logins.
- ✅ Premium tier: Investment tracking, savings goals.
- ✅ MLOps pipeline for continual AI learning.

---

## 👥 Contributors
- **Harshwardhan Patil** – Frontend, Dashboard, CI/CD, Plaid, OpenAI API.
- **Sanjana** – Backend Integrations, Alert System.
- **Matthew** – AI/ML & ChatGPT integration, Automation Testing, Debugging.

---

## 📬 Contact
For collaboration, raise an issue or reach out via GitHub discussions!

---

