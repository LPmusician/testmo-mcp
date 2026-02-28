"""
Automation run tools for Testmo MCP.
"""

from typing import Any

from mcp_testmo.client import TestmoClient
from mcp_testmo.tools.base import register_tool


@register_tool(
    name="testmo_list_automation_runs",
    description="""List automation runs in a project with optional filters.

Automation runs represent CI/CD test execution results. Filter by:
- source_id: Automation source IDs (comma-separated)
- milestone_id: Milestone IDs (comma-separated)
- status: Run status (2=Success, 3=Failure, 4=Running)
- created_after/before: Date range (ISO8601 format)""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The project ID",
            },
            "source_id": {
                "type": "string",
                "description": "Comma-separated automation source IDs to filter by",
            },
            "milestone_id": {
                "type": "string",
                "description": "Comma-separated milestone IDs to filter by",
            },
            "status": {
                "type": "string",
                "description": "Comma-separated status values (2=Success, 3=Failure, 4=Running)",
            },
            "created_after": {
                "type": "string",
                "description": "Filter runs created after (ISO8601 format)",
            },
            "created_before": {
                "type": "string",
                "description": "Filter runs created before (ISO8601 format)",
            },
            "tags": {
                "type": "string",
                "description": "Comma-separated tags to filter by",
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
            "expands": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Related entities to include",
            },
        },
        "required": ["project_id"],
    },
)
async def list_automation_runs(client: TestmoClient, args: dict[str, Any]) -> Any:
    """List automation runs in a project."""
    return await client.list_automation_runs(
        args["project_id"],
        source_id=args.get("source_id"),
        milestone_id=args.get("milestone_id"),
        status=args.get("status"),
        created_after=args.get("created_after"),
        created_before=args.get("created_before"),
        tags=args.get("tags"),
        page=args.get("page", 1),
        per_page=args.get("per_page", 100),
        expands=args.get("expands"),
    )


@register_tool(
    name="testmo_get_automation_run",
    description="Get details of a specific automation run.",
    input_schema={
        "type": "object",
        "properties": {
            "automation_run_id": {
                "type": "integer",
                "description": "The automation run ID",
            },
            "expands": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Related entities to include",
            },
        },
        "required": ["automation_run_id"],
    },
)
async def get_automation_run(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Get details of a specific automation run."""
    return await client.get_automation_run(
        args["automation_run_id"],
        expands=args.get("expands"),
    )


@register_tool(
    name="testmo_create_automation_run",
    description="""Create a new automation run in a project.

The source name identifies the CI/CD integration (e.g., 'frontend', 'backend', 'mobile').
If the source doesn't exist yet, Testmo auto-creates it.

Optional: attach artifacts (external file links), fields (key-value metadata),
links (URLs back to CI build), tags (for milestone auto-linking), and milestone.""",
    input_schema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "The target project ID",
            },
            "name": {
                "type": "string",
                "description": "Name of the automation run",
            },
            "source": {
                "type": "string",
                "description": "Automation source name (e.g., 'frontend', 'backend'). Auto-created if new.",
            },
            "config": {
                "type": "string",
                "description": "Configuration name (optional)",
            },
            "config_id": {
                "type": "integer",
                "description": "Configuration ID (takes precedence over config)",
            },
            "milestone": {
                "type": "string",
                "description": "Milestone name (optional)",
            },
            "milestone_id": {
                "type": "integer",
                "description": "Milestone ID (takes precedence over milestone)",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for the run. Matching automation tags on milestones auto-link the run.",
            },
            "artifacts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "size": {"type": "integer"},
                    },
                    "required": ["name", "url"],
                },
                "description": "External test artifacts (log files, screenshots, etc.)",
            },
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "integer"},
                        "value": {"type": "string"},
                    },
                    "required": ["name", "type", "value"],
                },
                "description": "Custom fields (environment vars, errors, terminal output)",
            },
            "links": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["name", "url"],
                },
                "description": "Links (e.g., back to CI build)",
            },
        },
        "required": ["project_id", "name", "source"],
    },
)
async def create_automation_run(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Create a new automation run."""
    return await client.create_automation_run(
        args["project_id"],
        args["name"],
        args["source"],
        config=args.get("config"),
        config_id=args.get("config_id"),
        milestone=args.get("milestone"),
        milestone_id=args.get("milestone_id"),
        tags=args.get("tags"),
        artifacts=args.get("artifacts"),
        fields=args.get("fields"),
        links=args.get("links"),
    )


@register_tool(
    name="testmo_append_automation_run",
    description="Append test artifacts, fields, or links to an existing automation run.",
    input_schema={
        "type": "object",
        "properties": {
            "automation_run_id": {
                "type": "integer",
                "description": "The automation run ID",
            },
            "artifacts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "size": {"type": "integer"},
                    },
                    "required": ["name", "url"],
                },
                "description": "External test artifacts to append",
            },
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "integer"},
                        "value": {"type": "string"},
                    },
                    "required": ["name", "type", "value"],
                },
                "description": "Custom fields to append",
            },
            "links": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["name", "url"],
                },
                "description": "Links to append",
            },
        },
        "required": ["automation_run_id"],
    },
)
async def append_automation_run(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Append artifacts, fields, or links to an automation run."""
    return await client.append_automation_run(
        args["automation_run_id"],
        artifacts=args.get("artifacts"),
        fields=args.get("fields"),
        links=args.get("links"),
    )


@register_tool(
    name="testmo_complete_automation_run",
    description="""Mark an automation run and its threads as completed.

Set measure_elapsed=true to auto-calculate execution time from
the run's creation time to completion time.""",
    input_schema={
        "type": "object",
        "properties": {
            "automation_run_id": {
                "type": "integer",
                "description": "The automation run ID to complete",
            },
            "measure_elapsed": {
                "type": "boolean",
                "description": "Auto-set execution time from creation to completion",
            },
        },
        "required": ["automation_run_id"],
    },
)
async def complete_automation_run(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Mark an automation run as completed."""
    return await client.complete_automation_run(
        args["automation_run_id"],
        measure_elapsed=args.get("measure_elapsed"),
    )


@register_tool(
    name="testmo_create_automation_run_thread",
    description="""Create a new thread in an automation run for submitting test results.

Threads represent parallel test execution lanes. Create a thread,
then use testmo_append_automation_run_thread to submit test results.""",
    input_schema={
        "type": "object",
        "properties": {
            "automation_run_id": {
                "type": "integer",
                "description": "The automation run ID",
            },
            "elapsed_observed": {
                "type": "integer",
                "description": "Observed execution time in microseconds",
            },
            "elapsed_computed": {
                "type": "integer",
                "description": "Computed execution time in microseconds",
            },
            "artifacts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "size": {"type": "integer"},
                    },
                    "required": ["name", "url"],
                },
                "description": "External test artifacts for the thread",
            },
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "integer"},
                        "value": {"type": "string"},
                    },
                    "required": ["name", "type", "value"],
                },
                "description": "Custom fields for the thread",
            },
        },
        "required": ["automation_run_id"],
    },
)
async def create_automation_run_thread(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Create a new thread in an automation run."""
    return await client.create_automation_run_thread(
        args["automation_run_id"],
        elapsed_observed=args.get("elapsed_observed"),
        elapsed_computed=args.get("elapsed_computed"),
        artifacts=args.get("artifacts"),
        fields=args.get("fields"),
    )


@register_tool(
    name="testmo_append_automation_run_thread",
    description="""Append test results, artifacts, or fields to a thread.

Each test in the 'tests' array represents one test result with:
- key: Unique identifier (e.g., SHA hash)
- name: Test name
- folder: Test folder/suite name
- status: 'passed', 'failed', 'skipped', etc.
- elapsed: Execution time in microseconds
- file/line: Source file location
- assertions: Number of assertions
- artifacts: Per-test artifacts (screenshots, etc.)
- fields: Per-test fields (with optional is_highlight for errors)""",
    input_schema={
        "type": "object",
        "properties": {
            "thread_id": {
                "type": "integer",
                "description": "The automation run thread ID",
            },
            "elapsed_observed": {
                "type": "integer",
                "description": "Partial observed time in microseconds to add",
            },
            "elapsed_computed": {
                "type": "integer",
                "description": "Partial computed time in microseconds to add",
            },
            "artifacts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "url": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "size": {"type": "integer"},
                    },
                    "required": ["name", "url"],
                },
                "description": "External test artifacts to append",
            },
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "integer"},
                        "value": {"type": "string"},
                    },
                    "required": ["name", "type", "value"],
                },
                "description": "Custom fields to append",
            },
            "tests": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Unique test identifier (e.g., SHA hash)",
                        },
                        "name": {
                            "type": "string",
                            "description": "Test name",
                        },
                        "folder": {
                            "type": "string",
                            "description": "Test folder/suite name",
                        },
                        "status": {
                            "type": "string",
                            "description": "Test status: passed, failed, skipped, etc.",
                        },
                        "elapsed": {
                            "type": "integer",
                            "description": "Execution time in microseconds",
                        },
                        "file": {
                            "type": "string",
                            "description": "Source file path",
                        },
                        "line": {
                            "type": "integer",
                            "description": "Source file line number",
                        },
                        "assertions": {
                            "type": "integer",
                            "description": "Number of assertions",
                        },
                        "artifacts": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Per-test artifacts",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Per-test fields (use is_highlight for errors)",
                        },
                    },
                    "required": ["name", "status"],
                },
                "description": "Test results to submit",
            },
        },
        "required": ["thread_id"],
    },
)
async def append_automation_run_thread(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Append test results to a thread."""
    return await client.append_automation_run_thread(
        args["thread_id"],
        elapsed_observed=args.get("elapsed_observed"),
        elapsed_computed=args.get("elapsed_computed"),
        artifacts=args.get("artifacts"),
        fields=args.get("fields"),
        tests=args.get("tests"),
    )


@register_tool(
    name="testmo_complete_automation_run_thread",
    description="Mark an automation run thread as completed and close it for new test results.",
    input_schema={
        "type": "object",
        "properties": {
            "thread_id": {
                "type": "integer",
                "description": "The automation run thread ID to complete",
            },
            "elapsed_observed": {
                "type": "integer",
                "description": "Observed execution time in microseconds",
            },
            "elapsed_computed": {
                "type": "integer",
                "description": "Computed execution time in microseconds",
            },
        },
        "required": ["thread_id"],
    },
)
async def complete_automation_run_thread(client: TestmoClient, args: dict[str, Any]) -> Any:
    """Mark an automation run thread as completed."""
    return await client.complete_automation_run_thread(
        args["thread_id"],
        elapsed_observed=args.get("elapsed_observed"),
        elapsed_computed=args.get("elapsed_computed"),
    )
