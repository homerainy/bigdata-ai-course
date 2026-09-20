# 大数据与人工智能 课程仓库

个人课程学习仓库，记录学习笔记、作业和项目代码。

## 📂 目录结构

```
bigdata-ai-course/
├── README.md                    # 本文件（总览导航）
├── .gitignore                   # Git 忽略规则
│
├── .workbuddy/skills/           # ⭐ WorkBuddy 官方技能包（老师检查重点）
│   ├── concept-learning-generator/   # 概念学习资料生成器（核心作业）
│   │   ├── SKILL.md                  # 技能说明书
│   │   ├── assets/                   # 资源文件
│   │   └── references/               # 参考资料
│   │
│   ├── concept-learner/              # 层层递进式刷题技能
│   │   ├── SKILL.md
│   │   └── scripts/skill.py          # 5关20题
│   │
│   ├── agent-skill-101/              # Agent Skill 概念讲解
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   └── references/
│   │
│   └── git-push-local-repo/          # 推送本地仓库到远程（2026-09-20）
│       ├── SKILL.md                  # 七阶段推送流程
│       ├── scripts/git_preflight.py  # 推送前体检脚本（只读，不修改文件）
│       ├── references/               # 认证失败/推送被拒等报错速查
│       └── assets/                   # .gitignore 模板
│
├── docs/                        # 文档资料
│   ├── GIT_CHEATSHEET.md        # Git 命令速查表
│   └── agent-skill-guide.html   # Agent Skill 可视化学习页
│
├── notes/                       # 学习笔记
│   └── agent-skill-一分钟速通.html
│
├── code/                        # 代码与示例
│   └── hello.py                 # 入门示例
│
├── homework/                    # 作业
│   └── scripts/                 # 第 1 课练习（2026-09-17）
│       ├── 01.py                # print 基础练习
│       ├── 01.ipynb             # Jupyter notebook 练习
│       └── 0917课程要点.md       # 课程要点笔记
│
└── projects/                    # 课程项目（待填充）
```

## 🔧 环境配置

| 工具 | 版本 |
|------|------|
| Python | 3.12.10 |
| Git | 2.55.0 |
| VS Code | 1.136.0 |

## 🚀 运行示例

```bash
# 概念学习资料生成器（WorkBuddy 自动调用 SKILL.md）

# 刷题程序
python .workbuddy/skills/concept-learner/scripts/skill.py

# 推送前体检（只读，不修改任何文件）
python .workbuddy/skills/git-push-local-repo/scripts/git_preflight.py .
```

## 📚 课程内容

- [ ] 大数据基础（Hadoop / Spark）
- [ ] 数据存储与处理
- [ ] 机器学习基础
- [ ] 深度学习
- [ ] 人工智能应用

## 📖 学习日志

| 日期 | 内容 |
|------|------|
| 2026-09-03 | 初始化仓库，配置开发环境 |
| 2026-09-05 | 学习 Agent Skill，写一分钟速通笔记 + 测试题 |
| 2026-09-10 | 添加 concept-learning-generator 概念学习资料生成器 Skill（核心作业） |
| 2026-09-17 | 第 1 课：Python 环境搭建（3.12.10 + venv）+ print 基础练习，作业归档至 homework/scripts/ |
| 2026-09-20 | 添加 git-push-local-repo 推送本地仓库技能（含推送前体检脚本） |
