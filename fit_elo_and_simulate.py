# 1) loads cleaned matches 
# 2) fit surface-weighted elo (hard court)
# 3) load AO 2024 draw with IDs (128 rows)
# 4) run Monte Carlo simulations (100,000)
# 5) save probabilities (R16/QF/SF/F/W) for every player in the draw

# Expected files in: 
#   - atp_matches_2021_2023_clean.csv
#   - AO2024Draw.csv
# optional (use for a nicer output)
# atp_players.csv  (to join names cleanly)
# MAKE SURE TO CHANGE THE BASE_DIR TO YOUR CURRENT WORKING DIRECTORY

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

# file paths
BASE_DIR = Path("*")

MATCHES_CLEAN = BASE_DIR / "atp_matches_2021_2023_clean.csv"
DRAW_FIXED = BASE_DIR / "AO2024Draw.csv"

OUT_ELO = BASE_DIR / "elo_asof_2024-01-01.csv"
OUT_PROBS = BASE_DIR / "ao2024_advancement_probabilities.csv"
OUT_CHAMP = BASE_DIR / "ao2024_champion_probabilities.csv"


@dataclass(frozen=True)
class EloParams:
    base_elo: float = 1500.0
    k_bo3: float = 24.0
    k_bo5: float = 32.0
    weight_hard: float = 1.0
    weight_other: float = 0.5


@dataclass(frozen=True)
class SimParams:
    n_sims: int = 100000
    seed: int = 42


# elo functions
def expected_score(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))

def k_for_best_of(best_of: int, p: EloParams) -> float:
    return p.k_bo5 if int(best_of) == 5 else p.k_bo3

def surface_weight(surface_norm: str, p: EloParams) -> float:
    return p.weight_hard if surface_norm == "Hard" else p.weight_other

def update_elo(
    elos: Dict[int, float],
    winner_id: int,
    loser_id: int,
    best_of: int,
    surface_norm: str,
    p: EloParams,
) -> None:
    w = int(winner_id)
    l = int(loser_id)

    if w not in elos:
        elos[w] = p.base_elo
    if l not in elos:
        elos[l] = p.base_elo

    ew = expected_score(elos[w], elos[l])
    k = k_for_best_of(best_of, p) * surface_weight(surface_norm, p)

    elos[w] = elos[w] + k * (1.0 - ew)
    elos[l] = elos[l] + k * (0.0 - (1.0 - ew))

def fit_elo(matches: pd.DataFrame, p: EloParams) -> Dict[int, float]:
    req = ["tourney_date_dt", "surface_norm", "best_of", "winner_id", "loser_id"]
    missing = [c for c in req if c not in matches.columns]
    if missing:
        raise ValueError(f"Matches file missing columns: {missing}")

    m = matches.sort_values("tourney_date_dt").reset_index(drop=True)
    elos: Dict[int, float] = {}

    for _, row in m.iterrows():
        update_elo(
            elos=elos,
            winner_id=int(row["winner_id"]),
            loser_id=int(row["loser_id"]),
            best_of=int(row["best_of"]),
            surface_norm=str(row["surface_norm"]),
            p=p,
        )
    return elos

# simulation functions
ROUNDS = ["R128", "R64", "R32", "R16", "QF", "SF", "F", "W"]

def match_win_prob(a_id: int, b_id: int, elos: Dict[int, float], base_elo: float) -> float:
    ea = elos.get(int(a_id), base_elo)
    eb = elos.get(int(b_id), base_elo)
    return expected_score(ea, eb)

def simulate_one_tournament_with_rounds(
    players_in_order: List[int],
    elos: Dict[int, float],
    base_elo: float,
    rng: np.random.Generator,
) -> Tuple[int, Dict[int, set]]:
    """
    Returns:
      champ_id
      reached: dict[player_id] -> set of rounds reached (e.g., {"R128","R64","R32",...})
    """
    n = len(players_in_order)
    if n == 0 or (n & (n - 1)) != 0:
        raise ValueError("Draw size must be a power of 2 (expected 128).")

    reached = {pid: {"R128"} for pid in players_in_order}

    round_players = list(players_in_order)
    round_names = ["R64", "R32", "R16", "QF", "SF", "F", "W"]

    for rn in round_names:
        nxt = []
        for i in range(0, len(round_players), 2):
            a = round_players[i]
            b = round_players[i + 1]
            p_a = match_win_prob(a, b, elos, base_elo)
            winner = a if rng.random() < p_a else b
            reached[winner].add(rn)
            nxt.append(winner)
        round_players = nxt

    champ = round_players[0]
    return champ, reached

