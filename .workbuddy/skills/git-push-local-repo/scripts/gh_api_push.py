#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh_api_push.py —— 当 github.com 连不通（git push 必然失败）时，改用 GitHub Git Data API 推送。

用法:
    python gh_api_push.py [项目路径] [远程名]
    # 项目路径默认当前目录；远程名默认 origin

为什么需要它
------------
某些网络环境下：
    github.com      超时 / 代理返回 502 —— git push / git fetch / git ls-remote 全部失败
    api.github.com  正常（200）
这时 git 协议走不通，但 REST API 是通的，可以用「Git Data API」把提交直接写进远程。

关键点：逐字节复刻本地提交
--------------------------
依次调用 blobs -> trees -> commits -> PATCH refs，并且把 tree / parent / author /
committer / message **全部照搬本地**。这样生成的远端 commit SHA 与本地**完全相同**，
推完两边天然一致 —— 不需要 fetch、不需要 reset/rebase，`git status` 直接干净。

（若只在远端重新拼一个 commit，SHA 会不同，本地就会出现「分叉」，还得手工对齐。）

凭证来源（按顺序尝试，脚本本身不保存任何密钥）
    1) git remote get-url <remote> 内嵌的 https://user:token@...
    2) git credential fill（凭证管理器：GCM / Windows 凭据管理器 / libsecret）
    3) 环境变量 GITHUB_TOKEN

