"""
规则检索服务 - 负责检索和匹配专利审核规则
"""
from typing import Dict, Any, List, Optional
from app.prompts.rules.loader import load_rules, format_rules_as_prompt, get_rules_for_template


class RuleRetriever:
    """
    规则检索器
    负责根据模板ID和案件类型检索匹配的审核规则
    """

    def __init__(self):
        self.rules_cache: Dict[int, Dict[str, Any]] = {}

    def get_system_prompt(
        self,
        template_id: int,
        case_type: str = None,
        extra_instructions: str = None
    ) -> str:
        """
        获取完整的system prompt

        Args:
            template_id: 模板ID (1=普通案例, 3=专案案例)
            case_type: 案件类型（实用新型/普通发明），可选
            extra_instructions: 额外指令，可选

        Returns:
            完整的system prompt字符串
        """
        rules = load_rules(template_id)
        if not rules:
            return ""

        # 格式化规则为基础prompt
        prompt_parts = []

        # 添加角色定义
        template_name = rules.get("template_name", "专利审核专家")
        prompt_parts.append(f"你是资深{template_name}，对专利申请书进行审核并输出详细、结构化的审核报告。")

        # 添加重要要求
        prompt_parts.append("\n【重要要求】")
        prompt_parts.append("- 每个审核项必须给出详细、具体的分析，篇幅充分")
        prompt_parts.append("- 问题描述要引用原文，说明具体位置（章/节/段落/权利要求号）")
        prompt_parts.append("- 修改建议要具体、可操作，不能泛泛而谈")
        prompt_parts.append("- 对于通过的项目，也要简要说明检查过程和结论依据")

        # 根据案件类型添加特定规则
        if case_type and case_type in ["实用新型", "普通发明"]:
            prompt_parts.append(f"\n【当前审核案件类型】：{case_type}")

        # 添加审核规则
        rules_prompt = self._format_rules_for_prompt(rules, case_type)
        if rules_prompt:
            prompt_parts.append("\n" + rules_prompt)

        # 添加额外指令
        if extra_instructions:
            prompt_parts.append(f"\n【额外要求】\n{extra_instructions}")

        return "\n".join(prompt_parts)

    def _format_rules_for_prompt(
        self,
        rules: Dict[str, Any],
        case_type: str = None
    ) -> str:
        """格式化规则为prompt字符串"""
        if not rules:
            return ""

        parts = []

        # 案件类型判定规则
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

        # 通用规则预审
        general_preview = rules.get("rules", {}).get("general_preview")
        if general_preview:
            parts.append("\n【通用规则预审 A-F】")
            categories = general_preview.get("categories", {})
            for cat_id, cat_info in sorted(categories.items()):
                name = cat_info.get("name", "")
                parts.append(f"\n{cat_id} {name}：")
                check_items = cat_info.get("check_items", [])
                for item in check_items:
                    parts.append(f"- {item.get('item', '')}：{item.get('check_point', '')}")
            parts.append("\n输出：结论（通过/不通过）+ 详细问题说明（引用原文+具体位置+修改建议）")

        # 领域审查（专案）
        field_review = rules.get("rules", {}).get("field_review")
        if field_review:
            parts.append("\n【领域审查】")
            check_items = field_review.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item', '')}：{item.get('check_point', '')}")

        # 分类型审核
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
                    parts.append(f"- {item.get('item', '')}：{item.get('requirement', '')}")

            content_review = um_rules.get("content_review", {})
            if content_review:
                parts.append("内容审查：")
                check_items = content_review.get("check_items", [])
                for item in check_items:
                    parts.append(f"- {item.get('item', '')}")
                    parts.append(f"  要求：{item.get('requirement', '')}")
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
                    parts.append(f"- {item.get('item', '')}：{item.get('requirement', '')}")

            content_review = in_rules.get("content_review", {})
            if content_review:
                parts.append("内容审查：")
                check_items = content_review.get("check_items", [])
                for item in check_items:
                    parts.append(f"- {item.get('item', '')}")
                    parts.append(f"  要求：{item.get('requirement', '')}")
                    parts.append(f"  检查方法：{item.get('method', '')}")

        # 格式审查（专案硬指标）
        format_review = rules.get("rules", {}).get("format_review")
        if format_review:
            parts.append("\n【格式审查】✅/❌/信息缺失")
            check_items = format_review.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item', '')}：{item.get('requirement', '')}")

        # 内容审查（含新颖性/创造性）
        content_review = rules.get("rules", {}).get("content_review")
        if content_review:
            parts.append("\n【内容审查（含新颖性/创造性）】")
            check_items = content_review.get("check_items", [])
            for item in check_items:
                parts.append(f"- {item.get('item', '')}")
                parts.append(f"  要求：{item.get('requirement', '')}")
                parts.append(f"  检查方法：{item.get('method', '')}")

        # 输出格式
        output_format = rules.get("output_format", {})
        if output_format:
            parts.append("\n【最终输出格式】（严格按此格式输出）")
            for section_id, section_info in sorted(output_format.items()):
                title = section_info.get("title", "")
                fields = section_info.get("fields", [])
                parts.append(f"\n{title}")
                for field in fields:
                    parts.append(f"- {field}：")

        return "\n".join(parts)

    def get_output_example(self, template_id: int) -> str:
        """
        获取输出示例

        Args:
            template_id: 模板ID

        Returns:
            输出示例字符串
        """
        rules = load_rules(template_id)
        if not rules:
            return ""

        # 从规则中提取输出示例
        # 这里可以添加详细的输出示例
        return ""

    def get_checklist(self, template_id: int, case_type: str = None) -> List[Dict[str, Any]]:
        """
        获取审核清单

        Args:
            template_id: 模板ID
            case_type: 案件类型

        Returns:
            审核清单列表
        """
        rules = load_rules(template_id)
        if not rules:
            return []

        checklist = []

        # 通用规则预审清单
        general_preview = rules.get("rules", {}).get("general_preview", {})
        categories = general_preview.get("categories", {})
        for cat_id, cat_info in sorted(categories.items()):
            for item in cat_info.get("check_items", []):
                checklist.append({
                    "category": f"{cat_id} {cat_info.get('name', '')}",
                    "item": item.get("item", ""),
                    "check_point": item.get("check_point", ""),
                    "method": item.get("method", ""),
                })

        # 分类型审核清单
        classified_audit = rules.get("rules", {}).get("classified_audit", {})
        audit_rules = classified_audit.get(case_type, {}) if case_type else {}

        format_review = audit_rules.get("format_review", {})
        for item in format_review.get("check_items", []):
            checklist.append({
                "category": "格式审查",
                "item": item.get("item", ""),
                "requirement": item.get("requirement", ""),
                "method": item.get("method", ""),
            })

        content_review = audit_rules.get("content_review", {})
        for item in content_review.get("check_items", []):
            checklist.append({
                "category": "内容审查",
                "item": item.get("item", ""),
                "requirement": item.get("requirement", ""),
                "method": item.get("method", ""),
            })

        return checklist


# 单例实例
rule_retriever = RuleRetriever()


def get_rule_retriever() -> RuleRetriever:
    """获取规则检索器单例"""
    return rule_retriever
