"""The mood of a doc line (mood.py): a record or a plan is a note, a statement about the code now is not.

Measured on ten repos never seen before (docs/bao-nham-2026-10.md): 12 of 16 false alarms were lines under a
`## Resolved` heading, rows of a table whose verdict was "extracted", plan items marked "(done: #6)" and the
implementation steps of RFDs. Every case below is one of those shapes, or the shape of a real finding that
must stay."""

import pytest

from mindmap_fixture import Repo, run
from mindmap.doctype import classify
from mindmap.mdscan import scan
from mindmap.model import evidence_text
from mindmap import mood


@pytest.fixture
def repo():
    r = Repo()
    yield r
    r.cleanup()


def only(res, rule):
    return [f for f in res.findings if f.rule == rule]


def gone_symbol(repo, doc_text: str, doc: str = "README.md"):
    """A repo whose code had `build_index` when the doc line was written and lost it after."""
    repo.write("src/app.py", "def build_index():\n    return 1\n")
    repo.write(doc, doc_text).commit("add")
    repo.write("src/app.py", "def rebuild_index():\n    return 1\n").commit("rename")
    return run(repo)


def gone_path(repo, doc_text: str, doc: str = "README.md"):
    """A repo whose `src/core.py` existed when the doc line was written and was deleted after."""
    repo.write("src/core.py", "x = 1\n")
    repo.write(doc, doc_text).commit("add")
    repo.remove("src/core.py").commit("drop")
    return run(repo)


def notes(f) -> list:
    return [e.get("note", "") for e in f.evidence]


# -- the headings above the line ---------------------------------------------------

def test_a_line_under_a_resolved_heading_is_a_record(repo):
    res = gone_path(repo, "# Feedback\n\n## Open\n\nNothing.\n\n## Resolved\n\n### The filter bug\n\n"
                          "`extract` in `src/core.py` filtered legitimate errors out.\n")
    [f] = only(res, "path-moved")
    assert f.severity == "info"
    assert "the section `Resolved` tells of the past" in notes(f)
    assert any(e.get("line") == 7 for e in f.evidence)        # the heading, so the reader can check the reading


@pytest.mark.parametrize("heading", ["Proposed follow-up issues", "Implementation details and plan",
                                     "Phase 2: Reference Implementation", "Next steps", "Roadmap"])
def test_a_line_under_a_plan_heading_is_a_plan(repo, heading):
    res = gone_symbol(repo, f"# Library\n\n## {heading}\n\n3. Extract `build_index` into the library.\n")
    [f] = only(res, "symbol-gone")
    assert f.severity == "info" and f"the section `{heading}` is a plan" in notes(f)


def test_the_nearest_heading_decides(repo):
    """`## History` far above does not reach a line under its own `### Current layout` heading."""
    res = gone_path(repo, "# App\n\n## History\n\nIt began small.\n\n### Current layout\n\nSee `src/core.py`.\n")
    [f] = only(res, "path-moved")
    assert f.severity == "error"


# -- the item the line is part of ----------------------------------------------------

def test_a_table_row_with_a_verdict_cell_is_a_record(repo):
    res = gone_symbol(repo, "# Modules\n\n| Module | Verdict |\n|---|---|\n"
                            "| `build_index`, `canon` | extracted (#7) as the library's `index` |\n")
    [f] = only(res, "symbol-gone")
    assert f.severity == "info" and "the item is marked `extracted`" in notes(f)


def test_a_table_row_without_a_verdict_keeps_its_warning(repo):
    res = gone_symbol(repo, "# Modules\n\n| Module | Does |\n|---|---|\n| `build_index` | builds the index |\n")
    [f] = only(res, "symbol-gone")
    assert f.severity == "warning"


@pytest.mark.parametrize("mark", ["(done: #6)", "(done)", "(fixed in 1.2)", "(merged)"])
def test_a_list_item_marked_done_is_a_record(repo, mark):
    res = gone_symbol(repo, f"# Work\n\n## Items\n\n1. Keep the parser.\n2. Extract `build_index`,\n   taking the fixes above {mark}.\n")
    [f] = only(res, "symbol-gone")
    assert f.severity == "info" and f"the item is marked `{mark}`" in notes(f)


# -- the sentence --------------------------------------------------------------------

