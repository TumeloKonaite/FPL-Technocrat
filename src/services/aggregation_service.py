from __future__ import annotations

from src.schemas.aggregate_report import (
    ConsensusItem,
    FixtureInsightConsensusItem,
    TransferConsensusItem,
)
from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.final_report import AggregatedFPLReport
from src.services.normalization import (
    canonical_chip_display,
    canonical_player_display,
    normalize_chip_name,
    normalize_lookup_key,
    normalize_player_name,
    normalize_text_label,
)


_CONFIDENCE_TO_SCORE = {
    "low": 1 / 3,
    "medium": 2 / 3,
    "high": 1.0,
}


def _confidence_score(level: str) -> float:
    return _CONFIDENCE_TO_SCORE[level]


def _sorted_experts(experts: set[str]) -> list[str]:
    return sorted(experts, key=str.casefold)


def _unique_normalized_players(players: list[str]) -> set[str]:
    return {normalize_player_name(player) for player in players if normalize_player_name(player)}


def _unique_normalized_text(items: list[str]) -> set[str]:
    return {normalize_text_label(item) for item in items if normalize_text_label(item)}


def aggregate_player_consensus(
    analyses: list[ExpertVideoAnalysis],
) -> list[ConsensusItem]:
    grouped: dict[str, dict[str, object]] = {}

    for analysis in analyses:
        confidence = _confidence_score(analysis.confidence)
        for player_key in _unique_normalized_players(analysis.recommended_players):
            entry = grouped.setdefault(
                player_key,
                {"experts": set(), "confidences": []},
            )
            experts = entry["experts"]
            if analysis.expert_name in experts:
                continue
            experts.add(analysis.expert_name)
            entry["confidences"].append(confidence)

    items = [
        ConsensusItem(
            item=canonical_player_display(player_key),
            mention_count=len(data["experts"]),  # type: ignore[arg-type,index]
            average_confidence=round(
                sum(data["confidences"]) / len(data["confidences"]),  # type: ignore[arg-type,index]
                4,
            ),
            supporting_experts=_sorted_experts(data["experts"]),  # type: ignore[arg-type,index]
        )
        for player_key, data in grouped.items()
    ]
    return sorted(
        items,
        key=lambda item: (-item.mention_count, -item.average_confidence, normalize_lookup_key(item.item)),
    )


def aggregate_captaincy(
    analyses: list[ExpertVideoAnalysis],
) -> list[ConsensusItem]:
    grouped: dict[str, dict[str, object]] = {}

    for analysis in analyses:
        confidence = _confidence_score(analysis.confidence)
        for player_key in _unique_normalized_players(analysis.captaincy_picks):
            entry = grouped.setdefault(
                player_key,
                {"experts": set(), "confidences": []},
            )
            experts = entry["experts"]
            if analysis.expert_name in experts:
                continue
            experts.add(analysis.expert_name)
            entry["confidences"].append(confidence)

    items = [
        ConsensusItem(
            item=canonical_player_display(player_key),
            mention_count=len(data["experts"]),  # type: ignore[arg-type,index]
            average_confidence=round(
                sum(data["confidences"]) / len(data["confidences"]),  # type: ignore[arg-type,index]
                4,
            ),
            supporting_experts=_sorted_experts(data["experts"]),  # type: ignore[arg-type,index]
        )
        for player_key, data in grouped.items()
    ]
    return sorted(
        items,
        key=lambda item: (-item.mention_count, -item.average_confidence, normalize_lookup_key(item.item)),
    )


