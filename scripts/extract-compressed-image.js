#!/usr/bin/env node

/**
 * 从会话记录中提取压缩后的图片，验证压缩质量
 */

const fs = require('fs');
const path = require('path');

if (process.argv.length < 3) {
  console.log('用法: node extract-compressed-image.js <session-file.jsonl>');
  console.log('');
  console.log('示例:');
  console.log('  node extract-compressed-image.js /Users/a123/.openclaw/agents/copywriter/sessions/xxx.jsonl');
  process.exit(1);
}

const sessionFile = process.argv[2];

if (!fs.existsSync(sessionFile)) {
  console.error(`❌ 会话文件不存在: ${sessionFile}`);
  process.exit(1);
}

console.log(`📖 读取会话文件: ${sessionFile}\n`);

const lines = fs.readFileSync(sessionFile, 'utf-8').split('\n').filter(l => l.trim());

let imageCount = 0;
const outputDir = '/Users/a123/.openclaw/tmp/extracted-images';

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

for (let i = 0; i < lines.length; i++) {
  try {
    const msg = JSON.parse(lines[i]);

    if (!msg.content || !Array.isArray(msg.content)) continue;

    for (const block of msg.content) {
      if (block.type === 'image' && block.data) {
        imageCount++;

        // 提取 base64 数据
        const base64Data = block.data.replace(/^data:image\/\w+;base64,/, '');
        const buffer = Buffer.from(base64Data, 'base64');

        const mimeType = block.mimeType || 'image/jpeg';
        const ext = mimeType.split('/')[1] || 'jpg';

        const outputPath = path.join(outputDir, `image_${imageCount}_line${i}.${ext}`);
        fs.writeFileSync(outputPath, buffer);

        console.log(`✅ 提取图片 ${imageCount}:`);
        console.log(`   行号: ${i}`);
        console.log(`   格式: ${mimeType}`);
        console.log(`   大小: ${(buffer.length / 1024).toFixed(2)} KB`);
        console.log(`   保存到: ${outputPath}`);

        // 如果是 JPEG，尝试获取质量信息
        if (ext === 'jpeg' || ext === 'jpg') {
          console.log(`   提示: 使用 'sips -g all "${outputPath}"' 查看详细信息`);
        }

        console.log('');
      }
    }
  } catch (e) {
    // 跳过解析错误
  }
}

if (imageCount === 0) {
  console.log('⚠️  未找到图片内容');
} else {
  console.log(`\n📊 总计提取 ${imageCount} 张图片`);
  console.log(`📁 输出目录: ${outputDir}`);
  console.log('');
  console.log('下一步：');
  console.log('  1. 打开提取的图片，人工检查压缩质量');
  console.log('  2. 对比原始图片，判断是否失真严重');
  console.log('  3. 如果失真明显，说明压缩参数过于激进');
}
