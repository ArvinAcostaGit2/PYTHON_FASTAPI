# FastAPI CRUD Application

A full-stack CRUD (Create, Read, Update, Delete) application built with FastAPI, SQLite, and vanilla JavaScript with Tailwind / Bootstrap CSS.

## Overview

This application provides a complete web-based interface for managing database records with a clean, modern UI. It features a RESTful API backend and an interactive frontend with modal-based workflows.

## Features

### Backend (FastAPI)
- **RESTful API** with full CRUD operations
- **SQLite Database** for persistent data storage
- **Automatic CSV/JSON Export** on data retrieval
- **Search Functionality** (searches name and remarks fields)
- **Data Validation** using Pydantic models
- **CSV Export Endpoint** for manual data downloads

### Frontend
- **Responsive Design** using Tailwind / Bootstrap CSS
- **Modal-Based Interface** for all operations
- **Real-time Alerts** for user feedback
- **Search Interface** with live results
- **Table Views** with sortable data
- **Action Buttons** for modify/delete operations

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite3
- **Frontend**: Vanilla JavaScript, HTML5
- **Styling**: Tailwind CSS (CDN)
- **Templating**: Jinja2

## Project Structure

```
├── main.py                # FastAPI application & API endpoints (main, main1, mainA, mainB)
├── config.toml            # Configuration file (for future enhancement use)
├── db/
│   └── database.db        # SQLite database
├── templates/
│   ├── welcome.html       # Landing page
│   └── main.html          # Main CRUD interface
├── static/
│   └── style.css          # Custom styles
└── records_export_*.csv   # Auto-generated exports
```

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <project-directory>
   ```

2. **Install dependencies**
   ```bash
   pip install fastapi uvicorn jinja2 pydantic
   ```

3. **Create config.toml** (if not exists)
   ```toml
   # Add your configuration here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the application**
   - Open browser to `http://localhost:8000`
   - API documentation at `http://localhost:8000/docs`

## API Endpoints

### Records Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/records/all` | Retrieve all records |
| POST | `/api/records` | Create a new record |
| PUT | `/api/records/{id}` | Update existing record |
| DELETE | `/api/records/{id}` | Delete a record |
| POST | `/api/search` | Search records by name/remarks |
| GET | `/api/export/csv` | Export all records to CSV |

### Frontend Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome page |
| GET | `/main` | Main CRUD interface |

## Database Schema

```sql
CREATE TABLE records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rights TEXT NOT NULL,          -- Admin, User, Staff
    status TEXT NOT NULL,          -- Active, Inactive, On Hold
    remarks TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Data Models

### RecordBase (Pydantic)
```python
{
    "name": str,       # max 100 chars
    "rights": str,     # max 50 chars
    "status": str,     # max 50 chars
    "remarks": str     # optional, max 500 chars
}
```

### RecordInDB
```python
{
    "id": int,
    "name": str,
    "rights": str,
    "status": str,
    "remarks": str | None,
    "timestamp": datetime
}
```

## Usage Guide

### Adding a Record
1. Click **"+ Add New Record"** button
2. Fill in the form fields:
   - Name (required)
   - Rights: Admin/User/Staff
   - Status: Active/Inactive/On Hold
   - Remarks (optional)
3. Click **"Save Record"**

### Viewing All Records
1. Click **"View All Records"** button
2. Browse the table with all records
3. Use **Modify** or **Delete** buttons on each row

### Searching Records
1. Enter search term in the search box
2. Click **"Search"** button
3. View results in the search modal
4. Search queries match against Name and Remarks fields

### Modifying a Record
1. From the "View All Records" table
2. Click **"Modify"** on the desired record
3. Update fields in the edit modal
4. Click **"Update Record"**

### Deleting a Record
1. From the "View All Records" table
2. Click **"Delete"** on the desired record
3. Confirm deletion in the confirmation modal

### Exporting Data
- **Automatic**: CSV and JSON files are auto-generated when viewing all records
- **Manual**: Access `/api/export/csv` endpoint for downloadable CSV

## Configuration Options

In `main.py`, you can configure:

```python
MAIN_PAGE = "mainA"           # Main interface template ( main, main1, mainA, mainB )
MAIN_PAGE = f"{MAIN_PAGE}.html"

