# Domain Docs

## Layout

This is a single-context repository:

- `GLOSSARY.md` at the repo root: domain vocabulary.
- `docs/adr/`: architecture decision records.

## Before exploring

Read `GLOSSARY.md` and ADRs relevant to the area being explored or changed.

If those files do not exist, proceed silently. Do not suggest creating them upfront.
The domain-modeling skill creates them lazily when terms or decisions are resolved.

## Use the glossary's vocabulary

Use defined terms in issue titles, proposals, hypotheses, and test names.
Follow any distinctions or avoided synonyms recorded in the glossary.

If a needed concept is missing, reconsider whether the term belongs to this domain;
record a genuine vocabulary gap for domain-modeling.

## Flag ADR conflicts

Surface contradictions with an existing ADR explicitly rather than silently overriding it.
Name the ADR and explain why reopening the decision is warranted.
