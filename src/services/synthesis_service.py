from __future__ import annotations

from src.agents.final_synthesis_agent import run_final_synthesis
from src.schemas.final_report import (
    AggregatedFPLReport,
    FinalDisagreement,
    FinalGameweekReport,
    FinalRecommendation,
)


def _build_empty_final_report(report: AggregatedFPLReport) -> FinalGameweekReport:
    return FinalGameweekReport(
        gameweek=report.gameweek,
        overview=(
            "There is not enough aggregated expert data yet to produce a confident final report. "
            "Treat this as a placeholder until more expert analysis is available."
        ),
        transfers=[],
        captaincy=[],
        chip_strategy=[],
        fixture_notes=[],
        disagreements=[],
        conditional_advice=[],
        wait_for_news=[],
        conclusion="Wait for more expert input before making aggressive moves.",
    )


def build_fallback_final_report(report: AggregatedFPLReport) -> FinalGameweekReport:
    """Build a safe report when synthesis is unavailable or malformed."""
    overview = (
        f"Aggregated input from {report.expert_count} expert sources highlights the strongest consensus plays, "
        "while preserving areas of uncertainty."
        if report.expert_count
        else "There is not enough aggregated expert data yet to produce a confident final report."
    )

    transfers = [
        FinalRecommendation(
            title=f"{item.direction.title()} {item.player_name}",
            rationale=(
                f"Mentioned by {item.mention_count} expert(s): "
                + ", ".join(item.supporting_experts)
            ),
            confidence=item.average_confidence,
        )
        for item in report.transfer_consensus[:3]
    ]
    captaincy = [
        FinalRecommendation(
            title=item.item,
            rationale=(
                f"Backed by {item.mention_count} expert(s): "
                + ", ".join(item.supporting_experts)
            ),
            confidence=item.average_confidence,
        )
        for item in report.captaincy_consensus[:2]
    ]
    chip_strategy = [
        FinalRecommendation(
            title=item.item,
            rationale=(
                f"Supported by {item.mention_count} expert(s): "
                + ", ".join(item.supporting_experts)
            ),
            confidence=item.average_confidence,
        )
        for item in report.chip_strategy_consensus[:2]
    ]
    disagreements = [
        FinalDisagreement(
            topic=f"Player split: {item.player}",
            summary=(
                f"Some experts support {item.player} while others advise against the move."
            ),
            sides=[
                f"Positive: {', '.join(item.positive_experts)}",
                f"Negative: {', '.join(item.negative_experts)}",
            ],
        )
        for item in report.disagreements.players
    ]

    return FinalGameweekReport(
        gameweek=report.gameweek,
        overview=overview,
        transfers=transfers,
        captaincy=captaincy,
        chip_strategy=chip_strategy,
        fixture_notes=[item.insight for item in report.fixture_insights[:3]],
        disagreements=disagreements,
        conditional_advice=[item.text for item in report.conditional_advice[:3]],
        wait_for_news=report.wait_for_news,
        conclusion="Use the strongest consensus signals and monitor late team news before the deadline.",
    )


async def synthesize_final_report(report: AggregatedFPLReport) -> FinalGameweekReport:
    """Convert aggregated FPL data into a polished final gameweek report."""
    if report.expert_count == 0:
        return _build_empty_final_report(report)

    try:
        return await run_final_synthesis(report)
    except Exception:
        return build_fallback_final_report(report)
