---
name: git-push-local-repo
description: 把本地项目推送到远程 Git 仓库（GitHub / Gitee / GitLab）的完整流程——推送前体检、写 .gitignore、初始化仓库、首次提交、关联远程、推送、验证，以及认证失败/推送被拒/大文件等报错的排查。当用户要求「把这个项目推送到 GitHub」「推送本地仓库」「git 提交并上传」「初始化 git 仓库并推送」「帮我 git push」「git push 报错了怎么解决」时使用。
agent_created: true
---

# 推送本地仓库到远程

把「本地写好的一堆文件」变成「远程仓库里的代码」：体检 → 忽略规则 → 初始化 → 提交 → 关联远程 → 推送 → 验证。

## 入口判断：先分清用户处于哪种情况

不要一上来就 `git add .`。先用 `git rev-parse --show-toplevel` 和 `git remote -v` 判断现状：

| 现状 | 从哪个阶段开始 |
|---|---|
| 项目还不是 git 仓库 | 阶段 2 → 阶段 7 全流程 |
| 已是仓库，但没配 remote | 阶段 5 起 |
| 已是仓库且有 remote，只是有新改动要传 | 阶段 7 |
| `git push` 报错，要排障 | 直接读 `references/troubleshooting.md` |
| `git push` 报网络错误（超时 / 代理 502 / 连接重置） | 先读 `references/troubleshooting.md` 第八节；若只有 `github.com` 不通而 `api.github.com` 通，用 `scripts/gh_api_push.py` 绕行 |

## 铁律

1. **先体检，再提交。** 永远先跑 `scripts/git_preflight.py`，看清「将会提交什么」。跳过这步最典型的后果是把虚拟环境（上百 MB）或密钥一起推上去。
2. **绝不 `git push --force`** 来解决冲突，除非用户明确要求；即便如此也优先 `--force-with-lease`，并先确认远程没有他人提交。
3. **绝不提交密钥。** `.env`、`*.key`、含 token 的文件一律先进 `.gitignore`。
4. **提交前把清单给用户过目。** `git status` 的结果要展示，不替用户决定提交什么。
5. **破坏性操作先问。** `reset --hard`、`git clean`、改已推送的历史，都必须先取得用户明确同意。
6. **不在任何文件里写 token**，也不把 token 拼进 remote URL（会残留在配置和命令历史里）。
7. **推送前确认远程仓库已存在。** 本机没有 `gh` CLI，无法自动创建仓库。

## 阶段 1：确认环境

```bash
git --version
git config --get user.name
git config --get user.email
git config --get credential.helper
git config --get init.defaultBranch
```

本机（Windows）已实测的基线：

| 项 | 值 | 影响 |
|---|---|---|
| git | `2.55.0.windows.3`（便携版，在 `.workbuddy/binaries/PortableGit/`） | 命令直接可用 |
| 提交身份 | 已配置 `user.name` / `user.email` | **仍要每次核对，不要假设** |
| credential.helper | 便携版 `git-credential-manager`(GCM) | 首次推送会弹**图形登录窗口**，必须提前提醒用户看屏幕 |
| `init.defaultBranch` | **未设置** → 默认建 `master` | 初始化必须显式写 `git init -b main` |
| `gh` CLI | **未安装** | 不能自动建远程仓库，见阶段 5 |

路径写法：Git Bash 下用 `/d/ai学习` 形式，中文路径正常，无需转义。

## 阶段 2：推送前体检

```bash
# Windows 上路径一律写 C:/... 正斜杠形式（Git Bash / PowerShell / cmd 都认）
python "C:/Users/<你>/<...>/scripts/git_preflight.py" "C:/path/to/项目"
```

> **Windows 路径坑（必读）**：Git Bash 的 `/c/Users/...` 传给**原生** Python 时不会自动转换。
> 脚本路径会因此被解析成 `C:\c\Users\...`，直接报 `No such file or directory`。
> 解决：**脚本路径与项目路径都写成 `C:/...` 形式**。脚本内部已用 `normalize_path()`
> 兜住「项目参数」，但**脚本自身的路径必须由调用方写对**。

脚本为**只读**，不修改任何文件。输出四块：git 状态、提交身份与凭证、工作树扫描（垃圾目录 / 大文件 / 疑似密钥）、结论。**issues 未清零前不要提交。**

报告中的远程地址会**自动给内嵌凭证打码**（`https://***@github.com/...`）。
若地址里确实内嵌了明文 token，脚本会额外提示改用 `git remote set-url origin <不含凭证的URL>`，
让凭证管理器保存凭据 —— 明文 token 躺在 `.git/config` 里是真实风险。

脚本已兼容两种路径写法：Git Bash 的 `/d/project` 与 Windows 的 `D:\project`（实测确认：Git Bash 传给原生 Windows Python 的 `/c/...` 不会被自动转换，脚本内部已做还原——这是踩过的坑）。退出码 0 表示无阻塞问题，1 表示有需要先处理的问题。

脚本能识别的典型风险：

- 目录名以 `.venv` / `venv` / `__pycache__` / `.ipynb_checkpoints` / `node_modules` 开头，且未被 `.gitignore` 覆盖
- 超过 5MB 的大文件（并单独警示超过 GitHub 100MB 硬限制的）
- 疑似密钥文件（`.env`、`*.key`、`*.pem`、含 `secret`/`token`/`credential` 字样的文件）

**真实案例**：`D:\ai学习` 项目里同时存在 `.venv` 和 `.venv_old_3.14`（各 100MB+），体检脚本会判定「未忽略，会被提交」。直接 `git add .` 会把整套 Python 解释器塞进仓库。**必须先做阶段 3。**

