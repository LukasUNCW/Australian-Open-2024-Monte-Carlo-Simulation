from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path("/Users/niclasnilsson/Desktop/AO")

CHAMP_PROBS = BASE_DIR / "ao2024_champion_probabilities.csv"  # columns: player_id, p_win
PLAYERS = BASE_DIR / "atp_players.csv"                        # columns: player_id, name_first, name_last

OUT_DIR = BASE_DIR / "outputs" / "plots"
OUT_PNG = OUT_DIR / "ao2024_champion_probabilities_top15.png"

TOP_N = 8
HIGHLIGHT_NAME = "Jannik Sinner"  # used after name merge


def main():
    for p in [CHAMP_PROBS, PLAYERS]:
        if not p.exists():
            raise FileNotFoundError(f"Missing file: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    champ = pd.read_csv(CHAMP_PROBS)
    players = pd.read_csv(PLAYERS, low_memory=False)

    # Validate columns
    if not {"player_id", "p_win"}.issubset(champ.columns):
        raise ValueError("ao2024_champion_probabilities.csv must contain: player_id, p_win")
    if not {"player_id", "name_first", "name_last"}.issubset(players.columns):
        raise ValueError("atp_players.csv must contain: player_id, name_first, name_last")

    champ["player_id"] = champ["player_id"].astype(int)
    players["player_id"] = players["player_id"].astype(int)

    df = champ.merge(players[["player_id", "name_first", "name_last"]], on="player_id", how="left")
    df["player"] = (df["name_first"].fillna("") + " " + df["name_last"].fillna("")).str.strip()
    df.loc[df["player"] == "", "player"] = df["player_id"].astype(str)

    df = df.sort_values("p_win", ascending=False).head(TOP_N).copy()
    df["p_pct"] = df["p_win"] * 100

    # Build plot
    plt.figure(figsize=(12, 6))
    ax = plt.gca()

    bars = ax.bar(df["player"], df["p_pct"])

    # Highlight Sinner using hatch + thicker edge (no explicit color needed)
    highlight_idx = None
    for i, name in enumerate(df["player"].tolist()):
        if name.strip().lower() == HIGHLIGHT_NAME.strip().lower():
            highlight_idx = i
            break

    if highlight_idx is not None:
        bars[highlight_idx].set_hatch("///")
        bars[highlight_idx].set_linewidth(2.5)

        # Annotate directly above the bar
        x = bars[highlight_idx].get_x() + bars[highlight_idx].get_width() / 2
        y = bars[highlight_idx].get_height()
        ax.text(x, y + 0.3, "Sinner", ha="center", va="bottom", fontsize=11, fontweight="bold")
    else:
        print(f"Note: '{HIGHLIGHT_NAME}' not found in top {TOP_N}. No highlight applied.")

    ax.set_title(f"AO 2024 Monte Carlo — Top {TOP_N} Title Probabilities")
    ax.set_ylabel("Probability of Winning Title (%)")
    ax.set_xlabel("")
    ax.set_ylim(0, max(df["p_pct"].max() * 1.15, 5))

    # Rotate x labels for readability
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    plt.savefig(OUT_PNG, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
