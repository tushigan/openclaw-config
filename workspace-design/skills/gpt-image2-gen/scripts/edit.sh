#!/bin/bash
# OpenAI-Compatible Image-to-Image Script
# Usage: ./edit.sh "prompt text" "reference_image_url" [aspect_ratio] [image_size] [output_path]

set -e

PROMPT="${1:-}"
REFERENCE_IMAGE="${2:-}"
ASPECT_RATIO="${3:-1:1}"
IMAGE_SIZE="${4:-1024x1024}"
OUTPUT_PATH="${5:-output.png}"

# Load from environment or use defaults
API_URL="${BANANA_API_URL:-https://n.lconai.com}"
API_KEY="${BANANA_API_KEY:-}"
MODEL="${BANANA_DEFAULT_MODEL:-gpt-image-2-pro}"
EXTRACT_B64_SCRIPT="/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/extract_image_b64.py"

if [ -z "$API_KEY" ]; then
    echo "Error: BANANA_API_KEY not set"
    exit 1
fi

if [ -z "$PROMPT" ] || [ -z "$REFERENCE_IMAGE" ]; then
    echo "Usage: $0 \"prompt text\" \"reference_image_url\" [aspect_ratio] [image_size] [output_path]"
    echo "Example: $0 \"Add festive elements\" https://example.com/base.png 1:1 1024x1024 festive.png"
    exit 1
fi

# Ensure width and height are divisible by 16 (gpt-image-2-pro requirement)
if [[ "$IMAGE_SIZE" =~ ^([0-9]+)x([0-9]+)$ ]]; then
    W="${BASH_REMATCH[1]}"
    H="${BASH_REMATCH[2]}"
    if (( W % 16 != 0 )); then
        W=$(( (W + 15) / 16 * 16 ))
        echo "[warn] width was adjusted to ${W} (must be divisible by 16)"
        IMAGE_SIZE="${W}x${H}"
    fi
    if (( H % 16 != 0 )); then
        H=$(( (H + 15) / 16 * 16 ))
        echo "[warn] height was adjusted to ${H} (must be divisible by 16)"
        IMAGE_SIZE="${W}x${H}"
    fi
fi

if [[ "$REFERENCE_IMAGE" =~ ^https?:// ]]; then
    IMAGE_REF_VALUE="$REFERENCE_IMAGE"
elif [ -f "$REFERENCE_IMAGE" ]; then
    EXT="${REFERENCE_IMAGE##*.}"
    case "$EXT" in
        png) MIME_TYPE="image/png" ;;
        jpg|jpeg) MIME_TYPE="image/jpeg" ;;
        webp) MIME_TYPE="image/webp" ;;
        *) MIME_TYPE="image/png" ;;
    esac
    IMAGE_BASE64=$(base64 -i "$REFERENCE_IMAGE" | tr -d '\n')
    IMAGE_REF_VALUE="data:${MIME_TYPE};base64,${IMAGE_BASE64}"
else
    echo "Error: REFERENCE_IMAGE must be a public URL or existing local file"
    exit 1
fi

# Build request payload
PAYLOAD=$(cat <<EOF
{
  "model": "$MODEL",
  "prompt": "$PROMPT",
  "n": 1,
  "size": "$IMAGE_SIZE",
  "response_format": "b64_json",
  "image": ["$IMAGE_REF_VALUE"]
}
EOF
)

echo "Editing image..."
echo "Prompt: $PROMPT"
echo "Reference: $REFERENCE_IMAGE"
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
