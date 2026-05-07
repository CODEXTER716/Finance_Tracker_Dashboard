# 💰 Finance Dashboard API

A **production-ready REST API** for personal finance management, built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. Features Role-Based Access Control (RBAC), full CRUD operations, analytics, and live deployment on Render.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-336791?style=flat&logo=postgresql)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Live Demo

**API Base URL:** `https://finance-tracker-shams.onrender.com`  
**Interactive Docs (Swagger UI):** `https://finance-tracker-shams.onrender.com/docs`  
**ReDoc:** `https://finance-tracker-shams.onrender.com/redoc`

> To test the API, open `/docs` and set the `x-mock-role` header to `Admin`, `Analyst`, or `Viewer`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Database (Production) | PostgreSQL via Railway |
| Database (Local Dev) | SQLite (zero setup) |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Deployment | Render (free tier) |
| Docs | Swagger UI + ReDoc (auto-generated) |

---

## ✨ Features

- ✅ **Full CRUD** — Create, Read, Update, Delete financial records
- ✅ **Role-Based Access Control (RBAC)** — Admin / Analyst / Viewer roles
- ✅ **Advanced Filtering** — Filter by type, category, date range
- ✅ **Pagination** — `skip` and `limit` query params on all list endpoints
- ✅ **Analytics** — Summary endpoint with income, expenses, net balance, category totals
- ✅ **Per-user Analytics** — Financial breakdown by individual user
- ✅ **User Management** — Create users, activate/deactivate accounts
- ✅ **Auto Docs** — Swagger UI at `/docs`, ReDoc at `/redoc`
- ✅ **PostgreSQL Ready** — Switches automatically between SQLite (local) and PostgreSQL (production)

---

## 🔐 Role-Based Access Control

| Endpoint | Viewer | Analyst | Admin |

| GET /records/ | ✅ | ✅ | ✅ |
| GET /summary/ | ✅ | ✅ | ✅ |
| POST /records/ | ❌ | ✅ | ✅ |
| PUT /records/{id} | ❌ | ❌ | ✅ |
| DELETE /records/{id} | ❌ | ❌ | ✅ |
| GET /users/ | ❌ | ✅ | ✅ |
| PUT /users/{id}/status | ❌ | ❌ | ✅ |

> Set the role via the `x-mock-role` HTTP header on each request.

---

## API Endpoints

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root — confirms API is running |
| GET | `/health` | Health check with timestamp |

### Users
| Method | Endpoint | Description |
|---|---|---|
| POST | `/users/` | Create new user |
| GET | `/users/` | List all users (Admin/Analyst) |
| GET | `/users/{id}` | Get user by ID |
| PUT | `/users/{id}/status` | Activate/deactivate user (Admin) |

### Records
| Method | Endpoint | Description |
|---|---|---|
| POST | `/records/` | Create record (Admin/Analyst) |
| GET | `/records/` | List records with filters + pagination |
| GET | `/records/{id}` | Get single record |
| PUT | `/records/{id}` | Update record (Admin) |
| DELETE | `/records/{id}` | Delete record (Admin) |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/summary/` | Global income/expense/balance summary |
| GET | `/summary/by-user/{id}` | Per-user financial summary |

---

## ⚙️ Local Setup (5 minutes)

### 1. Clone the repo
```bash
git clone https://github.com/CODEXTER716/Finance_Tracker_Dashboard.git
cd Finance_Tracker_Dashboard
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment (optional for local)
```bash
# Copy the example env file
cp .env.example .env
# For local dev, SQLite is used automatically — no changes needed
```

### 5. Run the server
```bash
uvicorn main:app --reload
```

### 6. Open docs
Visit: **http://127.0.0.1:8000/docs**

---

## ☁️ Deployment (Render + Railway)

### Database — Railway (Free PostgreSQL)
1. Sign up at [railway.app](https://railway.app)
2. New Project → Add PostgreSQL
3. Copy the `DATABASE_URL` from the PostgreSQL service

### API Server — Render (Free)
1. Sign up at [render.com](https://render.com)
2. New → Web Service → Connect your GitHub repo
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `DATABASE_URL` = your Railway URL
5. Deploy → get your live URL!

---

## 📁 Project Structure

```
finance-tracker/
├── main.py              # FastAPI app — all routes, models, schemas
├── requirements.txt     # Python dependencies
├── Procfile             # Render deployment config
├── .env.example         # Environment variable template
├── .gitignore           # Excludes .env, DB files, cache
└── README.md            # This file
```

---

## 👨‍💻 Author

**Shams Tabrej Alam**  
B.Tech Information Technology @ Dr. B.C. Roy Engineering College  
[GitHub](https://github.com/CODEXTER716) · [LinkedIn](https://linkedin.com/in/shams-tabrej-889b57291)

---

## 📄 License

MIT License — free to use, modify and share.