def test_a_dated_sentence_in_the_past_is_a_record(repo):
    res = gone_path(repo, "# Notes\n\n## Filter\n\nOn 2026-04-19 `extract` in `src/core.py` used a bare `contains`, which broke.\n")
    [f] = only(res, "path-moved")
    assert f.severity == "info" and notes(f)[-1].startswith("the sentence tells of the past: `2026-04-19`")


def test_one_past_verb_alone_is_not_enough(repo):
    """`was added in 2.0` opens many a line that still describes the code."""
    res = gone_symbol(repo, "# API\n\n## Index\n\n`build_index` was added in 2.0 and builds the index.\n")
    [f] = only(res, "symbol-gone")
    assert f.severity == "warning"


def test_a_present_sentence_in_a_live_doc_keeps_its_error(repo):
    res = gone_path(repo, "# CLAUDE.md\n\n## Architecture\n\n- **core** (`src/core.py`) - the entry point.\n", "CLAUDE.md")
    [f] = only(res, "path-moved")
    assert f.severity == "error" and not any("tells" in n or "plan" in n for n in notes(f))


def test_links_are_not_read_for_mood(repo):
    """A reader clicks a link whatever the sentence around it says."""
    repo.write("docs/old.md", "# Old\n")
    repo.write("README.md", "# App\n\n## Resolved\n\nSee [the old design](docs/old.md).\n").commit("add")
    repo.remove("docs/old.md").commit("drop")
    [f] = only(run(repo), "link-broken")
    assert f.severity == "error"


def test_vietnamese_notes(repo):
    res = gone_path(repo, "# Góp ý\n\n## Resolved\n\n`extract` trong `src/core.py` đã lọc sai.\n", "NOTES.md")
    res = run(repo, lang="vi")
    [f] = only(res, "path-moved")
    assert "mục `Resolved` kể chuyện đã qua" in notes(f)
    assert evidence_text("the item is marked `extracted`", "vi") == "mục này được đánh dấu `extracted`"


# -- the genre of the document -----------------------------------------------------------

RFD = """---
title: "Session List"
---

- Author(s): [@someone](https://example.com/someone)
- Champion: [@other](https://example.com/other)

## Elevator pitch

Add a `session/list` endpoint.

## Implementation details and plan

3. Implement in the Rust SDK (`src/core.py`).
"""


def test_an_rfd_is_a_plan(repo):
    res = gone_path(repo, RFD, "docs/rfds/session-list.md")
    assert res.doc_stats["docs/rfds/session-list.md"]["type"] == "plan"
    assert {f.severity for f in res.findings} <= {"info"}


def test_an_investigation_with_a_recommendation_is_a_plan():
    lines = ["# Shared library: recommendation", "", "Investigation for breki/rustbase#2. Question: can it be a library?",
             "", "**Recommendation: yes, proceed.**"]
    assert classify("docs/xtask-library.md", {}, "", lines=lines) == "plan"
    assert classify("docs/guide.md", {}, "", lines=["# Guide", "", "Run `make`."]) == "live"


def test_a_design_doc_without_the_template_stays_live():
    lines = ["# Go SDK Design", "", "This document discusses the design of a Go SDK and should be considered canonical."]
    assert classify("design/design.md", {}, "", lines=lines) == "live"


def test_a_doc_filled_in_elsewhere_is_a_template(repo):
    prompt = ("# Policy Evaluation Prompt\n\nYou are evaluating an SDK repository.\n\n## Input\n\n"
              "- **SDK path**: {local-path}\n- **Repository**: {repo}\n\n"
              "The CLI checks these files: `src/core.py`, `.github/renovate.json`.\n")
    res = gone_path(repo, prompt, ".claude/skills/audit/references/prompt.md")
    assert res.doc_stats[".claude/skills/audit/references/prompt.md"]["type"] == "template"
    assert {f.severity for f in res.findings} <= {"info"}
    assert mood.genre(["# Setup", "", "Run `{{ cookiecutter.name }}` then `{{ cookiecutter.cmd }}`."]) == "template"
    assert mood.genre(["# Setup", "", "```json", '{"a": 1}', "{b}", "```", "A JSON object `{}`."]) == ""


# -- the commit that took the thing away also edited the doc ---------------------------

