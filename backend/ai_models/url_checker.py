import torch
import os
import numpy as np
import torch.nn as nn

# Define the same model architecture as the one used for training
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

def load_model(model_path):
    """Load the trained phishing detection model."""
    # Make sure model path is absolute
    model_path = os.path.abspath(model_path)
    
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return None, None
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Use vocab_size=115 to match the saved model
    model = CNN_Attention_Model(vocab_size=115, emb_dim=64).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model, device

def predict_url_with_confidence(model, device, url):
    """Predict if a URL is phishing or not and return with confidence score."""
    tokens = safe_tokenize(url)
    input_tensor = torch.tensor([tokens], dtype=torch.long).to(device)
    
    with torch.no_grad():
        output = model(input_tensor)
        # Since this is binary classification with sigmoid output (0-1)
        prediction_prob = output.item()
        prediction = 1 if prediction_prob > 0.5 else 0
        
        # Calculate confidence as distance from 0.5 (decision boundary)
        # Rescale to 0-100%
        if prediction == 1:  # Phishing
            confidence = prediction_prob * 100
        else:  # Legitimate
            confidence = (1 - prediction_prob) * 100
    
    return prediction, confidence

def get_url_status_description(prediction):
    """Convert prediction code to human-readable status."""
    if prediction == 1:
        return "PHISHING (Malicious)"
    else:
        return "LEGITIMATE (Safe)"

def print_colored_result(prediction, confidence):
    """Print the result with colors based on prediction."""
    status = get_url_status_description(prediction)
    
    if prediction == 1:  # Phishing
        color_start = "\033[91m"  # Red
        symbol = "❌"
    else:  # Legitimate
        color_start = "\033[92m"  # Green
        symbol = "✓"
    
    color_end = "\033[0m"
    print(f"\n{symbol} URL Status: {color_start}{status}{color_end}")
    print(f"Confidence: {color_start}{confidence:.2f}%{color_end}\n")

def run_interactive_checker():
    """Run an interactive URL checker that allows multiple URLs to be checked."""
    print("\n" + "=" * 60)
    print("       URL PHISHING DETECTOR - CONFIDENCE CHECKER")
    print("=" * 60)
    
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.pt")
    model, device = load_model(model_path)
    
    if model is None:
        print("Error loading model. Please make sure the model file exists.")
        return
    
    print("\nModel loaded successfully! Ready to analyze URLs.")
    print("Enter 'exit' or 'quit' to terminate the program.")
    print("-" * 60)
    
    while True:
        url = input("\nEnter a URL to analyze: ").strip()
        
        if url.lower() in ['exit', 'quit']:
            print("\nExiting URL Phishing Detector. Goodbye!")
            break
        
        if not url:
            print("Please enter a valid URL.")
            continue
        
        print(f"\nAnalyzing: {url}")
        try:
            prediction, confidence = predict_url_with_confidence(model, device, url)
            print_colored_result(prediction, confidence)
        except Exception as e:
            print(f"Error analyzing URL: {e}")

if __name__ == "__main__":
    run_interactive_checker()