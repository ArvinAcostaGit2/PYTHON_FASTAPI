# main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pyodbc # ⬅️ NEW: Used for MS SQL Server connection
import time
from typing import List, Dict, Any
import uvicorn

# --- Setup ---
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- MS SQL CONNECTION CONFIGURATION ---
# ⚠️ IMPORTANT: These must match your docker run command settings
SERVER = 'localhost'
DATABASE = 'mssql_server'
USERNAME = 'sa'
PASSWORD = '!@#$1qaZ' 
ODBC_DRIVER = '{ODBC Driver 17 for SQL Server}' 

# Connection String
CONN_STR = (
    f'DRIVER={ODBC_DRIVER};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    f'UID={USERNAME};'
    f'PWD={PASSWORD}'
)

app = FastAPI()

# --- Database Functions (Updated for pyodbc and T-SQL) ---

def get_db_connection():
    """Establishes and returns a pyodbc SQL Server connection."""
    try:
        # autocommit=True is often helpful for simple web application transactions
        conn = pyodbc.connect(CONN_STR, autocommit=True)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        # Raise a general runtime error if connection fails (e.g., server is down)
        raise RuntimeError(f"Database connection error: {sqlstate}")

def create_table():
    """Creates the 'employees' table if it doesn't exist, with retry logic."""
    max_retries = 10
    retry_delay = 5 # seconds
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # T-SQL syntax for creating a table with an identity primary key
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[employees]') AND type in (N'U'))
                BEGIN
                    CREATE TABLE employees (
                        idx INT IDENTITY(1,1) PRIMARY KEY,
                        eid NVARCHAR(50) UNIQUE NOT NULL,
                        name NVARCHAR(100) NOT NULL,
                        timestamp FLOAT NOT NULL
                    )
                END
            """)
            conn.commit()
            conn.close()
            print("Database table initialized successfully.")
            return # Table created, exit function
            
        except RuntimeError:
            # Server not ready error
            if attempt < max_retries - 1:
                print(f"Connection failed (Attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect and initialize database after {max_retries} attempts.")
                raise # Re-raise error if all retries fail
        except pyodbc.Error as e:
            # Handle T-SQL errors
            print(f"Error during table creation: {e}")
            raise
        
# Initialize database table on startup
create_table()

# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_employees(
    request: Request, 
    search: str = None, 
    skip: int = 0,       # ⬅️ Query Parameter for Offset
    limit: int = 100     # ⬅️ Query Parameter for Limit
):
    conn = get_db_connection()
    
    try:
        base_query = "SELECT * FROM employees "
        params = []
        
        if search:
            # SQL Server uses CONCAT or + for string concatenation
            base_query += "WHERE eid LIKE CONCAT('%', ?, '%') OR name LIKE CONCAT('%', ?, '%') "
            params.extend([search, search]) 
        
        # ⬅️ SQL Server Pagination Syntax
        base_query += "ORDER BY idx DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([skip, limit]) 
            
        cursor = conn.execute(base_query, params)
        
        # pyodbc doesn't have a built-in row_factory, so we convert tuples to dicts manually
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        employees = [dict(zip(columns, row)) for row in rows]

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

# --- POST ENDPOINTS (Logic remains similar, errors changed) ---

@app.post("/add", response_class=RedirectResponse)
async def add_employee(
    request: Request,
    eid: str = Form(...),
    name: str = Form(...)
):
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
    except pyodbc.Error as e: # ⬅️ Changed error type
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()

    return RedirectResponse(url="/", status_code=303)

@app.post("/update/{idx}", response_class=RedirectResponse)
async def update_employee(
    idx: int,
    request: Request,
    eid: str = Form(...),
    name: str = Form(...)
):
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
    except pyodbc.Error as e: # ⬅️ Changed error type
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()
        
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{idx}", response_class=RedirectResponse)
async def delete_employee(idx: int):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM employees WHERE idx = ?", (idx,))
        conn.commit()
    except pyodbc.Error as e: # ⬅️ Changed error type
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {e}"
        )
    finally:
        conn.close()

    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    uvicorn.run("main_MSSql:app", host="0.0.0.0", port=8000, reload=True)