# Australian Open 2024 — Monte Carlo Simulation

A Python based project that simulates the 2024 Australian Open men's singles tournament using a surface-weighted Elo rating model and Monte Carlo methods to estimate player advancement and championship probabilities.

This project mirrors how probabilistic forecasting is done in sports analytics, emphasizing:
- Statistical rigor
- No look-ahead bias (Elo frozen pre-tournament)
- Reproducibility
- Clean, modular simulation design

---

## Table of Contents
- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Methodology](#methodology)
- [Prerequisites & Installation](#prerequisites--installation)
- [How to Run](#how-to-run)
- [Results & Visualizations](#results--visualizations)
- [Backtest Against Actual Results](#backtest-against-actual-results)
- [Data Sources](#data-sources)

---

## Overview

ATP match results from 2021–2023 are used to train a surface-weighted Elo rating model, which serves as a measure of player strength. Elo ratings are frozen prior to the tournament to avoid look-ahead bias. Using the official Round 1 draw, the tournament is simulated **100,000 times**, producing probabilistic forecasts for each player's progression through the bracket.

The objective is not to predict a single outcome, but to **quantify uncertainty** in a knockout tournament and demonstrate a clean, reproducible simulation pipeline.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.x | Core language |
| pandas | Data loading and preprocessing |
| NumPy | Probability sampling and simulation |
| Matplotlib | Visualization |

---

## Project Structure

```
AO2024-Monte-Carlo/
│
├── fit_elo_and_simulate.py           # Trains Elo ratings and runs the simulation
├── plot3.py                          # Generates result visualizations
│
├── atp_matches_2021_2023_clean.csv   # Cleaned ATP match data (2021–2023)
├── atp_players.csv                   # List of all current ATP players with IDs
└── AO2024Draw.csv                    # Official AO 2024 Round 1 draw with player IDs
```

---

## Methodology

### Elo Rating Model

Based on [Arpad Elo's rating system](https://en.wikipedia.org/wiki/Elo_rating_system), adapted for professional tennis.

- All players initialized at **Elo = 1500**
- Ratings updated **chronologically** using historical match data
- **Higher K-factor** applied to best-of-five matches (Grand Slam format)
- **Surface weighting** with emphasis on hard courts (the AO is played on hard court)
- Elo snapshot **frozen as of January 1, 2024** to prevent look-ahead bias

### Monte Carlo Simulation

- Full **128-player bracket** with real draw order preserved
- Match outcomes sampled using **Elo-based win probabilities**
- **100,000 tournament simulations** run in total
- Tracks each player's probability of reaching:
  - Round of 16
  - Quarterfinals
  - Semifinals
  - Final
  - Champion

---

## Prerequisites & Installation

**1. Clone the repository**
```bash
git clone https://github.com/LukasUNCW/AO2024-Monte-Carlo.git
cd AO2024-Monte-Carlo
```

**2. Install dependencies**
```bash
pip install pandas numpy matplotlib
```

---

## How to Run

### Run the Simulation

Trains Elo ratings on historical ATP data and simulates the AO 2024 tournament 100,000 times. Outputs advancement and title probabilities to the console.

```bash
python fit_elo_and_simulate.py
```

> **Note:** Update the `BASE_DIR` path inside `fit_elo_and_simulate.py` if your data files are in a different directory.

### Generate Visualizations

```bash
python plot3.py
```

### Quick Start (Preprocessed Data)

If you want to reproduce results without rerunning preprocessing:

1. Download these files into the same directory:
   - `atp_matches_2021_2023_clean.csv`
   - `AO2024Draw.csv`
2. Download `fit_elo_and_simulate.py` and update `BASE_DIR` if needed
3. Run the simulation, then optionally run `plot3.py` for visualizations

---

## Results & Visualizations

### Top 8 Title Win Probabilities

Includes the actual tournament winner for reference.

<img width="1476" height="733" alt="Top 8 Title Win Probabilities" src="https://github.com/user-attachments/assets/931caa41-f23c-4c40-8bb5-1840ee2605dc" />

### Top 8 Progression Probabilities

Shows the probability of each top player advancing through each round of the draw.

<img width="1980" height="1320" alt="Top 8 AO Progression Probabilities" src="https://github.com/user-attachments/assets/4b537831-071d-4ee6-9565-9bf32791584f" />

---

## Backtest Against Actual Results

To evaluate the model, simulated probabilities were compared against the real 2024 Australian Open results.

**Champion calibration:** The eventual champion, Jannik Sinner, was ranked **2nd** by the model with a **16.1% title probability** prior to the tournament — indicating strong calibration at the top of the field.

**Round-level coverage:**

| Round | Top-N Coverage |
|---|---|
| Round of 16 | 75% of actual players appeared in model's top-N |
| Quarterfinals | 87.5% coverage |
| Semifinals & beyond | Declined due to path dependency and upset propagation |

Coverage declining in later rounds is expected behavior in single-elimination tournaments, where small early upsets compound through the bracket.

**Upset detection:** The model identified several high-impact upsets, including multiple wins by Arthur Cazaux and Nuno Borges, which aligned with widely recognized tournament surprises.

Overall, the results demonstrate that a surface-weighted Elo Monte Carlo framework can provide **realistic probabilistic forecasts** while appropriately reflecting tournament uncertainty.

---

## Data Sources

| Dataset | Source |
|---|---|
| ATP Match Data (2021–2023) | [Jeff Sackmann's ATP match dataset](https://github.com/JeffSackmann/tennis_atp) — used to train Elo ratings chronologically |
| AO 2024 Draw | Manually transcribed Round 1 draw, stored as CSV and mapped to `player_id` |
