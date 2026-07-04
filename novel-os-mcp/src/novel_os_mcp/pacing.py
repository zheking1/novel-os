"""
Pacing & Emotion Curve Modeling Service

Tracks and controls narrative rhythm for 20M+ character novels:
  - Volume-level pacing blueprints
  - Per-chapter emotion intensity
  - Tension/release cycles
  - Climax density control
  - Reader engagement prediction
"""

from datetime import datetime
from typing import Any

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts


class PacingService:
    """Manages pacing blueprints and emotion curves."""

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # Volume Pacing Blueprint
    # ------------------------------------------------------------------

    async def create_volume_blueprint(
        self,
        project_id: str,
        volume_no: int,
        blueprint: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a pacing blueprint for a volume.

        blueprint structure:
        {
          "target_arc_count": 3,
          "climax_chapters": [45, 80, 120],
          "breather_chapters": [46, 81],
          "tension_curve": {1: 0.3, 20: 0.5, 45: 0.9, 50: 0.4, ...},
          "emotion_targets": {"chapter_range": [1,50], "dominant_emotion": "hope", "intensity": 0.6},
          "pacing_notes": "Slow build to first climax, fast middle section"
        }
        """
        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO pacing_blueprints
                      (project_id, volume_no, blueprint)
                    VALUES ($1, $2, $3::jsonb)
                    ON CONFLICT (project_id, volume_no)
                    DO UPDATE SET blueprint = EXCLUDED.blueprint, updated_at = now()
                    RETURNING id::text, volume_no, blueprint, created_at, updated_at
                    """,
                    project_id,
                    volume_no,
                    json_dumps(blueprint),
                )
        return row_to_dict(row)

    async def get_volume_blueprint(
        self,
        project_id: str,
        volume_no: int,
    ) -> dict[str, Any] | None:
        row = await self._db.fetchrow(
            """
            SELECT id::text, volume_no, blueprint, created_at, updated_at
            FROM pacing_blueprints
            WHERE project_id = $1 AND volume_no = $2
            """,
            project_id,
            volume_no,
        )
        return row_to_dict(row) if row else None

    async def list_volume_blueprints(
        self,
        project_id: str,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, volume_no, blueprint, created_at, updated_at
            FROM pacing_blueprints
            WHERE project_id = $1
            ORDER BY volume_no
            """,
            project_id,
        )
        return rows_to_dicts(rows)

    # ------------------------------------------------------------------
    # Chapter Emotion Intensity
    # ------------------------------------------------------------------

    async def record_chapter_emotion(
        self,
        project_id: str,
        chapter_no: int,
        tension: float,
        emotion: str,
        emotion_intensity: float,
        pacing_type: str = "normal",
        word_count: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record emotion/tension data for a chapter.

        tension: 0.0 (calm) to 1.0 (extreme tension)
        pacing_type: buildup, climax, breather, transition, climax_buildup, resolution
        """
        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO chapter_emotions
                      (project_id, chapter_no, tension, emotion, emotion_intensity,
                       pacing_type, word_count, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                    ON CONFLICT (project_id, chapter_no)
                    DO UPDATE SET tension = EXCLUDED.tension,
                                 emotion = EXCLUDED.emotion,
                                 emotion_intensity = EXCLUDED.emotion_intensity,
                                 pacing_type = EXCLUDED.pacing_type,
                                 word_count = EXCLUDED.word_count,
                                 metadata = EXCLUDED.metadata,
                                 updated_at = now()
                    RETURNING id::text, chapter_no, tension, emotion, emotion_intensity,
                              pacing_type, word_count, created_at, updated_at
                    """,
                    project_id,
                    chapter_no,
                    tension,
                    emotion,
                    emotion_intensity,
                    pacing_type,
                    word_count,
                    json_dumps(metadata or {}),
                )
        return row_to_dict(row)

    async def get_chapter_emotion(
        self,
        project_id: str,
        chapter_no: int,
    ) -> dict[str, Any] | None:
        row = await self._db.fetchrow(
            """
            SELECT id::text, chapter_no, tension, emotion, emotion_intensity,
                   pacing_type, word_count, metadata, created_at, updated_at
            FROM chapter_emotions
            WHERE project_id = $1 AND chapter_no = $2
            """,
            project_id,
            chapter_no,
        )
        return row_to_dict(row) if row else None

    async def get_emotion_curve(
        self,
        project_id: str,
        from_chapter: int | None = None,
        to_chapter: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Get the emotion curve for a chapter range."""
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
            SELECT chapter_no, tension, emotion, emotion_intensity, pacing_type
            FROM chapter_emotions
            WHERE {' AND '.join(conditions)}
            ORDER BY chapter_no
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    # ------------------------------------------------------------------
    # Pacing Analysis
    # ------------------------------------------------------------------

    async def analyze_pacing_rhythm(
        self,
        project_id: str,
        from_chapter: int,
        to_chapter: int,
    ) -> dict[str, Any]:
        """Analyze pacing rhythm in a chapter range."""
        curve = await self.get_emotion_curve(project_id, from_chapter, to_chapter)
        if not curve:
            return {"ok": False, "reason": "no_data"}

        tensions = [c["tension"] for c in curve]
        avg_tension = sum(tensions) / len(tensions)
        max_tension = max(tensions)
        min_tension = min(tensions)

        climax_count = sum(1 for c in curve if c.get("pacing_type") == "climax")
        breather_count = sum(1 for c in curve if c.get("pacing_type") == "breather")
        buildup_count = sum(1 for c in curve if c.get("pacing_type") == "climax_buildup")

        transitions = []
        for i in range(1, len(curve)):
            prev = curve[i - 1]["tension"]
            curr = curve[i]["tension"]
            delta = curr - prev
            if abs(delta) > 0.3:
                transitions.append({
                    "from_chapter": curve[i - 1]["chapter_no"],
                    "to_chapter": curve[i]["chapter_no"],
                    "delta": round(delta, 3),
                    "direction": "sharp_rise" if delta > 0 else "sharp_drop",
                })

        avg_climax_gap = 0
        climax_chapters = [c["chapter_no"] for c in curve if c.get("pacing_type") == "climax"]
        if len(climax_chapters) > 1:
            gaps = [climax_chapters[i+1] - climax_chapters[i] for i in range(len(climax_chapters)-1)]
            avg_climax_gap = sum(gaps) / len(gaps)

        return {
            "ok": True,
            "chapter_range": [from_chapter, to_chapter],
            "total_chapters": len(curve),
            "avg_tension": round(avg_tension, 3),
            "max_tension": round(max_tension, 3),
            "min_tension": round(min_tension, 3),
            "tension_range": round(max_tension - min_tension, 3),
            "climax_count": climax_count,
            "breather_count": breather_count,
            "buildup_count": buildup_count,
            "avg_climax_gap": round(avg_climax_gap, 1),
            "sharp_transitions": transitions[:10],
        }

    async def check_pacing_health(
        self,
        project_id: str,
        from_chapter: int,
        to_chapter: int,
        volume_no: int | None = None,
    ) -> dict[str, Any]:
        """Check pacing health against blueprint and general rules."""
        analysis = await self.analyze_pacing_rhythm(project_id, from_chapter, to_chapter)
        if not analysis.get("ok"):
            return analysis

        issues = []
        warnings = []

        if analysis["total_chapters"] >= 10:
            if analysis["climax_count"] == 0:
                issues.append({
                    "type": "no_climax",
                    "severity": "warning",
                    "message": "No climax chapters in range — tension may feel flat",
                })
            elif analysis["climax_count"] > analysis["total_chapters"] * 0.3:
                issues.append({
                    "type": "too_many_climaxes",
                    "severity": "warning",
                    "message": f"Too many climaxes ({analysis['climax_count']}/{analysis['total_chapters']}) — reader fatigue risk",
                })

            if analysis["breather_count"] == 0 and analysis["climax_count"] > 2:
                issues.append({
                    "type": "no_breathers",
                    "severity": "info",
                    "message": "No breather chapters after multiple climaxes — add rest points",
                })

        if analysis["avg_tension"] > 0.8:
            warnings.append({
                "type": "sustained_high_tension",
                "message": f"Avg tension {analysis['avg_tension']:.2f} — sustained high tension may exhaust readers",
            })
        elif analysis["avg_tension"] < 0.2 and analysis["total_chapters"] > 20:
            warnings.append({
                "type": "sustained_low_tension",
                "message": f"Avg tension {analysis['avg_tension']:.2f} — long low-tension stretch may bore readers",
            })

        if volume_no:
            blueprint = await self.get_volume_blueprint(project_id, volume_no)
            if blueprint:
                bp = blueprint.get("blueprint") or {}
                expected_climaxes = bp.get("climax_chapters", [])
                if expected_climaxes:
                    in_range = [c for c in expected_climaxes if from_chapter <= c <= to_chapter]
                    actual_climaxes = analysis["climax_count"]
                    if len(in_range) > 0 and actual_climaxes == 0:
                        issues.append({
                            "type": "missed_planned_climax",
                            "severity": "error",
                            "message": f"Planned climax chapters {in_range} but no climax recorded",
                        })

        return {
            "ok": len([i for i in issues if i.get("severity") == "error"]) == 0,
            "analysis": analysis,
            "issues": issues,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Tension Curve Comparison
    # ------------------------------------------------------------------

    async def compare_to_blueprint(
        self,
        project_id: str,
        volume_no: int,
        from_chapter: int,
        to_chapter: int,
    ) -> dict[str, Any]:
        """Compare actual tension curve to planned blueprint."""
        blueprint = await self.get_volume_blueprint(project_id, volume_no)
        if not blueprint:
            return {"ok": False, "reason": "no_blueprint"}

        bp = blueprint.get("blueprint") or {}
        planned_curve = bp.get("tension_curve", {})
        if not planned_curve:
            return {"ok": False, "reason": "no_tension_curve_in_blueprint"}

        actual = await self.get_emotion_curve(project_id, from_chapter, to_chapter)
        if not actual:
            return {"ok": False, "reason": "no_actual_data"}

        planned_points = sorted(
            [(int(k), v) for k, v in planned_curve.items()],
            key=lambda x: x[0],
        )
        deviations = []
        for chapter_no, actual_tension in [(c["chapter_no"], c["tension"]) for c in actual]:
            planned_tension = self._interpolate_planned(planned_points, chapter_no)
            if planned_tension is not None:
                deviation = actual_tension - planned_tension
                if abs(deviation) > 0.2:
                    deviations.append({
                        "chapter_no": chapter_no,
                        "actual": round(actual_tension, 3),
                        "planned": round(planned_tension, 3),
                        "deviation": round(deviation, 3),
                    })

        avg_deviation = (
            sum(abs(d["deviation"]) for d in deviations) / len(deviations)
            if deviations else 0
        )

        return {
            "ok": True,
            "volume_no": volume_no,
            "chapter_range": [from_chapter, to_chapter],
            "total_deviations": len(deviations),
            "avg_deviation": round(avg_deviation, 3),
            "max_deviation": round(max((abs(d["deviation"]) for d in deviations), default=0), 3),
            "deviations": deviations[:20],
        }

    def _interpolate_planned(
        self, points: list[tuple[int, float]], chapter_no: int
    ) -> float | None:
        if not points:
            return None
        if chapter_no <= points[0][0]:
            return points[0][1]
        if chapter_no >= points[-1][0]:
            return points[-1][1]
        for i in range(len(points) - 1):
            ch_a, t_a = points[i]
            ch_b, t_b = points[i + 1]
            if ch_a <= chapter_no <= ch_b:
                ratio = (chapter_no - ch_a) / (ch_b - ch_a)
                return t_a + ratio * (t_b - t_a)
        return None

    # ------------------------------------------------------------------
    # Reader Engagement Prediction
    # ------------------------------------------------------------------

    async def predict_engagement(
        self,
        project_id: str,
        chapter_no: int,
        window: int = 10,
    ) -> dict[str, Any]:
        """Predict reader engagement based on recent pacing patterns."""
        recent = await self.get_emotion_curve(
            project_id,
            from_chapter=max(1, chapter_no - window),
            to_chapter=chapter_no,
        )
        if len(recent) < 3:
            return {
                "chapter_no": chapter_no,
                "prediction": "insufficient_data",
                "confidence": 0,
            }

        tensions = [c["tension"] for c in recent]
        avg_tension = sum(tensions) / len(tensions)

        variance = sum((t - avg_tension) ** 2 for t in tensions) / len(tensions)
        has_variety = variance > 0.02

        recent_types = [c.get("pacing_type", "normal") for c in recent]
        has_climax = "climax" in recent_types
        has_breather = "breather" in recent_types

        score = 50
        if has_variety:
            score += 15
        if has_climax:
            score += 10
        if has_breather:
            score += 5
        if 0.3 <= avg_tension <= 0.7:
            score += 10
        elif avg_tension > 0.85:
            score -= 10
        elif avg_tension < 0.15:
            score -= 5

        if len(recent) >= 5:
            trend = tensions[-1] - tensions[0]
            if -0.2 <= trend <= 0.3:
                score += 5
            elif trend > 0.5:
                score += 8

        score = max(0, min(100, score))

        if score >= 75:
            prediction = "high_engagement"
        elif score >= 50:
            prediction = "moderate_engagement"
        else:
            prediction = "risk_of_disengagement"

        return {
            "chapter_no": chapter_no,
            "prediction": prediction,
            "score": score,
            "avg_tension": round(avg_tension, 3),
            "has_variety": has_variety,
            "has_climax_recent": has_climax,
            "has_breather_recent": has_breather,
        }

    # ------------------------------------------------------------------
    # Context-Friendly Summary
    # ------------------------------------------------------------------

    async def get_pacing_summary_for_context(
        self,
        project_id: str,
        chapter_no: int,
        volume_no: int | None = None,
        max_tokens: int = 200,
    ) -> str:
        """Get compressed pacing summary for context injection."""
        recent = await self.get_emotion_curve(
            project_id,
            from_chapter=max(1, chapter_no - 15),
            to_chapter=chapter_no,
        )
        lines = [f"== Pacing Context (Ch.{chapter_no}) =="]
        if recent:
            tensions = [c["tension"] for c in recent]
            avg = sum(tensions) / len(tensions)
            lines.append(f"  Recent avg tension: {avg:.2f}")
            last = recent[-1]
            lines.append(f"  Current: tension={last['tension']:.2f}, emotion={last.get('emotion', '?')}, type={last.get('pacing_type', '?')}")

            types = [c.get("pacing_type", "normal") for c in recent[-5:]]
            lines.append(f"  Recent pacing: {' → '.join(types)}")

        if volume_no:
            blueprint = await self.get_volume_blueprint(project_id, volume_no)
            if blueprint:
                bp = blueprint.get("blueprint") or {}
                climax_chs = bp.get("climax_chapters", [])
                next_climax = next((c for c in climax_chs if c > chapter_no), None)
                if next_climax:
                    lines.append(f"  Next planned climax: Ch.{next_climax} ({next_climax - chapter_no} chapters away)")

        summary = "\n".join(lines)
        char_budget = max_tokens * 4
        if len(summary) > char_budget:
            summary = summary[:char_budget] + "..."
        return summary
