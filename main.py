from fastapi import FastAPI, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# 1. DATABASE SETUP (PostgreSQL for production, SQLite for local)
# ---------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finance_v3.db")

# Fix for Railway/Render PostgreSQL URL (they give postgres:// but SQLAlchemy needs postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------------------------------------
# 2. DATABASE MODELS
# ---------------------------------------------------------
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    records = relationship("FinancialRecordDB", back_populates="owner")


class FinancialRecordDB(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    record_type = Column(String, nullable=False)  # "Income" or "Expense"
    category = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("UserDB", back_populates="records")


Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# 3. PYDANTIC SCHEMAS
# ---------------------------------------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    role: str = Field(..., example="Admin")

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True

class RecordCreate(BaseModel):
    amount: float = Field(..., gt=0, example=1500.00)
    record_type: str = Field(..., example="Income")
    category: str = Field(..., example="Salary")
    description: Optional[str] = Field(None, example="Monthly salary")

class RecordOut(BaseModel):
    id: int
    user_id: int
    amount: float
    record_type: str
    category: str
    description: Optional[str]
    date: datetime

    class Config:
        from_attributes = True

class UserStatusUpdate(BaseModel):
    is_active: int = Field(..., ge=0, le=1, example=1)

class SummaryOut(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    category_totals: dict
    total_records: int

# ---------------------------------------------------------
# 4. FASTAPI APP
# ---------------------------------------------------------
app = FastAPI(
    title="💰 Finance Dashboard API",
    description="""
## Personal Finance Tracker — REST API

A production-ready backend API for managing personal finances with **Role-Based Access Control (RBAC)**.

### Roles:
- **Admin** — Full access (create, read, update, delete)
- **Analyst** — Read access + summary analytics
- **Viewer** — Read-only access

### How to use:
Set the `x-mock-role` header to `Admin`, `Analyst`, or `Viewer` when making requests.

Built by **Shams Tabrej Alam** | B.Tech IT @ Dr. B.C. Roy Engineering College
    """,
    version="2.0.0",
    contact={
        "name": "Shams Tabrej Alam",
        "url": "https://github.com/CODEXTER716",
    }
)

# ---------------------------------------------------------
# 5. DEPENDENCIES
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_role(x_mock_role: str = Header(default="Viewer")):
    valid_roles = ["Admin", "Analyst", "Viewer"]
    if x_mock_role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    return x_mock_role

# ---------------------------------------------------------
# 6. ROOT ROUTE
# ---------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    return {
        "message": "💰 Finance Dashboard API is running!",
        "version": "2.0.0",
        "docs": "/docs",
        "author": "Shams Tabrej Alam"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# ---------------------------------------------------------
# 7. USER ROUTES
# ---------------------------------------------------------
@app.post("/users/", response_model=UserOut, tags=["Users"], status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user with a role. No auth required for registration."""
    if user.role not in ["Admin", "Analyst", "Viewer"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be one of: Admin, Analyst, Viewer"
        )
    existing = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    db_user = UserDB(username=user.username, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/", response_model=List[UserOut], tags=["Users"])
def get_all_users(
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Get all users. Admins and Analysts only."""
    if role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot view user list.")
    return db.query(UserDB).all()


@app.get("/users/{user_id}", response_model=UserOut, tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db), role: str = Depends(get_user_role)):
    """Get a specific user by ID."""
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}/status", tags=["Users"])
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Activate or deactivate a user. Admins only."""
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can manage user status.")

    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = status_update.is_active
    db.commit()
    status_text = "Active" if user.is_active == 1 else "Inactive"
    return {"message": f"User '{user.username}' is now {status_text}"}

# ---------------------------------------------------------
# 8. FINANCIAL RECORD ROUTES
# ---------------------------------------------------------
@app.post("/records/", response_model=RecordOut, tags=["Records"], status_code=201)
def create_record(
    record: RecordCreate,
    user_id: int = Query(..., description="ID of the user creating this record"),
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Create a new financial record. Admins and Analysts only."""
    if role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create records.")
    if record.record_type not in ["Income", "Expense"]:
        raise HTTPException(status_code=400, detail="record_type must be 'Income' or 'Expense'")

    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive.")

    db_record = FinancialRecordDB(
        user_id=user_id,
        amount=record.amount,
        record_type=record.record_type,
        category=record.category,
        description=record.description
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/records/", response_model=List[RecordOut], tags=["Records"])
def get_records(
    record_type: Optional[str] = Query(None, example="Income"),
    category: Optional[str] = Query(None, example="Salary"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Get all records with optional filters and pagination. All roles can access."""
    query = db.query(FinancialRecordDB)

    if record_type:
        query = query.filter(FinancialRecordDB.record_type == record_type)
    if category:
        query = query.filter(FinancialRecordDB.category == category)
    if start_date:
        query = query.filter(FinancialRecordDB.date >= start_date)
    if end_date:
        query = query.filter(FinancialRecordDB.date <= end_date)

    return query.offset(skip).limit(limit).all()


@app.get("/records/{record_id}", response_model=RecordOut, tags=["Records"])
def get_record(record_id: int, db: Session = Depends(get_db), role: str = Depends(get_user_role)):
    """Get a single record by ID."""
    record = db.query(FinancialRecordDB).filter(FinancialRecordDB.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.put("/records/{record_id}", response_model=RecordOut, tags=["Records"])
def update_record(
    record_id: int,
    record_update: RecordCreate,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Update a financial record. Admins only."""
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can update records.")

    db_record = db.query(FinancialRecordDB).filter(FinancialRecordDB.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")

    db_record.amount = record_update.amount
    db_record.record_type = record_update.record_type
    db_record.category = record_update.category
    db_record.description = record_update.description
    db.commit()
    db.refresh(db_record)
    return db_record


@app.delete("/records/{record_id}", tags=["Records"])
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Delete a record. Admins only."""
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can delete records.")

    db_record = db.query(FinancialRecordDB).filter(FinancialRecordDB.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(db_record)
    db.commit()
    return {"message": f"Record {record_id} deleted successfully"}

# ---------------------------------------------------------
# 9. ANALYTICS / SUMMARY ROUTES
# ---------------------------------------------------------
@app.get("/summary/", response_model=SummaryOut, tags=["Analytics"])
def get_summary(db: Session = Depends(get_db), role: str = Depends(get_user_role)):
    """Returns income, expenses, net balance and category breakdown. All roles."""
    records = db.query(FinancialRecordDB).all()

    total_income = 0.0
    total_expenses = 0.0
    category_totals = {}

    for record in records:
        if record.record_type == "Income":
            total_income += record.amount
        elif record.record_type == "Expense":
            total_expenses += record.amount

        category_totals[record.category] = (
            category_totals.get(record.category, 0.0) + record.amount
        )

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(total_income - total_expenses, 2),
        "category_totals": {k: round(v, 2) for k, v in category_totals.items()},
        "total_records": len(records)
    }


@app.get("/summary/by-user/{user_id}", tags=["Analytics"])
def get_user_summary(
    user_id: int,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Returns financial summary for a specific user. Analysts and Admins only."""
    if role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot access user summaries.")

    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    records = db.query(FinancialRecordDB).filter(FinancialRecordDB.user_id == user_id).all()

    total_income = sum(r.amount for r in records if r.record_type == "Income")
    total_expenses = sum(r.amount for r in records if r.record_type == "Expense")

    return {
        "user": user.username,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(total_income - total_expenses, 2),
        "total_records": len(records)
    }
