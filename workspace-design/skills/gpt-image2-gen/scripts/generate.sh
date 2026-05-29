#!/bin/bash
# OpenAI-Compatible Image Generation Script
# Usage: ./generate.sh "prompt text" [aspect_ratio] [image_size] [output_path]

set -e

PROMPT="${1:-}"
ASPECT_RATIO="${2:-1:1}"
IMAGE_SIZE="${3:-1024x1024}"
OUTPUT_PATH="${4:-output.png}"

# Load from environment or use defaults
API_URL="${BANANA_API_URL:-https://n.lconai.com}"
API_KEY="${BANANA_API_KEY:-}"
MODEL="${BANANA_DEFAULT_MODEL:-gpt-image-2-pro}"
EXTRACT_B64_SCRIPT="/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/extract_image_b64.py"

if [ -z "$API_KEY" ]; then
    echo "Error: BANANA_API_KEY not set"
    exit 1
fi

if [ -z "$PROMPT" ]; then
    echo "Usage: $0 \"prompt text\" [aspect_ratio] [image_size] [output_path]"
    echo "Example: $0 \"A shrimp snack package\" 1:1 2K product.png"
    exit 1
fi

# Ensure width and height are divisible by 16 (gpt-image-2-pro requirement)
if [[ "$IMAGE_SIZE" =~ ^([0-9]+)x([0-9]+)$ ]]; then
    W="${BASH_REMATCH[1]}"
    H="${BASH_REMATCH[2]}"
    if (( W % 16 != 0 )); then
        W=$(( (W + 15) / 16 * 16 ))
        echo "[warn] width $((W)) was adjusted to ${W} (must be divisible by 16)"
        IMAGE_SIZE="${W}x${H}"
    fi
    if (( H % 16 != 0 )); then
        H=$(( (H + 15) / 16 * 16 ))
        echo "[warn] height ${H} was adjusted to ${H} (must be divisible by 16)"
        IMAGE_SIZE="${W}x${H}"
    fi
fi

# Build request payload
PAYLOAD=$(cat <<EOF
{
  "model": "$MODEL",
  "prompt": "$PROMPT",
  "n": 1,
  "size": "$IMAGE_SIZE",
  "response_format": "b64_json"
}
EOF
)

echo "Generating image..."
echo "Prompt: $PROMPT"
echo "Aspect Ratio (compat): $ASPECT_RATIO"
echo "Size: $IMAGE_SIZE"

# Make API request
if [ "$MODEL" != "gpt-image-2-pro" ]; then
    MODEL="gpt-image-2-pro"
fi
RESPONSE=$(curl -s -X POST \
    "${API_URL}/v1/images/generations" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d "$PAYLOAD")

# Check for errors
if echo "$RESPONSE" | grep -q "error"; then
    echo "Error: $RESPONSE"
    exit 1
fi

# Extract base64 image data
IMAGE_DATA=$(printf '%s' "$RESPONSE" | python3 "$EXTRACT_B64_SCRIPT")

if [ -z "$IMAGE_DATA" ]; then
    echo "Error: No image data in response"
    echo "Response: $RESPONSE"
    exit 1
fi

# Decode and save
echo "$IMAGE_DATA" | base64 -d > "$OUTPUT_PATH"
echo "Image saved to: $OUTPUT_PATH"
