import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from tqdm import tqdm

# --- 1. URL Tokenization ---
from collections import defaultdict

class URLTokenizer:
    def __init__(self):
        # Replace the lambda with a regular dictionary and handle unknown chars in encode
        self.char2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2char = {0: '<PAD>', 1: '<UNK>'}
        self.fitted = False

    def fit(self, urls):
        idx = 2
        for url in urls:
            for c in url:
                if c not in self.char2idx:
                    self.char2idx[c] = idx
                    self.idx2char[idx] = c
                    idx += 1
        self.fitted = True

    def encode(self, url, maxlen):
        # Get char index or 1 (UNK) if char not in vocabulary
        tokens = [self.char2idx.get(c, 1) for c in url]
        if len(tokens) < maxlen:
            tokens += [0] * (maxlen - len(tokens))
        else:
            tokens = tokens[:maxlen]
        return tokens

# --- 2. Custom Dataset ---
class URLDataset(Dataset):
    def __init__(self, csv_path, tokenizer, maxlen):
        self.data = pd.read_csv(csv_path)
        self.urls = self.data['url'].astype(str).tolist()
        self.labels = self.data['label'].astype(int).tolist()
        self.tokenizer = tokenizer
        self.maxlen = maxlen

    def __len__(self):
        return len(self.urls)

    def __getitem__(self, idx):
        url = self.urls[idx]
        label = self.labels[idx]
        url_tensor = torch.tensor(self.tokenizer.encode(url, self.maxlen), dtype=torch.long)
        return url_tensor, torch.tensor(label, dtype=torch.float32)

# --- 3. Model: CNN + Self-Attention ---
class CNN_Attention_Model(nn.Module):
    def __init__(self, vocab_size, emb_dim=64, maxlen=200):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.conv1 = nn.Conv1d(emb_dim, 128, kernel_size=5, padding=2)
        self.relu = nn.ReLU()
        self.attention = nn.MultiheadAttention(128, num_heads=4, batch_first=True)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc = nn.Linear(128, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.embedding(x)               # (batch, seq, emb_dim)
        x = x.permute(0, 2, 1)              # (batch, emb_dim, seq)
        x = self.conv1(x)                   # (batch, 128, seq)
        x = self.relu(x)
        x = x.permute(0, 2, 1)              # (batch, seq, 128)
        attn_output, _ = self.attention(x, x, x)
        x = attn_output.permute(0, 2, 1)    # (batch, 128, seq)
        x = self.pool(x).squeeze(-1)        # (batch, 128)
        x = self.fc(x)
        return self.sigmoid(x).squeeze(-1)

# --- 4. Training Utilities ---
def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for X, y in tqdm(loader, desc="Training", leave=False):
        X, y = X.to(device), y.to(device)
        optimizer.zero_grad()
        y_pred = model(X)
        loss = criterion(y_pred, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * X.size(0)
    return total_loss / len(loader.dataset)

def eval_epoch(model, loader, device):
    model.eval()
    preds, targets = [], []
    with torch.no_grad():
        for X, y in tqdm(loader, desc="Evaluating", leave=False):
            X = X.to(device)
            y_pred = model(X).cpu().numpy()
            preds.extend((y_pred > 0.5).astype(int))
            targets.extend(y.numpy().astype(int))
    return accuracy_score(targets, preds)

# --- 5. Main Training Script ---
def main():
    csv_path = r'backend\data\urls_new.csv'
    model_path = r'backend\ai_models\urls.pt'
    maxlen = 200  # Truncate/pad URLs to 200 chars

    # Step 1: Tokenizer fit
    print("Fitting tokenizer...")
    sample_df = pd.read_csv(csv_path, nrows=100000)  # Sample for tokenizer
    tokenizer = URLTokenizer()
    tokenizer.fit(sample_df['url'].astype(str).tolist())

    # Step 2: Dataset and DataLoader
    print("Preparing datasets...")
    full_df = pd.read_csv(csv_path)
    train_df, val_df = train_test_split(full_df, test_size=0.05, stratify=full_df['label'], random_state=42)
    train_df.to_csv('train_temp.csv', index=False)
    val_df.to_csv('val_temp.csv', index=False)
    train_dataset = URLDataset('train_temp.csv', tokenizer, maxlen)
    val_dataset = URLDataset('val_temp.csv', tokenizer, maxlen)
    train_loader = DataLoader(train_dataset, batch_size=2048, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=2048, shuffle=False, num_workers=2, pin_memory=True)

    # Step 3: Model, Optimizer, Loss
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = CNN_Attention_Model(vocab_size=len(tokenizer.char2idx), emb_dim=64, maxlen=maxlen).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    criterion = nn.BCELoss()

    # Step 4: Training Loop
    best_acc = 0
    for epoch in range(1, 21):
        print(f"Epoch {epoch}/20")
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_acc = eval_epoch(model, val_loader, device)
        print(f"Train loss: {train_loss:.4f} | Val accuracy: {val_acc:.4f}")
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), model_path)
            print(f"Saved best model with accuracy {val_acc:.4f}")

    print("Training complete. Best validation accuracy:", best_acc)
    os.remove('train_temp.csv')
    os.remove('val_temp.csv')

if __name__ == "__main__":
    main()
