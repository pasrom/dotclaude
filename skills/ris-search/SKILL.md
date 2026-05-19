---
name: ris-search
description: Use when searching Austrian legal sources - OGH/VwGH/VfGH decisions by Geschäftszahl, federal laws (Bundesrecht konsolidiert), state laws (Landesrecht), or keyword searches in judicature. Covers RIS (Rechtsinformationssystem des Bundes) at ris.bka.gv.at.
---

# Skill: ris-search

## What This Does

Searches Austrian legal resources via the official RIS (Rechtsinformationssystem des Bundes) at `ris.bka.gv.at` using `WebFetch`. Covers court decisions, consolidated federal/state laws, and the Bundesgesetzblatt.

## When to Use

- User cites a Geschäftszahl (e.g. "5 Ob 105/24p", "4 Ob 12/23s")
- User references a paragraph (e.g. "§ 16 WEG", "§ 879 ABGB")
- User wants case law on a topic ("OGH zu Klimaanlage WEG")
- User asks about a Bundesgesetzblatt entry

## URL Patterns

### 1. OGH/Court decision by Geschäftszahl

```
https://www.ris.bka.gv.at/Ergebnis.wxe?Abfrage=Justiz&GZ=<URL-encoded GZ>&SucheNachRechtssatz=True&SucheNachText=True
```

Example: `5 Ob 105/24p` → `GZ=5+Ob+105%2f24p`

The result list contains links of form `/Dokumente/Justiz/JJT_YYYYMMDD_OGH.../...html` — fetch that next for the full decision.

### 2. Keyword search in judicature (Justiz)

```
https://www.ris.bka.gv.at/Ergebnis.wxe?Abfrage=Justiz&Suchworte=<keywords+url+encoded>&SucheNachRechtssatz=True&SucheNachText=True&ResultPageSize=50
```

Also available: `Abfrage=Vwgh` (Verwaltungsgerichtshof), `Abfrage=Vfgh` (Verfassungsgerichtshof).

### 3. Federal law paragraph (Bundesrecht konsolidiert)

```
https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Gesetzesnummer=<law ID>&Paragraf=<n>
```

Gesetzesnummern für häufige Gesetze:
- `10001622` — ABGB
- `20001921` — WEG 2002
- `10002296` — MRG
- `10002062` — StGB
- `10005387` — UGB

Unknown Gesetzesnummer? Search title first:
```
https://www.ris.bka.gv.at/Ergebnis.wxe?Abfrage=Bundesnormen&Titel=<title+keywords>
```

### 4. State law (Landesrecht)

Replace `Bundesnormen` with a state-specific Abfrage:
`LrVbg` (Vorarlberg), `LrW` (Wien), `LrT` (Tirol), `LrStmk` (Steiermark), etc.

### 5. Structured API (optional, returns JSON)

```
https://data.bka.gv.at/ris/api/v2.6/Judikatur?Applikation=Justiz&Geschaeftszahl=<GZ>
```

Use this when you need many results programmatically. For ad-hoc reading, the web URLs above are simpler.

## Workflow

1. Build the search URL from the pattern above.
2. `WebFetch` it with a prompt like "Extract the document URL(s) and case summary for this decision/topic."
3. If a document link is returned, `WebFetch` that URL for the full text.
4. Cite the Geschäftszahl and the RIS URL in your answer.

## Tips

- Geschäftszahlen encode the slash `/` as `%2f`, spaces as `+`.
- Full-text decisions are usually under `/Dokumente/Justiz/JJT_...` — the `.html` version is easiest to parse.
- "Rechtssätze" (RS-numbers, e.g. `RS0135294`) are extracted legal principles — useful to cite alongside the full decision.
- For consolidated law, the displayed text is always "geltende Fassung" at the request date — note the "In Kraft seit" line.
- If a Gesetzesnummer lookup fails, fall back to `Abfrage=Gesamtabfrage` with keywords.

## Limits

- RIS has no authentication; rate-limit yourself to a handful of requests per search.
- JUSLine, LexisNexis, RDB are paywalled and not covered by this skill.
- For older BGBl entries (pre-2004) use `Abfrage=BgblAlt` instead of `BgblAuth`.
