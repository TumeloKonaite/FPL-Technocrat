from __future__ import annotations

from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.services.disagreement_service import (
    build_disagreement_report,
    extract_conditional_advice,
    extract_wait_for_news_entities,
)


def _build_analysis(
    expert_name: str,
    *,
    recommended_players: list[str] | None = None,
    avoid_players: list[str] | None = None,
    captaincy_picks: list[str] | None = None,
    chip_strategy: str | None = None,
    key_takeaways: list[str] | None = None,
    reasoning: list[str] | None = None,
    summary: str | None = None,
) -> ExpertVideoAnalysis:
    return ExpertVideoAnalysis(
        expert_name=expert_name,
        video_title=f"{expert_name} GW5",
        gameweek=5,
        summary=summary or f"Summary for {expert_name}",
        key_takeaways=key_takeaways or [],
        recommended_players=recommended_players or [],
        avoid_players=avoid_players or [],
        captaincy_picks=captaincy_picks or [],
        chip_strategy=chip_strategy,
        reasoning=reasoning or [],
        confidence="medium",
    )


def test_detects_player_disagreement_with_expert_attribution() -> None:
    analyses = [
        _build_analysis("Expert A", recommended_players=["Saka"]),
        _build_analysis("Expert B", avoid_players=["Bukayo Saka"]),
    ]

    report = build_disagreement_report(analyses)

    assert len(report.players) == 1
    assert report.players[0].player == "Bukayo Saka"
    assert report.players[0].positive_experts == ["Expert A"]
    assert report.players[0].negative_experts == ["Expert B"]


def test_detects_split_captaincy() -> None:
    analyses = [
        _build_analysis("Expert A", captaincy_picks=["Salah"]),
        _build_analysis("Expert B", captaincy_picks=["Haaland"]),
        _build_analysis("Expert C", captaincy_picks=["Mohamed Salah"]),
    ]

    report = build_disagreement_report(analyses)

    assert len(report.captaincy) == 1
    assert report.captaincy[0].options == [
        "Mohamed Salah",
        "Erling Haaland",
    ]
    assert report.captaincy[0].expert_map["Mohamed Salah"] == ["Expert A", "Expert C"]
    assert report.captaincy[0].expert_map["Erling Haaland"] == ["Expert B"]


def test_detects_strategy_disagreement() -> None:
    analyses = [
        _build_analysis("Expert A", reasoning=["I would roll the transfer this week"]),
        _build_analysis("Expert B", reasoning=["I would buy now before the price rise"]),
    ]

    report = build_disagreement_report(analyses)

    assert len(report.strategy) == 1
    assert report.strategy[0].side_a == "roll"
    assert report.strategy[0].side_a_experts == ["Expert A"]
    assert report.strategy[0].side_b == "buy_now"
    assert report.strategy[0].side_b_experts == ["Expert B"]


def test_extracts_conditional_phrases() -> None:
    analyses = [
        _build_analysis(
            "Expert A",
            reasoning=["If Saka is fit, he becomes the standout buy"],
        ),
    ]

    items = extract_conditional_advice(analyses)

    assert len(items) == 1
    assert items[0].expert_name == "Expert A"
    assert items[0].text == "If Saka is fit, he becomes the standout buy"
    assert items[0].reason == "injury_update"
    assert items[0].related_entities == ["Bukayo Saka"]


def test_extracts_wait_for_news_entities() -> None:
    analyses = [
        _build_analysis(
            "Expert A",
            reasoning=["Wait for press conference news on Saka"],
        ),
    ]

    items = extract_conditional_advice(analyses)

    assert len(items) == 1
    assert items[0].reason == "press_conference"
    assert extract_wait_for_news_entities(items) == ["Bukayo Saka"]