WELCOME_PAGE = "welcome.html" # Landing page template

CREATE_CSV = True             # Auto-export to CSV backend
CREATE_JSON = True            # Auto-export to JSON backend
```

## API Request Examples

### Create a Record
```bash
curl -X POST "http://127.0.0.1:8000/api/records" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "rights": "Admin",
    "status": "Active",
    "remarks": "New administrator"
  }'
```

### Search Records
```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "John"}'
```

### Get All Records (with jq formatting)
```bash
curl -s -X GET "http://127.0.0.1:8000/api/records/all" | jq
```

## Features in Detail

### Automatic Export System
When records are retrieved via `/api/records/all`:
- A timestamped CSV file is generated in the root directory
- A timestamped JSON file is generated in the root directory
- Files follow the format: `records_export_YYYYMMDD_HHMMSS.csv/json`

### Search Functionality
- Case-insensitive search
- Searches in both `name` and `remarks` fields
- Returns results ordered by ID (descending)
- Displays formatted results in a modal

### Modal System
The frontend uses 5 specialized modals:
1. **Search Results Modal** - Displays search results
2. **Add Record Modal** - Form for creating new records
3. **View All Modal** - Table with all records + CRUD actions
4. **Edit Modal** - Form for updating existing records
5. **Delete Confirmation Modal** - Confirmation dialog for deletions

### Alert System
- Success alerts (green) - Successful operations
- Error alerts (red) - Failed operations
- Info alerts (blue) - Informational messages
- Auto-dismiss after 5 seconds

## Security Considerations

⚠️ **This is a development/demo application. Before production use:**
(LACKING - For more enhancement)
- Implement proper authentication and authorization
- Add input sanitization and validation
- Use environment variables for sensitive configuration
- Implement rate limiting
- Add CORS policies
- Use HTTPS in production
- Implement proper error handling and logging
- Add database connection pooling
- Validate user permissions for CRUD operations

## Troubleshooting

### Database Issues
- Check if `db/` directory exists
- Verify file permissions on `database.db`
- Check SQLite version compatibility

### Frontend Not Loading
- Ensure `templates/` and `static/` directories exist
- Verify Tailwind CDN is accessible
- Check browser console for JavaScript errors

### API Errors
- Check FastAPI logs in terminal
- Verify request payload format
- Ensure Content-Type headers are correct

## Development

### Running in Development Mode
```bash
# With auto-reload Directly in the Console / Terminal
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# current parameter in Sample Image
MAIN_PAGE = "mainA"           # Main interface template ( main, main1, mainA, mainB )
MAIN_PAGE = f"{MAIN_PAGE}.html"
```

<img width="777" height="607" alt="image" src="https://github.com/user-attachments/assets/325ef9fd-941c-486f-abf2-c4065187901c" />

<img width="1604" height="633" alt="image" src="https://github.com/user-attachments/assets/2c0c7bcf-b4dc-4926-b6ba-ce17d26317fd" />

<img width="1743" height="785" alt="image" src="https://github.com/user-attachments/assets/60f42be7-4327-4849-b9fc-0771322d5bd0" />





### Testing the API
- Interactive docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

<img width="1344" height="971" alt="image" src="https://github.com/user-attachments/assets/c618ab9b-7e71-41a9-ba4d-e406463c48c2" />


## License

Free for everyone to Learn. Just Let me know.

## Contributing

[Add contribution guidelines here]

## Author

- Arvin P. Acosta
- IT NOC - System Engineer L-1 
- ePerformax Contact Centers

---

**Note**: This application is designed for learning and development purposes. Ensure proper security measures are implemented before deploying to production environments.
