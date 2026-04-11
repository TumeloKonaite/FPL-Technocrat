from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.schemas.aggregate_report import ExpertTeamRevealItem
from src.services.normalization import canonical_player_display, normalize_lookup_key, normalize_player_name


@dataclass(frozen=True)
class SuggestedTeamOfWeek:
    starting_xi: list[str]
    bench: list[str]
    captain: str | None
    vice_captain: str | None
    player_votes: dict[str, int]
    bench_votes: dict[str, int]


TEAM_UI_ALIASES = {
    "semeno": "antoine semenyo",
}


def _rank_counter(counter: Counter[str]) -> list[tuple[str, int]]:
    return sorted(counter.items(), key=lambda item: (-item[1], item[0].lower()))


def _normalize_team_player(name: str | None) -> str:
    lookup = normalize_lookup_key(name)
    if lookup in TEAM_UI_ALIASES:
        return TEAM_UI_ALIASES[lookup]

    normalized = normalize_player_name(name or "")
    if normalized:
        return normalized
    return lookup


def build_suggested_team_of_week(
    reveals: list[ExpertTeamRevealItem],
) -> SuggestedTeamOfWeek | None:
    if not reveals:
        return None

    starter_votes: Counter[str] = Counter()
    bench_votes: Counter[str] = Counter()
    captain_votes: Counter[str] = Counter()
    vice_votes: Counter[str] = Counter()

    for reveal in reveals:
        starter_votes.update(
            normalized
            for player in reveal.starting_xi
            if (normalized := _normalize_team_player(player))
        )
        bench_votes.update(
            normalized
            for player in reveal.bench
            if (normalized := _normalize_team_player(player))
        )
        if reveal.captain:
            normalized_captain = _normalize_team_player(reveal.captain)
            if normalized_captain:
                captain_votes.update([normalized_captain])
        if reveal.vice_captain:
            normalized_vice = _normalize_team_player(reveal.vice_captain)
            if normalized_vice:
                vice_votes.update([normalized_vice])

    if not starter_votes:
        return None

    starting_xi = [
        canonical_player_display(player)
        for player, _ in _rank_counter(starter_votes)[:11]
    ]
    excluded = set(starting_xi)
    bench = [
        canonical_player_display(player)
        for player, _ in _rank_counter(bench_votes)
        if canonical_player_display(player) not in excluded
    ][:4]

    captain = canonical_player_display(_rank_counter(captain_votes)[0][0]) if captain_votes else None
    vice_captain = (
        canonical_player_display(_rank_counter(vice_votes)[0][0]) if vice_votes else None
    )

    return SuggestedTeamOfWeek(
        starting_xi=starting_xi,
        bench=bench,
        captain=captain,
        vice_captain=vice_captain,
        player_votes={
            canonical_player_display(player): votes
            for player, votes in _rank_counter(starter_votes)
        },
        bench_votes={
            canonical_player_display(player): votes
            for player, votes in _rank_counter(bench_votes)
        },
    )
