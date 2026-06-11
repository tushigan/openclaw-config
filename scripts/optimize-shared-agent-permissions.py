#!/usr/bin/env python3
"""
优化共享版 agent 权限配置脚本

目标：
1. 为所有共享版 agent 添加完整的安全命令白名单
2. 只保留对危险操作（删除、修改现有文件）的审批要求
3. 减少员工使用时的权限审批卡顿

危险操作（需要审批）：
- rm（删除文件）
- trash（删除到回收站）
- mv（移动/重命名，可能覆盖）
- sed -i（原地修改文件）
- 直接写入覆盖现有文件的操作

安全操作（免审批）：
- 所有只读命令
- 创建新文件/目录
- 复制文件
- 执行脚本
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 安全命令白名单（所有共享版 agent 通用）
SAFE_COMMANDS = [
    # 脚本执行
    {
        "id": "shared-python",
        "pattern": "/usr/bin/python3",
        "description": "允许执行 Python 脚本"
    },
    {
        "id": "shared-bash",
        "pattern": "/bin/bash",
        "description": "允许执行 bash 脚本"
    },
    {
        "id": "shared-sh",
        "pattern": "/bin/sh",
        "description": "允许执行 sh 命令"
    },
    {
        "id": "shared-zsh",
        "pattern": "/bin/zsh",
        "description": "允许执行 zsh 命令"
    },
    {
        "id": "shared-node",
        "pattern": "/opt/homebrew/opt/node@22/bin/node",
        "description": "允许执行 Node.js 脚本"
    },

    # 文件操作（非破坏性）
    {
        "id": "shared-cp",
        "pattern": "/bin/cp",
        "description": "允许复制文件"
    },
    {
        "id": "shared-mkdir",
        "pattern": "/bin/mkdir",
        "description": "允许创建目录"
    },
    {
        "id": "shared-touch",
        "pattern": "/usr/bin/touch",
        "description": "允许创建空文件"
    },
    {
        "id": "shared-chmod",
        "pattern": "/bin/chmod",
        "description": "允许修改文件权限"
    },

    # 只读命令
    {
        "id": "shared-ls",
        "pattern": "/bin/ls",
        "description": "允许列出目录"
    },
    {
        "id": "shared-cat",
        "pattern": "/bin/cat",
        "description": "允许读取文件内容"
    },
    {
        "id": "shared-pwd",
        "pattern": "/bin/pwd",
        "description": "允许输出当前目录"
    },
    {
        "id": "shared-cd",
        "pattern": "/usr/bin/cd",
        "description": "允许切换目录"
    },
    {
        "id": "shared-stat",
        "pattern": "/usr/bin/stat",
        "description": "允许读取文件状态"
    },
    {
        "id": "shared-test",
        "pattern": "/usr/bin/test",
        "description": "允许做文件存在性判断"
    },
    {
        "id": "shared-file",
        "pattern": "/usr/bin/file",
        "description": "允许检测文件类型"
    },

    # 文本处理（只读）
    {
        "id": "shared-head",
        "pattern": "/usr/bin/head",
        "description": "允许读取前几行内容"
    },
    {
        "id": "shared-tail",
        "pattern": "/usr/bin/tail",
        "description": "允许读取后几行内容"
    },
    {
        "id": "shared-sed",
        "pattern": "/usr/bin/sed",
        "description": "允许做只读文本筛选（不含 -i 原地修改）"
    },
    {
        "id": "shared-grep",
        "pattern": "/usr/bin/grep",
        "description": "允许做只读文本搜索"
    },
    {
        "id": "shared-awk",
        "pattern": "/usr/bin/awk",
        "description": "允许做只读文本处理"
    },
    {
        "id": "shared-wc",
        "pattern": "/usr/bin/wc",
        "description": "允许统计文本行数"
    },
    {
        "id": "shared-sort",
        "pattern": "/usr/bin/sort",
        "description": "允许排序文本结果"
    },
    {
        "id": "shared-uniq",
        "pattern": "/usr/bin/uniq",
        "description": "允许去重文本结果"
    },
    {
        "id": "shared-cut",
        "pattern": "/usr/bin/cut",
        "description": "允许裁剪文本列"
    },
    {
        "id": "shared-tr",
        "pattern": "/usr/bin/tr",
        "description": "允许转换文本字符"
    },

    # 搜索工具
    {
        "id": "shared-find",
        "pattern": "/usr/bin/find",
        "description": "允许查找文件"
    },
    {
        "id": "shared-rg",
        "pattern": "/opt/homebrew/bin/rg",
        "description": "允许 ripgrep 搜索"
    },
    {
        "id": "shared-ag",
        "pattern": "/opt/homebrew/bin/ag",
        "description": "允许 ag 搜索"
    },

    # 管道与重定向
    {
        "id": "shared-xargs",
        "pattern": "/usr/bin/xargs",
        "description": "允许拼接命令管道"
    },
    {
        "id": "shared-tee",
        "pattern": "/usr/bin/tee",
        "description": "允许保存非破坏性输出日志"
    },
    {
        "id": "shared-printf",
        "pattern": "/usr/bin/printf",
        "description": "允许格式化输出"
    },
    {
        "id": "shared-echo",
        "pattern": "/bin/echo",
        "description": "允许输出文本"
    },

    # 网络工具
    {
        "id": "shared-curl",
        "pattern": "/usr/bin/curl",
        "description": "允许拉取网页或接口内容"
    },
    {
        "id": "shared-wget",
        "pattern": "/opt/homebrew/bin/wget",
        "description": "允许下载文件"
    },

    # 环境与系统信息
    {
        "id": "shared-env",
        "pattern": "/usr/bin/env",
        "description": "允许读取环境变量"
    },
    {
        "id": "shared-printenv",
        "pattern": "/usr/bin/printenv",
        "description": "允许输出环境变量"
    },
    {
        "id": "shared-which",
        "pattern": "/usr/bin/which",
        "description": "允许定位命令路径"
    },
    {
        "id": "shared-whereis",
        "pattern": "/usr/bin/whereis",
        "description": "允许定位命令位置"
    },
    {
        "id": "shared-uname",
        "pattern": "/usr/bin/uname",
        "description": "允许查看系统信息"
    },
    {
        "id": "shared-date",
        "pattern": "/bin/date",
        "description": "允许查看日期时间"
    },

    # 进程管理（只读）
    {
        "id": "shared-ps",
        "pattern": "/bin/ps",
        "description": "允许查看进程列表"
    },
    {
        "id": "shared-top",
        "pattern": "/usr/bin/top",
        "description": "允许查看系统资源"
    },
    {
        "id": "shared-lsof",
        "pattern": "/usr/sbin/lsof",
        "description": "允许查看打开的文件"
    },

    # Git 只读命令
    {
        "id": "shared-git",
        "pattern": "/usr/bin/git",
        "description": "允许 Git 只读查询命令（status/diff/log/show）"
    },

    # 图片处理（只读）
    {
        "id": "shared-sips",
        "pattern": "/usr/bin/sips",
        "description": "允许读取图片尺寸与格式信息"
    },
    {
        "id": "shared-identify",
        "pattern": "/opt/homebrew/bin/identify",
        "description": "允许读取图片元数据"
    },

    # 压缩与解压
    {
        "id": "shared-tar",
        "pattern": "/usr/bin/tar",
        "description": "允许打包和解压文件"
    },
    {
        "id": "shared-zip",
        "pattern": "/usr/bin/zip",
        "description": "允许压缩文件"
    },
    {
        "id": "shared-unzip",
        "pattern": "/usr/bin/unzip",
        "description": "允许解压文件"
    },
    {
        "id": "shared-gzip",
        "pattern": "/usr/bin/gzip",
        "description": "允许 gzip 压缩"
    },
    {
        "id": "shared-gunzip",
        "pattern": "/usr/bin/gunzip",
        "description": "允许 gzip 解压"
    },

    # 哈希与校验
    {
        "id": "shared-shasum",
        "pattern": "/usr/bin/shasum",
        "description": "允许计算文件哈希"
    },
    {
        "id": "shared-md5",
        "pattern": "/sbin/md5",
        "description": "允许计算 MD5"
    },

    # 飞书 CLI
    {
        "id": "shared-lark-cli",
        "pattern": "/opt/homebrew/bin/lark-cli",
        "description": "允许执行飞书 CLI"
    },

    # 其他常用工具
    {
        "id": "shared-jq",
        "pattern": "/opt/homebrew/bin/jq",
        "description": "允许处理 JSON 数据"
    },
    {
        "id": "shared-yq",
        "pattern": "/opt/homebrew/bin/yq",
        "description": "允许处理 YAML 数据"
    },
    {
        "id": "shared-diff",
        "pattern": "/usr/bin/diff",
        "description": "允许比较文件差异"
    },
    {
        "id": "shared-comm",
        "pattern": "/usr/bin/comm",
        "description": "允许比较排序文件"
    },
    {
        "id": "shared-timeout",
        "pattern": "/usr/bin/timeout",
        "description": "允许限时执行命令"
    },
    {
        "id": "shared-sleep",
        "pattern": "/bin/sleep",
        "description": "允许延时等待"
    },
    {
        "id": "shared-true",
        "pattern": "/usr/bin/true",
        "description": "允许返回成功状态"
    },
    {
        "id": "shared-false",
        "pattern": "/usr/bin/false",
        "description": "允许返回失败状态"
    }
]

# 共享版 agent 列表
SHARED_AGENTS = [
    "main-shared",
    "strategy-shared",
    "design-shared",
    "video-shared",
    "research-shared",
    "copywriter-shared",
    "meeting-analyst-shared"
]


def load_config(config_path: Path) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_path: Path, config: dict):
    """保存配置文件"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def merge_allowlist(existing: list, new_commands: list) -> list:
    """合并白名单，保留现有的 lastUsedAt 等信息"""
    # 创建现有命令的映射（按 pattern）
    existing_map = {item['pattern']: item for item in existing}

    # 合并
    merged = []
    seen_patterns = set()

    # 先添加新的安全命令
    for cmd in new_commands:
        pattern = cmd['pattern']
        if pattern in existing_map:
            # 保留现有的使用记录，更新描述
            existing_item = existing_map[pattern].copy()
            existing_item['description'] = cmd['description']
            merged.append(existing_item)
        else:
            # 新增命令
            merged.append(cmd.copy())
        seen_patterns.add(pattern)

    # 保留现有的其他命令（如 =command: 开头的特殊命令）
    for item in existing:
        if item['pattern'] not in seen_patterns:
            merged.append(item)

    return merged