def test_a_removal_that_also_edited_the_doc_is_a_note(repo):
    repo.write("src/app.py", "def build_index():\n    return 1\n")
    repo.write("docs/notes.md", "# Notes\n\n## Index\n\n`build_index` builds it.\n\nMore.\n").commit("add")
    repo.write("src/app.py", "def rebuild_index():\n    return 1\n")
    repo.write("docs/notes.md", "# Notes\n\n## Index\n\n`build_index` builds it.\n\nMore, edited.\n").commit("rename")
    [f] = only(run(repo), "symbol-gone")
    assert f.severity == "info" and "this commit also edited the doc and kept the line" in notes(f)


def test_a_removal_that_edited_an_agent_file_still_warns(repo):
    """In CLAUDE.md a stale line does harm, and the co-edit is proof of nothing but an open editor."""
    repo.write("src/app.py", "def build_index():\n    return 1\n")
    repo.write("CLAUDE.md", "# Agent\n\n## Index\n\n`build_index` builds it.\n\nMore.\n").commit("add")
    repo.write("src/app.py", "def rebuild_index():\n    return 1\n")
    repo.write("CLAUDE.md", "# Agent\n\n## Index\n\n`build_index` builds it.\n\nMore, edited.\n").commit("rename")
    [f] = only(run(repo), "symbol-gone")
    assert f.severity == "warning"


def test_a_removal_elsewhere_keeps_the_warning(repo):
    res = gone_symbol(repo, "# Notes\n\n## Index\n\n`build_index` builds it.\n", "docs/notes.md")
    [f] = only(res, "symbol-gone")
    assert f.severity == "warning" and not any("also edited" in n for n in notes(f))


def test_a_moved_path_whose_commit_edited_the_doc_is_a_note(repo):
    repo.write("src/core.py", "x = 1\n")
    repo.write("docs/notes.md", "# Notes\n\n## Layout\n\nSee `src/core.py`.\n\nMore.\n").commit("add")
    repo.remove("src/core.py")
    repo.write("docs/notes.md", "# Notes\n\n## Layout\n\nSee `src/core.py`.\n\nMore, edited.\n").commit("drop")
    [f] = only(run(repo), "path-moved")
    assert f.severity == "info" and "this commit also edited the doc and kept the line" in notes(f)


# -- the source of a generated doc -----------------------------------------------------------

def test_the_links_of_a_doc_source_are_read_for_the_page_it_builds(repo):
    repo.write("LICENSE", "MIT\n")
    repo.write("docs/protocol.md", "# Protocol\n\n## Stdio transport\n")
    repo.write("internal/readme/README.src.md", "# App\n\nSee [LICENSE](./LICENSE) and [stdio](protocol.md#stdio-transport) "
                                                "and [gone](nowhere.md).\n").commit()
    res = run(repo)
    assert [(f.rule, f.severity, f.claim) for f in res.findings] == [("link-broken", "info", "nowhere.md")]
    assert "written for the page it builds" in res.findings[0].suggestion


def test_an_ordinary_doc_keeps_its_broken_link(repo):
    repo.write("LICENSE", "MIT\n")
    repo.write("internal/readme/README.md", "# App\n\nSee [LICENSE](./LICENSE).\n").commit()
    [f] = only(run(repo), "link-broken")
    assert f.severity == "error"


# -- the same sentence about different pull requests ---------------------------------------------

def test_the_same_sentence_about_different_pull_requests_is_not_a_copy(repo):
    line = ("The initial preview protocol implementation of this feature landed in "
            "[PR #{0}](https://example.com/pull/{0}), with the client capability following.\n")
    repo.write("docs/rfds/a.md", "# A\n\n### Implemented\n\n" + line.format(2002)).commit("a")
    repo.write("docs/rfds/b.md", "# B\n\n### Implemented\n\n" + line.format(2004)).commit("b")
    assert only(run(repo), "copies-diverged") == []


def test_copies_with_different_figures_are_still_found(repo):
    line = "The suite runs {} tests in about {} seconds on the reference machine used by the project.\n"
    repo.write("docs/a.md", "# A\n\n" + line.format(120, 4)).commit("a")
    repo.write("docs/b.md", "# B\n\n" + line.format(150, 5)).commit("b")
    assert len(only(run(repo), "copies-diverged")) == 1


