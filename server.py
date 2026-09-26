"""GoAI Moat — Decision-Maker Lookup MCP

Find the person to contact at a company, then get a verified work email.

Why an agent pays for this: a model can name a company but cannot look up who works
there or reach a deliverable address. The search here is free; only the reveal is paid,
and you reveal just the rows you picked — so you size the job before spending anything.

Hosted endpoint (no install): https://contacts.mcp.goaimoat.com/mcp
  Free 3 calls per email, then a $29/yr license.

Run locally:
  MONID_API_KEY=... python server.py            # stdio (default)
  MCP_TRANSPORT=streamable-http MCP_PORT=8003 python server.py

Parameter names below were verified against the live upstream with
`monid inspect -p hunterio -e /multi-domain-search` (note: `company_name`, not `company`).
"""

import json
import os
import subprocess

from fastmcp import FastMCP

MONID_BIN = os.environ.get("MONID_BIN", "monid")
MONID_API_KEY = os.environ.get("MONID_API_KEY", "")
_KEY_INITIALIZED = {"done": False}

mcp = FastMCP(
    name="GoAI Moat — Decision-Maker Lookup",
    instructions=(
        "Find B2B decision-makers and verify their work emails. "
        "Step 1: find_decision_makers(company) — a FREE search returning a population with "
        "existence flags (decision_maker / phone_number_exists / linkedin_exists), so you can "
        "size the job before spending. "
        "Step 2: reveal_work_email(reveal_handle) — a PAID reveal that turns one selected row "
        "into a verified email. get_balance() checks remaining credit. "
        "The list is free; the reveal is the paid step."
    ),
)


def _run(*args, timeout=120):
    try:
        p = subprocess.run([MONID_BIN, *args], capture_output=True, text=True, timeout=timeout)
        return {
            "ok": p.returncode == 0,
            "stdout": (p.stdout or "").strip(),
            "stderr": (p.stderr or "").strip(),
            "exit_code": p.returncode,
        }
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": f"{MONID_BIN} not installed", "exit_code": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": f"{type(e).__name__}: {e}", "exit_code": -1}


def _ensure_key():
    """Register the upstream key once. 'already exists' is a normal response."""
    if not MONID_API_KEY:
        return "not set"
    if _KEY_INITIALIZED["done"]:
        return ""
    r = _run("keys", "add", "-k", MONID_API_KEY, "-l", "main")
    _KEY_INITIALIZED["done"] = True
    err = r["stderr"] or ""
    if r["ok"] or "already exists" in err:
        return ""
    return err


def _no_key_response():
    return {
        "ok": False,
        "error": "No upstream credential configured. Set MONID_API_KEY, or use the hosted "
                 "endpoint https://contacts.mcp.goaimoat.com/mcp (free 3 calls per email).",
    }


def _to_json(text):
    try:
        return json.loads(text)
    except Exception:
        return text


@mcp.tool()
def find_decision_makers(company: str, department: str = "sales", location: str = "",
                         limit: int = 20, email: str = "", license_key: str = "") -> dict:
    """Free search: find people at a company, with decision-maker / phone / LinkedIn flags.

    Returns existence flags only — addresses stay masked. This call does not spend credit.

    Args:
        company: Company name or domain (e.g. "anker" or "example.com").
        department: Department filter (sales/marketing/engineering...), default sales.
        location: Optional region (e.g. "US", "Shenzhen").
        limit: Max rows to return (default 20).
        email: Optional. Identifies the caller for the free quota on the hosted endpoint.
        license_key: Optional. Paid license key for unlimited calls.
    """
    key_err = _ensure_key()
    if key_err:
        return _no_key_response() if key_err == "not set" else {
            "ok": False, "error": f"credential init failed: {key_err}"}

    query = {"department": department}
    if location:
        query["location"] = location
    query["company_name"] = company
    query["limit"] = limit

    r = _run("run", "-p", "hunterio", "-e", "/multi-domain-search",
             "--query", json.dumps(query, ensure_ascii=False))
    if not r["ok"]:
        return {"ok": False, "error": r["stderr"] or f"exit_code={r['exit_code']}",
                "raw": r["stdout"][:1000]}
    return {
        "ok": True,
        "company": company,
        "result": _to_json(r["stdout"]),
        "next_step": "Pick the rows you want, then call reveal_work_email() with their "
                     "reveal_handle to get a verified address (paid).",
    }


