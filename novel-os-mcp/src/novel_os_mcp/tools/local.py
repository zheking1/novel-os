import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, knowledge_service
from ..local_service import LocalService
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.local")

local_service = LocalService(db)


@mcp.tool(name="local.project.register")
async def local_project_register(
    project_id: str,
    local_root: str,
) -> dict[str, Any]:
    """注册本地项目目录。将本地目录与项目关联，用于后续扫描和索引同步。"""
    principal = await get_principal("write")
    validate_required(locals(), "project_id", "local_root")
    result = await local_service.register_project(project_id, local_root)
    logger.info("local_project_register: %s → %s", project_id, local_root)
    return result


@mcp.tool(name="local.project.list")
async def local_project_list() -> dict[str, Any]:
    """列出所有已注册的本地项目。返回项目根目录、文件数、总字数等信息。"""
    principal = await get_principal("read")
    projects = await local_service.list_projects()
    return {"projects": projects, "count": len(projects)}


@mcp.tool(name="local.project.scan")
async def local_project_scan(
    project_id: str,
    local_root: str,
) -> dict[str, Any]:
    """扫描本地项目目录。构建章节、设定、审查的索引，同步到 DB 并写入 .novel-index.json。"""
    principal = await get_principal("write")
    validate_required(locals(), "project_id", "local_root")
    result = await local_service.scan_directory(project_id, local_root)
    logger.info("local_project_scan: %s, %d chapters, %d settings", project_id, len(result["chapters"]), len(result["settings"]))
    return {
        "chapters": result["chapters"],
        "settings": result["settings"],
        "file_count": result["file_count"],
        "total_words": result["total_words"],
    }


@mcp.tool(name="local.chapter.list")
async def local_chapter_list(
    project_id: str,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """列出章节（从 DB 索引）。返回章节元数据（编号、标题、状态、字数、摘要），不返回正文。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id")
    chapters = await local_service.list_chapters(project_id, status, limit, offset)
    return {"chapters": chapters, "count": len(chapters)}


@mcp.tool(name="local.chapter.get")
async def local_chapter_get(
    project_id: str,
    chapter_no: int,
) -> dict[str, Any]:
    """获取章节元数据。返回编号、标题、状态、字数、摘要、本地路径。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id", "chapter_no")
    chapter = await local_service.get_chapter(project_id, chapter_no)
    if not chapter:
        return {"error": f"章节 {chapter_no} 不存在"}
    return chapter


@mcp.tool(name="local.chapter.read")
async def local_chapter_read(
    project_id: str,
    chapter_no: int,
    version: str = "final",
) -> dict[str, Any]:
    """读取章节正文（从本地文件）。按需加载，不经过 DB。version: draft/final。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id", "chapter_no")
    content = await local_service.get_chapter_content(project_id, chapter_no, version)
    if content is None:
        return {"error": f"章节 {chapter_no} ({version}) 不存在"}
    return {"chapter_no": chapter_no, "version": version, "content": content, "word_count": len(content)}


@mcp.tool(name="local.chapter.write")
async def local_chapter_write(
    project_id: str,
    chapter_no: int,
    content: str,
    version: str = "draft",
) -> dict[str, Any]:
    """写入章节正文到本地。自动生成文件路径并创建目录。"""
    principal = await get_principal("write")
    validate_required(locals(), "project_id", "chapter_no", "content")
    project = await local_service.get_project(project_id)
    if not project:
        return {"error": "项目未注册"}
    rel_path = f"第{chapter_no:02d}章/ch{chapter_no:02d}_{version}.md"
    result = await local_service.write_file(project["local_root"], rel_path, content)
    logger.info("local_chapter_write: %s ch%d %s, %d words", project_id, chapter_no, version, result["word_count"])
    return {"chapter_no": chapter_no, "version": version, **result}


@mcp.tool(name="local.chapter.write_outline")
async def local_chapter_write_outline(
    project_id: str,
    chapter_no: int,
    outline: str,
) -> dict[str, Any]:
    """写入章纲到本地。生成 ch{N}_outline.md。"""
    principal = await get_principal("write")
    validate_required(locals(), "project_id", "chapter_no", "outline")
    project = await local_service.get_project(project_id)
    if not project:
        return {"error": "项目未注册"}
    rel_path = f"第{chapter_no:02d}章/ch{chapter_no:02d}_outline.md"
    result = await local_service.write_file(project["local_root"], rel_path, outline)
    return {"chapter_no": chapter_no, "type": "outline", **result}


@mcp.tool(name="local.review.write")
async def local_review_write(
    project_id: str,
    chapter_no: int,
    model_name: str,
    report: str,
    score: float | None = None,
    passed: bool | None = None,
    issues: list[dict] | None = None,
) -> dict[str, Any]:
    """写入审查报告到本地。生成 审查报告/{model_name}_report.md。"""
    principal = await get_principal("write")
    validate_required(locals(), "project_id", "chapter_no", "model_name", "report")
    project = await local_service.get_project(project_id)
    if not project:
        return {"error": "项目未注册"}
    rel_path = f"第{chapter_no:02d}章/审查报告/{model_name}_report.md"
    result = await local_service.write_file(project["local_root"], rel_path, report)

    # 写入审查索引
    await local_service._db.connect()
    chapter = await local_service.get_chapter(project_id, chapter_no)
    await local_service._db.execute(
        """INSERT INTO review_index (project_id, chapter_id, chapter_no, model_name, score, passed, issues, summary, local_path)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
        project_id,
        chapter["id"] if chapter else None,
        chapter_no,
        model_name,
        score,
        passed,
        issues or [],
        report[:500],
        rel_path,
    )
    return {"chapter_no": chapter_no, "model_name": model_name, **result}


