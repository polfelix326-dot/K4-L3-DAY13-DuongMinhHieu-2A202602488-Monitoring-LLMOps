from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import dotenv
dotenv.load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import httpx
from langfuse import Langfuse
from app.agent import LabAgent
from app.tracing import get_langfuse_client

def run_workflow():
    print("=== Step 1 & 2: Verify Prompts on Langfuse ===")
    lf = Langfuse(httpx_client=httpx.Client(timeout=30.0))
    p_baseline = lf.get_prompt("day13-chat", label="baseline")
    print(f"Prompt baseline: version {p_baseline.version}, labels: {p_baseline.labels}")
    p_candidate = lf.get_prompt("day13-chat", label="candidate")
    print(f"Prompt candidate: version {p_candidate.version}, labels: {p_candidate.labels}")

    agent = LabAgent()

    print("\n=== Step 3: Run request with label 'baseline' ===")
    os.environ["LANGFUSE_PROMPT_LABEL"] = "baseline"
    res1 = agent.run(
        user_id="student-test-01",
        feature="qa",
        session_id="session-baseline-01",
        message="Explain why metrics, traces and logs work together in monitoring",
        correlation_id="req-prompt-baseline-01",
    )
    get_langfuse_client().flush()
    time.sleep(2)
    print(f"Baseline run complete: {res1.answer[:60]}...")

    print("\n=== Step 3: Run same input with label 'candidate' ===")
    os.environ["LANGFUSE_PROMPT_LABEL"] = "candidate"
    res2 = agent.run(
        user_id="student-test-01",
        feature="qa",
        session_id="session-candidate-01",
        message="Explain why metrics, traces and logs work together in monitoring",
        correlation_id="req-prompt-candidate-01",
    )
    get_langfuse_client().flush()
    time.sleep(2)
    print(f"Candidate run complete: {res2.answer[:60]}...")

    print("\n=== Step 4 & 5: Promote 'candidate' to 'production' ===")
    lf.update_prompt(name="day13-chat", version=p_candidate.version, new_labels=["candidate", "production"])
    time.sleep(2)
    p_prod_v2 = lf.get_prompt("day13-chat", label="production")
    print(f"Promoted to production: version {p_prod_v2.version}, labels: {p_prod_v2.labels}")

    os.environ["LANGFUSE_PROMPT_LABEL"] = "production"
    res3 = agent.run(
        user_id="student-test-01",
        feature="qa",
        session_id="session-promoted-01",
        message="Explain why metrics, traces and logs work together in monitoring",
        correlation_id="req-prompt-promoted-01",
    )
    get_langfuse_client().flush()
    time.sleep(2)
    print(f"Promoted production run complete: {res3.answer[:60]}...")

    print("\n=== Step 5: Rollback 'production' to version 1 (baseline) ===")
    lf.update_prompt(name="day13-chat", version=p_baseline.version, new_labels=["baseline", "production"])
    lf.update_prompt(name="day13-chat", version=p_candidate.version, new_labels=["candidate"])
    time.sleep(2)
    p_rolled_back = lf.get_prompt("day13-chat", label="production")
    print(f"Rolled back production: version {p_rolled_back.version}, labels: {p_rolled_back.labels}")

    res4 = agent.run(
        user_id="student-test-01",
        feature="qa",
        session_id="session-rollback-01",
        message="Explain why metrics, traces and logs work together in monitoring",
        correlation_id="req-prompt-rollback-01",
    )
    get_langfuse_client().flush()
    time.sleep(2)
    print(f"Rollback run complete: {res4.answer[:60]}...")

    print("\n=== Done Prompt Workflow ===")

if __name__ == "__main__":
    run_workflow()
