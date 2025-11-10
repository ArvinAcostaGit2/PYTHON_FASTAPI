# THIS CRUD FASTAPI

import sqlite3
import os
import json
import csv
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager
from io import StringIO

import uvicorn

from fastapi import FastAPI, Depends, HTTPException, Request, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import tomllib  # Python 3.11+ built-in

from pydantic import BaseModel, Field

# --- LOAD CONFIG --- (For Future Use - Variables Parameterized)
with open("config.toml", "rb") as f:
    config = tomllib.load(f)


# --- Configuration and Setup ---

# Define base directory for locating files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Database directory and file name
DB_DIR = "db"
SQLITE_FILE = os.path.join(DB_DIR, "database.db")

# Create necessary directories if they don't exist
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"

# this can be placed in a .env file
MAIN_PAGE = "mainA"     # main, main1, mainA, mainB
MAIN_PAGE = f"{MAIN_PAGE}.html"

WELCOME_PAGE = "welcome.html"     

# For Debugging use
CREATE_CSV = True # this will export the data directly to the backend
CREATE_JSON = True


# this will create Folder if not exist
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# --- Database Helper Functions ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(SQLITE_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initializes the database: creates the table structure."""
    os.makedirs(DB_DIR, exist_ok=True) 

    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rights TEXT NOT NULL,
            status TEXT NOT NULL,
            remarks TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    
    print("Database structure initialized.")

    conn.close()

# --- Lifespan Event Handler ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    init_db()
    yield
    print("Application shut down.")


# Initialize FastAPI app with the new lifespan manager
app = FastAPI(
    title="FastAPI Simple CRUD App",
    description="A basic CRUD application using FastAPI, SQLite, and Jinja2 templates.",
    lifespan=lifespan
)

# Setup Templates and Static Files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Pydantic Models for Data Validation and Serialization ---

class RecordBase(BaseModel):
    name: str = Field(..., max_length=100)
    rights: str = Field(..., max_length=50)
    status: str = Field(..., max_length=50)
    remarks: Optional[str] = Field(None, max_length=500)

class RecordCreate(RecordBase):
    pass

class RecordUpdate(RecordBase):
    name: Optional[str] = Field(None, max_length=100)
    rights: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    remarks: Optional[str] = Field(None, max_length=500)

class RecordInDB(RecordBase):
    id: int
    timestamp: datetime



# --- API Router for CRUD Operations ---

api_router = APIRouter(prefix="/api")

# curl -s -X GET "http://127.0.0.1:8000/api/records/all" | jq
# winget install jqlang.jq
# this will retrieve all Records (VIEW)
@api_router.get("/records/all", response_model=List[RecordInDB])
async def get_all_records():
    """Fetch all records from the database with Export to CSV Feature """
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection error.")
    
    records = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
    
    # Export to CSV Backend Side, if Conditioning is CREATE_CSV=True -------------------
    if CREATE_CSV:
        try:
            # Create CSV file
            csv_filename = f"records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_filepath = os.path.join(BASE_DIR, csv_filename)
            
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['ID', 'Name', 'Rights', 'Status', 'Remarks', 'Timestamp'])
                
                # Write data rows
                for record in records:
                    writer.writerow([
                        record['id'],
                        record['name'],
                        record['rights'],
                        record['status'],
                        record['remarks'] or '',
                        record['timestamp']
                    ])
            
            print(f"CSV exported successfully: {csv_filepath}")
        except Exception as e:
            print(f"CSV export failed: {e}")
    # Export to CSV -------------------


    # Export to JSON automatically -------------------
    if CREATE_JSON:
        try:
            # Convert rows → list of dicts
            processed_records = []
            for r in records:
                processed_records.append(dict(r))   # convert Row → dict

            # Build filename
            json_filename = f"records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_filepath = os.path.join(BASE_DIR, json_filename)

            # JSON string
            json_data = json.dumps(processed_records, indent=4, default=str)

            # Save file
            with open(json_filepath, 'w', encoding='utf-8') as jsonfile:
                jsonfile.write(json_data)

            # Print to console
            print("JSON exported successfully!")
            print(json_data)
            print(f"JSON file saved at: {json_filepath}")

        except Exception as e:
            print(f"JSON export failed: {e}")
    # Export to JSON  -------------------


    conn.close()
    
    return [RecordInDB(**dict(record)) for record in records]


# this will Add a NEW Record to the Database via POST Method 
# (CRUD - CREATE - INSERT)
@api_router.post("/records", response_model=RecordInDB, status_code=201)
async def create_record(record: RecordCreate):
    
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection error.")
    
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO records (name, rights, status, remarks)
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(query, (record.name, record.rights, record.status, record.remarks))
        conn.commit() # excute the Insert of Record
        
        new_record_id = cursor.lastrowid
        new_record = conn.execute("SELECT * FROM records WHERE id = ?", (new_record_id,)).fetchone()
        
        if new_record is None:
            raise HTTPException(status_code=500, detail="Record created but failed to retrieve.")

        conn.close()
        return RecordInDB(**dict(new_record))
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Integrity error: Check unique constraints.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to create record: {e}")


# (CRUD - UPDATE)
@api_router.put("/records/{record_id}", response_model=RecordInDB)
async def update_record(record_id: int, record: RecordUpdate):
    """Update an existing record by ID."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection error.")
    
    updates = []
    values = []
    
    if record.name is not None:
        updates.append("name = ?")
        values.append(record.name)
    if record.rights is not None:
        updates.append("rights = ?")
        values.append(record.rights)
    if record.status is not None:
        updates.append("status = ?")
        values.append(record.status)
    if record.remarks is not None:
        updates.append("remarks = ?")
        values.append(record.remarks)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    updates.append("timestamp = CURRENT_TIMESTAMP")
    
    query = f"UPDATE records SET {', '.join(updates)} WHERE id = ?"
    values.append(record_id)
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, tuple(values))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found.")

        updated_record = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        
        conn.close()
        return RecordInDB(**dict(updated_record))
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update record: {e}")

# (CRUD - DELETE)
@api_router.delete("/records/{record_id}", status_code=204)
async def delete_record(record_id: int):
    """Delete a record by ID."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection error.")
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found.")
            
        conn.close()
        return JSONResponse(status_code=204, content={"message": "Record deleted successfully."})

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete record: {e}")


# (ETL - VIEW)
@api_router.post("/search", response_model=List[RecordInDB])
async def search_records(request: Request):
    """Search records by name or remarks only using a text query."""
    try:
        data = await request.json()

        # --- DEBUG PRINT STATEMENT UPDATED TO JSON FORMATTED OUTPUT ---
        print("--- Formatted Search Payload Received ---")
        print(json.dumps(data, indent=4))
        print("------------------------------------------")

        query_text = data.get("query", "").strip()
    except:
        raise HTTPException(status_code=400, detail="Invalid request body.")

    if not query_text:
        return []

    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection error.")
    
    # UPDATED: Search only in name and remarks fields
    lower_query_text = query_text.lower()
    search_param = f"%{lower_query_text}%"
    
    query = """
        SELECT * FROM records
        WHERE LOWER(name) LIKE ? OR LOWER(remarks) LIKE ?
        ORDER BY id DESC
    """
    
    records = conn.execute(query, (search_param, search_param)).fetchall()
    conn.close()
    
    return [RecordInDB(**dict(record)) for record in records]




# defines an HTTP endpoint on the Frontend
# (API for export CSV)
@api_router.get("/export/csv")
async def export_records_to_csv():
    """Export all records to CSV file."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection error.")
    
    records = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
    conn.close()
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Rights', 'Status', 'Remarks', 'Timestamp'])
    
    # Write data rows
    for record in records:
        writer.writerow([
            record['id'],
            record['name'],
            record['rights'],
            record['status'],
            record['remarks'] or '',
            record['timestamp']
        ])
    
    # Get CSV content
    output.seek(0)
    
    # Generate filename with current date
    filename = f"records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Return as downloadable file
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



# Attach the API router ==========================================================
app.include_router(api_router)

# --- Frontend Routes (Serving HTML Templates) ---

@app.get("/", response_class=HTMLResponse)
async def welcome_page(request: Request):
    """The initial welcome page."""
    return templates.TemplateResponse(
        name=WELCOME_PAGE,
        context={"request": request},
        status_code=200
    )

@app.get("/main", response_class=HTMLResponse)
async def main_page(request: Request):
    """The main CRUD application page."""
    return templates.TemplateResponse(
        name=MAIN_PAGE,
        context={"request": request},
        status_code=200
    )

# --- Server Start Entry Point ---

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
