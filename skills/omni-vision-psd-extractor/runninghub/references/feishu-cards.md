# Feishu Interactive Card for RunningHub

Use this card to let users select parameters visually.

```json
{
  "config": { "wide_screen_mode": true },
  "header": {
    "title": { "tag": "plain_text", "content": "🎨 RunningHub 创作中心" },
    "template": "blue"
  },
  "elements": [
    {
      "tag": "div",
      "text": { "tag": "lark_md", "content": "**请选择您的创作任务**\n点击下方按钮快速开始" }
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "text": { "tag": "plain_text", "content": "🚀 文本生图" },
          "type": "primary",
          "value": { "action": "draw_text" }
        },
        {
          "tag": "button",
          "text": { "tag": "plain_text", "content": "🎬 图片生视频" },
          "type": "primary",
          "value": { "action": "video_img" }
        }
      ]
    },
    {
      "tag": "hr"
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "text": { "tag": "plain_text", "content": "💰 检查余额" },
          "type": "default",
          "value": { "action": "check_balance" }
        }
      ]
    }
  ]
}
```
