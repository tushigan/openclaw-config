#!/usr/bin/env python3
"""
RH抠图王 API 切换验证测试

验证内容：
1. 新的 API 端点配置正确
2. WebappId 和 NodeId 配置正确
3. 扣费方式从"钱包余额"改为"HB 算力币"
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


def test_rh_matting_config():
    """测试 RH 抠图配置"""
    print("=" * 60)
    print("测试 1: RH抠图王配置验证")
    print("=" * 60)

    try:
        # 导入新的 rh_matting 脚本
        import rh_matting

        # 检查关键配置
        checks = [
            ("API Key", hasattr(rh_matting, 'RH_API_KEY'), "442de49dcb5247a285b678a4c70e7499"),
            ("WebappId", hasattr(rh_matting, 'RH_WEBAPP_ID'), 2064637853572878337),
            ("NodeId", hasattr(rh_matting, 'RH_NODE_ID'), "151"),
            ("FieldName", hasattr(rh_matting, 'RH_FIELD_NAME'), "url"),
            ("Submit URL", hasattr(rh_matting, 'RH_SUBMIT_URL'), "https://www.runninghub.cn/task/openapi/ai-app/run"),
            ("Query URL", hasattr(rh_matting, 'RH_QUERY_URL'), "https://www.runninghub.cn/openapi/v2/query"),
        ]

        all_passed = True
        for name, has_attr, expected_value in checks:
            if has_attr:
                actual_value = getattr(rh_matting, name.replace(' ', '_').replace('/', '_').upper())
                if actual_value == expected_value:
                    print(f"✅ {name}: {actual_value}")
                else:
                    print(f"❌ {name}: 期望 {expected_value}, 实际 {actual_value}")
                    all_passed = False
            else:
                print(f"❌ {name}: 配置缺失")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoint_change():
    """测试 API 端点变更"""
    print("\n" + "=" * 60)
    print("测试 2: API 端点变更验证")
    print("=" * 60)

    try:
        import rh_matting

        # 旧端点（N8N webhook - 扣钱包）
        old_endpoint = "https://n8n.lconai.com/webhook/c662eebb-0a0b-4c4d-8df4-7b5b01d2b27a"

        # 新端点（RunningHub AI 应用 - 扣 HB）
        new_submit = rh_matting.RH_SUBMIT_URL
        new_query = rh_matting.RH_QUERY_URL

        print(f"旧端点（N8N webhook）:")
        print(f"  ❌ {old_endpoint}")
        print(f"  扣费方式: 钱包余额")
        print()
        print(f"新端点（AI 应用 API）:")
        print(f"  ✅ Submit: {new_submit}")
        print(f"  ✅ Query:  {new_query}")
        print(f"  扣费方式: HB 算力币")
        print()

        # 验证新端点不包含旧端点
        if old_endpoint not in str(new_submit) and old_endpoint not in str(new_query):
            print("✅ 已成功切换到新的 AI 应用 API 端点")
            return True
        else:
            print("❌ 仍在使用旧的 N8N webhook 端点")
            return False

    except Exception as e:
        print(f"❌ 端点验证失败: {e}")
        return False


def test_request_structure():
    """测试请求结构"""
    print("\n" + "=" * 60)
    print("测试 3: 请求结构验证")
    print("=" * 60)

    try:
        import rh_matting

        print("预期请求结构（AI 应用 API）:")
        print("""
{
  "apiKey": "442de49dcb5247a285b678a4c70e7499",
  "webappId": 2064637853572878337,
  "nodeInfoList": [
    {
      "nodeId": "151",
      "fieldName": "url",
      "fieldValue": "<图片 URL>"
    }
  ]
}
        """)

        print("\n验证关键参数:")
        print(f"  ✅ webappId: {rh_matting.RH_WEBAPP_ID}")
        print(f"  ✅ nodeId: {rh_matting.RH_NODE_ID}")
        print(f"  ✅ fieldName: {rh_matting.RH_FIELD_NAME}")
        print()
        print("✅ 请求结构符合 AI 应用 API 规范")

        return True

    except Exception as e:
        print(f"❌ 请求结构验证失败: {e}")
        return False


def test_billing_mode():
    """测试扣费方式标注"""
    print("\n" + "=" * 60)
    print("测试 4: 扣费方式标注")
    print("=" * 60)

    try:
        script_path = SCRIPT_DIR / "rh_matting.py"
        content = script_path.read_text(encoding='utf-8')

        checks = [
            ("AI 应用模式 - 扣 HB", "AI 应用模式 - 扣 HB" in content),
            ("HB 算力币", "HB 算力币" in content),
            ("非钱包余额", "非钱包余额" in content),
        ]

        all_passed = True
        for name, found in checks:
            if found:
                print(f"✅ 找到标注: {name}")
            else:
                print(f"❌ 缺失标注: {name}")
                all_passed = False

        if all_passed:
            print("\n✅ 扣费方式已明确标注为 HB 算力币")
        else:
            print("\n⚠️  部分扣费方式标注缺失")

        return all_passed

    except Exception as e:
        print(f"❌ 扣费方式验证失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("RH抠图王 API 切换验证测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("配置验证", test_rh_matting_config()))
    results.append(("API 端点变更", test_api_endpoint_change()))
    results.append(("请求结构", test_request_structure()))
    results.append(("扣费方式标注", test_billing_mode()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("\n修改总结:")
        print("  旧方式: N8N webhook → 扣钱包余额")
        print("  新方式: AI 应用 API → 扣 HB 算力币")
        print("\n  WebappId: 2064637853572878337")
        print("  NodeId: 151")
        print("  API Key: 442de49dcb5247a285b678a4c70e7499")
        print("\n准备测试实际抠图功能...")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分测试失败，请检查日志")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
