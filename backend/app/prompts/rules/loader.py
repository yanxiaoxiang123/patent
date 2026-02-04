"""
规则加载器 - 负责加载和管理专利审核规则
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# 规则文件基础路径
RULES_DIR = Path(__file__).parent

# 规则缓存
_rules_cache: Dict[int, Dict[str, Any]] = {}


def load_rules(template_id: int) -> Optional[Dict[str, Any]]:
    """
    加载指定模板ID的审核规则

    Args:
        template_id: 模板ID (1=普通案例, 3=专案案例)

    Returns:
        规则字典，如果加载失败返回None
    """
    # 检查缓存
    if template_id in _rules_cache:
        return _rules_cache[template_id]

    # 规则文件映射
    rule_files = {
        1: "general_case_rules.json",
        3: "project_case_rules.json",
    }

    if template_id not in rule_files:
        print(f"[ERROR] 未找到模板ID {template_id} 对应的规则文件")
        return None

    rule_file = RULES_DIR / rule_files[template_id]

    try:
        with open(rule_file, "r", encoding="utf-8") as f:
            rules = json.load(f)

        # 缓存规则
        _rules_cache[template_id] = rules
        print(f"[INFO] 已加载模板ID {template_id} 的规则文件: {rule_file}")

        return rules

    except FileNotFoundError:
        print(f"[ERROR] 规则文件不存在: {rule_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] 规则文件JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 加载规则文件时发生错误: {e}")
        return None


def get_rules_for_template(template_id: int) -> Dict[str, Any]:
    """
    获取指定模板的规则，如果加载失败返回空字典

    Args:
        template_id: 模板ID

    Returns:
        规则字典
    """
    rules = load_rules(template_id)
    return rules if rules else {}


def get_all_rules() -> Dict[int, Dict[str, Any]]:
    """
    加载所有可用的规则

    Returns:
        所有规则的字典，key为template_id
    """
    all_rules = {}
    for template_id in [1, 3]:
        rules = load_rules(template_id)
        if rules:
            all_rules[template_id] = rules
    return all_rules


def clear_cache():
    """清除规则缓存"""
    global _rules_cache
    _rules_cache = {}
    print("[INFO] 规则缓存已清除")


def format_rules_as_prompt(rules: Dict[str, Any], case_type: str = None) -> str:
    """
    将规则格式化为system prompt

    Args:
        rules: 规则字典
        case_type: 案件类型（实用新型/普通发明），用于筛选对应规则

    Returns:
        格式化的prompt字符串
    """
    if not rules:
        return ""

    parts = []

    # 添加角色定义
    template_name = rules.get("template_name", "专利审核专家")
    parts.append(f"你是资深{template_name}，对专利申请书进行审核并输出详细、结构化的审核报告。")

    # 添加重要要求
    parts.append("\n【重要要求】")
    parts.append("- 每个审核项必须给出详细、具体的分析，篇幅充分")
    parts.append("- 问题描述要引用原文，说明具体位置（章/节/段落/权利要求号）")
    parts.append("- 修改建议要具体、可操作，不能泛泛而谈")
    parts.append("- 对于通过的项目，也要简要说明检查过程和结论依据")

    # 添加案件类型判定规则
    case_type_rules = rules.get("rules", {}).get("case_type_judgment")
    if case_type_rules:
        parts.append("\n【案件类型判定】")
        parts.append("根据文本判断：实用新型 / 普通发明")
        parts.append("输出：判定结果 + 详细依据（必须引用原文条款，说明判断依据）")

        judgment_criteria = case_type_rules.get("judgment_criteria", {})
        if judgment_criteria:
            parts.append("\n判断标准：")
            for case, criteria in judgment_criteria.items():
                parts.append(f"- {case}：{criteria}")

    # 添加通用规则预审
    general_preview = rules.get("rules", {}).get("general_preview")
    if general_preview:
        parts.append("\n【通用规则预审 A-F】")
        categories = general_preview.get("categories", {})
        for cat_id, cat_info in sorted(categories.items()):
            name = cat_info.get("name", "")
            parts.append(f"\n{cat_id} {name}：")
            check_items = cat_info.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item')}：{item.get('check_point', '')}")
        parts.append("\n输出：结论（通过/不通过）+ 详细问题说明（引用原文+具体位置+修改建议）")

    # 添加领域审查（专案）
    field_review = rules.get("rules", {}).get("field_review")
    if field_review:
        parts.append("\n【领域审查】")
        check_items = field_review.get("check_items", [])
        for item in check_items:
            parts.append(f"- {item.get('item')}：{item.get('check_point', '')}")

    # 添加分类审核（根据案件类型）
    classified_audit = rules.get("rules", {}).get("classified_audit", {})

    # 实用新型审核
    if "实用新型" in classified_audit:
        um_rules = classified_audit["实用新型"]
        parts.append("\n【实用新型审核】")

        format_review = um_rules.get("format_review", {})
        if format_review:
            parts.append("格式审查：✅/❌/信息缺失")
            check_items = format_review.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item')}：{item.get('requirement', '')}")

        content_review = um_rules.get("content_review", {})
        if content_review:
            parts.append("内容审查：")
            check_items = content_review.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item')}（{item.get('requirement', '')}）")
                parts.append(f"  检查方法：{item.get('method', '')}")

    # 普通发明审核
    if "普通发明" in classified_audit:
        in_rules = classified_audit["普通发明"]
        parts.append("\n【普通发明审核】")

        format_review = in_rules.get("format_review", {})
        if format_review:
            parts.append("格式审查：✅/❌/信息缺失")
            check_items = format_review.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item')}：{item.get('requirement', '')}")

        content_review = in_rules.get("content_review", {})
        if content_review:
            parts.append("内容审查：")
            check_items = content_review.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item')}（{item.get('requirement', '')}）")
                parts.append(f"  检查方法：{item.get('method', '')}")

    # 添加格式审查（专案硬指标）
    format_review = rules.get("rules", {}).get("format_review")
    if format_review:
        parts.append("\n【格式审查】✅/❌/信息缺失")
        check_items = format_review.get("check_items", [])
        for item in check_items:
            parts.append(f"- {item.get('item')}：{item.get('requirement', '')}")

    # 添加内容审查（含新颖性/创造性）
    content_review = rules.get("rules", {}).get("content_review")
    if content_review:
        parts.append("\n【内容审查（含新颖性/创造性）】")
        check_items = content_review.get("check_items", [])
        for item in check_items:
            parts.append(f"- {item.get('item')}：{item.get('requirement', '')}")
            parts.append(f"  检查方法：{item.get('method', '')}")

    # 添加输出格式
    output_format = rules.get("output_format", {})
    if output_format:
        parts.append("\n【最终输出格式】（严格按此格式输出）")
        for section_id, section_info in sorted(output_format.items()):
            title = section_info.get("title", "")
            fields = section_info.get("fields", [])
            parts.append(f"\n{title}")
            parts.append(f"- 字段：{', '.join(fields)}")

    return "\n".join(parts)


def reload_rules(template_id: int = None):
    """
    重新加载规则

    Args:
        template_id: 指定模板ID，如果为None则重新加载所有规则
    """
    global _rules_cache
    _rules_cache = {}

    if template_id:
        load_rules(template_id)
    else:
        get_all_rules()
