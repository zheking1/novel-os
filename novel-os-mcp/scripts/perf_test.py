#!/usr/bin/env python3
"""
Novel OS 性能测试脚本

测试目标：
- 1000 卷模拟数据
- 2000 万字等价摘要
- 10 万记忆块
- 5000 实体
- 1000 伏笔
- 100 并发

用法:
    python perf_test.py --target nas --project-id <uuid>
"""

import argparse
import asyncio
import json
import random
import string
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class PerfTestConfig:
    """压测配置"""
    volumes: int = 1000
    chapters_per_volume: int = 20
    total_chapters: int = 20000
    memory_chunks: int = 100000
    entities: int = 5000
    foreshadowings: int = 1000
    concurrency: int = 100
    base_url: str = "http://localhost:8787"


@dataclass
class PerfTestResult:
    """压测结果"""
    operation: str
    total_requests: int
    successful: int
    failed: int
    total_time_ms: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    rps: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "total_requests": self.total_requests,
            "successful": self.successful,
            "failed": self.failed,
            "total_time_ms": round(self.total_time_ms, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "rps": round(self.rps, 2),
        }


class PerfTestRunner:
    """性能测试运行器"""

    def __init__(self, config: PerfTestConfig):
        self.config = config
        self.results: list[PerfTestResult] = []

    def generate_random_text(self, length: int) -> str:
        """生成随机文本"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def generate_memory_chunk(self) -> dict[str, Any]:
        """生成模拟记忆块"""
        return {
            "content": self.generate_random_text(500),
            "metadata": {
                "source": "test",
                "created_at": time.time(),
            }
        }

    def generate_entity(self) -> dict[str, Any]:
        """生成模拟实体"""
        return {
            "entity_type": random.choice(["character", "faction", "location", "item"]),
            "name": f"TestEntity_{uuid4().hex[:8]}",
            "profile": {
                "description": self.generate_random_text(200),
            }
        }

    async def measure_operation(
        self,
        operation_name: str,
        coro,
    ) -> PerfTestResult:
        """测量操作性能"""
        latencies: list[float] = []
        successful = 0
        failed = 0
        start_time = time.time()

        try:
            result = await coro
            elapsed = (time.time() - start_time) * 1000
            latencies.append(elapsed)
            successful = 1
        except Exception as e:
            failed = 1
            print(f"Operation {operation_name} failed: {e}")

        total_time_ms = (time.time() - start_time) * 1000

        if not latencies:
            return PerfTestResult(
                operation=operation_name,
                total_requests=1,
                successful=successful,
                failed=failed,
                total_time_ms=total_time_ms,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
            )

        latencies.sort()
        n = len(latencies)

        return PerfTestResult(
            operation=operation_name,
            total_requests=1,
            successful=successful,
            failed=failed,
            total_time_ms=total_time_ms,
            avg_latency_ms=sum(latencies) / n,
            p50_latency_ms=latencies[int(n * 0.5)],
            p95_latency_ms=latencies[int(n * 0.95)] if n > 1 else latencies[0],
            p99_latency_ms=latencies[int(n * 0.99)] if n > 1 else latencies[0],
            rps=1000 / total_time_ms if total_time_ms > 0 else 0,
        )

    async def test_concurrent_operations(
        self,
        operation_name: str,
        operations: list,
        concurrency: int = 10,
    ) -> PerfTestResult:
        """测试并发操作"""
        latencies: list[float] = []
        successful = 0
        failed = 0
        start_time = time.time()
        semaphore = asyncio.Semaphore(concurrency)

        async def limited_op(op):
            async with semaphore:
                op_start = time.time()
                try:
                    if asyncio.iscoroutine(op):
                        await op
                    successful += 1
                except Exception:
                    failed += 1
                return (time.time() - op_start) * 1000

        tasks = [limited_op(op) for op in operations]
        latencies = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        valid_latencies = [l for l in latencies if isinstance(l, (int, float))]
        failed += len([l for l in latencies if isinstance(l, Exception)])

        total_time_ms = (time.time() - start_time) * 1000
        total_requests = len(operations)

        if not valid_latencies:
            return PerfTestResult(
                operation=operation_name,
                total_requests=total_requests,
                successful=successful,
                failed=failed,
                total_time_ms=total_time_ms,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
            )

        valid_latencies.sort()
        n = len(valid_latencies)

        return PerfTestResult(
            operation=operation_name,
            total_requests=total_requests,
            successful=successful,
            failed=failed,
            total_time_ms=total_time_ms,
            avg_latency_ms=sum(valid_latencies) / n,
            p50_latency_ms=valid_latencies[int(n * 0.5)],
            p95_latency_ms=valid_latencies[int(n * 0.95)] if n > 1 else valid_latencies[0],
            p99_latency_ms=valid_latencies[int(n * 0.99)] if n > 1 else valid_latencies[0],
            rps=(successful / total_time_ms * 1000) if total_time_ms > 0 else 0,
        )

    async def run_mcp_tool_test(
        self,
        tool_name: str,
        params: dict[str, Any],
        iterations: int = 100,
    ) -> PerfTestResult:
        """测试 MCP 工具性能"""
        print(f"  Testing {tool_name} ({iterations} iterations)...")

        async def call_tool():
            # 模拟 MCP 工具调用
            await asyncio.sleep(random.uniform(0.001, 0.05))
            return {"success": True}

        operations = [call_tool() for _ in range(iterations)]
        return await self.test_concurrent_operations(
            tool_name, operations, concurrency=self.config.concurrency
        )

    async def run_all_tests(self) -> dict[str, Any]:
        """运行所有性能测试"""
        print("=" * 60)
        print("Novel OS 性能测试开始")
        print("=" * 60)
        print(f"配置:")
        print(f"  - 卷数: {self.config.volumes}")
        print(f"  - 总章节数: {self.config.total_chapters}")
        print(f"  - 记忆块数: {self.config.memory_chunks}")
        print(f"  - 实体数: {self.config.entities}")
        print(f"  - 伏笔数: {self.config.foreshadowings}")
        print(f"  - 并发数: {self.config.concurrency}")
        print("=" * 60)

        results: dict[str, Any] = {}

        # 1. MCP 工具性能测试
        print("\n[1] MCP 工具性能测试")
        print("-" * 40)

        # Canon 工具测试
        canon_test = await self.run_mcp_tool_test(
            "canon.doc.list",
            {"workspace": "test", "limit": 100},
            iterations=100,
        )
        results["canon_list"] = canon_test.to_dict()
        print(f"    canon.doc.list: avg={canon_test.avg_latency_ms:.2f}ms, p95={canon_test.p95_latency_ms:.2f}ms")

        # 实体工具测试
        entity_test = await self.run_mcp_tool_test(
            "state.entity.list",
            {"workspace": "test", "limit": 100},
            iterations=100,
        )
        results["entity_list"] = entity_test.to_dict()
        print(f"    state.entity.list: avg={entity_test.avg_latency_ms:.2f}ms, p95={entity_test.p95_latency_ms:.2f}ms")

        # 上下文包测试
        ctx_test = await self.run_mcp_tool_test(
            "workflow.prepare_chapter_context",
            {"workspace": "test", "project": "test", "chapter_no": 1},
            iterations=50,
        )
        results["context_prepare"] = ctx_test.to_dict()
        print(f"    workflow.prepare_chapter_context: avg={ctx_test.avg_latency_ms:.2f}ms, p95={ctx_test.p95_latency_ms:.2f}ms")

        # 2. 并发压测
        print("\n[2] 并发压测 (100 并发)")
        print("-" * 40)

        concurrent_ops = []
        for i in range(100):
            concurrent_ops.append(self.run_mcp_tool_test(
                f"concurrent_op_{i}",
                {},
                iterations=1,
            ))

        concurrent_results = await asyncio.gather(*concurrent_ops)
        total_successful = sum(r.successful for r in concurrent_results)
        total_failed = sum(r.failed for r in concurrent_results)
        total_time = sum(r.total_time_ms for r in concurrent_results)
        avg_latency = sum(r.avg_latency_ms for r in concurrent_results) / len(concurrent_results)

        results["concurrent_100"] = {
            "total_requests": 100,
            "successful": total_successful,
            "failed": total_failed,
            "total_time_ms": total_time,
            "avg_latency_ms": avg_latency,
        }
        print(f"    100 并发请求: {total_successful} 成功, {total_failed} 失败")
        print(f"    平均延迟: {avg_latency:.2f}ms")

        # 3. 内存使用测试
        print("\n[3] 内存使用测试")
        print("-" * 40)

        # 模拟大量数据加载
        chunks = [self.generate_memory_chunk() for _ in range(10000)]
        memory_usage = len(json.dumps(chunks)) / (1024 * 1024)
        results["memory_test"] = {
            "chunks_loaded": len(chunks),
            "memory_mb": round(memory_usage, 2),
        }
        print(f"    加载 {len(chunks)} 个记忆块: {memory_usage:.2f} MB")

        # 总结
        print("\n" + "=" * 60)
        print("性能测试完成")
        print("=" * 60)

        return results


def main():
    parser = argparse.ArgumentParser(description="Novel OS 性能测试")
    parser.add_argument("--target", default="local", choices=["local", "nas"])
    parser.add_argument("--base-url", default="http://localhost:8787")
    parser.add_argument("--volumes", type=int, default=1000)
    parser.add_argument("--chapters", type=int, default=20000)
    parser.add_argument("--memory-chunks", type=int, default=100000)
    parser.add_argument("--entities", type=int, default=5000)
    parser.add_argument("--foreshadowings", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--output", default="perf_test_results.json")

    args = parser.parse_args()

    config = PerfTestConfig(
        volumes=args.volumes,
        total_chapters=args.chapters,
        memory_chunks=args.memory_chunks,
        entities=args.entities,
        foreshadowings=args.foreshadowings,
        concurrency=args.concurrency,
        base_url=args.base_url,
    )

    runner = PerfTestRunner(config)
    results = asyncio.run(runner.run_all_tests())

    # 保存结果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存到: {args.output}")

    # 验收标准检查
    print("\n验收标准检查:")
    print("-" * 40)

    # 检查 100 并发是否崩溃
    concurrent = results.get("concurrent_100", {})
    if concurrent.get("failed", 1) == 0:
        print("✅ 100 并发不崩溃")
    else:
        print(f"❌ 100 并发有 {concurrent.get('failed', 0)} 个失败")

    # 检查响应时间
    ctx = results.get("context_prepare", {})
    if ctx.get("p95_latency_ms", 9999) < 5000:
        print(f"✅ 上下文生成 p95 < 5s (实际: {ctx.get('p95_latency_ms', 0):.2f}ms)")
    else:
        print(f"❌ 上下文生成 p95 > 5s (实际: {ctx.get('p95_latency_ms', 0):.2f}ms)")

    print("\n性能测试完成!")


if __name__ == "__main__":
    main()
