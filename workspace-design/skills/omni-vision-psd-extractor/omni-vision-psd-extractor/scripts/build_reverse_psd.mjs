import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 动态依赖检测与自愈
async function loadDependency(moduleName) {
  try {
    return await import(moduleName);
  } catch (err) {
    console.warn(`[自愈] 缺失必要依赖模块: ${moduleName}，正在静默安装...`);
    try {
      execSync('npm install pngjs ag-psd --no-save --no-audit --no-fund', { cwd: __dirname, stdio: 'inherit' });
      return await import(moduleName);
    } catch (installErr) {
      console.error(`[自愈:错误] 依赖模块 ${moduleName} 自动安装失败:`, installErr);
      throw installErr;
    }
  }
}

const { PNG } = await loadDependency('pngjs');
const { writePsdBuffer } = await loadDependency('ag-psd');


function parseArgs(argv) {
  const args = { scene: '', output: '' };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--scene') {
      args.scene = argv[i + 1] || '';
      i += 1;
    } else if (token === '--output') {
      args.output = argv[i + 1] || '';
      i += 1;
    }
  }
  return args;
}

function loadPngImageData(path) {
  const png = PNG.sync.read(readFileSync(path));
  return {
    width: png.width,
    height: png.height,
    data: new Uint8ClampedArray(png.data),
  };
}

function alphaBounds(image) {
  let minX = image.width;
  let minY = image.height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < image.height; y += 1) {
    for (let x = 0; x < image.width; x += 1) {
      const alpha = image.data[(y * image.width + x) * 4 + 3];
      if (alpha === 0) continue;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    }
  }

  if (maxX < minX || maxY < minY) {
    return null;
  }

  return {
    left: minX,
    top: minY,
    right: maxX + 1,
    bottom: maxY + 1,
  };
}

function cropImageData(image, bounds) {
  const width = bounds.right - bounds.left;
  const height = bounds.bottom - bounds.top;
  const data = new Uint8ClampedArray(width * height * 4);

  for (let y = 0; y < height; y += 1) {
    const srcStart = ((bounds.top + y) * image.width + bounds.left) * 4;
    const dstStart = y * width * 4;
    data.set(image.data.slice(srcStart, srcStart + width * 4), dstStart);
  }

  return { width, height, data };
}

function layerFromImageSpec(spec) {
  const image = loadPngImageData(spec.path);
  let pixelData = image;
  let left = spec.left ?? 0;
  let top = spec.top ?? 0;

  if (spec.crop_to_alpha) {
    const bounds = alphaBounds(image);
    if (bounds) {
      pixelData = cropImageData(image, bounds);
      left += bounds.left;
      top += bounds.top;
    }
  }

  return {
    name: spec.name,
    top,
    left,
    bottom: top + pixelData.height,
    right: left + pixelData.width,
    opacity: spec.opacity ?? 255,
    hidden: spec.hidden ?? false,
    imageData: pixelData,
  };
}

function layerFromTextSpec(spec) {
  return {
    name: spec.name,
    text: {
      text: spec.text,
      style: {
        fontName: spec.fontName || 'ArialMT',
        fontSize: spec.fontSize || 36,
        fillColor: spec.fillColor || { r: 0, g: 0, b: 0, a: 255 },
      }
    },
    top: spec.top ?? 0,
    left: spec.left ?? 0,
    bottom: (spec.top ?? 0) + (spec.height ?? 100),
    right: (spec.left ?? 0) + (spec.width ?? 300),
    opacity: spec.opacity ?? 255,
    hidden: spec.hidden ?? false,
  };
}

function buildPsd(scene) {
  const groupOrder = scene.group_order;
  const grouped = new Map();
  for (const group of groupOrder) grouped.set(group, []);

  for (const spec of scene.image_layers || []) {
    grouped.get(spec.group).push(layerFromImageSpec(spec));
  }

  // Hydrate true text layers
  for (const spec of scene.text_layers || []) {
    grouped.get(spec.group).push(layerFromTextSpec(spec));
  }

  const preview = loadPngImageData(scene.preview_path);

  return {
    width: preview.width,
    height: preview.height,
    imageData: preview,
    children: groupOrder.map((group) => ({
      name: group,
      opened: true,
      hidden: false,
      children: grouped.get(group),
    })),
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.scene) throw new Error('Missing --scene path');
  if (!args.output) throw new Error('Missing --output path');

  const scene = JSON.parse(readFileSync(resolve(args.scene), 'utf-8'));
  const outputPath = resolve(args.output);
  mkdirSync(dirname(outputPath), { recursive: true });

  const psd = buildPsd(scene);
  const buffer = writePsdBuffer(psd, { noBackground: true, invalidateTextLayers: false });
  writeFileSync(outputPath, buffer);
  console.log(`PSD written to ${outputPath}`);
}

main();
