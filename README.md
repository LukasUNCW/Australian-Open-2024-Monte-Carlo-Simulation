# Australian-Open-2024-Monte-Carlo-Simulation

Australian Open 2024 Monte Carlo Simulation (ATP Men’s Singles)
Overview

This project implements a Monte Carlo simulation framework to estimate player advancement and championship probabilities for the 2024 Australian Open men’s singles tournament, using only pre-tournament historical data.

ATP match results from 2021–2023 are used to train a surface-weighted Elo rating model, which serves as a measure of player strength. Elo ratings are frozen prior to the tournament to avoid look-ahead bias. Using the official Round-1 draw, the tournament is simulated 100,000 times, producing probabilistic forecasts for each player’s progression through the draw.

The objective is not to predict a single outcome, but to quantify uncertainty in a knockout tournament and demonstrate a clean, reproducible simulation pipeline.

# Data Sources
ATP Match Data (2021-2023)
Source: Jeff Sackmann's ATP match dataset
Used to train Elo ratings chronologically
Australian Open 2024 Draw
Manually transcribed Round-1 draw
Stored as a human-readable CSV and later mapped to 'player_id'

# Methodology
Elo Rating Model