def aggregate_transfers(
    analyses: list[ExpertVideoAnalysis],
) -> list[TransferConsensusItem]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}

    for analysis in analyses:
        confidence = _confidence_score(analysis.confidence)

        for player_key in _unique_normalized_players(analysis.recommended_players):
            entry = grouped.setdefault(
                ("buy", player_key),
                {"experts": set(), "confidences": []},
            )
            experts = entry["experts"]
            if analysis.expert_name in experts:
                continue
            experts.add(analysis.expert_name)
            entry["confidences"].append(confidence)

        for player_key in _unique_normalized_players(analysis.avoid_players):
            entry = grouped.setdefault(
                ("sell", player_key),
                {"experts": set(), "confidences": []},
            )
            experts = entry["experts"]
            if analysis.expert_name in experts:
                continue
            experts.add(analysis.expert_name)
            entry["confidences"].append(confidence)

    items = [
        TransferConsensusItem(
            player_name=canonical_player_display(player_key),
            direction=direction,
            mention_count=len(data["experts"]),  # type: ignore[arg-type,index]
            average_confidence=round(
                sum(data["confidences"]) / len(data["confidences"]),  # type: ignore[arg-type,index]
                4,
            ),
            supporting_experts=_sorted_experts(data["experts"]),  # type: ignore[arg-type,index]
        )
        for (direction, player_key), data in grouped.items()
    ]
    return sorted(
        items,
        key=lambda item: (
            item.direction,
            -item.mention_count,
            -item.average_confidence,
            normalize_lookup_key(item.player_name),
        ),
    )


def aggregate_fixture_insights(
    analyses: list[ExpertVideoAnalysis],
) -> list[FixtureInsightConsensusItem]:
    grouped: dict[str, dict[str, object]] = {}

    for analysis in analyses:
        for raw_insight in analysis.key_takeaways + analysis.reasoning:
            insight_key = normalize_text_label(raw_insight)
            if not insight_key:
                continue

            entry = grouped.setdefault(
                insight_key,
                {"display": raw_insight.strip(), "experts": set()},
            )
            entry["experts"].add(analysis.expert_name)

    items = [
        FixtureInsightConsensusItem(
            insight=data["display"],  # type: ignore[index]
            mention_count=len(data["experts"]),  # type: ignore[arg-type,index]
            supporting_experts=_sorted_experts(data["experts"]),  # type: ignore[arg-type,index]
        )
        for data in grouped.values()
    ]
    return sorted(
        items,
        key=lambda item: (-item.mention_count, normalize_lookup_key(item.insight)),
    )


def aggregate_chip_strategy(
    analyses: list[ExpertVideoAnalysis],
) -> list[ConsensusItem]:
    grouped: dict[str, dict[str, object]] = {}

    for analysis in analyses:
        chip_key = normalize_chip_name(analysis.chip_strategy)
        if chip_key == "none":
            continue

        entry = grouped.setdefault(
            chip_key,
            {"experts": set(), "confidences": []},
        )
        experts = entry["experts"]
        if analysis.expert_name in experts:
            continue
        experts.add(analysis.expert_name)
        entry["confidences"].append(_confidence_score(analysis.confidence))

    items = [
        ConsensusItem(
            item=canonical_chip_display(chip_key),
            mention_count=len(data["experts"]),  # type: ignore[arg-type,index]
            average_confidence=round(
                sum(data["confidences"]) / len(data["confidences"]),  # type: ignore[arg-type,index]
                4,
            ),
            supporting_experts=_sorted_experts(data["experts"]),  # type: ignore[arg-type,index]
        )
        for chip_key, data in grouped.items()
    ]
    return sorted(
        items,
        key=lambda item: (-item.mention_count, -item.average_confidence, normalize_lookup_key(item.item)),
    )


def build_aggregated_fpl_report(
    analyses: list[ExpertVideoAnalysis],
) -> AggregatedFPLReport:
    if not analyses:
        return AggregatedFPLReport(
            gameweek=None,
            expert_count=0,
            player_consensus=[],
            captaincy_consensus=[],
            transfer_consensus=[],
            fixture_insights=[],
            chip_strategy_consensus=[],
        )

    return AggregatedFPLReport(
        gameweek=analyses[0].gameweek,
        expert_count=len(analyses),
        player_consensus=aggregate_player_consensus(analyses),
        captaincy_consensus=aggregate_captaincy(analyses),
        transfer_consensus=aggregate_transfers(analyses),
        fixture_insights=aggregate_fixture_insights(analyses),
        chip_strategy_consensus=aggregate_chip_strategy(analyses),
    )
