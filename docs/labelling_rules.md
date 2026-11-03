# Labelling Rules: Fact Spans

Version 0.1 · 03.11.2026 · Fadil · draft for the agreement round

These rules say which spans of text count as a **fact** and which type each one gets. They apply to:

- NER training data (train split only)
- the hand-labelled test set
- the 50-sentence agreement round (Cohen's kappa)
- the pre-labellers in the NER labelling plan (regex, spaCy/CLASSLA, Gemini prompt)

The same rules apply to source articles and generated posts, and to English and Bosnian text.

Notation in this document: `[text]TYPE` marks a labelled span.

## Fact types

| Type | What counts |
| --- | --- |
| PERSON | Names of specific real people |
| ORG | Names of specific organisations and their units |
| DATE | Calendar dates, months with a year, years, academic years |
| NUMBER | Cardinal quantities: counts, amounts, money, percentages |

Places, events, times and ordinals are **not** labelled in v1 (see [Open questions](#open-questions)).

## General rules

| # | Rule | Example |
| --- | --- | --- |
| G1 | Label the surface form exactly as written, with its case ending. Never the base form. | `sa [Univerzitetom u Sarajevu]ORG`, not *Univerzitet u Sarajevu* |
| G2 | Whole words only. Never cut a word in the middle. | `[Amrom]` not `[Amr]om` |
| G3 | Leave out prepositions, articles, quotes, brackets and trailing punctuation. **Exception:** the Bosnian ordinal dot belongs to the date or number. | `on [October 21]DATE.` · `[21. oktobra 2026.]DATE` |
| G4 | Longest span wins. No nested or overlapping spans. | `[IBU Faculty of Engineering]ORG`, not `[IBU]ORG Faculty of Engineering` |
| G5 | Label every mention, including repeats and abbreviations. | `[International Burch University]ORG ([IBU]ORG)` |
| G6 | Label what is written, even if it is wrong. A misspelled name or a wrong date is still a fact. Catching these is the point of the project. | `[Skeledzija]PERSON` (missing ž) still counts as PERSON |
| G7 | Hashtags and @handles do not count, even if they contain a name or a year. | `#IBUCareerFair2026`, `@ibu.edu.ba` |
| G8 | If you are unsure, label your best guess and add the `unsure` tag in Label Studio. Never skip the span. Unsure cases are reviewed after the agreement round. | |

## PERSON

**Counts:** a full name, a surname alone, or a first name alone when it refers to one specific person, in any case form.

**Leave out:** titles and roles (prof., dr., mr. sc., Rector, dekan). Rewrites often add or drop these, and that is not a changed fact.

| | Example | Note |
| --- | --- | --- |
| ✅ EN | `Rector [Mehmet Can]PERSON welcomed the new students.` | Role is outside the span |
| ✅ BS | `Studenti su razgovarali s prof. dr. [Amrom Hodžić]PERSON.` | Instrumental *Amrom* (from *Amra*); title outside the span |
| ❌ Does not count | `Izložba je otvorena u [Gazi Husrev-begovoj biblioteci]ORG.` | The person's name is part of an ORG name, so the whole span is ORG (G4). A role alone (*rektor*, *the dean*) is also not PERSON. |

## ORG

**Counts:** named universities, faculties, departments, offices, companies, NGOs, government bodies, embassies and international bodies. Abbreviations count too (IBU, UNSA, EU).

| | Example | Note |
| --- | --- | --- |
| ✅ EN | `IBU signed a memorandum with the [University of Sarajevo]ORG.` | *the* is outside the span; also label `[IBU]ORG` |
| ✅ BS | `Sporazum je potpisan sa [Univerzitetom u Sarajevu]ORG.` | *u Sarajevu* is part of the name, so it stays inside the span |
| ❌ Does not count | `Konferencija je održana u Sarajevu.` | A city, country or place alone is not ORG. Generic words (*the university*, *fakultet*) are not ORG either. |

## DATE

**Counts:** a day with a month, a month with a year, a year, an academic year (*2026/2027*) or a date range, in any format or language. A range is **one** span.

**Leave out:** *godine/godina*, weekdays, *on/the*.

| | Example | Note |
| --- | --- | --- |
| ✅ EN | `The fair takes place on Monday, [October 21, 2026]DATE.` | Weekday is outside the span |
| ✅ BS | `Sajam će biti održan [21. oktobra 2026.]DATE godine.` | Genitive *oktobra*; ordinal dots inside; *godine* outside. Short forms count too: `[21.10.]DATE` |
| ❌ Does not count | `Radionica je održana prošle sedmice, u ponedjeljak.` | Relative and unanchored expressions (*yesterday*, *next week*, *prošle sedmice*, *u ponedjeljak*) have no calendar value to compare. Years inside names don't count either (*Agenda 2030*). |

Croatian or Serbian month names in generated posts still count as DATE: `[21. listopada]DATE`, `[jul 2026.]DATE`.

## NUMBER

**Counts:** cardinal quantities written in digits or words: counts, amounts, money and percentages. Multiplier words stay inside the span (*million*, *miliona*, *hiljada*). Written-out numbers are one span (*dvadeset pet*).

**Leave out:** units, currency and the percent sign or word (*KM*, *€*, *%*, *posto*, *percent*).

| | Example | Note |
| --- | --- | --- |
| ✅ EN | `More than [200]NUMBER students and [five]NUMBER companies took part.` | Digits and words both count |
| ✅ BS | `Stipendiju od [1.500]NUMBER KM dobilo je [pet]NUMBER studenata.` | *1.500* = 1500 (dot as thousands separator); *KM* outside. Decimal comma: `[1,5 miliona]NUMBER` |
| ❌ Does not count | `IBU je jedan od najboljih univerziteta prema COVID-19 istraživanju.` | *jedan od* / *one of* is not a quantity. Numbers inside names, codes and identifiers (*COVID-19*, *Erasmus+*, *IT 3004*, *Industry 4.0*, phone and room numbers) don't count. Numbers inside a DATE don't count separately. Ordinals (*first*, *3rd*, *treći*) are not labelled in v1. |

## Tricky cases

| Case | Decision |
| --- | --- |
| `prof. dr. Amra Hodžić` | `prof. dr. [Amra Hodžić]PERSON` |
| `IBU Faculty of Economics` | One ORG span (G4) |
| `21–23. oktobra 2026.` | One DATE span |
| `20%` / `20 posto` | `[20]NUMBER%` / `[20]NUMBER posto` |
| `dvadeset i pet studenata` | `[dvadeset i pet]NUMBER studenata` |
| `International Burch University (IBU)` | Two ORG spans. Whether they are the same fact is decided by normalisation, not by the annotator. |
| `2026/2027 academic year` | `[2026/2027]DATE academic year` |
| Name without diacritics (`Hodzic`) | Still PERSON (G6) |

## Open questions

Decide these before the agreement round. Adding a type later means relabelling everything.

1. **Locations.** Should we add LOC? Changing *Sarajevo* to *Mostar* is a real fact error, but it is outside the four types in the proposal.
2. **Events, programmes and awards** (*Erasmus+*, *IBU Career Fair*). Should these be ORG, a new type, or not labelled?
3. **Times and ordinal rankings** (*10:00*, *ranked 3rd*). Should these count?
4. **Unit of agreement.** We could compute kappa on tokens (BIO tag per token) or on whole spans. Token level is the usual choice and is easier to compute from a Label Studio export.

## Notes for normalisation

These forms will appear in labelled spans. The normaliser has to handle them:

- Month names in Bosnian (*oktobar*), Croatian (*listopad*) and Serbian (*avgust*, *jul*), in any case (*oktobar / oktobra / oktobru*).
- Ordinal dots (*21.*, *2026.*) and short dates (*21.10.*).
- Thousands dot and decimal comma (*1.500*, *1,5*) against English *1,500* and *1.5*.
- Written numbers in both languages (*pet*, *five*, *dvadeset pet*, *hiljadu* / *tisuću*).
- Inflected names (*Amrom Hodžić* ↔ *Amra Hodžić*). Comparing these needs lemmatisation or fuzzy matching, not exact string match.
