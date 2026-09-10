# Git 速查手册

> 上课时忘了命令就来这里查。

## 📂 仓库路径

```
C:\Users\lenovo\WorkBuddy\2026-09-03-10-56-06\bigdata-ai-course
```

用 VS Code 打开：在仓库路径下打开终端（VS Code 里 `Ctrl+``）输入：

```bash
code .
```

---

## 🔧 常用 Git 命令（必背）

```bash
# 1. 查看状态（文件改了哪些）
git status

# 2. 添加文件到暂存区
git add .                  # 添加所有改动
git add 文件名             # 添加指定文件

# 3. 提交（写一条说明）
git commit -m "完成了XX作业"

# 4. 推送到 GitHub
git push
```

**懒人三连（一次完成 add + commit + push）**：

```bash
git add . && git commit -m "提交说明" && git push
```

---

## 🚀 网络恢复后补 push 步骤（GitHub）

等你能打开 `github.com` 后：

1. **生成 token**：打开 `https://github.com/settings/tokens/new`，勾 `repo`，生成 `ghp_` 开头的令牌
2. **把 token 发给我**，我会帮你完成 `remote add` + `push`

或者你自己在终端执行（把 `ghp_xxx` 换成你的 token）：

```bash
cd "/c/Users/lenovo/WorkBuddy/2026-09-03-10-56-06/bigdata-ai-course"

# 创建远程仓库（如果还没创建）
curl -u homerainy -X POST https://api.github.com/user/repos \
  -d '{"name":"bigdata-ai-course","description":"大数据与人工智能课程仓库","private":false}'

# 添加远程地址
git remote add origin https://github.com/homerainy/bigdata-ai-course.git

# 推送（会让你输入用户名和密码，密码就是 token）
git push -u origin main
```

---

## 🐍 Python 3.12 使用

```bash
# 查看版本
"/c/Users/lenovo/AppData/Local/Programs/Python/Python312/python.exe" --version

# 装包（建议加 --user 避免权限问题）
"/c/Users/lenovo/AppData/Local/Programs/Python/Python312/python.exe" -m pip install --user numpy pandas

# 跑脚本
"/c/Users/lenovo/AppData/Local/Programs/Python/Python312/python.exe" 脚本名.py
```

> 💡 **建议**：在 VS Code 里 `Ctrl+Shift+P` → 输入 `Python: Select Interpreter` → 选 `Python 3.12.10`，就不用每次敲完整路径了。