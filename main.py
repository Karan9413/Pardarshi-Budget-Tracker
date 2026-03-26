from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3
from typing import List

app = FastAPI()

# 1. ADD MIDDLEWARE RIGHT AFTER APP INITIALIZATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
def init_db():
    conn = sqlite3.connect('audit.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            details TEXT,
            pincode TEXT,
            timestamp DATETIME,
            status TEXT DEFAULT 'Pending Verification'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Data Model
class Report(BaseModel):
    category: str
    details: str
    pincode: str

# --- ROUTES ---

@app.post("/submit-report")
async def create_report(report: Report):
    try:
        conn = sqlite3.connect('audit.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reports (category, details, pincode, timestamp) VALUES (?, ?, ?, ?)",
            (report.category, report.details, report.pincode, datetime.now())
        )
        report_id = cursor.lastrowid # Get the ID of the new report
        conn.commit()
        conn.close()
        return {"message": f"Report filed! Your Audit ID is: {report_id}", "id": report_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-alerts/{pincode}")
async def get_alerts(pincode: str):
    conn = sqlite3.connect('audit.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE pincode = ? ORDER BY id DESC", (pincode,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# NEW: Status Lookup Route
@app.get("/report-status/{report_id}")
async def get_report_status(report_id: int):
    conn = sqlite3.connect('audit.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status, timestamp FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"id": report_id, "status": row[0], "timestamp": row[1]}
    else:
        raise HTTPException(status_code=404, detail="Audit ID not found")

# 2. RUN BLOCK AT THE VERY BOTTOM
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)