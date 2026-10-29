#!/bin/sh
# 启用本仓库的 git hooks。
#
# core.hooksPath 是「本地配置」，不会随仓库传递，所以每个克隆者都要跑一次。
#
#   sh scripts/install-hooks.sh
#
# 装了什么：pre-commit 会在提交前重建 data/index、data/detail，并同步
# index.html 里的 ?v= 版本戳。详见 .git-hooks/pre-commit。
set -e
cd "$(git rev-parse --show-toplevel)"

chmod +x .git-hooks/pre-commit
git config core.hooksPath .git-hooks

echo "已启用 git hooks：core.hooksPath = $(git config core.hooksPath)"
echo "  pre-commit → 自动重建分片 + 同步版本戳"
echo "  跳过本次检查：git commit --no-verify"