## 阶段 3：写 .gitignore（必须早于首次提交）

把 `assets/gitignore-python.txt` 复制到项目根目录，改名为 `.gitignore`。

**时机至关重要**：`.gitignore` 只对**未跟踪**的文件生效。一旦文件已被提交，之后写进 `.gitignore` 也不会让它脱离跟踪 —— 那时要额外 `git rm --cached`。所以顺序永远是：**先 .gitignore，再 add。**

## 阶段 4：初始化与首次提交

```bash
cd "/d/项目路径"
git init -b main            # -b main 不能省：本机未设默认分支名
git status                  # 第一遍：确认没有垃圾文件混进来
git add .
git status                  # 第二遍：这份「将提交」的清单必须展示给用户
git commit -m "首次提交：<一句话说明这是什么项目>"
```

**提交信息要求**：一行说清「做了什么」。学习项目可写 `首次提交：Python 基础练习与笔记`。不要用 `update`、`修改`、`.` 这类无信息量的信息。

**提交前检查点**：

- `git status` 里不应出现 `.venv`、`__pycache__`、`.ipynb_checkpoints`
- 用户自己的代码、notebook、`.vscode/settings.json` 应该在列表里
- 没有 `.env`、`*.key`

若远程仓库已经建好，此时一并关联：

```bash
git remote add origin <URL>
```

## 阶段 5：创建并关联远程仓库

**本机没有 `gh`，不能命令行建仓库。** 两条路：

**路线 A —— 引导用户在网页创建（默认做法）**

1. 让用户打开 https://github.com/new
2. Repository name 建议用英文（与本地目录名对应即可）
3. **不要勾选** "Add a README file"、.gitignore、license —— 勾了远程就会先有提交，首次推送会被拒
4. 创建后复制 HTTPS 地址，回到本地执行：

```bash
git remote add origin https://github.com/<用户名>/<仓库名>.git
git remote -v               # 核对地址
```

**路线 B —— 用代码托管类 connector**

检查当前会话的 connector 列表，若已连接 GitHub / GitLab 类服务，可代用户创建仓库后再关联。没有对应 connector 时不要臆造能力，直接走路线 A。

**Gitee 备用**：GitHub 直连不稳定时改用 Gitee（https://gitee.com/projects/new），后续命令完全相同。

## 阶段 6：推送

```bash
git push -u origin main
```

`-u` 把本地 main 与远程 main 绑定，之后直接 `git push` 即可。

**推送前必须提醒用户**：本机凭证助手是 GCM，首次推送通常会弹出**图形登录窗口**，需要用户本人去点登录。**不要静默等待** —— 不提醒的话用户会以为程序卡死了。

**推送后立即验证**（不要只报「成功」）：

```bash
git status -sb              # 应显示 ## main...origin/main，且无 ahead/behind
git log --oneline -1        # 确认最新提交在里面
git ls-remote origin        # 能列出远程引用，说明通道与凭据都通了
```

最后把仓库 URL 给用户，让他自己在浏览器打开确认能看到文件。

## 阶段 7：后续日常推送

```bash
git status -sb              # 看改了哪些文件
git diff                    # 看具体改动（可选）
git add -A                  # 或精确 add 指定文件
git commit -m "本次改了什么"
git push
```

**已经误提交了 `.venv` 之类的文件**：

```bash
git rm -r --cached .venv    # --cached 绝对不能漏，否则磁盘上的真实文件也被删
echo ".venv/" >> .gitignore
git commit -m "移除误提交的虚拟环境"
git push
```

**撤销最后一次提交**：`git reset HEAD~1`（保留改动、取消暂存，比 `--soft` 更安全）。

## 交付时要告诉用户什么

1. **仓库地址**，并请他在浏览器打开确认。
2. **本次提交了什么**（文件清单或数量）。
3. **.gitignore 忽略了什么**（尤其虚拟环境）。
4. **下次怎么推**：`git add -A && git commit -m "说明" && git push`。
5. **分支名是什么**（main 还是 master），以及为什么。
6. **遗留问题要明说**：大文件、疑似密钥、远程已有提交等，不要静默略过。

## 反面清单

- ❌ 不体检直接 `git add .` —— 本机现实存在 `.venv`（100MB+）被误提交的风险。
- ❌ 用 `git push --force` 解决冲突。
- ❌ 提交 `.env`、密钥、token。
- ❌ 把 token 写进 remote URL。
- ❌ `git rm -r .venv` 漏掉 `--cached`（会真实删除用户的虚拟环境）。
- ❌ 不提醒用户就去等 GCM 弹窗，然后把「等待登录」误判成「推送卡死」。
- ❌ 在用户项目目录做 `rm -rf`、`git clean -fdx` 等破坏性清理。
- ❌ 假设远程仓库已存在，不先 `git remote -v` 核对。
- ❌ 只输出「推送成功」而不给出验证命令的真实结果。
- ❌ 在没有 `gh` 的机器上声称能自动创建远程仓库。

## 附带资源

- `scripts/git_preflight.py` —— 推送前体检脚本，只读，纯标准库，无第三方依赖
- `scripts/gh_api_push.py` —— `github.com` 连不通时的绕行：改用 GitHub Git Data API 推送。逐字段复刻本地提交，远端 commit SHA 与本地完全一致，不会分叉；凭证按「URL 内嵌 → 凭证管理器 → `GITHUB_TOKEN`」顺序获取，脚本不保存密钥
- `references/troubleshooting.md` —— 认证失败、推送被拒、大文件超限、Windows 换行符等报错速查
- `assets/gitignore-python.txt` —— Python / Jupyter 项目 `.gitignore` 模板