# -- commands run inside a project the reader cloned ------------------------------------------------

def test_commands_after_entering_a_clone_are_that_projects(repo):
    repo.write("package.json", '{"name": "conformance", "scripts": {"build": "tsc"}}\n')
    repo.write("CONTRIBUTING.md", "# Dev\n\n```bash\ngit clone https://github.com/org/other-sdk.git\ncd other-sdk\n"
                                  "pnpm install\npnpm run build:all\ncd ..\npnpm run build\npnpm run missing\n```\n").commit()
    res = run(repo)
    assert [(f.rule, f.claim) for f in res.findings if f.severity != "info"] == [("npm-script-missing", "pnpm run missing")]
    d = scan("CONTRIBUTING.md", repo.root.joinpath("CONTRIBUTING.md").read_text(encoding="utf-8"))
    assert [t for _, t in d.fences[0].lines] == ["git clone https://github.com/org/other-sdk.git", "cd ..",
                                                 "pnpm run build", "pnpm run missing"]


# -- causes found on a third unseen set (docs/bao-nham-2026-10.md, set C) ----------------------------

def test_a_hedged_sentence_is_a_note(repo):
    repo.write("package.json", '{"name": "site", "scripts": {"dev": "next dev"}}\n')
    repo.write("AGENTS.md", "# Agents\n\n| Command | Does |\n|---|---|\n| `npm run test` | Execute the test suite (if present). |\n"
                            "| `npm run lint` | Run the linter. |\n").commit()
    res = run(repo)
    [missing] = [f for f in res.findings if f.claim == "npm run test"]
    assert missing.severity == "info" and "the sentence hedges: `if present`" in notes(missing)
    [lint] = [f for f in res.findings if f.claim == "npm run lint"]
    assert lint.severity == "error"


def test_a_path_offered_among_alternatives_one_of_which_is_there(repo):
    repo.write("package-lock.json", "{}\n")
    repo.write("AGENTS.md", "# Agents\n\n1. Update the appropriate lockfile (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`).\n").commit("add")
    repo.remove("package-lock.json")
    repo.write("pnpm-lock.yaml", "lockfileVersion: 9\n").commit("pnpm")
    [f] = only(run(repo), "path-moved")
    assert f.severity == "info" and "the line offers `pnpm-lock.yaml` in its place, and that one is there" in notes(f)


def test_a_path_offered_with_or(repo):
    repo.write(".github/dependabot.yml", "version: 2\n")
    repo.write("docs/policy.md", "# Policy\n\nPass if `.github/dependabot.yml` or `.github/renovate.json` exists.\n").commit("add")
    repo.remove(".github/dependabot.yml")
    repo.write(".github/renovate.json", "{}\n").commit("renovate")
    [f] = only(run(repo), "path-moved")
    assert f.severity == "info"


def test_a_path_named_alone_keeps_its_error(repo):
    repo.write("package-lock.json", "{}\n")
    repo.write("README.md", "# App\n\nInstall, then commit `package-lock.json`.\n").commit("add")
    repo.remove("package-lock.json")
    repo.write("pnpm-lock.yaml", "lockfileVersion: 9\n").commit("pnpm")
    [f] = only(run(repo), "path-moved")
    assert f.severity == "error"


def test_a_title_that_carries_its_date_is_a_note_of_its_day(repo):
    repo.write("scripts/check.js", "x\n")
    repo.write("docs/best-practices.md", "# MCP Best Practices - May 26, 2025\n\nThe release script checks `scripts/check.js`.\n").commit("add")
    repo.remove("scripts/check.js").commit("drop")
    res = run(repo)
    assert res.doc_stats["docs/best-practices.md"]["type"] == "plan"
    assert {f.severity for f in res.findings} <= {"info"}
    assert classify("x.md", {}, "", lines=["# Release 2.0 for 2025 users"]) == "live"
    assert classify("x.md", {}, "", lines=["# Notes (2026-04-19)"]) == "plan"


def test_list_item_numbers_are_not_figures(repo):
    item = "**WebFetch** - Fallback when the browser tool is unavailable on the machine running the skill\n"
    repo.write("commands/fix.md", "# Fix\n\n1. **Browser** - first\n2. " + item).commit("a")
    repo.write("skills/daily/SKILL.md", "# Daily\n\n1. **Browser** - first\n2. **Other** - second\n3. " + item).commit("b")
    assert only(run(repo), "copies-diverged") == []


