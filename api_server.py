from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from models.database import SessionLocal
from services.export_service import ExportService
from monitoring.healthcheck import app as health_app
from loguru import logger
import uvicorn

app = FastAPI(title="B2B Contact Miner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/health", health_app)


@app.get("/export/csv")
async def export_csv(min_confidence: int = 0, domain: str = None):
    """Export contacts to CSV"""
    db = SessionLocal()
    try:
        export_service = ExportService(db)
        
        filters = {"min_confidence": min_confidence}
        if domain:
            filters["domain"] = domain
        
        csv_content = export_service.export_to_csv(filters)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=contacts.csv"}
        )
    finally:
        db.close()


@app.get("/export/excel")
async def export_excel(min_confidence: int = 0, domain: str = None):
    """Export contacts to Excel"""
    db = SessionLocal()
    try:
        export_service = ExportService(db)
        
        filters = {"min_confidence": min_confidence}
        if domain:
            filters["domain"] = domain
        
        excel_content = export_service.export_to_excel(filters)
        
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=contacts.xlsx"}
        )
    finally:
        db.close()


@app.get("/export/summary")
async def export_summary():
    """Get export summary statistics"""
    db = SessionLocal()
    try:
        export_service = ExportService(db)
        return export_service.get_export_summary()
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
