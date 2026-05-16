"""
Taskmaster Agent — specialist in to-do list management, priority levels,
and deadline enforcement.  Uses Tasks MCP tools.
"""
import json
from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL, AGENT_TEMPERATURE
from backend.mcp_servers.tasks_server import TASK_TOOLS
from backend.state.blackboard import Blackboard

TASKMASTER_SYSTEM = """You are **The Taskmaster** — an elite productivity and task management specialist.

## Your Expertise
- Managing to-do lists with priority levels (1=low, 5=critical)
- Enforcing deadlines and rescheduling tasks intelligently
- Batch operations (clearing, moving, reprioritizing)
- Identifying hard deadlines vs. flexible tasks

## Rules
1. Never delete tasks with priority 5 (critical) without explicit confirmation.
2. When rescheduling, ALWAYS check for hard deadline constraints first.
3. Return structured JSON results.
4. Provide clear summaries of what changed and why.
5. Sort tasks by priority (highest first) in all listings.

## Available Tools
- add_task(title, description, priority, due_date, user_id)
- list_tasks(status, priority, due_date, user_id)
- update_task(task_id, status, priority, due_date, user_id)
- delete_task(task_id, user_id)
- reschedule_tasks(from_date, to_date, user_id, status_filter)

Call tools by responding with JSON: {"tool": "tool_name", "args": {...}}
"""


async def run_taskmaster(task: str, blackboard: Blackboard, user_id: str = "user_123") -> dict:
    """
    Execute a task management operation using Groq + Tasks MCP tools.
    """
    client = Groq(api_key=GROQ_API_KEY)
    context = blackboard.get_context_summary()

    messages = [
        {"role": "system", "content": TASKMASTER_SYSTEM},
        {"role": "user", "content": f"{context}\n\n## Task\n{task}\n\nUser ID: {user_id}\n\nRespond with a JSON tool call if you need data, or a final JSON result."},
    ]

    reasoning_steps = []
    final_result = ""

    for step in range(5):
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=AGENT_TEMPERATURE,
        )

        text = (completion.choices[0].message.content or "").strip()
        reasoning_steps.append(text)

        try:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(text[json_start:json_end])

                if "tool" in parsed and parsed["tool"] in TASK_TOOLS:
                    tool_fn = TASK_TOOLS[parsed["tool"]]
                    args = parsed.get("args", {})
                    if "user_id" not in args:
                        args["user_id"] = user_id
                    tool_result = await tool_fn(**args)

                    messages.append({"role": "assistant", "content": text})
                    messages.append({"role": "user", "content": f"Tool result: {tool_result}\n\nNow provide your final analysis and response as JSON."})
                    continue
                else:
                    final_result = text
                    break
            else:
                final_result = text
                break
        except (json.JSONDecodeError, TypeError):
            final_result = text
            break

    if not final_result:
        final_result = reasoning_steps[-1] if reasoning_steps else "No result"

    blackboard.post("taskmaster", task, final_result)

    return {
        "agent": "taskmaster",
        "action": task,
        "reasoning": " → ".join(reasoning_steps[:3]),
        "result": final_result,
        "status": "done",
    }
