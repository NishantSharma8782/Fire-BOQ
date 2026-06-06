from fastapi import APIRouter, HTTPException, BackgroundTasks
from bson import ObjectId
from datetime import datetime
from app.models.analysis import AnalysisResponse, AnalysisTriggerResponse
from app.db.database import get_collection
from app.services import gemini_service
from app.services.boq_engine import calculate_fire_recommendations
from app.services.layout_engine import generate_layout

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def _serialize(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


@router.post("/{project_id}/analyze", response_model=AnalysisTriggerResponse)
async def trigger_analysis(project_id: str):
    """Trigger Gemini AI analysis for a project's drawings."""
    projects_col = get_collection("projects")
    drawings_col = get_collection("drawings")
    analyses_col = get_collection("analyses")

    # Get project
    project = await projects_col.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Get latest drawing
    drawing = await drawings_col.find_one(
        {"project_id": project_id},
        sort=[("uploaded_at", -1)]
    )
    if not drawing:
        raise HTTPException(
            status_code=400,
            detail="No drawings found. Please upload a drawing first."
        )

    hazard_category = project.get("hazard_category", "light")
    building_type = project.get("building_type", "office")

    # Run Gemini analysis
    analysis_result = await gemini_service.analyze_drawing(
        file_path=drawing["file_path"],
        building_type=building_type,
        hazard_category=hazard_category,
    )
    building_data = analysis_result["building_data"]

    # Get fire recommendations from BOQ engine
    recommendations = calculate_fire_recommendations(building_data, hazard_category)

    # Get placement strategy from Gemini
    strategy_result = await gemini_service.get_fire_recommendations(building_data, hazard_category)
    if strategy_result.get("success"):
        recommendations["placement_strategy"] = strategy_result["strategy"]["placement_strategy"]

    # Generate layout coordinates
    layout_data = generate_layout(building_data, recommendations)

    # Save to DB
    now = datetime.utcnow()
    doc = {
        "project_id": project_id,
        "building_data": building_data,
        "recommendations": recommendations,
        "layout_data": layout_data,
        "raw_analysis": analysis_result.get("raw", ""),
        "created_at": now,
    }

    # Delete old analysis if exists
    await analyses_col.delete_many({"project_id": project_id})
    result = await analyses_col.insert_one(doc)
    created = await analyses_col.find_one({"_id": result.inserted_id})

    # Update project status
    await projects_col.update_one(
        {"project_id": project_id},
        {"$set": {"status": "analyzed", "updated_at": now}}
    )

    return AnalysisTriggerResponse(
        success=True,
        message="Analysis completed successfully",
        analysis=_serialize(created),
    )


@router.get("/{project_id}", response_model=AnalysisResponse)
async def get_analysis(project_id: str):
    """Get analysis results for a project."""
    analyses_col = get_collection("analyses")
    doc = await analyses_col.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="No analysis found for this project. Run analysis first."
        )
    return _serialize(doc)
