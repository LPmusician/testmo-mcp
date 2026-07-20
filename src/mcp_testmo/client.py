"""
Testmo API Client

Async HTTP client for interacting with the Testmo REST API.
Designed for use within the MCP server.
"""

import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestmoAPIError(Exception):
    """Custom exception for Testmo API errors."""

    def __init__(self, status_code: int, message: str, details: Any = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"Testmo API Error {status_code}: {message}")


class TestmoClient:
    """
    Async client for interacting with Testmo REST API.

    Usage:
        async with TestmoClient() as client:
            projects = await client.list_projects()

    Environment Variables:
        TESTMO_URL: Base URL for Testmo instance (e.g., https://your-instance.testmo.net)
        TESTMO_API_KEY: API token for authentication
    """

    MAX_CASES_PER_REQUEST = 100
    REQUEST_TIMEOUT = 30.0
    RATE_LIMIT_DELAY = 0.5

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize the Testmo client.

        Args:
            base_url: Testmo instance URL (default: TESTMO_URL env var)
            api_key: API token (default: TESTMO_API_KEY env var)
        """
        self.base_url = (base_url or os.environ.get("TESTMO_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("TESTMO_API_KEY", "")

        if not self.base_url:
            raise ValueError(
                "TESTMO_URL not set. Set environment variable or pass base_url parameter."
            )
        if not self.api_key:
            raise ValueError(
                "TESTMO_API_KEY not set. Set environment variable or pass api_key parameter."
            )

        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "TestmoClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url}/api/v1",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(self.REQUEST_TIMEOUT),
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, ensuring it's initialized."""
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with TestmoClient() as client:'"
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request."""
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
            )

            if response.status_code == 204:
                return {"success": True}

            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                raise TestmoAPIError(
                    response.status_code,
                    f"Request failed: {response.reason_phrase}",
                    error_body,
                )

            return response.json()

        except httpx.TimeoutException:
            raise TestmoAPIError(408, "Request timed out")
        except httpx.ConnectError as e:
            raise TestmoAPIError(0, f"Connection error: {e}")

    # =========================================================================
    # Projects
    # =========================================================================

    async def list_projects(self) -> list[dict[str, Any]]:
        """
        List all accessible projects.

        Returns:
            List of project objects with id, name, and other metadata.
        """
        result = await self._request("GET", "/projects")
        return result.get("result", [])

    async def get_project(self, project_id: int) -> dict[str, Any]:
        """
        Get details of a specific project.

        Args:
            project_id: The project ID.

        Returns:
            Project object with full details.
        """
        result = await self._request("GET", f"/projects/{project_id}")
        return result.get("result", result)

    # =========================================================================
    # Folders
    # =========================================================================

    async def list_folders(
        self,
        project_id: int,
        page: int = 1,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """
        List folders in a project (paginated).

        Args:
            project_id: The project ID.
            page: Page number (1-indexed).
            per_page: Number of folders per page (max 100).

        Returns:
            Paginated result with folders and pagination info.
        """
        return await self._request(
            "GET",
            f"/projects/{project_id}/folders",
            params={"page": page, "per_page": per_page},
        )

    async def get_all_folders(self, project_id: int) -> list[dict[str, Any]]:
        """
        Get all folders in a project (handles pagination automatically).

        Args:
            project_id: The project ID.

        Returns:
            List of all folder objects in the project.
        """
        all_folders: list[dict[str, Any]] = []
        page = 1

        while True:
            result = await self.list_folders(project_id, page=page, per_page=100)
            folders = result.get("result", [])
            all_folders.extend(folders)

            if result.get("next_page") is None:
                break
            page += 1
            await asyncio.sleep(self.RATE_LIMIT_DELAY)

        return all_folders

    async def get_folder(self, project_id: int, folder_id: int) -> dict[str, Any]:
        """
        Get details of a specific folder.

        Args:
            project_id: The project ID.
            folder_id: The folder ID.

        Returns:
            Folder object with full details.
        """
        result = await self._request(
            "GET", f"/projects/{project_id}/folders/{folder_id}"
        )
        return result.get("result", result)

    async def create_folder(
        self,
        project_id: int,
        name: str,
        parent_id: int | None = None,
        docs: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a folder in a project.

        Args:
            project_id: The project ID.
            name: Folder name.
            parent_id: Parent folder ID (None for root level).
            docs: Folder documentation / reference field. Useful for storing
                a link back to a source-of-truth (e.g., a Jira ticket URL).
                Accepts HTML.

        Returns:
            Created folder object.
        """
        folder_data: dict[str, Any] = {"name": name}
        if parent_id:
            folder_data["parent_id"] = parent_id
        if docs is not None:
            folder_data["docs"] = docs

        result = await self._request(
            "POST", f"/projects/{project_id}/folders", data={"folders": [folder_data]}
        )
        folders = result.get("result", [])
        return folders[0] if folders else result

    async def update_folder(
        self,
        project_id: int,
        folder_id: int,
        name: str | None = None,
        parent_id: int | None = None,
        docs: str | None = None,
    ) -> dict[str, Any]:
        """
        Update a folder.

        Args:
            project_id: The project ID.
            folder_id: The folder ID.
            name: New folder name (optional).
            parent_id: New parent folder ID (optional).
            docs: New folder documentation / reference (optional). Useful for
                storing a link back to a source-of-truth (e.g., a Jira ticket URL).
                Accepts HTML. Pass an empty string to clear.

        Returns:
            Updated folder object.
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if parent_id is not None:
            data["parent_id"] = parent_id
        if docs is not None:
            data["docs"] = docs

        result = await self._request(
            "PUT", f"/projects/{project_id}/folders/{folder_id}", data=data
        )
        return result.get("result", result)

    async def delete_folder(self, project_id: int, folder_id: int) -> dict[str, Any]:
        """
        Delete a folder.

        Args:
            project_id: The project ID.
            folder_id: The folder ID.

        Returns:
            Success status.
        """
        return await self._request(
            "DELETE", f"/projects/{project_id}/folders/{folder_id}"
        )

    async def find_folder_by_name(
        self,
        project_id: int,
        name: str,
        parent_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Find a folder by name at a specific level.

        Args:
            project_id: The project ID.
            name: Folder name to find.
            parent_id: Parent folder ID (None for root level).

        Returns:
            Folder object if found, None otherwise.
        """
        all_folders = await self.get_all_folders(project_id)

        for folder in all_folders:
            folder_parent = folder.get("parent_id") or 0
            search_parent = parent_id or 0

            if folder["name"] == name and folder_parent == search_parent:
                return folder

        return None

    # =========================================================================
    # Milestones
    # =========================================================================

    async def list_milestones(
        self,
        project_id: int,
        is_completed: bool | None = None,
        page: int = 1,
        per_page: int = 100,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List milestones in a project.

        Args:
            project_id: The project ID.
            is_completed: Filter by completion status.
            page: Page number.
            per_page: Results per page.
            expands: Related entities to include.

        Returns:
            Paginated list of milestone objects.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if is_completed is not None:
            params["is_completed"] = is_completed
        if expands:
            params["expands"] = ",".join(expands)

        return await self._request(
            "GET", f"/projects/{project_id}/milestones", params=params
        )

    async def get_milestone(
        self,
        milestone_id: int,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get details of a specific milestone.

        Args:
            milestone_id: The milestone ID.
            expands: Related entities to include.

        Returns:
            Milestone object with full details.
        """
        params: dict[str, Any] = {}
        if expands:
            params["expands"] = ",".join(expands)

        result = await self._request(
            "GET",
            f"/milestones/{milestone_id}",
            params=params if params else None,
        )
        return result.get("result", result)

    # =========================================================================
    # Test Cases
    # =========================================================================

    async def list_cases(
        self,
        project_id: int,
        folder_id: int | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """
        List test cases in a project (paginated).

        Args:
            project_id: The project ID.
            folder_id: Filter by folder (optional).
            page: Page number (1-indexed).
            per_page: Number of cases per page (max 100).

        Returns:
            Paginated result with test cases and pagination info.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if folder_id:
            params["folder_id"] = folder_id

        return await self._request(
            "GET", f"/projects/{project_id}/cases", params=params
        )

    async def get_all_cases(
        self,
        project_id: int,
        folder_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get all test cases in a project or folder (handles pagination).

        Args:
            project_id: The project ID.
            folder_id: Filter by folder (optional).

        Returns:
            List of all test case objects.
        """
        all_cases: list[dict[str, Any]] = []
        page = 1

        while True:
            result = await self.list_cases(
                project_id, folder_id=folder_id, page=page, per_page=100
            )
            cases = result.get("result", [])
            all_cases.extend(cases)

            if result.get("next_page") is None:
                break
            page += 1
            await asyncio.sleep(self.RATE_LIMIT_DELAY)

        return all_cases

    async def get_case(self, project_id: int, case_id: int) -> dict[str, Any]:
        """
        Get details of a specific test case.

        Args:
            project_id: The project ID (accepted for API symmetry but unused —
                Testmo's single-case GET endpoint doesn't scope by project;
                case IDs are globally unique).
            case_id: The test case ID.

        Returns:
            Test case object with full details.
        """
        # Testmo's single-case GET is `/cases/{id}`, not
        # `/projects/{project_id}/cases/{case_id}` (that path returns 404).
        # Keep the project_id parameter for backwards-compatible signatures.
        result = await self._request("GET", f"/cases/{case_id}")
        return result.get("result", result)

    # Fields Testmo's POST endpoint requires on every case, even when the
    # caller doesn't explicitly set them. When missing, we default to the
    # SwiftOtter Normal QA profile (Chrome, Latest, Desktop) so callers
    # don't have to memorize the required-field list.
    _CREATE_CASE_DEFAULT_BROWSER = [12]  # Chrome
    _CREATE_CASE_DEFAULT_BROWSER_VERSION = [20]  # Latest
    _CREATE_CASE_DEFAULT_DEVICE = [25]  # Desktop

    def _normalize_case_payload(self, case: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize a single case payload for the Testmo API.

        - Auto-fills required browser/device fields with SwiftOtter defaults
          if the caller omitted them.
        - Translates step objects from human-friendly ``{content, expected}``
          keys to Testmo's native ``{text1, text3}`` schema.
        - Leaves everything else alone.

        Returns a new dict; does not mutate the input.
        """
        normalized = dict(case)

        # Browser/device defaults
        if "custom_browser" not in normalized:
            normalized["custom_browser"] = list(self._CREATE_CASE_DEFAULT_BROWSER)
        if "custom_browser_version" not in normalized:
            normalized["custom_browser_version"] = list(
                self._CREATE_CASE_DEFAULT_BROWSER_VERSION
            )
        if "custom_device" not in normalized:
            normalized["custom_device"] = list(self._CREATE_CASE_DEFAULT_DEVICE)

        # Step field translation
        steps = normalized.get("custom_steps")
        if isinstance(steps, list):
            translated_steps = []
            for step in steps:
                if not isinstance(step, dict):
                    translated_steps.append(step)
                    continue
                new_step = dict(step)
                # Accept content/expected as friendlier aliases for text1/text3.
                if "content" in new_step and "text1" not in new_step:
                    new_step["text1"] = new_step.pop("content")
                if "expected" in new_step and "text3" not in new_step:
                    new_step["text3"] = new_step.pop("expected")
                translated_steps.append(new_step)
            normalized["custom_steps"] = translated_steps

        return normalized

    async def create_case(
        self, project_id: int, case_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a single test case.

        Auto-normalization applied (see ``_normalize_case_payload``):
        - Browser/device fields default to SwiftOtter Normal QA profile
          (Chrome / Latest / Desktop) when omitted.
        - ``custom_steps`` entries accept ``{content, expected}`` as aliases
          for Testmo's native ``{text1, text3}`` schema.

        If ``issues`` is present in ``case_data``, this method creates the
        case first (without issues, since some templates reject issues[] on
        POST) and then follows up with an ``update_case`` to attach them.
        The returned case reflects the post-update state.

        Args:
            project_id: The project ID.
            case_data: Test case data.

        Returns:
            Created test case object (with issues attached if supplied).
        """
        # Separate issues out — Testmo's template_id=2 rejects issues[]
        # on POST, so we attach via a follow-up update.
        pending_issues = case_data.get("issues")
        payload = dict(case_data)
        if pending_issues is not None:
            payload.pop("issues", None)

        result = await self.create_cases(project_id, [payload])
        cases = result.get("result", [])
        created = cases[0] if cases else result

        if pending_issues and isinstance(created, dict) and "id" in created:
            try:
                updated = await self.update_case(
                    project_id,
                    created["id"],
                    {"issues": pending_issues},
                )
                if isinstance(updated, dict):
                    return updated
            except TestmoAPIError:
                # Bubble the create result even if the issue-attach fails —
                # caller can retry the link separately.
                pass

        return created

    async def create_cases(
        self, project_id: int, cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Create multiple test cases in a batch.

        Args:
            project_id: The project ID.
            cases: List of test case objects (max 100 per request).

        Returns:
            API response with created cases.

        Raises:
            ValueError: If more than 100 cases are provided.
        """
        if len(cases) > self.MAX_CASES_PER_REQUEST:
            raise ValueError(
                f"Too many cases: {len(cases)}. Max is {self.MAX_CASES_PER_REQUEST}. "
                "Use batch_create_cases for larger batches."
            )

        normalized = [self._normalize_case_payload(c) for c in cases]

        return await self._request(
            "POST",
            f"/projects/{project_id}/cases",
            data={"cases": normalized},
        )

    async def batch_create_cases(
        self, project_id: int, cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Create test cases in batches (handles any number of cases).

        When a batch fails with an opaque validation error, this method falls
        back to per-case creates for that batch so the caller sees exactly
        which case(s) triggered the error, indexed by their position in the
        input list. Successful cases in the failed batch are still created.

        Args:
            project_id: The project ID.
            cases: List of test case objects.

        Returns:
            Combined result with all created cases and any errors. Errors
            include the input-list index so the caller can identify the
            bad case's payload.
        """
        all_created: list[dict[str, Any]] = []
        errors: list[str] = []

        for i in range(0, len(cases), self.MAX_CASES_PER_REQUEST):
            batch = cases[i : i + self.MAX_CASES_PER_REQUEST]
            batch_num = (i // self.MAX_CASES_PER_REQUEST) + 1

            try:
                result = await self.create_cases(project_id, batch)
                created = result.get("result", [])
                all_created.extend(created)
            except TestmoAPIError as batch_err:
                # Batch failed with an opaque error. Retry per-case so we
                # can surface which specific case(s) are bad. Successful
                # cases in the batch still get created.
                errors.append(
                    f"Batch {batch_num} bulk create failed: {batch_err.message}. "
                    f"Retrying per-case to isolate."
                )
                for j, case in enumerate(batch):
                    input_index = i + j
                    try:
                        single_result = await self.create_cases(project_id, [case])
                        single_created = single_result.get("result", [])
                        all_created.extend(single_created)
                    except TestmoAPIError as single_err:
                        errors.append(
                            f"Case at index {input_index} "
                            f"(name={case.get('name', '<unnamed>')}): "
                            f"{single_err.message}"
                        )
                        if single_err.details:
                            errors.append(f"  details: {single_err.details}")
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)

            if i + self.MAX_CASES_PER_REQUEST < len(cases):
                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        return {
            "result": all_created,
            "total_submitted": len(cases),
            "total_created": len(all_created),
            "errors": errors if errors else None,
        }

    # Fields the Testmo PATCH endpoint requires on every update, even
    # when the caller isn't changing them. When the caller supplies a
    # partial update that omits these, we fetch the existing case and
    # merge the current values in so the caller doesn't have to.
    _UPDATE_CASE_REQUIRED_FIELDS = (
        "custom_browser",
        "custom_browser_version",
        "custom_device",
    )

    async def update_case(
        self, project_id: int, case_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update a single test case via the bulk PATCH endpoint.

        Testmo's PATCH endpoint requires certain custom fields (browser,
        browser version, device) even when they aren't being changed. This
        method auto-fetches the existing case and merges any required fields
        the caller didn't supply, so partial updates like
        ``{"name": "New name"}`` just work.

        Args:
            project_id: The project ID.
            case_id: The test case ID.
            data: Fields to update. Only include fields you want to change;
                required custom fields are preserved automatically.

        Returns:
            Updated test case object.
        """
        # If any required fields are missing, fetch and merge them in
        missing = [
            f for f in self._UPDATE_CASE_REQUIRED_FIELDS if f not in data
        ]
        if missing:
            existing = await self.get_case(project_id, case_id)
            merged_data = dict(data)
            for field in missing:
                value = existing.get(field)
                # The GET response wraps these as [{id, name}, ...] objects,
                # but the PATCH endpoint expects [id, id, ...] bare IDs.
                if isinstance(value, list):
                    normalized = [
                        item.get("id") if isinstance(item, dict) else item
                        for item in value
                    ]
                    merged_data[field] = [n for n in normalized if n is not None]
                elif value is not None:
                    merged_data[field] = value
            data = merged_data

        result = await self.batch_update_cases(project_id, [case_id], data)
        # batch_update_cases returns list; extract the single case
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        return result

    async def batch_update_cases(
        self,
        project_id: int,
        ids: list[int],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Bulk update up to 100 test cases with the same field values.

        Args:
            project_id: The project ID.
            ids: List of case IDs to update (max 100).
            data: Fields to apply to all cases (folder_id, state_id,
                  custom_priority, tags, issues, automation_links, etc.).

        Returns:
            List of updated case objects.
        """
        payload: dict[str, Any] = {"ids": ids}
        payload.update(data)

        result = await self._request(
            "PATCH",
            f"/projects/{project_id}/cases",
            data=payload,
        )
        return result.get("result", result)

    async def delete_case(self, project_id: int, case_id: int) -> dict[str, Any]:
        """
        Delete a single test case via the bulk DELETE endpoint.

        Args:
            project_id: The project ID.
            case_id: The test case ID.

        Returns:
            Success status.
        """
        return await self.batch_delete_cases(project_id, [case_id])

    async def batch_delete_cases(
        self, project_id: int, case_ids: list[int]
    ) -> dict[str, Any]:
        """
        Delete up to 100 test cases in a single request.

        Args:
            project_id: The project ID.
            case_ids: List of test case IDs to delete (max 100).

        Returns:
            Success status (204 No Content from API).
        """
        return await self._request(
            "DELETE",
            f"/projects/{project_id}/cases",
            data={"ids": case_ids},
        )

    # =========================================================================
    # Search
    # =========================================================================

    # Fields kept when summary_only=True on search_cases. Everything else
    # (custom_steps, custom_expected, custom_preconditions, etc.) is dropped
    # to keep responses compact — Testmo case bodies can be huge and easily
    # overflow LLM context when scanning many cases at once.
    _SEARCH_SUMMARY_FIELDS = (
        "id",
        "key",
        "name",
        "folder_id",
        "state_id",
        "status_id",
        "tags",
        "issues",
        "custom_priority",
        "created_at",
        "updated_at",
    )

    async def search_cases(
        self,
        project_id: int,
        query: str | None = None,
        folder_id: int | None = None,
        tags: list[str] | None = None,
        state_id: int | None = None,
        page: int = 1,
        per_page: int = 25,
        summary_only: bool = True,
    ) -> dict[str, Any]:
        """
        Search for test cases with filters.

        By default, results are returned in ``summary_only`` mode: each case
        is stripped to core identifying fields (id, key, name, folder_id,
        state_id, tags, issues, priority, timestamps). This keeps responses
        compact enough to scan through many results without overflowing LLM
        context. Full case bodies (steps, expected, preconditions, HTML
        content) are dropped in summary mode — fetch specific cases with
        ``get_case`` when you need the full body.

        Args:
            project_id: The project ID.
            query: Search query string (searches name and description).
            folder_id: Filter by folder.
            tags: Filter by tags.
            state_id: Filter by state.
            page: Page number.
            per_page: Results per page. Default 25 (down from Testmo's 100)
                to keep responses small when combined with summary_only.
            summary_only: When True (default), strip each case to core
                identifying fields. Set False for full case bodies.

        Returns:
            Paginated search results.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if query:
            params["query"] = query
        if folder_id:
            params["folder_id"] = folder_id
        if tags:
            params["tags"] = ",".join(tags)
        if state_id:
            params["state_id"] = state_id

        result = await self._request(
            "GET", f"/projects/{project_id}/cases", params=params
        )

        if summary_only:
            cases = result.get("result", result if isinstance(result, list) else [])
            if isinstance(cases, list):
                summarized = [
                    {k: case.get(k) for k in self._SEARCH_SUMMARY_FIELDS if k in case}
                    for case in cases
                ]
                if isinstance(result, dict):
                    result = {**result, "result": summarized}
                else:
                    result = summarized

        return result

    # =========================================================================
    # Test Runs
    # =========================================================================

    async def list_runs(
        self,
        project_id: int,
        page: int = 1,
        per_page: int = 100,
        is_closed: bool | None = None,
        milestone_id: str | None = None,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List test runs in a project.

        Args:
            project_id: The project ID.
            page: Page number.
            per_page: Results per page.
            is_closed: Filter by closed status.
            milestone_id: Comma-separated milestone IDs to filter by.
            expands: Related entities to include.

        Returns:
            Paginated list of test runs.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if is_closed is not None:
            params["is_closed"] = is_closed
        if milestone_id:
            params["milestone_id"] = milestone_id
        if expands:
            params["expands"] = ",".join(expands)

        return await self._request(
            "GET",
            f"/projects/{project_id}/runs",
            params=params,
        )

    async def get_run(
        self,
        run_id: int,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get details of a specific test run.

        Args:
            run_id: The test run ID.
            expands: Related entities to include.

        Returns:
            Test run object with full details.
        """
        params: dict[str, Any] = {}
        if expands:
            params["expands"] = ",".join(expands)

        result = await self._request(
            "GET",
            f"/runs/{run_id}",
            params=params if params else None,
        )
        return result.get("result", result)

    # =========================================================================
    # Run Results
    # =========================================================================

    async def list_run_results(
        self,
        run_id: int,
        status_id: str | None = None,
        assignee_id: str | None = None,
        created_by: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        get_latest_result: bool | None = None,
        page: int = 1,
        per_page: int = 100,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List test results for a run with optional filters.

        Args:
            run_id: The test run ID.
            status_id: Comma-separated status IDs to filter by.
            assignee_id: Comma-separated assignee IDs to filter by.
            created_by: Comma-separated user IDs who created results.
            created_after: Filter results created after (ISO8601).
            created_before: Filter results created before (ISO8601).
            get_latest_result: If true, return only the latest result per test.
            page: Page number.
            per_page: Results per page.
            expands: Related entities to include.

        Returns:
            Paginated list of test results.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if status_id:
            params["status_id"] = status_id
        if assignee_id:
            params["assignee_id"] = assignee_id
        if created_by:
            params["created_by"] = created_by
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        if get_latest_result is not None:
            params["get_latest_result"] = get_latest_result
        if expands:
            params["expands"] = ",".join(expands)

        return await self._request(
            "GET",
            f"/runs/{run_id}/results",
            params=params,
        )

    # =========================================================================
    # Case Attachments
    # =========================================================================

    async def list_case_attachments(
        self,
        case_id: int,
        page: int = 1,
        per_page: int = 100,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List attachments for a test case.

        Args:
            case_id: The test case ID.
            page: Page number.
            per_page: Results per page.
            expands: Related entities to include.

        Returns:
            Paginated list of attachment objects.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if expands:
            params["expands"] = ",".join(expands)

        return await self._request(
            "GET",
            f"/cases/{case_id}/attachments",
            params=params,
        )

    async def upload_case_attachment(
        self,
        case_id: int,
        filename: str,
        content_base64: str,
        content_type: str = "application/octet-stream",
    ) -> dict[str, Any]:
        """
        Upload a single attachment to a test case.

        Args:
            case_id: The test case ID.
            filename: Name of the file.
            content_base64: Base64-encoded file content.
            content_type: MIME type of the file.

        Returns:
            Created attachment object.

        Raises:
            TestmoAPIError: If the upload fails or the base64 content is invalid.
        """
        import base64
        import binascii

        # Validate and decode base64 content
        try:
            file_content = base64.b64decode(content_base64)
        except binascii.Error as e:
            raise TestmoAPIError(
                400,
                f"Invalid base64 content: {e}",
                {"detail": "The content_base64 parameter must be valid base64-encoded data"},
            )

        # Use multipart form upload with error handling
        try:
            response = await self.client.post(
                f"/cases/{case_id}/attachments/single",
                files={"file": (filename, file_content, content_type)},
            )
        except httpx.TimeoutException:
            raise TestmoAPIError(408, "Upload request timed out")
        except httpx.ConnectError as e:
            raise TestmoAPIError(0, f"Connection error during upload: {e}")

        # Handle 204 No Content response
        if response.status_code == 204:
            return {"success": True}

        if response.status_code >= 400:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            raise TestmoAPIError(
                response.status_code,
                f"Upload failed: {response.reason_phrase}",
                error_body,
            )

        result = response.json()
        return result.get("result", result)

    async def delete_case_attachments(
        self,
        case_id: int,
        attachment_ids: list[int],
    ) -> dict[str, Any]:
        """
        Delete one or more attachments from a test case.

        Args:
            case_id: The test case ID.
            attachment_ids: List of attachment IDs to delete.

        Returns:
            Success status.
        """
        return await self._request(
            "DELETE",
            f"/cases/{case_id}/attachments",
            data={"ids": attachment_ids},
        )

    # =========================================================================
    # Automation Sources
    # =========================================================================

    async def list_automation_sources(
        self,
        project_id: int,
        is_retired: bool | None = None,
        page: int = 1,
        per_page: int = 100,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List automation sources in a project.

        Args:
            project_id: The project ID.
            is_retired: Filter by retired status.
            page: Page number.
            per_page: Results per page.
            expands: Related entities to include.

        Returns:
            Paginated list of automation sources.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if is_retired is not None:
            params["is_retired"] = is_retired
        if expands:
            params["expands"] = ",".join(expands)

        return await self._request(
            "GET",
            f"/projects/{project_id}/automation/sources",
            params=params,
        )

    async def get_automation_source(
        self,
        automation_source_id: int,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get details of a specific automation source.

        Args:
            automation_source_id: The automation source ID.
            expands: Related entities to include.

        Returns:
            Automation source object with full details.
        """
        params: dict[str, Any] = {}
        if expands:
            params["expands"] = ",".join(expands)

        result = await self._request(
            "GET",
            f"/automation/sources/{automation_source_id}",
            params=params if params else None,
        )
        return result.get("result", result)

    # =========================================================================
    # Automation Runs
    # =========================================================================

    async def list_automation_runs(
        self,
        project_id: int,
        source_id: str | None = None,
        milestone_id: str | None = None,
        status: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        tags: str | None = None,
        page: int = 1,
        per_page: int = 100,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List automation runs in a project.

        Args:
            project_id: The project ID.
            source_id: Comma-separated automation source IDs to filter by.
            milestone_id: Comma-separated milestone IDs to filter by.
            status: Comma-separated status values (2=Success, 3=Failure, 4=Running).
            created_after: Filter runs created after (ISO8601).
            created_before: Filter runs created before (ISO8601).
            tags: Comma-separated tags to filter by.
            page: Page number.
            per_page: Results per page.
            expands: Related entities to include.

        Returns:
            Paginated list of automation runs.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if source_id:
            params["source_id"] = source_id
        if milestone_id:
            params["milestone_id"] = milestone_id
        if status:
            params["status"] = status
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        if tags:
            params["tags"] = tags
        if expands:
            params["expands"] = ",".join(expands)

        return await self._request(
            "GET",
            f"/projects/{project_id}/automation/runs",
            params=params,
        )

    async def get_automation_run(
        self,
        automation_run_id: int,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get details of a specific automation run.

        Args:
            automation_run_id: The automation run ID.
            expands: Related entities to include.

        Returns:
            Automation run object with full details.
        """
        params: dict[str, Any] = {}
        if expands:
            params["expands"] = ",".join(expands)

        result = await self._request(
            "GET",
            f"/automation/runs/{automation_run_id}",
            params=params if params else None,
        )
        return result.get("result", result)

    async def create_automation_run(
        self,
        project_id: int,
        name: str,
        source: str,
        config: str | None = None,
        config_id: int | None = None,
        milestone: str | None = None,
        milestone_id: int | None = None,
        tags: list[str] | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        fields: list[dict[str, Any]] | None = None,
        links: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new automation run.

        Args:
            project_id: The project ID.
            name: Name of the automation run.
            source: Name of the automation source (auto-created if new).
            config: Configuration name (optional).
            config_id: Configuration ID (takes precedence over config).
            milestone: Milestone name (optional).
            milestone_id: Milestone ID (takes precedence over milestone).
            tags: List of tags for the run.
            artifacts: List of artifact objects (name, url, mime_type, size).
            fields: List of field objects (name, type, value).
            links: List of link objects (name, url).

        Returns:
            Dict with the created run ID: {"id": <int>}.
        """
        data: dict[str, Any] = {"name": name, "source": source}
        if config is not None:
            data["config"] = config
        if config_id is not None:
            data["config_id"] = config_id
        if milestone is not None:
            data["milestone"] = milestone
        if milestone_id is not None:
            data["milestone_id"] = milestone_id
        if tags:
            data["tags"] = tags
        if artifacts:
            data["artifacts"] = artifacts
        if fields:
            data["fields"] = fields
        if links:
            data["links"] = links

        return await self._request(
            "POST",
            f"/projects/{project_id}/automation/runs",
            data=data,
        )

    async def append_automation_run(
        self,
        automation_run_id: int,
        artifacts: list[dict[str, Any]] | None = None,
        fields: list[dict[str, Any]] | None = None,
        links: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Append artifacts, fields, or links to an existing automation run.

        Args:
            automation_run_id: The automation run ID.
            artifacts: List of artifact objects to append.
            fields: List of field objects to append.
            links: List of link objects to append.

        Returns:
            Success status (HTTP 204).
        """
        data: dict[str, Any] = {}
        if artifacts:
            data["artifacts"] = artifacts
        if fields:
            data["fields"] = fields
        if links:
            data["links"] = links

        return await self._request(
            "POST",
            f"/automation/runs/{automation_run_id}/append",
            data=data,
        )

    async def complete_automation_run(
        self,
        automation_run_id: int,
        measure_elapsed: bool | None = None,
    ) -> dict[str, Any]:
        """
        Mark an automation run as completed.

        Args:
            automation_run_id: The automation run ID.
            measure_elapsed: Auto-set execution time from creation to completion.

        Returns:
            Success status (HTTP 204).
        """
        data: dict[str, Any] = {}
        if measure_elapsed is not None:
            data["measure_elapsed"] = measure_elapsed

        return await self._request(
            "POST",
            f"/automation/runs/{automation_run_id}/complete",
            data=data if data else None,
        )

    async def create_automation_run_thread(
        self,
        automation_run_id: int,
        elapsed_observed: int | None = None,
        elapsed_computed: int | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new thread in an automation run.

        Args:
            automation_run_id: The automation run ID.
            elapsed_observed: Observed execution time in microseconds.
            elapsed_computed: Computed execution time in microseconds.
            artifacts: List of artifact objects.
            fields: List of field objects.

        Returns:
            Dict with the created thread ID: {"id": <int>}.
        """
        data: dict[str, Any] = {}
        if elapsed_observed is not None:
            data["elapsed_observed"] = elapsed_observed
        if elapsed_computed is not None:
            data["elapsed_computed"] = elapsed_computed
        if artifacts:
            data["artifacts"] = artifacts
        if fields:
            data["fields"] = fields

        return await self._request(
            "POST",
            f"/automation/runs/{automation_run_id}/threads",
            data=data if data else None,
        )

    async def append_automation_run_thread(
        self,
        thread_id: int,
        elapsed_observed: int | None = None,
        elapsed_computed: int | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        fields: list[dict[str, Any]] | None = None,
        tests: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Append results, artifacts, or fields to an automation run thread.

        Args:
            thread_id: The automation run thread ID.
            elapsed_observed: Partial observed time in microseconds to add.
            elapsed_computed: Partial computed time in microseconds to add.
            artifacts: List of artifact objects to append.
            fields: List of field objects to append.
            tests: List of test result objects to append.

        Returns:
            Success status (HTTP 204).
        """
        data: dict[str, Any] = {}
        if elapsed_observed is not None:
            data["elapsed_observed"] = elapsed_observed
        if elapsed_computed is not None:
            data["elapsed_computed"] = elapsed_computed
        if artifacts:
            data["artifacts"] = artifacts
        if fields:
            data["fields"] = fields
        if tests:
            data["tests"] = tests

        return await self._request(
            "POST",
            f"/automation/runs/threads/{thread_id}/append",
            data=data,
        )

    async def complete_automation_run_thread(
        self,
        thread_id: int,
        elapsed_observed: int | None = None,
        elapsed_computed: int | None = None,
    ) -> dict[str, Any]:
        """
        Mark an automation run thread as completed.

        Args:
            thread_id: The automation run thread ID.
            elapsed_observed: Observed execution time in microseconds.
            elapsed_computed: Computed execution time in microseconds.

        Returns:
            Success status (HTTP 204).
        """
        data: dict[str, Any] = {}
        if elapsed_observed is not None:
            data["elapsed_observed"] = elapsed_observed
        if elapsed_computed is not None:
            data["elapsed_computed"] = elapsed_computed

        return await self._request(
            "POST",
            f"/automation/runs/threads/{thread_id}/complete",
            data=data if data else None,
        )

    # =========================================================================
    # Issue Connections
    # =========================================================================

    async def list_issue_connections(
        self,
        project_id: int | None = None,
        integration_type: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 100,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        List available issue integrations (GitHub, Jira, etc.).

        Args:
            project_id: Filter by project ID (optional).
            integration_type: Filter by integration type (e.g., 'github', 'jira').
            is_active: Filter by active status.
            page: Page number.
            per_page: Results per page.
            expands: Related entities to include.

        Returns:
            Paginated list of issue connection objects.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if project_id is not None:
            params["project_id"] = project_id
        if integration_type:
            params["integration_type"] = integration_type
        if is_active is not None:
            params["is_active"] = is_active
        if expands:
            params["expands"] = ",".join(expands)

        return await self._request(
            "GET",
            "/issues/connections",
            params=params,
        )

    async def get_issue_connection(
        self,
        connection_id: int,
        expands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get details of a specific issue connection.

        Args:
            connection_id: The issue connection ID.
            expands: Related entities to include.

        Returns:
            Issue connection object with full details.
        """
        params: dict[str, Any] = {}
        if expands:
            params["expands"] = ",".join(expands)

        result = await self._request(
            "GET",
            f"/issues/connections/{connection_id}",
            params=params if params else None,
        )
        return result.get("result", result)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_web_url(
        self,
        project_id: int,
        resource_type: str = "repositories",
        resource_id: int | None = None,
    ) -> str:
        """
        Generate a web URL for a Testmo resource.

        Args:
            project_id: The project ID.
            resource_type: Type of resource (repositories, runs, etc.)
            resource_id: Optional resource ID (folder ID, run ID, etc.)

        Returns:
            URL string for the resource.
        """
        url = f"{self.base_url}/{resource_type}/{project_id}"
        if resource_id:
            url += f"?group_id={resource_id}"
        return url
