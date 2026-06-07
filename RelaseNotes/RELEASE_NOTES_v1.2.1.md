# Release Notes v1.2.1 / 发布说明 v1.2.1

A focused patch release fixing two **data-loss** bugs in cloaked-file detection and archive grouping. No breaking changes.

一个聚焦的补丁版本，修复了伪装文件检测和档案分组中的两个**数据丢失**问题。无破坏性更改。

## 🐛 Bug Fixes / 错误修复

### Don't rename ordinary files into bogus archive parts / 不再把普通文件改名成伪造的档案分卷
A plain non-archive file whose name ends in digits (e.g. `2382`) could be renamed into a fake 7z multipart part (`2.7z.382`). It was then swept into a same-named real archive set and **deleted at the end without ever being extracted — losing the user's data**.

Root cause: `_verify_with_signature()` always returned `True`, so the weak extensionless/digit-suffix cloaking rules renamed *any* digit-suffixed file.

The signature gate now distinguishes deliberate cloaking from a guess:
- If the name carries an explicit archive token (`.7z` / `.rar` / `.zip`, via `ARCHIVE_TOKEN_RE`), the rename is trusted — continuation parts legitimately have no signature (e.g. `something.7z.002删除`).
- If the type was only **guessed** from a trailing number, a real magic-byte signature is now **required** before renaming.
- On verification error the tool is now conservative and **skips** the rename instead of assuming the file is valid.

Genuine cloaked first parts and `.7z.00N删` style parts still uncloak correctly.

名字以数字结尾的普通（非档案）文件（例如 `2382`）原先可能被改名成伪造的 7z 分卷（`2.7z.382`），随后被并入同名的真实档案集合，**在结尾被删除却从未解压 —— 导致用户数据丢失**。

根因：`_verify_with_signature()` 永远返回 `True`，导致弱规则（无扩展名 / 尾部数字）会改名**任何**带数字后缀的文件。

签名校验现在区分"有意伪装"与"猜测"：
- 名字中带有显式档案标记（`.7z` / `.rar` / `.zip`，由 `ARCHIVE_TOKEN_RE` 识别）时，信任改名 —— 续卷本来就没有签名（例如 `something.7z.002删除`）。
- 若类型只是从尾部数字**猜测**得到，改名前现在**必须**有真实的魔数签名。
- 校验出错时改为保守处理，**跳过**改名，而不是假定文件有效。

真正的伪装首卷以及 `.7z.00N删` 之类的分卷仍能正确还原。

### Don't merge different archive types that share a base name / 不再合并同名但类型不同的档案
The similarity check in `_should_group_files` ignored the archive extension, so a standalone `.7z` could be swept into a spanned `.zip` / `.z01` group when they shared a base name and directory. The merged multipart group then **deleted the `.7z` along with the zip parts (data loss)** and mishandled the set during extraction.

Fix: the similarity path now requires `ext1 == ext2`, so only same-family archives group that way. `.zip` / `.z01` still group via the exact `(base, ext)` check, and `foo.7z` stays its own single group alongside the `foo.zip` / `foo.z01` set.

`_should_group_files` 的相似度判断忽略了档案扩展名，导致独立的 `.7z` 在与跨卷 `.zip` / `.z01` 同名且同目录时被并入同一组。合并后的多卷组随后**把 `.7z` 连同 zip 分卷一起删除（数据丢失）**，解压时也处理错误。

修复：相似度路径现在要求 `ext1 == ext2`，只有同家族档案才走该路径分组。`.zip` / `.z01` 仍通过精确的 `(base, ext)` 判断分组，而 `foo.7z` 与 `foo.zip` / `foo.z01` 集合并存时保持为独立的单档案组。

## ✅ Test Coverage / 测试覆盖

### New/Updated Tests / 新增/更新测试
- **Cloaked false-positives** (`TestCloakedFalsePositives`): a plain `2382` file is not detected/renamed, `uncloak_file` leaves a non-archive digit-suffixed file untouched, and a genuine cloaked 7z first part (real magic bytes) still uncloaks to `secret.7z.001`. Two existing `_verify_with_signature` tests were updated to pin the stricter behavior.
- **Grouping guard**: unit (`_should_group_files`) regression that `foo.7z` vs `foo.zip` are not grouped, plus an integration (`create_groups_by_name`) regression asserting `foo.7z` stays a standalone group while `foo.zip` / `.z01` / `.z02` form one spanned set.

Total: **168 tests pass** (was 163 in v1.2.0, +5 new).

- **伪装误报**（`TestCloakedFalsePositives`）：普通的 `2382` 文件不会被检测/改名；`uncloak_file` 对非档案的数字后缀文件保持原样；而真正的伪装 7z 首卷（带真实魔数）仍会还原为 `secret.7z.001`。两个原有的 `_verify_with_signature` 测试更新为锁定更严格的行为。
- **分组守卫**：单元测试（`_should_group_files`）回归确认 `foo.7z` 与 `foo.zip` 不被分到一组；集成测试（`create_groups_by_name`）回归确认 `foo.7z` 保持独立组，而 `foo.zip` / `.z01` / `.z02` 组成一个跨卷集合。

总计：**168 个测试通过**（v1.2.0 是 163 个，新增 5 个）。

## 🚀 Migration Notes / 迁移说明

### For Users / 用户须知
- **No breaking changes.**
- Ordinary files whose names happen to end in digits (e.g. `2382`) are no longer mistaken for archive parts, renamed, or deleted — they are left exactly as they are.
- A standalone `.7z` that shares a base name with a spanned `.zip` set is now extracted on its own instead of being deleted with the zip parts.

- **无破坏性更改。**
- 名字恰好以数字结尾的普通文件（例如 `2382`）不再被误认为档案分卷、被改名或被删除 —— 它们保持原样。
- 与跨卷 `.zip` 集合同名的独立 `.7z` 现在会被单独解压，而不会随 zip 分卷一起被删除。
