# Repository instructions

## Commit attribution

For commits made on behalf of the repository owner, use the repository-local Git author identity associated with `ynhy513`. Verify it with `git var GIT_AUTHOR_IDENT` before committing.

For changes made with OpenAI Codex, add the `Assisted-by: OpenAI Codex` trailer to the commit message. Contributors committing on their own behalf use their own author identities.

## Documentation languages

Keep every reference Markdown page paired with an `.en.md` translation and reciprocal language links. English README, usage pages, stories and Skill links must stay within English documentation except explicit `简体中文` switches. Preserve command names, JSON keys and operational constraints across translations. Before publishing documentation changes, run `python scripts/check_docs.py` and `python -m unittest discover -s scripts -p 'test_check_docs.py'` from the repository root.
