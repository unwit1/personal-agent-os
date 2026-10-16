# Next: finish HR assistant batch 3 (cloud session)

Branch `claude/hr-assistant-audit`. Be terse. No audits, no re-reading docs, don't poll.

1. Attach and clone `unwit1/ingester-engine` next to this repo; `pip install -e ../ingester-engine`, then `pip install -e . pytest pytest-xdist`.
2. Write `~/.agent-os/providers.json` from `python agent.py orchestrate providers --suggest` and set the
   `claude-code` entry's `profile` to `{"deployment": "subscription", "billing": {"mode": "credits"}}`
   so workers bill to cloud credit (operator-approved 2026-10-16; see `headroom.py` `source_key`).
3. If `origin/codex/project-board-wip` exists, merge it.
4. Create, downshift reviewers, then drive:
   ```
   python agent.py orchestrate start-recommended --repo . --project personal-agent-os --run-id hr-cc-run4 \
     --tasks docs/audits/2026-10-16-hr-assistant/batch3-tasks.json --goal "Finish HR assistant batch 3" \
     --validator "python -m pytest -q -p no:cacheprovider tests/test_executive_window_server.py tests/test_executive_window_builtin.py tests/test_command_center_server.py" \
     --set allow_paid_spend=true --no-drive
   python agent.py orchestrate override hr-cc-run4 --role reviewer --model sonnet --effort medium
   python agent.py orchestrate run hr-cc-run4    # run in the background; wait for one completion notice
   ```
5. Merge `agent-os/hr-cc-run4/integration` (and any PASSED node branches not yet integrated), run pytest on the
   touched test files only, fix trivial fixture breaks, commit, push. Report in 5 lines.