def run_monte_carlo(
    players_in_order: List[int],
    elos: Dict[int, float],
    base_elo: float,
    n_sims: int,
    seed: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      advancement_probs_df: one row per player_id with columns for round reach probabilities
      champion_probs_df: one row per player_id with P(win)
    """
    rng = np.random.default_rng(seed)

    counts = {pid: {r: 0 for r in ROUNDS} for pid in players_in_order}
    champ_counts = {pid: 0 for pid in players_in_order}

    for _ in range(int(n_sims)):
        champ, reached = simulate_one_tournament_with_rounds(players_in_order, elos, base_elo, rng)

        champ_counts[champ] += 1
        for pid, rs in reached.items():
            for r in rs:
                counts[pid][r] += 1

    # build advancement probs
    adv = []
    for pid in players_in_order:
        row = {"player_id": pid}
        for r in ROUNDS:
            row[r] = counts[pid][r] / n_sims
        adv.append(row)

    advancement_df = pd.DataFrame(adv)

    # champion probs
    champ_df = pd.DataFrame(
        {"player_id": list(champ_counts.keys()), "p_win": [v / n_sims for v in champ_counts.values()]}
    )

    return advancement_df, champ_df


def main():
    if not MATCHES_CLEAN.exists():
        raise FileNotFoundError(f"Missing matches file: {MATCHES_CLEAN}")
    if not DRAW_FIXED.exists():
        raise FileNotFoundError(f"Missing draw file: {DRAW_FIXED}")

    print("Loading matches...")
    matches = pd.read_csv(MATCHES_CLEAN)
    # Ensure date column is datetime
    matches["tourney_date_dt"] = pd.to_datetime(matches["tourney_date_dt"], errors="coerce")
    matches = matches.dropna(subset=["tourney_date_dt"]).copy()
    matches["tourney_date_dt"] = matches["tourney_date_dt"].dt.date

    print("Fitting Elo...")
    elo_params = EloParams()
    elos = fit_elo(matches, elo_params)

    # Save Elo snapshot
    elo_df = pd.DataFrame({"player_id": list(elos.keys()), "elo": list(elos.values())}).sort_values("elo", ascending=False)
    elo_df.to_csv(OUT_ELO, index=False)
    print(f"Saved Elo snapshot: {OUT_ELO}")

    print("Loading draw...")
    draw = pd.read_csv(DRAW_FIXED)

    # Validate draw
    if "player_id" not in draw.columns:
        raise ValueError("Draw file must contain player_id column.")
    draw = draw.sort_values("draw_position")
    if len(draw) != 128:
        raise ValueError(f"Expected 128 rows in draw, found {len(draw)}")
    if draw["draw_position"].min() != 1 or draw["draw_position"].max() != 128:
        raise ValueError("draw_position must run from 1 to 128.")
    if not draw["draw_position"].is_unique:
        raise ValueError("draw_position contains duplicates.")
    if draw["player_id"].isna().any():
        raise ValueError("Some player_id are missing in draw.")

    players_in_order = draw["player_id"].astype(int).tolist()

    print("Running Monte Carlo...")
    sim_params = SimParams()
    advancement_df, champ_df = run_monte_carlo(
        players_in_order=players_in_order,
        elos=elos,
        base_elo=elo_params.base_elo,
        n_sims=sim_params.n_sims,
        seed=sim_params.seed,
    )

    # join names/seed/entry from draw for readability
    meta_cols = [c for c in ["draw_position", "section", "seed", "player", "entry", "player_id"] if c in draw.columns]
    meta = draw[meta_cols].copy()

    advancement_out = meta.merge(advancement_df, on="player_id", how="left")
    champ_out = meta.merge(champ_df, on="player_id", how="left")

    # sort for output
    advancement_out = advancement_out.sort_values("W", ascending=False)
    champ_out = champ_out.sort_values("p_win", ascending=False)

    advancement_out.to_csv(OUT_PROBS, index=False)
    champ_out.to_csv(OUT_CHAMP, index=False)

    print(f"Saved advancement probabilities: {OUT_PROBS}")
    print(f"Saved champion probabilities:    {OUT_CHAMP}")

    # quick preview
    print("\nTop 15 by P(win):")
    print(champ_out[["player", "seed", "p_win"]].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
