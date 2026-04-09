from __future__ import annotations

import re

from src.schemas.aggregate_report import (
    CaptaincyDisagreementItem,
    ConditionalAdviceItem,
    DisagreementReport,
    PlayerDisagreementItem,
    StrategyDisagreementItem,
)
from src.schemas.expert_analysis import ExpertVideoAnalysis
from src.services.normalization import (
    PLAYER_ALIASES,
    canonical_player_display,
    normalize_chip_name,
    normalize_lookup_key,
    normalize_player_name,
    normalize_text_label,
)


_STRATEGY_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "roll": (
        re.compile(r"\broll\b"),
        re.compile(r"\broll transfer\b"),
        re.compile(r"\bsave (?:the )?transfer\b"),
        re.compile(r"\bbank (?:the )?transfer\b"),
        re.compile(r"\bhold (?:the )?transfer\b"),
    ),
    "buy_now": (
        re.compile(r"\bbuy\b"),
        re.compile(r"\bbuy now\b"),
        re.compile(r"\battack\b"),
        re.compile(r"\bmove early\b"),
        re.compile(r"\bmove now\b"),
        re.compile(r"\bmake (?:the )?move now\b"),
        re.compile(r"\bbring .* in now\b"),
        re.compile(r"\bjump on\b"),
    ),
    "wait": (
        re.compile(r"\bwait\b"),
        re.compile(r"\bwait for news\b"),
        re.compile(r"\bhold fire\b"),
        re.compile(r"\bdelay\b"),
        re.compile(r"\bmonitor\b"),
        re.compile(r"\bdelay transfer\b"),
    ),
    "take_hit": (
        re.compile(r"\btake (?:a )?hit\b"),
        re.compile(r"\bhit\b"),
        re.compile(r"\bminus ?4\b"),
        re.compile(r"\b-4\b"),
    ),
}

_STRATEGY_CONFLICTS = (
    ("roll", "buy_now"),
    ("roll", "take_hit"),
    ("wait", "buy_now"),
    ("wait", "take_hit"),
    ("roll", "wildcard"),
    ("roll", "free_hit"),
)

_CONDITIONAL_REASON_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("press_conference", re.compile(r"\bpress conference\b|\bpresser\b")),
    ("rotation_risk", re.compile(r"\brotation\b|\blineup\b|\bstarting xi\b")),
    ("injury_update", re.compile(r"\bfit\b|\bfitness\b|\binjur(?:y|ies)\b|\bknock\b|\bdoubt\b|\blate fitness test\b")),
    ("team_news", re.compile(r"\bteam news\b")),
    ("wait_for_news", re.compile(r"\bwait for news\b|\bmonitor\b|\bwait\b")),
    ("conditional_scenario", re.compile(r"^\s*(if|unless|provided|assuming|depending on)\b")),
)

_CONDITIONAL_SIGNAL = re.compile(
    r"^\s*(if|unless|provided|assuming|depending on)\b|\bwait\b|\bmonitor\b|\bpress conference\b|\bteam news\b|\bfitness\b|\binjury news\b",
)

_SPLIT_PATTERN = re.compile(r"[.!?;\n]+")


def _sorted_experts(experts: set[str]) -> list[str]:
    return sorted(experts, key=str.casefold)


def _extract_text_fragments(analysis: ExpertVideoAnalysis) -> list[str]:
    fragments: list[str] = []
    for raw_text in [analysis.summary, *analysis.key_takeaways, *analysis.reasoning]:
        for fragment in _SPLIT_PATTERN.split(raw_text):
            cleaned = fragment.strip()
            if cleaned:
                fragments.append(cleaned)
    return fragments


def _extract_players_from_text(text: str) -> list[str]:
    normalized_text = f" {normalize_text_label(text)} "
    players: set[str] = set()
    for alias in PLAYER_ALIASES:
        candidate = alias.strip()
        if not candidate or len(candidate) < 3:
            continue
        if f" {candidate} " in normalized_text:
            players.add(normalize_player_name(candidate))
    return sorted(players, key=normalize_lookup_key)


def detect_player_disagreements(
    analyses: list[ExpertVideoAnalysis],
) -> list[PlayerDisagreementItem]:
    positive_by_player: dict[str, set[str]] = {}
    negative_by_player: dict[str, set[str]] = {}

    for analysis in analyses:
        positive_players = {
            normalize_player_name(player)
            for player in analysis.recommended_players
            if normalize_player_name(player)
        }
        negative_players = {
            normalize_player_name(player)
            for player in analysis.avoid_players
            if normalize_player_name(player)
        }

        for player_key in positive_players:
            positive_by_player.setdefault(player_key, set()).add(analysis.expert_name)

        for player_key in negative_players:
            negative_by_player.setdefault(player_key, set()).add(analysis.expert_name)

    disagreements: list[PlayerDisagreementItem] = []
    for player_key in sorted(set(positive_by_player) & set(negative_by_player), key=normalize_lookup_key):
        disagreements.append(
            PlayerDisagreementItem(
                player=canonical_player_display(player_key),
                positive_experts=_sorted_experts(positive_by_player[player_key]),
                negative_experts=_sorted_experts(negative_by_player[player_key]),
            )
        )
    return disagreements


