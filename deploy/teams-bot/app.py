"""Phase 0 Teams bot: read-only Claude agent over the company docs. See README.md."""
import asyncio
import logging
import os
import time
from os import environ

from aiohttp import web
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter, jwt_authorization_middleware, start_agent_process
from microsoft_agents.hosting.core import AgentApplication, Authorization, MemoryStorage, TurnContext, TurnState

import botlogic as bl

DATA_DIR = environ.get("DATA_DIR", "/data")
COMPANIES_DIR = environ.get("COMPANIES_DIR", "/workspace/companies")
PLUGINS_DIR = environ.get("PLUGINS_DIR", "/opt/ai-team-plugins/plugins")
ALLOWED_USERS = bl.parse_list(environ.get("ALLOWED_USERS"))
DEFAULT_COMPANY = environ.get("DEFAULT_COMPANY", "catice")
CHANNEL_COMPANY_MAP = dict(p.split("=", 1) for p in bl.parse_list(environ.get("CHANNEL_COMPANY_MAP")))
MODEL = environ.get("BOT_MODEL", "claude-sonnet-5-5")  # model-selection: Sonnet is the default tier
MAX_BUDGET_USD = float(environ.get("MAX_BUDGET_USD", "0.50"))

# Phase 0 is read-only: no Bash, no file writes, no subagents, no MCP servers.
READ_ONLY_TOOLS = ["Read", "Glob", "Grep", "Skill", "WebSearch", "WebFetch"]
BLOCKED_TOOLS = ["Bash", "Write", "Edit", "NotebookEdit", "Agent", "Workflow"]

sessions = bl.SessionStore(os.path.join(DATA_DIR, "sessions.json"))
config = load_configuration_from_env(environ)
storage = MemoryStorage()
connection_manager = MsalConnectionManager(**config)
adapter = CloudAdapter(connection_manager=connection_manager)
authorization = Authorization(storage, connection_manager, **config)
AGENT_APP = AgentApplication[TurnState](storage=storage, authorization=authorization, **config.get("AGENTAPPLICATION", {}))


def agent_options(company, session_id):
    return ClaudeAgentOptions(
        cwd=os.path.join(COMPANIES_DIR, company),
        setting_sources=["project"],  # company CLAUDE.md, rules, project skills
        plugins=[{"type": "local", "path": os.path.join(PLUGINS_DIR, p)} for p in ("platform-core", "marketing-core")],
        allowed_tools=READ_ONLY_TOOLS,
        disallowed_tools=BLOCKED_TOOLS,
        permission_mode="dontAsk",  # anything not allowed is silently denied — no one to answer a prompt
        mcp_servers={},
        strict_mcp_config=True,
        model=MODEL,
        max_budget_usd=MAX_BUDGET_USD,
        max_turns=30,
        resume=session_id,
    )


async def run_agent(prompt, company, conversation_id, user):
    started = time.time()
    result = None
    async for message in query(prompt=prompt, options=agent_options(company, sessions.get(conversation_id))):
        if isinstance(message, ResultMessage):
            result = message
    if result is None:
        return "ขออภัย ไม่ได้รับคำตอบจากระบบ"
    sessions.set(conversation_id, result.session_id)
    bl.append_jsonl(os.path.join(DATA_DIR, "usage.jsonl"), {
        "ts": int(started), "user": user, "company": company, "conversation": conversation_id,
        "cost_usd": result.total_cost_usd, "turns": result.num_turns, "is_error": result.is_error,
        "duration_ms": result.duration_ms,
    })
    if result.is_error:
        return f"เกิดข้อผิดพลาด ({result.subtype}) ลองใหม่อีกครั้ง หรือแจ้งผู้ดูแล"
    return result.result or "(ไม่มีข้อความตอบกลับ)"


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState) -> None:
    sender = context.activity.from_property
    aad_id = sender.aad_object_id if sender else None
    if not bl.is_allowed(aad_id, ALLOWED_USERS):
        await context.send_activity("บอทนี้ยังเปิดให้เฉพาะผู้ทดสอบ")
        return
    conversation_id = context.activity.conversation.id
    company = bl.company_for(conversation_id, CHANNEL_COMPANY_MAP, DEFAULT_COMPANY)
    prompt = context.activity.text or ""
    identity = context.identity
    reference = context.activity.get_conversation_reference()
    await context.send_activity(f"รับแล้ว กำลังทำ… ({company})")

    async def work():
        try:
            answer = await run_agent(prompt, company, conversation_id, aad_id)
        except Exception:  # never let a failure vanish silently in a background task
            logging.exception("agent run failed")
            answer = "เกิดข้อผิดพลาดภายใน แจ้งผู้ดูแลระบบ"

        async def send(turn_context: TurnContext):
            for chunk in bl.split_message(answer):
                await turn_context.send_activity(chunk)

        await adapter.continue_conversation_with_claims(identity, reference.get_continuation_activity(), send)

    # Teams expects the HTTP call answered within seconds; the real reply goes out proactively.
    asyncio.create_task(work())


async def messages(request: web.Request) -> web.Response:
    response = await start_agent_process(request, AGENT_APP, adapter)
    return response or web.Response(status=202)


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application(middlewares=[jwt_authorization_middleware])
    app["agent_configuration"] = connection_manager.get_default_connection_configuration()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/healthz", health)
    web.run_app(app, host="0.0.0.0", port=int(environ.get("PORT", "3978")))


if __name__ == "__main__":
    main()
