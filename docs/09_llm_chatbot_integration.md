# LLM Chatbot Integration (Optional)

This project can add an optional LLM chatbot as a public explainer layer.

Phase 1 uses a static GitHub Pages site and chatbot-ready knowledge base. A real chatbot widget should only be added after the public docs are reviewed.

## Deployment targets
- GitHub Pages
- Cargo sites
- Shopify pages

## Important implementation rules
- Do not embed chatbot code directly in the GitHub README.
- Do not expose API keys in frontend code.
- Do not call LLM APIs directly from browser JavaScript with secret credentials.
- Use official third-party chatbot provider embed code, or a backend proxy.

## Suggested first knowledge base sources
- `docs/08_public_faq.md`
- `docs/02_v1_to_v4_iteration.md`

## Suggested starter questions
- "Introduce the V1 to V4 iteration."
- "What is the current progress of this project?"
- "Explain the V1 smart contract in simple terms."
- "What should Edmond Jordan review first?"
- "What is not claimed by this project?"
- "How is this different from a legal REC?"
- "What is Material Event Signature?"
