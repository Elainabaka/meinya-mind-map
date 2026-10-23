# Báo nhầm, tháng 10/2026: đo, tìm gốc, cắt

Mục tiêu đặt ra: lượt chạy đầu trên repo lạ, số phát hiện nhầm không quá 1 trên 10, mà không mất phát hiện đúng.
Số cũ (bản 1.0, ba bộ repo lạ): loại phỏng đoán đúng 38, nhầm 112; loại sự thật đúng 64, nhầm 12.

Cách đo trong tài liệu này: clone repo công khai dưới 300 file có `AGENTS.md` hoặc `CLAUDE.md`, chạy
`mindmap check <repo> --all` (cả phỏng đoán lẫn sự thật), đọc từng phát hiện mức lỗi/cảnh báo trong ngữ cảnh và
gán một trong ba nhãn: **đúng** (dòng tài liệu sai so với code), **nhầm** (dòng tài liệu đúng, tool hiểu sai ý),
**tranh cãi** (dòng sai về chữ nhưng tác giả hẳn biết: tài liệu thiết kế cũ, CLAUDE.md chép từ template).
Mỗi bộ repo chỉ được xem kết quả *sau khi* code đã sửa xong theo bộ trước, nên số "lượt đầu" là số mù.

## 1. Bộ A: 10 repo, số đo ban đầu

| Repo | Ngôn ngữ | File | Phát hiện | Đúng | Tranh cãi | Nhầm |
|---|---|---|---|---|---|---|
| modelcontextprotocol/go-sdk | Go | 227 | 6 | 0 | 4 | 2 |
| steipete/camsnap | Go | 93 | 0 | | | |
| breki/rustbase | Rust | 159 | 9 | 0 | 0 | 9 |
| jdx/clx | Rust | 54 | 2 | 2 | | |
| zed-industries/agent-client-protocol | Rust + TS | 274 | 6 | 1 | 0 | 5 |
| anthropics/claude-agent-sdk-typescript | TS | 37 | 0 | | | |
| anthropics/claude-code-action | TS | 225 | 0 | | | |
| nadimtuhin/claude-token-optimizer | JS | 98 | 0 | | | |
| anthropics/claude-agent-sdk-python | Python | 160 | 1 | 0 | 1 | 0 |
| huggingface/smolagents | Python | 185 | 3 | 3 | | |
| **Cộng** | | | **27** | **6** | **5** | **16** |

16 nhầm trên 27, tức 59%. Tách theo loại: phỏng đoán (`symbol-gone`, `copies-diverged`) 15 phát hiện, 0 đúng;
sự thật (`path-moved`, `link-broken`, `command-missing`) 12 phát hiện, 5 nhầm. Chế độ mặc định (không `--all`)
cũng nhầm 5 trên 12: tách "sự thật / phỏng đoán" không đủ.

Từng phát hiện nhầm và lý do:

| Repo | Dòng | Luật | Vì sao dòng tài liệu vẫn đúng |
|---|---|---|---|
| rustbase | docs/developer/template-feedback.md:748 | path-moved | mục nằm dưới `## Resolved`, có ngày 2026-04-19: biên bản một lỗi đã sửa, câu ở thì quá khứ ("used") |
| rustbase | docs/xtask-library.md:213, 214 (×3) | symbol-gone | hàng bảng với ô kết luận "extracted (#7) as the library's …": hàng nói tên đã dời vào thư viện |
| rustbase | docs/xtask-library.md:559, 561, 562 (×4) | symbol-gone | mục kế hoạch đánh số dưới `## Proposed follow-up issues`, ghi "(done: #6)" |
| go-sdk | internal/docs/troubleshooting.src.md:23 | link-broken | `.src.md` là nguồn mà `weave` dệt thành `docs/troubleshooting.md`, nơi `protocol.md` nằm cạnh |
| go-sdk | internal/readme/README.src.md:94 | link-broken | như trên: dệt thành `README.md` ở gốc, cạnh `LICENSE` |
| agent-client-protocol | docs/rfds/session-list.mdx:191 (×2) | path-moved | một RFD (Author/Champion/Status quo); "Phase 2: Reference Implementation" là kế hoạch của đề xuất |
| agent-client-protocol | docs/rfds/session-usage.mdx:148 | symbol-gone | bước kế hoạch "gate behind `unstable_session_usage`"; sau đó feature được ổn định, kế hoạch là biên bản |
| agent-client-protocol | docs/rfds/session-compaction.mdx:215, session-notices.mdx:157 | copies-diverged | "landed in [PR #2002]" và "[PR #2004]": cùng câu mẫu nói về hai PR khác nhau |

Tranh cãi: 4 dòng của `design/design.md` (go-sdk, tài liệu thiết kế 2025, tên đã rời API; commit bỏ tên cũng sửa
chính tài liệu này mà giữ dòng) và `e2e-tests/README.md:42` (sdk-python, lệnh pytest với tên file test bịa làm ví dụ).

