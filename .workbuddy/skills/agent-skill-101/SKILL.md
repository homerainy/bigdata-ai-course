---
name: "agent-skill-101"
description: "Explain the core concept of WorkBuddy Agent Skill in one minute. Use when the user wants to learn what an Agent Skill is, how to create one, or how it differs from a regular tool/script."
agent_created: true
---

# Agent Skill 101

A lightweight onboarding skill for understanding WorkBuddy Agent Skills.

## What is an Agent Skill?

An Agent Skill is a reusable instruction package for WorkBuddy. It is not a script or executable; it is a structured guide (primarily `SKILL.md`) that tells WorkBuddy:

- **When** to activate itself (trigger words / scenarios)
- **What** domain knowledge to apply
- **How** to execute a specific workflow step by step

Think of it as a "playbook" or "onboarding manual" that turns a general-purpose agent into a domain specialist.

## Anatomy of a Skill

A valid skill is a folder containing at least one required file:

```
skill-name/
├── SKILL.md           (required)   YAML frontmatter + Markdown instructions
├── assets/            (optional)   templates, icons, images, fonts
└── references/        (optional)   docs, schemas, examples for context
```

### SKILL.md Frontmatter (Required)

```yaml
---
name: "skill-name"
description: "Concise description so WorkBuddy knows when to use this skill."
agent_created: true
---
```

The `name` and `description` determine whether WorkBuddy loads this skill into context for a given user request.

## Skill vs. Tool vs. Regular Script

| Aspect | Agent Skill | Tool / MCP | Regular Script |
|--------|-------------|------------|----------------|
| Core content | Prompts / instructions | Executable functions | Standalone code |
| Purpose | Teach AI how to behave | Give AI new capabilities | Run directly by user |
| Activation | Triggered by keywords | Called explicitly | Executed manually |
| File of focus | `SKILL.md` | Tool schema / config | `.py`, `.js`, etc. |

## When to Create a Skill

Create or use this skill concept when the user asks:

- "What is an Agent Skill?"
- "How do I make a WorkBuddy Skill?"
- "Skill 和 Python 程序有什么区别？"
- "为什么别人的仓库有 `.workbuddy/skills/`？"
- "帮我检查一下这个 Skill 是否规范"

## How to Explain Agent Skill in 60 Seconds

Use this three-sentence pattern:

1. **定义**：An Agent Skill is a packaged guide, not code.
2. **结构**：It lives in `.workbuddy/skills/<name>/` and must contain `SKILL.md`.
3. **作用**：It tells WorkBuddy when to activate and what workflow to follow.

Add the file-tree diagram above if the user wants to see the structure.

## Common Mistakes to Avoid

- Putting only a `.py` file in the repo and calling it a Skill.
- Missing `SKILL.md` or forgetting the YAML frontmatter.
- Writing the description too vaguely; be specific about triggers.
- Duplicating long docs in `SKILL.md`; move them to `references/`.

## Quick Checklist

When reviewing a skill, verify:

- [ ] Folder is under `.workbuddy/skills/<skill-name>/`
- [ ] `SKILL.md` exists with valid YAML frontmatter
- [ ] Frontmatter includes `name`, `description`, and `agent_created: true`
- [ ] Instructions are written in imperative/infinitive form
- [ ] Optional `assets/` and `references/` are used only when needed
