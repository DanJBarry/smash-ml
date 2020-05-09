from asyncio import Future, gather
from statistics import mode
from typing import Awaitable, Callable, List

from pandas import DataFrame


def preprocess_set(node: dict) -> dict:
    winner_id = node.pop("winnerId")
    slots = node.pop("slots")
    games = node.pop("games")
    set_seeds = {}
    for slot in slots:
        set_seeds[slot["seed"]["seedNum"]] = slot["entrant"]["id"]
    high_seed_num = min(set_seeds.keys())
    low_seed_num = max(set_seeds.keys())
    high_seed_id = set_seeds[high_seed_num]
    low_seed_id = set_seeds[low_seed_num]
    node["highSeedNum"] = high_seed_num
    node["lowSeedNum"] = low_seed_num
    node["upset"] = winner_id == low_seed_id
    if games:
        if len(games) <= 3:
            node["bestOf"] = 3
        elif len(games) <= 5:
            node["bestOf"] = 5
        characters = ([], [])
        for game in games:
            if game["selections"]:
                for selection in game["selections"]:
                    if selection["entrant"]["id"] == low_seed_id:
                        characters[0].append(selection["selectionValue"])
                    else:
                        characters[1].append(selection["selectionValue"])
        if len(characters[0]) > 0:
            node["lowSeedCharacter"] = mode(characters[0])
        else:
            node["lowSeedCharacter"] = 0
        if len(characters[1]) > 0:
            node["highSeedCharacter"] = mode(characters[1])
        else:
            node["highSeedCharacter"] = 0
    else:
        node["bestOf"] = 0
        node["lowSeedCharacter"] = 0
        node["highSeedCharacter"] = 0
    if node["startedAt"]:
        node["startedAt"] = node["startedAt"] % 86400
    else:
        node["startedAt"] = -1
    return node


def _preprocess_entrant(entrant: dict) -> dict:
    entrant["entrantId"] = entrant.pop("id")
    entrant["playerId"] = entrant.pop("participants")[0]["player"]["id"]
    return entrant


def preprocess_sets(sets: List[dict]) -> List[dict]:
    return map(preprocess_set, sets)


def preprocess_entrants(entrants: List[dict]) -> List[dict]:
    # seeds is actually a list of lists so flatten it
    return map(_preprocess_entrant, entrants)
