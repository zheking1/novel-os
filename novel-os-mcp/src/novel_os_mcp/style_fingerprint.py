"""
Style Consistency Fingerprinting Service

Tracks writing style across 20M+ character novels:
  - Narrative POV consistency
  - Sentence structure patterns
  - Dialogue style anchoring
  - Emotional tone baseline
  - Vocabulary fingerprint
"""

import re
from collections import Counter
from typing import Any

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value


class StyleFingerprintService:
    """Tracks and checks writing style consistency."""

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # Style Profile Recording
    # ------------------------------------------------------------------

    async def create_style_profile(
        self,
        project_id: str,
        profile_name: str = "default",
        narrative_pov: str = "third_limited",
        tense: str = "past",
        tone: str = "neutral",
        target_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a style profile for the project."""
        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO style_profiles
                      (project_id, profile_name, narrative_pov, tense, tone, target_metrics)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                    ON CONFLICT (project_id, profile_name)
                    DO UPDATE SET narrative_pov = EXCLUDED.narrative_pov,
                                 tense = EXCLUDED.tense,
                                 tone = EXCLUDED.tone,
                                 target_metrics = EXCLUDED.target_metrics,
                                 updated_at = now()
                    RETURNING id::text, profile_name, narrative_pov, tense, tone,
                              target_metrics, created_at, updated_at
                    """,
                    project_id,
                    profile_name,
                    narrative_pov,
                    tense,
                    tone,
                    json_dumps(target_metrics or {}),
                )
        return row_to_dict(row)

    async def get_style_profile(
        self,
        project_id: str,
        profile_name: str = "default",
    ) -> dict[str, Any] | None:
        row = await self._db.fetchrow(
            """
            SELECT id::text, profile_name, narrative_pov, tense, tone,
                   target_metrics, created_at, updated_at
            FROM style_profiles
            WHERE project_id = $1 AND profile_name = $2
            """,
            project_id,
            profile_name,
        )
        return row_to_dict(row) if row else None

    # ------------------------------------------------------------------
    # Chapter Style Analysis
    # ------------------------------------------------------------------

    async def analyze_chapter_style(
        self,
        project_id: str,
        chapter_no: int,
        content: str,
    ) -> dict[str, Any]:
        """Analyze style metrics of a chapter."""
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        sentences = re.split(r'[.!?。！？]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        word_count = len(content)
        char_count = len(content)
        para_count = len(paragraphs)
        sentence_count = len(sentences)

        avg_sentence_len = word_count / max(sentence_count, 1)
        avg_para_len = word_count / max(para_count, 1)

        dialogue_lines = re.findall(r'[""「」『』][^""「」『』]+[""「」『』]', content)
        dialogue_ratio = len(dialogue_lines) / max(para_count, 1)

        exclamations = content.count("!") + content.count("！")
        questions = content.count("?") + content.count("？")
        ellipses = content.count("...") + content.count("……")

        punctuation_density = (exclamations + questions + ellipses) / max(word_count, 1) * 1000

        cn_chars = re.findall(r'[\u4e00-\u9fff]', content)
        en_words = re.findall(r'[a-zA-Z]+', content)
        cn_ratio = len(cn_chars) / max(len(cn_chars) + len(en_words), 1)

        vocab = Counter(cn_chars + [w.lower() for w in en_words])
        unique_words = len(vocab)
        vocab_richness = unique_words / max(word_count, 1)

        pov_markers_first = len(re.findall(r'[\u6211\u54ea\u5168\u5DF2\u5404\u5207]|\b(I|me|my|mine|we|us|our)\b', content))
        pov_markers_third = len(re.findall(r'[\u4ED6\u5979\u5B83\u4ED6\u4EEC]|\b(he|she|his|her|him|they|them|their)\b', content))
        pov_detected = "first" if pov_markers_first > pov_markers_third else "third"

        style_data = {
            "word_count": word_count,
            "char_count": char_count,
            "paragraph_count": para_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_len, 1),
            "avg_paragraph_length": round(avg_para_len, 1),
            "dialogue_ratio": round(dialogue_ratio, 3),
            "exclamation_count": exclamations,
            "question_count": questions,
            "ellipsis_count": ellipses,
            "punctuation_density": round(punctuation_density, 2),
            "cn_ratio": round(cn_ratio, 3),
            "vocab_richness": round(vocab_richness, 3),
            "pov_detected": pov_detected,
            "top_words": vocab.most_common(20),
        }

        async with self._db.acquire() as conn:
            async with conn.transaction():
                await conn.fetchrow(
                    """
                    INSERT INTO chapter_style_metrics
                      (project_id, chapter_no, style_data)
                    VALUES ($1, $2, $3::jsonb)
                    ON CONFLICT (project_id, chapter_no)
                    DO UPDATE SET style_data = EXCLUDED.style_data, updated_at = now()
                    """,
                    project_id,
                    chapter_no,
                    json_dumps(style_data),
                )

        return style_data

    async def get_chapter_style(
        self,
        project_id: str,
        chapter_no: int,
    ) -> dict[str, Any] | None:
        row = await self._db.fetchrow(
            """
            SELECT chapter_no, style_data, created_at, updated_at
            FROM chapter_style_metrics
            WHERE project_id = $1 AND chapter_no = $2
            """,
            project_id,
            chapter_no,
        )
        if not row:
            return None
        data = row_to_dict(row)
        data["style_data"] = ensure_json_value(data.get("style_data") or {})
        return data

    # ------------------------------------------------------------------
    # Style Drift Detection
    # ------------------------------------------------------------------

    async def detect_style_drift(
        self,
        project_id: str,
        chapter_no: int,
        window: int = 20,
        threshold: float = 0.3,
    ) -> dict[str, Any]:
        """Detect style drift from established baseline."""
        current = await self.get_chapter_style(project_id, chapter_no)
        if not current:
            return {"chapter_no": chapter_no, "drift_detected": False, "reason": "no_current_data"}

        current_data = current.get("style_data", {})

        baseline_start = max(1, chapter_no - window)
        baseline_rows = await self._db.fetch(
            """
            SELECT style_data FROM chapter_style_metrics
            WHERE project_id = $1 AND chapter_no >= $2 AND chapter_no < $3
            ORDER BY chapter_no
            """,
            project_id,
            baseline_start,
            chapter_no,
        )
        baselines = [ensure_json_value(r["style_data"]) for r in baseline_rows]
        if not baselines:
            return {"chapter_no": chapter_no, "drift_detected": False, "reason": "no_baseline_data"}

        metrics_to_check = [
            "avg_sentence_length",
            "avg_paragraph_length",
            "dialogue_ratio",
            "punctuation_density",
            "vocab_richness",
        ]

        drifts = []
        for metric in metrics_to_check:
            current_val = current_data.get(metric, 0)
            baseline_vals = [b.get(metric, 0) for b in baselines if b.get(metric) is not None]
            if not baseline_vals:
                continue
            baseline_avg = sum(baseline_vals) / len(baseline_vals)
            baseline_std = (sum((v - baseline_avg) ** 2 for v in baseline_vals) / len(baseline_vals)) ** 0.5

            if baseline_std > 0:
                z_score = abs(current_val - baseline_avg) / baseline_std
                if z_score > 2.0:
                    drifts.append({
                        "metric": metric,
                        "current": round(current_val, 3),
                        "baseline_avg": round(baseline_avg, 3),
                        "baseline_std": round(baseline_std, 3),
                        "z_score": round(z_score, 2),
                        "direction": "above" if current_val > baseline_avg else "below",
                    })

        pov_values = [b.get("pov_detected") for b in baselines]
        dominant_pov = max(set(pov_values), key=pov_values.count) if pov_values else None
        current_pov = current_data.get("pov_detected")
        pov_consistent = current_pov == dominant_pov

        return {
            "chapter_no": chapter_no,
            "drift_detected": len(drifts) > 0 or not pov_consistent,
            "drift_count": len(drifts),
            "drifts": drifts,
            "pov_consistent": pov_consistent,
            "pov_expected": dominant_pov,
            "pov_actual": current_pov,
        }

    # ------------------------------------------------------------------
    # Style Summary for Context
    # ------------------------------------------------------------------

    async def get_style_summary_for_context(
        self,
        project_id: str,
        chapter_no: int,
        max_tokens: int = 150,
    ) -> str:
        """Get compressed style summary for context injection."""
        profile = await self.get_style_profile(project_id)
        recent_styles = await self._db.fetch(
            """
            SELECT chapter_no, style_data FROM chapter_style_metrics
            WHERE project_id = $1 AND chapter_no < $2
            ORDER BY chapter_no DESC LIMIT 5
            """,
            project_id,
            chapter_no,
        )
        lines = ["== Style Context =="]
        if profile:
            lines.append(f"  POV: {profile['narrative_pov']}, Tense: {profile['tense']}, Tone: {profile['tone']}")

        if recent_styles:
            metrics = [ensure_json_value(r["style_data"]) for r in recent_styles]
            avg_sent = sum(m.get("avg_sentence_length", 0) for m in metrics) / len(metrics)
            avg_para = sum(m.get("avg_paragraph_length", 0) for m in metrics) / len(metrics)
            avg_dial = sum(m.get("dialogue_ratio", 0) for m in metrics) / len(metrics)
            lines.append(f"  Recent avg: sent={avg_sent:.0f}chars, para={avg_para:.0f}chars, dialogue={avg_dial:.1%}")

            pvs = [m.get("pov_detected", "?") for m in metrics]
            dominant_pv = max(set(pvs), key=pvs.count)
            lines.append(f"  Dominant POV: {dominant_pv}")

        summary = "\n".join(lines)
        char_budget = max_tokens * 4
        if len(summary) > char_budget:
            summary = summary[:char_budget] + "..."
        return summary

    # ------------------------------------------------------------------
    # Batch Analysis
    # ------------------------------------------------------------------

    async def batch_analyze_chapters(
        self,
        project_id: str,
        from_chapter: int,
        to_chapter: int,
    ) -> dict[str, Any]:
        """Batch analyze style for a range of chapters."""
        chapters = await self._db.fetch(
            """
            SELECT id, chapter_no, content
            FROM chapters
            WHERE project_id = $1 AND chapter_no >= $2 AND chapter_no <= $3
            ORDER BY chapter_no
            """,
            project_id,
            from_chapter,
            to_chapter,
        )
        results = []
        for ch in chapters:
            content = ch.get("content", "")
            if content:
                r = await self.analyze_chapter_style(project_id, ch["chapter_no"], content)
                results.append({"chapter_no": ch["chapter_no"], **r})

        return {
            "ok": True,
            "analyzed_count": len(results),
            "chapter_range": [from_chapter, to_chapter],
        }

    async def get_style_trend(
        self,
        project_id: str,
        from_chapter: int | None = None,
        to_chapter: int | None = None,
        metric: str = "avg_sentence_length",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get trend data for a specific style metric."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2
        if from_chapter is not None:
            conditions.append(f"chapter_no >= ${idx}")
            params.append(from_chapter)
            idx += 1
        if to_chapter is not None:
            conditions.append(f"chapter_no <= ${idx}")
            params.append(to_chapter)
            idx += 1
        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT chapter_no, style_data
            FROM chapter_style_metrics
            WHERE {' AND '.join(conditions)}
            ORDER BY chapter_no
            LIMIT ${idx}
            """,
            *params,
        )
        return [
            {
                "chapter_no": r["chapter_no"],
                "value": (ensure_json_value(r.get("style_data") or {})).get(metric),
            }
            for r in rows
        ]

