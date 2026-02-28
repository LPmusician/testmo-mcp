# Testmo API Coverage

This document tracks which Testmo REST API endpoints are covered by the MCP tools in this project. Use this to track API coverage and identify gaps when new Testmo API versions are released.

**API Version**: 2.2.0
**Last Updated**: 2026-02-28

## Coverage Summary

| Category | Covered | Total | Coverage |
|----------|---------|-------|----------|
| Projects | 2 | 2 | 100% |
| Folders | 4 | 4 | 100% |
| Milestones | 2 | 2 | 100% |
| Test Cases | 5 | 5 | 100% |
| Test Runs | 2 | 2 | 100% |
| Run Results | 1 | 1 | 100% |
| Sessions | 0 | 2 | 0% |
| Case Attachments | 3 | 3 | 100% |
| Automation Sources | 2 | 2 | 100% |
| Automation Runs | 8 | 8 | 100% |
| Users | 0 | 4 | 0% |
| Groups | 0 | 2 | 0% |
| Roles | 0 | 2 | 0% |
| **Total** | **29** | **37** | **78%** |

## Detailed Coverage

### Projects

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects` | GET | `testmo_list_projects` | Covered |
| `/api/v1/projects/{project_id}` | GET | `testmo_get_project` | Covered |

### Folders

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects/{project_id}/folders` | GET | `testmo_list_folders` | Covered |
| `/api/v1/projects/{project_id}/folders` | POST | `testmo_create_folder` | Covered |
| `/api/v1/projects/{project_id}/folders` | PATCH | `testmo_update_folder` | Covered |
| `/api/v1/projects/{project_id}/folders` | DELETE | `testmo_delete_folder` | Covered |

**Additional Tools**: `testmo_get_folder`, `testmo_find_folder_by_name` (client-side operations)

### Milestones

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects/{project_id}/milestones` | GET | `testmo_list_milestones` | Covered |
| `/api/v1/milestones/{milestone_id}` | GET | `testmo_get_milestone` | Covered |

### Test Cases (Repository Cases)

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects/{project_id}/cases` | GET | `testmo_list_cases`, `testmo_get_all_cases`, `testmo_search_cases` | Covered |
| `/api/v1/projects/{project_id}/cases` | POST | `testmo_create_case`, `testmo_create_cases`, `testmo_batch_create_cases` | Covered |
| `/api/v1/projects/{project_id}/cases/{case_id}` | PUT | `testmo_update_case` | Covered |
| `/api/v1/projects/{project_id}/cases` | PATCH | `testmo_batch_update_cases` | Covered |
| `/api/v1/projects/{project_id}/cases` | DELETE | `testmo_delete_case`, `testmo_batch_delete_cases` | Covered |

**Additional Tools**: `testmo_get_case` (individual case retrieval)

### Test Runs

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects/{project_id}/runs` | GET | `testmo_list_runs` | Covered |
| `/api/v1/runs/{run_id}` | GET | `testmo_get_run` | Covered |

### Run Results

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/runs/{run_id}/results` | GET | `testmo_list_run_results` | Covered |

### Sessions

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects/{project_id}/sessions` | GET | - | Not Covered |
| `/api/v1/sessions/{session_id}` | GET | - | Not Covered |

### Case Attachments

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/cases/{case_id}/attachments` | GET | `testmo_list_case_attachments` | Covered |
| `/api/v1/cases/{case_id}/attachments/single` | POST | `testmo_upload_case_attachment` | Covered |
| `/api/v1/cases/{case_id}/attachments` | DELETE | `testmo_delete_case_attachments` | Covered |

### Automation Sources

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects/{project_id}/automation/sources` | GET | `testmo_list_automation_sources` | Covered |
| `/api/v1/automation/sources/{automation_source_id}` | GET | `testmo_get_automation_source` | Covered |

### Automation Runs

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/projects/{project_id}/automation/runs` | GET | `testmo_list_automation_runs` | Covered |
| `/api/v1/projects/{project_id}/automation/runs` | POST | `testmo_create_automation_run` | Covered |
| `/api/v1/automation/runs/{automation_run_id}` | GET | `testmo_get_automation_run` | Covered |
| `/api/v1/automation/runs/{automation_run_id}/append` | POST | `testmo_append_automation_run` | Covered |
| `/api/v1/automation/runs/{automation_run_id}/complete` | POST | `testmo_complete_automation_run` | Covered |
| `/api/v1/automation/runs/{automation_run_id}/threads` | POST | `testmo_create_automation_run_thread` | Covered |
| `/api/v1/automation/runs/threads/{thread_id}/append` | POST | `testmo_append_automation_run_thread` | Covered |
| `/api/v1/automation/runs/threads/{thread_id}/complete` | POST | `testmo_complete_automation_run_thread` | Covered |

### Users

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/user` | GET | - | Not Covered |
| `/api/v1/users` | GET | - | Not Covered |
| `/api/v1/users/{user_id}` | GET | - | Not Covered |
| `/api/v1/projects/{project_id}/users` | GET | - | Not Covered |

### Groups

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/groups` | GET | - | Not Covered |
| `/api/v1/groups/{group_id}` | GET | - | Not Covered |

### Roles

| Endpoint | Method | MCP Tool | Status |
|----------|--------|----------|--------|
| `/api/v1/roles` | GET | - | Not Covered |
| `/api/v1/roles/{role_id}` | GET | - | Not Covered |

## Utility Tools

These tools don't map directly to API endpoints but provide additional functionality:

| MCP Tool | Description |
|----------|-------------|
| `testmo_get_field_mappings` | Returns field value mappings for your Testmo instance (priorities, types, states, etc.) |
| `testmo_get_web_url` | Generates web URLs for viewing resources in Testmo |

## Not Covered (Planned for Future)

### Medium Priority
- **Users**: User listing and details
- **Groups**: Group management
- **Roles**: Role management

## Changelog

### 2026-02-28
- Added `testmo_create_automation_run` tool (POST create run)
- Added `testmo_append_automation_run` tool (POST append artifacts/fields/links)
- Added `testmo_complete_automation_run` tool (POST mark run complete)
- Added `testmo_create_automation_run_thread` tool (POST create thread)
- Added `testmo_append_automation_run_thread` tool (POST submit test results)
- Added `testmo_complete_automation_run_thread` tool (POST mark thread complete)
- Added `testmo_batch_update_cases` tool (PATCH bulk update cases with automation_links)
- Automation Runs coverage: 29% → 100% (8/8 endpoints)
- Overall coverage: 59% → 78% (29/37 endpoints)

### 2026-01-26
- Added `testmo_get_milestone` tool
- Added `testmo_list_run_results` tool
- Added `testmo_list_case_attachments` tool
- Added `testmo_upload_case_attachment` tool
- Added `testmo_delete_case_attachments` tool
- Added `testmo_list_automation_sources` tool
- Added `testmo_get_automation_source` tool
- Added `testmo_list_automation_runs` tool
- Added `testmo_get_automation_run` tool
- Enhanced existing tools with `expands` parameter support
- Refactored to clean architecture with registry pattern

### Initial Release
- Projects: list, get
- Folders: list, get, create, update, delete, find_by_name
- Milestones: list
- Test Cases: list, get_all, get, create, create_batch, batch_create, update, delete, batch_delete, search
- Test Runs: list, get
- Utility: get_field_mappings, get_web_url
