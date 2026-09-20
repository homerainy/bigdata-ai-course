#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""git_preflight.py —— 推送前体检（只读，不修改任何文件）

用法:
    python git_preflight.py [项目路径]
    # 不传路径则检查当前工作目录

在 git add / commit / push 之前，先回答三个问题:
    1. 这个目录现在是 git 仓库吗？远程与身份配好了吗？
    2. 如果现在提交，会不小心带上哪些不该带的东西？
       （虚拟环境、缓存目录、密钥文件）
    3. 有没有超过阈值的大文件？

退出码: 0 = 未发现阻塞问题; 1 = 发现需要先处理的问题
"""

import os
import re
import subprocess
import sys

BIG_MB = 5.0

# 绝不该进仓库的目录名（前缀匹配，兼容 .venv_old_3.14 这类改名备份）
JUNK_DIR_PREFIXES = (
    ".venv", "venv", "env", "__pycache__", ".ipynb_checkpoints",
    "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "htmlcov", "site-packages",
)
JUNK_DIR_EXACT = ("dist", "build", ".cache", "logs", ".vscode-test")

# 绝不该进仓库的文件
JUNK_FILE_SUFFIXES = (".pyc", ".pyo", ".pyd", ".log", ".tmp")
JUNK_FILE_NAMES = (".DS_Store", "Thumbs.db", "desktop.ini")

# 敏感文件特征
SECRET_SUFFIXES = (".env", ".key", ".pem", ".p12", ".pfx", ".keystore")
SECRET_NAMES = (".netrc", "_netrc", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
                ".env.local", ".env.production")
SECRET_KEYWORDS = ("credential", "secret", "password", "passwd", "api_key",
                   "apikey", "access_token")


def normalize_path(p):
    """兼容 Git Bash 的 /c/Users/... 写法与 Windows 的 C:\\Users\\... 写法。

    Git Bash 传给 Windows 原生 Python 的路径不一定会被自动转换，
    /c/Users/x 会被 abspath 当成 C:\\c\\Users\\x —— 必须先手工还原。
    """
    if len(p) >= 3 and p[0] == "/" and p[1].isalpha() and p[2] == "/":
        # /c/Users/xxx  ->  C:/Users/xxx
        p = p[1].upper() + ":" + p[2:]
    return p


def redact_url(text):
    """把 URL 里内嵌的凭证打码，避免 token / 密码被打印进报告或日志。

    https://user:ghp_xxxxxxxx@github.com/a/b.git  ->  https://***@github.com/a/b.git
    """
    return re.sub(r"://[^/\s@]+:[^/\s@]+@", "://***@", text)


def run(cmd, cwd):
    """执行命令，返回 (退出码, stdout, stderr)。命令不存在时返回 (127, '', msg)。"""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "命令不存在: %s" % cmd[0]


def is_junk_dir(name):
    low = name.lower()
    if low.startswith(JUNK_DIR_PREFIXES):
        return True
    return low in JUNK_DIR_EXACT


def is_junk_file(name):
    low = name.lower()
    if low.endswith(JUNK_FILE_SUFFIXES):
        return True
    return low in JUNK_FILE_NAMES


def is_secret_file(name):
    low = name.lower()
    if low.endswith(SECRET_SUFFIXES) or low in SECRET_NAMES:
        return True
    if low == ".env" or low.startswith(".env."):
        return True
    return any(k in low for k in SECRET_KEYWORDS)


def human(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "%.1f %s" % (size, unit)
        size /= 1024.0


def scan_tree(root):
    """扫描工作树，返回 (垃圾目录, 大文件, 可疑敏感文件, 文件总数)"""
    junk_dirs, big_files, secrets, total = [], [], [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")          # 不扫描 git 内部
        keep = []
        for d in dirnames:
            if is_junk_dir(d):
                junk_dirs.append(os.path.relpath(os.path.join(dirpath, d), root))
            else:
                keep.append(d)
        dirnames[:] = keep                   # 剪枝，不进入垃圾目录内部
        for f in filenames:
            total += 1
            abspath = os.path.join(dirpath, f)
            rel = os.path.relpath(abspath, root)
            try:
                size = os.path.getsize(abspath)
            except OSError:
                continue
            if size > BIG_MB * 1024 * 1024:
                big_files.append((rel, size))
            if is_secret_file(f):
                secrets.append(rel)
    return junk_dirs, big_files, secrets, total


def parse_gitignore(root):
    """返回 .gitignore 中出现的规则集合（已去掉注释与空行）"""
    path = os.path.join(root, ".gitignore")
    if not os.path.isfile(path):
        return None
    rules = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                rules.add(line.rstrip("/").lstrip("/"))
    return rules


def covered(name, rules):
    """粗略判断某个目录名是否被 .gitignore 覆盖"""
    low = name.lower()
    for r in rules:
        rl = r.lower()
        if rl == low or rl == "**/" + low:
            return True
        if rl.endswith("/" + low):
            return True
        if low.startswith(rl) and rl.startswith(".venv"):
            return True
    return False


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    root = os.path.abspath(normalize_path(raw))
    issues = []
    notes = []

    print("=" * 62)
    print("推送前体检报告")
    print("项目路径: %s" % root)
    print("=" * 62)
    print()

    if not os.path.isdir(root):
        print("[错误] 路径不存在或不是目录: %s" % root)
        return 1

    # ---------- 一、Git 状态 ----------
    print("[1] Git 状态")
    code, _, _ = run(["git", "--version"], root)
    if code != 0:
        print("    git 命令不可用，无法继续。")
        return 1
    print("    git 版本: %s" % run(["git", "--version"], root)[1])

    code, top, _ = run(["git", "rev-parse", "--show-toplevel"], root)
    is_repo = code == 0 and bool(top)
    if not is_repo:
        print("    是否仓库: 否 —— 这个目录还没有 git 仓库")
        issues.append("需要先初始化仓库（git init -b main）")
        branch = remote = None
        commits = None
        dirty = None
    else:
        print("    是否仓库: 是")
        print("    仓库根目录: %s" % top)
        root = top
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)[1]
        commits = run(["git", "rev-list", "--count", "HEAD"], root)[1]
        print("    当前分支: %s" % (branch or "?"))
        print("    提交数量: %s" % (commits if commits.isdigit() else "0（还没有任何提交）"))
        porcelain = run(["git", "status", "--porcelain"], root)[1]
        dirty = len([x for x in porcelain.splitlines() if x.strip()])
        print("    未提交改动: %d 项" % dirty)
        remote = run(["git", "remote", "-v"], root)[1]
        if remote:
            first = remote.splitlines()[0]
            print("    远程仓库: %s" % redact_url(first))
            if redact_url(first) != first:
                notes.append(
                    "远程地址里内嵌了明文凭证（token / 密码），体检报告已自动打码；"
                    "但凭证仍明文存在 .git/config 中，建议改用 "
                    "git remote set-url origin <不含凭证的URL>，让凭证管理器保存凭据")
        else:
            print("    远程仓库: 未配置")
            issues.append("尚未关联远程仓库（git remote add origin <URL>）")
        if branch == "HEAD":
            issues.append("当前没有分支名（通常因还没有首次提交）")
        elif branch in ("master",):
            notes.append("当前分支是 master；GitHub 默认分支为 main，"
                         "如需统一执行: git branch -m main")
        if commits is not None and commits.isdigit() and int(commits) == 0:
            issues.append("还没有任何提交，需要先 commit")
        elif commits is not None and commits.isdigit() and int(commits) > 0:
            ahead = run(["git", "status", "-sb"], root)[1].splitlines()[0] if dirty is not None else ""
            if "ahead" in ahead:
                notes.append("本地领先远程: %s" % ahead)
    print()

    # ---------- 二、身份与凭证 ----------
    print("[2] 提交身份与凭证")
    name = run(["git", "config", "user.name"], root)[1]
    mail = run(["git", "config", "user.email"], root)[1]
    if name and mail:
        print("    user.name  = %s" % name)
        print("    user.email = %s" % mail)
    else:
        print("    提交身份: 未配置全（缺少 %s）"
              % ", ".join([k for k, v in (("user.name", name), ("user.email", mail)) if not v]))
        issues.append("缺少提交身份，先执行: "
                      "git config --global user.name \"你的名字\" 与 "
                      "git config --global user.email \"你的邮箱\"")

    helper = run(["git", "config", "--get", "credential.helper"], root)[1]
    if helper:
        print("    凭证助手: %s" % helper)
        if "git-credential-manager" in helper.lower():
            notes.append("凭证助手是 GCM：首次推送会弹出图形登录窗口，"
                         "请提前告知用户到屏幕上完成登录")
    else:
        print("    凭证助手: 未配置")
        notes.append("未配置凭证助手，HTTPS 推送时会要求输入用户名与密码"
                     "（推荐配置: git config --global credential.helper manager）")

    dbranch = run(["git", "config", "--get", "init.defaultBranch"], root)[1]
    if not dbranch:
        notes.append("init.defaultBranch 未设置，新建仓库默认分支将是 master；"
                     "初始化时请显式写 git init -b main")
    print()

    # ---------- 三、工作树扫描 ----------
    print("[3] 工作树扫描（判断哪些内容不该进仓库）")
    junk_dirs, big_files, secrets, total = scan_tree(root)
    print("    扫描到 %d 个文件" % total)

    rules = parse_gitignore(root)
    if rules is None:
        print("    .gitignore: 不存在")
        issues.append("缺少 .gitignore —— 现在提交会把虚拟环境等垃圾文件一并带上")
    else:
        print("    .gitignore: 存在，%d 条规则" % len(rules))
    print()

    if junk_dirs:
        print("    发现「不该提交」的目录 %d 个:" % len(junk_dirs))
        unignored = []
        for d in sorted(junk_dirs)[:15]:
            mark = ""
            base = os.path.basename(d)
            if rules is not None and covered(base, rules):
                mark = "  [已被 .gitignore 忽略]"
            else:
                unignored.append(d)
                mark = "  [未忽略，会被提交!]"
            print("      - %s%s" % (d, mark))
        if len(junk_dirs) > 15:
            print("      ... 另有 %d 个" % (len(junk_dirs) - 15))
        if unignored:
            issues.append("有 %d 个垃圾目录未被 .gitignore 覆盖，"
                          "先补 .gitignore 再提交" % len(unignored))
        print()

    if secrets:
        print("    [严重] 发现疑似敏感文件 %d 个:" % len(secrets))
        for s in secrets[:10]:
            print("      - %s" % s)
        issues.append("疑似敏感文件（密钥/密码/凭据）会被提交，"
                      "必须加入 .gitignore 并确认内容")
        print()

    if big_files:
        big_files.sort(key=lambda x: -x[1])
        print("    发现大文件（> %.0f MB）%d 个:" % (BIG_MB, len(big_files)))
        for rel, size in big_files[:10]:
            print("      - %s  (%s)" % (rel, human(size)))
        over100 = [x for x in big_files if x[1] > 100 * 1024 * 1024]
        if over100:
            issues.append("存在超过 100MB 的文件，GitHub 会直接拒绝推送，"
                          "需改用 Git LFS 或移出仓库")
        else:
            notes.append("大文件会让仓库体积膨胀，确认是否真的需要提交")
        print()

    # ---------- 四、结论 ----------
    print("[4] 结论")
    if issues:
        print("    暂不建议直接推送，先处理以下 %d 项:" % len(issues))
        for i, msg in enumerate(issues, 1):
            print("      %d. %s" % (i, msg))
    else:
        print("    未发现阻塞问题，可以进入提交与推送流程。")
    if notes:
        print()
        print("    另有提示 %d 条（不阻塞，但要留意）:" % len(notes))
        for i, msg in enumerate(notes, 1):
            print("      %d. %s" % (i, msg))
    print()
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
