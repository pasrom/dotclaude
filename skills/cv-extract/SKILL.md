---
name: cv-extract
description: Extract a CV / Lebenslauf / résumé PDF into a validated JSON Resume v1.0.0 document, plus the portrait photo. Trigger when the user wants to parse a CV, ingest a Lebenslauf, or extract structured data from a résumé PDF. Output is schema-neutral (JSON Resume) — downstream skills/services then adapt it to their own format.
---

# CV Extract Skill

Reads a CV PDF and produces:

1. `<out-dir>/<KRZ>.json` — a [JSON Resume v1.0.0](https://jsonresume.org/schema) document
2. `<out-dir>/<KRZ>.jpg` — the portrait extracted from the PDF (if present)

Default `<out-dir>` is `imports/` in the current working directory. Defaults are overridable per invocation.

This skill is **schema-neutral on purpose**. Downstream consumers (e.g. cv-generator's `cv-import` adapter, an ATS, an HR API) map JSON Resume into their own format. Keep all rendering, taxonomy-matching and project-specific transforms *out* of here.

## Inputs you need from the user

- **PDF path** (required)
- **Kürzel / handle** — 3-letter uppercase identifier used as filename. Derive from initials of first + last name (e.g. Thomas Zangerle → `TZA` or `ZAN`); ask if ambiguous.

## Steps

### 1. Extract the portrait

```bash
python3 <skill-dir>/extract_photo.py <pdf_path> <KRZ> --out-dir <out-dir>
```

The helper picks the largest portrait-shaped embedded image (heuristics: ≥ 150 × 150, aspect ratio 0.8–2.0, page-1/2 boost). If it returns non-zero (no embedded image, e.g. scanned PDF), set `basics.image` to `""` in the JSON and tell the user no photo was extracted.

If extracted, set `basics.image` to a path the downstream consumer can resolve — usually `<out-dir>/<KRZ>.jpg` relative or absolute. JSON Resume expects a URL but tolerates any string.

### 2. Read the PDF

Use the `Read` tool on the PDF path. You'll receive multimodal content (text + page images). Read **every page** — CVs scatter sections across pages and split education over multiple headings.

### 3. Map to JSON Resume v1.0.0

Use the schema in `<skill-dir>/jsonresume.schema.json` (or [the canonical spec](https://jsonresume.org/schema)) as the ground truth. Top-level sections used:

| JSON Resume section | What goes here                                                                                            |
|--------------------|-----------------------------------------------------------------------------------------------------------|
| `basics`           | Name, label (current job title), image, email, phone, url, summary, location, profiles                    |
| `work[]`           | Each employment / consulting / leadership role with dates, highlights, summary                            |
| `volunteer[]`      | Unpaid roles, board mandates, mentoring, student-society work                                             |
| `education[]`      | Formal education: universities, FH, HTL, vocational schools, apprenticeships                              |
| `awards[]`         | Scholarships, prizes, honors                                                                              |
| `certificates[]`   | Vocational certifications with formal expiry / issuer (TÜV, ISTQB, AWS, etc.)                             |
| `publications[]`   | Papers, articles, books, conference talks                                                                 |
| `skills[]`         | Grouped skills — see "Skill grouping" below                                                               |
| `languages[]`      | Spoken languages with `fluency` string                                                                    |
| `interests[]`      | Hobbies — **omit** unless the user explicitly asks to keep them                                           |
| `projects[]`       | Standalone projects (open source, side projects, thesis, hackathons) distinct from a paid `work` entry    |

#### Date format

ISO 8601: `YYYY-MM-DD`, or partial `YYYY-MM` if the day is unknown. **Don't invent the day** — partial dates are valid.

For ongoing roles, **omit `endDate`** entirely (the schema's date pattern rejects empty strings — set the field only when you have a real date). Don't use sentinels like `"present"` or `"Bis dato"` — those belong to specific renderer formats, not the canonical data.

```
"Seit September 2023"           → startDate: "2023-09"   (no endDate)
"Juni 2019 – Juli 2023"         → startDate: "2019-06", endDate: "2023-07"
"März 2017" (single-day course) → startDate: "2017-03", endDate: "2017-03"
"Expected June 2014"            → startDate: "2014-06"   (no endDate — still studying)
unknown month                   → startDate: "2019"      (year-only is ok)
```

#### Skill grouping

JSON Resume's `skills[]` is flat: each entry has `name`, `level`, `keywords[]`. Use it as a **grouping container**:

```json
{ "name": "Projekt- & Produktmanagement",
  "keywords": ["Projektmanagement", "Roadmap", "Kalkulation", "Angebotsausarbeitung"] }
```

So `name` = group label, `keywords[]` = individual skills. Pick 3–5 thematic groups, not one per skill. **Omit `level` entirely** when grouping (groups don't have a level — and `null` fails schema validation). Per-skill levels live in extension `x_skill_levels` if needed (see below).

#### Skill / language level mapping

JSON Resume uses **strings**, not integers. Map explicit CV phrasing to these canonical levels:

| CV phrasing                                    | `skills[].level` / `languages[].fluency` |
|------------------------------------------------|------------------------------------------|
| "Muttersprache" / "native"                     | `Native speaker`                          |
| "verhandlungssicher" / "fluent" / "C1/C2"      | `Fluent`                                  |
| "sehr gut" / "advanced"                        | `Advanced`                                |
| "good" / "gut" / "B1/B2"                       | `Intermediate`                            |
| "Grundkenntnisse" / "Basic" / "A1/A2"          | `Basic`                                   |
| "Anfänger" / "beginner"                        | `Beginner`                                |

When the level is uncertain, use the lower bucket — the human reviewer can bump it up. Always cite your reasoning in `x_evidence` (see below).

#### Extension fields (vendor-prefix `x_`)

JSON Resume tolerates additional fields; the validator in this skill explicitly allows keys prefixed with `x_`. Use these to surface metadata downstream consumers may want, without breaking the standard:

- `x_evidence` — a verbatim CV quote that justifies a level / skill / claim. Belongs on `skills[]`, `languages[]`, or `work[].highlights[]` items as a sibling field. Lets a reviewer see *why* the model picked a specific level.
- `x_industry` — industry tag on `work[]` entries (e.g. "Battery / BMS", "AV Industry"). JSON Resume doesn't model this natively.
- `x_location` — granular city/region on `work[]` (JSON Resume has only `name` for the company; location often lives in `basics.location` for the candidate, not per role).
- `x_technologies` — comma-separated tool / tech tags per `work[]` entry.
- `x_thesis` — thesis / dissertation title on `education[]` entries.
- `x_skill_levels` — optional per-keyword level map on a `skills[]` group: `{ "C++": "Advanced", "Java": "Intermediate" }`.

Downstream adapters can use these or ignore them — neither breaks anything.

### 4. What to skip (don't extract)

Strict rule: **don't invent**. The model must only emit fields backed by the CV. Beyond that, drop:

- **Schulbildung** (Volksschule / Hauptschule / Grundschule / primary school) — never relevant for a professional CV
- **Wehrdienst / military service** — unless the role is military-relevant
- **Hobbys / interests** — JSON Resume has `interests[]`; populate only on explicit user request
- **References** — JSON Resume has `references[]`; same rule

For everything else: if it's in the CV verbatim, extract it; if it's an interpretation (skill level from prose, profile summary from scattered bullets), include an `x_evidence` field citing the source phrase.

### 5. Write the JSON

Use the `Write` tool. Default path: `<out-dir>/<KRZ>.json`. Pretty-print with 2-space indent so it's human-diffable.

### 6. Validate

```bash
python3 <skill-dir>/validate.py <out-dir>/<KRZ>.json
```

Exit code 0 = valid JSON Resume v1.0.0 (extensions tolerated). Exit code 1 = errors with paths; fix them in the JSON and re-validate before reporting success.

### 7. Tell the user what to do next

Report:

- Path to the JSON file
- Path to the photo (or "no photo extracted — set `basics.image` manually if needed")
- Validation result
- Mention which downstream skill / consumer is appropriate (e.g. cv-import in the cv-generator project to render an e.bs-formatted PDF; an API endpoint for a backend ingest).

## Anti-goals

- **Don't render a final document here.** No PDF, no HTML, no YAML for any specific consumer format. That's the adapter's job.
- **Don't do taxonomy matching** (e.g. "is 'React.js' in our skill catalog?"). That requires consumer-specific context.
- **Don't write to a project-specific path** (`profiles/imports/` etc.). Default `imports/` in cwd is intentionally neutral.
- **Don't commit any output.** YAMLs, JSONs and photos with real candidate data are personal data — the consumer's `.gitignore` is responsible for that, but cv-extract itself never stages or commits.
