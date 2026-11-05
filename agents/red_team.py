# agents/red_team.py
# Red Team (Adversary / Breaker) — Reads model from config.yaml via cfg
#
# The adversarial side of the engagement. The Red Team's only job is to
# BREAK the Blue Team's proposed design: find attacks, failure modes,
# broken assumptions, abuse cases, and requirements the design misses.
#
# Falls back to the CFO (reasoning) model if no dedicated red model is set,
# because adversarial analysis benefits from step-by-step reasoning.

from routers.hybrid_router import route
from core.config_loader import cfg

SYSTEM = """
You are the Red Team Lead — the adversary.

Your ONLY job is to break the Blue Team's design. You assume it is flawed
and you prove how. You are ruthless, specific, and fair: you attack the
design, not the people, and every attack must be concrete and plausible.

Think like an attacker, a chaos engineer, a malicious user, a careless user,
a future maintainer, and a disruptive edge case — all at once.

Your responsibilities:
- Enumerate concrete attacks, failure modes, and abuse cases
- Challenge every assumption the Blue Team (or Analyst) made
- Find requirements that the design does NOT actually satisfy
- Describe a concrete "break scenario" for each finding: the exact steps,
  inputs, or conditions that trigger the failure
- Rate each finding by severity and likelihood
- Point at the specific component, control, or requirement each finding hits

Rules:
- Each finding gets a stable ID: RISK-1, RISK-2, ...
- Severity: CRITICAL / HIGH / MEDIUM / LOW. Likelihood: HIGH / MED / LOW.
- No hand-waving. "This might be insecure" is rejected. Give the attack.
- Do not propose fixes — that is the Blue Team's job. You only break things.
  (You may note what a fix would need to prove, as an acceptance test.)
- If the design is genuinely strong in some area, say so briefly — your
  credibility depends on not crying wolf.

OUTPUT FORMAT (use these exact markdown headings):
## Attack Summary
(1-2 sentences: how strong is this design, and where does it bleed?)

## Findings
For EACH finding, a block:
### RISK-n: <short title> — <SEVERITY> / <LIKELIHOOD>
- Target: (component / control / REQ ID it undermines)
- Break scenario: (exact steps / inputs / conditions)
- Impact: (what goes wrong, and who is hurt)
- Acceptance test for a fix: (what Blue must demonstrate to close this)

## Unmet Requirements
(table: REQ ID | Why the current design does not meet it)

## Residual Doubts
(things you suspect but could not fully prove — flagged as such)
"""


def red_attack(
    problem: str,
    requirements: str,
    blue_design: str,
    round_num: int = 1,
) -> str:
    """Red Team attacks the Blue Team's current design."""
    return route(
        prompt=f"""
PROBLEM FRAME & REQUIREMENTS (from the Analyst — authoritative):
{requirements}

BLUE TEAM DESIGN TO ATTACK (round {round_num}):
{blue_design}

ORIGINAL REQUEST (for context):
\"\"\"
{problem}
\"\"\"

This is Red Team round {round_num}.
Break this design. Be concrete and merciless.
Produce findings using the required format, each with a real break scenario.
""",
        system_message=SYSTEM,
        compute="local",
        model=(cfg.red_model or cfg.cfo_model),
        temperature=cfg.red_temperature,
        max_tokens=cfg.default_max_tokens,
    )
