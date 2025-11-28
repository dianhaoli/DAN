import numpy as np
import pandas as pd
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
    output_dir="distilbert-model",
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

trainer.train()
trainer.save_model("distilbert-model")
tokenizer.save_pretrained("distilbert-model")


device = 0 if torch.cuda.is_available() else -1

clf = pipeline(
    "text-classification", 
    model="distilbert-model", 
    tokenizer="distilbert-model", 
    device=device,
    truncation=True 
)

df = pd.read_csv("behavioral_data.csv")

print("Running inference...")

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

xgb_model.fit(X_train, y_train)
y_pred = xgb_model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"RMSE: {rmse}")
print(f"R2 Score: {r2}")

xgb_model.save_model("xgboost_productivity.json")
