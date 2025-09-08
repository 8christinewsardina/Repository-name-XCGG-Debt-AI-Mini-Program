"""合规模块：检查模型输出，注入免责声明，并决定是否需要人工复核。

规则（示例）：
- 如果 recommendations 中包含法律行动（例如 '起诉', '诉讼'）或明确法律条款，标记为需要人工法律复核。
- 始终附加简短免责声明，提示用户咨询本地执业律师以获得法律意见。
"""
from typing import Dict, Any
import re


LEGAL_KEYWORDS = ['起诉', '诉讼', '仲裁', '法律程序', '诉讼方案']


def check_compliance(result: Dict[str, Any]) -> Dict[str, Any]:
    """返回增强后的结果和合规元数据"""
    needs_legal = False
    recs = result.get('recommendations', []) or []
    for r in recs:
        for kw in LEGAL_KEYWORDS:
            if re.search(kw, r):
                needs_legal = True
                break
        if needs_legal:
            break

    # 注入免责声明（简短）
    disclaimer = '本报告为信息性建议，不构成法律意见；如需法律意见，请咨询持牌律师。'
    result['_disclaimer'] = disclaimer
    result['_needs_legal_review'] = needs_legal
    return result
