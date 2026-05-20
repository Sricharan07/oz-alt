# KnowledgeBase

**Kind:** expected
**Signature:** `KnowledgeBase`
**Source:** https://docs.smallest.ai/atoms/llms-full.txt

## Example

```markdown
* **Legal & Compliance** — Include policies, regulations, approved language. Agents stay within bounds.

***

## Key Concepts

### One Agent, One KB

Each agent can link to one knowledge base via the `globalKnowledgeBaseId` field. This becomes the default source for all conversations with that agent.

### KB Independence

Knowledge bases exist independently of agents. You can:

* Create a KB first, then link agents later
* Reuse one KB across multiple agents
* Update KB content without touching agent configuration
```
