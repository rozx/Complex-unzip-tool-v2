---
name: complex-unzip-release
description: "在 Complex-unzip-tool-v2 的已有发布分支上准备版本升级、双语 release note 和发布 PR。用于发版准备或补齐发布材料；不负责创建分支、合并 PR 或切回 main。"
---

# Complex Unzip Tool 发布准备

仅用于 `pyproject.toml` 中包名为 `complex-unzip-tool-v2` 的项目。始终用中文与用户沟通，发布说明沿用中英双语格式。

从用户已选定的发布分支开始，不创建或切换分支。按本次请求执行版本升级、发布说明和 PR 准备；只请求其中一项时，不自动扩大范围。创建或更新发布 PR 的请求包含对应提交和推送；仅请求本地文档或版本修改时，不自行推送。合并 PR 和发布操作不属于本技能。

先阅读项目的 [README 发布流程](../../../README.md)、[AGENTS.md](../../../AGENTS.md) 和 [release.yml](../../../.github/workflows/release.yml)。与当前文档有冲突时，按 README 和用户指令执行。复用 [scripts/version.py](../../../scripts/version.py) 和 [scripts/release.py](../../../scripts/release.py)，不要另建发布工具。

## 核对当前状态

- 查看工作区、当前分支和 `origin`，保留用户已有改动，确认本次目标版本 `X.Y.Z`。
- 检查当前版本和已有发布材料，识别已经完成的步骤，避免重复 bump 或重复创建 PR。
- 准备发布 PR 时，来源分支须为已有的 `release/*` 分支，通常命名为 `release/vX.Y.Z`，目标为 `main`。若没有选定符合条件的现有分支，明确缺少的信息，不自动创建分支。
- 核对本次改动及关联 issues，阅读最近一版 `ReleaseNotes/RELEASE_NOTES_v*.md`，沿用其格式，只总结本次版本实际包含的变更。

## 升级版本

`pyproject.toml` 的 `version`、`complex_unzip_tool_v2/__init__.py` 的 `__version__` 和 `.bumpversion.cfg` 的 `current_version` 必须一致。

使用项目现有 bump 命令，例如 patch 发布：

```sh
poetry run bump-patch
```

按目标版本选用 `bump-minor` 或 `bump-major`。明确指定的版本不是下一次普通增量时，使用 `poetry run bump2version --allow-dirty --new-version X.Y.Z patch`，并核对最终三处声明。若已经是目标版本，不再次 bump。配置中的 `commit = False`、`tag = False` 保持不变，完成检查后统一提交。

优先使用现有 Poetry 环境。没有 Poetry 时，可用项目可用的 Python 3.11+ 虚拟环境运行同一脚本和命令；需要补依赖时使用临时隔离环境并按 `poetry.lock` 对齐，不修改项目依赖。直接调用 `scripts.version.bump_patch()` 等函数时，确保该环境的 `bump2version` 在 PATH 中。

## 编写发布说明并更新文档

创建 `ReleaseNotes/RELEASE_NOTES_vX.Y.Z.md`：

- 标题为 `# Release Notes vX.Y.Z / 发布说明 vX.Y.Z`，先用英文和中文简述本版变化。
- 沿用已有的 `Bug Fixes / 错误修复` 等分类，仅保留本版需要的分类。
- 每项描述具体触发场景和修复后的行为，链接关联 issue；确有升级注意事项时再说明。
- 验证结果只写实际执行过的检查，未完成的其他平台构建不能写成已通过。

保持中英文 README 的现有结构，更新当前版本摘要、发布包表格、示例包名及发布说明链接。版本摘要必须描述新版本内容，不能只把上一版摘要中的版本号替换掉。旧版发布说明保持原样。

## 本地校验

在仓库根目录运行：

```sh
poetry run python -m scripts.release version
poetry run python -m scripts.release verify-notes
poetry run python -m scripts.release verify-engines
poetry run main --version
poetry run main --help
poetry run pytest -q
poetry run python -m scripts.smoke_test
git diff --check
```

确认版本输出为本次目标，发布说明存在且非空，并使用实际测试结果填写 PR。单元测试继续模拟解压调用；真实引擎检查交给已有的源码冒烟脚本。若从未安装项目的临时虚拟环境运行源码冒烟，子进程会进入临时目录，需要将仓库根目录加入 `PYTHONPATH`。

按项目配置执行格式、lint 和类型检查。全仓静态检查存在既有问题时，与修改前基线比较，确认没有新增诊断并如实说明；不要为本次发布顺带重构或清理无关问题。测试失败或新增诊断时先修复，不把失败标为通过。

## 提交并准备发布 PR

- 外部写入前核实 `origin` 的仓库归属、可见性和写入权限，确认与用户指定项目一致。检查远端 tag 和 Release，目标版本不得与已公开的版本或其他提交的 tag 冲突。
- 提交本次相关文件并推送当前发布分支。已有相同来源分支、目标 `main` 的未合并 PR 时更新它，不重复创建；否则创建 PR。
- 标题以 `Release vX.Y.Z` 开头，后接本版主要变化。正文概括问题、最终行为、版本升级、发布说明及实际验证结果，使用 `Closes #N` 关联本版已解决的 issue。
- 完整发布材料准备好后添加 `release` 标签，确保来源为 `release/*`、目标为 `main`。把已有草稿标记为可审阅；用户明确要求草稿时保留草稿状态。
- 在 PR 中说明：合并时带有 `release` 标签才会触发自动发布。工作流使用确切的合并提交构建全部平台，并直接采用对应版本 release note 的原文作为发布正文。缺失或空白说明不能用自动生成的 GitHub notes 替代。
- 不手动创建发布 tag 或 GitHub Release，不移动已有 tag，也不覆盖已公开的 Release。由工作流完成构建、校验和发布。
- 在 Codex 中创建或更新 PR 后，使用可用的 `attach_artifact` 工具将其关联到当前聊天。

完成后报告目标版本、发布说明路径、PR 链接和实际验证结果；CI 尚未完成时明确其状态。本技能到 PR 准备完成为止，不执行合并，也不包含合并后的分支切换。
