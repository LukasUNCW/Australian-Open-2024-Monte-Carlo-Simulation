from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path("/Users/niclasnilsson/Desktop/AO")

CHAMP = BASE_DIR / "ao2024_champion_probabilities.csv"
ADV = BASE_DIR / "ao2024_advancement_probabilities.csv"

OUT = BASE_DIR / "plot_top8_progression_overlay.png"


def main():
    champ = pd.read_csv(CHAMP)
    adv = pd.read_csv(ADV)

    # Ensure needed columns exist
    if "player_id" not in champ.columns or "p_win" not in champ.columns:
        raise ValueError("Champion probabilities CSV must include columns: player_id, p_win")
    if "player_id" not in adv.columns:
        raise ValueError("Advancement probabilities CSV must include column: player_id")

    rounds = ["R16", "QF", "SF", "F", "W"]
    for r in rounds:
        if r not in adv.columns:
            raise ValueError(f"Advancement probabilities CSV missing column: {r}")

    # Select top 8 by title probability
    top8 = champ.sort_values("p_win", ascending=False).head(8)[["player_id", "p_win"]].copy()

    # Merge to get advancement probabilities + names
    merged = top8.merge(
        adv[["player_id", "player"] + rounds],
        on="player_id",
        how="left"
    )

    # Plot overlay
    plt.figure(figsize=(9, 6))
    for _, row in merged.iterrows():
        label = f"{row['player']} ({row['p_win']:.1%})"
        probs = [row[r] for r in rounds]
        plt.plot(rounds, probs, marker="o", label=label)

    plt.ylim(0, 1)
    plt.ylabel("Probability")
    plt.xlabel("Round Reached")
    plt.title("AO 2024 Monte Carlo Backtest: Top 8 Title Favorites Progression")
    plt.legend(loc="lower left", fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT, dpi=220)
    plt.close()

    print(f"✅ Saved overlay plot to: {OUT}")


if __name__ == "__main__":
    main()