def test_a_link_that_leaves_the_repo_is_a_note(repo):
    repo.write("README.md", "# Base action\n\nSee the [security docs](../docs/security.md#warning).\n").commit()
    res = run(repo)
    assert [(f.rule, f.severity) for f in res.findings] == [("link-outside", "info")]
    assert "outside the repo" in res.findings[0].message
    assert [c.status for c in res.claims if c.kind == "link"] == ["external"]


def test_a_link_that_leaves_a_subfolder_but_not_the_repo_is_still_checked(repo):
    repo.write("docs/guide.md", "# Guide\n\nSee [the policy](../SECURITY.md).\n").commit()
    assert [(f.rule, f.severity) for f in run(repo).findings] == [("link-broken", "error")]


# -- causes found on a fourth unseen set (docs/bao-nham-2026-10.md, set D) ----------------------------

def test_a_tree_of_what_a_run_creates_is_not_the_repo(repo):
    repo.write("agents/README.md", "# Agents\n")
    repo.write("CLAUDE.md", "# Factory\n\n## 📁 Output Directory Structure\n\nEvery agent factory run creates:\n```\n"
                            "agents/\n└── [agent_name]/\n    ├── planning/\n    │   └── prompts.md\n    ├── agent.py\n    └── cli.py\n```\n").commit()
    assert run(repo).findings == []


def test_entries_under_a_placeholder_folder_have_no_path():
    from mindmap.claims import Extractor
    d = scan("README.md", "# Layout\n\nRepository structure:\n\n```\nsrc/\n├── <name>/\n│   └── main.py\n└── cli.py\n```\n")
    assert [c.target for c in Extractor().extract(d)] == ["src/cli.py"]


def test_a_doc_that_tracks_work_in_boxes_is_a_plan(repo):
    boxes = "".join(f"- [ ] [P{i}] step {i}\n" for i in range(5))
    res = gone_symbol(repo, "# Unified architecture\n\n## Requirements\n\nCurrent `build_index` refactored into the app layer.\n\n"
                            "## Tasks\n\n" + boxes, "specs/unified.md")
    assert res.doc_stats["specs/unified.md"]["type"] == "plan"
    assert {f.severity for f in res.findings} <= {"info"}


def test_an_open_task_box_is_a_plan_item(repo):
    res = gone_symbol(repo, "# Notes\n\n## Index\n\n- [ ] Delete `build_index` from the loader.\n")
    [f] = only(res, "symbol-gone")
    assert f.severity == "info" and "the item is an open task `[ ]`" in notes(f)


def test_a_tasks_heading_is_a_plan(repo):
    res = gone_symbol(repo, "# Spec\n\n## Tasks\n\n### 8. Cleanup\n\nDelete `build_index` from the loader.\n")
    [f] = only(res, "symbol-gone")
    assert f.severity == "info"


def test_a_pair_of_made_up_commands_in_parentheses_is_an_example(repo):
    repo.write("scripts/real.sh", "echo\n")
    repo.write("skills/writing/SKILL.md", "# Writing\n\n## Files\n\nInvoke bundled scripts through their interpreter "
                                          "(`bash scripts/tool.sh`, `node scripts/tool.js`), never by bare path.\n").commit()
    assert run(repo).findings == []


def test_one_made_up_command_alone_is_still_reported(repo):
    repo.write("scripts/real.sh", "echo\n")
    repo.write("README.md", "# App\n\nRun `bash scripts/tool.sh` to start.\n").commit()
    assert [f.rule for f in run(repo).findings] == ["command-missing"]


def test_bold_alternatives_with_or(repo):
    repo.write("CLAUDE.md", "# Agent\n")
    repo.write("docs/muse.md", "# Muse\n\nOn Muse this is **`CLAUDE.md`** or **`AGENTS.md`** in the project root.\n").commit("add")
    repo.remove("CLAUDE.md")
    repo.write("AGENTS.md", "# Agent\n").commit("rename")
    [f] = only(run(repo), "path-moved")
    assert f.severity == "info"
