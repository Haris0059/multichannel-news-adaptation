# Plan: Bosnian Labelling

Version 0.1 · 03.11.2026 · Fadil · draft, to agree with Haris

## Where Bosnian text comes from

- All 166 source articles are in English.
- The IBU CMS has no Bosnian versions. On 03.11.2026, `en` returned 166 articles and `bs-BA`, `hr` and `sr` each returned 0.
- So the only Bosnian text is the posts from `src/generate_posts.py` (Haris, due 13.11.2026): 3 Bosnian posts per article, so about 348 posts from the 116 train articles.

This is the right training domain, because the checker reads exactly these posts. But it is machine-written Bosnian, possibly with Croatian or Serbian forms (*listopad*, *jul*), not native text. That goes in the paper's limitations.

## Steps

| # | Step | When | Depends on |
| --- | --- | --- | --- |
| 1 | English agreement round: 50 article sentences (`src/sample_sentences.py`), labelled by Fadil and Haris, kappa from `src/agreement.py` | now – 13.11. | rules v0.1 |
| 2 | Agree the posts file format with Haris (path, `post_id`, `slug`, `channel`, `language`, `text`) | this week's call | — |
| 3 | Extend `sample_sentences.py` to sample from train-split Bosnian posts | when step 2 is agreed | step 2 |
| 4 | Bosnian agreement round: 25 post sentences, labelled by both, kappa reported separately for Bosnian | 13.–16.11. | Bosnian posts |
| 5 | Rules v0.2 from the disagreements in both rounds | 16.11. | steps 1, 4 |
| 6 | Pick the annotator models on **Bosnian** F1 as well as English, since a model that is good on English can still fail on case forms | 16.11. | step 4 |
| 7 | NER training data: 300+ sentences, about 100 from English articles, 100 from English posts and 100+ from Bosnian posts, train split only | 16.–20.11. | steps 5, 6 |

If the posts arrive late, steps 4–7 move, but step 1 does not wait for them.

## What to watch in the Bosnian round

- Names in other cases: *prof. dr. Amre Hodžić* (genitive), *s Amrom Hodžić* (instrumental).
- Organisation names in other cases: *Univerzitetom u Sarajevu*, *na Internacionalnom Burch univerzitetu*.
- Dates with ordinal dots and *godine*: *21. oktobra 2026. godine*.
- Numbers with the thousands dot and the decimal comma (*1.500*, *1,5*), and written numbers (*pet*, *dvadeset i pet*).
- Croatian or Serbian forms in posts, which still count (rule notes under DATE).

## To ask Haris

1. The path and fields of the posts file, and whether each post has a stable `post_id`.
2. Whether Bosnian posts for the train split will be ready by 13.11.
3. Whether we keep the IBU names in their English form inside Bosnian posts (*International Burch University*) or let Gemini translate them. This changes what the ORG labels look like.
