from __future__ import annotations

import requests
from typing import Any


class FPLService:
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "fpl-agent/0.1",
                "Accept": "application/json",
            }
        )

    def _get(self, path: str) -> Any:
        url = f"{self.BASE_URL}{path}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_bootstrap_static(self) -> dict[str, Any]:
        return self._get("/bootstrap-static/")

    def get_fixtures(self) -> list[dict[str, Any]]:
        return self._get("/fixtures/")

    def get_event_live(self, gameweek: int) -> dict[str, Any]:
        return self._get(f"/event/{gameweek}/live/")

    def get_element_summary(self, player_id: int) -> dict[str, Any]:
        return self._get(f"/element-summary/{player_id}/")

    def get_entry(self, team_id: int) -> dict[str, Any]:
        return self._get(f"/entry/{team_id}/")

    def get_entry_picks(self, team_id: int, gameweek: int) -> dict[str, Any]:
        return self._get(f"/entry/{team_id}/event/{gameweek}/picks/")

    def get_my_team(self, team_id: int, gameweek: int) -> dict[str, Any]:
        return self._get(f"/entry/{team_id}/event/{gameweek}/picks/")

    def get_player_news(self) -> list[dict[str, Any]]:
        data = self.get_bootstrap_static()
        players = data.get("elements", [])
        teams = {team["id"]: team["name"] for team in data.get("teams", [])}
        positions = {
            element_type["id"]: element_type["singular_name_short"]
            for element_type in data.get("element_types", [])
        }

        news_items: list[dict[str, Any]] = []

        for player in players:
            news_text = (player.get("news") or "").strip()

            news_items.append(
                {
                    "id": player["id"],
                    "player_id": player["id"],
                    "web_name": player["web_name"],
                    "name": player["web_name"],
                    "team_id": player["team"],
                    "team_name": teams.get(player["team"]),
                    "position_id": player.get("element_type"),
                    "position": positions.get(player.get("element_type")),
                    "price": (player.get("now_cost") or 0) / 10,
                    "availability": player.get("status"),
                    "status": player.get("status"),
                    "chance_of_playing_next_round": player.get("chance_of_playing_next_round"),
                    "chance_of_playing_this_round": player.get("chance_of_playing_this_round"),
                    "news": news_text,
                }
            )

        return news_items
