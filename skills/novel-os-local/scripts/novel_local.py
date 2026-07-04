#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from uuid import uuid4

# ============================================================================
# 本地目录结构规范
# ============================================================================

LOCAL_DIR_STRUCTURE = {
    ".novel-os": "配置、元数据、内部状态",
    "设定集": "人物设定、势力设定、地点设定、世界观设定",
    "设定集/人物": "各人物详细设定",
    "设定集/势力": "各势力详细设定",
    "设定集/地点": "地点、场景详细设定",
    "设定集/道具": "重要道具详细设定",
    "大纲": "整体大纲、卷大纲、章大纲",
    "大纲/卷大纲": "各卷大纲",
    "大纲/章节": "各章节大纲",
    "细纲": "章节细纲、情节点",
    "正文": "已确认的正文文件",
    "草稿": "AI 生成的草稿",
    "审查报告": "审查模型输出报告",
    "导出": "导出的打包文件",
}

# 章节文件命名规范: chXXXX.md (如 ch0001.md)
CHAPTER_PATTERN = re.compile(r"^ch(\d{4})\.md$")
# 卷目录命名规范: volume_XXX (如 volume_001)
VOLUME_PATTERN = re.compile(r"^volume_(\d{3})$")
# 设定文件命名规范: [类型]_[名称].md (如 人物_张三.md)
SETTING_PATTERN = re.compile(r"^\[?\w+\]?_\w+\.md$")

# ============================================================================
# 上下文缓存
# ============================================================================

CONTEXT_CACHE_DIR = ".novel-os" / "context-cache"
CONTEXT_INDEX_FILE = ".novel-os" / "context-cache" / "index.json"
CONTEXT_MAX_CACHED = 50  # 最多缓存多少个上下文


def get_context_cache_path(root: Path, chapter_no: int) -> Path:
    """获取指定章节的缓存路径。"""
    return root / str(CONTEXT_CACHE_DIR) / f"ch{chapter_no:04d}.context.json"


def load_context_cache_index(root: Path) -> dict[str, Any]:
    """加载上下文缓存索引。"""
    index_path = root / CONTEXT_INDEX_FILE
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return {"cached": [], "last_updated": None}


def save_context_cache_index(root: Path, index: dict[str, Any]) -> None:
    """保存上下文缓存索引。"""
    index_path = root / CONTEXT_INDEX_FILE
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index["last_updated"] = __import__("datetime").datetime.now().isoformat()
    save_json(index_path, index)


def cache_context(root: Path, chapter_no: int, context_pack: dict[str, Any]) -> None:
    """缓存上下文到本地。"""
    cache_path = get_context_cache_path(root, chapter_no)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(cache_path, context_pack)

    # 更新索引
    index = load_context_cache_index(root)
    cache_entry = {
        "chapter_no": chapter_no,
        "cache_file": str(cache_path.relative_to(root)),
        "cached_at": __import__("datetime").datetime.now().isoformat(),
        "chapter_no_str": f"ch{chapter_no:04d}",
    }

    # 移除旧条目（如果存在）
    index["cached"] = [c for c in index["cached"] if c["chapter_no"] != chapter_no]
    # 添加到最前面
    index["cached"].insert(0, cache_entry)

    # 限制缓存数量
    if len(index["cached"]) > CONTEXT_MAX_CACHED:
        removed = index["cached"][CONTEXT_MAX_CACHED:]
        index["cached"] = index["cached"][:CONTEXT_MAX_CACHED]
        # 删除多余缓存文件
        for entry in removed:
            old_path = root / entry["cache_file"]
            if old_path.exists():
                old_path.unlink()

    save_context_cache_index(root, index)


def get_cached_context(root: Path, chapter_no: int) -> dict[str, Any] | None:
    """获取缓存的上下文，如果不存在返回 None。"""
    cache_path = get_context_cache_path(root, chapter_no)
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    return None


def list_cached_contexts(root: Path) -> list[dict[str, Any]]:
    """列出所有缓存的上下文。"""
    index = load_context_cache_index(root)
    return index.get("cached", [])


def clear_context_cache(root: Path, chapter_no: int | None = None) -> int:
    """清除指定章节的缓存，或全部缓存（chapter_no 为 None）。返回清除的数量。"""
    if chapter_no is not None:
        cache_path = get_context_cache_path(root, chapter_no)
        if cache_path.exists():
            cache_path.unlink()
        # 更新索引
        index = load_context_cache_index(root)
        index["cached"] = [c for c in index["cached"] if c["chapter_no"] != chapter_no]
        save_context_cache_index(root, index)
        return 1
    else:
        # 清除所有
        cache_dir = root / CONTEXT_CACHE_DIR
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
        index = {"cached": [], "last_updated": __import__("datetime").datetime.now().isoformat()}
        save_context_cache_index(root, index)
        return len(list_cached_contexts(root))  # 返回清除前的数量


# ============================================================================
# 离线提交队列
# ============================================================================

OFFLINE_QUEUE_FILE = ".novel-os" / "offline-queue.json"
MAX_QUEUE_SIZE = 100


def load_offline_queue(root: Path) -> list[dict[str, Any]]:
    """加载离线提交队列。"""
    queue_path = root / OFFLINE_QUEUE_FILE
    if queue_path.exists():
        return json.loads(queue_path.read_text(encoding="utf-8"))
    return []


def save_offline_queue(root: Path, queue: list[dict[str, Any]]) -> None:
    """保存离线提交队列。"""
    queue_path = root / OFFLINE_QUEUE_FILE
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(queue_path, queue)


def queue_offline_commit(root: Path, commit_data: dict[str, Any]) -> None:
    """将提交加入离线队列。"""
    queue = load_offline_queue(root)

    # 检查是否已存在相同章节的待同步提交
    chapter_no = commit_data.get("chapter_no")
    queue = [c for c in queue if c.get("chapter_no") != chapter_no]

    # 添加新提交
    commit_data["queued_at"] = __import__("datetime").datetime.now().isoformat()
    commit_data["status"] = "pending"
    queue.insert(0, commit_data)

    # 限制队列大小
    if len(queue) > MAX_QUEUE_SIZE:
        queue = queue[:MAX_QUEUE_SIZE]

    save_offline_queue(root, queue)


def sync_offline_queue(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """同步离线提交队列到 MCP。返回同步结果。"""
    queue = load_offline_queue(root)
    if not queue:
        return {"synced": 0, "failed": 0, "remaining": 0}

    client = make_client(config)
    synced = 0
    failed = 0
    errors = []

    # 按时间顺序同步（先提交的先同步）
    for item in queue:
        try:
            result = client.call_tool(
                "workflow.submit_chapter_commit",
                {
                    "workspace": config["workspace"],
                    "project": config["project"],
                    "chapter_no": item["chapter_no"],
                    "title": item["title"],
                    "local_files": item.get("local_files", []),
                    "commit": item.get("commit", {}),
                    "accept": item.get("accept", True),
                },
            )
            synced += 1
        except Exception as exc:
            failed += 1
            errors.append({"chapter_no": item["chapter_no"], "error": str(exc)})

    # 更新队列，移除成功的提交
    remaining = [q for i, q in enumerate(queue) if i >= synced]

    # 如果有失败，保留失败的条目
    if failed > 0:
        # 保留失败的条目到队列末尾
        failed_items = queue[synced:synced + failed]
        remaining = remaining + failed_items

    save_offline_queue(root, remaining)

    return {
        "synced": synced,
        "failed": failed,
        "remaining": len(remaining),
        "errors": errors,
    }

# ============================================================================


DEFAULT_DIRS = [
    ".novel-os",
    "设定集/人物",
    "设定集/势力",
    "设定集/地点",
    "设定集/道具",
    "大纲/卷大纲",
    "大纲/章节",
    "细纲",
    "正文",
    "草稿",
    "审查报告",
    "导出",
]


def validate_local_structure(root: Path) -> dict[str, Any]:
    """验证本地项目目录结构，返回缺失和多余的目录/文件列表。"""
    missing_dirs = []
    unexpected_items = []
    structure_errors = []

    for rel_path, desc in LOCAL_DIR_STRUCTURE.items():
        full_path = root / rel_path
        if not full_path.exists():
            missing_dirs.append({"path": rel_path, "description": desc})

    # 检查非标准目录/文件（排除 .git 等）
    for item in root.rglob("*"):
        if item.is_relative_to(root / ".novel-os"):
            continue
        if item.name in (".git", "__pycache__", "node_modules", ".DS_Store", "Thumbs.db"):
            continue

        rel = item.relative_to(root)
        rel_str = str(rel).replace("\\", "/")

        # 检查章节文件命名
        if item.is_file() and item.suffix == ".md":
            parent = item.parent.relative_to(root)
            parent_str = str(parent).replace("\\", "/")

            if parent_str == "正文":
                m = CHAPTER_PATTERN.match(item.name)
                if not m:
                    structure_errors.append({
                        "path": rel_str,
                        "error": "正文目录下文件应命名为 chXXXX.md 格式",
                        "hint": f"当前: {item.name}",
                    })

            elif parent_str.startswith("设定集"):
                if not SETTING_PATTERN.match(item.name):
                    structure_errors.append({
                        "path": rel_str,
                        "error": "设定集文件命名建议使用 [类型]_[名称].md 格式",
                        "hint": f"当前: {item.name}",
                    })

        # 检查卷目录
        if item.is_dir() and item.name.startswith("volume_"):
            m = VOLUME_PATTERN.match(item.name)
            if not m:
                structure_errors.append({
                    "path": rel_str,
                    "error": "卷目录应命名为 volume_XXX 格式（三位数字）",
                    "hint": f"当前: {item.name}",
                })

    return {
        "valid": len(missing_dirs) == 0 and len(structure_errors) == 0,
        "missing_dirs": missing_dirs,
        "structure_errors": structure_errors,
    }


def generate_local_manifest(root: Path, include_drafts: bool = False) -> dict[str, Any]:
    """生成本地项目 manifest，记录所有文件的哈希值。"""
    manifest = {
        "version": 1,
        "project_root": str(root),
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "files": [],
    }

    for item in root.rglob("*"):
        if not item.is_file():
            continue

        # 跳过 .novel-os 内部文件
        if item.is_relative_to(root / ".novel-os"):
            if item.name.startswith(".") or item.suffix in (".json", ".lock"):
                continue

        # 跳过草稿（除非明确包含）
        if not include_drafts:
            rel = item.relative_to(root)
            if str(rel).startswith("草稿/"):
                continue

        if item.name in (".DS_Store", "Thumbs.db"):
            continue

        rel = item.relative_to(root)
        manifest["files"].append({
            "path": str(rel).replace("\\", "/"),
            "size": item.stat().st_size,
            "sha256": sha256_file(item),
        })

    return manifest


def create_local_structure(root: Path, force: bool = False) -> list[str]:
    """创建标准目录结构，返回创建的目录列表。"""
    created = []
    for rel_path in LOCAL_DIR_STRUCTURE.keys():
        full_path = root / rel_path
        if force or not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(rel_path)
    return created

TEXT_IMPORT_SUFFIXES = {".md", ".markdown", ".txt", ".json", ".csv", ".yaml", ".yml"}

DEFAULT_MODEL_ID = "gpt-4.1"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_API_KEY_ENVS = ["NOVEL_OS_MODEL_API_KEY", "OPENAI_API_KEY", "API_KEY"]
DEFAULT_EMBEDDING_MODEL_ID = "text-embedding-3-small"

REVIEW_MODELS_EXAMPLE = {
    "models": [
        {
            "id": "consistency-reviewer",
            "name": "一致性审查",
            "description": "审查世界观、人物设定、时间线的一致性",
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4.1",
            "temperature": 0.1,
            "max_tokens": 2000,
            "dimensions": ["consistency", "world_logic"],
        },
        {
            "id": "style-reviewer",
            "name": "文风审查",
            "description": "审查文风、表达、对话质量",
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4.1",
            "temperature": 0.2,
            "max_tokens": 2000,
            "dimensions": ["writing_style", "dialogue", "prose"],
        },
        {
            "id": "pacing-reviewer",
            "name": "节奏审查",
            "description": "审查节奏、爽点、高潮设计",
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4.1",
            "temperature": 0.3,
            "max_tokens": 2000,
            "dimensions": ["pacing", "reader_pull", "climax"],
        },
        {
            "id": "foreshadowing-reviewer",
            "name": "伏笔审查",
            "description": "审查伏笔铺设与回收",
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4.1",
            "temperature": 0.2,
            "max_tokens": 2000,
            "dimensions": ["foreshadowing_setup", "payoff", "coherence"],
        },
    ]
}

MODEL_CONFIG_EXAMPLE = {
    "providers": {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY"
        },
        "openai_compatible": {
            "base_url": "https://example-openai-compatible-endpoint/v1",
            "api_key_env": "COMPATIBLE_API_KEY"
        }
    },
    "profiles": {
        "outline": [
            {
                "id": "outline-main",
                "provider": "openai",
                "model": "gpt-4.1",
                "temperature": 0.7,
                "max_tokens": 5000
            }
        ],
        "draft": [
            {
                "id": "draft-main",
                "provider": "openai",
                "model": "gpt-4.1",
                "temperature": 0.8,
                "max_tokens": 8000
            }
        ],
        "review": [
            {
                "id": "default-reviewer",
                "provider": "openai",
                "model": "gpt-4.1",
                "temperature": 0.2,
                "max_tokens": 2000
            }
        ],
        "embedding": [
            {
                "id": "embedding-main",
                "provider": "openai",
                "model": "text-embedding-3-small"
            }
        ]
    }
}

