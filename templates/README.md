# Scripted video templates

One file per template: `templates/<name>.md`. Saagii names one when he asks for an edit ("use
hook-proof-cta"). Claude follows it for structure and pacing and fills it from the recording.

Suggested shape:

```markdown
# hook-proof-cta

- Format: 9:16, 30–45 s
- Beats:
  1. Hook (0–3 s): claim or question + a visible change by second 3. Layout: split, product on top.
  2. Context (1 line): who/what. Layout: face.
  3. Proof (2–4 shots): real footage or screen recording of the thing, each anchored to its spoken noun.
  4. Payoff: the result, calling back to the hook visual.
  5. CTA: punch-in on the face + end card with the handle.
- Captions: brand default.
- Music: <mood or none>. SFX: on visible actions only.
- Filming notes for Saagii: say the hook line first, one clean take per beat.
```

The `saagii-script-engine` skill (on Saagii's claude.ai account) writes bullet scripts in his voice. Templates
here describe how the *edit* is built from those bullets.
