"""AI Reviewer Worker - AI评审工作进程

后台服务，持续监控并处理待评审的进化提案。

使用方法:
    python -m novel_os_mcp.ai_reviewer_worker

环境变量:
    DATABASE_URL: PostgreSQL连接字符串
    MCP_API_URL: MCP服务URL (默认: http://localhost:8787)
    POLL_INTERVAL: 轮询间隔秒数 (默认: 30)
    MAX_CONCURRENT: 最大并发评审数 (默认: 2)
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Any

import asyncpg
import httpx

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ai_reviewer_worker")


class AIReviewerWorker:
    """AI评审工作器"""
    
    def __init__(self):
        self.db_pool: asyncpg.Pool | None = None
        self.http_client: httpx.AsyncClient | None = None
        self.running = False
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
        self.max_concurrent = int(os.getenv('MAX_CONCURRENT', '2'))
        self.mcp_api_url = os.getenv('MCP_API_URL', 'http://novel-os-mcp:8787')
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
    async def initialize(self):
        """初始化连接。"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # 创建数据库连接池
        self.db_pool = await asyncpg.create_pool(
            dsn=database_url,
            min_size=1,
            max_size=5
        )
        
        # 创建HTTP客户端
        self.http_client = httpx.AsyncClient(timeout=300.0)  # 5分钟超时
        
        logger.info(f"Worker initialized: poll_interval={self.poll_interval}s, max_concurrent={self.max_concurrent}")
        
    async def close(self):
        """关闭连接。"""
        if self.db_pool:
            await self.db_pool.close()
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Worker closed")
        
    async def get_pending_proposals(self) -> list[dict[str, Any]]:
        """获取待评审的提案列表。"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id::text, title, target_entity_type, status, ai_retry_count
                FROM system_evolution_proposals
                WHERE status = 'ai_reviewing'
                AND (ai_last_error IS NULL OR ai_retry_count < 3)
                ORDER BY created_at ASC
                LIMIT 10
                """
            )
            return [dict(row) for row in rows]
            
    async def review_proposal(self, proposal_id: str) -> dict[str, Any]:
        """调用MCP工具执行AI评审。"""
        async with self.semaphore:
            try:
                # 调用 system.evolution.ai_review 工具
                response = await self.http_client.post(
                    f"{self.mcp_api_url}/mcp/tool",
                    json={
                        "tool": "system.evolution.ai_review",
                        "arguments": {
                            "proposal_id": proposal_id,
                            "workspace": "system"  # 系统级工作区
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("error"):
                    raise Exception(f"AI review failed: {result['error']}")
                    
                return result.get("result", {})
                
            except Exception as e:
                logger.error(f"Error reviewing proposal {proposal_id}: {e}")
                raise
                
    async def process_proposal(self, proposal: dict[str, Any]):
        """处理单个提案。"""
        proposal_id = proposal["id"]
        logger.info(f"Processing proposal: {proposal_id} - {proposal['title']}")
        
        try:
            # 执行评审
            result = await self.review_proposal(proposal_id)
            
            logger.info(
                f"Proposal {proposal_id} reviewed: "
                f"score={result.get('score', 'N/A')}, "
                f"verdict={result.get('verdict', 'N/A')}, "
                f"status={result.get('status', 'N/A')}"
            )
            
        except Exception as e:
            logger.error(f"Failed to process proposal {proposal_id}: {e}")
            
            # 更新重试计数
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE system_evolution_proposals
                    SET ai_retry_count = ai_retry_count + 1,
                        ai_last_error = $1,
                        updated_at = now()
                    WHERE id = $2
                    """,
                    str(e)[:500],
                    proposal_id
                )
                
    async def run_once(self):
        """执行一次轮询和处理。"""
        try:
            # 获取待处理提案
            proposals = await self.get_pending_proposals()
            
            if not proposals:
                logger.debug("No pending proposals found")
                return
                
            logger.info(f"Found {len(proposals)} pending proposals")
            
            # 并发处理
            tasks = [
                self.process_proposal(proposal)
                for proposal in proposals
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error in run_once: {e}")
            
    async def run(self):
        """主循环。"""
        self.running = True
        logger.info("AI Reviewer Worker started")
        
        while self.running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                
            # 等待下一次轮询
            await asyncio.sleep(self.poll_interval)
            
    def stop(self):
        """停止工作器。"""
        logger.info("Stopping worker...")
        self.running = False


async def main():
    """主函数。"""
    worker = AIReviewerWorker()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        worker.stop()
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await worker.initialize()
        await worker.run()
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        sys.exit(1)
    finally:
        await worker.close()


if __name__ == "__main__":
    asyncio.run(main())
