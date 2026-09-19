# Candidate investigation workflow

This is the first workflow contract. It is executable through the project CLI inside Codex/Rosalind; a standalone model API integration has not yet been built.

## Investigator request

Investigate an ordered gene-pair candidate using the supplied public study evidence. Report what is supported, what is ambiguous, and which additional evidence would change the decision. Distinguish RNA evidence, protein plausibility and measured protein function. Link each factual claim to a source record or reproducible computation.

## Bounded tools

- `chrna build`: verify source hashes, preserve evidence states, construct candidate and sequence tables.
- `chrna inspect GENE_A:GENE_B`: retrieve input features without revealing confirmation outcomes.
- `chrna benchmark`: execute development comparisons under the fixed protocol.
- `chrna inspect GENE_A:GENE_B --include-published-outcomes`: explicitly revealed case review; never a hidden-label prediction.

Do not invent a probability of biological truth from a ranking score. If reference reconstruction, replicate mapping or a protein measurement is unavailable, state the gap.

## Initial demo

1. Build and validate the data; display unmatched names and the absence of biological negatives.
2. Inspect one candidate without published outcomes.
3. Explain the evidence and uncertainties using source fields only.
4. Reveal the published outcome as a separate step, labelled retrospective review.
5. Show the development baseline comparison. Do not describe it as a trained model's result.

## Remote controller

Follow AGENTS.md and infra/budget-policy.json. The CPU controller may prepare analysis and bounded GPU jobs after authentication. It must record the selected quote and existing project instances before each GPU launch, check the combined hourly ceiling, and stop its GPU after the job. It must not alter unrelated teammates' instances or copy authentication material into this repository.