**Gốc rễ:** 12 trong 16 dòng nhầm không hề *khẳng định* rằng tên đó đang có trong code. Chúng kể chuyện đã qua
(mục Resolved, hàng "extracted", "(done: #6)") hoặc nêu kế hoạch (RFD). Tool 1.0 so chuỗi tên với code mà không
hỏi dòng đó *đang nói ở thì nào*. 2 dòng là file nguồn sinh tài liệu, 2 dòng là câu mẫu khác số PR.

## 2. Ba hướng đã cân

**Hướng 1: hiểu cấu trúc code thay vì so chuỗi.** Parse định nghĩa theo ngôn ngữ, phân biệt API công khai với
biến cục bộ, theo dõi đổi tên qua diff. Lợi: bớt nhầm loại "biến cục bộ bị coi là định nghĩa". Hại: chỉ thư viện
chuẩn thì mỗi ngôn ngữ vẫn là regex; và trên bộ A nó sửa được **0/16**: các tên quả thật đã biến khỏi code, sai
không nằm ở phía code mà ở cách đọc dòng tài liệu. Bỏ làm hướng chính.

**Hướng 2: lịch sử git làm bằng chứng mạnh hơn.** Hỏi git: commit bỏ tên đó có *đồng thời sửa chính tài liệu này*
không? Nếu có, tác giả đã mở tài liệu lúc bỏ tên mà vẫn giữ dòng: thường là biên bản, không phải sót. Đo trên bộ A:
12/13 `symbol-gone` có dấu hiệu này (9 nhầm, 3 tranh cãi), **0 phát hiện đúng nào có**. Rẻ (một `git diff-tree`
mỗi phát hiện). Hại: mơ hồ (tác giả có thể sửa chỗ khác và sót dòng này); không giúp gì cho sự thật không có
commit xóa (link trong `.src.md`, câu mẫu, đường dẫn chưa từng có); trên bộ D không cứu được dòng nào trong 37.
Giữ làm kênh phụ, tắt với file hướng dẫn agent (ở đó một dòng cũ gây hại thật và bằng chứng này quá mỏng).

**Hướng 3: mô hình hóa ý định của dòng tài liệu (chọn).** Đọc ngữ cảnh của dòng một lần, theo lớp từ ngoài vào:
thể loại tài liệu (RFD theo mẫu `Author(s):`/`Champion:`/`## Status quo`; điều tra có `**Recommendation:**`;
danh sách việc toàn ô `- [ ]`; prompt điền chỗ trống `{repo}`) → chuỗi tiêu đề phía trên (`## Resolved`,
`## Implemented`, `## Tasks`, `### Phase 2`) → mục chứa dòng (hàng bảng có ô kết luận, mục đánh dấu xong, ô
`[ ]` còn mở) → chính câu (ngày tháng + động từ quá khứ; câu có điều kiện "(if present)"). Kết quả là một *mood*
kèm đoạn chữ làm bằng chứng, in ra dưới phát hiện ("the section `Resolved` tells of the past") để người đọc
kiểm được cách đọc của máy. Trên bộ A riêng lớp này cắt **16/16** (12 bằng mood, 2 bằng luật file nguồn, 2 bằng
luật số PR), không mất phát hiện đúng nào. Khác với vá luật: các luật rời của 1.0 (`DONE` cell, câu quá khứ, tên
file kế hoạch) gom về một chỗ (`mindmap/mood.py`), có thứ bậc, và mỗi lần hạ mức đều nói lý do.

## 3. Cài đặt

- `mindmap/mood.py` (mới): `genre()`, `heading_chain()`, `item()`, `assess()`. Thư viện chuẩn, regex.
- `checks.py`: `Checker.add` hỏi mood trước mọi hạ mức khác và gắn bằng chứng; `_coedited` (hướng 2);
  file nguồn `*.src.md`, `*.tmpl.md` đọc link theo trang nó sinh; `copies-diverged` bỏ qua số PR/issue, địa chỉ
  link và số thứ tự mục; `_alternative` (dòng nêu lựa chọn thay thế và cái đó có); `_example_pair` (cặp tên bịa
  trong ngoặc); link rời khỏi repo thành ghi chú `link-outside`.
- `doctype.py`: thể loại `template` (prompt điền chỗ trống), RFD và danh sách việc là `plan`, tiêu đề mang ngày
  (`# MCP Best Practices - May 26, 2025`) là ghi chép của ngày đó.
- `gitinfo.py`: `Git.touched(rev, path)`.
- `mdscan.py`: cây thư mục mà câu dẫn nói "creates:" hoặc tiêu đề nói "Output" là minh họa; lệnh sau khi
  `cd` vào repo vừa `git clone` là của dự án kia.
- `claims.py`: mục dưới một thư mục giữ chỗ (`[agent_name]/`) không có đường dẫn để kiểm.
- `tests/test_mindmap_mood.py` (mới): 47 test, mỗi hành vi một test, kèm test giữ nguyên phát hiện đúng.

