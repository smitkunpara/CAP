import torch
import os
from urls_test import tokenize
import torch.nn as nn

# Define the same model architecture as in urls.py
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

def load_model(model_path):
    """Load the trained phishing detection model."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Use vocab_size=115 to match the saved model
    model = CNN_Attention_Model(vocab_size=115, emb_dim=64).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model, device

# Custom tokenize function that explicitly uses vocab_size=115
def safe_tokenize(url, max_len=100):
    """Tokenize URL ensuring all values are within the model's vocabulary size."""
    url = url.lower()
    vocab_size = 115  # Match the model's vocabulary size
    encoded = [ord(c) for c in url][:max_len]
    # Clip values to be within the range [0, vocab_size-1]
    encoded = [min(c, vocab_size - 1) for c in encoded]
    padded = encoded + [0] * (max_len - len(encoded))
    return padded

def predict_single_url(url, model_path):
    """Predict if a single URL is phishing or not."""
    # Load the model
    model, device = load_model(model_path)

    # Use our safe_tokenize function instead of the imported one
    tokens = safe_tokenize(url)
    input_tensor = torch.tensor([tokens], dtype=torch.long).to(device)

    # Make prediction
    with torch.no_grad():
        output = model(input_tensor)
        # Since this is a binary classification with sigmoid output
        prediction = 1 if output.item() > 0.5 else 0

    return prediction

if __name__ == "__main__":
    # Example usage
    model_path = r"backend\ai_models\urls1.pt"
    url = input("Enter a URL to predict: ")
    prediction = predict_single_url(url, model_path)
    print(f"The URL is {'phishing' if prediction == 1 else 'legitimate'}.")