def detect_captaincy_disagreements(
    analyses: list[ExpertVideoAnalysis],
) -> list[CaptaincyDisagreementItem]:
    experts_by_player: dict[str, set[str]] = {}

    for analysis in analyses:
        unique_picks = {
            normalize_player_name(player)
            for player in analysis.captaincy_picks
            if normalize_player_name(player)
        }
        for player_key in unique_picks:
            experts_by_player.setdefault(player_key, set()).add(analysis.expert_name)

    if len(experts_by_player) < 2:
        return []

    sorted_items = sorted(
        experts_by_player.items(),
        key=lambda item: (-len(item[1]), normalize_lookup_key(item[0])),
    )
    expert_map = {
        canonical_player_display(player_key): _sorted_experts(experts)
        for player_key, experts in sorted_items
    }
    return [CaptaincyDisagreementItem(options=list(expert_map), expert_map=expert_map)]


def _extract_strategy_labels(analysis: ExpertVideoAnalysis) -> set[str]:
    labels: set[str] = set()

    chip_key = normalize_chip_name(analysis.chip_strategy)
    if chip_key != "none":
        labels.add(chip_key)

    for fragment in _extract_text_fragments(analysis):
        normalized_fragment = normalize_text_label(fragment)
        for label, patterns in _STRATEGY_PATTERNS.items():
            if any(pattern.search(normalized_fragment) for pattern in patterns):
                labels.add(label)

    return labels


def detect_strategy_disagreements(
    analyses: list[ExpertVideoAnalysis],
) -> list[StrategyDisagreementItem]:
    experts_by_strategy: dict[str, set[str]] = {}

    for analysis in analyses:
        for label in _extract_strategy_labels(analysis):
            experts_by_strategy.setdefault(label, set()).add(analysis.expert_name)

    disagreements: list[StrategyDisagreementItem] = []
    for side_a, side_b in _STRATEGY_CONFLICTS:
        experts_a = experts_by_strategy.get(side_a, set())
        experts_b = experts_by_strategy.get(side_b, set())
        if not experts_a or not experts_b:
            continue
        disagreements.append(
            StrategyDisagreementItem(
                side_a=side_a,
                side_a_experts=_sorted_experts(experts_a),
                side_b=side_b,
                side_b_experts=_sorted_experts(experts_b),
            )
        )

    return disagreements


def extract_conditional_advice(
    analyses: list[ExpertVideoAnalysis],
) -> list[ConditionalAdviceItem]:
    seen: set[tuple[str, str, str]] = set()
    items: list[ConditionalAdviceItem] = []

    for analysis in analyses:
        for fragment in _extract_text_fragments(analysis):
            normalized_fragment = normalize_text_label(fragment)
            if not _CONDITIONAL_SIGNAL.search(normalized_fragment):
                continue

            reason = "conditional"
            for candidate_reason, pattern in _CONDITIONAL_REASON_PATTERNS:
                if pattern.search(normalized_fragment):
                    reason = candidate_reason
                    break

            dedupe_key = (analysis.expert_name, normalized_fragment, reason)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            items.append(
                ConditionalAdviceItem(
                    expert_name=analysis.expert_name,
                    text=fragment,
                    reason=reason,
                    related_entities=[
                        canonical_player_display(player)
                        for player in _extract_players_from_text(fragment)
                    ],
                )
            )

    return sorted(
        items,
        key=lambda item: (
            item.expert_name.casefold(),
            normalize_lookup_key(item.text),
        ),
    )


def extract_wait_for_news_entities(
    conditional_advice: list[ConditionalAdviceItem],
) -> list[str]:
    entities = {
        entity
        for item in conditional_advice
        if item.reason in {
            "press_conference",
            "rotation_risk",
            "injury_update",
            "team_news",
            "wait_for_news",
        }
        for entity in item.related_entities
    }
    return sorted(entities, key=normalize_lookup_key)


def build_disagreement_report(
    analyses: list[ExpertVideoAnalysis],
) -> DisagreementReport:
    return DisagreementReport(
        players=detect_player_disagreements(analyses),
        captaincy=detect_captaincy_disagreements(analyses),
        strategy=detect_strategy_disagreements(analyses),
    )