退出码: 0 = 成功; 1 = 失败
"""

import base64
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
MODE_FILE = "100644"


def git(args, cwd, binary=False):
    # 显式用 UTF-8 解码：git 输出的路径与提交信息都是 UTF-8，
    # 若走系统默认编码（中文 Windows 是 cp936），含中文的内容会乱码
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                       text=not binary,
                       encoding=None if binary else "utf-8",
                       errors=None if binary else "replace")
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace") if binary else p.stderr
        raise SystemExit("git %s 失败: %s" % (" ".join(args), err.strip()))
    return p.stdout


def normalize_path(p):
    """兼容 Git Bash 的 /c/Users/... 写法与 Windows 的 C:\\Users\\... 写法。"""
    if len(p) >= 3 and p[0] == "/" and p[1].isalpha() and p[2] == "/":
        p = p[1].upper() + ":" + p[2:]
    return p


def redact(text):
    return re.sub(r"://[^/\s@]+:[^/\s@]+@", "://***@", text)


def resolve_token(cwd, remote):
    """按 URL 内嵌 -> 凭证管理器 -> 环境变量 的顺序取 token。"""
    url = git(["remote", "get-url", remote], cwd).strip()
    m = re.match(r"https://([^:/@]+):([^@]+)@", url)
    if m:
        return m.group(1), m.group(2), "remote URL 内嵌凭证"

    host = re.search(r"://([^/]+)", url).group(1)
    payload = "protocol=https\nhost=%s\n\n" % host
    p = subprocess.run(["git", "credential", "fill"], cwd=cwd,
                       input=payload, capture_output=True, text=True, timeout=60)
    if p.returncode == 0 and p.stdout:
        fields = dict(
            line.split("=", 1) for line in p.stdout.splitlines() if "=" in line)
        if fields.get("password"):
            return fields.get("username", ""), fields["password"], "凭证管理器"

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return os.environ.get("GITHUB_USER", ""), token, "环境变量 GITHUB_TOKEN"

    raise SystemExit("拿不到凭证：URL 内嵌、凭证管理器、GITHUB_TOKEN 都没有")


def iso(ts, tz):
    off = (1 if tz[0] == "+" else -1) * (int(tz[1:3]) * 60 + int(tz[3:5]))
    t = datetime.timezone(datetime.timedelta(minutes=off))
    return datetime.datetime.fromtimestamp(ts, tz=t).isoformat()


def main():
    root = normalize_path(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    remote = sys.argv[2] if len(sys.argv) > 2 else "origin"
    root = os.path.abspath(root)

    if not os.path.isdir(os.path.join(root, ".git")):
        raise SystemExit("不是 git 仓库: %s" % root)

    url = git(["remote", "get-url", remote], root).strip()
    mm = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
    if not mm:
        raise SystemExit("无法从远程地址解析出 owner/repo: %s" % redact(url))
    owner, repo = mm.group(1), mm.group(2)

    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], root).strip()
    head = git(["rev-parse", "HEAD"], root).strip()

    # 起始点：优先用远程跟踪分支，没有就把 HEAD 的父提交当作起点
    tracking = "refs/remotes/%s/%s" % (remote, branch)
    if subprocess.run(["git", "rev-parse", "--verify", "--quiet", tracking],
                      cwd=root, capture_output=True).returncode == 0:
        base = git(["rev-parse", tracking], root).strip()
    else:
        base = git(["rev-parse", "HEAD^"], root).strip()

    commits = git(["rev-list", "--reverse", "%s..%s" % (base, head)],
                  root).strip().split()
    print("仓库    : %s/%s" % (owner, repo))
    print("分支    : %s" % branch)
    print("本地HEAD: %s" % head)
    print("起点    : %s" % base)
    print("待推送  : %d 个提交" % len(commits))
    if not commits:
        print("没有需要推送的提交，退出。")
        return
    print()

    user, token, source = resolve_token(root, remote)
    print("凭证来源: %s（%s）" % (source, user or "未知名"))
    print()

    def api(method, path, payload=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            API + path, method=method, data=data,
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json",
                     "User-Agent": "gh-api-push"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            raise SystemExit("API %s %s 失败: %s %s" % (method, path, e.code, detail))

    for sha in commits:
        raw = git(["cat-file", "commit", sha], root)
        tree_sha = re.search(r"^tree ([0-9a-f]+)", raw, re.M).group(1)
        parents = re.findall(r"^parent ([0-9a-f]+)", raw, re.M)
        a = re.search(r"^author (.+) <(.+)> (\d+) ([+-]\d{4})$", raw, re.M)
        c = re.search(r"^committer (.+) <(.+)> (\d+) ([+-]\d{4})$", raw, re.M)
        message = raw.split("\n\n", 1)[1]

        if not parents:
            raise SystemExit("提交 %s 没有父提交（首次提交），请改用普通 git push" % sha[:10])
        parent_sha = parents[0]
        # base_tree 必须是「父提交的 tree」这个远端已有的对象；
        # 传成本次的最终 tree 会报 422 base_tree is not a valid tree oid
        parent_tree = git(["rev-parse", "%s^{tree}" % parent_sha], root).strip()

        print("提交 %s  %s" % (sha[:10], message.strip().splitlines()[0]))

        # 必须用 -z（NUL 分隔）拿路径：git 默认 core.quotepath=true，
        # 会把「课程要点.md」这类中文名转义成 "\350\257\276..."，
        # 这种转义串既喂不回 git show、也传不了 API，必然失败。
        raw_diff = git(["diff", "--name-status", "-z",
                        "%s..%s" % (parent_sha, sha)], root)
        parts = [x for x in raw_diff.split("\0") if x != ""]
        entries = []
        i = 0
        while i < len(parts):
            status = parts[i].strip()
            i += 1
            if status[:1] in ("R", "C"):
                # 重命名 / 复制：后面跟两个路径（旧、新），删旧 + 写新
                old, path = parts[i], parts[i + 1]
                i += 2
                entries.append({"path": old, "mode": MODE_FILE,
                                "type": "blob", "sha": None})
            else:
                path = parts[i]
                i += 1
                if status[:1] == "D":
                    entries.append({"path": path, "mode": MODE_FILE,
                                    "type": "blob", "sha": None})
                    print("    %s %s" % (status, path))
                    continue
            content = git(["show", "%s:%s" % (sha, path)], root, binary=True)
            blob = api("POST", "/repos/%s/%s/git/blobs" % (owner, repo), {
                "content": base64.b64encode(content).decode("ascii"),
                "encoding": "base64"})
            entries.append({"path": path, "mode": MODE_FILE,
                            "type": "blob", "sha": blob["sha"]})
            print("    %s %s" % (status, path))

        tree = api("POST", "/repos/%s/%s/git/trees" % (owner, repo),
                   {"base_tree": parent_tree, "tree": entries})
        if tree["sha"] != tree_sha:
            print("    注意: 远端 tree %s 与本地 %s 不同" % (tree["sha"][:10], tree_sha[:10]))

        commit = api("POST", "/repos/%s/%s/git/commits" % (owner, repo), {
            "message": message,
            "tree": tree["sha"],
            "parents": [parent_sha],
            "author": {"name": a.group(1), "email": a.group(2),
                       "date": iso(int(a.group(3)), a.group(4))},
            "committer": {"name": c.group(1), "email": c.group(2),
                          "date": iso(int(c.group(3)), c.group(4))}})
        new_sha = commit["sha"]
        print("    远端 commit: %s  %s" % (
            new_sha[:10], "SHA 与本地一致" if new_sha == sha else "SHA 不一致"))

        api("PATCH", "/repos/%s/%s/git/refs/heads/%s" % (owner, repo, branch),
            {"sha": new_sha, "force": False})
        print()

    # 让本地的远程跟踪记录与远端保持一致（本环境 update-ref 可能静默失败，故直接写 ref 文件）
    final = git(["rev-parse", "HEAD"], root).strip()
    ref_path = os.path.join(root, ".git", "refs", "remotes", remote)
    os.makedirs(ref_path, exist_ok=True)
    with open(os.path.join(ref_path, branch), "w", encoding="ascii") as f:
        f.write(final + "\n")

    print("完成。远端 %s/%s 已指向 %s" % (remote, branch, final[:10]))
    print("提示: 稍后网络恢复时，可正常使用 git push；本次已推送的提交不会重复。")


if __name__ == "__main__":
    main()
