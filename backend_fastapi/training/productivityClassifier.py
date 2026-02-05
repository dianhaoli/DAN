"""
Productivity Classifier Training Script

Trains a two-stage ML pipeline:
1. DistilBERT: Text classification (study/distraction/research)
2. XGBoost: Productivity score prediction (0-100)

Output: ../ml_models/distilbert-model/ and ../ml_models/xgboost_productivity.json
"""

import numpy as np
import pandas as pd
import os
from pathlib import Path
from datasets import load_dataset
from sklearn.preprocessing import LabelEncoder
from transformers import (
    DistilBertTokenizerFast, 
    DistilBertForSequenceClassification, 
    TrainingArguments, 
    Trainer, 
    pipeline
)
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
import torch

# Paths
SCRIPT_DIR = Path(__file__).parent
ML_MODELS_DIR = SCRIPT_DIR.parent / "ml_models"
DISTILBERT_OUTPUT = ML_MODELS_DIR / "distilbert-model"
XGBOOST_OUTPUT = ML_MODELS_DIR / "xgboost_productivity.json"

# Ensure output directory exists
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ===== GENERATE SAMPLE DATA IF FILES DON'T EXIST =====
if not os.path.exists("browser_activity.csv"):
    print("📝 Creating sample browser_activity.csv...")
    browser_data = {
        'text': [
            'Introduction to Machine Learning | Coursera',
            'Python Documentation - Built-in Functions',
            'How to implement quicksort - Stack Overflow',
            'GitHub - awesome-project: Repository',
            'Watch: Funny Cat Videos - YouTube',
            'Reddit: r/programming - Latest discussions',
            'Netflix - Stranger Things Season 4',
            'Khan Academy - Calculus: Derivatives',
            'LeetCode - Two Sum Problem Solution',
            'MDN Web Docs - JavaScript Array Methods',
            'Research Paper: Deep Learning - arXiv',
            'Instagram - Explore Feed',
            'Google Scholar - Machine Learning Papers',
            'Notion - Study Notes Template',
            'TikTok - Trending Videos',
            'Coursera - Data Science Specialization',
            'Udemy - Complete Python Bootcamp',
            'edX - MIT Introduction to Algorithms',
            'Codecademy - Learn JavaScript',
            'FreeCodeCamp - Web Development',
            'HackerRank - Problem Solving',
            'Developer Mozilla - Web APIs',
            'Python.org - Tutorial',
            'Overleaf - LaTeX Editor',
            'JSTOR - Academic Articles',
            'ResearchGate - Scientific Papers',
            'Evernote - Note Taking',
            'OneNote - Digital Notebook',
            'Roam Research - Knowledge Graph',
            'Obsidian - Markdown Notes',
        ] * 10,  # Repeat to get more training data (300 samples)
        'label': [
            'study', 'study', 'study', 'study', 'distraction',
            'distraction', 'distraction', 'study', 'study', 'study',
            'research', 'distraction', 'research', 'study', 'distraction',
            'study', 'study', 'study', 'study', 'study',
            'study', 'study', 'study', 'study', 'research',
            'research', 'study', 'study', 'study', 'study',
        ] * 10
    }
    pd.DataFrame(browser_data).to_csv('browser_activity.csv', index=False)
    print("✅ Created browser_activity.csv with 300 samples")

if not os.path.exists("behavioral_data.csv"):
    print("📝 Creating sample behavioral_data.csv...")
    np.random.seed(42)
    n_samples = 500
    
    titles = [
        'Machine Learning Course - Week 3',
        'Python Documentation',
        'Stack Overflow - Error Solution',
        'GitHub Repository',
        'YouTube Video',
        'Reddit Thread',
        'Research Paper Abstract',
        'Notion Study Notes',
        'LeetCode Problem',
        'MDN Web Docs',
        'Coursera Lecture Video',
        'Khan Academy Tutorial',
        'Netflix Show',
        'Instagram Feed',
        'TikTok Video',
    ]
    
    behavioral_data = {
        'title': np.random.choice(titles, n_samples),
        'clicks': np.random.randint(5, 200, n_samples),
        'keystrokes': np.random.randint(10, 1000, n_samples),
        'time_on_page': np.random.uniform(30, 3600, n_samples),
        'productivity_score': np.random.uniform(20, 95, n_samples)
    }
    pd.DataFrame(behavioral_data).to_csv('behavioral_data.csv', index=False)
    print("✅ Created behavioral_data.csv with 500 samples")

# ===== STAGE 1: TEXT CLASSIFICATION =====
print("\n📚 Stage 1: Training Text Classifier (DistilBERT)...")
text_data = load_dataset("csv", data_files="browser_activity.csv")["train"]

le = LabelEncoder()
le.fit(text_data["label"])

id2label = {i: label for i, label in enumerate(le.classes_)}
label2id = {label: i for i, label in enumerate(le.classes_)}

text_data = text_data.map(lambda x: {"labels": le.transform([x["label"]])[0]})

tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)

text_data = text_data.map(tokenize_function, batched=True) 
text_data.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

split = text_data.train_test_split(test_size=0.2)
train_dataset = split["train"]
test_dataset = split["test"]

model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=len(le.classes_),
    id2label=id2label, 
    label2id=label2id
)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {"accuracy": accuracy_score(labels, predictions)}

args = TrainingArguments(
    output_dir=str(DISTILBERT_OUTPUT),
    eval_strategy="epoch", 
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=2,
    weight_decay=0.01,
    load_best_model_at_end=True
)

trainer = Trainer(
    model=model, 
    args=args, 
    train_dataset=train_dataset, 
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)

print("Training DistilBERT model...")
trainer.train()
trainer.save_model(str(DISTILBERT_OUTPUT))
tokenizer.save_pretrained(str(DISTILBERT_OUTPUT))
print(f"✅ Text classifier trained and saved to {DISTILBERT_OUTPUT}")

# ===== STAGE 2: PRODUCTIVITY SCORE PREDICTION =====
print("\n🎯 Stage 2: Training Productivity Score Predictor (XGBoost)...")

device = 0 if torch.cuda.is_available() else -1

clf = pipeline(
    "text-classification", 
    model=str(DISTILBERT_OUTPUT), 
    tokenizer=str(DISTILBERT_OUTPUT), 
    device=device,
    truncation=True 
)

df = pd.read_csv("behavioral_data.csv")

print("Running inference on behavioral data...")
batch_results = clf(df["title"].tolist(), batch_size=32)

df["activity_label"] = [res["label"] for res in batch_results]
df["activity_confidence"] = [res["score"] for res in batch_results]

df["activity_label_encoded"] = le.transform(df["activity_label"])

X = df[["clicks", "keystrokes", "time_on_page", "activity_label_encoded"]]
y = df["productivity_score"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

xgb_model = xgb.XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.85,
    colsample_bytree=0.85,
    random_state=42
)

print("Training XGBoost model...")
xgb_model.fit(X_train, y_train)
y_pred = xgb_model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"\n📊 Model Performance:")
print(f"RMSE: {rmse:.4f}")
print(f"R² Score: {r2:.4f}")

xgb_model.save_model(str(XGBOOST_OUTPUT))
print(f"✅ Productivity predictor trained and saved to {XGBOOST_OUTPUT}")
print("\n🎉 Training complete! Models saved:")
print(f"  - {DISTILBERT_OUTPUT} (text classifier)")
print(f"  - {XGBOOST_OUTPUT} (productivity predictor)")