"""
Folder management tools for Testmo MCP.
"""

from typing import Any

from mcp_testmo.client import TestmoClient
from mcp_testmo.tools.base import register_tool


@register_tool(
    name="testmo_list_folders",
    description="List all folders in a Testmo project. Returns folder hierarchy with IDs, names, and parent relationships.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
        },
        "required": ["project_id"],
    },
)
async def list_folders(client: TestmoClient, args: dict[str, Any]) -> Any:
    """List all folders in a project with full paths."""
    folders = await client.get_all_folders(args["project_id"])
    # Build folder paths for easier reading
    folder_map = {f["id"]: f for f in folders}
    for folder in folders:
        path_parts = [folder["name"]]
        parent_id = folder.get("parent_id")
        while parent_id and parent_id in folder_map:
            parent = folder_map[parent_id]
            path_parts.insert(0, parent["name"])
            parent_id = parent.get("parent_id")
        folder["full_path"] = " / ".join(path_parts)
    return folders


@register_tool(
    name="testmo_get_folder",
    description="Get details of a specific folder.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "folder_id": {
                "type": "integer",
                "description": "The folder ID",
            },
        },
        "required": ["project_id", "folder_id"],
    },
)
async def get_folder(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Get details of a specific folder."""
    return await client.get_folder(args["project_id"], args["folder_id"])


@register_tool(
    name="testmo_create_folder",
    description="Create a new folder in a Testmo project.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "name": {
                "type": "string",
                "description": "Folder name",
            },
            "parent_id": {
                "type": "integer",
                "description": "Parent folder ID (optional, omit for root level)",
            },
            "docs": {
                "type": "string",
                "description": (
                    "Folder documentation / reference field (optional). "
                    "Useful for storing a link back to a source-of-truth "
                    "(e.g., '<p>https://swiftotter.atlassian.net/browse/SWM-914</p>'). "
                    "Accepts HTML."
                ),
            },
        },
        "required": ["project_id", "name"],
    },
)
async def create_folder(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Create a new folder."""
    return await client.create_folder(
        args["project_id"],
        args["name"],
        args.get("parent_id"),
        args.get("docs"),
    )


@register_tool(
    name="testmo_update_folder",
    description="Update a folder's name, parent, or docs reference field.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "folder_id": {
                "type": "integer",
                "description": "The folder ID to update",
            },
            "name": {
                "type": "string",
                "description": "New folder name (optional)",
            },
            "parent_id": {
                "type": "integer",
                "description": "New parent folder ID (optional)",
            },
            "docs": {
                "type": "string",
                "description": (
                    "New folder documentation / reference field (optional). "
                    "Useful for linking the folder to a source-of-truth "
                    "(e.g., '<p>https://swiftotter.atlassian.net/browse/SWM-914</p>'). "
                    "Accepts HTML. Pass an empty string to clear."
                ),
            },
        },
        "required": ["project_id", "folder_id"],
    },
)
async def update_folder(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Update a folder."""
    return await client.update_folder(
        args["project_id"],
        args["folder_id"],
        args.get("name"),
        args.get("parent_id"),
        args.get("docs"),
    )


@register_tool(
    name="testmo_delete_folder",
    description="Delete a folder from a project. WARNING: This will also delete all test cases in the folder.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "folder_id": {
                "type": "integer",
                "description": "The folder ID to delete",
            },
        },
        "required": ["project_id", "folder_id"],
    },
)
async def delete_folder(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Delete a folder."""
    return await client.delete_folder(args["project_id"], args["folder_id"])


@register_tool(
    name="testmo_find_folder_by_name",
    description="Find a folder by its name within a project.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "name": {
                "type": "string",
                "description": "Folder name to search for",
            },
            "parent_id": {
                "type": "integer",
                "description": "Parent folder ID to search within (optional, omit for root level)",
            },
        },
        "required": ["project_id", "name"],
    },
)
async def find_folder_by_name(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Find a folder by name."""
    result = await client.find_folder_by_name(
        args["project_id"],
        args["name"],
        args.get("parent_id"),
    )
    if result:
        return result
    return {"found": False, "message": f"Folder '{args['name']}' not found"}
