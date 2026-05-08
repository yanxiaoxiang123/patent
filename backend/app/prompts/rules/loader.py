"""
规则加载器 - 负责加载和管理专利审核规则
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

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
        1: "general_case_rules.json",       # 普通案例审核
        2: "patent_guidance_rules.json",    # 专利审核指导
        3: "project_case_rules.json",       # 专案案例审核
        5: "ipc_classification_rules.json", # IPC 分类指导
    }

    if template_id not in rule_files:
        logger.error("未找到模板ID %s 对应的规则文件", template_id)
        return None

    rule_file = RULES_DIR / rule_files[template_id]

    try:
        with open(rule_file, "r", encoding="utf-8") as f:
            rules = json.load(f)

        # 缓存规则
        _rules_cache[template_id] = rules
        logger.info("已加载模板ID %s 的规则文件: %s", template_id, rule_file)

        return rules

    except FileNotFoundError:
        logger.error("规则文件不存在: %s", rule_file)
        return None
    except json.JSONDecodeError as e:
        logger.error("规则文件JSON解析错误: %s", e)
        return None
    except Exception as e:
        logger.error("加载规则文件时发生错误: %s", e)
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
    for template_id in [1, 2, 3, 5]:
        rules = load_rules(template_id)
        if rules:
            all_rules[template_id] = rules
    return all_rules


def clear_cache():
    """清除规则缓存"""
    global _rules_cache
    _rules_cache = {}
    logger.info("规则缓存已清除")


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
