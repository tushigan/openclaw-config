#!/usr/bin/env node

/**
 * 诊断 Claude 模型图片对话问题
 *
 * 问题描述：
 * - 虾指挥 (main-shared): 使用 aixor-g/gpt-5.5 (openai-completions API)
 * - 文案策划专家 (copywriter): 使用 cc-vibe/claude-opus-4-6 (anthropic-messages API)
 * - 调研专家 (research): 使用 aixor-g/gpt-5.4 (openai-completions API)
 *
 * 用户报告：Claude 模型读取图片时会"乱回"，GPT 模型则正常
 */

const fs = require('fs');
const path = require('path');

console.log('=== OpenClaw 图片处理问题诊断工具 ===\n');

// 读取配置
const configPath = '/Users/a123/.openclaw/openclaw.json';
const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

// 需要检查的 agents
const agentsToCheck = [
  { id: 'main-shared', name: '虾指挥（共享版）' },
  { id: 'copywriter', name: '文案策划专家' },
  { id: 'research', name: '调研专家' }
];

console.log('1. Agent 模型配置检查：\n');

agentsToCheck.forEach(({ id, name }) => {
  const agent = config.agents.list.find(a => a.id === id);
  if (!agent) {
    console.log(`❌ ${name} (${id}): 未找到配置\n`);
    return;
  }

  const primaryModel = agent.model.primary;
  const [provider, modelId] = primaryModel.split('/');

  // 查找 provider 配置
  const providerConfig = config.models.providers[provider];

  console.log(`📋 ${name} (${id}):`);
  console.log(`   主模型: ${primaryModel}`);
  console.log(`   Provider: ${provider}`);
  console.log(`   API 类型: ${providerConfig?.api || '未知'}`);

  if (providerConfig) {
    const model = providerConfig.models.find(m => m.id === modelId);
    if (model) {
      console.log(`   支持输入: ${model.input.join(', ')}`);
      console.log(`   支持图片: ${model.input.includes('image') ? '✅' : '❌'}`);
    }
  }
  console.log('');
});

console.log('\n2. API 类型分析：\n');

console.log('anthropic-messages API:');
console.log('  - Anthropic 原生 Messages API');
console.log('  - 图片格式: base64 编码的 image content block');
console.log('  - 可能的问题: 图片压缩过度导致细节丢失\n');

console.log('openai-completions API:');
console.log('  - OpenAI Chat Completions API 格式');
console.log('  - 图片格式: image_url 或 base64');
console.log('  - 通常对图片质量要求更宽松\n');

console.log('\n3. 可能的问题原因：\n');

console.log('❌ 图片压缩过度');
console.log('   日志显示图片被压缩到 20-60KB (-89% ~ -94%)');
console.log('   Anthropic API 对图片质量敏感，过度压缩会导致识别不准确\n');

console.log('❌ API endpoint 差异');
console.log('   cc-vibe/aixor 可能对 anthropic-messages 请求格式有特殊处理\n');

console.log('❌ 图片尺寸限制');
console.log('   Anthropic API 图片限制: 最大 5MB, 推荐 < 200KB');
console.log('   当前压缩目标可能过于激进\n');

console.log('\n4. 建议的解决方案：\n');

console.log('方案 1: 调整图片压缩策略（推荐）');
console.log('  - 为 anthropic-messages API 提高压缩质量阈值');
console.log('  - 从当前 20-60KB 提升到 100-150KB');
console.log('  - 修改 OpenClaw 源码中的图片处理逻辑\n');

console.log('方案 2: 切换到 GPT 模型');
console.log('  - 文案策划专家: cc-vibe/claude-opus-4-6 → aixor-g/gpt-5.4');
console.log('  - 调研专家: 已经是 gpt-5.4，应该正常\n');

console.log('方案 3: 检查 provider API 实现');
console.log('  - 验证 cc-vibe 和 aixor 的 anthropic-messages 实现');
console.log('  - 可能存在图片预处理差异\n');

// 检查最近的会话日志
console.log('\n5. 最近会话检查：\n');

agentsToCheck.forEach(({ id, name }) => {
  const sessionsPath = `/Users/a123/.openclaw/agents/${id}/sessions/`;

  if (!fs.existsSync(sessionsPath)) {
    console.log(`⚠️  ${name}: 会话目录不存在`);
    return;
  }

  const files = fs.readdirSync(sessionsPath)
    .filter(f => f.endsWith('.jsonl'))
    .map(f => ({
      name: f,
      path: path.join(sessionsPath, f),
      mtime: fs.statSync(path.join(sessionsPath, f)).mtime
    }))
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, 1);

  if (files.length === 0) {
    console.log(`⚠️  ${name}: 无会话文件`);
    return;
  }

  const sessionFile = files[0];
  const lines = fs.readFileSync(sessionFile.path, 'utf-8').split('\n').filter(l => l.trim());

  let imageCount = 0;
  lines.forEach(line => {
    try {
      const msg = JSON.parse(line);
      if (msg.content && Array.isArray(msg.content)) {
        const images = msg.content.filter(c => c.type === 'image');
        imageCount += images.length;
      }
    } catch (e) {
      // 跳过解析错误
    }
  });

  console.log(`📊 ${name}:`);
  console.log(`   最近会话: ${sessionFile.name}`);
  console.log(`   更新时间: ${sessionFile.mtime.toLocaleString('zh-CN')}`);
  console.log(`   图片消息数: ${imageCount}`);
  console.log('');
});

console.log('\n6. 下一步行动：\n');
console.log('□ 收集用户反馈：具体是什么"乱回"（答非所问/识别错误/内容混乱）');
console.log('□ 对比测试：同一张图片分别用 Claude 和 GPT 模型处理');
console.log('□ 检查压缩质量：提取压缩后的图片人工查看是否失真');
console.log('□ 修改压缩参数：临时提高 anthropic-messages 的图片质量阈值');
console.log('□ 联系 provider：向 cc-vibe/aixor 反馈图片识别问题');

console.log('\n=== 诊断完成 ===\n');
