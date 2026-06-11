/**
 * build_psd.mjs
 * ─────────────────────────────────────────────────────
 * 将多个 PNG 图层文件按 scene.json 描述组装为一个 PSD 文件。
 *
 * 用法:
 *   node build_psd.mjs --scene scene.json --output output.psd
 *
 * 依赖: ag-psd, pngjs（脚本启动时自动检测并安装）
 */

import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { parseArgs } from "node:util";

// ──────────────────────────────────────────────
// 0. 自动安装缺失依赖
// ──────────────────────────────────────────────

function ensureDeps() {
  const required = ["ag-psd", "pngjs"];
  const missing = required.filter((pkg) => {
    try {
      // 尝试 resolve，找不到说明未安装
      import.meta.resolve(pkg);
      return false;
    } catch {
      return true;
    }
  });

  if (missing.length === 0) return;

  console.log(`[build_psd] 正在安装缺失依赖: ${missing.join(", ")} ...`);
  try {
    execSync(`npm install ${missing.join(" ")} --no-save`, {
      stdio: "inherit",
      cwd: path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")),
    });
  } catch (err) {
    console.error("[build_psd] 依赖安装失败，请手动执行:");
    console.error(`  npm install ${missing.join(" ")} --no-save`);
    process.exit(1);
  }
}

ensureDeps();

// 依赖安装后再 import，避免静态 import 在缺失时直接崩溃
const { default: agPsd } = await import("ag-psd");
const { writePsd: writePsdBuffer } = agPsd;
const { PNG } = await import("pngjs");

// ──────────────────────────────────────────────
// 1. 解析命令行参数
// ──────────────────────────────────────────────

const { values: args } = parseArgs({
  options: {
    scene: { type: "string" },
    output: { type: "string" },
  },
  strict: true,
});

if (!args.scene || !args.output) {
  console.error("用法: node build_psd.mjs --scene <scene.json> --output <output.psd>");
  process.exit(1);
}

const scenePath = path.resolve(args.scene);
const outputPath = path.resolve(args.output);

if (!fs.existsSync(scenePath)) {
  console.error(`[build_psd] scene.json 不存在: ${scenePath}`);
  process.exit(1);
}

// ──────────────────────────────────────────────
// 2. 读取 scene.json
// ──────────────────────────────────────────────

const sceneDir = path.dirname(scenePath);
const scene = JSON.parse(fs.readFileSync(scenePath, "utf-8"));

const { width, height, preview_path, group_order, image_layers } = scene;

if (!width || !height || !Array.isArray(image_layers)) {
  console.error("[build_psd] scene.json 缺少必要字段 (width / height / image_layers)");
  process.exit(1);
}

console.log(`[build_psd] 画布尺寸: ${width}×${height}，共 ${image_layers.length} 个图层`);

// ──────────────────────────────────────────────
// 3. 辅助函数
// ──────────────────────────────────────────────

/**
 * 扫描 RGBA 像素数据，找到所有 alpha > 0 的像素的最小包围盒。
 * @param {Uint8Array | Uint8ClampedArray | Buffer} data  RGBA 像素数据
 * @param {number} width   图像宽度
 * @param {number} height  图像高度
 * @returns {{ top: number, left: number, bottom: number, right: number } | null}
 *          返回 null 表示图层完全透明
 */
function alphaBounds(data, width, height) {
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4 + 3; // alpha 通道偏移
      if (data[idx] > 0) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }

  if (maxX < 0) return null; // 完全透明

  return { top: minY, left: minX, bottom: maxY + 1, right: maxX + 1 };
}

/**
 * 从完整像素数据中裁切出指定边界框区域。
 * @param {Uint8Array | Uint8ClampedArray | Buffer} data  原始 RGBA 数据
 * @param {number} width   原始宽度
 * @param {number} _height 原始高度（未使用，保留签名一致性）
 * @param {{ top: number, left: number, bottom: number, right: number }} bounds
 * @returns {Uint8ClampedArray} 裁切后的 RGBA 数据
 */
function cropImageData(data, width, _height, bounds) {
  const cropW = bounds.right - bounds.left;
  const cropH = bounds.bottom - bounds.top;
  const out = new Uint8ClampedArray(cropW * cropH * 4);

  for (let y = 0; y < cropH; y++) {
    const srcOffset = ((bounds.top + y) * width + bounds.left) * 4;
    const dstOffset = y * cropW * 4;
    out.set(data.subarray(srcOffset, srcOffset + cropW * 4), dstOffset);
  }

  return out;
}

/**
 * 读取 PNG 文件并返回 { data, width, height }。
 * @param {string} filePath PNG 文件绝对路径
 */
