# goaimoat-decision-maker-lookup-mcp

Find the person to contact at a company, then get a verified work email.

Built for agents doing B2B outreach: a model can name a company, but it cannot look up
who works there or reach a deliverable address. Results are **honestly labelled** — when
a company or person is not in the source data, you get a not-found result back instead of
a guessed address. You are never charged for a lookup that returns nothing.

- **Hosted (no install):** `https://contacts.mcp.goaimoat.com/mcp`
- **Registry name:** `com.goaimoat/decision-maker-lookup`
- **Free:** 3 calls per email. Then a $29/yr license.

## Tools

| Tool | What it does | Cost |
|---|---|---|
| `find_decision_makers(company)` | Search a company and get people with `decision_maker` / `phone_number_exists` / `linkedin_exists` flags. **Addresses stay masked.** | **Free** |
| `reveal_work_email(reveal_handle)` | Turn one selected row into a verified address | **Paid** |
| `verify_email(address)` | Check whether an address you already have is deliverable, before you send to it | Paid |
| `get_balance()` | Show remaining credit so you don't overspend | Free |

You size the job before spending anything: search first, filter to the decision-makers you
actually want, then reveal only those rows.

`find_decision_makers` finds addresses you don't have; `verify_email` checks one you already
have. They're different jobs — use the right one and you don't pay for a lookup you don't need.

## Use the hosted endpoint

```json
{
  "mcpServers": {
    "decision-maker-lookup": {
      "type": "streamable-http",
      "url": "https://contacts.mcp.goaimoat.com/mcp"
    }
  }
}
```

Then call `find_decision_makers` with your `email` — no key, no signup for the first 3 calls.

## Run it yourself

Requires a `MONID_API_KEY` (the upstream data provider). Get one at [monid.ai](https://monid.ai).

### Docker

```bash
docker build -t goaimoat-decision-maker-lookup-mcp .
docker run --rm -i -e MONID_API_KEY=your_key goaimoat-decision-maker-lookup-mcp
```

Runs on **stdio** by default — what directory scanners (Glama and similar) use for introspection.

### Local

```bash
pip install -r requirements.txt
MONID_API_KEY=your_key python server.py
```

Without `MONID_API_KEY` the server still starts and answers introspection; tool calls return a
clear "no credential configured" error rather than fabricating a result.

## Note on parameters

Upstream parameter names were verified live with
`monid inspect -p hunterio -e /multi-domain-search` — the field is **`company_name`**, not
`company`. Guessing parameter names against an undocumented endpoint is how this kind of
server silently returns HTTP 400, so this repo pins the verified ones.

## Part of GoAI Moat

A suite of MCP servers giving agents data they cannot reach themselves: verified work
emails, company records, Google search, and web scraping.

- Catalog: https://goaimoat.com/mcp-catalog.html
- All servers (monorepo): https://github.com/jayniebingyu-cyber/goaimoat-mcp

## License

MIT
