#!/usr/bin/env python3
"""
generate_image_lconai.py — 薄壳转发层 (delegation shim)

brand-poster-creator 是完整的品牌海报 workflow（Phase 1-4 / brief / 素材 / 版式蒸馏 / 执行蓝图 / 生图）。
真正的「发 API、拿图」原子能力已经统一抽到 gpt-image2-gen 技能里。
这个脚本不再自己调 API，只是把老签名（-p/-f/--ref/--ref-logo/--ref-extra/--resolution 1K|2K|4K/
--aspect-ratio/-m）翻译成新 generate.py 的签名并 exec 过去。

这样带来的好处：
- brand-poster-creator 这条 workflow 不用作废
- 所有 bug 修复、蒸馏卡自动挂载、参考图角色标注…都从 gpt-image2-gen 拿到
- 老 agent 用老参数调用也能跑通，逐步迁移

不再支持的路径（已明确报错，避免静默走坏分支）：
- Midjourney 相关: chat_fast_imagine / chat_relax_imagine / mj_upscale / --task-id / --position / --mask
- Gemini / doubao / 其它非 gpt-image 系列的模型
如果你真的需要 MJ/Gemini，请走它们自己的技能或回退到 git 历史里的旧版。
"""
from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path

SKILLS_ROOT = Path('/Users/a123/.openclaw/workspace-design/skills')
TARGET_SCRIPT = SKILLS_ROOT / 'gpt-image2-gen' / 'scripts' / 'generate.py'

# 智创聚合 API 的 /v1/images/edits 文档说支持三种 size 写法：
#   1. 档位形式: 1K / 2K / 4K（原样返回）
#   2. 像素形式: 1280~4096 per side，用 x 或 *
#   3. 比例形式: 1:1/4:3/3:4/16:9/9:16/3:2/2:3（自动映射到 2K 级推荐像素）
# 经过真机验证: gpt-image-2-pro 正确响应比例形式，返回的尺寸就是对的比例。
# 所以这里不再做任何下采样/降级映射，能透传就透传，让下游 generate.py
# 的 normalize_size 做统一处理。

# 老参数只做「建议档位」→ 新参数的轻量翻译，不再重写内容
LEGACY_RESOLUTION_PASSTHROUGH = {'1K', '2K', '4K'}


def die(msg: str, code: int = 2):
    sys.stderr.write(f'[brand-poster-creator shim] {msg}\n')
    sys.exit(code)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description='brand-poster-creator image-gen shim → forwards to gpt-image2-gen',
    )
    p.add_argument('--prompt', '-p', help='Image prompt')
    p.add_argument('--filename', '-f', required=True, help='Output file path')
    p.add_argument('--reference-image', '--ref', dest='reference_image',
                   help='单张原始参考图 (图一)')
    p.add_argument('--ref-logo', dest='ref_logo', help='品牌 LOGO 参考图')
    p.add_argument('--ref-extra', dest='ref_extra',
                   help='更多参考图，逗号分隔路径（图三、图四…）')
    p.add_argument('--model', '-m', default=None, help='Model name（仅允许 gpt-image 系列）')
    p.add_argument('--resolution', '-r', default=None,
                   help='老的分辨率档位(1K/2K/4K)，透传给下游 generate.py')
    p.add_argument('--aspect-ratio', '-a', dest='aspect_ratio', default=None,
                   help='比例形式 size，推荐用: 1:1/4:3/3:4/16:9/9:16/3:2/2:3，'
                        '透传给下游，网关会自动映射到 2K 级像素')
    p.add_argument('--size', '-s', default=None,
                   help='直接指定 size（优先级最高），支持比例/像素/档位三种写法')
    p.add_argument('--distill-id', dest='distill_id',
                   help='新增：挂载 brand-poster-distiller 的蒸馏卡（骨架图 + 版式约束）')
    p.add_argument('--no-auto-skeleton', action='store_true',
                   help='蒸馏卡模式下不自动挂骨架图')
    p.add_argument('--api-key', '-k', dest='api_key', help='API key 覆盖（通过环境变量传给子进程）')
    p.add_argument('--base-url', '-u', dest='base_url', help='Base URL 覆盖（通过环境变量传给子进程）')

    for arg in ('--mask', '--task-id', '--position'):
        p.add_argument(arg, help=argparse.SUPPRESS)

    return p


def resolve_size(args) -> str:
    """优先级: --size > --aspect-ratio > --resolution > 默认 1:1。

    不再做降级映射；下游 gpt-image2-gen/generate.py 的 normalize_size
    会把比例/像素/档位统一处理，然后透传给网关。
    """
    if args.size:
        return args.size
    if args.aspect_ratio:
        return args.aspect_ratio
    if args.resolution:
        return args.resolution
    return '1:1'


def reject_unsupported(args):
    if args.mask or args.task_id or args.position is not None:
        die('本 shim 不再支持 Midjourney 的 mj_upscale / mj_inpaint / --task-id / --position / --mask。'
            '如需用 MJ 探索调性，请直接走 Midjourney 自己的工具链。')
    if args.model:
        m = args.model.lower()
        if not (m.startswith('gpt-image') or m == 'gpt-image-2-pro'):
            die(f'本 shim 只支持 gpt-image 系列模型，收到 model={args.model}。'
                '如需 Gemini/Banana Pro/Doubao，请对接对应技能或等后续扩展。')


def build_target_cmd(args) -> list[str]:
    if not TARGET_SCRIPT.exists():
        die(f'target generator not found: {TARGET_SCRIPT}')

    cmd: list[str] = ['python3', str(TARGET_SCRIPT)]

    if args.prompt:
        cmd += ['--prompt', args.prompt]
    cmd += ['-o', args.filename]
    cmd += ['-s', resolve_size(args)]

    if args.model:
        cmd += ['-m', args.model]

    if args.reference_image:
        cmd += ['-r', args.reference_image]
    if args.ref_logo:
        cmd += ['--ref-logo', args.ref_logo]
    if args.ref_extra:
        for p in [x.strip() for x in args.ref_extra.split(',') if x.strip()]:
            cmd += ['-r', p]

    if args.distill_id:
        cmd += ['--distill-id', args.distill_id]
    if args.no_auto_skeleton:
        cmd.append('--no-auto-skeleton')

    return cmd


def build_env(args) -> dict:
    env = os.environ.copy()
    if args.api_key:
        env['BANANA_API_KEY'] = args.api_key
    if args.base_url:
        env['BANANA_API_URL'] = args.base_url
    return env


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    reject_unsupported(args)
    cmd = build_target_cmd(args)
    print('[shim] forwarding →', ' '.join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, env=build_env(args))
    return proc.returncode


if __name__ == '__main__':
    sys.exit(main())
