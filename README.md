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
- Surface weightign with emphasis on hard courts (AO is played on hard court)
- Elo snapshot frozen as of January 1, 2024

<h3>Monte Carlo Simulation</h3>

- Full **128p-player bracket**
- Real draw order preserved
- Match outcomes sampled using Elo-based win probabilities
- **100,000 tournament simulations**
- Tracks probability of reaching:
  - Round of 16
  - Quarterfinals
  - Semifinals
  - Final
  - Champion

# Project Structure
<img width="329" height="509" alt="Screenshot 2026-01-20 at 3 19 04 PM" src="https://github.com/user-attachments/assets/ccb239c2-0576-4f83-8f99-d700de58b456" />

# How to Run

1. Download the atp_matches_2021_2023_clean.csv
2. Download the AO2024Draw.csv
3. (Optional) Download the atp_players.csv
4. Make sure all downloaded files are in the same directory, if not, script will not work
5. Download/Copy the fit_elo_and_simulate.py script and change the directory accordingly
6. Running the script will provide you with three files, those will be found in the current working directory

