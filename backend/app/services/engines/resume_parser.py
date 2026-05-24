"""简历文件解析引擎 - PDF/DOCX."""
import os
from pathlib import Path

from app.config import Config


class ResumeParser:
    """从简历文件中提取纯文本."""

    def extract_text(self, file_path: str, ext: str) -> str:
        ext = ext.lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path)
        if ext in (".docx",):
            return self._parse_docx(file_path)
        if ext == ".doc":
            raise ValueError("暂不支持旧版 .doc，请转换为 PDF 或 DOCX")
        raise ValueError(f"不支持的格式: {ext}")

    def _parse_pdf(self, path: str) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(path)
            parts = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
            text = "\n".join(parts).strip()
            if not text or len(text) < 20:
                raise ValueError("PDF 文本提取失败或内容过少")
            return text
        except Exception as e:
            raise ValueError(f"PDF 解析失败: {e}") from e

    def _parse_docx(self, path: str) -> str:
        try:
            from docx import Document

            doc = Document(path)
            parts = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(parts).strip()
            if len(text) < 20:
                raise ValueError("DOCX 内容过少")
            return text
        except Exception as e:
            raise ValueError(f"DOCX 解析失败: {e}") from e

    @staticmethod
    def validate_file(filename: str, file_bytes: bytes) -> str:
        """校验扩展名与文件头，返回安全扩展名."""
        ext = Path(filename).suffix.lower()
        if ext not in Config.ALLOWED_RESUME_EXT:
            raise ValueError("仅支持 PDF、DOCX、DOC 格式")
        if len(file_bytes) > Config.MAX_CONTENT_LENGTH:
            raise ValueError("文件超过 10MB 限制")
        # magic bytes
        if ext == ".pdf" and not file_bytes[:4] == b"%PDF":
            raise ValueError("PDF 文件头校验失败")
        if ext == ".docx" and file_bytes[:2] != b"PK":
            raise ValueError("DOCX 文件头校验失败")
        return ext

    @staticmethod
    def save_upload(user_id: int, filename: str, content: bytes) -> str:
        """保存到私有简历目录，避免通过公开 uploads 路由暴露."""
        ext = Path(filename).suffix.lower()
        folder = Path(Config.RESUME_UPLOAD_FOLDER) / str(user_id)
        folder.mkdir(parents=True, exist_ok=True)
        safe_name = f"resume_{os.urandom(4).hex()}{ext}"
        path = folder / safe_name
        path.write_bytes(content)
        return str(path)
