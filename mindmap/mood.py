"""The mood of a doc line: does it describe the code as it is, or tell of the past or of a plan?

Every check compares a doc line with the code as it is now. A line is only wrong when it meant to describe
the code as it is. Docs also keep records (an entry under `## Resolved`, a table row whose verdict is
"extracted", a plan item marked "(done: #6)") and plans (the implementation steps of an RFD), and there a
name that is gone from the code is the point of the line, not a mistake in it. On ten repos never seen
before, 12 of the 16 false alarms were lines of that kind (docs/bao-nham-2026-10.md).

Version 1.0 read a few of those cases with separate rules spread over the checker (a DONE cell, a past
sentence, a plan file name). Here the context of a line is read once, in layers, from the outside in:

1. the genre of the document (an RFD or proposal, told by its template: `Author(s):`, `Champion:`,
   `## Status quo`; an investigation: `Investigation for …`, `**Recommendation:**`; a task list of `- [ ]`
   boxes; a prompt filled in elsewhere: `{repo}`), see `genre()`;
2. the headings above the line (`## Resolved`, `## Implemented`, `## Proposed follow-up issues`,
   `### Phase 2: Reference Implementation`);
3. the item the line belongs to (a table row with a verdict cell, a list item marked done, a strike-through);
4. the sentence itself (a date, a verb in the past: "used", "landed", "surfaced from"; or a hedge that says
   the thing may not be there: "the test suite (if present)").

A heading or an item verdict settles it alone. The sentence needs two signs (a date and a past verb, or two
past verbs): "`Foo` was added in 2.0" also opens many a line that still describes the code. The answer is
a `Mood` with the piece of text that gave it away; the finding keeps it as evidence, so the reader sees why
a line became a note and can disagree with the reading.

Links are not read this way: a reader clicks a link whatever the sentence around it says.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PAST_HEADING = re.compile(
    r"\b(?:resolved|implemented|done|completed|finished|shipped|landed|merged|fixed|closed|released|"
    r"history|historical|changelog|change ?log|release ?notes|what changed|changes (?:in|since|from)|"
    r"previous(?:ly)?|prior art|retrospective|retro|lessons(?: learned)?|post-?mortems?|feedback|"
    r"archived?|legacy|deprecated|deprecations?|removed|removals?|"
    r"migrat(?:e|ing|ion) from|upgrading from|breaking changes|known issues|what we tried|attempts|timeline)\b"
    r"|(?<!\w)(?:đã xong|đã làm|đã xử lý|đã giải quyết|hoàn tất|hoàn thành|lịch sử|bài học|đã bỏ|đã gỡ|cũ)(?!\w)",
    re.I)
PLAN_HEADING = re.compile(
    r"\b(?:plans?|planned|planning|proposals?|proposed|roadmap|future(?: work)?|next steps?|follow-?ups?|"
    r"phase \d|milestones?|to-?do|tasks?|task list|user stor(?:y|ies)|acceptance criteria|implementation steps|"
    r"open questions?|ideas?|unresolved|alternatives?(?: considered)?|rejected|"
    r"out of scope|non-goals|wishlist|backlog|upcoming|not yet|someday|draft|rfcs?|rfds?)\b"
    r"|(?<!\w)(?:kế hoạch|đề xuất|dự kiến|sắp tới|bước tiếp theo|việc còn lại|chưa làm|ý tưởng)(?!\w)", re.I)
# a heading that says its section describes the present; it stops the climb to the headings above it
PRESENT_HEADING = re.compile(r"\b(?:current(?:ly)?|now|today|present|as of|how it works|usage|install\w*|"
                             r"quick ?start|getting started)\b|(?<!\w)(?:hiện tại|bây giờ|cách dùng)(?!\w)", re.I)
# a verdict in a cell of a table row, or a status word a list item starts with
VERDICT = (r"(?:done|xong|đã xong|hoàn tất|hoàn thành|closed|merged|shipped|landed|extracted|implemented|fixed|"
           r"resolved|released|removed|dropped|superseded|retired|replaced|deleted|obsolete|cancell?ed|"
           r"won'?t ?fix|rejected|declined|moved|migrated|ported|upstreamed|folded|abandoned|complete[d]?)")
DONE_CELL = re.compile(r"^\s*(?:\**\s*)?(?:" + VERDICT + r"\b|[✅☑✔])", re.I)
DONE_LINE = re.compile(r"^\s*[-*+]\s+\[[xX]\]|✅|\bDONE\b|\bXONG\b")
# "(done: #6)", "(fixed in 1.2)", "(merged)": a mark the author put on a finished item
DONE_MARK = re.compile(r"\((?:done|fixed|merged|shipped|resolved|closed|landed|implemented|released|xong|đã xong|"
                       r"đã làm|hoàn tất)(?:\s*[:,][^)]{0,40}|\s+(?:in|by|as|#)[^)]{0,40})?\)", re.I)
# the sentence says the thing may not be there: "Execute the test suite (if present)"
HEDGE = re.compile(r"\b(?:if (?:present|any|available|exists?|defined|configured|there is one|it exists|you have one)|"
                   r"when (?:present|available)|where (?:present|available)|optional(?:ly)?)\b"
                   r"|(?<!\w)(?:nếu có|nếu tồn tại|không bắt buộc)(?!\w)", re.I)
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# a verb that tells of an event or a behaviour of the past; not "was added", which often introduces a thing
# that is still there
PAST_VERB = re.compile(
    r"\b(?:surfaced|landed|shipped|merged|introduced|extracted|migrated|ported|took|became|caused|broke|"
    r"failed|fixed|resolved|reverted|rewrote|folded|used|had|were|was)\b"
    r"|(?<!\w)(?:đã từng|hồi đó|lúc đó|trước đây|đã dùng|đã sửa|đã gộp|đã chuyển)(?!\w)", re.I)
GENRE_LINE = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*|__)?\s*(?:authors?\(s\)|authors?|champions?|reviewers?|"
    r"sponsors?|drivers?|owners?|approvers?)\s*(?:\*\*|__)?\s*:", re.I)
TEMPLATE_SECTION = re.compile(
    r"^\s{0,3}#{1,6}\s+(?:elevator pitch|status quo|what we propose|proposed (?:change|solution|design)|"
    r"context and problem statement|decision outcome)\b", re.I)
GENRE_TITLE = re.compile(r"^\s{0,3}#{1,6}\s+.*\b(?:rfd|rfc|adr|proposal|investigation|recommendation)\b", re.I)
TASK_BOX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[[ xX]\]\s")
OPEN_BOX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[ \]\s")
PLACEHOLDER = re.compile(r"\{[a-z][a-z0-9_-]*\}|\{\{\s*[A-Za-z_][\w.-]*\s*\}\}")     # {repo}, {{ name }}
GENRE_TEXT = re.compile(r"^\s*(?:(?:\*\*|__)?\s*recommendation\s*(?:\*\*|__)?\s*:|investigation (?:for|into|of)\b)", re.I)


@dataclass
class Mood:
    kind: str       # past | plan | maybe
    reason: str     # the evidence note, in English (model.evidence_text translates the fixed forms)
    line: int       # where the sign is (a heading, or the line itself)


def heading_chain(doc, line: int) -> list:
    """The headings above `line`, nearest first, each one level up from the one before."""
    out = []
    level = 99
    for h in reversed(doc.headings):
        if h.line <= line and h.level < level:
            out.append(h)
            level = h.level
    return out


def genre(lines: list) -> str:
    """'plan' for a document written on the template of a proposal (an RFD, an RFC, an ADR, an investigation
    with a recommendation): the names in it are what the author meant to build, read at the time of writing.
    Told by its first lines: a `Champion:` or `Author(s):` field, a `## Status quo` or `## Elevator pitch`
    section, a title that says RFD, or an opening `Investigation for …` / `**Recommendation:**`.

    'template' for a document filled in elsewhere (`**Repository**: {repo}`, `{local-path}`): a prompt or a
    form about whatever it is run on, so the files it names are that thing's, not this repo's."""
    head = lines[:40]
    start = 0
    if head and head[0].lstrip("﻿").strip() == "---":
        start = next((i for i, t in enumerate(head[1:], 1) if t.strip() in ("---", "...")), 0) + 1
    body = head[start:start + 30]
    fields = sum(1 for t in body if GENRE_LINE.match(t))
    opening = any(GENRE_TEXT.match(t) for t in body)
    holes: set = set()
    fence = False
    for t in body:
        if re.match(r"^\s{0,3}(?:```|~~~)", t):
            fence = not fence
        elif not fence:
            holes.update(PLACEHOLDER.findall(t))
    if len(holes) >= 2:
        return "template"
    if sum(1 for t in lines if TASK_BOX.match(t)) >= 5:
        return "plan"           # a doc that tracks work in `- [ ]` boxes: a spec or a task list
    if fields >= 2:
        return "plan"           # `Author(s):` and `Champion:`: the fields of an RFD
    if any(TEMPLATE_SECTION.match(t) for t in lines[:120]):
        return "plan"           # `## Status quo`, `## Elevator pitch`: the sections of an RFD
    if (fields or opening) and any(GENRE_TITLE.match(t) for t in body):
        return "plan"           # `# RFC 12: …` with an `Author:` line; `# Shared library: recommendation` opening
    return ""                   # with `Investigation for …`


def item(text: str, sentence: str = "") -> str:
    """The mark on a finished item: a verdict cell, a ticked box, "(done: #6)", or '' when there is none."""
    if not text:
        return ""
    if text.lstrip().startswith("|"):
        from .mdscan import split_cells
        for cell in split_cells(text)[1:]:
            m = DONE_CELL.match(cell)
            if m:
                return m.group(0).strip("* ")
    m = DONE_LINE.search(text)
    if m:
        return m.group(0).strip()
    m = DONE_MARK.search(sentence or text)
    return m.group(0) if m else ""


def assess(doc, line: int, sentence: str, text: str = "") -> Mood | None:
    """The mood of the line, or None when it reads as a statement about the code as it is."""
    for h in heading_chain(doc, line):
        if PRESENT_HEADING.search(h.text):
            break               # `### Current layout` under `## History`: the nearer heading speaks for the line
        if PAST_HEADING.search(h.text):
            return Mood("past", f"the section `{h.text}` tells of the past", h.line)
        if PLAN_HEADING.search(h.text):
            return Mood("plan", f"the section `{h.text}` is a plan", h.line)
    text = text or doc.line_text(line)
    if OPEN_BOX.match(text):
        return Mood("plan", "the item is an open task `[ ]`", line)
    mark = item(text, sentence)
    if mark:
        return Mood("past", f"the item is marked `{mark}`", line)
    m = HEDGE.search(sentence)
    if m:
        return Mood("maybe", f"the sentence hedges: `{m.group(0)}`", line)
    signs = []
    m = ISO_DATE.search(sentence)
    if m:
        signs.append(m.group(0))
    verbs = [v.group(0) for v in PAST_VERB.finditer(sentence)]
    signs += list(dict.fromkeys(verbs))[:2]
    if len(signs) >= 2 and (m or len(verbs) >= 2):
        return Mood("past", "the sentence tells of the past: " + ", ".join(f"`{s}`" for s in signs[:2]), line)
    return None
