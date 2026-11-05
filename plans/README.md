# Plans

Output directory for the **Red Team / Blue Team / Purple Team** swarm
(`purple_team_swarm.py`).

Each run writes a self-contained markdown file:

```
plans/implementation_plan_<slug>_<timestamp>.md
```

The file is designed to be handed to a **separate implementing agent**. It
contains:

1. The **implementation plan** produced by the Purple Team — problem
   statement, traced requirements, the final decision, **options considered
   and rejected (with evidence)**, architecture, a reconciled risk register,
   ordered implementation steps, and a verification plan.
2. An **evidence appendix** — the Analyst's problem frame and requirements,
   every Blue Team design round, and every Red Team attack round — so every
   decision and rejected option can be traced to its source.

Generated plan files are git-ignored (only this README is tracked). Commit a
plan explicitly if you want to keep it under version control.
