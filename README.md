# Australian Open 2024 Monte Carlo Simulation

Australian Open 2024 Monte Carlo Simulation (ATP Men’s Singles)
Overview

This project implements a Monte Carlo simulation framework to estimate player advancement and championship probabilities for the 2024 Australian Open men’s singles tournament, using only pre-tournament historical data.

ATP match results from 2021–2023 are used to train a surface-weighted Elo rating model, which serves as a measure of player strength. Elo ratings are frozen prior to the tournament to avoid look-ahead bias. Using the official Round-1 draw, the tournament is simulated 100,000 times, producing probabilistic forecasts for each player’s progression through the draw.

The objective is not to predict a single outcome, but to quantify uncertainty in a knockout tournament and demonstrate a clean, reproducible simulation pipeline.

# Data Sources
- ATP Match Data (2021-2023)<br>
Source: Jeff Sackmann's ATP match dataset<br>
Used to train Elo ratings chronologically<br>
- Australian Open 2024 Draw<br>
Manually transcribed Round-1 draw<br>
Stored as a human-readable CSV and later mapped to 'player_id'<br>

# Methodology
<h3>Elo Rating Model</h3>

- All players initialized at Elo = 1500
- Ratings updated chronologically by match data
- Higher K-factor for best-of-five matches
- Surface weighting with emphasis on hard courts (AO is played on hard court)
- Elo snapshot frozen as of January 1, 2024

<h3>Monte Carlo Simulation</h3>

- Full **128-player bracket**
- Real draw order preserved
- Match outcomes sampled using Elo-based win probabilities
- **100,000 tournament simulations**
- Tracks probability of reaching:
  - Round of 16
  - Quarterfinals
  - Semifinals
  - Final
  - Champion

# Quick Usage (Preprocessed Data)
If you want to reproduce the results without rerunning preprocessing, follow these steps:
1. Download the following files into the same directory:
  - atp_matches_2021_2023_clean.csv
  - AO2024Draw.csv
2. Download fit_elo_and_simulate.py
  - update the BASE_DIR path inside the script if needed.
3. Run the simulation:
  - python or python3 fit_elo_and_simulate.py<br>

This will:
- train Elo ratings on historical ATP data
- simulate the AO 2024 tournament 100,000 times
- output advancement and title probabilites
4. (Optional) Download and run plot.py to generate visualizations:
  - python or python3 plot.py
 
# Example Visual of Top 8 Title Favorites Progression
<img width="1475" height="731" alt="Screenshot 2026-01-20 at 5 02 56 PM" src="https://github.com/user-attachments/assets/a11307d6-f768-4c73-8167-6ad1fad2d6c8" />


# Backtest Against Actual Australian Open 2024

To evaluate the model, the simulated probabilities were compared against the real 2024 Australian Open results.

The eventual champion, Jannik Sinner, was ranked 2nd by the model and assigned a 16.1% title probability prior to the tournament, indicating strong calibration at the top of the field.

Round-level evaluation showed high coverage in earlier rounds (75% of R16 players and 87.5% of quarterfinalists appeared in the model’s top-N predictions). As expected, coverage declined in later rounds due to path dependency and upset propagation inherent in single-elimination tournaments.

The model also identified several high-impact upsets, including multiple wins by Arthur Cazaux and Nuno Borges, which aligned with widely recognized tournament surprises.

Overall, the results demonstrate that a surface-weighted Elo Monte Carlo framework can provide realistic probabilistic forecasts while appropriately reflecting tournament uncertainty.