@mcp.tool(name="local.review.list")
async def local_review_list(
    project_id: str,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """列出审查记录（从 DB 索引）。返回评分、状态、问题列表。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id")
    reviews = await local_service.list_reviews(project_id, chapter_no)
    return {"reviews": reviews, "count": len(reviews)}


@mcp.tool(name="local.review.read")
async def local_review_read(
    project_id: str,
    review_id: str,
) -> dict[str, Any]:
    """读取审查报告全文（从本地文件）。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id", "review_id")
    content = await local_service.get_review_content(project_id, review_id)
    if content is None:
        return {"error": "审查报告不存在"}
    return {"review_id": review_id, "content": content}


@mcp.tool(name="local.setting.list")
async def local_setting_list(
    project_id: str,
    category: str | None = None,
) -> dict[str, Any]:
    """列出设定（从 DB 索引）。返回名称、分类、摘要、关键词。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id")
    await local_service._db.connect()
    if category:
        rows = await local_service._db.fetch(
            "SELECT * FROM setting_index WHERE project_id = $1 AND category = $2 ORDER BY name",
            project_id, category,
        )
    else:
        rows = await local_service._db.fetch(
            "SELECT * FROM setting_index WHERE project_id = $1 ORDER BY category, name",
            project_id,
        )
    from ..utils import rows_to_dicts
    settings = rows_to_dicts(rows)
    return {"settings": settings, "count": len(settings)}


@mcp.tool(name="local.setting.read")
async def local_setting_read(
    project_id: str,
    local_path: str,
) -> dict[str, Any]:
    """读取设定文件内容（从本地）。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id", "local_path")
    project = await local_service.get_project(project_id)
    if not project:
        return {"error": "项目未注册"}
    content = await local_service.read_file(project["local_root"], local_path)
    return {"local_path": local_path, "content": content}


@mcp.tool(name="local.stats")
async def local_stats(project_id: str) -> dict[str, Any]:
    """获取本地项目统计信息。章节数、总字数、各状态章节分布。"""
    principal = await get_principal("read")
    validate_required(locals(), "project_id")
    project = await local_service.get_project(project_id)
    if not project:
        return {"error": "项目未注册"}
    await local_service._db.connect()
    chapters = await local_service._db.fetch(
        "SELECT status, COUNT(*) as count, SUM(word_count) as words FROM chapter_index WHERE project_id = $1 GROUP BY status",
        project_id,
    )
    status_dist = {r["status"]: {"count": r["count"], "words": r["words"]} for r in chapters}
    total = await local_service._db.fetchrow(
        "SELECT COUNT(*) as ch_count, SUM(word_count) as total_words FROM chapter_index WHERE project_id = $1",
        project_id,
    )
    return {
        "project_id": project_id,
        "local_root": project["local_root"],
        "chapter_count": total["ch_count"],
        "total_words": total["total_words"] or 0,
        "status_distribution": status_dist,
    }
