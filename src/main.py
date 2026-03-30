from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.services.bigquery import BigQueryService
from src.services.clickup import ClickUpService
from src.services.reorder_engine import ReorderEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    app.state.settings = settings
    yield
    # Shutdown (nothing to clean up yet)


app = FastAPI(
    title="PurchasingAgent",
    description="Automated purchasing agent for Potomax Brands / PotomacBeads",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "purchasing-agent"}


@app.get("/inventory/below-threshold")
async def inventory_below_threshold():
    """Return items currently below their days-supply reorder threshold."""
    settings = get_settings()
    try:
        bq = BigQueryService(settings)
        items = bq.get_items_below_threshold()
        return {"count": len(items), "items": [i.model_dump() for i in items]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reorder/recommendations")
async def get_recommendations():
    """Calculate and return current reorder recommendations."""
    settings = get_settings()
    try:
        bq = BigQueryService(settings)
        engine = ReorderEngine(settings, bq)
        recommendations = engine.generate_recommendations()
        return {
            "count": len(recommendations),
            "recommendations": [r.model_dump() for r in recommendations],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reorder/stage")
async def stage_recommendations():
    """Stage reorder recommendations as ClickUp tasks for human approval."""
    settings = get_settings()
    try:
        bq = BigQueryService(settings)
        engine = ReorderEngine(settings, bq)
        clickup = ClickUpService(settings)

        recommendations = engine.generate_recommendations()
        if not recommendations:
            return {"staged": 0, "message": "No reorder recommendations at this time"}

        task_ids = []
        for rec in recommendations:
            task_id = clickup.create_reorder_task(rec)
            task_ids.append(task_id)

        return {
            "staged": len(task_ids),
            "task_ids": task_ids,
            "message": f"Staged {len(task_ids)} reorder recommendations for approval",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
