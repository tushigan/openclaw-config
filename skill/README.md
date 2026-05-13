# OpenClaw 技能包交付说明

本包包含 2 个相关项目和技能，用于品牌海报版式蒸馏和电商详情页的生成。

---

## 📦 包含内容

| 项目 | 路径 | 说明 |
|------|------|------|
| **xiangqingye-desigen** | `xiangqingye-desigen/` | 电商详情页设计技能（3 阶段紧凑流程） |
| **brand-poster-distiller** | `brand-poster-distiller/` | 品牌海报版式蒸馏库（v3.2）含 Web 管理界面 |

---

## 🎨 1. xiangqingye-desigen - 电商详情页设计

### 功能
从 0 开始规划电商详情页工作流，采用 **3 阶段紧凑流程**：
- 阶段 1：策略（载体 + 产品事实 + 分段方案 + 风格指南）
- 阶段 2：手稿（所有段黑白手稿一次性产出）
- 阶段 3：成稿（最终设计稿 + 封闭边界硬拼接）

### 特点
- 单张方形画板 2880x2880，4 列纵向排列展示全部屏
- 全局风格指南确保风格统一
- 项目化文件管理避免混乱
- 重点服务食品/烘焙/快消品

### 触发词
详情页、详情页手稿、电商长图、移动端详情页、PC详情页、详情页策划、详情页生成、详情页拼接

### 核心文件
```
xiangqingye-desigen/
├── SKILL.md              # 技能完整文档
└── scripts/              # 脚本目录
```

---

## 🔬 2. brand-poster-distiller - 品牌海报版式蒸馏库（v3.2）

### 功能
把参考海报蒸馏为可复用的版式结构（骨架图+坐标表），并配套本地蒸馏库网页进行查看、搜索、筛选、编辑与按 ID 调用。

### 工作流
1. 用户提供参考海报图片
2. 创建新的蒸馏卡（v3.2 精简格式），包含 id / title / source_images
3. 运行 `layout_analyzer.py` 对海报进行 AI 版式分析，生成骨架图和元素坐标表
4. 用户可在网页端通过拖拽画布或编辑表格微调坐标
5. 保存后本地卡片即为最终版式锁定数据

### Web 管理界面
- **启动命令**：
  ```bash
  cd brand-poster-distiller
  python3 scripts/admin_server.py
  ```
- **本地访问**：`http://127.0.0.1:8766/site/index.html`
- **远程访问**（通过 frp）：`http://39.108.54.123:20000/site/index.html`

### 数据存储
- 所有数据存储在本地 Mac 上
- 通过 frp 内网穿透实现远程访问
- 不需要上传到云端

### 核心文件
```
brand-poster-distiller/
├── SKILL.md              # 技能完整文档
├── cards/                # 蒸馏卡 JSON 文件
├── data/                 # 原始图片和数据
├── scripts/
│   ├── admin_server.py    # Web 服务器
│   └── layout_analyzer.py  # 版式分析脚本
└── site/
    ├── index.html         # Web 管理界面
    └── assets/           # 静态资源
```

---

## 🔄 两者协作关系

```
用户参考海报
    ↓
[brand-poster-distiller]
    ↓ 生成蒸馏卡（骨架图 + 坐标表）
    ↓
输出版式数据供外部调用

用户需求（产品 + 平台）
    ↓
[xiangqingye-desigen]
    ↓ 3 阶段流程（策略 → 手稿 → 成稿）
    ↓ 生成电商详情页
```

---

## 📋 使用前提

### 必需环境
- Python 3.x
- OpenClaw 框架已安装

### 可选配置
如需调用生图模型，需要配置：
```bash
# 智创聚合 API
export BANANA_API_URL="https://n.lconai.com"
export BANANA_API_KEY="sk-your-api-key"
```

---

## 🚀 快速开始

### 启动蒸馏库 Web 界面
```bash
cd brand-poster-distiller
python3 scripts/admin_server.py
```

### 查看技能文档
每个技能都有完整的 `SKILL.md` 文档，包含详细的使用说明和工作流。

---

## 📝 注意事项

1. **不要直接修改原始副本**：本包是从原项目复制的独立副本，用于研究和学习
2. **蒸馏卡版本**：当前为 v3.2，数据格式已简化
3. **生图模型**：如需生图，使用 gpt-image-2-pro，端点为 n.lconai.com

---

## 📞 技术支持

如有问题，请查看各项目的 `SKILL.md` 文档或联系原项目负责人。

---

*打包日期：2026-05-08*
