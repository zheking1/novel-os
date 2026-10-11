#!/usr/bin/env sh
# 应用单个数据库迁移，并在执行前后做结构核对。
#
# 用法（在 NAS 的 /opt/novel-os/deploy/nas/ 目录内执行）：
#   sh scripts/apply-migration.sh <迁移文件名> [需要核对的表...]
#
# 示例：
#   sh scripts/apply-migration.sh 222_runtime_tables.sql global_rules evolution_logs ref_tones ref_tone_rules
#   sh scripts/apply-migration.sh 223_rule_summaries.sql rule_summaries
#
# 说明：
#   - 迁移文件必须位于 postgres/migrations/ 下
#   - 执行前会打印目标表当前结构（不存在则跳过），用于与代码期望比对
#   - 使用 ON_ERROR_STOP=1，任一条语句失败即中止
#   - 脚本只做 ADD / CREATE IF NOT EXISTS，不会 DROP 任何对象
#
# 非交互执行（通过 ssh/plink 远程调用时必须，否则 read 读不到输入会直接取消）：
#   APPLY_MIGRATION_YES=1 sh scripts/apply-migration.sh 222_runtime_tables.sql ...
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ./.env ]; then
  set -a
  . ./.env
  set +a
fi

PG_CONTAINER="${PG_CONTAINER:-novel-postgres}"
PG_USER="${POSTGRES_USER:-novel_os}"
PG_DB="${POSTGRES_DB:-novel_os}"

MIGRATION="${1:-}"
if [ -z "$MIGRATION" ]; then
  echo "用法: sh scripts/apply-migration.sh <迁移文件名> [需要核对的表...]" >&2
  exit 1
fi
shift

SRC="postgres/migrations/$MIGRATION"
if [ ! -f "$SRC" ]; then
  echo "找不到迁移文件: $SRC" >&2
  exit 1
fi

# ---------- 1. 执行前核对 ----------
if [ "$#" -gt 0 ]; then
  echo "===== 执行前结构核对 ====="
  for t in "$@"; do
    echo "--- \\d $t ---"
    # 表可能还不存在，psql 会报错，这里允许失败并继续
    docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -c "\\d $t" 2>&1 || echo "(表 $t 尚不存在，将由本次迁移创建)"
  done
  echo
  echo "请比对上表结构与代码期望是否一致；若缺少列，请先手工 ALTER 补齐（不要 DROP）。"
  echo
  if [ "${APPLY_MIGRATION_YES:-0}" = "1" ]; then
    echo "APPLY_MIGRATION_YES=1，跳过交互确认。"
  else
    printf "确认继续应用迁移 %s？[y/N] " "$MIGRATION"
    # 非交互场景（无 TTY，如 ssh/plink 远程调用）下 read 会返回非 0，
    # 这里兜底为空串以免被 set -e 中断；结果等同于"取消"，避免误执行。
    answer=""
    read -r answer || true
    case "$answer" in
      [yY]*) ;;
      *) echo "已取消（远程执行请加 APPLY_MIGRATION_YES=1）。"; exit 0 ;;
    esac
  fi
fi

# ---------- 2. 复制并执行 ----------
echo "===== 应用迁移 ====="
docker cp "$SRC" "$PG_CONTAINER:/tmp/$MIGRATION"
docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -v ON_ERROR_STOP=1 -f "/tmp/$MIGRATION"

# ---------- 3. 执行后验证 ----------
echo
echo "===== 执行后验证 ====="
for t in "$@"; do
  printf "%-20s " "$t"
  docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc "SELECT count(*) FROM $t" 2>&1 || echo "查询失败"
done

echo "迁移 $MIGRATION 完成。"
