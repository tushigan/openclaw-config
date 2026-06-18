#!/usr/bin/env node

/**
 * 分析 OpenClaw 图片压缩逻辑
 * 验证 anthropic-messages 和 openai-completions 是否使用相同的压缩策略
 */

const fs = require('fs');
const path = require('path');

console.log('=== OpenClaw 图片压缩策略分析 ===\n');

console.log('📋 源码分析结果：\n');

console.log('1. 压缩参数（所有 API 统一）：');
console.log('   - DEFAULT_IMAGE_MAX_DIMENSION_PX = 1200px');
console.log('   - DEFAULT_IMAGE_MAX_BYTES = 5MB (5 * 1024 * 1024)');
console.log('   - 可通过 openclaw.json 中 agents.defaults.imageMaxDimensionPx 配置\n');

console.log('2. 压缩策略（所有 API 统一）：');
console.log('   - 函数: sanitizeContentBlocksImages()');
console.log('   - 调用位置: embedded-agent-helpers.js');
console.log('   - 对所有 role=user 和 role=toolResult 的图片内容统一处理');
console.log('   - 没有针对不同 API (anthropic-messages vs openai-completions) 的差异化逻辑\n');

console.log('3. 压缩算法：');
console.log('   - 使用 sharp 库进行 JPEG 压缩');
console.log('   - 质量级别：从 85 递减到 10，逐步尝试');
console.log('   - 尺寸缩放：如果超过 maxDimensionPx，按比例缩小');
console.log('   - 目标：压缩到 < maxBytes (5MB) 为止\n');

console.log('❌ 结论：OpenClaw 源码中不存在针对不同 API 的差异化压缩策略\n');

console.log('=== 重新评估问题原因 ===\n');

console.log('既然压缩策略相同，为什么 Claude 模型会"乱回"？\n');

console.log('可能原因 1: Provider 端的二次处理');
console.log('  - cc-vibe/aixor 等中转服务可能对图片做了二次压缩');
console.log('  - Anthropic 官方 API 对图片质量要求高，中转服务压缩可能导致失真\n');

console.log('可能原因 2: 图片格式转换问题');
console.log('  - anthropic-messages 使用 base64 + image content block');
console.log('  - openai-completions 使用 image_url 或 base64');
console.log('  - 不同格式在中转服务的处理逻辑可能不同\n');

console.log('可能原因 3: 上下文截断');
console.log('  - Claude 模型的 context window 管理策略可能不同');
console.log('  - 图片 base64 占用大量 tokens，可能被提前截断\n');

console.log('可能原因 4: 模型本身的差异');
console.log('  - Claude Opus 4.6 vs GPT-5.4 在视觉理解能力上的差异');
console.log('  - 不是压缩问题，而是模型对低质量图片的容错性不同\n');

console.log('=== 验证方案 ===\n');

console.log('□ 方案 A: 对比原始图片 vs 压缩后图片');
console.log('  1. 提取一张被"乱回"的图片的原始版本');
console.log('  2. 查看压缩后的版本（从会话记录中提取 base64）');
console.log('  3. 人工对比质量，判断是否失真严重\n');

console.log('□ 方案 B: 同一张图片测试两个模型');
console.log('  1. 准备一张测试图片（包含明确文字或细节）');
console.log('  2. 分别发给 copywriter (Claude) 和 research (GPT)');
console.log('  3. 对比回答质量，确认是否存在识别差异\n');

console.log('□ 方案 C: 测试不同 provider');
console.log('  1. 将 copywriter 的 Claude 从 cc-vibe 切换到 aixor');
console.log('  2. 测试是否仍然"乱回"');
console.log('  3. 判断是否是 cc-vibe 特定问题\n');

console.log('□ 方案 D: 检查实际的 API 请求');
console.log('  1. 开启 gateway 的详细日志');
console.log('  2. 抓取发送给 cc-vibe 和 aixor-g 的实际 payload');
console.log('  3. 对比图片的 base64 大小和格式\n');

console.log('=== 建议的下一步 ===\n');

console.log('推荐先执行 方案 B：同图测试');
console.log('  - 最直接，能快速验证是否真的存在差异');
console.log('  - 如果两个模型对同一张图片的回答都正确，说明不是压缩问题');
console.log('  - 如果 Claude 确实识别错误，再进一步排查原因\n');

console.log('需要用户提供：');
console.log('  1. 具体哪张图片被"乱回"了');
console.log('  2. "乱回"的具体表现（答非所问/识别错误/内容混乱）');
console.log('  3. 期望的正确回答是什么\n');

console.log('=== 分析完成 ===');
