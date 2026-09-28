"""
Regenerates the README figures and backtest table.

    python fit_elo_and_simulate.py   # writes results/
    python make_figures.py           # writes assets/

Compares the pre-tournament simulation against what actually happened
(AO2024Results.csv) and against a seeding-only baseline.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
ADV = BASE_DIR / "results" / "ao2024_advancement_probabilities.csv"
ACTUAL = BASE_DIR / "AO2024Results.csv"
OUT = BASE_DIR / "assets"

ROUNDS = ["R16", "QF", "SF", "F", "W"]
ROUND_LABELS = {"R16": "Round of 16", "QF": "Quarterfinal", "SF": "Semifinal",
                "F": "Final", "W": "Champion"}

plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]

# fixed categorical order, light / dark steps (colorblind-validated palette)
SERIES = {"light": ["#2a78d6", "#eb6834"], "dark": ["#3987e5", "#d95926"]}
# sequential blue ramp, light -> dark
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
THEMES = {
    "light": dict(surface="#ffffff", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  grid="#e1e0d9", axis="#c3c2b7", empty="#f0efec"),
    "dark":  dict(surface="#0d1117", ink="#ffffff", ink2="#c3c2b7", muted="#898781",
                  grid="#2c2c2a", axis="#383835", empty="#1f2328"),
}


# ── data ─────────────────────────────────────────────────────────────────────

def load() -> pd.DataFrame:
    adv = pd.read_csv(ADV)
    actual = pd.read_csv(ACTUAL)[["player_id", "furthest_round"]]
    df = adv.merge(actual, on="player_id", how="left")
    depth = {r: i for i, r in enumerate(ROUNDS)}
    for r in ROUNDS:
        # everyone outside AO2024Results.csv lost before the round of 16
        df[f"actual_{r}"] = df["furthest_round"].map(depth).fillna(-1) >= depth[r]
    df["short"] = df["player"].str.split().str[-1]
    df.loc[df["player"] == "Alex de Minaur", "short"] = "de Minaur"
    return df


def coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    """Top-N hit rate per round: model ranking vs. seeding (unseeded ranked last)."""
    seed_rank = df["seed"].fillna(999)
    rows = []
    for r in ROUNDS:
        actual = set(df.loc[df[f"actual_{r}"], "player_id"])
        n = len(actual)
        model_top = set(df.nlargest(n, r)["player_id"])
        seed_top = set(df.loc[seed_rank.nsmallest(n).index, "player_id"])
        rows.append({
            "Round": ROUND_LABELS[r],
            "N": n,
            "Model hits": len(model_top & actual),
            "Seeding hits": len(seed_top & actual),
            "Model coverage": len(model_top & actual) / n,
            "Seeding coverage": len(seed_top & actual) / n,
        })
    return pd.DataFrame(rows).set_index("Round")


# ── plotting helpers ─────────────────────────────────────────────────────────

def new_fig(t, w=10, h=4.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=160)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(t["axis"])
    ax.tick_params(colors=t["muted"], labelsize=9, length=0, pad=6)
    ax.set_axisbelow(True)
    return fig, ax


def titles(fig, t, title, subtitle):
    fig.text(0.012, 0.965, title, color=t["ink"], fontsize=13, fontweight="bold", va="top")
    fig.text(0.012, 0.905, subtitle, color=t["ink2"], fontsize=9.5, va="top")


def save(fig, name, mode):
    suffix = "" if mode == "light" else "_dark"
    fig.savefig(OUT / f"{name}{suffix}.png", facecolor=fig.get_facecolor())
    plt.close(fig)


# ── figures ──────────────────────────────────────────────────────────────────

def fig_title_odds(df, t, c, mode, top_n=10):
    top = df.nlargest(top_n, "W")[::-1]
    fig, ax = new_fig(t, h=4.4)
    fig.subplots_adjust(left=0.17, right=0.95, top=0.80, bottom=0.08)
    ax.grid(axis="x", color=t["grid"], linewidth=0.8)
    ys = np.arange(len(top))
    colors = [c[1] if champ else c[0] for champ in top["actual_W"]]
    ax.barh(ys, top["W"], height=0.55, color=colors)
    for y, (_, row) in zip(ys, top.iterrows()):
        label = f"{row['W']:.1%}" + ("   ← actual champion" if row["actual_W"] else "")
        ax.text(row["W"] + 0.005, y, label, color=t["ink2"], fontsize=9, va="center")
    seeds = top["seed"].map(lambda s: f"  [{int(s)}]" if pd.notna(s) else "")
    ax.set_yticks(ys, top["player"] + seeds, color=t["ink"], fontsize=10)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlim(0, top["W"].max() * 1.25)
    ax.spines["bottom"].set_visible(False)
    titles(fig, t, "Pre-tournament title odds, AO 2024 men's singles",
           "100,000 simulated brackets from surface-weighted Elo frozen on Jan 1, 2024 · "
           "[n] = seed · Sinner was the model's #2 pick")
    save(fig, "title_odds", mode)


def fig_progression(df, t, c, mode, top_n=12):
    top = df.nlargest(top_n, "W").reset_index(drop=True)
    vals = top[ROUNDS].to_numpy()
    fig, ax = new_fig(t, w=10, h=5.4)
    fig.subplots_adjust(left=0.19, right=0.98, top=0.78, bottom=0.04)
    ax.spines["bottom"].set_visible(False)

    bounds = [0, 0.02, 0.05, 0.10, 0.20, 0.35, 0.55, 1.0001]
    cmap = matplotlib.colors.ListedColormap(RAMP)
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    gap = 0.06
    for i in range(len(top)):
        for j, r in enumerate(ROUNDS):
            v = vals[i, j]
            face = cmap(norm(v))
            ax.add_patch(matplotlib.patches.FancyBboxPatch(
                (j + gap, i + gap), 1 - 2 * gap, 1 - 2 * gap,
                boxstyle="round,pad=0,rounding_size=0.08", linewidth=0, facecolor=face))
            if top.loc[i, f"actual_{r}"]:
                ax.add_patch(matplotlib.patches.FancyBboxPatch(
                    (j + gap + 0.03, i + gap + 0.03), 1 - 2 * gap - 0.06, 1 - 2 * gap - 0.06,
                    boxstyle="round,pad=0,rounding_size=0.06", linewidth=2.2,
                    facecolor="none", edgecolor=c[1]))
            lum = np.dot(matplotlib.colors.to_rgb(face), [0.299, 0.587, 0.114])
            ax.text(j + 0.5, i + 0.5, f"{v:.0%}" if v >= 0.005 else "<1%", ha="center",
                    va="center", fontsize=9.5, color="#0b0b0b" if lum > 0.6 else "#ffffff")
    ax.set_xlim(0, len(ROUNDS))
    ax.set_ylim(len(top), 0)
    ax.set_xticks(np.arange(len(ROUNDS)) + 0.5, [ROUND_LABELS[r] for r in ROUNDS],
                  color=t["ink"], fontsize=10)
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(top)) + 0.5, top["player"], color=t["ink"], fontsize=10)
    ax.plot([], [], marker="s", ls="", ms=10, mfc="none", mec=c[1], mew=2,
            label="Actually reached this round")
    fig.legend(frameon=False, fontsize=9, labelcolor=t["ink2"], loc="upper left",
               bbox_to_anchor=(0.19, 0.918), handletextpad=0.4)
    titles(fig, t, "Probability of reaching each round vs. what happened",
           "Top 12 by title odds.")
    save(fig, "progression", mode)


def fig_r16_surprises(df, t, c, mode):
    r16 = df[df["actual_R16"]].sort_values("R16")
    fig, ax = new_fig(t, h=5.0)
    fig.subplots_adjust(left=0.23, right=0.96, top=0.80, bottom=0.08)
    ax.grid(axis="x", color=t["grid"], linewidth=0.8)
    ys = np.arange(len(r16))
    surprise = r16["R16"] < 0.20
    ax.hlines(ys, 0, r16["R16"], color=t["grid"], lw=2)
    ax.scatter(r16["R16"], ys, s=70, zorder=3, edgecolor=t["surface"], linewidth=2,
               color=[c[1] if s else c[0] for s in surprise])
    for y, (_, row) in zip(ys, r16.iterrows()):
        ax.text(row["R16"] + 0.018, y, f"{row['R16']:.0%}", color=t["ink2"], fontsize=9, va="center")
    seeds = r16["seed"].map(lambda s: f"  [{int(s)}]" if pd.notna(s) else "  unseeded")
    ax.set_yticks(ys, r16["player"] + seeds, color=t["ink"], fontsize=10)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlim(0, 1)
    ax.spines["bottom"].set_visible(False)
    ax.scatter([], [], s=70, color=c[1], label="Under 20%: the model's upsets")
    ax.scatter([], [], s=70, color=c[0], label="20% or higher")
    ax.legend(frameon=False, fontsize=9, labelcolor=t["ink2"], loc="lower left",
              ncol=2, bbox_to_anchor=(-0.02, 1.0), handletextpad=0.2)
    titles(fig, t, "The actual round of 16, through the model's eyes",
           "Pre-tournament probability each of the 16 real fourth-rounders would get there")
    save(fig, "r16_surprises", mode)


def fig_coverage(cov, t, c, mode):
    fig, ax = new_fig(t, h=4.0)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.76, bottom=0.12)
    ax.grid(axis="y", color=t["grid"], linewidth=0.8)
    x = np.arange(len(cov))
    w = 0.2
    for k, (col, lab) in enumerate([("Model", "Elo Monte Carlo"), ("Seeding", "Seeding baseline")]):
        xs = x + (k - 0.5) * (w + 0.02)
        ax.bar(xs, cov[f"{col} coverage"], width=w, color=c[k], label=lab)
        for xi, (hits, n) in zip(xs, zip(cov[f"{col} hits"], cov["N"])):
            ax.text(xi, cov.iloc[list(xs).index(xi)][f"{col} coverage"] + 0.02, f"{hits}/{n}",
                    ha="center", color=t["ink2"], fontsize=9)
    ax.set_xticks(x, [f"{r}\n(top {n})" for r, n in zip(cov.index, cov["N"])], color=t["ink"], fontsize=9.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_ylim(0, 1.1)
    ax.legend(frameon=False, fontsize=9, labelcolor=t["ink2"], loc="lower left",
              ncol=2, bbox_to_anchor=(-0.01, 1.0))
    titles(fig, t, "How many of the real survivors did each ranking pick?",
           "Top-N coverage: of the N players ranked most likely to reach a round, how many actually did")
    save(fig, "coverage", mode)


def main():
    OUT.mkdir(exist_ok=True)
    df = load()
    cov = coverage_table(df)
    cov.to_csv(OUT / "coverage.csv", float_format="%.4f")
    print(cov.to_string(float_format=lambda f: f"{f:.1%}"))
    for mode in ("light", "dark"):
        t, c = THEMES[mode], SERIES[mode]
        fig_title_odds(df, t, c, mode)
        fig_progression(df, t, c, mode)
        fig_r16_surprises(df, t, c, mode)
        fig_coverage(cov, t, c, mode)


if __name__ == "__main__":
    main()
