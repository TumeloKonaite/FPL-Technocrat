from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.services.fpl_service import FPLService

fpl_service = FPLService()


class BootstrapResponse(BaseModel):
    """Structured summary of the main FPL bootstrap dataset."""

    total_players: int
    total_teams: int
    total_events: int
    sample_players: list[dict[str, Any]]


def get_bootstrap_data() -> dict[str, Any]:
    """Return a compact summary of the FPL bootstrap-static dataset.

    Includes overall counts for players, teams, and events, plus a small
    sample of player records for quick inspection.
    """
    data = fpl_service.get_bootstrap_static()
    return BootstrapResponse(
        total_players=len(data.get("elements", [])),
        total_teams=len(data.get("teams", [])),
        total_events=len(data.get("events", [])),
        sample_players=[
            {
                "id": p["id"],
                "web_name": p["web_name"],
                "team": p["team"],
                "now_cost": p["now_cost"],
                "total_points": p["total_points"],
                "form": p["form"],
                "minutes": p["minutes"],
                "selected_by_percent": p["selected_by_percent"],
            }
            for p in data.get("elements", [])[:10]
        ],
    ).model_dump()


def get_fixtures() -> list[dict[str, Any]]:
    """Return a trimmed list of upcoming or recent FPL fixtures."""
    fixtures = fpl_service.get_fixtures()
    return fixtures[:20]


def get_player_news() -> list[dict[str, Any]]:
    """Return player availability and injury news from FPL bootstrap data."""
    return fpl_service.get_player_news()


def get_live_gameweek_data(gameweek: int) -> dict[str, Any]:
    """Return live FPL data for a specific gameweek.

    Args:
        gameweek: The FPL gameweek number to fetch.
    """
    return fpl_service.get_event_live(gameweek)


def get_player_detail(player_id: int) -> dict[str, Any]:
    """Return detailed FPL history and fixture data for one player.

    Args:
        player_id: The FPL player ID.
    """
    return fpl_service.get_element_summary(player_id)


def get_manager_team(team_id: int, gameweek: int) -> dict[str, Any]:
    """Return a manager's entry details and picks for a given gameweek."""
    entry = fpl_service.get_entry(team_id)
    picks = fpl_service.get_entry_picks(team_id, gameweek)
    return {
        "entry": entry,
        "picks": picks,
    }


def get_manager_team_summary(team_id: int, gameweek: int) -> dict[str, Any]:
    """Return starters, bench, and automatic substitutions for a manager.

    Also attaches player names and gameweek points.
    """
    team_data = get_manager_team(team_id, gameweek)
    bootstrap = fpl_service.get_bootstrap_static()
    live = fpl_service.get_event_live(gameweek)

    picks_data = team_data["picks"]

    player_names: dict[int, str] = {
        player["id"]: f"{player['first_name']} {player['second_name']}"
        for player in bootstrap["elements"]
    }

    player_points: dict[int, int] = {
        item["id"]: item["stats"]["total_points"]
        for item in live["elements"]
    }

    starters = []
    bench = []

    for pick in picks_data["picks"]:
        player_id = pick["element"]
        player_info = {
            "element": player_id,
            "name": player_names.get(player_id, f"Player {player_id}"),
            "position": pick["position"],
            "points": player_points.get(player_id, 0),
            "multiplier": pick["multiplier"],
            "is_captain": pick["is_captain"],
            "is_vice_captain": pick["is_vice_captain"],
        }

        if pick["position"] <= 11:
            starters.append(player_info)
        else:
            bench.append(player_info)

    automatic_substitutions = []
    for sub in picks_data.get("automatic_subs", []):
        out_id = sub["element_out"]
        in_id = sub["element_in"]

        automatic_substitutions.append(
            {
                "out_element": out_id,
                "out_name": player_names.get(out_id, f"Player {out_id}"),
                "out_points": player_points.get(out_id, 0),
                "in_element": in_id,
                "in_name": player_names.get(in_id, f"Player {in_id}"),
                "in_points": player_points.get(in_id, 0),
            }
        )

    return {
        "entry": team_data["entry"],
        "gameweek": gameweek,
        "starters": starters,
        "bench": bench,
        "automatic_substitutions": automatic_substitutions,
    }