@mcp.tool()
def reveal_work_email(reveal_handle: str = "", name: str = "", company: str = "",
                      email: str = "", license_key: str = "") -> dict:
    """Paid reveal: turn one selected row into a verified work email.

    Args:
        reveal_handle: The handle from find_decision_makers results (preferred).
        name: Person's name — alternative path, use together with company.
        company: Company name or domain — use together with name.
        email: Optional. Identifies the caller for the free quota on the hosted endpoint.
        license_key: Optional. Paid license key for unlimited calls.
    """
    key_err = _ensure_key()
    if key_err:
        return _no_key_response() if key_err == "not set" else {
            "ok": False, "error": f"credential init failed: {key_err}"}

    if reveal_handle:
        r = _run("run", "-p", "hunterio", "-e", "/multi-domain-search/reveal",
                 "--query", json.dumps({"reveal_handle": reveal_handle}, ensure_ascii=False))
    elif name and company:
        r = _run("run", "-p", "contactout", "-e", "/v1/people/search/work-email",
                 "--query", json.dumps({"name": name, "company": company}, ensure_ascii=False))
    else:
        return {"ok": False, "error": "Provide reveal_handle, or both name and company."}

    if not r["ok"]:
        return {"ok": False, "error": r["stderr"] or f"exit_code={r['exit_code']}",
                "raw": r["stdout"][:1000]}
    return {"ok": True, "result": _to_json(r["stdout"])}


@mcp.tool()
def verify_email(address: str, email: str = "", license_key: str = "") -> dict:
    """Check whether one email address is actually deliverable, before you send to it.

    Use this when you already have an address and want to know if it will bounce.
    Distinct from reveal_work_email, which finds an address you don't have yet.

    Args:
        address: The email address to check (e.g. "jane@example.com").
        email: Optional. Identifies the caller for the free quota on the hosted endpoint.
        license_key: Optional. Paid license key for unlimited calls.
    """
    key_err = _ensure_key()
    if key_err:
        return _no_key_response() if key_err == "not set" else {
            "ok": False, "error": f"credential init failed: {key_err}"}

    # 参数名以 `monid inspect -p hunterio -e /email-verifier` 实测为准（query param: email）
    r = _run("run", "-p", "hunterio", "-e", "/email-verifier",
             "--query", json.dumps({"email": address}, ensure_ascii=False))
    if not r["ok"]:
        return {"ok": False, "error": r["stderr"] or f"exit_code={r['exit_code']}",
                "raw": r["stdout"][:1000]}
    return {"ok": True, "address": address, "result": _to_json(r["stdout"])}


@mcp.tool()
def get_balance(email: str = "", license_key: str = "") -> dict:
    """Check remaining upstream credit so you do not overspend.

    Args:
        email: Optional. Identifies the caller on the hosted endpoint.
        license_key: Optional. Paid license key.
    """
    key_err = _ensure_key()
    if key_err:
        return _no_key_response() if key_err == "not set" else {
            "ok": False, "error": f"credential init failed: {key_err}"}
    r = _run("balance")
    return {"ok": r["ok"], "result": _to_json(r["stdout"]) if r["ok"] else r["stderr"]}


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(transport="streamable-http",
                host=os.getenv("MCP_HOST", "127.0.0.1"),
                port=int(os.getenv("MCP_PORT", "8003")))
    else:
        mcp.run()
