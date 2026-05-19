# Judge Rubric

Score from 0 to 5.

5: Correct, source-grounded, version-aware, concise, and directly useful for coding.

4: Correct and source-grounded with minor missing nuance.

3: Mostly correct but incomplete, too broad, or contains noisy context.

2: Partially relevant but risky, weakly sourced, or misses the main query.

1: Mostly wrong, noisy, or unsupported by the cited docs.

0: No useful answer, no docs evidence, or unusable output.

Also mark:

- `expected_source_used`: true/false
- `hallucinated_api`: true/false
- `excessive_context`: true/false
- `version_mismatch`: true/false

Primary judgement evidence:

1. Did Oz retrieve useful local files?
2. Did the agent read and cite the right local files?
3. Did the answer use the docs accurately?
4. Did the answer avoid unnecessary token-heavy context?
