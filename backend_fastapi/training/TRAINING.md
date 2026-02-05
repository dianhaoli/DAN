# ML Model Training Guide

This directory contains scripts for training the productivity classification models used by the DAN backend.

## Models

### 1. DistilBERT Text Classifier
- **Purpose**: Classifies browser activity text (page titles) into categories
- **Labels**: `study`, `distraction`, `research`
- **Output**: `../ml_models/distilbert-model/`

### 2. XGBoost Productivity Predictor
- **Purpose**: Predicts productivity scores (0-100) based on behavioral features
- **Features**: clicks, keystrokes, time_on_page, activity_label_encoded
- **Output**: `../ml_models/xgboost_productivity.json`

## Setup

### Install Dependencies

```bash
cd backend_fastapi/training
pip install -r requirements.txt
```

## Running Training

```bash
python productivityClassifier.py
```

### What It Does

**Stage 1: Text Classification**
- Generates or loads `browser_activity.csv` (300 samples)
- Fine-tunes DistilBERT for activity classification
- Saves model to `../ml_models/distilbert-model/`

**Stage 2: Productivity Prediction**
- Generates or loads `behavioral_data.csv` (500 samples)  
- Uses trained classifier to label behavioral data
- Trains XGBoost regressor for productivity prediction
- Saves model to `../ml_models/xgboost_productivity.json`

## Training Data Format

### browser_activity.csv
```csv
text,label
"Introduction to Machine Learning | Coursera",study
"Watch: Funny Cat Videos - YouTube",distraction
"Research Paper: Deep Learning - arXiv",research
```

### behavioral_data.csv
```csv
title,clicks,keystrokes,time_on_page,productivity_score
"Machine Learning Course - Week 3",85,450,1200,78.5
```

## Output

The script will:
1. Generate sample CSV files if they don't exist
2. Download DistilBERT model (~250MB) on first run
3. Train both models (5-10 minutes depending on hardware)
4. Print performance metrics (RMSE, R² Score)
5. Save trained models to `../ml_models/`

## Model Performance

Expected metrics with sample data:
- **DistilBERT Accuracy**: ~95% (on small sample set)
- **XGBoost RMSE**: ~15-20 points
- **XGBoost R²**: ~0.3-0.5 (on random data)

> Note: Real production data will yield different results.

## Retraining

To retrain with new data:
1. Replace CSV files with production data
2. Run `python productivityClassifier.py`
3. Models will be overwritten in `../ml_models/`
4. Restart the FastAPI server to load new models

## Notes

- First run downloads DistilBERT from Hugging Face (~250MB)
- Training uses GPU if available, falls back to CPU
- Sample data is randomly generated - use real data for production
- The label encoder expects exactly 3 classes: `study`, `distraction`, `research`
