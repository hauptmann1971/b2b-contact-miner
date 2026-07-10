from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from models.database import SessionLocal
from services.auth_service import verify_basic_user
from services.export_service import ExportService
from monitoring.healthcheck import app as health_app
from config.settings import settings
from loguru import logger
import uvicorn

app = FastAPI(title="B2B Contact Miner API", version="1.0.0")
_security = HTTPBasic()


def require_tenant_basic(credentials: HTTPBasicCredentials = Depends(_security)) -> int:
    db = SessionLocal()
    try:
        user = verify_basic_user(db, credentials.username, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Basic"},
            )
        return user.tenant_id
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/health", health_app)


@app.get("/export/csv")
async def export_csv(min_confidence: int = 0, domain: str = None, tenant_id: int = Depends(require_tenant_basic)):
    """Export contacts to CSV"""
    db = SessionLocal()
    try:
        export_service = ExportService(db, tenant_id=tenant_id)
        
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
async def export_excel(min_confidence: int = 0, domain: str = None, tenant_id: int = Depends(require_tenant_basic)):
    """Export contacts to Excel"""
    db = SessionLocal()
    try:
        export_service = ExportService(db, tenant_id=tenant_id)
        
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
async def export_summary(tenant_id: int = Depends(require_tenant_basic)):
    """Get export summary statistics"""
    db = SessionLocal()
    try:
        export_service = ExportService(db, tenant_id=tenant_id)
        return export_service.get_export_summary()
    finally:
        db.close()


if __name__ == "__main__":
    # SECURITY: Bind to localhost only (not all interfaces)
    uvicorn.run(app, host="127.0.0.1", port=8000)
