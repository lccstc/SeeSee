# Real Exception Corpus

## Purpose

This note captures a live slice of the quote exception pool to support a new pre-P3 phase focused on candidate-generation accuracy from real customer samples. It is intentionally scoped to planning: Phase 1 already split candidates from facts, Phase 2 already created validator custody, and Phase 3 is still the guarded publisher phase. The gap exposed by the live pool is upstream of publisher safety: the candidate layer is still missing enough real-sample coverage.

## Dataset Source

- Source API: `GET http://100.66.25.75:8765/api/quotes/exceptions?limit=500&offset=0&resolution_status=open`
- Fetch date: `2026-04-14`
- Sample size: `226` open exceptions
- Coverage: `25` chats
- Concentration: top `8` chats contribute `159 / 226` exceptions (`70%`)

## Reason Counts

| Reason | Count | Share |
|---|---:|---:|
| `missing_group_template` | 149 | 66% |
| `strict_match_failed` | 77 | 34% |

The live pool is not dominated by validator or publisher failures. It is dominated by candidate-generation coverage gaps: either no usable group template exists, or an existing strict template cannot survive real message variation.

## Content-Shape Buckets

Counts below are heuristic and overlapping. They are useful for planning a pre-P3 candidate phase, not as final production taxonomy.

| Bucket | Count | What it means |
|---|---:|---|
| `multi_section_board` | 196 | One message often contains several sections, products, or region blocks, not one flat quote list |
| `long_board_message` | 192 | Most exceptions are full boards or long update posts, not tiny single-line samples |
| `quote_plus_rule_text` | 171 | Quote lines are mixed with operating rules, warnings, and handling notes |
| `manual_or_ask_lines` | 145 | Messages contain `问价` / `先问` / conditional acceptance language that should not become publishable rows |
| `update_or_shift_message` | 93 | `单独更新` / `价格更新` / `晚班开工` style messages imply delta-style context and shift handoff boards |
| `context_dependent_numeric_rows` | 35 | Rows like `50=5.25` or `100/150=5.41` depend on a preceding header or block context |
| `short_header_like_source_line` | 123 | The stored exception line is often just a header marker; planning must inspect `raw_text`, not only `source_line` |
| `token_only_source_line` | 2 | A few exceptions are pure noise / token strings and should be classified out early |

## Representative Samples

1. `#244` `strict_match_failed` `LD-QS-1616-C-528【Leng】Itunes`
   `【苹果极速快刷1-15min】 ... US 横白 ... AUD 图/密 ... 【XBOX】 ... 【chime转账】 ...`
   One long board mixes US fast, foreign cards, Xbox, Chime, and rule tails. This needs block segmentation before row extraction.

2. `#242` `strict_match_failed` `C-556-【飞鸿FHS028】-IT❤`
   `50=5.25 / 100/150=5.41 / 200-450=5.45 ... #VIP广告更新 / #US凑卡网单 ...`
   Price rows are context-dependent and surrounded by rules. The current strict matcher cannot carry header context into naked numeric rows.

3. `#241` `strict_match_failed` `C-518 【胖达】 超市卡`
   `代码快加 ... CAD ... DE ... AUD ... =======US网单====== ... 横白卡图 ...`
   One post contains multiple region/product modes separated by banners. Candidate generation must split sections and preserve per-section scope.

4. `#222` `strict_match_failed` `C-518 【胖达】 超市卡`
   `Sephora / Macy / ND / Footlocker ... 问价-请勿直发 / 默认卡图,代码提前问`
   Real quote rows and explicit manual-review instructions are mixed together. Candidate generation needs a line classifier, not just regex matching.

5. `#169` `strict_match_failed` `C-512 【米乐022】 IT`
   `[福]晚班更新 ... US ... 50=5.3 / 100/150=5.4 ... CAD 200-500=3.91 / 德国 ...`
   Shift-update style board: one header establishes context, then rows switch between naked numbers and named regions. This is candidate-side context propagation work.

6. `#243` `missing_group_template` `C-535-【SK】--S035--星黛露`
   `Steam价格更新卡图卡密同价 / 美金USD----5.00 / 欧盟EUR----5.80 ...`
   Clean, structured, high-value board with no group template. This is not a validator problem; it is template/bootstrap backlog.

7. `#238` `missing_group_template` `C-541【影子】 steam`
   `【影子steam价格表】 ... USD / EUR / GBP / CAD / AUD ... === 雷蛇/Razer === ...`
   One message spans Steam and Razer. The missing-template path must support multi-product section recognition, not assume one brand per board.

