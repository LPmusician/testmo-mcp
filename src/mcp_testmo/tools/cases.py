"""
Test case management tools for Testmo MCP.
"""

from typing import Any

from mcp_testmo.client import TestmoClient
from mcp_testmo.tools.base import register_tool


@register_tool(
    name="testmo_list_cases",
    description="List test cases in a project or folder. Supports pagination.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "folder_id": {
                "type": "integer",
                "description": "Filter by folder ID (optional)",
            },
            "page": {
                "type": "integer",
                "description": "Page number (default: 1)",
                "default": 1,
            },
            "per_page": {
                "type": "integer",
                "description": "Results per page (default: 100, max: 100). Valid values: 25, 50, 100",
                "default": 100,
                "enum": [25, 50, 100],
            },
        },
        "required": ["project_id"],
    },
)
async def list_cases(client: TestmoClient, args: dict[str, Any]) -> Any:
    """List test cases in a project or folder."""
    return await client.list_cases(
        args["project_id"],
        args.get("folder_id"),
        args.get("page", 1),
        args.get("per_page", 100),
    )


@register_tool(
    name="testmo_get_all_cases",
    description="Get all test cases in a folder (handles pagination automatically). Use for discovering existing test cases.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "folder_id": {
                "type": "integer",
                "description": "Folder ID to get cases from (optional)",
            },
        },
        "required": ["project_id"],
    },
)
async def get_all_cases(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Get all test cases with auto-pagination."""
    cases = await client.get_all_cases(
        args["project_id"],
        args.get("folder_id"),
    )
    return {
        "total": len(cases),
        "cases": cases,
    }


@register_tool(
    name="testmo_get_case",
    description="Get full details of a specific test case, including custom fields and Gherkin scenarios.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "case_id": {
                "type": "integer",
                "description": "The test case ID",
            },
        },
        "required": ["project_id", "case_id"],
    },
)
async def get_case(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Get full details of a specific test case."""
    return await client.get_case(args["project_id"], args["case_id"])


@register_tool(
    name="testmo_create_case",
    description="""Create a single test case in Testmo.

Required fields:
- name: Test case title
- folder_id: Target folder ID (0 for root)
- custom_priority: Priority ID (52=Critical, 1=High, 2=Medium, 3=Low; SwiftOtter default: 33)
- template_id: 2=Steps Table (SwiftOtter default), 4=BDD/Gherkin
- custom_expected: HTML string with the expected outcome
- custom_steps: Array of step objects (see Steps below)

Auto-filled if you omit them (SwiftOtter Normal QA profile):
- custom_browser: [12] (Chrome)
- custom_browser_version: [20] (Latest)
- custom_device: [25] (Desktop)

Steps:
Each step is either {"content": "...", "expected": "..."} (friendly aliases)
or {"text1": "...", "text3": "..."} (Testmo's native schema). Both work —
this wrapper translates content→text1 and expected→text3 automatically.

Optional fields:
- state_id: 1=Draft (default), 2=Review, 3=Approved, 4=Active, 5=Deprecated
- tags: Array of strings
- custom_preconditions: HTML string
- issues: Array of issue objects to link (see Issue Linking below)

Issue Linking:
Some templates (notably template_id=2 / Steps Table) reject the `issues[]`
array on POST. This wrapper handles that automatically: if you supply
`issues`, the case is created first without them, then a follow-up
`update_case` attaches them. The returned case reflects the post-attach
state.

Payload format for each issue:
- {"display_id": "PROJ-123", "integration_id": 1, "connection_project_id": 11641}

`connection_project_id` must be an integer (the Jira project's numeric ID),
NOT a string. Discover valid values via `testmo_list_issue_connections`.

Not all fields are honored by all templates. `custom_type`, `custom_creator`,
`tags`, and `custom_features` may be silently dropped or rejected under
`template_id=2` — set them via update_case afterward if needed, or use
`template_id=4` (BDD/Gherkin) if you need those fields on create.""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "case_data": {
                "type": "object",
                "description": "Test case data object with all required fields",
            },
        },
        "required": ["project_id", "case_data"],
    },
)
async def create_case(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Create a single test case."""
    return await client.create_case(args["project_id"], args["case_data"])


@register_tool(
    name="testmo_create_cases",
    description="""Create multiple test cases in a batch (max 100 per call).

Same auto-normalization as testmo_create_case applies to every case:
- Browser/device fields default to Chrome/Latest/Desktop if omitted.
- Steps accept {content, expected} or {text1, text3} — both work.

Note on issues[]: this bulk-create tool does NOT auto-attach issues
(unlike testmo_create_case). If you need issues linked, use
testmo_create_case (per-case) or follow up this call with
testmo_update_case for each returned case.""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "cases": {
                "type": "array",
                "description": "Array of test case objects (max 100)",
                "items": {"type": "object"},
            },
        },
        "required": ["project_id", "cases"],
    },
)
async def create_cases(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Create multiple test cases in a batch."""
    return await client.create_cases(args["project_id"], args["cases"])


@register_tool(
    name="testmo_batch_create_cases",
    description="""Create any number of test cases, automatically handling batching (100 per request).

Same auto-normalization as testmo_create_case applies to every case
(browser/device defaults, step alias translation).

Error surfacing: if a batch fails with an opaque 422, this method
automatically retries each case in that batch individually so the returned
`errors` array names the specific case(s) that are bad. Successful cases
in a failed batch are still created.

Note on issues[]: this tool does NOT auto-attach issues. See
testmo_create_cases / testmo_create_case if issue linking is needed.""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "cases": {
                "type": "array",
                "description": "Array of test case objects",
                "items": {"type": "object"},
            },
        },
        "required": ["project_id", "cases"],
    },
)
async def batch_create_cases(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Create test cases with auto-batching."""
    return await client.batch_create_cases(args["project_id"], args["cases"])


@register_tool(
    name="testmo_update_case",
    description="""Update an existing test case. Only include fields you want to change.

Partial updates are safe: fields Testmo's PATCH endpoint requires
(custom_browser, custom_browser_version, custom_device) are automatically
preserved from the existing case if you don't supply them. You can update a
single field (e.g., {"name": "New name"}) without a 422 error.

Issue Linking (Enhanced API - Jan 2026):
Link external issues using flexible issue objects instead of internal IDs:
- issues: [{"display_id": "PROJ-123", "integration_id": 1, "connection_project_id": "org/repo"}]

Use testmo_list_issue_connections to discover integration_id and connection_project_id values.""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "case_id": {
                "type": "integer",
                "description": "The test case ID to update",
            },
            "data": {
                "type": "object",
                "description": "Fields to update",
            },
        },
        "required": ["project_id", "case_id", "data"],
    },
)
async def update_case(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Update an existing test case."""
    return await client.update_case(
        args["project_id"],
        args["case_id"],
        args["data"],
    )


@register_tool(
    name="testmo_batch_update_cases",
    description="""Bulk update up to 100 test cases with the same field values (PATCH).

Applies the same changes to all specified case IDs. Useful for:
- Moving cases to a new folder
- Updating priority, state, or status in bulk
- Linking automation sources to manual test cases via automation_links
- Adding tags or issue links to multiple cases at once

Note: When updating cases with different templates, custom fields must
exist in ALL templates or a 422 error is returned.""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Array of case IDs to update (max 100)",
            },
            "folder_id": {
                "type": "integer",
                "description": "Target folder ID",
            },
            "state_id": {
                "type": "integer",
                "description": "State ID (1=Draft, 2=Review, 3=Approved, 4=Active, 5=Deprecated)",
            },
            "status_id": {
                "type": "integer",
                "description": "Status ID to apply",
            },
            "estimate": {
                "type": "integer",
                "description": "Estimated execution duration",
            },
            "custom_priority": {
                "type": "integer",
                "description": "Priority ID (52=Critical, 1=High, 2=Medium, 3=Low)",
            },
            "automation_links": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "automation_source_id": {"type": "integer"},
                        "automation_case_id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "description": "Automation links to associate (automation_source_id, automation_case_id, name)",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags to apply",
            },
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "display_id": {"type": "string"},
                        "integration_id": {"type": "integer"},
                        "connection_project_id": {},
                    },
                },
                "description": "Issue links (display_id, integration_id, connection_project_id)",
            },
        },
        "required": ["project_id", "ids"],
    },
)
async def batch_update_cases(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Bulk update test cases with the same field values."""
    project_id = args["project_id"]
    ids = args["ids"]
    # Extract update fields (everything except project_id and ids)
    skip_keys = {"project_id", "ids"}
    data = {k: v for k, v in args.items() if k not in skip_keys and v is not None}
    return await client.batch_update_cases(project_id, ids, data)


@register_tool(
    name="testmo_delete_case",
    description="Delete a test case.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "case_id": {
                "type": "integer",
                "description": "The test case ID to delete",
            },
        },
        "required": ["project_id", "case_id"],
    },
)
async def delete_case(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Delete a test case."""
    return await client.delete_case(args["project_id"], args["case_id"])


@register_tool(
    name="testmo_batch_delete_cases",
    description="Delete multiple test cases.",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "case_ids": {
                "type": "array",
                "description": "Array of test case IDs to delete",
                "items": {"type": "integer"},
            },
        },
        "required": ["project_id", "case_ids"],
    },
)
async def batch_delete_cases(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Delete multiple test cases."""
    return await client.batch_delete_cases(
        args["project_id"],
        args["case_ids"],
    )


@register_tool(
    name="testmo_search_cases",
    description="""Search for test cases with filters (query, folder, tags, state).

By default returns cases in summary form — id, key, name, folder_id, state_id,
tags, issues, priority, timestamps only. Full case bodies (custom_steps,
custom_expected, custom_preconditions, HTML content) are stripped out to keep
responses compact enough to scan through many results without overflowing
context. Set summary_only=false to get full case bodies, or use
testmo_get_case for individual cases you actually need in full.""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "query": {
                "type": "string",
                "description": "Search query (searches name and description)",
            },
            "folder_id": {
                "type": "integer",
                "description": "Filter by folder ID",
            },
            "tags": {
                "type": "array",
                "description": "Filter by tags",
                "items": {"type": "string"},
            },
            "state_id": {
                "type": "integer",
                "description": "Filter by state (1=Draft, 2=Review, 3=Approved, 4=Active, 5=Deprecated)",
            },
            "page": {
                "type": "integer",
                "description": "Page number (default: 1)",
            },
            "per_page": {
                "type": "integer",
                "description": "Results per page (default: 25). Valid values: 25, 50, 100",
                "enum": [25, 50, 100],
            },
            "summary_only": {
                "type": "boolean",
                "description": "When true (default), strip each case to core identifying fields (id, key, name, folder_id, state_id, tags, issues, priority, timestamps). Set false to get full case bodies.",
            },
        },
        "required": ["project_id"],
    },
)
async def search_cases(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Search for test cases with filters."""
    return await client.search_cases(
        args["project_id"],
        args.get("query"),
        args.get("folder_id"),
        args.get("tags"),
        args.get("state_id"),
        args.get("page", 1),
        args.get("per_page", 25),
        args.get("summary_only", True),
    )
