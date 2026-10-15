"""Collect every feature router under the `/v1` prefix.

The order here is the order of the sections in /docs.
"""

from fastapi import APIRouter

from app.admin.router import router as admin_router
from app.business.router import router as business_router
from app.dashboard.router import router as dashboard_router
from app.documents.router import router as documents_router
from app.invoices.router import router as invoices_router
from app.library.router import router as library_router
from app.platform.router import router as platform_router
from app.quotes.router import router as quotes_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(platform_router)
api_router.include_router(business_router)
api_router.include_router(library_router)
api_router.include_router(quotes_router)
api_router.include_router(invoices_router)
api_router.include_router(documents_router)
api_router.include_router(dashboard_router)
api_router.include_router(admin_router)
