# Finance Dashboard Backend API

## Objective
A RESTful backend API built to manage financial records, user roles, permissions, and summary-level analytics for a Finance Dashboard system.

## Tech Stack
* **Framework:** FastAPI (Python)
* **Database:** SQLite (managed via SQLAlchemy ORM)
* **Data Validation:** Pydantic

## Assumptions & Tradeoffs
As per the assignment guidelines, the following reasonable assumptions and tradeoffs were made to focus on core logical structure and clean implementation:
1. **Mock Authentication:** Instead of a complex JWT token system, Role-Based Access Control (RBAC) is implemented via a simulated HTTP Header (`x-mock-role`). This successfully demonstrates policy checks and guards without the overhead of full session management.
2. **Database Choice:** SQLite was chosen for data persistence. It provides full relational database features (Foreign Keys, filtering, date querying) while allowing the project to remain highly portable and easy to run locally without installing an external database server like PostgreSQL.

## Features & Access Control Logic
The system enforces strict Role-Based Access Control (RBAC):
* **Viewer:** Can read records and dashboard summaries, but cannot create, update, or delete.
* **Analyst:** (Same as Viewer for this scope) Can read records and access insights.
* **Admin:** Full management access. Can create users, manage user activation status, and create, update, and delete financial records.

## Local Setup Instructions

**1. Navigate to the project folder:**
```bash
cd finance

## Create and activate a virtual environment:
python -m venv venv

# On Windows:
venv\Scripts\activate

## Install dependencies:

pip install fastapi uvicorn sqlalchemy pydantic

## Run the server:

uvicorn main:app --reload

View API Documentation:
Open your browser and navigate to: http://127.0.0.1:8000/docs to view the interactive Swagger UI and test the endpoints.

Core API Endpoints
User Management

POST /users/ - Create a new user (Assigns roles).

PUT /users/{id}/status - Activate or deactivate a user account (Admins only).

Financial Records

POST /records/ - Create a new financial record (Admins only).

GET /records/ - Fetch records. Supports advanced filtering (record_type, category, start_date, end_date) and pagination (skip, limit).

PUT /records/{id} - Update a record (Admins only).

DELETE /records/{id} - Delete a record (Admins only).

Analytics

GET /summary/ - Returns calculated total income, total expenses, net balance, and category-wise totals.
