"""Layer 3 task workers, hosted in the single ``aicoe-workers-lambda``.

Module agents call workers via ``invoke_worker`` (lambda:Invoke). Routing is the
same explicit static-dispatch registry as the module agents (see ``router.py`` and
``vault/decisions/worker-pattern.md``) — no Strands.

The maturity-assessment workers (WORKER-01/02/03) are fully deterministic: a fixed
question bank, a rule-based scorer, and a filter-based recommender. This satisfies
the "deterministic scoring" guardrail and keeps them unit-testable without AWS or
an LLM. Conversational phrasing is the module agent's concern, not the worker's.
"""
