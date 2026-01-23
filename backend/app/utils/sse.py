# backend/app/utils/sse.py
import asyncio
import json
from datetime import datetime
from typing import Dict

# Shared event queue for live logs
# Format: { "job_id": asyncio.Queue }
live_log_queues: Dict[str, asyncio.Queue] = {}

def push_live_log(job_id: str, agent: str, thought: str, status: str = "success"):
    """
    Helper to push logs from agents to the shared queue.
    Does not import any agents, safe for all agents to use.
    """
    if job_id in live_log_queues:
        # Using call_soon_threadsafe or create_task to ensure it works in async
        asyncio.create_task(live_log_queues[job_id].put({
            "agent": agent,
            "thought": thought,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }))