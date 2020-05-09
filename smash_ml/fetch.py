import json
from asyncio import Future
from datetime import datetime
from os import path
from sys import maxsize
from time import sleep
from typing import Awaitable, Callable, Coroutine, List

from aiohttp import ClientSession

_api_token: str = None
_event_entrants_query: str = None
_event_phase_groups_query: str = None
_event_sets_query: str = None
_event_standings_query: str = None
_player_info_query: str = None
_tournament_events_query: str = None

_QUERYDIR = path.join(path.dirname(__file__), "queries")
_session = ClientSession()
_query_times = []
_rate_limit_delay = 0.75


async def _fetch(query: str, variables: dict) -> dict:
    global _api_token, _session, _query_times, _rate_limit_delay
    if _api_token is None:
        with open(path.join(path.dirname(__file__), "token"), "r") as file:
            _api_token = file.read().strip()
    _query_times = list(
        filter(
            lambda query_time: (datetime.now() - query_time).total_seconds() <= 60,
            _query_times,
        )
    )
    if len(_query_times) >= 80:
        sleep(0.75)
    async with _session.post(
        "https://api.smash.gg/gql/alpha",
        json={"query": query, "variables": variables},
        headers={"Authorization": f"Bearer {_api_token}"},
    ) as response:
        json = await response.json()
        if "success" in json and json["success"] == False:
            message = json["message"]
            if message == "Rate limit exceeded - api-token":
                print("Rate limit hit")
                sleep(_rate_limit_delay)
                _rate_limit_delay += 0.05
                return await _fetch(query, variables)
            else:
                raise Exception(f"Query failed: {message}")
        if "errors" in json:
            message = json["errors"][0]["message"]
            raise Exception(f"Query failed: {message}")
        _query_times.append(datetime.now())
        return json


async def _get_pages(get: Callable[[str, int], Awaitable[dict]], arg: str) -> list:
    page_num = 0
    page = await get(arg, page_num)
    entries = page["nodes"]
    total = page["pageInfo"]["total"]
    while len(entries) < total:
        page_num += 1
        page = await get(arg, page_num)
        new_entries = page["nodes"]
        entries.extend(new_entries)
    return entries


async def _event_entrants(eventId: str, page: int) -> dict:
    global _QUERYDIR, _event_entrants_query
    if _event_entrants_query is None:
        with open(path.join(_QUERYDIR, "EventEntrants.graphql"), "r") as query:
            _event_entrants_query = query.read()
    variables = {"eventId": eventId, "page": page, "perPage": 50}
    resp = await _fetch(_event_entrants_query, variables)
    return resp["data"]["event"]["entrants"]


def event_entrants(eventId: str) -> Awaitable[list]:
    return _get_pages(_event_entrants, eventId)


def tournament_events(eventSlug: str) -> Awaitable[dict]:
    global _QUERYDIR, _tournament_events_query
    if _tournament_events_query is None:
        with open(path.join(_QUERYDIR, "TournamentEvents.graphql"), "r") as query:
            _tournament_events_query = query.read()
    variables = {"tournamentSlug": eventSlug}
    return _fetch(_tournament_events_query, variables)


def event_phase_groups(eventId: str) -> Awaitable[dict]:
    global _QUERYDIR, _event_phase_groups_query
    if _event_phase_groups_query is None:
        with open(path.join(_QUERYDIR, "EventPhaseGroups.graphql"), "r") as query:
            _event_phase_groups_query = query.read()
    variables = {"eventId": eventId}
    return _fetch(_event_phase_groups_query, variables)


async def _event_sets(eventId: str, page: int) -> dict:
    global _QUERYDIR, _event_sets_query
    if _event_sets_query is None:
        with open(path.join(_QUERYDIR, "EventSets.graphql"), "r") as query:
            _event_sets_query = query.read()
    variables = {"eventId": eventId, "page": page, "perPage": 30}
    resp = await _fetch(_event_sets_query, variables)
    return resp["data"]["event"]["sets"]


def event_sets(eventId: str) -> Awaitable[list]:
    return _get_pages(_event_sets, eventId)


async def _event_standings(eventId: str, page: int) -> dict:
    global _QUERYDIR, _event_standings_query
    if _event_standings_query is None:
        with open(path.join(_QUERYDIR, "EventStandings.graphql"), "r") as query:
            _event_standings_query = query.read()
    variables = {"eventId": eventId, "page": page, "perPage": 250}
    resp = await _fetch(_event_standings_query, variables)
    return resp["data"]["event"]["standings"]


def event_standings(eventId: str) -> Awaitable[list]:
    return _get_pages(_event_standings, eventId)
