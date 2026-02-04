"""
专利文档解析服务
支持 .docx 和 .pdf 格式的专利文档解析，提取结构化内容
"""
import re
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import docx
import PyPDF2
import pdfplumber
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

class PatentDocumentParser:
    """专利文档解析器"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 专利文档结构关键词
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

    async def parse_document(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """解析专利文档"""
        try:
            logger.info(f"开始解析文档: {file_path}, 类型: {file_type}")

            if file_type.lower() == 'docx':
                parse_result = await self._parse_docx(file_path)
            elif file_type.lower() == 'doc':
                parse_result = await self._parse_doc(file_path)
            elif file_type.lower() == 'pdf':
                parse_result = await self._parse_pdf(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")

            if isinstance(parse_result, dict):
                content = parse_result.get('full_content') or ''
                first_page_content = parse_result.get('first_page_content') or ''
            else:
                content = parse_result
                first_page_content = ''

            # 结构化解析
            structured_content = self._extract_structured_content(content)

            logger.info("文档解析完成")
            return {
                'raw_content': content,
                'first_page_content': first_page_content,
                'structured': structured_content,
                'sections': self._get_sections_info(structured_content)
            }

        except Exception as e:
            logger.error(f"文档解析失败: {str(e)}")
            raise Exception(f"文档解析失败: {str(e)}")

    async def _parse_docx(self, file_path: str) -> Dict[str, str]:
        """解析 DOCX 文件"""
        def _parse():
            try:
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

                full_content = '\n'.join(content_parts)
                first_page_content = '\n'.join(first_page_parts).strip()
                if not first_page_content:
                    first_page_content = full_content[:2000]

                return {
                    'full_content': full_content,
                    'first_page_content': first_page_content,
                }

            except Exception as e:
                raise Exception(f"DOCX 解析失败: {str(e)}")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _parse)

    async def _parse_doc(self, file_path: str) -> Dict[str, str]:
        """解析 DOC 文件（旧版 Word 格式）"""
        def _parse():
            try:
                def normalize_text(text: str) -> str:
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
                    text = "\n".join(lines[idx:])
                    return text.strip()

                def score_text(text: str) -> float:
                    if not text:
                        return 0.0
                    total = len(text)
                    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
                    alnum = sum(1 for ch in text if ch.isalnum())
                    bad = len(re.findall(r"(?i)PAGE\s*\\?\*\s*MERGEFORMAT\s*\d+", text))
                    head = text[:300]
                    head_total = max(len(head), 1)
                    head_cjk = sum(1 for ch in head if "\u4e00" <= ch <= "\u9fff")
                    weird = 0
                    for ch in head:
                        o = ord(ch)
                        if ch in "\n\t ":
                            continue
                        if "\u4e00" <= ch <= "\u9fff":
                            continue
                        if ch.isalnum():
                            continue
                        if 0x20 <= o <= 0x7E:
                            continue
                        weird += 1
                    head_weird_ratio = weird / head_total
                    base = (cjk + 0.3 * alnum) / max(total, 1) - 0.05 * bad
                    if head_cjk < 5:
                        base -= 0.05
                    base -= 0.15 * head_weird_ratio
                    return base

                def run_capture(cmd: list, timeout_s: int = 60) -> str:
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="ignore",
                            timeout=timeout_s,
                        )
                        if result.returncode != 0:
                            return ""
                        return result.stdout or ""
                    except Exception:
                        return ""

                def run_wvtext(doc_path: str, timeout_s: int = 60) -> str:
                    tmp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                            tmp_path = tmp.name
                        result = subprocess.run(
                            ["wvText", doc_path, tmp_path],
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="ignore",
                            timeout=timeout_s,
                        )
                        if result.returncode != 0:
                            return ""
                        with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                            return f.read()
                    except Exception:
                        return ""
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            try:
                                os.remove(tmp_path)
                            except OSError:
                                pass

                candidates = []

                catdoc_text = normalize_text(run_capture(["catdoc", file_path]))
                if catdoc_text:
                    candidates.append(catdoc_text)

                wv_text = normalize_text(run_wvtext(file_path))
                if wv_text:
                    candidates.append(wv_text)

                antiword_text = normalize_text(run_capture(["antiword", file_path]))
                if antiword_text:
                    candidates.append(antiword_text)

                if candidates:
                    best = max(candidates, key=score_text)
                    if catdoc_text:
                        if score_text(catdoc_text) >= score_text(best) - 0.02:
                            best = catdoc_text
                    return {
                        'full_content': best,
                        'first_page_content': (best[:2000] if best else ""),
                    }

                # 方法3: 如果系统工具都不可用，尝试 olefile 和 struct (简化解析)
                try:
                    import olefile
                    import struct

                    if olefile.isOleFile(file_path):
                        with olefile.OleFileIO(file_path) as ole:
                            # 尝试读取 WordDocument 流
                            if ole._olestream_exists('WordDocument'):
                                with ole.openstream('WordDocument') as stream:
                                    # 简化的文本提取（可能不完整）
                                    data = stream.read()
                                    # 这里需要复杂的 Word 格式解析，暂时返回基本信息
                                    full_content = f"DOC 文件已加载，但需要专门的解析器。文件大小: {len(data)} 字节。"
                                    return {
                                        'full_content': full_content,
                                        'first_page_content': full_content,
                                    }

                except Exception:
                    pass

                # 如果所有方法都失败，返回基本信息
                file_size = os.path.getsize(file_path)
                full_content = f"无法完整解析 DOC 文件，但文件已识别。文件大小: {file_size} 字节。建议将文件另存为 DOCX 格式以获得更好的解析效果。"
                return {
                    'full_content': full_content,
                    'first_page_content': full_content,
                }

            except Exception as e:
                raise Exception(f"DOC 解析失败: {str(e)}")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _parse)

    async def _parse_pdf(self, file_path: str) -> Dict[str, str]:
        """解析 PDF 文件（使用 pdfplumber，支持更好的中文处理）"""
        def _parse():
            try:
                content_parts = []
                first_page_content = ""

                with pdfplumber.open(file_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if text and text.strip():
                            if page_num == 1 and not first_page_content:
                                first_page_content = text.strip()
                            content_parts.append(f"[第{page_num}页]\n{text.strip()}")

                full_content = '\n\n'.join(content_parts)
                if not first_page_content:
                    first_page_content = full_content[:2000]

                return {
                    'full_content': full_content,
                    'first_page_content': first_page_content,
                }

            except Exception as e:
                # 如果 pdfplumber 失败，尝试 PyPDF2
                try:
                    content_parts = []
                    first_page_content = ""
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for page_num, page in enumerate(reader.pages, 1):
                            text = page.extract_text()
                            if text and text.strip():
                                if page_num == 1 and not first_page_content:
                                    first_page_content = text.strip()
                                content_parts.append(f"[第{page_num}页]\n{text.strip()}")
                    full_content = '\n\n'.join(content_parts)
                    if not first_page_content:
                        first_page_content = full_content[:2000]
                    return {
                        'full_content': full_content,
                        'first_page_content': first_page_content,
                    }
                except Exception as e2:
                    raise Exception(f"PDF 解析失败 (pdfplumber: {e}, PyPDF2: {e2})")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _parse)

    def _extract_structured_content(self, content: str) -> Dict[str, Any]:
        """提取结构化内容"""
        structured = {
            'title': '',
            'abstract': '',
            'claims': [],
            'description': ''
        }

        try:
            # 提取标题
            title = self._extract_title(content)
            if title:
                structured['title'] = title.strip()

            # 提取各个部分
            sections = self._split_into_sections(content)

            if 'abstract' in sections:
                structured['abstract'] = sections['abstract'].strip()

            if 'claims' in sections:
                claims_text = sections['claims']
                structured['claims'] = self._parse_claims(claims_text)

            if 'description' in sections:
                structured['description'] = sections['description'].strip()

            def extract_claims_block(text: str) -> str:
                lines = [ln.strip() for ln in (text or "").split("\n")]
                start = None
                for i, ln in enumerate(lines):
                    if re.match(r"^1[\.、]\s*\S", ln) or re.match(r"^1[\.、]$", ln):
                        start = i
                        break
                if start is None:
                    return ""
                end = len(lines)
                for j in range(start + 1, len(lines)):
                    ln = lines[j]
                    if re.match(r"^(技术领域|背景技术|发明内容|实用新型内容|具体实施方式|附图说明|说明书|实施例)\s*$", ln):
                        end = j
                        break
                return "\n".join(lines[start:end]).strip()

            def improve_abstract_and_description(text: str) -> tuple[str, str]:
                lines = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
                if not lines:
                    return "", ""
                claim_start = None
                for i, ln in enumerate(lines):
                    if re.match(r"^1[\.、]\s*\S", ln) or re.match(r"^1[\.、]$", ln):
                        claim_start = i
                        break
                abstract_text = ""
                if claim_start is not None and claim_start > 0:
                    abstract_text = "\n".join(lines[:claim_start]).strip()
                if not abstract_text:
                    for i, ln in enumerate(lines[:60]):
                        if ln.startswith("摘要"):
                            j = i + 1
                            while j < len(lines) and j < i + 25:
                                if re.match(r"^(权利要求书|权利要求|技术领域|背景技术|说明书)\s*$", lines[j]):
                                    break
                                j += 1
                            abstract_text = "\n".join(lines[i:j]).strip()
                            break
                desc_start = None
                for i, ln in enumerate(lines):
                    if ln == "技术领域":
                        desc_start = i
                        break
                if desc_start is None:
                    if claim_start is not None:
                        desc_start = claim_start
                description_text = "\n".join(lines[desc_start:]).strip() if desc_start is not None else ""
                return abstract_text[:800].strip(), description_text[:4000].strip()

            abstract_bad = (
                not (structured.get('abstract') or '').strip()
                or len((structured.get('abstract') or '').strip()) < 30
                or '附图' in (structured.get('abstract') or '')
                or re.fullmatch(r"\d+(\s*\n\s*\d+)*", (structured.get('abstract') or '').strip()) is not None
            )
            claims_bad = (
                not structured.get('claims')
                or all(not (c.get('content') or '').strip() for c in (structured.get('claims') or []))
            )
            description_bad = (
                not (structured.get('description') or '').strip()
                or len((structured.get('description') or '').strip()) < 80
                or '附图' in (structured.get('description') or '')
            )

            if claims_bad:
                claims_block = extract_claims_block(content)
                if claims_block:
                    structured['claims'] = self._parse_claims(claims_block)

            if abstract_bad or description_bad:
                improved_abstract, improved_description = improve_abstract_and_description(content)
                if abstract_bad and improved_abstract:
                    structured['abstract'] = improved_abstract
                if description_bad and improved_description:
                    structured['description'] = improved_description

            # 如果没有找到明确的结构化部分，尝试从全文中提取
            if not any([structured['abstract'], structured['claims'], structured['description']]):
                logger.warning("未能找到明确的文档结构，尝试智能识别")
                structured = self._smart_extract(content, structured)

        except Exception as e:
            logger.error(f"结构化提取失败: {str(e)}")

        return structured

    def _extract_title(self, content: str) -> Optional[str]:
        """提取文档标题"""
        lines = content.split('\n')
        for i, line in enumerate(lines[:50]):
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                # 检查是否包含标题关键词
                for pattern in self.section_patterns['title']:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(1).strip()

                # 如果第一行看起来像标题（不包含常见段落词汇）
                if '一种' in line and len(line) < 60 and not any(word in line for word in ['摘要', '技术领域', '背景技术', '说明书', '权利要求', '附图']):
                    return line

                if i == 0 and not any(word in line for word in ['本发明', '本实用新型', '所述', '包括', '涉及']):
                    cjk = sum(1 for ch in line if "\u4e00" <= ch <= "\u9fff")
                    if cjk / max(len(line), 1) >= 0.3:
                        return line

        return None

    def _split_into_sections(self, content: str) -> Dict[str, str]:
        """将文档分割为不同部分"""
        sections = {}
        current_section = None
        current_content = []

        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是章节标题
            section_found = False
            for section_name, patterns in self.section_patterns.items():
                if section_name == 'title':
                    continue  # 标题已经单独处理

                for pattern in patterns:
                    if re.match(pattern, line):
                        # 保存当前部分
                        if current_section and current_content:
                            sections[current_section] = '\n'.join(current_content)

                        # 开始新部分
                        current_section = section_name
                        current_content = []
                        section_found = True
                        break

                if section_found:
                    break

            if not section_found and current_section:
                current_content.append(line)

        # 保存最后的部分
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _parse_claims(self, claims_text: str) -> list:
        """解析权利要求书"""
        claims = []
        lines = claims_text.split('\n')

        current_claim = []
        claim_number = 0

        for line in lines:
            line = line.strip()

            # 匹配权利要求编号
            claim_match = re.match(r'^(\d+)\.?\s*(.*)', line)
            if claim_match:
                # 保存前一个权利要求
                if current_claim:
                    claims.append({
                        'number': claim_number,
                        'content': ' '.join(current_claim).strip()
                    })

                # 开始新的权利要求
                claim_number = int(claim_match.group(1))
                current_claim = [claim_match.group(2)]
            else:
                # 检查是否是从属权利要求
                dependent_match = re.match(r'^\s*(\d+)\.?\s*根据权利要求(\d+)(.*)', line)
                if dependent_match and current_claim:
                    # 这是当前权利要求的延续
                    current_claim.append(line)
                elif current_claim:
                    current_claim.append(line)

        # 保存最后一个权利要求
        if current_claim:
            claims.append({
                'number': claim_number,
                'content': ' '.join(current_claim).strip()
            })

        return claims

    def _smart_extract(self, content: str, structured: Dict[str, Any]) -> Dict[str, Any]:
        """智能提取（当明确的结构化识别失败时）"""
        lines = content.split('\n')

        # 尝试找到权利要求
        claims_found = False
        for i, line in enumerate(lines):
            if '权利要求' in line:
                # 提取权利要求部分
                claims_section = []
                for j in range(i, len(lines)):
                    line = lines[j].strip()
                    if line and (re.match(r'^\d+\.', line) or '权利要求' in line or any(claim in line for claim in claims_section)):
                        claims_section.append(line)
                    elif claims_section and not line.startswith(' '):
                        break

                if claims_section:
                    structured['claims'] = self._parse_claims('\n'.join(claims_section))
                    claims_found = True
                break

        # 尝试找到摘要或技术方案
        for line in lines[:50]:  # 只检查前50行
            if any(keyword in line for keyword in ['摘要', '技术方案', '本发明涉及']):
                if not structured['abstract']:
                    structured['abstract'] = line
                break

        return structured

    def _get_sections_info(self, structured_content: Dict[str, Any]) -> Dict[str, Any]:
        """获取文档各部分的信息"""
        sections_info = {
            'has_title': bool(structured_content.get('title')),
            'has_abstract': bool(structured_content.get('abstract')),
            'has_claims': len(structured_content.get('claims', [])) > 0,
            'claims_count': len(structured_content.get('claims', [])),
            'has_description': bool(structured_content.get('description')),
            'content_length': len(structured_content.get('description', '')),
            'parsing_quality': self._assess_parsing_quality(structured_content)
        }

        return sections_info

    def _assess_parsing_quality(self, structured_content: Dict[str, Any]) -> str:
        """评估解析质量"""
        score = 0

        if structured_content.get('title'):
            score += 20
        if structured_content.get('abstract'):
            score += 25
        if len(structured_content.get('claims', [])) > 0:
            score += 35
        if structured_content.get('description'):
            score += 20

        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        else:
            return 'poor'

    async def close(self):
        """关闭解析器"""
        self.executor.shutdown(wait=True)


# 全局解析器实例
document_parser = PatentDocumentParser()
