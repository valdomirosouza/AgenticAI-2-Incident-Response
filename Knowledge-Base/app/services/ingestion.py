from app.models.chunk import (
    ChunkMetadata,
    ChunkType,
    GoldenSignal,
    IncidentIngestRequest,
)


def incident_to_chunks(incident: IncidentIngestRequest) -> list[tuple[str, ChunkMetadata]]:
    """Explode a full IncidentIngestRequest into (content, metadata) pairs for embedding."""

    primary_signal = (
        incident.golden_signals[0] if len(incident.golden_signals) == 1
        else GoldenSignal.MULTIPLE if incident.golden_signals
        else None
    )

    base: dict = dict(
        incident_id=incident.incident_id,
        severity=incident.severity,
        root_cause_category=incident.root_cause_category,
        resolution_type=incident.resolution_type,
        affected_services=incident.affected_services,
        affected_cujs=incident.affected_cujs,
        mttd_minutes=incident.mttd_minutes,
        mttr_minutes=incident.mttr_minutes,
        incident_date=incident.date,
        golden_signal=primary_signal,
    )

    chunks: list[tuple[str, ChunkMetadata]] = []

    # Summary → postmortem chunk
    chunks.append((
        f"[{incident.incident_id}] {incident.title}\n\n{incident.summary}",
        ChunkMetadata(chunk_type=ChunkType.POSTMORTEM, **base),
    ))

    if incident.postmortem_text:
        chunks.append((
            incident.postmortem_text,
            ChunkMetadata(chunk_type=ChunkType.POSTMORTEM, **base),
        ))

    for pattern in incident.symptom_patterns:
        chunks.append((
            f"Padrão de sintoma — {incident.incident_id}: {pattern}",
            ChunkMetadata(chunk_type=ChunkType.SYMPTOM_FINGERPRINT, **base),
        ))

    for excerpt in incident.log_excerpts:
        text = f"[{excerpt.source}]"
        if excerpt.context:
            text += f" {excerpt.context}"
        text += f"\n{excerpt.content}"
        chunks.append((text, ChunkMetadata(chunk_type=ChunkType.LOG_EVIDENCE, **base)))

    for cmd in incident.recovery_commands:
        text = f"Comando de recuperação ({cmd.phase}): `{cmd.command}`\n{cmd.description}"
        chunks.append((text, ChunkMetadata(chunk_type=ChunkType.RECOVERY_COMMAND, **base)))

    for step in incident.runbook_steps:
        text = f"Runbook passo {step.step_number} [{step.action_type}]: {step.description}"
        if step.command:
            text += f"\n`{step.command}`"
        chunks.append((
            text,
            ChunkMetadata(chunk_type=ChunkType.RUNBOOK_STEP, step_number=step.step_number, **base),
        ))

    for lesson in incident.lessons_learned:
        chunks.append((
            f"Lição aprendida — {incident.incident_id}: {lesson}",
            ChunkMetadata(chunk_type=ChunkType.LESSON_LEARNED, **base),
        ))

    for snapshot in incident.metric_snapshots:
        parts = [f"Métricas ({snapshot.phase}) — {incident.incident_id}:"]
        for label, val in [
            ("P50", snapshot.p50_ms), ("P95", snapshot.p95_ms), ("P99", snapshot.p99_ms),
            ("5xx%", snapshot.error_rate_5xx_pct), ("4xx%", snapshot.error_rate_4xx_pct),
            ("RPS", snapshot.rps), ("Redis%", snapshot.redis_memory_pct),
        ]:
            if val is not None:
                parts.append(f"{label}={val}")
        chunks.append((" ".join(parts), ChunkMetadata(chunk_type=ChunkType.METRIC_SNAPSHOT, **base)))

    if incident.error_budget:
        eb = incident.error_budget
        text = (
            f"Error Budget — {incident.incident_id}: SLO={eb.slo_target_pct}%, "
            f"duração={eb.duration_minutes}min, consumido={eb.budget_consumed_pct}%"
        )
        if eb.budget_remaining_after_pct is not None:
            text += f", restante={eb.budget_remaining_after_pct}%"
        chunks.append((text, ChunkMetadata(chunk_type=ChunkType.ERROR_BUDGET, **base)))

    for signal in incident.precursor_signals:
        chunks.append((
            f"Sinal precursor — {incident.incident_id}: {signal}",
            ChunkMetadata(chunk_type=ChunkType.PRECURSOR_SIGNAL, **base),
        ))

    return chunks
