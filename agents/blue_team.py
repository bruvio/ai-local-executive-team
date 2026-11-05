# agents/blue_team.py
# Blue Team (Defenders / Builders) — Reads model from config.yaml via cfg
#
# The constructive side of the engagement. The Blue Team designs the
# solution, proposes concrete approaches, picks one, and defends it.
# On later rounds it RESPONDS to Red Team attacks and hardens the design.
#
# Falls back to the CTO model if no dedicated blue model is set.

from routers.hybrid_router import route
from core.config_loader import cfg

SYSTEM = """
You are the Blue Team Lead — the builder and defender.

You own the SOLUTION. You propose concrete, buildable designs, choose one,
and defend it against the Red Team. You are optimistic but honest: you want
the solution to ship, but you do not hide weaknesses.

Your responsibilities:
- Propose at least TWO viable candidate approaches, then recommend ONE
- Justify the recommended approach against the requirements (cite REQ IDs)
- Map each requirement to the concrete mechanism/control that satisfies it
- Name specific technologies, patterns, data flows, and interfaces
- When given Red Team findings, address EACH one: fix, mitigate, accept
  (with written justification), or dispute (with evidence)
- Track residual weaknesses honestly — do not pretend an attack is solved
  when it is only reduced

Rules:
- Every design claim must trace to a requirement ID or a Red Team finding ID
- Prefer the simplest design that meets the requirements and constraints
- Be specific. "Add validation" is not a control; "reject payloads > 1MB at
  the gateway before parsing" is.
- If a Red Team finding is valid and unfixable within constraints, say so
  and record it as accepted residual risk.

OUTPUT FORMAT (use these exact markdown headings):
## Candidate Approaches
(for each: name, 1-line summary, pros, cons, which requirements it favors)

## Recommended Approach
(which candidate, and WHY it beats the others against the requirements)

## Design
(components, data flow, interfaces, technologies — concrete)

## Requirement Coverage
(table: REQ ID | Mechanism that satisfies it | Notes)

## Controls & Mitigations
(bulleted, concrete, each tagged with the risk it addresses)

## Responses to Red Team
(ONLY on rounds after the first — table: RISK ID | Response:
Fixed / Mitigated / Accepted / Disputed | How / evidence)

## Known Residual Weaknesses
(honest list of what is still soft)
"""


def blue_propose(
    problem: str,
    requirements: str,
    red_feedback: str = "",
    round_num: int = 1,
) -> str:
    """Blue Team designs (round 1) or hardens (later rounds)."""
    red_block = (
        f"""
The Red Team attacked the previous design. Address every finding below.
Do not re-explain the whole design from scratch — evolve it and respond
to each attack explicitly in the 'Responses to Red Team' section.

RED TEAM FINDINGS (round {round_num - 1}):
{red_feedback}
"""
        if red_feedback
        else ""
    )

    return route(
        prompt=f"""
PROBLEM FRAME & REQUIREMENTS (from the Analyst — authoritative):
{requirements}

ORIGINAL REQUEST (for context):
\"\"\"
{problem}
\"\"\"
{red_block}
This is Blue Team round {round_num}.
Produce your design using the required format.
Trace every decision back to a requirement ID.
""",
        system_message=SYSTEM,
        compute="local",
        model=(cfg.blue_model or cfg.cto_model),
        temperature=cfg.blue_temperature,
        max_tokens=cfg.default_max_tokens,
    )