NOVEL_OS_PACK_EXAMPLE = {
    "items": [
        {
            "item_type": "trope",
            "key": "example_trope",
            "title": "Example Trope",
            "content": "Describe a reusable trope, pattern, prompt, or writing technique here.",
            "metadata": {"tags": ["example"]},
        }
    ],
    "rules": [
        {
            "rule_key": "example.style.rule",
            "rule_type": "style",
            "title": "Example Style Rule",
            "content": "Rules imported here become active project data and can evolve without MCP code changes.",
            "severity": "warning",
        }
    ],
    "review_councils": [
        {
            "name": "default-review-council",
            "is_active": True,
            "config": {
                "dimensions": ["consistency", "ooc", "pacing", "reader_pull", "foreshadowing"],
                "models": [
                    {"id": "default-reviewer", "role": "full_review"},
                ],
            },
        }
    ],
}

INITIAL_PROJECT_PACK_EXAMPLE = {
    "version": 1,
    "canon_documents": [
        {
            "doc_type": "world",
            "key": "world_overview",
            "title": "World Overview",
            "content": "Describe the world setting here.",
            "status": "active",
        },
        {
            "doc_type": "character",
            "key": "protagonist",
            "title": "Protagonist",
            "content": "Describe the main character here.",
            "status": "active",
        },
    ],
    "rules": [
        {
            "rule_key": "style.tone",
            "rule_type": "style",
            "title": "Tone Guideline",
            "content": "Maintain a consistent narrative tone throughout.",
            "severity": "warning",
            "status": "active",
        }
    ],
    "entities": [
        {
            "entity_type": "character",
            "name": "Main Character",
            "core_profile": "The protagonist of the story.",
        }
    ],
    "relationships": [
        {
            "relation_type": "allied",
            "source_name": "Main Character",
            "source_entity_type": "character",
            "target_name": "Support Character",
            "target_entity_type": "character",
            "attitude": "friendly",
            "intensity": 0.8,
        }
    ],
    "plot_threads": [
        {
            "thread_key": "main_quest",
            "title": "Main Quest",
            "thread_type": "main",
            "importance": "critical",
            "status": "open",
        }
    ],
    "foreshadowing": [
        {
            "key": "mysterious_pendant",
            "title": "Mysterious Pendant",
            "status": "planted",
            "importance": "high",
            "layer": "subtle",
        }
    ],
    "volumes": [
        {
            "volume_no": 1,
            "title": "Volume 1: Awakening",
            "status": "planned",
            "start_chapter_no": 1,
            "end_chapter_no": 50,
        }
    ],
    "chapter_plans": [
        {
            "chapter_no": 1,
            "plan": {
                "title": "Chapter 1",
                "summary": "The opening chapter.",
                "beats": [
                    "Introduce protagonist",
                    "Inciting incident",
                    "Hook for next chapter",
                ],
            },
        }
    ],
}


# ============================================================================
# 初始化模板
# ============================================================================

GENRE_TEMPLATE = """# {title} - 题材设定

## 基本信息
- **题材**: {genre}
- **风格**: {style}
- **目标读者**: {target_audience}
- **字数目标**: {word_count_target}

## 核心卖点
1. {selling_point_1}
2. {selling_point_2}
3. {selling_point_3}

## 核心冲突
{core_conflict}

## 参考作品
- {reference_1}
- {reference_2}
- {reference_3}
"""

CHARACTER_TEMPLATE = """# {name} - 人物设定

## 基本信息
- **姓名**: {name}
- **年龄**: {age}
- **性别**: {gender}
- **身份**: {identity}

## 外貌描写
{appearance}

## 性格特点
{personality}

## 背景故事
{backstory}

## 核心目标
{goal}

## 主要矛盾
{conflict}

## 人物弧光
{character_arc}
"""

LOCATION_TEMPLATE = """# {name} - 地点设定

## 基本信息
- **名称**: {name}
- **类型**: {type}
- **重要性**: {importance}

## 外观描述
{appearance}

## 功能区域
{features}

## 氛围特点
{atmosphere}

## 在故事中的作用
{role_in_story}
"""

OUTLINE_TEMPLATE = """# {title} - 大纲模板

## 作品概述
{overview}

## 整体结构
- **总卷数**: {total_volumes}
- **总章节数**: {total_chapters}
- **预计完本字数**: {total_word_count}

## 核心主题
{theme}

## 主线剧情
### 第一阶段: {arc_1_title}
{arc_1_summary}

### 第二阶段: {arc_2_title}
{arc_2_summary}

### 第三阶段: {arc_3_title}
{arc_3_summary}

## 伏笔设计
{foreshadowing}

## 关键情节点
1. **{key_point_1}**: {key_point_1_desc}
2. **{key_point_2}**: {key_point_2_desc}
3. **{key_point_3}**: {key_point_3_desc}
"""


def generate_genre_document(genre: str, title: str) -> str:
    """生成题材设定文档。"""
    return GENRE_TEMPLATE.format(
        title=title,
        genre=genre,
        style="",
        target_audience="",
        word_count_target="",
        selling_point_1="",
        selling_point_2="",
        selling_point_3="",
        core_conflict="",
        reference_1="",
        reference_2="",
        reference_3="",
    )


def generate_character_document(name: str) -> str:
    """生成人物设定文档。"""
    return CHARACTER_TEMPLATE.format(
        name=name,
        age="",
        gender="",
        identity="",
        appearance="",
        personality="",
        backstory="",
        goal="",
        conflict="",
        character_arc="",
    )


def generate_location_document(name: str) -> str:
    """生成地点设定文档。"""
    return LOCATION_TEMPLATE.format(
        name=name,
        type="",
        importance="",
        appearance="",
        features="",
        atmosphere="",
        role_in_story="",
    )


def generate_outline_document(title: str) -> str:
    """生成大纲文档。"""
    return OUTLINE_TEMPLATE.format(
        title=title,
        overview="",
        total_volumes="",
        total_chapters="",
        total_word_count="",
        theme="",
        arc_1_title="",
        arc_1_summary="",
        arc_2_title="",
        arc_2_summary="",
        arc_3_title="",
        arc_3_summary="",
        foreshadowing="",
        key_point_1="",
        key_point_1_desc="",
        key_point_2="",
        key_point_2_desc="",
        key_point_3="",
        key_point_3_desc="",
    )


class McpHttpClient:
    def __init__(self, url: str, bearer_token: str | None = None):
        self.url = url
        self.bearer_token = bearer_token
        self.session_id: str | None = None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
            headers["X-Novel-OS-Token"] = self.bearer_token
        return headers

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.url, data=body, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                sid = resp.headers.get("mcp-session-id")
                if sid:
                    self.session_id = sid
                raw = resp.read().decode("utf-8", errors="replace")
                return parse_mcp_response(raw)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"MCP HTTP {exc.code}: {detail}") from exc

    def initialize(self) -> None:
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "novel-os-local", "version": "0.1.0"},
                },
            }
        )
        if response and response.get("error"):
            raise RuntimeError(response["error"])
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if not self.session_id:
            self.initialize()
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        if response is None:
            return None
        if response.get("error"):
            raise RuntimeError(response["error"])
        result = response.get("result")
        if isinstance(result, dict) and "content" in result:
            return decode_tool_content(result["content"])
        return result


