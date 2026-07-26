"""Centralized dependency injection for all services."""
import logging

from .config import get_settings
from .db import Database
from .auth import AuthService
from .cache import CacheService
from .degradation import DependencyHealthService, DegradationModeService
from .p7_services import (
    ChapterAnnotationService, ContextWeightService, FulltextSearchService,
    PromptTemplateService, ProperNounService, ReaderExpectationService,
    ReferenceMaterialService,
)
from .context_compression import ContextCompressionService
from .multipass import MultiPassService
from .character_arc import CharacterArcService
from .causality import CausalityService
from .novelty import NoveltyService
from .pacing import PacingService
from .style_fingerprint import StyleFingerprintService
from .embedding import EmbeddingService, RerankService
from .kb_service import KBService
from .services.gatekeeper import GatekeeperService
from .services import (
    ArchiveService, BackupService, CanonService, ComplianceService,
    ContextService, GlobalSettingsService, MemoryService,
    ModelCostService, PlotService, ReferenceService, ReviewService,
    RulesService, SyncService, VectorIndexService, WorkflowService,
    WorkspaceService, KnowledgeAuditService, KnowledgeCouncilService,
)
from .vector import VectorIndex
from .p8_services import RelationshipGraphService
from .local_service import LocalService
from .skill_service import SkillService
from .llm_client import LLMClient

logger = logging.getLogger("novel_os_mcp.deps")

settings = get_settings()
logging.basicConfig(level=settings.log_level)

db = Database(settings)
auth = AuthService(settings, db)

# Core services
workspace_service = WorkspaceService(db)
canon_service = CanonService(db)
rules_service = RulesService(db)
compliance_service = ComplianceService(db, rules_service)
plot_service = PlotService(db)
vector_index = VectorIndex(settings)
embedding_service = EmbeddingService(db)
rerank_service = RerankService(db)
memory_service = MemoryService(db, embedding_service=embedding_service, vector_index=vector_index)
character_arc_service = CharacterArcService(db)
causality_service = CausalityService(db)
pacing_service = PacingService(db)
style_fingerprint_service = StyleFingerprintService(db)
context_service = ContextService(
    db, memory_service, rules_service, plot_service,
    embedding_service=embedding_service,
    rerank_service=rerank_service,
    character_arc_service=character_arc_service,
    causality_service=causality_service,
    pacing_service=pacing_service,
    style_fingerprint_service=style_fingerprint_service,
)
review_service = ReviewService(db)
workflow_service = WorkflowService(db)
reference_service = ReferenceService(db)
sync_service = SyncService(db)
model_cost_service = ModelCostService(db)
global_settings_service = GlobalSettingsService(db)
vector_index_service = VectorIndexService(db)
cache_service = CacheService(settings)
archive_service = ArchiveService(db)
backup_service = BackupService(db)
kb_service = KBService(db)
prompt_template_service = PromptTemplateService(db)
context_weight_service = ContextWeightService(db)
reference_material_service = ReferenceMaterialService(db)
reader_expectation_service = ReaderExpectationService(db)
chapter_annotation_service = ChapterAnnotationService(db)
proper_noun_service = ProperNounService(db)
fulltext_search_service = FulltextSearchService(db)
llm_client = LLMClient(db)
context_compression_service = ContextCompressionService(db, llm_client)
multipass_service = MultiPassService(db)
novelty_service = NoveltyService(db, vector_index)
graph_service = RelationshipGraphService(db)
local_service = LocalService(db)
skill_service = SkillService(db)
knowledge_audit_service = KnowledgeAuditService(db, llm_client)
knowledge_council_service = KnowledgeCouncilService(db, llm_client)

gatekeeper_service = GatekeeperService(db)

# Initialize AI reviewer with LLM client
from .services.ai_reviewer import init_ai_reviewer
init_ai_reviewer(llm_client)

# Health / degradation (special init)
_health_service = DependencyHealthService(settings)
_degradation_service = DegradationModeService(settings)