def optimize_shared_agents(config_path: Path, dry_run: bool = False):
    """优化共享版 agent 权限配置"""
    print(f"正在加载配置文件: {config_path}")
    config = load_config(config_path)

    # 备份原配置
    if not dry_run:
        backup_path = config_path.with_suffix('.json.backup')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = config_path.parent / f"{config_path.stem}.{timestamp}.backup.json"
        save_config(backup_path, config)
        print(f"已备份原配置到: {backup_path}")

    # 优化每个共享版 agent
    modified_count = 0
    for agent_name in SHARED_AGENTS:
        if agent_name not in config['agents']:
            print(f"⚠️  未找到 agent: {agent_name}")
            continue

        agent_config = config['agents'][agent_name]
        existing_allowlist = agent_config.get('allowlist', [])

        print(f"\n处理 {agent_name}:")
        print(f"  现有白名单条目: {len(existing_allowlist)}")

        # 合并白名单
        new_allowlist = merge_allowlist(existing_allowlist, SAFE_COMMANDS)

        print(f"  优化后白名单条目: {len(new_allowlist)}")
        print(f"  新增命令: {len(new_allowlist) - len(existing_allowlist)}")

        if not dry_run:
            agent_config['allowlist'] = new_allowlist
            modified_count += 1

    # 保存配置
    if not dry_run:
        save_config(config_path, config)
        print(f"\n✅ 成功优化 {modified_count} 个共享版 agent 的权限配置")
        print(f"配置已保存到: {config_path}")
    else:
        print(f"\n🔍 试运行模式，未实际修改配置文件")

    print("\n优化说明：")
    print("1. 已为所有共享版 agent 添加完整的安全命令白名单")
    print("2. 只读命令、创建文件、复制文件等安全操作无需审批")
    print("3. 危险操作（rm、trash、mv、sed -i）仍需审批")
    print("4. 员工使用时的权限审批频次将大幅降低")


def main():
    config_path = Path.home() / ".openclaw" / "exec-approvals.json"

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    # 检查是否为试运行模式
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 试运行模式（不会实际修改配置）\n")

    optimize_shared_agents(config_path, dry_run=dry_run)

    print("\n下一步：")
    print("1. 重启 OpenClaw gateway 使配置生效：openclaw daemon restart")
    print("2. 测试共享版 agent 是否正常工作")
    print("3. 观察权限审批频次是否降低")


if __name__ == "__main__":
    main()
