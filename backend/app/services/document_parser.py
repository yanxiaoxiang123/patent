"""专利文档解析服务"""
import re
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import docx
import pdfplumber
import PyPDF2
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)


# ===================== 文本处理工具 =====================

def normalize_text(text: str) -> str:
    """标准化 DOC 文本"""
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\x0c", "\n")
    text = re.sub(r"(?im)^[ \t]*PAGE[ \t]*\\?\*[ \t]*MERGEFORMAT[ \t]*\d+[ \t]*$", "", text)
    text = re.sub(r"(?i)PAGE\s*\\?\*\s*MERGEFORMAT\s*\d+", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [ln.rstrip() for ln in text.split("\n")]
    idx = 0
    while idx < len(lines):
        ln = (lines[idx] or "").strip()
        if not ln:
            idx += 1
            continue
        cjk = sum(1 for ch in ln if "\u4e00" <= ch <= "\u9fff")
        alnum = sum(1 for ch in ln if ch.isalnum())
        if (cjk + alnum) >= 2:
            break
        if len(ln) > 30:
            break
        idx += 1
    return "\n".join(lines[idx:]).strip()


def score_text(text: str) -> float:
    """评估文本质量分数"""
    if not text:
        return 0.0
    total = len(text)
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    alnum = sum(1 for ch in text if ch.isalnum())
    bad = len(re.findall(r"(?i)PAGE\s*\\?\*\s*MERGEFORMAT\s*\d+", text))
    head = text[:300]
    head_total = max(len(head), 1)
    head_cjk = sum(1 for ch in head if "\u4e00" <= ch <= "\u9fff")
    weird = sum(1 for ch in head if (
        ch not in "\n\t "
        and not ("\u4e00" <= ch <= "\u9fff")
        and not ch.isalnum()
        and not (0x20 <= ord(ch) <= 0x7E)
    ))
    head_weird_ratio = weird / head_total
    base = (cjk + 0.3 * alnum) / max(total, 1) - 0.05 * bad
    if head_cjk < 5:
        base -= 0.05
    base -= 0.15 * head_weird_ratio
    return base


# ===================== DOC 解析工具 =====================

def run_subprocess(cmd: list, timeout_s: int = 60) -> str:
    """运行子进程命令"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="ignore", timeout=timeout_s
        )
        return result.stdout or "" if result.returncode == 0 else ""
    except Exception:
        return ""


def run_wvtext(doc_path: str, timeout_s: int = 60) -> str:
    """使用 wvText 解析 DOC"""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp_path = tmp.name
        result = subprocess.run(
            ["wvText", doc_path, tmp_path],
            capture_output=True, text=True,
            encoding="utf-8", errors="ignore", timeout=timeout_s
        )
        if result.returncode == 0:
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        return ""
    except Exception:
        return ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def parse_doc_with_tools(file_path: str) -> Optional[str]:
    """使用系统工具解析 DOC 文件"""
    candidates = []

    # 尝试 catdoc
    catdoc_text = normalize_text(run_subprocess(["catdoc", file_path]))
    if catdoc_text:
        candidates.append(("catdoc", catdoc_text))

    # 尝试 wvText
    wv_text = normalize_text(run_wvtext(file_path))
    if wv_text:
        candidates.append(("wvText", wv_text))

    # 尝试 antiword
    antiword_text = normalize_text(run_subprocess(["antiword", file_path]))
    if antiword_text:
        candidates.append(("antiword", antiword_text))

    # 选择最佳结果
    if candidates:
        best_name, best = max(candidates, key=lambda x: score_text(x[1]))
        # 如果 catdoc 分数接近最佳，也使用 catdoc（兼容性更好）
        if catdoc_text and best_name != "catdoc":
            if score_text(catdoc_text) >= score_text(best) - 0.02:
                return catdoc_text
        return best

    return None


def parse_doc_fallback(file_path: str) -> str:
    """DOC 解析备用方案（无法解析时）"""
    try:
        import olefile
        if olefile.isOleFile(file_path):
            with olefile.OleFileIO(file_path) as ole:
                if ole._olestream_exists('WordDocument'):
                    with ole.openstream('WordDocument') as stream:
                        data = stream.read()
                        return f"DOC 文件已加载，文件大小: {len(data)} 字节。"
    except Exception:
        pass

    file_size = os.path.getsize(file_path)
    return f"无法完整解析 DOC 文件，文件大小: {file_size} 字节。建议另存为 DOCX 格式。"


# ===================== 专利解析器 =====================

class PatentDocumentParser:
    """专利文档解析器"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.section_patterns = {
            'title': [
                r'发明创造名称[：:]?\s*(.+)',
                r'名称[：:]?\s*(.+)',
                r'专利名称[：:]?\s*(.+)'
            ],
            'abstract': [
                r'说明书摘要\s*(?:\n|$)',
                r'摘要\s*(?:\n|$)',
                r'技术领域\s*(?:\n|$)'
            ],
            'claims': [
                r'权利要求书\s*(?:\n|$)',
                r'权利要求\s*(?:\n|$)',
                r'权\s*利\s*要\s*求\s*书\s*(?:\n|$)'
            ],
            'description': [
                r'说明书\s*(?:\n|$)',
                r'技术方案\s*(?:\n|$)',
                r'具体实施方式\s*(?:\n|$)'
            ]
        }

    async def parse_document(
        self,
        file_path: str,
        file_type: str,
        progress_callback: Optional[Callable[[str, int, str], None]] = None
    ) -> Dict[str, Any]:
        """解析专利文档

        Args:
            file_path: 文件路径
            file_type: 文件类型 (docx, doc, pdf)
            progress_callback: 进度回调函数，接受 (stage, percent, message) 参数
        """
        def report_progress(stage: str, percent: int, message: str):
            if progress_callback:
                try:
                    progress_callback(stage, percent, message)
                except Exception as e:
                    logger.warning(f"进度回调失败: {e}")

        try:
            logger.info(f"开始解析文档: {file_path}, 类型: {file_type}")

            # 阶段1: 提取文本
            report_progress("extracting_text", 10, "正在提取文件文本内容...")
            if file_type.lower() == 'docx':
                parse_result = await self._parse_docx(file_path)
            elif file_type.lower() == 'doc':
                parse_result = await self._parse_doc(file_path)
            elif file_type.lower() == 'pdf':
                parse_result = await self._parse_pdf(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")

            # 阶段2: 分析结构
            report_progress("analyzing_structure", 40, "正在分析文档结构...")
            content = parse_result.get('full_content', '')
            first_page = parse_result.get('first_page_content', '')

            # 阶段3: 提取章节
            report_progress("extracting_sections", 70, "正在提取专利章节信息...")
            structured = self._extract_structured_content(content)

            # 阶段4: 评估质量
            report_progress("assessing_quality", 90, "正在评估解析质量...")
            sections_info = self._get_sections_info(structured)

            logger.info("文档解析完成")
            report_progress("complete", 100, "文档解析已完成")

            return {
                'raw_content': content,
                'first_page_content': first_page,
                'structured': structured,
                'sections': sections_info
            }
        except Exception as e:
            logger.error(f"文档解析失败: {str(e)}")
            report_progress("error", 0, f"解析失败: {str(e)}")
            raise

    async def _parse_docx(self, file_path: str) -> Dict[str, str]:
        """解析 DOCX 文件"""
        def _parse():
            doc = docx.Document(file_path)
            content_parts = []
            first_page_parts = []
            first_page_done = False

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content_parts.append(paragraph.text.strip())
                    if not first_page_done:
                        first_page_parts.append(paragraph.text.strip())

                if not first_page_done and paragraph.runs:
                    for run in paragraph.runs:
                        xml = getattr(run._element, "xml", "") or ""
                        if 'w:type="page"' in xml or "lastRenderedPageBreak" in xml:
                            first_page_done = True
                            break

            full = '\n'.join(content_parts)
            first_page = '\n'.join(first_page_parts).strip() or full[:2000]
            return {'full_content': full, 'first_page_content': first_page}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _parse)

    async def _parse_doc(self, file_path: str) -> Dict[str, str]:
        """解析 DOC 文件"""
        def _parse():
            text = parse_doc_with_tools(file_path)
            if text:
                return {'full_content': text, 'first_page_content': text[:2000]}
            return {'full_content': parse_doc_fallback(file_path), 'first_page_content': ''}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _parse)

    async def _parse_pdf(self, file_path: str) -> Dict[str, str]:
        """解析 PDF 文件"""
        def _parse():
            try:
                with pdfplumber.open(file_path) as pdf:
                    content_parts = []
                    first_page = ""
                    for i, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if text and text.strip():
                            if i == 1 and not first_page:
                                first_page = text.strip()
                            content_parts.append(f"[第{i}页]\n{text.strip()}")
                    full = '\n\n'.join(content_parts)
                    return {'full_content': full, 'first_page_content': first_page or full[:2000]}
            except Exception:
                pass

            # PyPDF2 备用
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    content_parts = []
                    first_page = ""
                    for i, page in enumerate(reader.pages, 1):
                        text = page.extract_text()
                        if text and text.strip():
                            if i == 1 and not first_page:
                                first_page = text.strip()
                            content_parts.append(f"[第{i}页]\n{text.strip()}")
                    full = '\n\n'.join(content_parts)
                    return {'full_content': full, 'first_page_content': first_page or full[:2000]}
            except Exception as e:
                raise Exception(f"PDF 解析失败: {e}")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _parse)

    # ===================== 结构化提取 =====================

    def _extract_structured_content(self, content: str) -> Dict[str, Any]:
        """提取结构化内容"""
        structured = {'title': '', 'abstract': '', 'claims': [], 'description': ''}

        try:
            structured['title'] = self._extract_title(content).strip() if self._extract_title(content) else ''
            sections = self._split_into_sections(content)

            if 'abstract' in sections:
                structured['abstract'] = sections['abstract'].strip()
            if 'claims' in sections:
                structured['claims'] = self._parse_claims(sections['claims'])
            if 'description' in sections:
                structured['description'] = sections['description'].strip()

            # 修复不完整的提取
            self._fix_structured_content(structured, content)
        except Exception as e:
            logger.error(f"结构化提取失败: {str(e)}")

        return structured

    def _fix_structured_content(self, structured: Dict[str, Any], content: str):
        """修复不完整的结构化内容"""
        # 提取权利要求块
        claims_block = self._extract_claims_block(content)
        if not structured['claims'] and claims_block:
            structured['claims'] = self._parse_claims(claims_block)

        # 改进摘要和描述
        abstract, description = self._improve_abstract_description(content)
        if not structured['abstract'] and abstract:
            structured['abstract'] = abstract
        if not structured['description'] and description:
            structured['description'] = description

    def _extract_claims_block(self, text: str) -> str:
        """提取权利要求块"""
        lines = [ln.strip() for ln in (text or "").split("\n")]
        for i, ln in enumerate(lines):
            if re.match(r"^1[\.、]\s*\S", ln) or re.match(r"^1[\.、]$", ln):
                start = i
                for j in range(i + 1, len(lines)):
                    if re.match(r"^(技术领域|背景技术|发明内容|实用新型内容|具体实施方式|附图说明|说明书)\s*$", lines[j]):
                        return "\n".join(lines[start:j]).strip()
                return "\n".join(lines[start:]).strip()
        return ""

    def _improve_abstract_description(self, text: str) -> tuple:
        """改进摘要和描述"""
        lines = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
        if not lines:
            return "", ""

        # 找到权利要求开始位置
        claim_start = None
        for i, ln in enumerate(lines):
            if re.match(r"^1[\.、]\s*\S", ln) or re.match(r"^1[\.、]$", ln):
                claim_start = i
                break

        # 提取摘要
        abstract = ""
        if claim_start and claim_start > 0:
            abstract = "\n".join(lines[:claim_start]).strip()
        if not abstract:
            for i, ln in enumerate(lines[:60]):
                if ln.startswith("摘要"):
                    j = i + 1
                    while j < len(lines) and j < i + 25:
                        if re.match(r"^(权利要求书|权利要求|技术领域|背景技术|说明书)\s*$", lines[j]):
                            break
                        j += 1
                    abstract = "\n".join(lines[i:j]).strip()
                    break

        # 提取描述
        desc_start = None
        for i, ln in enumerate(lines):
            if ln == "技术领域":
                desc_start = i
                break
        if desc_start is None and claim_start:
            desc_start = claim_start

        description = "\n".join(lines[desc_start:]).strip() if desc_start is not None else ""

        return abstract[:800].strip(), description[:4000].strip()

    def _extract_title(self, content: str) -> Optional[str]:
        """提取文档标题"""
        for line in content.split('\n')[:50]:
            line = line.strip()
            if 5 < len(line) < 100:
                for pattern in self.section_patterns['title']:
                    if match := re.search(pattern, line):
                        return match.group(1).strip()
                if '一种' in line and len(line) < 60:
                    if not any(w in line for w in ['摘要', '技术领域', '背景技术']):
                        return line
                if line and not any(w in line for w in ['本发明', '本实用新型', '所述', '包括']):
                    if sum(1 for ch in line if "\u4e00" <= ch <= "\u9fff") / max(len(line), 1) >= 0.3:
                        return line
        return None

    def _split_into_sections(self, content: str) -> Dict[str, str]:
        """分割文档章节"""
        sections, current_section, current_content = {}, None, []

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            for section_name, patterns in self.section_patterns.items():
                if section_name == 'title':
                    continue
                for pattern in patterns:
                    if re.match(pattern, line):
                        if current_section and current_content:
                            sections[current_section] = '\n'.join(current_content)
                        current_section, current_content = section_name, []
                        break
                else:
                    continue
                break

            if current_section and not re.match(r"^\d+[\.、]|^权利要求|^技术领域|^背景|^说明|^附图", line):
                current_content.append(line)

        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        return sections

    def _parse_claims(self, claims_text: str) -> list:
        """解析权利要求"""
        claims, current_claim, claim_number = [], [], 0

        for line in claims_text.split('\n'):
            line = line.strip()
            if match := re.match(r'^(\d+)\.?\s*(.*)', line):
                if current_claim:
                    claims.append({'number': claim_number, 'content': ' '.join(current_claim).strip()})
                claim_number, current_claim = int(match.group(1)), [match.group(2)]
            elif current_claim and '根据权利要求' in line:
                current_claim.append(line)
            elif current_claim:
                current_claim.append(line)

        if current_claim:
            claims.append({'number': claim_number, 'content': ' '.join(current_claim).strip()})
        return claims

    def _get_sections_info(self, structured_content: Dict[str, Any]) -> Dict[str, Any]:
        """获取文档部分信息"""
        return {
            'has_title': bool(structured_content.get('title')),
            'has_abstract': bool(structured_content.get('abstract')),
            'has_claims': len(structured_content.get('claims', [])) > 0,
            'claims_count': len(structured_content.get('claims', [])),
            'has_description': bool(structured_content.get('description')),
            'content_length': len(structured_content.get('description', '')),
            'parsing_quality': self._assess_parsing_quality(structured_content)
        }

    def _assess_parsing_quality(self, structured_content: Dict[str, Any]) -> str:
        """评估解析质量"""
        score = 0
        if structured_content.get('title'): score += 20
        if structured_content.get('abstract'): score += 25
        if structured_content.get('claims'): score += 35
        if structured_content.get('description'): score += 20

        if score >= 80: return 'excellent'
        if score >= 60: return 'good'
        if score >= 40: return 'fair'
        return 'poor'

    async def close(self):
        """关闭解析器"""
        self.executor.shutdown(wait=True)


# 全局实例
document_parser = PatentDocumentParser()
