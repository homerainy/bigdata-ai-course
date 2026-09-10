---
name: "concept-learner"
description: "A layered, progressive quiz skill for reviewing Big Data and AI concepts. Use when the user wants to practice questions, review course material, or test their knowledge through an interactive quiz that increases in difficulty level by level."
agent_created: true
---

# Concept Learner（层层递进刷题）

An interactive quiz skill for reviewing Big Data and Artificial Intelligence concepts through progressively harder levels.

## Purpose

Help the user review and reinforce course knowledge by running an interactive, level-by-level quiz. The quiz covers Python basics, control flow, data structures, data analysis, and machine learning / AI, with difficulty increasing at each level.

## When to Use

Activate this skill when the user says things like:

- "帮我刷题" / "做几道题" / "测试一下我的知识"
- "复习一下大数据与人工智能课程内容"
- "练练 Python / 机器学习的选择题"
- Any request to run a progressive quiz or self-test.

## How to Run

Run the bundled quiz script with Python:

```bash
python .workbuddy/skills/concept-learner/scripts/skill.py
```

Or from the repository root:

```bash
python .workbuddy/skills/concept-learner/scripts/skill.py
```

## Quiz Design

The quiz has 5 levels, from easiest to hardest:

1. Python 入门 — basic syntax, variables, data types, I/O
2. 流程控制 — conditionals and loops
3. 数据结构 — list, dict, tuple, set
4. 数据分析 — pandas / numpy basics
5. 机器学习与 AI — supervised learning, model evaluation, frameworks

Each level has 4 multiple-choice questions. After each answer the script shows immediate right/wrong feedback plus an explanation. A level is passed at 60 points; finishing all levels shows a total score summary.

## Extending the Quiz

To add questions, edit `scripts/skill.py` and append entries to the `LEVELS` data structure. Each question object contains:

```python
{
    "question": "题目内容",
    "options": ["选项1", "选项2", "选项3", "选项4"],
    "answer": "选项2",   # 正确选项的文本，须与 options 中某一项完全一致
    "explain": "解析说明"
}
```

Keep the difficulty ascending across levels.
