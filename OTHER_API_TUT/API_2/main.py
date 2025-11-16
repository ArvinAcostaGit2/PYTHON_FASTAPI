# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel # New Import
import sqlite3
import time
from typing import List, Dict, Any
import uvicorn

# --- Pydantic Model (NEW) ---
# Defines the required structure for incoming JSON data
class EmployeeBase(BaseModel):
    eid: str
    name: str

# --- Setup ---
BASE_DIR = Path(__file__).resolve().parent
# 1. Update: Point Jinja2Templates to the 'templates' subdirectory
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 2. Update: Define the database folder and full path
DB_FOLDER = BASE_DIR / "db"
DB_FOLDER.mkdir(exist_ok=True)
DATABASE_PATH = DB_FOLDER / "crud_fastapi.db"

app = FastAPI()

# --- Database Functions (No Change) ---

def get_db_connection():
    """Establishes and returns a SQLite database connection."""
    # 3. Update: Connect using the full database path
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Creates the 'employees' table if it doesn't exist."""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                idx INTEGER PRIMARY KEY AUTOINCREMENT,
                eid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                timestamp REAL
            );
        """)
        conn.commit()
    finally:
        conn.close()

# Initialize database table on startup
create_table()

# --- FastAPI Endpoints ---

# READ (No Change)
@app.get("/", response_class=HTMLResponse)
async def read_employees(request: Request, search: str = None):
    conn = get_db_connection()
    employees = []
    
    try:
        if search:
            cursor = conn.execute(
                "SELECT * FROM employees WHERE eid LIKE ? OR name LIKE ? ORDER BY idx DESC",
                (f"%{search}%", f"%{search}%")
            )
        else:
            cursor = conn.execute("SELECT * FROM employees ORDER BY idx DESC")
            
        employees = cursor.fetchall()
    finally:
        conn.close()

    employee_list = []
    for emp in employees:
        employee_dict = dict(emp)
        employee_dict['timestamp_str'] = time.strftime(
            '%Y-%m-%d %H:%M:%S', 
            time.localtime(employee_dict['timestamp'])
        )
        employee_list.append(employee_dict)
        
    return TEMPLATES.TemplateResponse(
        "index.html", 
        {"request": request, "employees": employee_list, "search_term": search}
    )

# CREATE (UPDATED: Accepts EmployeeBase Pydantic model)
@app.post("/add")
async def add_employee(employee: EmployeeBase): # FastAPI automatically expects JSON body validated by EmployeeBase
    



    # ...
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT eid FROM employees WHERE eid = ?", (employee.eid,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, 
                detail=f"Employee with EID '{employee.eid}' already exists."
            )

        conn.execute(
            "INSERT INTO employees (eid, name, timestamp) VALUES (?, ?, ?)",
            (employee.eid, employee.name, time.time())
        )
        conn.commit()
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()
    
    # Return a JSON response for AJAX success
    return {"message": "Employee added successfully"}

# UPDATE (UPDATED: Accepts EmployeeBase Pydantic model)
@app.put("/update/{idx}") # Changed from POST to PUT (better REST practice for update)
async def update_employee(idx: int, employee: EmployeeBase):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT idx FROM employees WHERE eid = ? AND idx != ?", 
            (employee.eid, idx)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, 
                detail=f"EID '{employee.eid}' is already used by another employee."
            )

        cursor = conn.execute(
            "UPDATE employees SET eid = ?, name = ?, timestamp = ? WHERE idx = ? RETURNING idx",
            (employee.eid, employee.name, time.time(), idx)
        )
        if cursor.rowcount == 0:
             raise HTTPException(status_code=404, detail="Employee not found")

        


        conn.commit()
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()
        
    # Return a JSON response for AJAX success
    return {"message": "Employee updated successfully"}


# DELETE (UPDATED: Removed RedirectResponse, now returns JSON)
@app.delete("/delete/{idx}")
async def delete_employee(idx: int):
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM employees WHERE idx = ?", (idx,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Employee not found")
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()

    return {"message": "Employee deleted successfully"}

# --- Uvicorn Startup Block (No Change) ---
if __name__ == "__main__":
    # The arguments specify:
    # app: The FastAPI instance
    # host: Binds the server to all interfaces
    # port: Sets the server port
    # reload: Enables hot-reloading (helpful during development)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)