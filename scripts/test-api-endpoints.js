#!/usr/bin/env node

/**
 * API 端点性能测试脚本
 * 测试多个端点的响应速度和稳定性
 */

const https = require('https');

// 测试配置
const ENDPOINTS = [
  { name: 's.lconai.com', url: 'https://s.lconai.com/v1/chat/completions' },
  { name: 'n.lconai.com', url: 'https://n.lconai.com/v1/chat/completions' },
  { name: 'cdn1.openaicn.com', url: 'https://cdn1.openaicn.com/v1/chat/completions' }
];

const TEST_ROUNDS = 10; // 测试轮数
const TIMEOUT = 10000; // 超时时间（毫秒）

// 从环境变量或命令行参数获取 API Key
const API_KEY = process.env.LCONAI_API_KEY || process.argv[2];

if (!API_KEY) {
  console.error('❌ 错误：需要提供 API Key');
  console.error('使用方式：');
  console.error('  LCONAI_API_KEY=your_key node test-api-endpoints.js');
  console.error('  或者：node test-api-endpoints.js your_key');
  process.exit(1);
}

// 测试请求体（使用较小的模型和简短的提示以加快测试）
const TEST_PAYLOAD = {
  model: 'gpt-4o-mini',
  messages: [
    { role: 'user', content: 'Say "ok" in one word.' }
  ],
  max_tokens: 10
};

/**
 * 发送单次测试请求
 */
function testEndpoint(endpoint) {
  return new Promise((resolve) => {
    const startTime = Date.now();
    const url = new URL(endpoint.url);

    const postData = JSON.stringify(TEST_PAYLOAD);

    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Length': Buffer.byteLength(postData)
      },
      timeout: TIMEOUT
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        const duration = Date.now() - startTime;

        if (res.statusCode === 200) {
          resolve({
            success: true,
            duration,
            statusCode: res.statusCode
          });
        } else {
          resolve({
            success: false,
            duration,
            statusCode: res.statusCode,
            error: `HTTP ${res.statusCode}`
          });
        }
      });
    });

    req.on('error', (err) => {
      const duration = Date.now() - startTime;
      resolve({
        success: false,
        duration,
        error: err.message
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        success: false,
        duration: TIMEOUT,
        error: 'Timeout'
      });
    });

    req.write(postData);
    req.end();
  });
}

/**
 * 运行完整测试套件
 */
async function runTests() {
  console.log('🧪 开始 API 端点性能测试\n');
  console.log(`📊 测试配置：`);
  console.log(`   - 测试轮数：${TEST_ROUNDS}`);
  console.log(`   - 超时时间：${TIMEOUT}ms`);
  console.log(`   - 测试端点数：${ENDPOINTS.length}\n`);

  const results = {};

  // 初始化结果统计
  for (const endpoint of ENDPOINTS) {
    results[endpoint.name] = {
      durations: [],
      successes: 0,
      failures: 0,
      errors: []
    };
  }

  // 执行测试
  for (let round = 1; round <= TEST_ROUNDS; round++) {
    console.log(`\n🔄 第 ${round}/${TEST_ROUNDS} 轮测试：`);

    for (const endpoint of ENDPOINTS) {
      process.stdout.write(`   ${endpoint.name} ... `);

      const result = await testEndpoint(endpoint);
      const stats = results[endpoint.name];

      if (result.success) {
        stats.successes++;
        stats.durations.push(result.duration);
        console.log(`✅ ${result.duration}ms`);
      } else {
        stats.failures++;
        stats.errors.push(result.error);
        console.log(`❌ ${result.error} (${result.duration}ms)`);
      }

      // 请求之间稍微延迟，避免触发限流
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }

  // 计算和显示统计结果
  console.log('\n\n' + '='.repeat(70));
  console.log('📈 测试结果统计\n');

  const summary = [];

  for (const endpoint of ENDPOINTS) {
    const stats = results[endpoint.name];
    const successRate = (stats.successes / TEST_ROUNDS * 100).toFixed(1);

    let avgDuration = 0;
    let minDuration = 0;
    let maxDuration = 0;
    let p95Duration = 0;

    if (stats.durations.length > 0) {
      avgDuration = Math.round(stats.durations.reduce((a, b) => a + b, 0) / stats.durations.length);
      minDuration = Math.min(...stats.durations);
      maxDuration = Math.max(...stats.durations);

      const sorted = [...stats.durations].sort((a, b) => a - b);
      const p95Index = Math.floor(sorted.length * 0.95);
      p95Duration = sorted[p95Index] || sorted[sorted.length - 1];
    }

    summary.push({
      name: endpoint.name,
      successRate: parseFloat(successRate),
      avgDuration,
      minDuration,
      maxDuration,
      p95Duration,
      successes: stats.successes,
      failures: stats.failures
    });

    console.log(`🔸 ${endpoint.name}`);
    console.log(`   成功率：${successRate}% (${stats.successes}/${TEST_ROUNDS})`);

    if (stats.durations.length > 0) {
      console.log(`   平均响应：${avgDuration}ms`);
      console.log(`   最快响应：${minDuration}ms`);
      console.log(`   最慢响应：${maxDuration}ms`);
      console.log(`   P95 响应：${p95Duration}ms`);
    }

    if (stats.failures > 0) {
      const errorCounts = {};
      stats.errors.forEach(err => {
        errorCounts[err] = (errorCounts[err] || 0) + 1;
      });
      console.log(`   失败原因：`);
      for (const [err, count] of Object.entries(errorCounts)) {
        console.log(`      - ${err}: ${count}次`);
      }
    }
    console.log('');
  }

  // 排序和推荐
  console.log('='.repeat(70));
  console.log('🏆 综合评分排名\n');

  // 计算综合得分（成功率权重 60%，速度权重 40%）
  summary.forEach(s => {
    const successScore = s.successRate;
    const speedScore = s.avgDuration > 0 ? Math.max(0, 100 - s.avgDuration / 50) : 0;
    s.totalScore = successScore * 0.6 + speedScore * 0.4;
  });

  summary.sort((a, b) => b.totalScore - a.totalScore);

  summary.forEach((s, index) => {
    const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉';
    console.log(`${medal} 第 ${index + 1} 名：${s.name}`);
    console.log(`   综合得分：${s.totalScore.toFixed(1)}/100`);
    console.log(`   成功率：${s.successRate}%`);
    console.log(`   平均响应：${s.avgDuration}ms`);
    console.log('');
  });

  console.log('='.repeat(70));
  console.log('💡 推荐建议\n');

  const best = summary[0];
  console.log(`推荐使用：${best.name}`);
  console.log(`理由：`);

  if (best.successRate === 100) {
    console.log(`  ✓ 稳定性极佳（成功率 100%）`);
  } else if (best.successRate >= 90) {
    console.log(`  ✓ 稳定性良好（成功率 ${best.successRate}%）`);
  }

  if (best.avgDuration < 1000) {
    console.log(`  ✓ 响应速度快（平均 ${best.avgDuration}ms）`);
  } else if (best.avgDuration < 2000) {
    console.log(`  ✓ 响应速度中等（平均 ${best.avgDuration}ms）`);
  }

  console.log('');
}

// 运行测试
runTests().catch(err => {
  console.error('❌ 测试过程出错：', err);
  process.exit(1);
});