def parse_mcp_response(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if not text:
        return None
    if text.startswith("{"):
        return json.loads(text)
    data_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if data_lines:
        return json.loads("\n".join(data_lines))
    raise RuntimeError(f"Unrecognized MCP response: {text[:300]}")


def decode_tool_content(content: Any) -> Any:
    if not isinstance(content, list) or not content:
        return content
    first = content[0]
    if isinstance(first, dict) and first.get("type") == "text":
        text = first.get("text", "")
        if text.startswith("Error calling tool"):
            raise RuntimeError(text)
        try:
            value = json.loads(text)
            if isinstance(value, str) and value.strip().startswith(("{", "[")):
                return json.loads(value)
            if isinstance(value, str) and value.startswith("Error calling tool"):
                raise RuntimeError(value)
            return value
        except json.JSONDecodeError:
            return text
    return content


def project_file(root: Path) -> Path:
    return root / ".novel-os" / "project.json"


def load_project(root: Path) -> dict[str, Any]:
    path = project_file(root)
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run init first.")
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_project_templates(root: Path, overwrite: bool = False) -> list[str]:
    targets = [
        (root / ".novel-os" / "model-config.example.json", MODEL_CONFIG_EXAMPLE),
        (root / ".novel-os" / "review-models.example.json", REVIEW_MODELS_EXAMPLE),
        (root / ".novel-os" / "novel-os-pack.example.json", NOVEL_OS_PACK_EXAMPLE),
        (root / ".novel-os" / "initial-project-pack.example.json", INITIAL_PROJECT_PACK_EXAMPLE),
    ]
    written = []
    for path, payload in targets:
        if overwrite or not path.exists():
            save_json(path, payload)
            written.append(str(path))
    return written


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_cjk_aware_words(text: str) -> int:
    # Good enough for rough chapter statistics across Chinese and English text.
    return len([ch for ch in text if not ch.isspace()])


def render_context_markdown(pack: dict[str, Any]) -> str:
    sections = ensure_json_value(pack.get("sections", []))
    retrieval_audit = ensure_json_value(pack.get("retrieval_audit", []))
    lines = [f"# Chapter {pack.get('chapter_no')} Context", ""]
    for section in sections:
        if isinstance(section, str):
            section = ensure_json_value(section)
        if not isinstance(section, dict):
            section = {"name": "section", "content": str(section)}
        lines.append(f"## {section.get('name')}")
        lines.append("")
        lines.append(str(section.get("content", "")))
        lines.append("")
    lines.append("## Retrieval Audit")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(retrieval_audit, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def ensure_json_value(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("{", "[")):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return value
    return value


def make_client(config: dict[str, Any]) -> McpHttpClient:
    return McpHttpClient(config["mcp_url"], config.get("api_token"))


def config_from_args_or_root(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "mcp_url", None):
        return {"mcp_url": args.mcp_url, "api_token": getattr(args, "api_token", None)}
    root = Path(getattr(args, "root", ".")).resolve()
    config = load_project(root)
    if getattr(args, "api_token", None):
        config["api_token"] = args.api_token
    return config


def project_config_from_args(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(getattr(args, "root", ".")).resolve()
    config = load_project(root)
    if getattr(args, "api_token", None):
        config["api_token"] = args.api_token
    return config


def cmd_whoami(args: argparse.Namespace) -> None:
    config = config_from_args_or_root(args)
    client = make_client(config)
    result = client.call_tool("auth.whoami", {})
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_token_create(args: argparse.Namespace) -> None:
    config = config_from_args_or_root(args)
    client = make_client(config)
    result = client.call_tool(
        "auth.create_api_token",
        {
            "username": args.username,
            "name": args.name,
            "scopes": args.scope or ["read", "write"],
            "workspace": args.workspace,
            "project": args.project,
            "expires_at": args.expires_at,
        },
    )
    if args.save_to_root:
        root = Path(args.save_to_root).resolve()
        project_config = load_project(root)
        project_config["api_token"] = result["token"]
        save_json(project_file(root), project_config)
        result = dict(result)
        result["saved_to"] = str(project_file(root))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_user_create(args: argparse.Namespace) -> None:
    config = config_from_args_or_root(args)
    client = make_client(config)
    result = client.call_tool(
        "user.create",
        {
            "username": args.username,
            "display_name": args.display_name,
            "email": args.email,
            "status": args.status,
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_workspace_create(args: argparse.Namespace) -> None:
    config = config_from_args_or_root(args)
    client = make_client(config)
    result = client.call_tool("workspace.create", {"slug": args.workspace, "name": args.name})
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_workspace_add_member(args: argparse.Namespace) -> None:
    config = config_from_args_or_root(args)
    client = make_client(config)
    result = client.call_tool(
        "workspace.add_member",
        {"workspace": args.workspace, "username": args.username, "role": args.role},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def write_local_project_config(
    root: Path,
    mcp_url: str,
    workspace: str,
    project: str,
    title: str,
    client_id: str,
    api_token: str | None,
) -> None:
    for item in DEFAULT_DIRS:
        (root / item).mkdir(parents=True, exist_ok=True)
    config = {
        "mcp_url": mcp_url,
        "workspace": workspace,
        "project": project,
        "title": title,
        "client_id": client_id,
        "api_token": api_token,
        "local_root": str(root),
    }
    save_json(project_file(root), config)
    save_json(root / ".novel-os" / "sync-state.json", {"last_context_chapter": None, "last_commit_chapter": None})
    write_project_templates(root, overwrite=False)


def cmd_onboard_project(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    admin_config = config_from_args_or_root(args)
    client = make_client(admin_config)

    user = client.call_tool(
        "user.create",
        {
            "username": args.username,
            "display_name": args.display_name,
            "email": args.email,
            "status": "active",
        },
    )
    workspace = client.call_tool("workspace.create", {"slug": args.workspace, "name": args.workspace_name or args.workspace})
    client.call_tool("workspace.add_member", {"workspace": args.workspace, "username": args.username, "role": args.workspace_role})
    project = client.call_tool(
        "project.create",
        {
            "workspace": args.workspace,
            "slug": args.project,
            "title": args.title,
            "description": args.description,
        },
    )

    client.call_tool("project.add_member", {"workspace": args.workspace, "project": args.project, "username": args.username, "role": args.project_role})
    project_token = client.call_tool(
        "auth.create_api_token",
        {
            "username": args.username,
            "name": args.token_name or f"{args.username}-{args.project}-local",
            "scopes": args.scope or ["read", "write"],
            "workspace": args.workspace,
            "project": args.project,
            "expires_at": args.expires_at,
        },
    )
    write_local_project_config(
        root=root,
        mcp_url=admin_config["mcp_url"],
        workspace=args.workspace,
        project=args.project,
        title=args.title,
        client_id=args.client_id,
        api_token=project_token["token"],
    )
    local_config = load_project(root)
    binding_client = make_client(local_config)
    binding = binding_client.call_tool(
        "project.register_local_binding",
        {
            "workspace": args.workspace,
            "project": args.project,
            "client_id": args.client_id,
            "local_root_hint": str(root),
            "manifest": {
                "outlines_dir": "outlines",
                "plans_dir": "plans",
                "chapters_dir": "chapters",
                "reviews_dir": "reviews",
                "context_dir": "context",
            },
        },
    )
    result = {
        "user": user,
        "workspace": workspace,
        "project": project,
        "project_root": str(root),
        "project_config": str(project_file(root)),
        "binding": binding,
        "token_saved": True,
    }
    save_json(root / ".novel-os" / "onboard-result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_project_add_member(args: argparse.Namespace) -> None:
    config = config_from_args_or_root(args)
    client = make_client(config)
    result = client.call_tool(
        "project.add_member",
        {"workspace": args.workspace, "project": args.project, "username": args.username, "role": args.role},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_call_tool(args: argparse.Namespace) -> None:
    config = config_from_args_or_root(args)
    payload = json.loads(args.arguments) if args.arguments else {}
    if args.arguments_file:
        payload = json.loads(Path(args.arguments_file).read_text(encoding="utf-8"))
    client = make_client(config)
    result = client.call_tool(args.tool, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def slugify(value: str) -> str:
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", value).strip("_")
    return text[:80] or "item"


def guess_item_type(path: Path, content: str) -> str:
    lower = "/".join(part.lower() for part in path.parts)
    if "review" in lower or "审查" in content[:500] or "审核" in content[:500]:
        return "review_dimension"
    if "rule" in lower or "规则" in content[:500]:
        return "rule_reference"
    if "trope" in lower or "套路" in content[:500]:
        return "trope"
    if "outline" in lower or "大纲" in content[:500]:
        return "outline_template"
    if "prompt" in lower:
        return "prompt"
    return "skill_note"


def first_heading_or_stem(path: Path, content: str) -> str:
    for line in content.splitlines()[:30]:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
    return path.stem


def iter_import_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source] if source.suffix.lower() in TEXT_IMPORT_SUFFIXES else []
    files = []
    for path in source.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_IMPORT_SUFFIXES:
            if any(part in {".git", "__pycache__", "node_modules"} for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def classify_webnovel_item(path: Path, content: str) -> str:
    lower = "/".join(part.lower() for part in path.parts)
    if "agent" in lower:
        return "agent_profile"
    if "review" in lower or "审核" in content[:1000] or "审查" in content[:1000]:
        return "review_workflow"
    if "template" in lower or "模板" in content[:1000]:
        return "genre_template"
    if "csv" in lower or path.suffix.lower() == ".csv":
        return "reference_table"
    if "skill" in lower:
        return "writing_skill"
    if "dashboard" in lower:
        return "dashboard_reference"
    return guess_item_type(path, content)


def webnovel_seed_rules(source_name: str) -> list[dict[str, Any]]:
    return [
        {
            "rule_key": "webnovel.import.use_reference_pack",
            "rule_type": "workflow",
            "title": "Use imported webnovel reference pack",
            "content": (
                "When preparing outlines, drafts, or reviews, search the imported webnovel reference pack first. "
                "Treat imported skills, templates, trope tables, and review workflows as reusable guidance, "
                "but keep project canon and active Novel OS rules above imported references."
            ),
            "severity": "warning",
            "metadata": {"source_pack": source_name},
        },
        {
            "rule_key": "webnovel.import.review_before_rule_change",
            "rule_type": "review",
            "title": "Review findings become proposals before rules",
            "content": (
                "Do not automatically rewrite active rules from imported skills or review findings. "
                "Convert recurring issues into rule proposals first, then approve them deliberately."
            ),
            "severity": "blocking",
            "metadata": {"source_pack": source_name},
        },
    ]


def build_webnovel_pack(source_path: Path, source_name: str, max_file_bytes: int) -> dict[str, Any]:
    items = []
    for path in iter_import_files(source_path):
        if path.stat().st_size > max_file_bytes:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(source_path) if source_path.is_dir() else Path(path.name)
        key = slugify(str(rel).replace("\\", "/"))
        items.append(
            {
                "item_type": classify_webnovel_item(path, content),
                "key": key,
                "title": first_heading_or_stem(path, content),
                "content": content,
                "metadata": {
                    "path": str(rel).replace("\\", "/"),
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "source_pack": source_name,
                },
            }
        )
    return {
        "items": items,
        "rules": webnovel_seed_rules(source_name),
        "review_councils": [
            {
                "name": "webnovel-default-review",
                "is_active": False,
                "config": {
                    "dimensions": [
                        "consistency",
                        "ooc",
                        "pacing",
                        "reader_pull",
                        "foreshadowing",
                        "genre_expectation",
                    ],
                    "models": [{"id": "default-reviewer", "role": "full_review"}],
                    "reference_pack": source_name,
                },
            }
        ],
    }


def cmd_webnovel_pack_build(args: argparse.Namespace) -> None:
    source_path = Path(args.source).resolve()
    if not source_path.exists():
        raise SystemExit(f"Source not found: {source_path}")
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    pack = build_webnovel_pack(source_path, args.name or source_path.name, args.max_file_bytes)
    save_json(output_path, pack)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "items": len(pack["items"]),
                "rules": len(pack["rules"]),
                "review_councils": len(pack["review_councils"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_skill_import(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    client = make_client(config)
    source_path = Path(args.source).resolve()
    if not source_path.exists():
        raise SystemExit(f"Source not found: {source_path}")

    source = client.call_tool(
        "reference.source_create",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "source_type": args.source_type,
            "name": args.name or source_path.name,
            "source_uri": str(source_path),
            "license": args.license,
            "metadata": {"importer": "novel-os-local", "root": str(root)},
        },
    )

    imported_items = []
    imported_rules = []
    imported_review_configs = []

    pack_file = source_path if source_path.is_file() and source_path.name == "novel-os-pack.json" else source_path / "novel-os-pack.json"
    if pack_file.exists():
        pack = json.loads(pack_file.read_text(encoding="utf-8"))
        for item in pack.get("items", []):
            imported_items.append(
                client.call_tool(
                    "reference.item_add",
                    {
                        "source_id": source["id"],
                        "workspace": config["workspace"],
                        "project": config["project"],
                        "item_type": item.get("item_type", "skill_note"),
                        "key": item["key"],
                        "title": item.get("title"),
                        "content": item["content"],
                        "metadata": item.get("metadata", {}),
                    },
                )
            )
        for rule in pack.get("rules", []):
            imported_rules.append(
                client.call_tool(
                    "rules.upsert",
                    {
                        "workspace": config["workspace"],
                        "project": config["project"],
                        "rule_key": rule["rule_key"],
                        "rule_type": rule.get("rule_type", "style"),
                        "title": rule.get("title", rule["rule_key"]),
                        "content": rule["content"],
                        "scope": rule.get("scope", "global"),
                        "severity": rule.get("severity", "warning"),
                        "status": rule.get("status", "active"),
                        "metadata": rule.get("metadata", {}),
                        "change_reason": "imported from novel-os-pack",
                        "source": args.source_type,
                    },
                )
            )
        for review in pack.get("review_councils", []):
            imported_review_configs.append(
                client.call_tool(
                    "review.upsert_council_config",
                    {
                        "workspace": config["workspace"],
                        "project": config["project"],
                        "name": review["name"],
                        "config": review.get("config", {}),
                        "is_active": bool(review.get("is_active", False)),
                    },
                )
            )
    else:
        for path in iter_import_files(source_path):
            content = path.read_text(encoding=args.encoding, errors="replace")
            rel = path.relative_to(source_path) if source_path.is_dir() else path.name
            key = slugify(str(rel).replace("\\", "/"))
            imported_items.append(
                client.call_tool(
                    "reference.item_add",
                    {
                        "source_id": source["id"],
                        "workspace": config["workspace"],
                        "project": config["project"],
                        "item_type": guess_item_type(path, content),
                        "key": key,
                        "title": first_heading_or_stem(path, content),
                        "content": content,
                        "metadata": {"path": str(rel), "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()},
                    },
                )
            )

    result = {
        "source": source,
        "items_imported": len(imported_items),
        "rules_imported": len(imported_rules),
        "review_configs_imported": len(imported_review_configs),
    }
    save_json(root / ".novel-os" / f"skill-import-{source['id']}.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_import_pack(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    client = make_client(config)
    pack_path = Path(args.pack_file).resolve()
    if not pack_path.exists():
        raise SystemExit(f"Pack file not found: {pack_path}")
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    result = client.call_tool(
        "sync.import_initial_project_pack",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "pack": pack,
        },
    )
    save_json(root / ".novel-os" / f"import-pack-{pack_path.stem}.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_export_pack(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    client = make_client(config)
    result = client.call_tool(
        "sync.export_project_pack",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "include_bindings": args.include_bindings,
        },
    )
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, result)
    print(json.dumps({"output": str(output_path), "pack_keys": list(result.keys()) if isinstance(result, dict) else []}, ensure_ascii=False, indent=2))


# ============================================================================
# 4.2 本地目录规范命令
# ============================================================================

def cmd_dirs_init(args: argparse.Namespace) -> None:
    """创建标准本地目录结构。"""
    root = Path(args.root).resolve()
    created = create_local_structure(root, force=args.force)

    if created:
        print(f"创建了 {len(created)} 个目录:")
        for d in created:
            print(f"  + {d}")
    else:
        print("所有目录已存在，未创建新目录（使用 --force 强制创建）")


def cmd_dirs_validate(args: argparse.Namespace) -> None:
    """验证本地目录结构。"""
    root = Path(args.root).resolve()
    result = validate_local_structure(root)

    if result["valid"]:
        print("✓ 目录结构验证通过")
        sys.exit(0)
    else:
        print("✗ 目录结构存在问题:")

        if result["missing_dirs"]:
            print(f"\n缺失目录 ({len(result['missing_dirs'])}):")
            for d in result["missing_dirs"]:
                print(f"  - {d['path']}: {d['description']}")

        if result["structure_errors"]:
            print(f"\n命名规范问题 ({len(result['structure_errors'])}):")
            for e in result["structure_errors"]:
                print(f"  - {e['path']}: {e['error']}")
                print(f"    提示: {e.get('hint', '')}")

        sys.exit(1)


def cmd_manifest_generate(args: argparse.Namespace) -> None:
    """生成本地项目 manifest。"""
    root = Path(args.root).resolve()
    manifest = generate_local_manifest(root, include_drafts=args.include_drafts)

    output_path = (root / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, manifest)

    print(f"Manifest 已生成: {output_path}")
    print(f"包含 {len(manifest['files'])} 个文件")


def cmd_templates_init(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    written = write_project_templates(root, overwrite=args.overwrite)
    print(json.dumps({"written": written, "overwrite": args.overwrite}, ensure_ascii=False, indent=2))


def cmd_init_templates(args: argparse.Namespace) -> None:
    """生成初始化模板文档。"""
    root = Path(args.root).resolve()
    title = args.title
    genre = args.genre

    # 确保目录存在
    dirs = [
        "设定集/人物",
        "设定集/势力",
        "设定集/地点",
        "大纲/卷大纲",
        "大纲/章节",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    written = []

    # 生成题材设定
    genre_path = root / "设定集" / f"【题材】{title}.md"
    if args.overwrite or not genre_path.exists():
        genre_path.write_text(generate_genre_document(genre, title), encoding="utf-8")
        written.append(str(genre_path))

    # 生成主角模板
    protagonist_path = root / "设定集/人物" / "【人物】主角模板.md"
    if args.overwrite or not protagonist_path.exists():
        protagonist_path.write_text(generate_character_document("主角"), encoding="utf-8")
        written.append(str(protagonist_path))

    # 生成大纲模板
    outline_path = root / "大纲" / f"【大纲】{title}.md"
    if args.overwrite or not outline_path.exists():
        outline_path.write_text(generate_outline_document(title), encoding="utf-8")
        written.append(str(outline_path))

    # 生成示例地点
    location_path = root / "设定集/地点" / "【地点】示例地点.md"
    if args.overwrite or not location_path.exists():
        location_path.write_text(generate_location_document("示例地点"), encoding="utf-8")
        written.append(str(location_path))

    print(f"生成 {len(written)} 个初始化模板文件:")
    for f in written:
        print(f"  + {f}")


def cmd_init_pack(args: argparse.Namespace) -> None:
    """从本地文件生成初始化 pack 并导入 MCP。"""
    root = Path(args.root).resolve()
    output_path = Path(args.output).resolve()

    pack = {
        "version": 1,
        "canon_documents": [],
        "rules": [],
        "entities": [],
        "relationships": [],
        "plot_threads": [],
        "foreshadowing": [],
        "volumes": [],
        "chapter_plans": [],
    }

    # 扫描设定集
    settings_dir = root / "设定集"
    if settings_dir.exists():
        for item_dir in ["人物", "势力", "地点", "道具"]:
            dir_path = settings_dir / item_dir
            if dir_path.exists():
                for md_file in dir_path.glob("*.md"):
                    content = md_file.read_text(encoding="utf-8")
                    # 提取标题
                    title = md_file.stem.replace("【人物】", "").replace("【势力】", "").replace("【地点】", "").replace("【道具】", "")

                    if item_dir == "人物":
                        pack["entities"].append({
                            "entity_type": "character",
                            "name": title,
                            "core_profile": content[:500],  # 取前 500 字作为核心设定
                        })
                    else:
                        doc_type = {"势力": "faction", "地点": "location", "道具": "item"}.get(item_dir, "world")
                        pack["canon_documents"].append({
                            "doc_type": doc_type,
                            "key": f"{item_dir}_{title}",
                            "title": title,
                            "content": content,
                            "status": "active",
                        })

    # 扫描大纲
    outline_dir = root / "大纲"
    if outline_dir.exists():
        for md_file in outline_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            title = md_file.stem.replace("【大纲】", "")
            pack["canon_documents"].append({
                "doc_type": "outline",
                "key": f"outline_{md_file.stem}",
                "title": title,
                "content": content,
                "status": "active",
            })

    # 扫描细纲
    xigang_dir = root / "细纲"
    if xigang_dir.exists():
        for md_file in xigang_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            # 从文件名提取章节号
            import re
            m = re.match(r"ch(\d+)", md_file.stem)
            if m:
                chapter_no = int(m.group(1))
                pack["chapter_plans"].append({
                    "chapter_no": chapter_no,
                    "plan": {"title": md_file.stem, "summary": content[:500]},
                })

    # 保存 pack 文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, pack)

    print(f"生成了初始化 pack: {output_path}")
    print(f"  canon_documents: {len(pack['canon_documents'])}")
    print(f"  entities: {len(pack['entities'])}")
    print(f"  chapter_plans: {len(pack['chapter_plans'])}")

    # 如果配置了 MCP，尝试导入
    config = project_config_from_args(args)
    if config.get("mcp_url") and config.get("workspace") and config.get("project"):
        try:
            client = make_client(config)
            result = client.call_tool(
                "sync.import_initial_project_pack",
                {
                    "workspace": config["workspace"],
                    "project": config["project"],
                    "pack": pack,
                },
            )
            save_json(root / ".novel-os" / "init-pack-result.json", result)
            print(f"已导入 MCP: {result.get('imported', {})}")
        except Exception as exc:
            print(f"警告: 导入 MCP 失败 ({exc})，请稍后手动导入")


def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    for item in DEFAULT_DIRS:
        (root / item).mkdir(parents=True, exist_ok=True)

    config = {
        "mcp_url": args.mcp_url,
        "workspace": args.workspace,
        "project": args.project,
        "title": args.title,
        "client_id": args.client_id,
        "api_token": args.api_token,
        "local_root": str(root),
    }
    save_json(project_file(root), config)
    save_json(root / ".novel-os" / "sync-state.json", {"last_context_chapter": None, "last_commit_chapter": None})
    write_project_templates(root, overwrite=False)

    client = make_client(config)
    client.call_tool("project.create", {"workspace": args.workspace, "slug": args.project, "title": args.title, "description": args.description})
    client.call_tool(
        "project.register_local_binding",
        {
            "workspace": args.workspace,
            "project": args.project,
            "client_id": args.client_id,
            "local_root_hint": str(root),
            "manifest": {
                "outlines_dir": "outlines",
                "plans_dir": "plans",
                "chapters_dir": "chapters",
                "reviews_dir": "reviews",
                "context_dir": "context",
            },
        },
    )
    print(f"Initialized Novel OS local project at {root}")


def cmd_context(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)

    # 检查是否使用离线模式
    use_cache = getattr(args, "offline", False)

    pack = None
    source = "mcp"

    if not use_cache:
        try:
            client = make_client(config)
            pack = client.call_tool(
                "workflow.prepare_chapter_context",
                {
                    "workspace": config["workspace"],
                    "project": config["project"],
                    "chapter_no": args.chapter,
                    "purpose": args.purpose,
                    "focus": args.focus or [],
                    "profile": getattr(args, "profile", None),
                    "pov": getattr(args, "pov", None),
                    "budget": {"recent_count": args.recent_count, "memory_limit": args.memory_limit},
                },
            )
            # 缓存结果
            cache_context(root, args.chapter, pack)
        except Exception as exc:
            if use_cache:
                raise
            print(f"警告: MCP 调用失败 ({exc})，尝试使用缓存...", file=sys.stderr)
            source = "cache"
            pack = None

    # 尝试从缓存获取
    if pack is None:
        pack = get_cached_context(root, args.chapter)
        if pack is None:
            raise SystemExit(f"无法获取上下文（离线模式且无缓存）: 章节 {args.chapter}")
        source = "cache"
        print(f"使用缓存的上下文 (ch{args.chapter:04d})")

    # 保存到 context 目录
    json_path = root / "context" / f"ch{args.chapter:04d}.context.json"
    md_path = root / "context" / f"ch{args.chapter:04d}.context.md"
    save_json(json_path, pack)
    md_path.write_text(render_context_markdown(pack), encoding="utf-8")
    print(f"Wrote {json_path} (来源: {source})")
    print(f"Wrote {md_path}")


def cmd_context_list(args: argparse.Namespace) -> None:
    """列出所有缓存的上下文。"""
    root = Path(args.root).resolve()
    cached = list_cached_contexts(root)

    if not cached:
        print("没有缓存的上下文")
        return

    print(f"共 {len(cached)} 个缓存的上下文:")
    for entry in cached:
        print(f"  ch{entry['chapter_no']:04d} - 缓存于 {entry['cached_at']}")


def cmd_context_clear(args: argparse.Namespace) -> None:
    """清除上下文缓存。"""
    root = Path(args.root).resolve()
    chapter_no = getattr(args, "chapter", None)

    if chapter_no is not None:
        count = clear_context_cache(root, chapter_no)
        print(f"已清除章节 ch{chapter_no:04d} 的缓存")
    else:
        count = clear_context_cache(root, None)
        print(f"已清除全部 {count} 个上下文缓存")


def cmd_commit(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    chapter_path = (root / args.chapter_file).resolve()
    if not chapter_path.exists():
        raise SystemExit(f"Chapter file not found: {chapter_path}")
    text = chapter_path.read_text(encoding=args.encoding)
    events = []
    if args.events_file:
        events = json.loads((root / args.events_file).read_text(encoding="utf-8"))

    commit_type = getattr(args, "commit_type", "draft")

    local_files = [
        {
            "kind": "chapter",
            "path_hint": str(Path(args.chapter_file).as_posix()),
            "sha256": sha256_file(chapter_path),
            "word_count": count_cjk_aware_words(text),
        }
    ]

    # 根据提交类型设置不同的 accept 行为
    if commit_type == "draft":
        # draft 不污染正式状态
        accept = False
        print(f"[draft] 草稿提交（不更新正式状态）")
    elif commit_type == "final":
        # final 更新状态、摘要、伏笔
        accept = True
        print(f"[final] 正式提交（更新所有状态）")
    else:
        accept = args.accept

    commit = {
        "summary": args.summary,
        "commit_type": commit_type,
        "events": events,
        "character_state_changes": [],
        "world_state_changes": [],
        "new_facts": [],
        "foreshadowing_changes": [],
        "plot_thread_changes": [],
        "rule_warnings": [],
        "next_chapter_hooks": [],
    }

    commit_data = {
        "chapter_no": args.chapter,
        "title": args.title,
        "local_files": local_files,
        "commit": commit,
        "accept": accept,
    }

    # 检查离线模式
    offline = getattr(args, "offline", False)

    if offline:
        # 离线模式：加入队列
        queue_offline_commit(root, commit_data)
        print(f"[offline] 提交已加入离线队列 (ch{args.chapter:04d})")
        result = {"status": "queued_offline", "chapter_no": args.chapter}
    else:
        # 在线模式：直接提交到 MCP
        try:
            client = make_client(config)
            result = client.call_tool(
                "workflow.submit_chapter_commit",
                {
                    "workspace": config["workspace"],
                    "project": config["project"],
                    "chapter_no": args.chapter,
                    "title": args.title,
                    "local_files": local_files,
                    "commit": commit,
                    "accept": accept,
                },
            )
        except Exception as exc:
            if offline:
                raise
            print(f"警告: MCP 调用失败 ({exc})，尝试加入离线队列...", file=sys.stderr)
            queue_offline_commit(root, commit_data)
            print(f"[offline] 提交已加入离线队列 (ch{args.chapter:04d})")
            result = {"status": "queued_offline", "chapter_no": args.chapter}

    save_json(root / ".novel-os" / f"ch{args.chapter:04d}.commit-result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_queue_list(args: argparse.Namespace) -> None:
    """列出离线提交队列。"""
    root = Path(args.root).resolve()
    queue = load_offline_queue(root)

    if not queue:
        print("离线队列为空")
        return

    print(f"离线提交队列（共 {len(queue)} 项）:")
    for i, item in enumerate(queue):
        status = item.get("status", "pending")
        chapter_no = item.get("chapter_no", "?")
        title = item.get("title", "?")
        queued_at = item.get("queued_at", "?")
        print(f"  {i + 1}. ch{chapter_no:04d} - {title} [{status}] @ {queued_at}")


def cmd_queue_sync(args: argparse.Namespace) -> None:
    """同步离线提交队列到 MCP。"""
    root = Path(args.root).resolve()
    config = project_config_from_args(args)

    print("正在同步离线队列...")
    result = sync_offline_queue(root, config)

    print(f"同步完成:")
    print(f"  成功: {result['synced']}")
    print(f"  失败: {result['failed']}")
    print(f"  剩余: {result['remaining']}")

    if result.get("errors"):
        print("\n错误详情:")
        for err in result["errors"]:
            print(f"  ch{err['chapter_no']:04d}: {err['error']}")


def cmd_review_start(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    local_files = []
    if args.chapter_file:
        chapter_path = (root / args.chapter_file).resolve()
        if not chapter_path.exists():
            raise SystemExit(f"Chapter file not found: {chapter_path}")
        local_files.append({"kind": "chapter", "path_hint": args.chapter_file, "sha256": sha256_file(chapter_path)})
    client = make_client(config)
    result = client.call_tool(
        "review.start_job",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "chapter_no": args.chapter,
            "local_files": local_files,
            "dimensions": args.dimension or ["consistency", "ooc", "pacing", "reader_pull", "foreshadowing"],
        },
    )
    save_json(root / ".novel-os" / f"ch{args.chapter:04d}.review-job.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_review_submit(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    report = json.loads((root / args.report_file).read_text(encoding="utf-8"))
    local_report_file = None
    if args.local_report_file:
        path = (root / args.local_report_file).resolve()
        local_report_file = {"path_hint": args.local_report_file, "sha256": sha256_file(path) if path.exists() else None}
    client = make_client(config)
    result = client.call_tool(
        "review.submit_model_report",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "review_job_id": args.review_job_id,
            "model_id": report.get("model_id", args.model_id),
            "score": report.get("score"),
            "summary": report.get("summary", ""),
            "findings": report.get("findings", []),
            "local_report_file": local_report_file,
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def load_review_models(root: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.models_file:
        path = Path(args.models_file)
        if not path.is_absolute():
            path = root / path
    else:
        path = root / ".novel-os" / "review-models.json"
        if not path.exists():
            return load_profile_models(root, args.profile, args.model_config)
    if not path.exists():
        raise SystemExit(f"Missing review model config: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = payload.get("models", payload if isinstance(payload, list) else [])
    if not isinstance(models, list) or not models:
        raise SystemExit("review model config must contain a non-empty models list")
    return models


def default_model_config() -> dict[str, Any]:
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("NOVEL_OS_MODEL_BASE_URL") or DEFAULT_BASE_URL
    model = os.environ.get("OPENAI_MODEL") or os.environ.get("NOVEL_OS_MODEL") or DEFAULT_MODEL_ID
    embedding_model = (
        os.environ.get("OPENAI_EMBEDDING_MODEL")
        or os.environ.get("NOVEL_OS_EMBEDDING_MODEL")
        or DEFAULT_EMBEDDING_MODEL_ID
    )
    return {
        "providers": {
            "default": {
                "base_url": base_url,
            }
        },
        "profiles": {
            "outline": [
                {
                    "id": "outline-main",
                    "provider": "default",
                    "model": model,
                    "temperature": 0.7,
                    "max_tokens": 5000,
                }
            ],
            "draft": [
                {
                    "id": "draft-main",
                    "provider": "default",
                    "model": model,
                    "temperature": 0.8,
                    "max_tokens": 8000,
                }
            ],
            "review": [
                {
                    "id": "default-reviewer",
                    "provider": "default",
                    "model": model,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                }
            ],
            "embedding": [
                {
                    "id": "embedding-main",
                    "provider": "default",
                    "model": embedding_model,
                }
            ],
        },
    }


def load_model_config(root: Path, config_file: str | None = None) -> dict[str, Any]:
    explicit_path = bool(config_file)
    if config_file:
        path = Path(config_file)
        if not path.is_absolute():
            path = root / path
    else:
        path = root / ".novel-os" / "model-config.json"
    if not path.exists():
        if explicit_path:
            raise SystemExit(f"Missing model config: {path}")
        return default_model_config()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("model config must be a JSON object")
    return payload


def load_profile_models(root: Path, profile: str, config_file: str | None = None) -> list[dict[str, Any]]:
    payload = load_model_config(root, config_file)
    providers = payload.get("providers", {})
    profiles = payload.get("profiles", {})
    models = profiles.get(profile)
    if not isinstance(models, list) or not models:
        models = default_model_config()["profiles"].get(profile)
    if not isinstance(models, list) or not models:
        raise SystemExit(f"model config profile is empty: {profile}")
    resolved = []
    for model in models:
        provider = providers.get(model.get("provider"), {}) if model.get("provider") else {}
        merged = {**provider, **model}
        if "id" not in merged:
            merged["id"] = merged.get("model", profile)
        resolved.append(merged)
    return resolved


def resolve_api_key(model_cfg: dict[str, Any]) -> str:
    if model_cfg.get("api_key"):
        return model_cfg["api_key"]
    env_name = model_cfg.get("api_key_env")
    if env_name:
        value = os.environ.get(env_name)
        if not value:
            raise SystemExit(f"Missing API key environment variable: {env_name}")
        return value
    for fallback_env in DEFAULT_API_KEY_ENVS:
        value = os.environ.get(fallback_env)
        if value:
            return value
    env_name = " or ".join(DEFAULT_API_KEY_ENVS)
    raise SystemExit(f"Missing API key environment variable: {env_name}")


def call_openai_compatible(model_cfg: dict[str, Any], messages: list[dict[str, str]], timeout: int) -> str:
    base_url = (model_cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    url = base_url + "/chat/completions"
    body = {
        "model": model_cfg["model"],
        "messages": messages,
        "temperature": model_cfg.get("temperature", 0.2),
    }
    if model_cfg.get("max_tokens"):
        body["max_tokens"] = model_cfg["max_tokens"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + resolve_api_key(model_cfg),
    }
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"model {model_cfg.get('id') or model_cfg.get('model')} HTTP {exc.code}: {detail}") from exc
    return payload["choices"][0]["message"]["content"]


def call_openai_embedding(model_cfg: dict[str, Any], texts: list[str], timeout: int) -> list[list[float]]:
    base_url = (model_cfg.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    url = base_url + "/embeddings"
    body = {
        "model": model_cfg["model"],
        "input": texts,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + resolve_api_key(model_cfg),
    }
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"embedding model {model_cfg.get('id') or model_cfg.get('model')} HTTP {exc.code}: {detail}") from exc
    data = payload.get("data", [])
    data = sorted(data, key=lambda item: item.get("index", 0))
    vectors = [item.get("embedding") for item in data]
    if len(vectors) != len(texts) or not all(isinstance(vector, list) for vector in vectors):
        raise RuntimeError("Embedding response did not contain one vector per input")
    return vectors


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        value = json.loads(match.group(0))
        if isinstance(value, dict):
            return value
    raise ValueError("Model response did not contain a JSON object")


def build_review_prompt(chapter_text: str, context_text: str, dimensions: list[str]) -> list[dict[str, str]]:
    system = (
        "You are a strict webnovel chapter reviewer. Return only valid JSON with keys: "
        "model_id, score, summary, findings. findings must be a list of objects with "
        "dimension, severity, target, evidence, suggestion. Severity is one of blocking, high, medium, low."
    )
    user = {
        "dimensions": dimensions,
        "context": context_text[:24000],
        "chapter": chapter_text[:50000],
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def read_optional_file(root: Path, value: str | None) -> str:
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def write_generation_outputs(root: Path, output_file: str, outputs: list[dict[str, Any]]) -> Path:
    output_path = Path(output_file)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if len(outputs) == 1:
        output_path.write_text(outputs[0]["content"], encoding="utf-8")
    else:
        lines = []
        for item in outputs:
            lines.append(f"# {item['model_id']}")
            lines.append("")
            lines.append(item["content"])
            lines.append("")
        output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_generation_profile(
    root: Path,
    profile: str,
    model_config: str | None,
    messages: list[dict[str, str]],
    timeout: int,
) -> list[dict[str, Any]]:
    outputs = []
    for model_cfg in load_profile_models(root, profile, model_config):
        model_id = model_cfg.get("id") or model_cfg["model"]
        outputs.append(
            {
                "model_id": model_id,
                "content": call_openai_compatible(model_cfg, messages, timeout),
            }
        )
    return outputs


def cmd_outline_run(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    context_text = read_optional_file(root, args.context_file)
    brief_text = args.brief or read_optional_file(root, args.brief_file)
    system = (
        "You are a senior webnovel outliner. Produce a practical outline in Markdown. "
        "Respect canon, current state, foreshadowing, and pacing constraints from the context."
    )
    user = json.dumps(
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "brief": brief_text,
            "context": context_text[:30000],
            "requirements": args.requirement or [],
        },
        ensure_ascii=False,
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if args.dry_run:
        path = root / ".novel-os" / "outline.prompt.json"
        save_json(path, {"profile": args.profile, "messages": messages})
        print(json.dumps({"dry_run": True, "prompt_file": str(path)}, ensure_ascii=False, indent=2))
        return
    outputs = run_generation_profile(root, args.profile, args.model_config, messages, args.timeout)
    output_path = write_generation_outputs(root, args.output_file, outputs)
    print(json.dumps({"output_file": str(output_path), "models": [item["model_id"] for item in outputs]}, ensure_ascii=False, indent=2))


def cmd_draft_run(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    context_text = read_optional_file(root, args.context_file)
    plan_text = read_optional_file(root, args.plan_file)
    extra_text = args.brief or read_optional_file(root, args.brief_file)
    system = (
        "You are a webnovel drafting model. Write immersive chapter prose in Chinese unless instructed otherwise. "
        "Follow context strictly, avoid contradicting accepted canon, and preserve unresolved foreshadowing."
    )
    user = json.dumps(
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "chapter_no": args.chapter,
            "target_words": args.target_words,
            "context": context_text[:30000],
            "chapter_plan": plan_text[:20000],
            "brief": extra_text,
            "requirements": args.requirement or [],
        },
        ensure_ascii=False,
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if args.dry_run:
        path = root / ".novel-os" / f"ch{args.chapter:04d}.draft.prompt.json"
        save_json(path, {"profile": args.profile, "messages": messages})
        print(json.dumps({"dry_run": True, "prompt_file": str(path)}, ensure_ascii=False, indent=2))
        return
    outputs = run_generation_profile(root, args.profile, args.model_config, messages, args.timeout)
    output_path = write_generation_outputs(root, args.output_file, outputs)
    print(json.dumps({"output_file": str(output_path), "models": [item["model_id"] for item in outputs]}, ensure_ascii=False, indent=2))


def cmd_review_run(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    chapter_path = (root / args.chapter_file).resolve()
    if not chapter_path.exists():
        raise SystemExit(f"Chapter file not found: {chapter_path}")
    chapter_text = chapter_path.read_text(encoding=args.encoding)
    context_text = ""
    if args.context_file:
        context_path = (root / args.context_file).resolve()
        if context_path.exists():
            context_text = context_path.read_text(encoding="utf-8", errors="replace")
    model_configs = load_review_models(root, args)
    dimensions = args.dimension or ["consistency", "ooc", "pacing", "reader_pull", "foreshadowing"]

    if args.dry_run:
        prompts = [
            {
                "model_id": model_cfg.get("id") or model_cfg.get("model"),
                "model": model_cfg.get("model"),
                "messages": build_review_prompt(chapter_text, context_text, dimensions),
            }
            for model_cfg in model_configs
        ]
        path = root / ".novel-os" / f"ch{args.chapter:04d}.review-prompts.json"
        save_json(path, {"chapter": args.chapter, "models": prompts})
        print(json.dumps({"dry_run": True, "prompt_file": str(path), "model_count": len(prompts)}, ensure_ascii=False, indent=2))
        return

    client = make_client(config)
    job = client.call_tool(
        "review.start_job",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "chapter_no": args.chapter,
            "local_files": [{"kind": "chapter", "path_hint": args.chapter_file, "sha256": sha256_file(chapter_path)}],
            "dimensions": dimensions,
        },
    )
    review_job_id = job["id"]
    reports_dir = root / "reviews" / f"volume_{args.volume:03d}"
    reports_dir.mkdir(parents=True, exist_ok=True)
    submitted = []
    errors = []
    for model_cfg in model_configs:
        model_id = model_cfg.get("id") or model_cfg["model"]
        try:
            raw = call_openai_compatible(
                model_cfg,
                build_review_prompt(chapter_text, context_text, dimensions),
                args.timeout,
            )
            report = extract_json_object(raw)
            report["model_id"] = report.get("model_id") or model_id
            report_path = reports_dir / f"ch{args.chapter:04d}.{slugify(model_id)}.report.json"
            save_json(report_path, report)
            result = client.call_tool(
                "review.submit_model_report",
                {
                    "workspace": config["workspace"],
                    "project": config["project"],
                    "review_job_id": review_job_id,
                    "model_id": report["model_id"],
                    "score": report.get("score"),
                    "summary": report.get("summary", ""),
                    "findings": report.get("findings", []),
                    "local_report_file": {"path_hint": str(report_path.relative_to(root)).replace("\\", "/"), "sha256": sha256_file(report_path)},
                },
            )
            submitted.append({"model_id": model_id, "report_file": str(report_path), "result": result})
        except Exception as exc:
            errors.append({"model_id": model_id, "error": str(exc)})
            if not args.continue_on_error:
                raise

    aggregate = None
    if submitted and args.aggregate:
        aggregate = client.call_tool(
            "review.aggregate",
            {
                "workspace": config["workspace"],
                "project": config["project"],
                "review_job_id": review_job_id,
                "create_revision_tasks": True,
            },
        )
        save_json(root / ".novel-os" / f"review-{review_job_id}.aggregate.json", aggregate)

    result = {"review_job": job, "submitted": submitted, "errors": errors, "aggregate": aggregate}
    save_json(root / ".novel-os" / f"ch{args.chapter:04d}.review-run.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_review_aggregate(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    client = make_client(config)
    result = client.call_tool(
        "review.aggregate",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "review_job_id": args.review_job_id,
            "create_revision_tasks": args.create_revision_tasks,
        },
    )
    save_json(root / ".novel-os" / f"review-{args.review_job_id}.aggregate.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_vector_pending(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    client = make_client(config)
    result = client.call_tool(
        "memory.pending_vector_chunks",
        {"workspace": config["workspace"], "project": config["project"], "limit": args.limit},
    )
    save_json(root / ".novel-os" / "pending-vector-chunks.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_vector_upsert(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    payload = json.loads((root / args.embedding_file).read_text(encoding="utf-8"))
    vector = payload.get("vector")
    if not isinstance(vector, list):
        raise SystemExit("embedding file must contain a 'vector' list")
    client = make_client(config)
    result = client.call_tool(
        "memory.upsert_vector",
        {
            "workspace": config["workspace"],
            "project": config["project"],
            "chunk_id": args.chunk_id or payload.get("chunk_id"),
            "vector": vector,
            "collection": args.collection,
            "payload": payload.get("payload", {}),
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_vector_run(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    client = make_client(config)
    pending = client.call_tool(
        "memory.pending_vector_chunks",
        {"workspace": config["workspace"], "project": config["project"], "limit": args.limit},
    )
    chunks = pending if isinstance(pending, list) else []
    if args.dry_run:
        result = {
            "dry_run": True,
            "pending_count": len(chunks),
            "chunk_ids": [chunk.get("id") for chunk in chunks],
        }
        save_json(root / ".novel-os" / "vector-run.dry-run.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not chunks:
        result = {"indexed": 0, "errors": []}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    model_cfgs = load_profile_models(root, args.profile, args.model_config)
    model_cfg = model_cfgs[0]
    indexed = []
    errors = []
    for start in range(0, len(chunks), args.batch_size):
        batch = chunks[start : start + args.batch_size]
        try:
            vectors = call_openai_embedding(model_cfg, [str(chunk.get("content", "")) for chunk in batch], args.timeout)
            for chunk, vector in zip(batch, vectors):
                payload = {
                    "source_type": chunk.get("source_type"),
                    "source_id": chunk.get("source_id"),
                    "chunk_key": chunk.get("chunk_key"),
                    "metadata": ensure_json_value(chunk.get("metadata")) or {},
                    "embedding_model": model_cfg.get("model"),
                    "embedding_provider": model_cfg.get("provider") or model_cfg.get("base_url"),
                }
                result = client.call_tool(
                    "memory.upsert_vector",
                    {
                        "workspace": config["workspace"],
                        "project": config["project"],
                        "chunk_id": chunk["id"],
                        "vector": vector,
                        "collection": args.collection,
                        "payload": payload,
                    },
                )
                indexed.append(result)
        except Exception as exc:
            errors.append({"batch_start": start, "error": str(exc), "chunk_ids": [chunk.get("id") for chunk in batch]})
            if not args.continue_on_error:
                raise
    result = {"indexed": len(indexed), "errors": errors, "model": model_cfg.get("model")}
    save_json(root / ".novel-os" / "vector-run.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def load_review_aggregate(root: Path, review_job_id: str | None, aggregate_file: str | None) -> dict[str, Any]:
    if aggregate_file:
        path = Path(aggregate_file)
        if not path.is_absolute():
            path = root / path
    elif review_job_id:
        path = root / ".novel-os" / f"review-{review_job_id}.aggregate.json"
    else:
        raise SystemExit("rules-evolve requires --review-job-id or --aggregate-file")
    if not path.exists():
        raise SystemExit(f"Aggregate file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def findings_from_aggregate(aggregate: dict[str, Any]) -> list[dict[str, Any]]:
    payload = ensure_json_value(aggregate.get("findings")) or {}
    findings = payload.get("top_findings", [])
    if isinstance(findings, list):
        return [item for item in findings if isinstance(item, dict)]
    return []


def rule_proposal_from_finding(finding: dict[str, Any], index: int, review_job_id: str | None) -> dict[str, Any]:
    dimension = slugify(str(finding.get("dimension") or "review")).lower()
    target = str(finding.get("target") or finding.get("dimension") or "review finding")
    severity = str(finding.get("severity") or "medium")
    suggestion = str(finding.get("suggestion") or finding.get("evidence") or "").strip()
    evidence = str(finding.get("evidence") or "").strip()
    title = f"Review rule: {target}"
    content_lines = [
        f"When writing or revising, guard against this recurring issue: {target}.",
    ]
    if suggestion:
        content_lines.append(f"Preferred correction: {suggestion}")
    if evidence:
        content_lines.append(f"Observed evidence: {evidence}")
    return {
        "title": title[:200],
        "content": "\n".join(content_lines),
        "proposal_type": "create",
        "source_type": "review_consensus",
        "confidence": 0.9 if severity in {"blocking", "high"} else 0.7,
        "agreement": {
            "review_job_id": review_job_id,
            "dimension": dimension,
            "severity": severity,
            "source_finding_index": index,
            "source_finding": finding,
        },
    }


def cmd_rules_evolve(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = project_config_from_args(args)
    aggregate = load_review_aggregate(root, args.review_job_id, args.aggregate_file)
    findings = findings_from_aggregate(aggregate)
    severities = set(args.severity or ["blocking", "high"])
    candidates = [
        rule_proposal_from_finding(finding, index, args.review_job_id)
        for index, finding in enumerate(findings)
        if str(finding.get("severity") or "medium") in severities
    ][: args.limit]
    if args.dry_run:
        result = {"dry_run": True, "proposal_count": len(candidates), "proposals": candidates}
        save_json(root / ".novel-os" / "rules-evolve.dry-run.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    client = make_client(config)
    proposals = []
    for candidate in candidates:
        proposal = client.call_tool(
            "rules.propose",
            {
                "workspace": config["workspace"],
                "project": config["project"],
                **candidate,
            },
        )
        proposals.append(proposal)
        if args.auto_apply:
            client.call_tool(
                "rules.apply_proposal",
                {
                    "workspace": config["workspace"],
                    "project": config["project"],
                    "proposal_id": proposal["id"],
                    "decision": "approved",
                    "reason": "auto-applied by local rules-evolve",
                },
            )
    result = {"proposal_count": len(proposals), "proposals": proposals, "auto_apply": args.auto_apply}
    save_json(root / ".novel-os" / "rules-evolve.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Novel OS local workspace helper")
    sub = parser.add_subparsers(dest="command", required=True)

    whoami = sub.add_parser("whoami")
    whoami.add_argument("--root", default=".")
    whoami.add_argument("--mcp-url")
    whoami.add_argument("--api-token")
    whoami.set_defaults(func=cmd_whoami)

    token_create = sub.add_parser("token-create")
    token_create.add_argument("--root", default=".")
    token_create.add_argument("--mcp-url")
    token_create.add_argument("--api-token")
    token_create.add_argument("--username", required=True)
    token_create.add_argument("--name", required=True)
    token_create.add_argument("--scope", action="append")
    token_create.add_argument("--workspace")
    token_create.add_argument("--project")
    token_create.add_argument("--expires-at")
    token_create.add_argument("--save-to-root")
    token_create.set_defaults(func=cmd_token_create)

    user_create = sub.add_parser("user-create")
    user_create.add_argument("--root", default=".")
    user_create.add_argument("--mcp-url")
    user_create.add_argument("--api-token")
    user_create.add_argument("--username", required=True)
    user_create.add_argument("--display-name")
    user_create.add_argument("--email")
    user_create.add_argument("--status", default="active")
    user_create.set_defaults(func=cmd_user_create)

    workspace_create = sub.add_parser("workspace-create")
    workspace_create.add_argument("--root", default=".")
    workspace_create.add_argument("--mcp-url")
    workspace_create.add_argument("--api-token")
    workspace_create.add_argument("--workspace", required=True)
    workspace_create.add_argument("--name", required=True)
    workspace_create.set_defaults(func=cmd_workspace_create)

    workspace_add_member = sub.add_parser("workspace-add-member")
    workspace_add_member.add_argument("--root", default=".")
    workspace_add_member.add_argument("--mcp-url")
    workspace_add_member.add_argument("--api-token")
    workspace_add_member.add_argument("--workspace", required=True)
    workspace_add_member.add_argument("--username", required=True)
    workspace_add_member.add_argument("--role", default="reader", choices=["owner", "writer", "reader"])
    workspace_add_member.set_defaults(func=cmd_workspace_add_member)

    project_add_member = sub.add_parser("project-add-member")
    project_add_member.add_argument("--root", default=".")
    project_add_member.add_argument("--mcp-url")
    project_add_member.add_argument("--api-token")
    project_add_member.add_argument("--workspace", required=True)
    project_add_member.add_argument("--project", required=True)
    project_add_member.add_argument("--username", required=True)
    project_add_member.add_argument("--role", default="writer", choices=["owner", "writer", "reader"])
    project_add_member.set_defaults(func=cmd_project_add_member)

    onboard_project = sub.add_parser("onboard-project")
    onboard_project.add_argument("--root", default=".")
    onboard_project.add_argument("--mcp-url")
    onboard_project.add_argument("--api-token")
    onboard_project.add_argument("--project-root", required=True)
    onboard_project.add_argument("--username", required=True)
    onboard_project.add_argument("--display-name")
    onboard_project.add_argument("--email")
    onboard_project.add_argument("--workspace", required=True)
    onboard_project.add_argument("--workspace-name")
    onboard_project.add_argument("--workspace-role", default="owner", choices=["owner", "writer", "reader"])
    onboard_project.add_argument("--project", required=True)
    onboard_project.add_argument("--title", required=True)
    onboard_project.add_argument("--description")
    onboard_project.add_argument("--project-role", default="owner", choices=["owner", "writer", "reader"])
    onboard_project.add_argument("--client-id", default="novel-os-local")
    onboard_project.add_argument("--token-name")
    onboard_project.add_argument("--scope", action="append")
    onboard_project.add_argument("--expires-at")
    onboard_project.set_defaults(func=cmd_onboard_project)

    call_tool = sub.add_parser("call-tool")
    call_tool.add_argument("--root", default=".")
    call_tool.add_argument("--mcp-url")
    call_tool.add_argument("--api-token")
    call_tool.add_argument("--tool", required=True)
    call_tool.add_argument("--arguments")
    call_tool.add_argument("--arguments-file")
    call_tool.set_defaults(func=cmd_call_tool)

    skill_import = sub.add_parser("skill-import")
    skill_import.add_argument("--root", default=".")
    skill_import.add_argument("--api-token")
    skill_import.add_argument("--source", required=True)
    skill_import.add_argument("--name")
    skill_import.add_argument("--source-type", default="skill_pack")
    skill_import.add_argument("--license")
    skill_import.add_argument("--encoding", default="utf-8")
    skill_import.set_defaults(func=cmd_skill_import)

    import_pack = sub.add_parser("import-pack")
    import_pack.add_argument("--root", default=".")
    import_pack.add_argument("--api-token")
    import_pack.add_argument("--pack-file", required=True)
    import_pack.set_defaults(func=cmd_import_pack)

    export_pack = sub.add_parser("export-pack")
    export_pack.add_argument("--root", default=".")
    export_pack.add_argument("--api-token")
    export_pack.add_argument("--output", required=True)
    export_pack.add_argument("--include-bindings", action="store_true")
    export_pack.set_defaults(func=cmd_export_pack)

    # 4.2 本地目录规范命令
    dirs_init = sub.add_parser("dirs-init")
    dirs_init.add_argument("--root", default=".")
    dirs_init.add_argument("--force", action="store_true", help="强制创建，即使目录已存在")
    dirs_init.set_defaults(func=cmd_dirs_init)

    dirs_validate = sub.add_parser("dirs-validate")
    dirs_validate.add_argument("--root", default=".")
    dirs_validate.add_argument("--strict", action="store_true", help="严格模式：命名不规范也报错")
    dirs_validate.set_defaults(func=cmd_dirs_validate)

    manifest_generate = sub.add_parser("manifest-generate")
    manifest_generate.add_argument("--root", default=".")
    manifest_generate.add_argument("--output", default="manifest.json")
    manifest_generate.add_argument("--include-drafts", action="store_true")
    manifest_generate.set_defaults(func=cmd_manifest_generate)

    webnovel_pack_build = sub.add_parser("webnovel-pack-build")
    webnovel_pack_build.add_argument("--source", required=True)
    webnovel_pack_build.add_argument("--output", required=True)
    webnovel_pack_build.add_argument("--name")
    webnovel_pack_build.add_argument("--max-file-bytes", type=int, default=1024 * 512)
    webnovel_pack_build.set_defaults(func=cmd_webnovel_pack_build)

    templates_init = sub.add_parser("templates-init")
    templates_init.add_argument("--root", default=".")
    templates_init.add_argument("--overwrite", action="store_true")
    templates_init.set_defaults(func=cmd_templates_init)

    # 4.7 初始化模板命令
    init_templates = sub.add_parser("init-templates")
    init_templates.add_argument("--root", default=".")
    init_templates.add_argument("--title", required=True, help="小说标题")
    init_templates.add_argument("--genre", default="玄幻", help="题材类型")
    init_templates.add_argument("--overwrite", action="store_true")
    init_templates.set_defaults(func=cmd_init_templates)

    init_pack = sub.add_parser("init-pack")
    init_pack.add_argument("--root", default=".")
    init_pack.add_argument("--output", default="initial-pack.json", help="输出文件路径")
    init_pack.add_argument("--api-token")
    init_pack.set_defaults(func=cmd_init_pack)

    outline_run = sub.add_parser("outline-run")
    outline_run.add_argument("--root", default=".")
    outline_run.add_argument("--api-token")
    outline_run.add_argument("--profile", default="outline")
    outline_run.add_argument("--model-config")
    outline_run.add_argument("--brief")
    outline_run.add_argument("--brief-file")
    outline_run.add_argument("--context-file")
    outline_run.add_argument("--requirement", action="append")
    outline_run.add_argument("--output-file", default="outlines/outline.generated.md")
    outline_run.add_argument("--timeout", type=int, default=180)
    outline_run.add_argument("--dry-run", action="store_true")
    outline_run.set_defaults(func=cmd_outline_run)

    draft_run = sub.add_parser("draft-run")
    draft_run.add_argument("--root", default=".")
    draft_run.add_argument("--api-token")
    draft_run.add_argument("--chapter", type=int, required=True)
    draft_run.add_argument("--profile", default="draft")
    draft_run.add_argument("--model-config")
    draft_run.add_argument("--context-file")
    draft_run.add_argument("--plan-file")
    draft_run.add_argument("--brief")
    draft_run.add_argument("--brief-file")
    draft_run.add_argument("--requirement", action="append")
    draft_run.add_argument("--target-words", type=int, default=3000)
    draft_run.add_argument("--output-file", required=True)
    draft_run.add_argument("--timeout", type=int, default=240)
    draft_run.add_argument("--dry-run", action="store_true")
    draft_run.set_defaults(func=cmd_draft_run)

    init = sub.add_parser("init")
    init.add_argument("--root", default=".")
    init.add_argument("--mcp-url", required=True)
    init.add_argument("--workspace", required=True)
    init.add_argument("--project", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--description")
    init.add_argument("--client-id", default="codex-local")
    init.add_argument("--api-token")
    init.set_defaults(func=cmd_init)

    context = sub.add_parser("context")
    context.add_argument("--root", default=".")
    context.add_argument("--api-token")
    context.add_argument("--chapter", type=int, required=True)
    context.add_argument("--purpose", default="draft")
    context.add_argument("--focus", action="append")
    context.add_argument("--profile", help="指定要包含的设定 profile")
    context.add_argument("--pov", help="指定 POV 角色")
    context.add_argument("--recent-count", type=int, default=8)
    context.add_argument("--memory-limit", type=int, default=20)
    context.add_argument("--offline", action="store_true", help="离线模式，只使用缓存")
    context.set_defaults(func=cmd_context)

    context_list = sub.add_parser("context-list")
    context_list.add_argument("--root", default=".")
    context_list.set_defaults(func=cmd_context_list)

    context_clear = sub.add_parser("context-clear")
    context_clear.add_argument("--root", default=".")
    context_clear.add_argument("--chapter", type=int, help="清除指定章节的缓存（不指定则清除全部）")
    context_clear.set_defaults(func=cmd_context_clear)

    commit = sub.add_parser("commit")
    commit.add_argument("--root", default=".")
    commit.add_argument("--api-token")
    commit.add_argument("--chapter", type=int, required=True)
    commit.add_argument("--title", required=True)
    commit.add_argument("--summary", required=True)
    commit.add_argument("--chapter-file", required=True)
    commit.add_argument("--events-file")
    commit.add_argument("--encoding", default="utf-8")
    commit.add_argument("--accept", action=argparse.BooleanOptionalAction, default=True)
    commit.add_argument("--commit-type", choices=["draft", "final"], default="draft",
                        help="提交类型: draft(草稿,不污染正式状态) 或 final(正式,更新所有状态)")
    commit.add_argument("--offline", action="store_true", help="离线模式，提交到本地队列")
    commit.set_defaults(func=cmd_commit)

    # 离线队列命令
    queue_list = sub.add_parser("queue-list")
    queue_list.add_argument("--root", default=".")
    queue_list.set_defaults(func=cmd_queue_list)

    queue_sync = sub.add_parser("queue-sync")
    queue_sync.add_argument("--root", default=".")
    queue_sync.add_argument("--api-token")
    queue_sync.set_defaults(func=cmd_queue_sync)

    review_start = sub.add_parser("review-start")
    review_start.add_argument("--root", default=".")
    review_start.add_argument("--api-token")
    review_start.add_argument("--chapter", type=int, required=True)
    review_start.add_argument("--chapter-file")
    review_start.add_argument("--dimension", action="append")
    review_start.set_defaults(func=cmd_review_start)

    review_submit = sub.add_parser("review-submit")
    review_submit.add_argument("--root", default=".")
    review_submit.add_argument("--api-token")
    review_submit.add_argument("--review-job-id", required=True)
    review_submit.add_argument("--report-file", required=True)
    review_submit.add_argument("--model-id", default="manual-reviewer")
    review_submit.add_argument("--local-report-file")
    review_submit.set_defaults(func=cmd_review_submit)

    review_run = sub.add_parser("review-run")
    review_run.add_argument("--root", default=".")
    review_run.add_argument("--api-token")
    review_run.add_argument("--chapter", type=int, required=True)
    review_run.add_argument("--volume", type=int, default=1)
    review_run.add_argument("--chapter-file", required=True)
    review_run.add_argument("--context-file")
    review_run.add_argument("--models-file")
    review_run.add_argument("--model-config")
    review_run.add_argument("--profile", default="review")
    review_run.add_argument("--dimension", action="append")
    review_run.add_argument("--encoding", default="utf-8")
    review_run.add_argument("--timeout", type=int, default=120)
    review_run.add_argument("--dry-run", action="store_true")
    review_run.add_argument("--aggregate", action=argparse.BooleanOptionalAction, default=True)
    review_run.add_argument("--continue-on-error", action=argparse.BooleanOptionalAction, default=True)
    review_run.set_defaults(func=cmd_review_run)

    review_aggregate = sub.add_parser("review-aggregate")
    review_aggregate.add_argument("--root", default=".")
    review_aggregate.add_argument("--api-token")
    review_aggregate.add_argument("--review-job-id", required=True)
    review_aggregate.add_argument("--create-revision-tasks", action=argparse.BooleanOptionalAction, default=True)
    review_aggregate.set_defaults(func=cmd_review_aggregate)

    vector_pending = sub.add_parser("vector-pending")
    vector_pending.add_argument("--root", default=".")
    vector_pending.add_argument("--api-token")
    vector_pending.add_argument("--limit", type=int, default=20)
    vector_pending.set_defaults(func=cmd_vector_pending)

    vector_upsert = sub.add_parser("vector-upsert")
    vector_upsert.add_argument("--root", default=".")
    vector_upsert.add_argument("--api-token")
    vector_upsert.add_argument("--chunk-id")
    vector_upsert.add_argument("--embedding-file", required=True)
    vector_upsert.add_argument("--collection")
    vector_upsert.set_defaults(func=cmd_vector_upsert)

    vector_run = sub.add_parser("vector-run")
    vector_run.add_argument("--root", default=".")
    vector_run.add_argument("--api-token")
    vector_run.add_argument("--limit", type=int, default=50)
    vector_run.add_argument("--batch-size", type=int, default=16)
    vector_run.add_argument("--profile", default="embedding")
    vector_run.add_argument("--model-config")
    vector_run.add_argument("--collection")
    vector_run.add_argument("--timeout", type=int, default=120)
    vector_run.add_argument("--dry-run", action="store_true")
    vector_run.add_argument("--continue-on-error", action=argparse.BooleanOptionalAction, default=True)
    vector_run.set_defaults(func=cmd_vector_run)

    rules_evolve = sub.add_parser("rules-evolve")
    rules_evolve.add_argument("--root", default=".")
    rules_evolve.add_argument("--api-token")
    rules_evolve.add_argument("--review-job-id")
    rules_evolve.add_argument("--aggregate-file")
    rules_evolve.add_argument("--severity", action="append")
    rules_evolve.add_argument("--limit", type=int, default=10)
    rules_evolve.add_argument("--dry-run", action="store_true")
    rules_evolve.add_argument("--auto-apply", action="store_true")
    rules_evolve.set_defaults(func=cmd_rules_evolve)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
