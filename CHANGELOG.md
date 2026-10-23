# Changelog

## Unreleased

**Reads the mood of a line before judging it.** A doc line is only wrong when it meant to describe the code as it
is. Lines under `## Resolved` or `## Implemented`, table rows with a verdict ("extracted (#7)"), plan items marked
"(done: #6)", open task boxes `- [ ]`, the steps of an RFD, a sentence with a date and a past verb, a hedge like
"(if present)": these are records and plans, and a name gone from the code is their point. Such findings are now
notes, each with the piece of text that gave it away (`mindmap/mood.py`; numbers in `docs/bao-nham-2026-10.md`:
on four sets of repos never seen before, 65 false alarms out of 97 findings became 0, with no real finding lost).

Also:

- A commit that took a name away and edited the doc in the same change: the author kept the line, a note.
  Not in an agent's instruction file.
- Docs written on a template: an RFD (`Author(s):`, `Champion:`, `## Status quo`), an investigation with a
  `**Recommendation:**`, a task list of `- [ ]` boxes are plans; a prompt filled in elsewhere (`{repo}`,
  `{local-path}`) is a `template`, about whatever it is run on; a title that carries its date is a note of its day.
- The source of a generated doc (`README.src.md`, `guide.tmpl.md`) has its links read for the page it builds.
- `copies-diverged` no longer counts PR and issue numbers, link addresses or the numbers of list items.
- A path offered among alternatives one of which is there ("`CLAUDE.md` or `AGENTS.md`"), and a pair of made-up
  names in parentheses ("(`bash scripts/tool.sh`, `node scripts/tool.js`)"), are not findings.
- A tree the doc says a run creates (`## Output Directory Structure`, "creates:"), and entries under a placeholder
  folder (`[agent_name]/`), are not the repo's files. Commands after `cd` into a repo the reader just cloned belong
  to that repo.
- `link-outside`, a note: a link that leaves the repo (`../docs/x.md` from the root README) works only where the
  repo sits inside a bigger tree.
- `check`, `claims`, `cost`, `context` and `impact` now stop with exit code 2 and a message on stderr when the path
  or `--root` does not exist or the doc lies outside the root. Before, `check` on a missing folder printed
  "0 docs" and exited 0 (a CI job passed on a typo), and `claims` on a missing file scanned the whole parent folder
  (`/` for `/gone.md`) or crashed with a traceback.
- README: the tests that need `pywebview` are four files, not two; Linux status and test commands updated.

## 1.0.0 (2026-10-09)

**Facts by default, guesses on request.** On the command line, in the GitHub Action and in pre-commit, findings
that rest on a reading of the text (`symbol-gone`, `symbol-removed-now`, `path-missing`, `path-typo`,
`make-target-missing`, `subcommand-missing`, `decision-unknown`, `copies-diverged`, `version-mismatch`,
`dep-mismatch`) are now notes. `--all` (or `args: --all` in the Action) reports them as before. The summary line
says how many were turned into notes. MCP, the Claude Code hook and the desktop app still get every finding, with
the note asking the agent to read each one in context.

New since 0.1.0:

- `path-missing`: a path that is not in the tree and never was (agents make these up), checked without git too.
  A guess, so on the command line it needs `--all`.
- The hook also reads Codex `apply_patch` edits. A Mind Map tab in the desktop app (English and Vietnamese).
- Install with `uv tool install`; setup notes for Codex, Cursor and VS Code.

Fewer false alarms on repos built with coding agents, found on four sets of repos never seen before (numbers in
the README, including the first runs that missed the bar):

- Release notes waiting for a release (`.changeset/`, `.changes/`, `changelog.d/`, `newsfragments/`) are history.
- Dated records (`**Date**: 2026-07-11` under the title), numbered feature specs (`specs/001-login/`, spec-kit) and
  a status given in a table row (`| Status | Proposed |`) are read as records and plans.
- A folder of work items that git drops whenever no work is in progress (`openspec/changes/<id>/`) is not "gone".
- A file tree drawn from the folder that holds the clone (`mytool/` on top) is read from the repo root.
- Build folders a `.gitignore` names, folder-only ignore patterns, file names the code writes as strings, a
  library's package path in an import, `bun run` patterns.
- Names built by format strings (`f"time_{n}_{field}"`), names from a package that moved to its own repo and is
  now a dependency, version requirements (`v1.2.0+`, `3.11 or later`).
- Commands of another project: a skill that has the reader `git clone` another repo and `cd` into it.
- One finding per line when a table names a thing in two cells.

Fixes:

- A long string in the code (base64, a minified bundle) could make a run on a big repo run out of memory: strings
  over 400 characters are no longer read as paths.
- `git check-ignore` is no longer asked about a folder with a trailing slash: with a `.gitignore` saved with CRLF,
  the `\r` of a blank line matched every such path and hid real findings.
- A broken link now suggests the path as the link must be written from the doc (`../LICENSE.md`).

## 0.1.0 (2026-10-09)

First public release: `mindmap check` with git history as proof, MCP server, Claude Code hook, `impact`, `cost`,
`context`, GitHub Action, pre-commit hook, SARIF, HTML report, English and Vietnamese messages.
