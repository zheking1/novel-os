"""
Novelty Detection Service

Detects repetitive patterns in 20M+ character novels:
  - Scene/plot repetition (vector semantic similarity)
  - Description deduplication
  - Dialogue pattern detection
"""

import re
from collections import Counter
from typing import Any

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value
from .vector import VectorIndex


class NoveltyService:
    """Detects repetitive patterns and novelty issues."""

    def __init__(self, db: Database, vector_index: VectorIndex | None = None):
        self._db = db
        self._vector = vector_index
        self._embedding_fn = None

    async def _get_embedding(self, text: str) -> list[float] | None:
        """Get embedding vector for text. Returns None if no embedding service available."""
        if self._embedding_fn:
            return await self._embedding_fn(text)
        return None

    def set_embedding_function(self, fn):
        """Set custom embedding function: async fn(text) -> list[float]"""
        self._embedding_fn = fn

    # ------------------------------------------------------------------
    # Scene Similarity
    # ------------------------------------------------------------------

    async def check_scene_novelty(
        self,
        project_id: str,
        chapter_no: int,
        scene_description: str,
        window: int = 50,
        threshold: float = 0.6,
    ) -> dict[str, Any]:
        """Check if a scene is too similar to recent scenes.
        Uses vector semantic similarity when available, falls back to keyword matching.
        """
        if self._vector:
            return await self._check_scene_vector(project_id, chapter_no, scene_description, threshold)

        recent_events = await self._db.fetch(
            """
            SELECT e.title, e.summary, e.chapter_id::text,
                   c.chapter_no, c.title AS chapter_title
            FROM events e
            JOIN chapters c ON c.id = e.chapter_id
            WHERE c.project_id = $1 AND c.chapter_no >= $2 AND c.chapter_no < $3
            ORDER BY c.chapter_no DESC, e.event_order
            LIMIT 100
            """,
            project_id,
            max(1, chapter_no - window),
            chapter_no,
        )
        events = rows_to_dicts(recent_events)

        similar = []
        scene_keywords = self._extract_keywords(scene_description)
        for event in events:
            event_keywords = self._extract_keywords(
                (event.get("summary", "") or "") + " " + (event.get("title", "") or "")
            )
            similarity = self._keyword_similarity(scene_keywords, event_keywords)
            if similarity >= threshold:
                similar.append({
                    "chapter_no": event["chapter_no"],
                    "chapter_title": event.get("chapter_title"),
                    "event_title": event.get("title"),
                    "similarity": round(similarity, 3),
                })

        return {
            "chapter_no": chapter_no,
            "is_novel": len(similar) == 0,
            "similar_count": len(similar),
            "similar_scenes": similar[:5],
            "threshold": threshold,
            "method": "keyword",
        }

    async def _check_scene_vector(
        self,
        project_id: str,
        chapter_no: int,
        scene_description: str,
        threshold: float,
    ) -> dict[str, Any]:
        """Vector-based scene novelty check using Qdrant."""
        embedding = await self._get_embedding(scene_description)
        if not embedding:
            return {"chapter_no": chapter_no, "is_novel": True, "reason": "no_embedding_service", "method": "vector"}

        results = await self._vector.search(
            collection="novel_events",
            vector=embedding,
            limit=10,
            project_id=project_id,
        )

        similar = []
        for r in results:
            score = r.get("score", 0)
            payload = r.get("payload", {})
            if score >= threshold and payload.get("chapter_no", 0) < chapter_no:
                similar.append({
                    "chapter_no": payload.get("chapter_no"),
                    "event_title": payload.get("title"),
                    "similarity": round(score, 3),
                    "method": "vector",
                })

        return {
            "chapter_no": chapter_no,
            "is_novel": len(similar) == 0,
            "similar_count": len(similar),
            "similar_scenes": similar[:5],
            "threshold": threshold,
            "method": "vector",
        }

    # ------------------------------------------------------------------
    # Description Deduplication
    # ------------------------------------------------------------------

    async def check_description_novelty(
        self,
        project_id: str,
        chapter_no: int,
        description: str,
        description_type: str = "general",
        window: int = 100,
        threshold: float = 0.7,
    ) -> dict[str, Any]:
        """Check if a description is too similar to recent descriptions."""
        recent_chunks = await self._db.fetch(
            """
            SELECT mc.content, mc.metadata, mc.chunk_key
            FROM memory_chunks mc
            WHERE mc.project_id = $1
              AND mc.source_type = 'event'
              AND mc.chunk_key LIKE 'chapter:%'
            ORDER BY mc.created_at DESC
            LIMIT 200
            """,
            project_id,
        )
        chunks = rows_to_dicts(recent_chunks)

        desc_keywords = self._extract_keywords(description)
        similar = []
        for chunk in chunks:
            content = chunk.get("content", "")
            chunk_keywords = self._extract_keywords(content)
            similarity = self._keyword_similarity(desc_keywords, chunk_keywords)
            if similarity >= threshold:
                meta = ensure_json_value(chunk.get("metadata") or {})
                similar.append({
                    "chunk_key": chunk.get("chunk_key"),
                    "chapter_no": meta.get("chapter_no"),
                    "similarity": round(similarity, 3),
                    "preview": content[:100],
                })

        return {
            "chapter_no": chapter_no,
            "description_type": description_type,
            "is_novel": len(similar) == 0,
            "similar_count": len(similar),
            "similar_descriptions": similar[:5],
            "threshold": threshold,
        }

    # ------------------------------------------------------------------
    # Dialogue Pattern Detection
    # ------------------------------------------------------------------

    async def check_dialogue_patterns(
        self,
        project_id: str,
        chapter_no: int,
        dialogues: list[dict[str, Any]],
        window: int = 30,
    ) -> dict[str, Any]:
        """Check for repetitive dialogue patterns."""
        recent_chapters = await self._db.fetch(
            """
            SELECT c.chapter_no, s.content
            FROM chapters c
            JOIN chapter_summaries s ON s.chapter_id = c.id AND s.summary_type = 'chapter'
            WHERE c.project_id = $1 AND c.chapter_no >= $2 AND c.chapter_no < $3
            ORDER BY c.chapter_no
            """,
            project_id,
            max(1, chapter_no - window),
            chapter_no,
        )
        summaries = rows_to_dicts(recent_chapters)

        new_patterns = self._extract_dialogue_patterns(dialogues)
        existing_patterns = []
        for s in summaries:
            content = s.get("content", "")
            existing_patterns.extend(self._extract_dialogue_patterns_from_text(content))

        overlaps = []
        for np in new_patterns:
            for ep in existing_patterns:
                sim = self._phrase_similarity(np["phrase"], ep["phrase"])
                if sim > 0.8:
                    overlaps.append({
                        "new_phrase": np["phrase"],
                        "existing_phrase": ep["phrase"],
                        "similarity": round(sim, 3),
                        "existing_chapter": ep.get("chapter_no"),
                    })

        return {
            "chapter_no": chapter_no,
            "dialogue_count": len(dialogues),
            "new_patterns_count": len(new_patterns),
            "overlaps_found": len(overlaps),
            "overlaps": overlaps[:5],
            "is_novel": len(overlaps) == 0,
        }

    # ------------------------------------------------------------------
    # Plot Beat Detection
    # ------------------------------------------------------------------

    async def check_plot_beat_novelty(
        self,
        project_id: str,
        chapter_no: int,
        plot_beats: list[str],
        window: int = 100,
        threshold: float = 0.5,
    ) -> dict[str, Any]:
        """Check if plot beats are repetitive."""
        recent_events = await self._db.fetch(
            """
            SELECT e.title, e.summary, c.chapter_no
            FROM events e
            JOIN chapters c ON c.id = e.chapter_id
            WHERE c.project_id = $1 AND c.chapter_no >= $2 AND c.chapter_no < $3
            ORDER BY c.chapter_no DESC
            LIMIT 200
            """,
            project_id,
            max(1, chapter_no - window),
            chapter_no,
        )
        events = rows_to_dicts(recent_events)

        repetitive_beats = []
        for beat in plot_beats:
            beat_keywords = self._extract_keywords(beat)
            for event in events:
                event_text = (event.get("summary", "") or "") + " " + (event.get("title", "") or "")
                event_keywords = self._extract_keywords(event_text)
                sim = self._keyword_similarity(beat_keywords, event_keywords)
                if sim >= threshold:
                    repetitive_beats.append({
                        "beat": beat,
                        "similar_event": event.get("title"),
                        "chapter_no": event.get("chapter_no"),
                        "similarity": round(sim, 3),
                    })
                    break

        return {
            "chapter_no": chapter_no,
            "total_beats": len(plot_beats),
            "repetitive_beats": len(repetitive_beats),
            "is_novel": len(repetitive_beats) == 0,
            "details": repetitive_beats[:5],
        }

    # ------------------------------------------------------------------
    # Comprehensive Novelty Report
    # ------------------------------------------------------------------

    async def full_novelty_check(
        self,
        project_id: str,
        chapter_no: int,
        content: str,
        scene_description: str | None = None,
        dialogues: list[dict[str, Any]] | None = None,
        plot_beats: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run all novelty checks and produce a report."""
        results = {}

        if scene_description:
            results["scene"] = await self.check_scene_novelty(
                project_id, chapter_no, scene_description,
            )

        results["description"] = await self.check_description_novelty(
            project_id, chapter_no, content[:2000],
        )

        if dialogues:
            results["dialogue"] = await self.check_dialogue_patterns(
                project_id, chapter_no, dialogues,
            )

        if plot_beats:
            results["plot_beats"] = await self.check_plot_beat_novelty(
                project_id, chapter_no, plot_beats,
            )

        issues = []
        for check_name, check_result in results.items():
            if not check_result.get("is_novel", True):
                issues.append({
                    "type": check_name,
                    "similar_count": check_result.get("similar_count", 0)
                        or check_result.get("overlaps_found", 0)
                        or check_result.get("repetitive_beats", 0),
                })

        return {
            "chapter_no": chapter_no,
            "is_novel": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues,
            "checks": results,
        }

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _extract_keywords(self, text: str) -> Counter:
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '让', '用', '对',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
            'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'under', 'again',
            'and', 'but', 'or', 'nor', 'not', 'so', 'if', 'then', 'than',
            'this', 'that', 'these', 'those', 'it', 'its', 'he', 'she', 'they',
            'his', 'her', 'their', 'my', 'your', 'our', 'me', 'him', 'us',
        }
        return Counter(w for w in words if w not in stopwords and len(w) > 1)

    def _keyword_similarity(self, kw1: Counter, kw2: Counter) -> float:
        if not kw1 or not kw2:
            return 0.0
        common = set(kw1.keys()) & set(kw2.keys())
        total = set(kw1.keys()) | set(kw2.keys())
        return len(common) / len(total) if total else 0.0

    def _phrase_similarity(self, p1: str, p2: str) -> float:
        kw1 = self._extract_keywords(p1)
        kw2 = self._extract_keywords(p2)
        return self._keyword_similarity(kw1, kw2)

    def _extract_dialogue_patterns(self, dialogues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        patterns = []
        for d in dialogues:
            text = d.get("text", "")
            if text:
                patterns.append({
                    "speaker": d.get("speaker", ""),
                    "phrase": text[:100],
                })
        return patterns

    def _extract_dialogue_patterns_from_text(self, text: str) -> list[dict[str, Any]]:
        patterns = []
        quoted = re.findall(r'[""「」『』]([^""「」『』]+)[""「」『』]', text)
        for q in quoted:
            patterns.append({"phrase": q[:100]})
        return patterns