8. `#236` `missing_group_template` `C-547 【洋羊】 超市卡`
   `#洋羊晚班Price updates： ... 【Sephora】 ... 【Macy9Pic】 ...`
   English labels, decorative separators, and brand-scoped rows appear together. Template bootstrap needs to tolerate mixed punctuation and bilingual headers.

9. `#235` `missing_group_template` `C-596 万瑞收AM02夕希`
   `【===XBOX===】 / US 10-250=5.1 / EUR【5.25】卡图 ... 3张连卡或以上先问`
   Quote rows and manual restrictions are interleaved. Candidate generation should separate quote facts from conditions before validation.

10. `#239` `missing_group_template` `C-523【QH-IT-设备组-禁赎回`
    `单独更新 / #快速网单5-20分钟 / 300/400/500=5.42 / 200/250/350/450=5.4 / 100/150=5.37`
    Delta-style update with naked numeric rows. The parser needs header-scoped inference, but publish semantics must still stay conservative.

11. `#198` `missing_group_template` `C-502CH-143-夕希&臻韵IT收卡群`
    `=【#iTunes 快刷】== ... =====【#iTunes 外卡】==== ... ======#Xbox====== ... ======#雷蛇======`
    Strong evidence that real boards are multi-section documents, not one-template-one-list strings.

12. `#230` `missing_group_template` `C-547 【洋羊】 超市卡`
    `【Nordstrom Pic】100-500 4.3 / 【Nordstrom Code】100-400 4.1`
    Minimal two-line board with brand + mode encoded in the header text. Good candidate for a small deterministic template, not a generic model guess.

13. `#174` `missing_group_template` `C-531-万诺-192-夕希对接群`
    `+100 xb 5.13`
    Shorthand quote syntax exists in the pool. Candidate generation needs an explicit shorthand lane or should hold/reject deterministically.

14. `#177` `missing_group_template` `B08-C-513【青松】IT-XiXi-AQSS`
    `X2RGQCYDM6D278KN`
    Pure token/noise line. This should be classified out before template or validator work.

## What The Buckets Mean By System Layer

| Bucket | Candidate generation | Validator | Publisher |
|---|---|---|---|
| `missing_group_template` | Needs template bootstrap or deterministic fallback section parser | Should only evaluate rows that candidate layer can justify | Must remain no-op if no `publishable_rows` |
| `strict_match_failed` | Needs better section splitting, scope carry-forward, and tolerant line normalization | Can reject/hold malformed candidate rows, but should not invent missing scope | No publish on failed candidate/validation path |
| `quote_plus_rule_text` | Needs quote-vs-rule line classification before row extraction | Can reject rule lines if they leak through | Publisher should never see these as facts |
| `multi_section_board` | Needs block segmentation and per-block product/region context | Can verify per-row completeness after segmentation | Publisher scope unchanged |
| `manual_or_ask_lines` | Needs explicit `inquiry/manual/conditional` classification | Should hold or reject if a row is conditional or non-final | Never publish inquiry-style content |
| `context_dependent_numeric_rows` | Needs header-scoped candidate inference with evidence retention | Must enforce that required fields are actually present after inference | No special publisher logic; still gated by validation |
| `token/noise` | Needs early noise suppression | Simple deterministic reject | Publisher unaffected |

## Planning Implications For A New Pre-P3 Phase

Recommended phase theme: `real-sample candidate-generation hardening` before guarded publisher work.

Targets:

1. Build a live exception corpus and replay acceptance set from the current open pool, starting with the top high-volume chats rather than random long-tail cleanup.
2. Add candidate-side section splitting and line classification: `quote`, `rule`, `inquiry`, `header`, `noise`.
3. Add context propagation for header-scoped numeric rows like `50=5.25` and shorthand rows like `+100 xb 5.13`, but keep evidence explicit so validator can still reject if scope is weak.
4. Add template bootstrap / deterministic fallback coverage for the highest-volume `missing_group_template` groups before expanding validator or publisher logic.
5. Measure success in candidate terms: fewer open exceptions, more replay-stable candidate bundles, and fewer cases where a full real board collapses into one unmatched line.

Non-goals for this pre-P3 phase:

- no publisher ownership changes
- no loosening of validator gates
- no direct publish from templates, agents, or prompts
- no automatic `full_snapshot` inference as a shortcut for bad candidate extraction

## Bottom Line

The live pool says the next bottleneck is not “how to publish safely.” Phase 3 still matters, but the open exceptions are mostly telling us the candidate layer cannot yet digest real multi-section vendor boards, mixed rule text, and context-dependent updates. A pre-P3 phase is justified if it stays narrow: improve candidate generation from real exception evidence without weakening validator or publisher custody.