function loadPng(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`PNG 文件不存在: ${filePath}`);
  }
  const buf = fs.readFileSync(filePath);
  const png = PNG.sync.read(buf);
  return {
    data: new Uint8ClampedArray(png.data.buffer, png.data.byteOffset, png.data.byteLength),
    width: png.width,
    height: png.height,
  };
}

// ──────────────────────────────────────────────
// 4. 加载所有图层并构建 PSD 结构
// ──────────────────────────────────────────────

/**
 * 把单个 image_layer 描述转为 ag-psd 的 Layer 对象。
 */
function buildLayer(layerDef) {
  const absPath = path.resolve(sceneDir, layerDef.path);
  console.log(`  ├─ 加载图层: ${layerDef.name} (${path.basename(absPath)})`);

  const { data, width: imgW, height: imgH } = loadPng(absPath);

  let finalData = data;
  let left = layerDef.left ?? 0;
  let top = layerDef.top ?? 0;
  let right = left + imgW;
  let bottom = top + imgH;

  // Alpha 裁切优化：去除完全透明的边距
  if (layerDef.crop_to_alpha) {
    const bounds = alphaBounds(data, imgW, imgH);
    if (bounds === null) {
      // 图层完全透明，仍然保留一个 1×1 的占位
      console.log(`  │  └─ [alpha裁切] 图层完全透明，保留占位`);
      finalData = new Uint8ClampedArray(4); // 1×1 透明像素
      right = left + 1;
      bottom = top + 1;
    } else {
      const cropW = bounds.right - bounds.left;
      const cropH = bounds.bottom - bounds.top;
      const saved = ((imgW * imgH) - (cropW * cropH)) * 4;
      if (saved > 0) {
        console.log(`  │  └─ [alpha裁切] ${imgW}×${imgH} → ${cropW}×${cropH}，节省 ${(saved / 1024).toFixed(0)} KB`);
        finalData = cropImageData(data, imgW, imgH, bounds);
        // 坐标偏移需要加上裁切区域在原图中的位置
        left += bounds.left;
        top += bounds.top;
        right = left + cropW;
        bottom = top + cropH;
      }
    }
  }

  return {
    name: layerDef.name,
    left,
    top,
    right,
    bottom,
    opacity: layerDef.opacity != null ? layerDef.opacity / 255 : 1,
    hidden: !!layerDef.hidden,
    imageData: {
      width: right - left,
      height: bottom - top,
      data: finalData,
    },
  };
}

// 按 group 分组
const groupMap = new Map();
for (const layer of image_layers) {
  const groupName = layer.group || "__ungrouped__";
  if (!groupMap.has(groupName)) {
    groupMap.set(groupName, []);
  }
  groupMap.get(groupName).push(layer);
}

// 确定分组顺序
const orderedGroups = Array.isArray(group_order) && group_order.length > 0
  ? group_order
  : [...groupMap.keys()];

console.log(`[build_psd] 分组: ${orderedGroups.join(", ")}`);

// 构建 PSD children（每个 group 是一个文件夹）
const psdChildren = [];

for (const groupName of orderedGroups) {
  const layerDefs = groupMap.get(groupName);
  if (!layerDefs || layerDefs.length === 0) {
    console.log(`  ├─ 跳过空分组: ${groupName}`);
    continue;
  }

  console.log(`  ├─ 分组 [${groupName}] (${layerDefs.length} 图层)`);

  const children = layerDefs.map((def) => buildLayer(def));

  psdChildren.push({
    name: groupName,
    opened: true, // 在 Photoshop 中默认展开
    children,
  });
}

// ──────────────────────────────────────────────
// 5. 构建 PSD 文档对象
// ──────────────────────────────────────────────

const psd = {
  width,
  height,
  children: psdChildren,
};

// 如果提供了预览图，加载为 PSD 的合并图层 (imageData)
if (preview_path) {
  const previewAbsPath = path.resolve(sceneDir, preview_path);
  if (fs.existsSync(previewAbsPath)) {
    console.log(`[build_psd] 加载预览图: ${path.basename(previewAbsPath)}`);
    const { data, width: pw, height: ph } = loadPng(previewAbsPath);
    psd.imageData = { width: pw, height: ph, data };
  } else {
    console.warn(`[build_psd] 预览图不存在，跳过: ${previewAbsPath}`);
  }
}

// ──────────────────────────────────────────────
// 6. 写入 PSD 文件
// ──────────────────────────────────────────────

console.log("[build_psd] 正在写入 PSD ...");

const buffer = writePsdBuffer(psd, {
  noBackground: true,
  invalidateTextLayers: false,
});

// 确保输出目录存在
const outputDir = path.dirname(outputPath);
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

fs.writeFileSync(outputPath, Buffer.from(buffer));

const sizeKB = (fs.statSync(outputPath).size / 1024).toFixed(1);
console.log(`[build_psd] ✅ PSD 已生成: ${outputPath} (${sizeKB} KB)`);
