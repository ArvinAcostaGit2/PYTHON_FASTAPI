# main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sqlite3
import time
from typing import List, Dict, Any
# Import uvicorn for self-running
import uvicorn







# --- Setup ---
BASE_DIR = Path(__file__).resolve().parent
# 1. Update: Point Jinja2Templates to the 'templates' subdirectory
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 2. Update: Define the database folder and full path
DB_FOLDER = BASE_DIR / "db"
DB_FOLDER.mkdir(exist_ok=True) # Create the 'db' folder if it doesn't exist
DATABASE_PATH = DB_FOLDER / "crud_fastapi.db"

app = FastAPI()

# --- Database Functions ---

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

# --- FastAPI Endpoints (No changes needed to endpoint logic) ---

@app.get("/", response_class=HTMLResponse)
async def read_employees(request: Request, search: str = None):
    # ... (function body remains the same, just uses the new get_db_connection)
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

# CREATE - Upon Client Page Submit the Form
@app.post("/add", response_class=RedirectResponse)
async def add_employee(
    request: Request,
    eid: str = Form(...),
    name: str = Form(...)
):
    # ... (function body remains the same, uses the new get_db_connection)
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT eid FROM employees WHERE eid = ?", (eid,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, 
                detail=f"Employee with EID '{eid}' already exists."
            )

        conn.execute(
            "INSERT INTO employees (eid, name, timestamp) VALUES (?, ?, ?)",
            (eid, name, time.time())
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


    return RedirectResponse(url="/", status_code=303)

# UPDATE 
@app.post("/update/{idx}", response_class=RedirectResponse)
async def update_employee(
    idx: int,
    request: Request,
    eid: str = Form(...),
    name: str = Form(...)
):
    # ... (function body remains the same, uses the new get_db_connection)
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT idx FROM employees WHERE eid = ? AND idx != ?", 
            (eid, idx)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, 
                detail=f"EID '{eid}' is already used by another employee."
            )

        conn.execute(
            "UPDATE employees SET eid = ?, name = ?, timestamp = ? WHERE idx = ?",
            (eid, name, time.time(), idx)
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
   

    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{idx}", response_class=RedirectResponse)
async def delete_employee(idx: int):
    # ... (function body remains the same, uses the new get_db_connection)
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM employees WHERE idx = ?", (idx,))
        conn.commit()
    

    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()

    return RedirectResponse(url="/", status_code=303)

# --- Uvicorn Startup Block (No Change) ---
if __name__ == "__main__":
    # The arguments specify:
    # app: The FastAPI instance
    # host: Binds the server to all interfaces
    # port: Sets the server port
    # reload: Enables hot-reloading (helpful during development)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)