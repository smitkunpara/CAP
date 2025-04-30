import csv
import torch
import torch.nn as nn
import json
import os

# Define tokenize function
def tokenize(url, max_len=100, vocab_size=128):
    url = url.lower()
    encoded = [ord(c) for c in url][:max_len]
    # Clip values to be within the range [0, vocab_size-1]
    encoded = [min(c, vocab_size - 1) for c in encoded]
    padded = encoded + [0] * (max_len - len(encoded))
    return padded

# Define the model class
class EnhancedPhishingCNN(nn.Module):
    def __init__(self, vocab_size=128, embed_dim=64, max_len=100, num_classes=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.network = nn.Sequential(
            nn.Conv1d(embed_dim, 128, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv1d(128, 256, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv1d(256, 512, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(1),
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.embedding(x)           # [batch, len, embed]
        x = x.permute(0, 2, 1)          # [batch, embed, len]
        return self.network(x)          # [batch, num_classes]

def read_urls_from_csv(file_path):
    """Read URLs and their expected status from a CSV file."""
    urls = []
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append((row['url'], row['label']))
    return urls

def load_model(model_path):
    """Load the trained phishing detection model."""
    # Make sure model path is absolute
    model_path = os.path.abspath(model_path)
    
    if not os.path.exists(model_path):
        print(f"Model file not found at {model_path}")
        print("Training a new model...")
        # Create a new model since we can't import from urls.py
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = EnhancedPhishingCNN().to(device)
        model_dir = os.path.dirname(model_path)
        os.makedirs(model_dir, exist_ok=True)
        return model, device
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = EnhancedPhishingCNN().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model, device

def predict_url(model, device, url):
    """Predict if a URL is phishing or not."""
    tokens = tokenize(url)
    input_tensor = torch.tensor([tokens], dtype=torch.long).to(device)
    with torch.no_grad():
        output = model(input_tensor)
        prediction = output.argmax(dim=1).item()
    return prediction

def validate_urls_and_generate_report(input_csv, model_path, output_report):
    """Validate URLs using the phishing detection model and generate a report for incorrect predictions."""
    model, device = load_model(model_path)
    urls = read_urls_from_csv(input_csv)

    incorrect_predictions = []
    correct_predictions = 0
    total_predictions = len(urls)

    for index, (url, expected_status) in enumerate(urls, start=1):
        print(f"Processing URL {index}/{total_predictions}: {url}")
        actual_status = predict_url(model, device, url)
        expected_status_int = int(expected_status)
        if actual_status == expected_status_int:
            correct_predictions += 1
        else:
            incorrect_predictions.append({
                'url': url,
                'expected_status': expected_status,
                'actual_status': str(actual_status)
            })

    accuracy = (correct_predictions / total_predictions) * 100
    print(f"Model Accuracy: {accuracy:.2f}%")

    # Write incorrect predictions to the output report file
    with open(output_report, 'w', encoding='utf-8') as report_file:
        json.dump(incorrect_predictions, report_file, indent=4)

print("before if")
# Example usage

if __name__ == "__main__":
    # Use absolute paths
    print("main")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_dir))
    
    input_csv = os.path.join(base_dir, "backend", "data", "urls_new.csv")
    model_path = os.path.join(base_dir, "backend", "ai_models", "urls.pt")
    output_report = os.path.join(base_dir, "report_url.json")
    
    validate_urls_and_generate_report(input_csv, model_path, output_report)