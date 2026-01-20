# mapAOdraw.py
# Maps AO 2024 draw player names -> player_id using atp_players.csv columns:
#   player_id, name_first, name_last, ...
#
# Input:
#   /Users/niclasnilsson/Desktop/AO/ao2024_draw.csv   (must include column: player)
#   /Users/niclasnilsson/Desktop/AO/atp_players.csv   (columns shown in your screenshot)
#
# Output:
#   /Users/niclasnilsson/Desktop/AO/ao2024_draw_with_ids.csv
#   /Users/niclasnilsson/Desktop/AO/ao2024_draw_unmatched.csv (only if some names fail)

from __future__ import annotations

from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path("/Users/niclasnilsson/Desktop/AO")

DRAW_CSV = BASE_DIR / "ao2024_draw.csv"
PLAYERS_CSV = BASE_DIR / "atp_players.csv"

OUT_MATCHED = BASE_DIR / "ao2024_draw_with_ids.csv"
OUT_UNMATCHED = BASE_DIR / "ao2024_draw_unmatched.csv"


def norm_name(s: str) -> str:
    """
    Strong normalization:
    - lowercase
    - remove all non-letter characters
    - collapse to single spaces
    """
    if pd.isna(s):
        return ""
    s = str(s).lower()
    s = re.sub(r"[^a-z]", " ", s)   # keep letters only
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_player_lookup(players: pd.DataFrame) -> pd.DataFrame:
    # Validate required columns
    required = {"player_id", "name_first", "name_last"}
    missing = sorted(required - set(players.columns))
    if missing:
        raise ValueError(
            f"Your atp_players.csv is missing columns: {missing}\n"
            f"Found columns: {list(players.columns)}"
        )

    p = players.copy()

    # Ensure numeric player_id
    p["player_id"] = pd.to_numeric(p["player_id"], errors="coerce").astype("Int64")
    p = p.dropna(subset=["player_id"]).copy()
    p["player_id"] = p["player_id"].astype(int)

    # Normalize first/last
    p["first_norm"] = p["name_first"].apply(norm_name)
    p["last_norm"] = p["name_last"].apply(norm_name)
    p["full_norm"] = (p["first_norm"] + " " + p["last_norm"]).str.strip()

    # Helpful fallback key
    p["first_initial_last"] = p["first_norm"].str[:1] + " " + p["last_norm"]

    return p[["player_id", "first_norm", "last_norm", "full_norm", "first_initial_last"]].drop_duplicates()


def main():
    if not DRAW_CSV.exists():
        raise FileNotFoundError(f"Missing draw file: {DRAW_CSV}")
    if not PLAYERS_CSV.exists():
        raise FileNotFoundError(f"Missing players file: {PLAYERS_CSV}")

    draw = pd.read_csv(DRAW_CSV)
    players = pd.read_csv(PLAYERS_CSV, low_memory=False)

    if "player" not in draw.columns:
        raise ValueError("Draw CSV must contain a column named 'player' with player full names.")

    lookup = build_player_lookup(players)

    draw = draw.copy()
    draw["player_norm"] = draw["player"].apply(norm_name)

    # 1) Exact match on normalized full name
    merged = draw.merge(
        lookup[["player_id", "full_norm"]],
        how="left",
        left_on="player_norm",
        right_on="full_norm",
    ).drop(columns=["full_norm"])

    merged["player_id"] = merged["player_id"].astype("Int64")

    # 2) Fallback for unmatched: last name + first token prefix
    unmatched_mask = merged["player_id"].isna()
    if unmatched_mask.any():
        tmp = merged.loc[unmatched_mask, ["player", "player_norm"]].copy()
        tmp["tokens"] = tmp["player_norm"].str.split()
        tmp["first_token"] = tmp["tokens"].apply(lambda t: t[0] if t else "")
        tmp["last_token"] = tmp["tokens"].apply(lambda t: t[-1] if t else "")

        cand = lookup[["player_id", "first_norm", "last_norm"]].copy()
        tmp = tmp.merge(cand, how="left", left_on="last_token", right_on="last_norm")

        # First name token prefix match (e.g., "jan" matches "jan lennard")
        tmp["first_ok"] = [
        fn.startswith(ft) if ft else False
        for fn, ft in zip(tmp["first_norm"].fillna(""), tmp["first_token"].fillna(""))]  
        tmp_ok = tmp[tmp["first_ok"]].copy()

        # If multiple candidates, pick the one with the longest first name
        tmp_ok["first_len"] = tmp_ok["first_norm"].fillna("").str.len()
        tmp_ok = tmp_ok.sort_values(["player_norm", "first_len"], ascending=[True, False])
        tmp_best = tmp_ok.drop_duplicates(subset=["player_norm"], keep="first")

        best_map = dict(zip(tmp_best["player_norm"], tmp_best["player_id"]))
        merged.loc[unmatched_mask, "player_id"] = (
            merged.loc[unmatched_mask, "player_norm"].map(best_map).astype("Int64")
        )

    # Save outputs
    merged_out = merged.drop(columns=["player_norm"])
    merged_out.to_csv(OUT_MATCHED, index=False)

    unmatched = merged_out[merged_out["player_id"].isna()].copy()
    if len(unmatched) > 0:
        unmatched.to_csv(OUT_UNMATCHED, index=False)
        print(f"Unmatched names: {len(unmatched)}")
        print(f"Saved: {OUT_UNMATCHED}")
        print("Examples:")
        print(unmatched["player"].head(20).to_string(index=False))
    else:
        print("All 128 players matched successfully.")

    print(f"Saved mapped draw: {OUT_MATCHED}")


if __name__ == "__main__":
    main()
