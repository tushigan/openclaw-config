#!/usr/bin/env bash
# 麦肯锡级跨平台适配脚本：Omni-Vision PSD Extractor (Mac专用)

echo "======================================================"
echo "[Mac Adaptation] Omni-Vision PSD Extractor Pipeline"
echo "======================================================"

# 1. 注入常见路径，解决 Mac GUI / Agent 环境下丢失 Homebrew 或 nvm 路径的问题
export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin:/opt/local/bin"

# 2. 如果存在 nvm，尝试加载
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
elif [ -s "/opt/homebrew/opt/nvm/nvm.sh" ]; then
    source "/opt/homebrew/opt/nvm/nvm.sh"
fi

# 3. 检查依赖命令
if ! command -v node &> /dev/null; then
    echo "[ERROR] 'node' command not found. Please install Node.js (e.g., via homebrew: brew install node)."
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] 'python3' command not found. Please install Python 3."
    exit 1
fi

# 4. 透传执行
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PIPELINE_SCRIPT="$SCRIPT_DIR/omni-vision-psd-extractor/omni-vision-psd-extractor/scripts/run_omni_pipeline.py"

echo "[INIT] Launching pipeline with python3..."
python3 "$PIPELINE_SCRIPT" "$@"