## 4. Số trước và sau

Mỗi bộ được xem lần đầu với code đã sửa xong theo các bộ trước, nên cột "lượt đầu (mù)" là số thật của một lần
chạy trên repo lạ; cột "sau" là sau khi sửa nguyên nhân chung tìm thấy ở chính bộ đó.

| Bộ | Repo | Trước (bản 1.0) | Lượt đầu (mù) với code mới | Sau khi sửa theo bộ này |
|---|---|---|---|---|
| A (10 repo trên) | 10 | 27: đúng 6, tranh cãi 5, **nhầm 16** | | 8: đúng 6, tranh cãi 2, **nhầm 0** |
| B: modelcontextprotocol/registry (Go), jdx/xx (Rust), Sahir619/fable-method (Py), modelcontextprotocol/conformance (TS), modelcontextprotocol/example-remote-server (TS) | 5 | 7: đúng 4, **nhầm 3** | 7: **nhầm 3** (43%) | 4: đúng 4, **nhầm 0** |
| C: jdx/ensembler (Rust), agentsmd/agents.md (TS), steipete/Terminator (Swift/TS), actionbook/rust-skills (Rust, docs), anthropics/claude-code-base-action (TS), steipete/claude-code-mcp (TS), modelcontextprotocol/ruby-sdk (Ruby) | 7 | 11: đúng 3, **nhầm 8** | 11: **nhầm 8** (73%) | 3: đúng 3, **nhầm 0** |
| D: mark3labs/mcphost (Go), astral-sh/setup-uv (TS), badlogic/lemmy (TS), coleam00/context-engineering-intro (Py), obra/superpowers (JS, docs) | 5 | 52: đúng 4, tranh cãi 10, **nhầm 38** | 51: **nhầm 37** (73%) | 14: đúng 4, tranh cãi 10, **nhầm 0** |
| **Cả bốn bộ, code cuối** | 27 | 97: nhầm 65 | | **29: đúng 17, tranh cãi 12, nhầm 0** |

Không phát hiện đúng nào bị mất ở bộ nào. Toàn bộ 450 test xanh (403 cũ + 47 mới).

Nguyên nhân từng bộ mù, đều chung chứ không riêng repo nào:

- **B:** một prompt đánh giá repo *khác* (`.claude/skills/…/references/policy-evaluation-prompt.md`, có `{repo}`,
  `{local-path}`) nêu `.github/dependabot.yml` mà repo này từng có rồi bỏ (2); `pnpm run build:all` chạy *sau khi*
  `git clone` và `cd` vào typescript-sdk, tức script của dự án kia (1).
- **C:** số thứ tự của danh sách đánh số bị đọc là con số của câu ("2. **WebFetch** - …" với "3. **WebFetch** - …",
  3); `npm run test` với chú thích "(if present)" (1); lockfile nêu trong ngoặc cùng hai lựa chọn khác, một cái
  có (1); link `../docs/security.md` rời khỏi repo (base-action là gói tách từ monorepo, 2); tài liệu có tiêu đề
  mang ngày "May 26, 2025" (1).
- **D:** một cây "Every agent factory run creates:" dưới `## Output Directory Structure`, con của `[agent_name]/`
  (13); một spec `specs/*.md` toàn ô `- [ ]` dưới `## Tasks`, các tên đã bị xóa đúng như spec bảo (21); "**`CLAUDE.md`**
  or **`AGENTS.md`**" (1); "(`bash scripts/tool.sh`, `node scripts/tool.js`)" làm ví dụ trong hướng dẫn viết skill (2).

Nhìn chung: mỗi bộ mù, 1 đến 2 tài liệu sinh ra gần hết số nhầm (D: 34/37). Một repo lạ với một tài liệu lạ kiểu
mới vẫn có thể cho một chùm báo nhầm; nhưng mỗi chùm là một *kiểu đọc* chung, sửa một lần cho mọi repo.

## 5. Còn lại

- Mục tiêu "lượt đầu nhầm ≤ 1/10" **chưa được chứng minh mù**: mỗi bộ mù vẫn vượt ngưỡng vì một kiểu tài liệu
  chưa gặp. Bộ E, chưa xem, là phép thử thật của code này.
- Lớp "tranh cãi" (12 dòng): tài liệu thiết kế cũ nhưng không theo mẫu nào (`design/design.md`), CLAUDE.md của
  use-case chép từ template rồi đổi bố cục `src/`. Có thể cần một tín hiệu "tài liệu lâu không sửa trong khi code
  đổi nhiều" để hạ mức, nhưng đó cũng là lúc dòng cũ gây hại.
- Chưa đo lại trên các bộ cũ của chủ repo (12 repo lớn, các bộ B–E của README) vì không có trong máy này; nên
  chạy để chắc không mất phát hiện đúng ở đó.
- Số trong README ("Measured, not promised") chưa cập nhật theo tài liệu này; chờ chủ repo quyết sau khi xem diff.
