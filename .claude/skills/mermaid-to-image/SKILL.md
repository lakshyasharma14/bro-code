---
name: mermaid-to-image
description: Render ```mermaid fences in this blog's .mdx posts to PNG images, since the site's MDX pipeline has no mermaid plugin and renders them as plain text. Use whenever a post contains a mermaid diagram, or the user reports a flowchart/diagram showing as text on the site.
---

This repo (`bro-code`, a Next.js/Tailwind blog) has no mermaid rendering in its MDX pipeline — no remark/rehype mermaid plugin anywhere in the codebase. A ` ```mermaid ` fence in a post therefore renders as a plain code block of text on the live site, not a diagram.

The fix is to pre-render each diagram to a PNG and embed it as a normal image, matching how every other diagram/screenshot in this blog is embedded:

```
<center>![alt text](/static/images/<name>.png)</center>
```

## Steps

1. Find the `.mdx` post with the mermaid fence(s), e.g. `data/blog/<slug>.mdx`.
2. Run the helper script from the repo root:

   ```bash
   python3 .claude/skills/mermaid-to-image/render_mermaid.py data/blog/<slug>.mdx
   ```

   This extracts every ` ```mermaid ` fence, renders it via the public [mermaid.ink](https://mermaid.ink) API (no local Chromium/Node dependency needed — useful since this repo's own Node version, 16.x, is too old for the current `@mermaid-js/mermaid-cli`), saves each as `public/static/images/<slug>/diagram-N.png`, and replaces the fence in place with `<center>![Diagram N](...)</center>`. It writes a `.mdx.bak` backup before editing.
3. **Read the rendered PNG(s)** (the `Read` tool can view images) to confirm the diagram actually rendered correctly — mermaid syntax errors come back from mermaid.ink as a small error-message image, not a failed HTTP call, so this check is required, not optional.
4. Replace the placeholder alt text (`Diagram 1`, `Diagram 2`, ...) with a real one-line description of what the diagram shows.
5. Delete the `.mdx.bak` file once you've confirmed the result.
6. If a post has multiple mermaid diagrams and you want more descriptive filenames than `diagram-N.png`, rename the files in `public/static/images/<slug>/` and update the corresponding paths in the `.mdx` — the script's naming is a safe default, not a requirement.

## Notes

- Default render width is 1600px on a white background — this blog doesn't render these images with dark-mode-aware inversion, so white background matches the existing convention (see e.g. `public/static/images/chatgpt.webp`) rather than trying for transparency.
- If mermaid.ink is unreachable, the alternative is `npx @mermaid-js/mermaid-cli` (`mmdc`), but that requires Node ≥18.4 — this repo's local Node (16.x) is too old for it, matching the same "Found invalid or discontinued Node.js Version: 16.x" issue seen in Vercel builds. Fixing that Node version (locally via nvm, and in Vercel's Project Settings → Node.js Version) is a separate, unrelated task.
- This only fixes existing posts. If you're aware the pipeline itself should support live mermaid rendering (a rehype-mermaid or remark-mermaidjs plugin wired into `next.config.js` / the MDX pipeline), that's a bigger change — flag it to the user rather than doing it silently as part of an image-fix task.
