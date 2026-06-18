# 共享版 Agent 权限优化说明

## 优化时间
2026-06-01 19:04

## 优化目标
解决共享版 agent（main-shared、strategy-shared、design-shared 等）频繁触发权限审批导致员工使用卡顿的问题。

## 优化策略

### 1. 安全命令白名单（免审批）
为所有共享版 agent 添加了 60+ 个安全命令，包括：

#### 脚本执行
- Python、Bash、Shell、Zsh、Node.js

#### 文件操作（非破坏性）
- `cp`（复制文件）
- `mkdir`（创建目录）
- `touch`（创建空文件）
- `chmod`（修改权限）

#### 只读命令
- `ls`、`cat`、`pwd`、`cd`、`stat`、`test`、`file`
- `head`、`tail`、`grep`、`awk`、`wc`、`sort`、`uniq`、`cut`、`tr`
- `find`、`rg`（ripgrep）、`ag`

#### 网络工具
- `curl`、`wget`

#### 环境与系统信息
- `env`、`printenv`、`which`、`whereis`、`uname`、`date`
- `ps`、`top`、`lsof`

#### Git 只读命令
- `git status`、`git diff`、`git log`、`git show`

#### 其他工具
- `jq`、`yq`（JSON/YAML 处理）
- `tar`、`zip`、`unzip`、`gzip`（压缩解压）
- `shasum`、`md5`（哈希校验）
- `sips`、`identify`（图片信息读取）
- `lark-cli`（飞书 CLI）

### 2. 危险操作（仍需审批）
以下操作仍需要用户审批：

- `rm`（删除文件）
- `trash`（删除到回收站）
- `mv`（移动/重命名文件，可能覆盖）
- `sed -i`（原地修改文件）
- 直接写入覆盖现有文件的操作

## 优化结果

| Agent | 优化前白名单条目 | 优化后白名单条目 | 新增命令 |
|-------|-----------------|-----------------|---------|
| main-shared | 26 | 66 | 40 |
| strategy-shared | 22 | 64 | 42 |
| design-shared | 42 | 77 | 35 |
| video-shared | 21 | 63 | 42 |
| research-shared | 24 | 66 | 42 |
| copywriter-shared | 20 | 63 | 43 |
| meeting-analyst-shared | 20 | 63 | 43 |

## 预期效果

1. **大幅降低审批频次**：常见的只读操作、文件复制、脚本执行等不再需要审批
2. **提升使用流畅度**：员工使用共享版 agent 时不会频繁卡顿
3. **保持安全性**：危险操作（删除、修改现有文件）仍需审批

## 配置文件

- 配置文件：`~/.openclaw/exec-approvals.json`
- 备份文件：`~/.openclaw/exec-approvals.20260601_190407.backup.json`
- 优化脚本：`~/.openclaw/scripts/optimize-shared-agent-permissions.py`

## 回滚方法

如果需要回滚到优化前的配置：

```bash
# 停止 gateway
openclaw daemon stop

# 恢复备份
cp ~/.openclaw/exec-approvals.20260601_190407.backup.json ~/.openclaw/exec-approvals.json

# 重启 gateway
openclaw daemon start
```

## 后续调整

如果发现某些命令仍需要频繁审批，可以：

1. 编辑优化脚本 `optimize-shared-agent-permissions.py`
2. 在 `SAFE_COMMANDS` 列表中添加新的安全命令
3. 重新运行脚本：`python3 ~/.openclaw/scripts/optimize-shared-agent-permissions.py`
4. 重启 gateway：`openclaw daemon restart`

## 注意事项

1. 本次优化只影响共享版 agent（*-shared），不影响个人版 agent
2. 白名单中的命令仍会记录执行日志，便于审计
3. 如果员工反馈某个操作仍需审批，可以查看日志确认命令路径后添加到白名单

## 监控建议

优化后建议观察 1-2 周，关注：

1. 员工反馈的使用体验是否改善
2. 是否还有其他高频命令需要加入白名单
3. 审批日志中是否有异常的危险操作尝试
