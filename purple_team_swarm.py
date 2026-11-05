# purple_team_swarm.py
# ══════════════════════════════════════════════════════
# Red Team / Blue Team / Purple Team orchestrator
#
# Runs an adversarial engagement to resolve a problem and emits a
# self-contained markdown IMPLEMENTATION PLAN that a separate agent
# can execute without seeing this conversation.
#
# Phases:
#   0. ANALYST  — understand the problem → requirements + engagement plan
#   1. BLUE     — propose & defend a concrete design
#   2. RED      — attack the design, find how it breaks
#     (repeat BLUE↔RED for `rounds` iterations; BLUE hardens each round)
#   3. PURPLE   — reconcile everything into ONE evidence-backed plan
#
# The final plan is written to plans/implementation_plan_<slug>_<ts>.md
# and includes the full Red/Blue/Analyst transcripts as appendices so the
# decision evidence (and the options considered and rejected) is auditable.
#
# Usage:
#   python purple_team_swarm.py "Design a rate limiter for our public API"
#   python purple_team_swarm.py --rounds 2 "Harden our file upload pipeline"
#   python purple_team_swarm.py --out myplan.md "..."
# ══════════════════════════════════════════════════════

import re
import sys
import argparse
from datetime import datetime
from pathlib import Path

from agents.analyst     import analyst_assess
from agents.blue_team   import blue_propose
from agents.red_team    import red_attack
from agents.purple_team import purple_synthesize
from core.config_loader import cfg
from rich.console import Console
from rich.panel import Panel

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

console = Console()

ROOT_DIR     = Path(__file__).parent
DEFAULT_PLAN_DIR = ROOT_DIR / "plans"


