"""Local storage service — manage local novel files + DB index sync."""
import logging
import os
import json
import re
from typing import Any
from datetime import datetime

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.local")

INDEX_FILENAME = ".novel-index.json"

CHAPTER_PATTERN = re.compile(r"第(\d+)章")
CHAPTER_FILE_PATTERN = re.compile(r"ch(\d+)_")


class LocalService:
    """本地文件管理服务：扫描、读取、写入、索引同步"""

    def __init__(self, db: Database):
        self._db = db

    # ========== 项目注册 ==========

    async def register_project(self, project_id: str, local_root: str) -> dict[str, Any]:
        """注册本地项目目录"""
        local_root = os.path.normpath(local_root)
        if not os.path.isdir(local_root):
            raise ValueError(f"目录不存在: {local_root}")

        await self._db.connect()
        await self._db.execute(
            """INSERT INTO local_projects (project_id, local_root)
               VALUES ($1, $2)
               ON CONFLICT (project_id) DO UPDATE SET local_root = $2, updated_at = NOW()""",
            project_id, local_root,
        )
        return {"project_id": project_id, "local_root": local_root}

    async def get_project(self, project_id: str) -> dict[str, Any] | None:
        """获取本地项目信息"""
        await self._db.connect()
        row = await self._db.fetchrow(
            "SELECT * FROM local_projects WHERE project_id = $1", project_id
        )
        return row_to_dict(row) if row else None

    async def list_projects(self) -> list[dict[str, Any]]:
        """列出所有注册的本地项目"""
        await self._db.connect()
        rows = await self._db.fetch("SELECT * FROM local_projects ORDER BY updated_at DESC")
        return rows_to_dicts(rows)

    # ========== 目录扫描 ==========

    async def scan_directory(self, project_id: str, local_root: str) -> dict[str, Any]:
        """扫描本地目录，构建索引"""
        local_root = os.path.normpath(local_root)
        if not os.path.isdir(local_root):
            raise ValueError(f"目录不存在: {local_root}")

        result = {
            "chapters": [],
            "settings": [],
            "reviews": [],
            "file_count": 0,
            "total_words": 0,
        }

        # 扫描章节目录
        for entry in sorted(os.listdir(local_root)):
            entry_path = os.path.join(local_root, entry)
            if not os.path.isdir(entry_path):
                continue

            match = CHAPTER_PATTERN.match(entry)
            if match:
                chapter_no = int(match.group(1))
                chapter_data = await self._scan_chapter(entry_path, chapter_no, project_id)
                result["chapters"].append(chapter_data)
                result["total_words"] += chapter_data.get("word_count", 0)

            # 扫描设定目录
            if entry == "小说设定":
                settings = await self._scan_settings(entry_path, project_id)
                result["settings"] = settings

        result["file_count"] = sum(
            len(os.listdir(os.path.join(local_root, d)))
            for d in os.listdir(local_root)
            if os.path.isdir(os.path.join(local_root, d))
        )

        # 更新 DB 索引
        await self._sync_to_db(project_id, local_root, result)

        # 写入 .novel-index.json
        index_path = os.path.join(local_root, INDEX_FILENAME)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": "1.0",
                "project_id": project_id,
                "last_sync": datetime.now().isoformat(),
                "chapters": {str(c["chapter_no"]): c for c in result["chapters"]},
                "settings": result["settings"],
            }, f, ensure_ascii=False, indent=2)

        return result

    async def _scan_chapter(self, chapter_path: str, chapter_no: int, project_id: str) -> dict[str, Any]:
        """扫描单个章节目录"""
        data = {"chapter_no": chapter_no, "project_id": project_id, "files": {}}

        for fname in os.listdir(chapter_path):
            fpath = os.path.join(chapter_path, fname)
            rel_path = os.path.relpath(fpath, os.path.dirname(chapter_path))

            if fname.endswith(".md"):
                size = os.path.getsize(fpath)
                word_count = self._count_chinese_words(fpath)

                if "outline" in fname.lower():
                    data["files"]["outline"] = rel_path
                    data["outline_path"] = rel_path
                    data["outline_summary"] = self._extract_summary(fpath)
                elif "draft" in fname.lower():
                    data["files"]["draft"] = rel_path
                    data["draft_word_count"] = word_count
                elif "final" in fname.lower():
                    data["files"]["final"] = rel_path
                    data["word_count"] = word_count
                    data["status"] = "final"
                    data["summary"] = self._extract_summary(fpath)
                elif "revision" in fname.lower():
                    data.setdefault("revisions", []).append(rel_path)

            # 扫描审查报告
            if fname == "审查报告" and os.path.isdir(fpath):
                reviews = await self._scan_reviews(fpath, chapter_no, project_id)
                data["reviews"] = reviews

        if not data.get("status"):
            if data.get("files", {}).get("draft"):
                data["status"] = "draft"
            else:
                data["status"] = "planned"

        if not data.get("title"):
            data["title"] = f"第{chapter_no}章"

        return data

    async def _scan_settings(self, settings_path: str, project_id: str) -> list[dict[str, Any]]:
        """扫描设定目录"""
        settings = []
        for subdir in os.listdir(settings_path):
            sub_path = os.path.join(settings_path, subdir)
            if not os.path.isdir(sub_path):
                continue

            category = self._map_category(subdir)
            for fname in os.listdir(sub_path):
                fpath = os.path.join(sub_path, fname)
                rel_path = os.path.relpath(fpath, os.path.dirname(settings_path))

                if fname.endswith(".json"):
                    with open(fpath, "r", encoding="utf-8") as f:
                        try:
                            structured = json.load(f)
                        except json.JSONDecodeError:
                            structured = {}
                    settings.append({
                        "category": category,
                        "name": fname.replace(".json", ""),
                        "local_path": rel_path,
                        "structured_data": structured,
                        "summary": str(structured)[:500],
                    })
                elif fname.endswith(".md"):
                    settings.append({
                        "category": category,
                        "name": fname.replace(".md", ""),
                        "local_path": rel_path,
                        "summary": self._extract_summary(fpath),
                        "keywords": self._extract_keywords(fpath),
                    })

        return settings

    async def _scan_reviews(self, review_path: str, chapter_no: int, project_id: str) -> list[dict[str, Any]]:
        """扫描审查报告目录"""
        reviews = []
        for fname in os.listdir(review_path):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(review_path, fname)
            rel_path = os.path.relpath(fpath, os.path.dirname(review_path))

            reviews.append({
                "chapter_no": chapter_no,
                "model_name": fname.replace("_report.md", "").replace(".md", ""),
                "local_path": rel_path,
                "summary": self._extract_summary(fpath),
            })

        return reviews

    # ========== DB 同步 ==========

    async def _sync_to_db(self, project_id: str, local_root: str, scan_result: dict[str, Any]):
        """将扫描结果同步到 DB 索引"""
        await self._db.connect()

        # 更新项目注册
        await self._db.execute(
            """INSERT INTO local_projects (project_id, local_root, file_count, total_words, chapter_count, last_scan_at)
               VALUES ($1, $2, $3, $4, $5, NOW())
               ON CONFLICT (project_id) DO UPDATE SET
                 file_count = $3, total_words = $4, chapter_count = $5, last_scan_at = NOW(), updated_at = NOW()""",
            project_id, local_root,
            scan_result["file_count"],
            scan_result["total_words"],
            len(scan_result["chapters"]),
        )

        # 同步章节索引
        for ch in scan_result["chapters"]:
            await self._db.execute(
                """INSERT INTO chapter_index (project_id, chapter_no, title, status, word_count, summary, local_path, outline_path)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   ON CONFLICT (project_id, chapter_no) DO UPDATE SET
                     title = $3, status = $4, word_count = $5, summary = $6,
                     local_path = $7, outline_path = $8, updated_at = NOW()""",
                project_id,
                ch["chapter_no"],
                ch.get("title"),
                ch.get("status", "planned"),
                ch.get("word_count", 0),
                ch.get("summary"),
                ch.get("files", {}).get("final") or ch.get("files", {}).get("draft"),
                ch.get("outline_path"),
            )

        # 同步设定索引
        for s in scan_result["settings"]:
            await self._db.execute(
                """INSERT INTO setting_index (project_id, category, name, keywords, summary, local_path, structured_data)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT DO NOTHING""",
                project_id,
                s.get("category"),
                s.get("name"),
                s.get("keywords", []),
                s.get("summary"),
                s.get("local_path"),
                ensure_json_value(s.get("structured_data")),
            )

    # ========== 文件读写 ==========

    async def read_file(self, local_root: str, relative_path: str) -> str:
        """读取本地文件内容"""
        full_path = os.path.normpath(os.path.join(local_root, relative_path))
        if not full_path.startswith(os.path.normpath(local_root)):
            raise ValueError("路径越界")
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    async def write_file(self, local_root: str, relative_path: str, content: str) -> dict[str, Any]:
        """写入本地文件"""
        full_path = os.path.normpath(os.path.join(local_root, relative_path))
        if not full_path.startswith(os.path.normpath(local_root)):
            raise ValueError("路径越界")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"path": relative_path, "size": len(content), "word_count": self._count_chinese_words_from_text(content)}

    # ========== 章节列表 ==========

    async def list_chapters(self, project_id: str, status: str | None = None, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """从 DB 索引获取章节列表"""
        await self._db.connect()
        if status:
            rows = await self._db.fetch(
                "SELECT * FROM chapter_index WHERE project_id = $1 AND status = $2 ORDER BY chapter_no LIMIT $3 OFFSET $4",
                project_id, status, limit, offset,
            )
        else:
            rows = await self._db.fetch(
                "SELECT * FROM chapter_index WHERE project_id = $1 ORDER BY chapter_no LIMIT $2 OFFSET $3",
                project_id, limit, offset,
            )
        return rows_to_dicts(rows)

    async def get_chapter(self, project_id: str, chapter_no: int) -> dict[str, Any] | None:
        """获取章节元数据"""
        await self._db.connect()
        row = await self._db.fetchrow(
            "SELECT * FROM chapter_index WHERE project_id = $1 AND chapter_no = $2",
            project_id, chapter_no,
        )
        return row_to_dict(row) if row else None

    async def get_chapter_content(self, project_id: str, chapter_no: int, version: str = "final") -> str | None:
        """读取章节正文（从本地文件）"""
        project = await self.get_project(project_id)
        if not project:
            raise ValueError("项目未注册")
        chapter = await self.get_chapter(project_id, chapter_no)
        if not chapter:
            return None
        local_path = chapter.get(f"{version}_path") or chapter.get("local_path")
        if not local_path:
            return None
        return await self.read_file(project["local_root"], local_path)

    # ========== 审查 ==========

    async def list_reviews(self, project_id: str, chapter_no: int | None = None) -> list[dict[str, Any]]:
        """从 DB 索引获取审查列表"""
        await self._db.connect()
        if chapter_no:
            rows = await self._db.fetch(
                "SELECT * FROM review_index WHERE project_id = $1 AND chapter_no = $2 ORDER BY created_at DESC",
                project_id, chapter_no,
            )
        else:
            rows = await self._db.fetch(
                "SELECT * FROM review_index WHERE project_id = $1 ORDER BY created_at DESC",
                project_id,
            )
        return rows_to_dicts(rows)

    async def get_review_content(self, project_id: str, review_id: str) -> str | None:
        """读取审查报告全文"""
        row = await self._db.fetchrow("SELECT * FROM review_index WHERE id = $1", review_id)
        if not row:
            return None
        project = await self.get_project(project_id)
        if not project or not row.get("local_path"):
            return None
        return await self.read_file(project["local_root"], row["local_path"])

    # ========== 工具方法 ==========

    def _count_chinese_words(self, filepath: str) -> int:
        """统计中文字数"""
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        return self._count_chinese_words_from_text(text)

    def _count_chinese_words_from_text(self, text: str) -> int:
        """从文本统计中文字数"""
        return len(re.findall(r"[\u4e00-\u9fff]", text))

    def _extract_summary(self, filepath: str, max_len: int = 500) -> str:
        """提取文件摘要（前500字）"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read().strip()
            # 跳过 YAML front matter
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    text = parts[2].strip()
            return text[:max_len]
        except Exception:
            return ""

    def _extract_keywords(self, filepath: str) -> list[str]:
        """提取关键词（从 YAML front matter）"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 2:
                    import yaml
                    meta = yaml.safe_load(parts[1])
                    if meta and "keywords" in meta:
                        return meta["keywords"] if isinstance(meta["keywords"], list) else []
        except Exception:
            pass
        return []

    def _map_category(self, dirname: str) -> str:
        """目录名 → category"""
        mapping = {
            "人物设定": "character",
            "世界规则": "world",
            "势力关系": "faction",
            "写作技巧": "technique",
            "设定": "rule",
        }
        return mapping.get(dirname, "other")
