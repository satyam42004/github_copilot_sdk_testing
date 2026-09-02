import asyncio
import json
import threading
from pathlib import Path

from copilot import CopilotClient, define_tool, ToolSet
from copilot.session_events import SessionEventType

from tools import list_files, read_file, search_code
from custom_tools import build_create_tool
from file_security import (
    FileAccessPolicy,
    build_default_file_access_policy,
    parse_allowed_folders,
)
from observability import configure_tracing, optional_span, record_event_span, flush_traces


class UsageTracker:
    """Track both session-level and per-request Copilot usage."""

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with getattr(self, "_lock", threading.Lock()):
            self.model = None
            self.input_tokens = 0
            self.output_tokens = 0
            self.cache_read_tokens = 0
            self.cache_write_tokens = 0
            self.reasoning_tokens = 0
            self.ai_credits = 0.0
            self.total_nano_aiu = 0.0
            self.assistant_calls = 0

            self.request_counter = 0
            self.current_request = None
            self.completed_requests = []

    def start_request(self, prompt: str):
        with self._lock:
            self.request_counter += 1
            request_id = f"REQ-{self.request_counter:04d}"
            self.current_request = {
                "request_id": request_id,
                "prompt": prompt[:1000],
                "status": "running",
                "model": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "reasoning_tokens": 0,
                "ai_credits": 0.0,
                "total_nano_aiu": 0.0,
                "assistant_calls": 0,
                "hitl_approvals": 0,
                "hitl_rejections": 0,
                "tools_started": 0,
                "tools_succeeded": 0,
                "tools_failed": 0,
                "last_tool": None,
                "last_tool_status": None,
            }
            record_event_span("copilot.request.started", {
                "copilot.request.id": request_id,
                "copilot.prompt": prompt[:1000],
            })
            print("\n" + "=" * 60)
            print(f"REQUEST START: {request_id}")
            print("=" * 60)
            return request_id

    def finish_request(self, status: str):
        with self._lock:
            if self.current_request is None:
                return None

            self.current_request["status"] = status
            self.current_request["total_tokens"] = (
                self.current_request["input_tokens"]
                + self.current_request["output_tokens"]
            )
            completed = dict(self.current_request)
            self.completed_requests.append(completed)
            self.completed_requests = self.completed_requests[-20:]

            record_event_span("copilot.request.completed", {
                "copilot.request.id": completed["request_id"],
                "copilot.request.status": status,
                "copilot.request.input_tokens": completed["input_tokens"],
                "copilot.request.output_tokens": completed["output_tokens"],
                "copilot.request.total_tokens": completed["total_tokens"],
                "copilot.request.ai_credits": completed["ai_credits"],
                "copilot.request.assistant_calls": completed["assistant_calls"],
                "copilot.request.hitl_approvals": completed["hitl_approvals"],
                "copilot.request.hitl_rejections": completed["hitl_rejections"],
                "copilot.request.tools_started": completed["tools_started"],
                "copilot.request.tools_succeeded": completed["tools_succeeded"],
                "copilot.request.tools_failed": completed["tools_failed"],
            })

            print("\n" + "=" * 60)
            print(f"REQUEST COMPLETE: {completed['request_id']}")
            print(f"Status: {status}")
            print(f"Model calls: {completed['assistant_calls']}")
            print(f"Request tokens: {completed['total_tokens']}")
            print(f"HITL approvals: {completed['hitl_approvals']}")
            print(f"HITL rejections: {completed['hitl_rejections']}")
            print(f"Tools succeeded: {completed['tools_succeeded']}")
            print(f"Tools failed: {completed['tools_failed']}")
            print("=" * 60)

            self.current_request = None
            return completed

    def _add_usage(self, d):
        with self._lock:
            input_tokens = d.input_tokens or 0
            output_tokens = d.output_tokens or 0
            cache_read = d.cache_read_tokens or 0
            cache_write = d.cache_write_tokens or 0
            reasoning = d.reasoning_tokens or 0
            cost = d.cost or 0.0

            self.model = d.model
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.cache_read_tokens += cache_read
            self.cache_write_tokens += cache_write
            self.reasoning_tokens += reasoning
            self.assistant_calls += 1
            self.ai_credits += cost

            if self.current_request is not None:
                r = self.current_request
                r["model"] = d.model
                r["input_tokens"] += input_tokens
                r["output_tokens"] += output_tokens
                r["cache_read_tokens"] += cache_read
                r["cache_write_tokens"] += cache_write
                r["reasoning_tokens"] += reasoning
                r["ai_credits"] += cost
                r["assistant_calls"] += 1

            record_event_span("copilot.usage", {
                "gen_ai.request.model": d.model or "unknown",
                "gen_ai.usage.input_tokens": input_tokens,
                "gen_ai.usage.output_tokens": output_tokens,
                "copilot.usage.cache_read_tokens": cache_read,
                "copilot.usage.cache_write_tokens": cache_write,
                "copilot.usage.reasoning_tokens": reasoning,
                "copilot.usage.ai_credits": cost,
            })

            print("\n" + "-" * 60)
            print("ASSISTANT USAGE")
            print("-" * 60)
            print(f"Model:              {d.model}")
            print(f"Input tokens:       {input_tokens}")
            print(f"Output tokens:      {output_tokens}")
            print(f"Cache read tokens:  {cache_read}")
            print(f"Cache write tokens: {cache_write}")
            print(f"Reasoning tokens:   {reasoning}")
            print(f"AI credits:         {cost}")

    def handle_event(self, event):
        if event.type == SessionEventType.ASSISTANT_USAGE:
            self._add_usage(event.data)

        elif event.type == SessionEventType.SESSION_USAGE_CHECKPOINT:
            d = event.data
            with self._lock:
                self.total_nano_aiu = getattr(d, "total_nano_aiu", 0) or 0

    def record_hitl(self, approved: bool):
        with self._lock:
            if self.current_request is not None:
                key = "hitl_approvals" if approved else "hitl_rejections"
                self.current_request[key] += 1

    def record_tool_started(self, tool_name: str):
        with self._lock:
            if self.current_request is not None:
                self.current_request["tools_started"] += 1
                self.current_request["last_tool"] = tool_name
                self.current_request["last_tool_status"] = "started"

    def record_tool_finished(self, tool_name: str, success: bool):
        with self._lock:
            if self.current_request is not None:
                key = "tools_succeeded" if success else "tools_failed"
                self.current_request[key] += 1
                self.current_request["last_tool"] = tool_name
                self.current_request["last_tool_status"] = (
                    "success" if success else "failure"
                )

    def get_usage(self):
        with self._lock:
            current = (
                dict(self.current_request)
                if self.current_request is not None
                else None
            )
            if current:
                current["total_tokens"] = (
                    current["input_tokens"] + current["output_tokens"]
                )

            last_completed = (
                dict(self.completed_requests[-1])
                if self.completed_requests
                else None
            )

            return {
                "model": self.model or "unknown",
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.input_tokens + self.output_tokens,
                "cache_read_tokens": self.cache_read_tokens,
                "cache_write_tokens": self.cache_write_tokens,
                "reasoning_tokens": self.reasoning_tokens,
                "ai_credits": self.ai_credits,
                "total_nano_aiu": self.total_nano_aiu,
                "assistant_calls": self.assistant_calls,
                "current_request": current,
                "last_completed_request": last_completed,
                "completed_requests": list(self.completed_requests[-20:]),
            }


