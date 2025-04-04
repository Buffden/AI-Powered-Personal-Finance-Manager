# 💰 AI-Powered Personal Finance Manager

An intelligent finance web application that allows users to securely connect bank accounts, auto-categorize expenses, track budgets, receive bill reminders, and gain insightful recommendations powered by AI.

---

## 🚀 Features

### 🔐 Banking API Integration
- Link multiple bank accounts via **Plaid**
- Fetch transaction history in real-time

### 🧠 AI-Powered Financial Analysis
- Auto-categorize transactions with smart category detection
- AI-powered budget suggestions based on spending patterns
- AI chatbot for financial insights and budgeting tips
- Receipt scanning & extraction using **ChatGPT Vision** (optional upgrade)

### 📊 Budget Tracking & Insights
- Set monthly spending limits per category
- Smart budget suggestions based on historical spending
- Interactive visualizations comparing budget vs. actual spending
- Get alerts when nearing/exceeding limits
- Visualize expenses by category & time

### ⏰ Bill Reminders
- Set recurring bill reminders
- UI & email-based alerts before due dates

### 📈 Analytics & Reports
- View daily/monthly spending trends
- Detect anomalies or spending spikes
- Exportable transaction tables

---

## 🧱 Tech Stack

| Layer        | Technology                      |
|--------------|----------------------------------|
| **Frontend** | Streamlit (Python), Altair (Visualizations) |
| **Backend**  | Flask REST API                   |
| **AI Layer** | OpenAI GPT (ChatGPT & Vision)    |
| **Banking**  | Plaid  API                       |
| **Database** | In-memory & AWS RDS              |
| **Deployment** | Docker + GitHub Actions + EC2 (planned) |

---

## 🗂️ Project Structure

```
AI-Powered-Personal-Finance-Manager/
├── backend/
│   ├── flask_app.py
│   ├── routes/
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
├── .env
└── requirements.txt
```

---

## 🧪 How to Run Locally

### 1. Clone the repo:
```bash
git clone https://github.com/your-username/AI-Powered-Personal-Finance-Manager.git
cd AI-Powered-Personal-Finance-Manager
```

### 2. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Add Plaid API Keys in `.env`
```
PLAID_CLIENT_ID=your-client-id
PLAID_SECRET=your-sandbox-secret
```

### 4. Run Backend
```bash
python3 backend/flask_app.py
```

### 5. Run Frontend
```bash
streamlit run frontend/streamlit_app.py
```

---

## 📦 Future Enhancements
- ✅ AWS EC2-based deployment
- ✅ PostgreSQL/AWS RDS for persistent storage
- ✅ OAuth integration for secure logins
- ✅ Premium tier: Investment tracking, savings goals
- ✅ MLOps pipeline for continual AI learning

---

## 👥 Contributors
- **Harshwardhan Patil** – Frontend, Dashboard, CI/CD, Plaid, OpenAI API
- **Sanjana** – Backend Integrations, Alert System
- **Matthew** – AI/ML & ChatGPT integration

---

## 📬 Contact
For collaboration, raise an issue or reach out via GitHub discussions!

---

