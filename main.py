from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime
from typing import Optional
import traceback

# ---------------------------------------------------------
# 1. DATABASE SETUP (SQLite)
# ---------------------------------------------------------
# Changed to v3 to guarantee a perfectly clean database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./finance_v3.db" 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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

    records = relationship("FinancialRecordDB", back_populates="owner")

class FinancialRecordDB(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    amount = Column(Float, nullable=False)
    record_type = Column(String, nullable=False) 
    category = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String)

    owner = relationship("UserDB", back_populates="records")

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# 3. PYDANTIC SCHEMAS
# ---------------------------------------------------------
class UserCreate(BaseModel):
    username: str
    role: str

class RecordCreate(BaseModel):
    amount: float
    record_type: str
    category: str
    description: Optional[str] = None
## new line is_active

class UserStatusUpdate(BaseModel):
    is_active: int  # 1 for active, 0 for inactive



# ---------------------------------------------------------
# 4. FASTAPI APP
# ---------------------------------------------------------
app = FastAPI(title="Finance Dashboard API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_role(x_mock_role: str = Header(default="Viewer")):
    valid_roles = ["Admin", "Analyst", "Viewer"]
    if x_mock_role not in valid_roles:
        raise HTTPException(status_code=400, detail="Invalid role in header")
    return x_mock_role

# ---------------------------------------------------------
# 5. API ROUTES
# ---------------------------------------------------------

# NOTE: Removed response_model temporarily to bypass any validation crashes
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        if user.role not in ["Admin", "Analyst", "Viewer"]:
            raise HTTPException(status_code=400, detail="Role must be Admin, Analyst, or Viewer")
        
        existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
            
        db_user = UserDB(username=user.username, role=user.role)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Manually returning the data to ensure it doesn't crash on the way out
        return {
            "id": db_user.id,
            "username": db_user.username,
            "role": db_user.role,
            "is_active": db_user.is_active,
            "message": "SUCCESS! The database works!"
        }
        
    except Exception as e:
        # If it crashes, this will print the EXACT reason to your browser!
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"CRASH REPORT: {str(e)}")


@app.post("/records/")
def create_record(
    record: RecordCreate, 
    user_id: int, 
    db: Session = Depends(get_db), 
    role: str = Depends(get_user_role)
):
    if role == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create records.")
    
    if record.record_type not in ["Income", "Expense"]:
        raise HTTPException(status_code=400, detail="Type must be Income or Expense")

    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

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
    
    return {
        "id": db_record.id,
        "user_id": db_record.user_id,
        "amount": db_record.amount,
        "category": db_record.category
    }







@app.get("/records/")
def get_records(
    record_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db), 
    role: str = Depends(get_user_role)
):
    """Fetches all records. Allows filtering by type, category, or date range. Accessible by all roles."""
    query = db.query(FinancialRecordDB)
    
    if record_type:
        query = query.filter(FinancialRecordDB.record_type == record_type)
    if category:
        query = query.filter(FinancialRecordDB.category == category)
    if start_date:
        query = query.filter(FinancialRecordDB.date >= start_date)
    if end_date:
        query = query.filter(FinancialRecordDB.date <= end_date)
        
    records = query.all()
    return records


## CRUD OPERATION

@app.put("/records/{record_id}")
def update_record(
    record_id: int, 
    record_update: RecordCreate, 
    db: Session = Depends(get_db), 
    role: str = Depends(get_user_role)
):
    """Updates an existing record. Admins only."""
    # RBAC LOGIC: Only Admins can update
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can update records.")
        
    # Find the record
    db_record = db.query(FinancialRecordDB).filter(FinancialRecordDB.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    # Apply the updates
    db_record.amount = record_update.amount
    db_record.record_type = record_update.record_type
    db_record.category = record_update.category
    db_record.description = record_update.description
    
    db.commit()
    db.refresh(db_record)
    
    return {"message": "Record updated successfully", "id": db_record.id}

## admin can activate / deactivate user


@app.put("/users/{user_id}/status")
def update_user_status(
    user_id: int, 
    status_update: UserStatusUpdate, 
    db: Session = Depends(get_db), 
    role: str = Depends(get_user_role)
):
    """Activates or deactivates a user. Admins only."""
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can manage user status.")
        
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db_user.is_active = status_update.is_active
    db.commit()
    
    status_text = "Active" if db_user.is_active == 1 else "Inactive"
    return {"message": f"User {db_user.username} is now {status_text}"}


@app.delete("/records/{record_id}")
def delete_record(
    record_id: int, 
    db: Session = Depends(get_db), 
    role: str = Depends(get_user_role)
):
    """Deletes a record. Admins only."""
    # RBAC LOGIC: Only Admins can delete
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can delete records.")
        
    # Find the record
    db_record = db.query(FinancialRecordDB).filter(FinancialRecordDB.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    # Delete it
    db.delete(db_record)
    db.commit()
    
    return {"message": f"Record {record_id} deleted successfully"}



# --- DASHBOARD SUMMARY ROUTE ---
@app.get("/summary/")
def get_summary(db: Session = Depends(get_db), role: str = Depends(get_user_role)):
    """Returns summary statistics for the dashboard. Accessible by all valid roles."""
    records = db.query(FinancialRecordDB).all()
    
    total_income = 0.0
    total_expenses = 0.0
    category_totals = {}
    
    for record in records:
        if record.record_type == "Income":
            total_income += record.amount
        elif record.record_type == "Expense":
            total_expenses += record.amount
            
        if record.category not in category_totals:
            category_totals[record.category] = 0.0
        category_totals[record.category] += record.amount
        
    net_balance = total_income - total_expenses
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": net_balance,
        "category_totals": category_totals
    }
















