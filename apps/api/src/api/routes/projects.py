from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()


@router.post("/")
async def create_project(project_data: dict):
    """Create a new project"""
    # TODO: Implement project creation
    return {"message": "Project created", "project_id": "proj_123"}


@router.get("/")
async def list_projects():
    """List all projects"""
    # TODO: Implement project listing
    return {"projects": []}


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get a specific project"""
    # TODO: Implement project retrieval
    return {"project_id": project_id, "name": "My Project"}


@router.put("/{project_id}")
async def update_project(project_id: str, project_data: dict):
    """Update a project"""
    # TODO: Implement project update
    return {"message": "Project updated"}


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    # TODO: Implement project deletion
    return {"message": "Project deleted"}