class CopilotService:
    def __init__(self):
        self.client = self.session = self.repository_path = None
        self.file_access_policy = None
        self.usage_tracker = UsageTracker()
        self.loop = self.loop_thread = None
        self.ready = threading.Event()

        self.approval_required = False
        self.pending_tool = self.pending_arguments = None
        self.approval_result = None
        self.approval_event = None

        self.agent_running = False
        self.agent_result = self.agent_error = None

        self.last_approval_decision = None
        self.last_approved_tool = self.last_approved_arguments = None
        self.last_denied_operation = None
        self.current_request_id = None
        self.current_request_status = None

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.ready.set()
        self.loop.run_forever()

    def _ensure_loop(self):
        if self.loop is None or self.loop_thread is None or not self.loop_thread.is_alive():
            self.ready.clear()
            self.loop_thread = threading.Thread(target=self._run_loop, daemon=True)
            self.loop_thread.start()
            self.ready.wait()

    def start(self, github_token: str | None, repository_path: str,
              allowed_folders: list[str] | None = None):
        configure_tracing()
        self.usage_tracker.reset()
        self._ensure_loop()
        f = asyncio.run_coroutine_threadsafe(
            self._async_start(github_token, repository_path, allowed_folders),
            self.loop,
        )
        return f.result()

    async def _async_start(self, github_token, repository_path, allowed_folders=None):
        repository = Path(repository_path).expanduser().resolve()
        if not repository.exists():
            raise ValueError(f"Repository does not exist:\n{repository}")
        if not repository.is_dir():
            raise ValueError(f"Repository path is not a directory:\n{repository}")

        self.repository_path = repository

        if allowed_folders:
            configured = parse_allowed_folders(allowed_folders, repository)
            self.file_access_policy = FileAccessPolicy(
                allowed_read_paths=configured,
                allowed_write_paths=configured,
            )
        else:
            self.file_access_policy = build_default_file_access_policy(repository)

        create_tool = build_create_tool(str(repository), self.file_access_policy)

        with optional_span("copilot.session.start", {
            "copilot.repository": str(repository),
            "copilot.auth_mode": "github_token" if github_token else "existing_login",
        }):
            if github_token:
                self.client = CopilotClient(
                    github_token=github_token.strip(),
                    use_logged_in_user=False,
                )
            else:
                self.client = CopilotClient(use_logged_in_user=True)

            await self.client.start()

            context = f"""
CURRENT LOCAL REPOSITORY:
{repository}

FILESYSTEM ACCESS POLICY:
- The repository is always allowed.
- Configured additional folders are allowed.
- Desktop is allowed by default.
- Downloads and Documents are blocked unless explicitly configured.
- The filesystem policy is authoritative.
"""

            available_tools = ToolSet()
            available_tools.add_custom("list_files")
            available_tools.add_custom("read_file")
            available_tools.add_custom("search_code")
            available_tools.add_custom("create")
            self.session = await self.client.create_session(
                model="gpt-5-mini",
                working_directory=r"C:\Users\satya\Desktop\copilot_empty_test",
                tools=[list_files, read_file, search_code, create_tool],
                available_tools=available_tools,
                enable_on_demand_instruction_discovery=True,
                on_event=self.usage_tracker.handle_event,
                hooks={
                    "on_pre_tool_use": self._pre_tool_use,
                    "on_post_tool_use": self._post_tool_use,
                    "on_post_tool_use_failure": self._post_tool_use_failure,
                },
                system_message={
    "mode": "append",
    "content": f"""
You are a software development assistant.

REPOSITORY:
{repository}

FILESYSTEM POLICY:
- Repository and configured folders are allowed.
- Desktop is allowed by default.
- Downloads and Documents are blocked unless explicitly configured.
- The filesystem policy is authoritative.

TOOLS:
- Use repository tools for repository operations.
- For NEW files, always use the custom create tool.
- Never use PowerShell or another tool to bypass file restrictions.
- Use the exact requested destination.
- If create returns BLOCKED, stop and report the block.

SECURITY:
- File writes, deletion, commits, pushes, and destructive actions require HITL approval.
- Never bypass HITL or retry a rejected operation.
- Never claim an operation succeeded unless it actually succeeded.
- Never expose secrets.
"""
},
            )

        print("[OK] Copilot session created.")
        print("[OK] Repository tools configured.")
        print("[OK] Filesystem access policy configured.")
        record_event_span("copilot.session.ready", {
            "repository": str(repository),
            "custom_tools": "list_files,read_file,search_code,create",
        })
        flush_traces()

    def get_usage(self):
        return self.usage_tracker.get_usage()

    def get_file_access_policy(self):
        if self.file_access_policy is None:
            return {"read": [], "write": []}
        return self.file_access_policy.describe()

    def get_repository_status(self):
        if not self.repository_path:
            return {"accessible": False, "path": None,
                    "message": "No repository is configured."}
        p = Path(self.repository_path)
        ok = p.exists() and p.is_dir()
        return {
            "accessible": ok,
            "path": str(p),
            "message": "Local repository is accessible." if ok else
                       "Local repository is not accessible.",
        }

    def _classify_tool(self, tool_name, tool_args):
        if tool_name in {"list_files", "read_file", "search_code"}:
            return "LOW"
        if tool_name in {
            "create", "write", "write_file", "edit", "delete",
            "remove", "rename", "move", "copy", "git_commit", "git_push",
        }:
            return "HIGH"

        if tool_name == "powershell":
            try:
                parsed = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
                command = str(parsed.get("command", "")).strip()
            except Exception:
                command = str(tool_args)
            c = command.lower().strip()

            mutations = [
                "remove-item", "del ", "erase ", "rmdir", "format-",
                "clear-content", "set-content", "add-content", "out-file",
                "new-item", "move-item", "copy-item", "rename-item",
                "git push", "git reset --hard", "git clean",
                "git checkout --", "git restore",
            ]
            if any(x in c for x in mutations):
                return "HIGH"

            reads = [
                "get-childitem", "get-content", "select-string",
                "get-location", "get-item", "test-path", "get-filehash",
                "git status", "git log", "git branch", "git diff", "git show",
            ]
            if any(c.startswith(x) for x in reads):
                return "LOW"
            return "MEDIUM"

        return "MEDIUM"

    async def _pre_tool_use(self, input_data, invocation):
        tool_name = input_data.get("toolName", "unknown")
        tool_args = input_data.get("toolArgs", {})

        if tool_name == "edit":
            try:
                args = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
            except Exception:
                args = {}

            path_value = args.get("path")
            if path_value:
                target = Path(path_value).expanduser()
                if not target.is_absolute():
                    target = Path(self.repository_path) / target
                target = target.resolve()

                old_str = args.get("old_str", None)

                # Prevent SDK edit from being used as an alternate create.
                if not target.exists() and (old_str is None or old_str == ""):
                    self.last_approval_decision = "rejected"
                    self.last_denied_operation = {
                        "tool": "edit",
                        "arguments": tool_args,
                        "reason": "New files must use the policy-aware create tool.",
                    }
                    record_event_span("copilot.tool.approval", {
                        "tool.name": "edit",
                        "hitl.risk": "BLOCKED",
                        "hitl.decision": "deny",
                        "hitl.source": "file_creation_policy",
                    })
                    return {
                        "permissionDecision": "deny",
                        "permissionDecisionReason":
                            "New-file creation must use the custom create tool.",
                    }

                try:
                    self.file_access_policy.validate(target, "write")
                except Exception as exc:
                    self.last_approval_decision = "rejected"
                    self.last_denied_operation = {
                        "tool": "edit",
                        "arguments": tool_args,
                        "reason": str(exc),
                    }
                    return {
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"File access denied: {exc}",
                    }

        if tool_name == "powershell":
            try:
                parsed = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
                command = str(parsed.get("command", "")).strip()
            except Exception:
                command = str(tool_args)

            c = command.lower()
            mutations = [
                "set-content", "add-content", "out-file", "new-item",
                "remove-item", "move-item", "copy-item", "rename-item",
                "del ", "erase ", "rmdir", "rd ", ">", ">>",
            ]
            if any(x in c for x in mutations):
                self.last_approval_decision = "rejected"
                self.last_denied_operation = {
                    "tool": tool_name,
                    "arguments": tool_args,
                    "reason": "Filesystem-changing PowerShell is blocked.",
                }
                return {
                    "permissionDecision": "deny",
                    "permissionDecisionReason":
                        "Filesystem-changing PowerShell commands are blocked.",
                }

        risk = self._classify_tool(tool_name, tool_args)
        self.usage_tracker.record_tool_started(tool_name)

        if risk == "LOW":
            record_event_span("copilot.tool.approval", {
                "tool.name": tool_name,
                "tool.risk": risk,
                "hitl.decision": "allow",
                "hitl.source": "automatic",
            })
            print(f"[HITL] Automatically allowing low-risk tool: {tool_name}")
            return {
                "permissionDecision": "allow",
                "permissionDecisionReason": "Low-risk read-only operation.",
            }

        self.approval_required = True
        self.pending_tool = tool_name
        self.pending_arguments = tool_args
        self.approval_result = None
        self.approval_event = asyncio.Event()

        print("=" * 60)
        print("HUMAN-IN-THE-LOOP APPROVAL REQUIRED")
        print("=" * 60)
        print(f"Tool: {tool_name}")
        print(f"Risk: {risk}")
        print(f"Arguments: {tool_args}")
        print("=" * 60)

        with optional_span("copilot.tool.approval", {
            "tool.name": tool_name,
            "tool.risk": risk,
            "hitl.source": "human",
        }) as span:
            await self.approval_event.wait()
            approved = self.approval_result
            if span:
                span.set_attribute("hitl.decision", "allow" if approved else "deny")

        if approved:
            self.last_approval_decision = "approved"
            self.usage_tracker.record_hitl(True)
            self.last_approved_tool = tool_name
            self.last_approved_arguments = tool_args
        else:
            self.last_approval_decision = "rejected"
            self.usage_tracker.record_hitl(False)
            self.last_denied_operation = {
                "tool": tool_name,
                "arguments": tool_args,
            }

        self.approval_required = False
        self.pending_tool = None
        self.pending_arguments = None
        self.approval_result = None
        self.approval_event = None

        return {
            "permissionDecision": "allow" if approved else "deny",
            "permissionDecisionReason":
                "Explicitly approved by the user."
                if approved else
                "Explicitly rejected by the user.",
        }

    async def _post_tool_use(self, input_data, invocation):
        tool_name = input_data.get("toolName", "unknown")
        self.usage_tracker.record_tool_finished(tool_name, True)
        record_event_span("copilot.tool.completed", {
            "tool.name": tool_name,
            "tool.status": "success",
        })

    async def _post_tool_use_failure(self, input_data, invocation):
        tool_name = input_data.get("toolName", "unknown")
        self.usage_tracker.record_tool_finished(tool_name, False)
        record_event_span("copilot.tool.completed", {
            "tool.name": tool_name,
            "tool.status": "failure",
        })

    def get_pending_approval(self):
        if not self.approval_required:
            return None
        return {"tool": self.pending_tool, "arguments": self.pending_arguments}

    def approve(self):
        if not self.approval_required or self.approval_event is None:
            return False
        self.approval_result = True
        self.loop.call_soon_threadsafe(self.approval_event.set)
        return True

    def reject(self):
        if not self.approval_required or self.approval_event is None:
            return False
        self.approval_result = False
        self.loop.call_soon_threadsafe(self.approval_event.set)
        return True

    def ask(self, prompt: str):
        if self.loop is None:
            raise RuntimeError("Copilot event loop is not running.")
        if self.session is None:
            raise RuntimeError("Copilot session is not initialized.")

        self.last_approval_decision = None
        self.last_approved_tool = None
        self.last_approved_arguments = None
        self.last_denied_operation = None
        self.current_request_status = "running"
        self.current_request_id = self.usage_tracker.start_request(prompt)

        f = asyncio.run_coroutine_threadsafe(
            self._async_ask(prompt),
            self.loop,
        )
        return f.result()

    async def _async_ask(self, prompt):
        status = "failed"

        with optional_span("copilot.agent.turn", {
            "openinference.span.kind": "AGENT",
            "copilot.prompt": prompt[:1000],
            "copilot.request.id": self.current_request_id or "unknown",
        }):
            try:
                response = await self.session.send_and_wait(prompt)

                if self.last_approval_decision == "rejected":
                    status = "rejected"
                    return (
                        "❌ **Operation declined or blocked**\n\n"
                        "The requested operation was rejected or blocked "
                        "and was not performed."
                    )

                status = "success"

                if self.last_approval_decision == "approved":
                    return "✅ **Operation approved**\n\n" + response.data.content

                return response.data.content
            except Exception:
                status = "failed"
                raise
            finally:
                self.current_request_status = status
                self.usage_tracker.finish_request(status)
                flush_traces()

    def ask_background(self, prompt: str):
        if self.agent_running:
            return False

        self.agent_result = self.agent_error = None
        self.agent_running = True

        def worker():
            try:
                self.agent_result = self.ask(prompt)
            except Exception as exc:
                self.agent_error = str(exc)
            finally:
                self.agent_running = False

        threading.Thread(target=worker, daemon=True).start()
        return True

    def get_agent_state(self):
        usage = self.usage_tracker.get_usage()
        current = usage.get("current_request") or {}
        return {
            "running": self.agent_running,
            "result": self.agent_result,
            "error": self.agent_error,
            "request_id": current.get("request_id"),
            "request_status": current.get("status"),
        }

    def clear_agent_result(self):
        self.agent_result = None
        self.agent_error = None

    def stop(self):
        if self.loop is None:
            return

        try:
            f = asyncio.run_coroutine_threadsafe(self._async_stop(), self.loop)
            f.result(timeout=10)
        except Exception:
            pass

        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass

        self.client = self.session = self.repository_path = None
        self.file_access_policy = None
        self.loop = self.loop_thread = None
        self.agent_running = False

    async def _async_stop(self):
        if self.client is not None:
            await self.client.stop()
        flush_traces()
