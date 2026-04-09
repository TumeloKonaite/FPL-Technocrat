from __future__ import annotations

from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.schemas.final_report import AggregatedFPLReport
from src.services.aggregation_service import build_aggregated_fpl_report


def _build_analysis(
    expert_name: str,
    *,
    recommended_players: list[str] | None = None,
    avoid_players: list[str] | None = None,
    captaincy_picks: list[str] | None = None,
    chip_strategy: str | None = None,
    key_takeaways: list[str] | None = None,
    reasoning: list[str] | None = None,
    confidence: str = "medium",
) -> ExpertVideoAnalysis:
    return ExpertVideoAnalysis(
        expert_name=expert_name,
        video_title=f"{expert_name} GW5",
        gameweek=5,
        summary=f"Summary for {expert_name}",
        key_takeaways=key_takeaways or [],
        recommended_players=recommended_players or [],
        avoid_players=avoid_players or [],
        captaincy_picks=captaincy_picks or [],
        chip_strategy=chip_strategy,
        reasoning=reasoning or [],
        confidence=confidence,
    )


def test_player_consensus_counts_supporting_experts_once() -> None:
    analyses = [
        _build_analysis("Expert A", recommended_players=["Saka", "Bukayo Saka"], confidence="high"),
        _build_analysis("Expert B", recommended_players=["Bukayo Saka"], confidence="medium"),
        _build_analysis("Expert C", recommended_players=["Salah"], confidence="low"),
    ]

    report = build_aggregated_fpl_report(analyses)

    assert report.player_consensus[0].item == "Bukayo Saka"
    assert report.player_consensus[0].mention_count == 2
    assert report.player_consensus[0].supporting_experts == ["Expert A", "Expert B"]


def test_confidence_averaging_is_arithmetic_mean() -> None:
    analyses = [
        _build_analysis("Expert A", recommended_players=["Salah"], confidence="high"),
        _build_analysis("Expert B", recommended_players=["Mohamed Salah"], confidence="medium"),
        _build_analysis("Expert C", recommended_players=["Salah"], confidence="low"),
    ]

    report = build_aggregated_fpl_report(analyses)

    salah = report.player_consensus[0]
    assert salah.item == "Mohamed Salah"
    assert salah.mention_count == 3
    assert salah.average_confidence == 0.6667


def test_duplicate_mentions_are_normalized_consistently() -> None:
    analyses = [
        _build_analysis(
            "Expert A",
            recommended_players=["Saka", "Bukayo Saka", " SAKA "],
            captaincy_picks=["Haaland", "Erling Haaland"],
            chip_strategy="WC",
            confidence="high",
        ),
        _build_analysis(
            "Expert B",
            recommended_players=["Bukayo Saka"],
            captaincy_picks=["Erling Haaland"],
            chip_strategy="wildcard",
            confidence="medium",
        ),
    ]

    report = build_aggregated_fpl_report(analyses)

    assert [item.item for item in report.player_consensus] == ["Bukayo Saka"]
    assert report.player_consensus[0].mention_count == 2
    assert [item.item for item in report.captaincy_consensus] == ["Erling Haaland"]
    assert report.captaincy_consensus[0].mention_count == 2
    assert [item.item for item in report.chip_strategy_consensus] == ["wildcard"]


def test_aggregated_report_is_schema_valid_for_empty_input() -> None:
    report = build_aggregated_fpl_report([])

    validated = AggregatedFPLReport.model_validate(report.model_dump())

    assert validated.expert_count == 0
    assert validated.gameweek is None
    assert validated.player_consensus == []
    assert validated.transfer_consensus == []
    assert validated.fixture_insights == []


def test_transfer_and_fixture_aggregation_are_deterministic() -> None:
    analyses = [
        _build_analysis(
            "Expert B",
            recommended_players=["Salah"],
            avoid_players=["Watkins"],
            key_takeaways=["Arsenal have a strong fixture run"],
            reasoning=["Arsenal have a strong fixture run"],
            confidence="medium",
        ),
        _build_analysis(
            "Expert A",
            recommended_players=["Mohamed Salah"],
            avoid_players=["Ollie Watkins"],
            key_takeaways=["Arsenal have a strong fixture run"],
            reasoning=["Liverpool attack still looks elite"],
            confidence="high",
        ),
    ]

    report = build_aggregated_fpl_report(analyses)

    assert [item.player_name for item in report.transfer_consensus] == [
        "Mohamed Salah",
        "Ollie Watkins",
    ]
    assert [item.direction for item in report.transfer_consensus] == ["buy", "sell"]
    assert report.fixture_insights[0].insight == "Arsenal have a strong fixture run"
    assert report.fixture_insights[0].mention_count == 2
