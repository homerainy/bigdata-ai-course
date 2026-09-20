# 推送报错速查

按「症状 → 原因 → 处理」组织。遇到报错先在这里定位，再动手。

---

## 一、认证类

### `fatal: Authentication failed for 'https://github.com/...'`

原因：凭据过期、账号密码变更，或用了已废弃的密码认证。

处理：
```bash
# 清掉旧凭据后重试（Windows 凭据管理器里的 github 条目）
git credential-manager erase <<< $'protocol=https\nhost=github.com\n'
git push
```
或让用户在「设置 → 凭据管理器 → Windows 凭据」里删掉 github.com 相关条目，再推送触发重新登录。

### `remote: Support for password authentication was removed on August 13, 2021`

原因：GitHub 早已不允许用账号密码走 HTTPS，必须用 token 或 OAuth。

处理：用 `git-credential-manager` 走浏览器 OAuth 登录（本机已配置好），或改用 Personal Access Token 作为密码，或换 SSH。

### 推送时没有任何反应，也没弹登录窗口

原因：非交互环境（自动化/后台任务）下，GCM 的图形窗口可能不出现。

处理：
1. 先告知用户「需要你在弹出的窗口里点一下登录」；
2. 若确实无法弹窗，改为让用户在自己的终端里执行一次 `git push` 完成登录，之后再回到自动化流程；
3. 不要在命令行里打印或写入 token。

### 想改用 SSH

```bash
ssh-keygen -t ed25519 -C "你的邮箱"
cat ~/.ssh/id_ed25519.pub        # 把公钥贴到 GitHub → Settings → SSH keys
ssh -T git@github.com            # 验证连通
git remote set-url origin git@github.com:用户名/仓库名.git
```

---

## 二、remote 配置类

### `error: remote origin already exists`

```bash
git remote set-url origin <新地址>       # 改地址，推荐
# 或先删再加
git remote remove origin && git remote add origin <新地址>
```

### remote 里已经有一个 README，推送被拒

```bash
git pull --rebase origin main            # 先把远程内容拉下来并置于本地提交之前
git push -u origin main
```

### ⚠️ remote 地址里内嵌了明文 token（`.git/config` 泄露凭证）

若 `git remote -v` 显示 `https://用户名:ghp_xxxx@github.com/...`，说明 token / 密码
**明文存在 `.git/config`** —— 同步网盘、备份、恶意软件，或任何能读到该目录的人都能直接拿到写权限。

正确做法是交给凭证管理器保存，URL 保持干净：

```bash
# 1. 先把凭据交给系统凭证管理器（GCM 会存进 Windows 凭据管理器，加密存储）
printf 'protocol=https\nhost=github.com\nusername=<用户名>\npassword=<token>\n\n' | git credential approve

# 2. 确认能自动取回（应输出 username= 与 password=）
printf 'protocol=https\nhost=github.com\n\n' | git credential fill

# 3. 只有第 2 步成功，才清洗 URL
git remote set-url origin https://github.com/<用户名>/<仓库>.git
```

**两个必须注意的点：**

1. **第 3 步一定要在第 2 步成功之后再做。** 若凭证管理器取不回来就清洗了 URL，
   会陷入「URL 里没凭据、管理器里也没有」的死局，推送彻底做不了。
2. **网络不通时 GCM 会卡住**（它要联网做 provider 校验），`git credential approve` /
   `fill` 都可能长时间无响应（`curl`/`timeout` 报 124 = 超时）。此时**先别迁移**，
   等网络正常再操作。

**已经泄露了怎么办**：清洗 URL 只是止血，不等于凭证安全。
**必须去 GitHub → Settings → Developer settings → Personal access tokens 把那个 token
作废并重新生成**，再用新 token 更新本地凭据。

---

## 三、推送被拒类

### `! [rejected] main -> main (non-fast-forward)` 或 `(fetch first)`

原因：远程有本地没有的提交（常见于在网页上改过文件，或协作中别人推过）。

处理：
```bash
git fetch origin
git log --oneline HEAD..origin/main      # 先看差异，确认是什么
git pull --rebase origin main
git push
```

**绝不使用 `git push --force`** 来「解决」这个问题 —— 会覆盖并永久丢失远程上别人的提交。用户若坚持，改用 `--force-with-lease`，且必须先确认远程没有他人提交。

### `error: src refspec main does not match any`

原因：本地还没有提交，或分支不叫 main。

```bash
git log --oneline -1                     # 有没有提交？
git branch                               # 分支叫什么？
git branch -m main                       # 改名
git commit -m "首次提交"                  # 若确实没有提交
git push -u origin main
```

---

## 四、分支名类

本机 `init.defaultBranch` 未设置，`git init` 默认建 `master`。GitHub 默认分支是 `main`，两者不一致会带来困惑。

处理：初始化时就写死
```bash
git init -b main
```
若已经建成了 master：
```bash
git branch -m main                       # 本地改名
# 已推送到远程时：先在 GitHub 网页把默认分支改成 main，再删掉远程 master
git push origin --delete master
```

