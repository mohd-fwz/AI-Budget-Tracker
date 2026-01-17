# Budget Tracker - Full Stack Application

A personal finance management platform with Flask backend, React frontend, and AI-powered insights.

**No authentication required** - simplified for personal use with local SQLite database.

---

## 🚀 Quick Start

> **👉 New to this project? Start here: [START_HERE.md](START_HERE.md)**

Get it running in 10 minutes:
1. Install Python & Node.js
2. Get Groq API key (free)
3. Run backend and frontend
4. Start tracking expenses!

---

## 📁 Project Structure

```
main_el/
├── Backend (Flask API)
│   ├── app.py              # Main server
│   ├── routes/             # API endpoints
│   │   ├── expenses.py     # CRUD operations
│   │   ├── analytics.py    # Charts & stats
│   │   └── recommendations.py  # AI tips
│   ├── utils/
│   │   ├── categorizer.py  # AI categorization
│   │   └── csv_parser.py   # CSV import
│   ├── models.py           # Database schema
│   └── config.py           # Configuration
│
├── frontend/ (React App)
│   ├── src/
│   │   ├── components/     # Dashboard, Analytics, etc.
│   │   ├── services/       # API client
│   │   └── App.jsx         # Main routing
│   └── package.json
│
├── budget.db              # SQLite database (auto-created)
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables
```

---

## ✨ Features

### Core Features
- 💰 **Expense Tracking** - Add, view, filter, and delete expenses
- 📊 **Visual Analytics** - Charts showing spending by category and trends over time
- 📤 **CSV Import** - Upload bank statements for automatic transaction import
- 🤖 **AI Recommendations** - Get personalized savings tips powered by Groq AI
- 🏷️ **Auto-Categorization** - AI automatically categorizes expenses

### Technical Highlights
- **Backend**: Flask REST API with SQLite database
- **Frontend**: React + Vite + Tailwind CSS
- **No Auth**: Simplified for personal use (no login required)
- **AI**: Groq API (Mixtral model) for smart categorization
- **Charts**: Recharts library for beautiful visualizations
- **Local First**: All data stored locally in SQLite

---

## 🎯 Prerequisites

1. **Python 3.9+** - [Download](https://www.python.org/downloads/)
2. **Node.js 16+** - [Download](https://nodejs.org/)
3. **Groq API Key** (free) - [Get one](https://console.groq.com)

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **[START_HERE.md](START_HERE.md)** | **Complete setup guide - READ THIS FIRST** |
| [PROJECT_MAP.md](PROJECT_MAP.md) | Detailed code structure and file explanations |

---

## 🔧 Tech Stack

### Backend
- **Flask 3.0** - Web framework
- **SQLite** - Local database (no cloud setup needed)
- **SQLAlchemy 2.0** - ORM
- **Groq API** - AI-powered features
- **Built-in CSV module** - No pandas dependency

### Frontend
- **React 18** - UI library
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **React Router** - Client-side routing

---

## 🏃 Running Locally

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start server
python app.py
```

Backend runs at: http://localhost:5000

### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start dev server
npm run dev
```

Frontend runs at: http://localhost:5173

---

## 📡 API Endpoints

### Expenses
- `POST /api/expenses` - Add new expense
- `GET /api/expenses/<user_id>` - Get all expenses
- `DELETE /api/expenses/<id>` - Delete expense
- `POST /api/upload-statement` - Upload CSV file

### Analytics
- `GET /api/analytics/<user_id>` - Get spending analytics
  - Query params: `start_date`, `end_date`, `period`

### Recommendations
- `GET /api/recommendations/<user_id>` - Get AI recommendations
  - Query param: `days` (default: 30)

### Health
- `GET /health` - Server health check

**Note**: `<user_id>` is ignored in all endpoints (uses default user)

---

## 🗄️ Database Schema

### Expense Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key (auto-increment) |
| user_id | String | User identifier (default: "default-user") |
| amount | Decimal | Expense amount |
| category | String | Expense category |
| date | DateTime | Transaction date |
| description | String | Optional description |
| created_at | DateTime | Record creation timestamp |

### Supported Categories

- Groceries
- Entertainment
- Rent
- Transport
- Bills
- Shopping
- Healthcare
- Other

---

## 🤖 AI Features

### Auto-Categorization
The app uses Groq's Mixtral model to automatically categorize expenses based on their description and amount.

Example:
- "Walmart groceries" → Groceries
- "Uber ride" → Transport
- "Netflix" → Entertainment

### Smart Recommendations
Analyzes your spending patterns and provides:
- Overspending alerts by category
- Budget allocation suggestions
- Specific money-saving tips
- Spending trend insights

---

## 📦 Dependencies

### Backend (requirements.txt)
```txt
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.23
python-dateutil==2.8.2
python-dotenv==1.0.0
requests==2.31.0
gunicorn==21.2.0
werkzeug==3.0.1
```

### Frontend (package.json)
- react, react-dom
- react-router-dom
- axios
- recharts
- date-fns
- lucide-react (icons)
- tailwindcss

---

## 🔒 Security Notes

**Important**: This version has **no authentication** for simplicity. It's designed for:
- Personal use on your local machine
- Learning and development
- Single-user environments

**Not suitable for**:
- Multi-user environments
- Production deployment with public access
- Storing sensitive financial data in shared environments

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Delete database and restart
rm budget.db
python app.py
```

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```

### CORS errors
Check `.env` has `CORS_ORIGINS=*` and restart backend

### AI features not working
Verify `GROQ_API_KEY` in `.env` is valid

---

## 📖 Learn More

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Docs](https://www.sqlalchemy.org/)
- [Groq API Docs](https://console.groq.com/docs)
- [Tailwind CSS](https://tailwindcss.com/)

---

## 🎯 Project Goals

This project demonstrates:
- ✅ Full-stack development (Python + JavaScript)
- ✅ RESTful API design
- ✅ Database modeling with SQLAlchemy
- ✅ AI integration (Groq)
- ✅ Modern React patterns (hooks, context)
- ✅ CSV parsing and data processing
- ✅ Data visualization
- ✅ Responsive UI design

---

## 📄 License

This project is open source and available for educational purposes.

---

**Built with ❤️ using Flask, React, and AI**
