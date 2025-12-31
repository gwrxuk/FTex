"""
API Router aggregation.
"""

from fastapi import APIRouter
from app.api.endpoints import entities, transactions, alerts, cases, analytics, graph, search, ftex, rfp, poc

router = APIRouter()

# FTex Core Technologies
router.include_router(ftex.router, prefix="/ftex", tags=["FTex Decision Intelligence"])

# Sales Engineering Tools
router.include_router(rfp.router, prefix="/rfp", tags=["RFP/RFI Management"])
router.include_router(poc.router, prefix="/poc", tags=["PoC/Demo Management"])

# Standard APIs
router.include_router(entities.router, prefix="/entities", tags=["Entities"])
router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
router.include_router(cases.router, prefix="/cases", tags=["Cases"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(graph.router, prefix="/graph", tags=["Graph"])
router.include_router(search.router, prefix="/search", tags=["Search"])