---

## 五、误提交了不该提交的文件

### 关键认知：**`.gitignore` 对被跟踪的文件无效**

文件一旦被 git 跟踪，之后再写进 `.gitignore` 也不会生效。必须先从索引里移除：

```bash
git rm -r --cached .venv                 # 只从索引移除，磁盘文件保留（--cached 是关键）
git rm -r --cached .venv_old_3.14
git commit -m "移除误提交的虚拟环境"
```
**务必带 `--cached`** —— 漏掉它会把磁盘上的真实文件一起删掉。

### 撤销最后一次提交但保留改动

```bash
git reset --soft HEAD~1                  # 保留改动在暂存区
git reset HEAD~1                         # 保留改动但取消暂存（更安全，优先用这个）
```

### 改提交信息

```bash
git commit --amend -m "新的提交信息"        # 仅在未推送到远程时使用
```

### 已经推送过的大文件 / 密钥

改历史属于破坏性操作，**必须先取得用户明确同意**，且优先考虑：
1. 立刻作废泄露的密钥（改密码、撤销 token）—— 这比清历史更紧急；
2. 再考虑 `git filter-repo` 重写历史（会改变所有 commit hash，协作者需重新克隆）。

---

## 六、大文件类

### `remote: error: File xxx is 135.00 MB; this exceeds GitHub's file size limit of 100.00 MB`

GitHub 硬限制：单文件 > 100MB 直接拒绝；> 50MB 会警告。

处理：
```bash
# 方案 A：移出仓库（推荐给数据集、模型权重）
#   加入 .gitignore，然后：
git rm --cached path/to/bigfile

# 方案 B：用 Git LFS
git lfs install
git lfs track "*.pth"
git add .gitattributes
```

---

## 七、Windows 特有

### `warning: LF will be replaced by CRLF in ...`

**正常警告，不必处理。** Git 在 Windows 上做换行符自动转换。想彻底一致可显式声明：
```bash
git config --global core.autocrlf true   # Windows 上的一般推荐值
```

### `fatal: detected dubious ownership in repository at 'D:/xxx'`

目录属主与当前用户不一致（常见于 U 盘、跨账号目录）。
```bash
git config --global --add safe.directory 'D:/xxx'
```

### 中文文件名显示成 `\346\226\207\344\273\266`

```bash
git config --global core.quotepath false
```

### 中文路径操作

Git Bash 下用 `/d/ai学习` 形式即可，`cd`、`git add` 全部正常，无需转义。

---

## 八、网络类

### `Failed to connect to github.com port 443: Timed out` / 连接被重置

按顺序排查：
```bash
ping github.com                          # DNS 是否解析
curl -sI --max-time 10 https://github.com  # 443 是否通
git config --global --get http.proxy     # 是否配了失效的代理
```
若本机走代理：
```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
# 取消代理
git config --global --unset http.proxy
```
GitHub 直连不稳定时，也可改用 Gitee 作为远程，或走 SSH 的 443 端口。

### 代理报 `CONNECT tunnel failed, response 502` —— github.com 彻底不通

先分清是「全都不通」还是「只有 github.com 不通」：

```bash
curl -s -o /dev/null -w "github.com     %{http_code}\n" https://github.com
curl -s -o /dev/null -w "api.github.com %{http_code}\n" https://api.github.com
```

如果**前者挂、后者通**：git 协议（push / fetch / ls-remote）全都走不通，
但 REST API 是通的 —— 可以绕行：

```bash
python "C:/.../scripts/gh_api_push.py" "C:/path/to/项目" origin
```

它用 Git Data API 把本地提交写进远程（`blobs → trees → commits → PATCH refs`），
并**逐字段复刻本地提交**（tree / parent / author / committer / message 全照搬），
因此远端 commit SHA 与本地**完全相同**，推完不会分叉，不需要 fetch / reset / rebase。

> 自己实现时最容易踩的坑：建 tree 时 `base_tree` 必须是**父提交的 tree**
> （远端已有的对象）。传成本次的最终 tree 会报
> `422 base_tree is not a valid tree oid`。

**这不是长久之计**：拉取他人提交、看远程历史仍需 `git fetch`。先用它把提交送上去保住进度，
网络恢复后再正常 `git push`。该脚本只处理「新增 / 修改 / 删除文件」的普通提交，
**不处理合并提交、标签、Git LFS、以及需要重建大对象的场景**。

---

## 九、通用排查顺序

推送失败时，按这个顺序逐层确认，不要凭猜测改配置：

```bash
git status -sb                # 1. 本地状态、是否领先远程
git remote -v                 # 2. 远程地址对不对
git log --oneline -3          # 3. 有没有该有的提交
git ls-remote origin          # 4. 远程能不能读到（测通道与凭据）
git push -u origin <分支名>    # 5. 显式指定分支再推一次
```

`git ls-remote origin` 能通说明认证没问题，问题在分支或提交层面；不通说明卡在认证或网络。
