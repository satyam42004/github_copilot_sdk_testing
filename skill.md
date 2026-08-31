---
name: html-generation
description: Generate clean, self-contained HTML pages using the repository create tool.
---

# HTML Generation Skill

Use this skill when the user asks to create, generate, export, or build an HTML page.

## Requirements
1. Generate valid HTML5.
2. Include `<!DOCTYPE html>`, `<html lang="en">`, and responsive viewport metadata.
3. Prefer self-contained HTML with CSS in a `<style>` block.
4. Use semantic and accessible HTML.
5. Keep the design clean and responsive.
6. Do not invent external assets unless requested.
7. Save generated HTML using the repository `create` tool.
8. Use a `.html` filename.
9. Never write outside the configured repository.
10. Report the exact created path only after the tool succeeds.

## Tool policy
For HTML creation, use the custom repository `create` tool exposed by this session.
Do not use an alternative built-in file creation mechanism.

## Safety
File creation is a modifying operation and remains subject to Human-in-the-Loop approval.
