# Human VS Bot Typer

Will you be able to tell the difference between a human typer and a bot typer? Well check if you can using this project!

## Quick start
 
```bash
pip install flask itsdangerous scikit-learn joblib numpy
python main.py
# open http://localhost:5000
```

## Features
 
- Replays a typing session keystroke-by-keystroke, including WPM, errors, and progress
- Simulates realistic human typists (steady, bursty, careful profiles) and three bot types (fixed, jitter, fake-human)
- ML + rule-based classifier predicts human vs. automated features.
- Shows per-round feedback: model confidence, key signals, pause count, autocorrelation

## How it works
 
Each round generates a typing session from one of ten fixed snippets, randomly assigned as human or bot. The frontend replays events with their original inter-keystroke intervals. After you guess, the session is scored.

## Local model training
 
```bash
python build_model.py
# saves models/bundle.joblib
```