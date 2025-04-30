import torch
import os
from urls_test import EnhancedPhishingCNN, tokenize, load_model

def predict_single_url(url, model_path):
    """Predict if a single URL is phishing or not."""
    # Load the model
    model, device = load_model(model_path)

    # Tokenize the input URL
    tokens = tokenize(url)
    input_tensor = torch.tensor([tokens], dtype=torch.long).to(device)

    # Make prediction
    with torch.no_grad():
        output = model(input_tensor)
        prediction = output.argmax(dim=1).item()

    return prediction

if __name__ == "__main__":
    # Example usage
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.pt")
    url = input("Enter a URL to predict: ")
    prediction = predict_single_url(url, model_path)
    print(f"The URL is {'phishing' if prediction == 1 else 'legitimate'}.")