def _slug(text: str, max_len: int = 48) -> str:
    """Filesystem-safe slug from the problem statement."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return (text[:max_len].rstrip("-")) or "engagement"


def _plan_models() -> dict:
    """Resolve which model each role will actually use (after fallbacks)."""
    return {
        "analyst": cfg.analyst_model or cfg.cpo_model,
        "blue":    cfg.blue_model    or cfg.cto_model,
        "red":     cfg.red_model     or cfg.cfo_model,
        "purple":  cfg.purple_model  or cfg.ceo_model,
    }


def run_purple_team_workflow(
    problem: str,
    rounds: int = 1,
    write_file: bool = True,
    output_path: str | None = None,
) -> dict:
    """
    Run the full Red/Blue/Purple engagement.

    Args:
        problem:     the raw request to resolve.
        rounds:      number of Blue→Red attack/defend cycles (>=1).
        write_file:  write the final plan to disk.
        output_path: explicit path for the plan (else auto under plans/).

    Returns a dict with every phase output plus:
        - "plan":      the purple team's final implementation plan (markdown)
        - "document":  the full saved document (plan + evidence appendices)
        - "plan_path": where it was written (or None)
    """
    rounds = max(1, int(rounds))
    models = _plan_models()

    console.print(Panel(
        f"[bold white]{problem}[/bold white]",
        title=(
            f"[bold magenta]RED / BLUE / PURPLE ENGAGEMENT — "
            f"{cfg.preset_name.upper()} · {rounds} round(s)[/bold magenta]"
        ),
        border_style="magenta",
    ))

    results: dict = {
        "problem": problem,
        "rounds": rounds,
        "models": models,
        "blue_rounds": [],
        "red_rounds": [],
    }

    # ── Phase 0 — Analyst understands the problem ──────────────────────
    console.print(
        f"\n[bold yellow]Phase 0 — Problem Analyst[/bold yellow] "
        f"[dim]({models['analyst']})[/dim]"
    )
    requirements = analyst_assess(problem)
    results["requirements"] = requirements
    console.print(Panel(
        requirements,
        title="[bold]ANALYST — Problem Frame & Requirements[/bold]",
        border_style="yellow",
    ))

    # ── Phases 1..N — Blue proposes, Red attacks, repeat ───────────────
    red_feedback = ""
    for r in range(1, rounds + 1):
        console.print(
            f"\n[bold blue]Phase 1.{r} — Blue Team "
            f"({'design' if r == 1 else 'harden'})[/bold blue] "
            f"[dim]({models['blue']})[/dim]"
        )
        blue = blue_propose(
            problem,
            requirements,
            red_feedback=red_feedback,
            round_num=r,
        )
        results["blue_rounds"].append(blue)
        console.print(Panel(
            blue,
            title=f"[bold]BLUE TEAM — Round {r}[/bold]",
            border_style="blue",
        ))

        console.print(
            f"\n[bold red]Phase 2.{r} — Red Team (attack)[/bold red] "
            f"[dim]({models['red']})[/dim]"
        )
        red = red_attack(problem, requirements, blue, round_num=r)
        results["red_rounds"].append(red)
        red_feedback = red
        console.print(Panel(
            red,
            title=f"[bold]RED TEAM — Round {r}[/bold]",
            border_style="red",
        ))

    # ── Final Phase — Purple reconciles everything ─────────────────────
    console.print(
        f"\n[bold magenta]Phase 3 — Purple Team "
        f"(synthesis)[/bold magenta] [dim]({models['purple']})[/dim]"
    )
    plan = purple_synthesize(
        problem,
        requirements,
        results["blue_rounds"],
        results["red_rounds"],
    )
    results["plan"] = plan
    console.print(Panel(
        plan,
        title="[bold bright_magenta]PURPLE TEAM — IMPLEMENTATION PLAN[/bold bright_magenta]",
        border_style="bright_magenta",
    ))

    # ── Assemble the full, auditable document ──────────────────────────
    document = _assemble_document(results)
    results["document"] = document

    if write_file:
        path = _write_plan(document, problem, output_path)
        results["plan_path"] = str(path)
        console.print(
            f"\n[bold green]✅ Implementation plan written to:[/bold green] "
            f"[bold]{path}[/bold]"
        )
        console.print(
            "[dim]   Hand this file to an implementing agent — it is "
            "self-contained.[/dim]"
        )
    else:
        results["plan_path"] = None

    return results


def _assemble_document(results: dict) -> str:
    """Final plan first, then full evidence appendices (red/blue/analyst)."""
    models = results["models"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = (
        f"<!--\n"
        f"Generated by the Red/Blue/Purple Team swarm.\n"
        f"Date: {now}\n"
        f"Preset: {cfg.preset_name}\n"
        f"Rounds: {results['rounds']}\n"
        f"Models: analyst={models['analyst']} | blue={models['blue']} | "
        f"red={models['red']} | purple={models['purple']}\n"
        f"-->\n\n"
    )

    appendix = ["\n\n---\n\n# Appendix — Engagement Evidence\n"]
    appendix.append(
        "_This appendix is the audit trail behind the plan above: the "
        "problem frame, every Blue Team design, and every Red Team attack. "
        "It exists so the chosen approach, the rejected options, and the "
        "accepted residual risks can all be traced to their source._\n"
    )

    appendix.append("\n## Appendix A — Analyst: Problem Frame & Requirements\n")
    appendix.append(results["requirements"])

    appendix.append("\n\n## Appendix B — Blue Team Design Rounds\n")
    for i, blue in enumerate(results["blue_rounds"], start=1):
        appendix.append(f"\n### Blue Team — Round {i}\n")
        appendix.append(blue)

    appendix.append("\n\n## Appendix C — Red Team Attack Rounds\n")
    for i, red in enumerate(results["red_rounds"], start=1):
        appendix.append(f"\n### Red Team — Round {i}\n")
        appendix.append(red)

    return header + results["plan"] + "\n".join(appendix) + "\n"


def _write_plan(
    document: str,
    problem: str,
    output_path: str | None,
) -> Path:
    if output_path:
        path = Path(output_path)
        if not path.is_absolute():
            path = ROOT_DIR / path
    else:
        DEFAULT_PLAN_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = DEFAULT_PLAN_DIR / f"implementation_plan_{_slug(problem)}_{ts}.md"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")
    return path


# ── CLI ────────────────────────────────────────────────
def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Red/Blue/Purple team swarm — turn a problem into an "
            "evidence-backed markdown implementation plan."
        )
    )
    parser.add_argument(
        "problem",
        nargs="*",
        help="The problem to resolve (quote it, or pass as trailing words).",
    )
    parser.add_argument(
        "--rounds", "-r",
        type=int,
        default=1,
        help="Number of Blue→Red attack/defend cycles (default 1).",
    )
    parser.add_argument(
        "--out", "-o",
        default=None,
        help="Output path for the plan (default: plans/implementation_plan_*.md).",
    )
    parser.add_argument(
        "--no-file",
        action="store_true",
        help="Print the plan but do not write a file.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    cfg.summary()
    args = _parse_args(sys.argv[1:])

    if args.problem:
        user_problem = " ".join(args.problem)
    else:
        user_problem = input(
            "\nWhat problem should the Red/Blue/Purple teams resolve?\n> "
        )

    run_purple_team_workflow(
        user_problem,
        rounds=args.rounds,
        write_file=not args.no_file,
        output_path=args.out,
    )
