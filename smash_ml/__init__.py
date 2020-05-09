from asyncio import get_event_loop
from os import path
from pathlib import Path, PurePath
from pickle import HIGHEST_PROTOCOL, dump, load

from pandas import DataFrame, read_csv

from smash_ml.fetch import (
    _session,
    event_entrants,
    event_phase_groups,
    event_sets,
    tournament_events,
)
from smash_ml.preprocess import preprocess_entrants, preprocess_sets
from smash_ml.train import train

__version__ = "0.1.0"

_PICKLEDIR = Path(Path(__file__).parent / "pickle")
_loaded_slugs = []

_DEFAULT_SLUGS = (
    "ceo-2018-fighting-game-championships",
    "ceo-2019-fighting-game-championships",
    "ceo-dreamland-2020",
    "don-t-park-on-the-grass-2018-1",
    "dreamhack-atlanta-2019",
    "dreamhack-dallas-2019",
    "dreamhack-montreal-2019",
    "evo-2018",
    "full-bloom-5",
    "gametyrant-expo-2018",
    "gametyrant-expo-2019-1",
    "genesis-6",
    "genesis-7-1",
    "get-on-my-level-2019-canadian-fighting-game-championships-3",
    "low-tier-city-7",
    "mainstage",
    "mango-s-birthday-bash-red-bull-adrenalan",
    "momocon-2019-1",
    "pound-2019",
    "shine-2018",
    "shine-2019",
    "smash-conference-united",
    "smash-n-splash-4",
    "smash-n-splash-5",
    "smash-summit-8",
    "smash-summit-9",
    "super-smash-con-2019",
    "the-big-house-8",
    "the-big-house-9",
    "the-quarantine-series",
)


async def _gather_sets(eventId: str) -> DataFrame:
    return DataFrame.from_records(
        preprocess_sets(await event_sets(eventId))
    ).convert_dtypes()


async def _gather_entrants(eventId: str) -> (DataFrame, DataFrame):
    entrants = preprocess_entrants(await event_entrants(eventId))
    return DataFrame.from_records(entrants).convert_dtypes()


async def train_on_event(slug):
    global _PICKLEDIR, _loaded_slugs
    if slug in _loaded_slugs:
        print(f"Tournament {slug} already trained")
        return
    sets: DataFrame = None
    pickle_file = _PICKLEDIR.joinpath(f"{slug}.pickle")
    if pickle_file.is_file():
        print(f"Loading from {pickle_file}")
        with open(str(pickle_file), "rb") as file_stream:
            sets = load(file_stream)
    else:
        event_resp = await tournament_events(slug)
        tournament = event_resp["data"]["tournament"]
        tournamentName = tournament["name"]
        print(f"{tournamentName} events: ")
        events = list(
            filter(lambda event: event["videogame"]["id"] == 1, tournament["events"])
        )
        event_id = events[0]["id"]
        if len(events) > 1:
            for index, event in enumerate(events):
                eventName = event["name"]
                print(f"{index + 1} - {eventName}")
            event_id = events[
                int(input("Choose an event to get set data for: ").strip()) - 1
            ]["id"]
        entrants = await _gather_entrants(event_id)
        sets = await _gather_sets(event_id)
        with open(str(pickle_file), "wb") as file_stream:
            dump(sets, file_stream)
    _loaded_slugs.append(slug)
    train(sets)


async def loop():
    global _PICKLEDIR, _DEFAULT_SLUGS, _loaded_slugs
    for slug in _DEFAULT_SLUGS:
        await train_on_event(slug)
    for file in _PICKLEDIR.glob("*.pickle"):
        if file.stem not in _loaded_slugs:
            await train_on_event(file.stem)
    while True:
        slug = input("Enter tournament slug: ").strip()
        if slug == "-1" or slug == "":
            return await _session.close()
        await train_on_event(slug)


def main():
    event_loop = get_event_loop()
    event_loop.run_until_complete(loop())
