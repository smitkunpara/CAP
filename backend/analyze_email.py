from models import EmailData
import re
from urllib.parse import urlparse
import torch
import torch.nn as nn
import tldextract
import sys
import os


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

# Define device for model inference
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load the model at server startup
try:
    model_path = r"D:\CAP\backend\ai_models\urls.pt"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Adjusted vocab_size to match the saved model
    url_model = EnhancedPhishingCNN(vocab_size=115).to(device)

    # Load the state dictionary with strict=False to ignore mismatched keys
    url_model.load_state_dict(torch.load(model_path, map_location=device), strict=False)
    url_model.eval()
    print(f"URL phishing model loaded successfully from {model_path}")
except Exception as e:
    print(f"Error loading URL phishing model: {e}")
    url_model = None

def clean_url(url):
    url = url.replace("http://", "").replace("https://", "").replace("www.", "")
    return url

def analyze_attachments(attachments: list[str]):
    # check that it contains any suspicious file types
    suspicious_files={}
    suspicious_file_types = ['.exe', '.scr', '.zip', '.rar', '.js', '.vbs']
    for attachment in attachments:
        if any(attachment.endswith(ext) for ext in suspicious_file_types):
            suspicious_files[attachment] = True
        else:
            suspicious_files[attachment] = False
    return suspicious_files
    
def analyze_sender(sender: str):
    # Basic sender analysis
    analysis = {
        "address": sender,
        "suspicious": False
    }
    
    # Check for common red flags in sender addresses
    if sender:
        # Check for mismatch between display name and email address
        if "<" in sender and ">" in sender:
            display_name = sender.split("<")[0].strip().lower()
            email_address = sender.split("<")[1].split(">")[0].lower()
            
            # Check if display name contains a known organization but email doesn't match
            common_orgs = ["paypal", "amazon", "microsoft", "apple", "google", "bank", "netflix"]
            for org in common_orgs:
                if org in display_name and org not in email_address:
                    analysis["suspicious"] = True
                    analysis["reason"] = f"Display name contains '{org}' but email domain doesn't match"
                    break
    
    return analysis

def analyze_subject(subject: str):
    # Basic subject line analysis
    suspicious_keywords = [
        "urgent", "action required", "account suspended", "verify", "confirm",
        "update your information", "password", "login", "suspicious activity",
        "won", "prize", "lottery", "free", "money", "click"
    ]
    
    analysis = {
        "subject": subject,
        "suspicious": False,
        "urgency_indicators": False,
        "reward_indicators": False
    }
    
    if subject:
        subject_lower = subject.lower()
        
        # Check for urgency indicators
        urgency_words = ["urgent", "immediately", "action required", "suspended", "limited", "locked"]
        if any(word in subject_lower for word in urgency_words):
            analysis["urgency_indicators"] = True
        
        # Check for reward indicators
        reward_words = ["free", "won", "winner", "prize", "gift", "reward"]
        if any(word in subject_lower for word in reward_words):
            analysis["reward_indicators"] = True
            
        # Overall suspicious check
        if any(keyword in subject_lower for keyword in suspicious_keywords):
            analysis["suspicious"] = True
    
    return analysis

def analyze_body_content(body: str):
    if not body:
        return {"available": False}
    
    analysis = {
        "available": True,
        "length": len(body),
        "contains_html": "<html" in body.lower(),
        "suspicious_patterns": []
    }
    
    # Check for suspicious patterns in the body
    patterns = {
        "urgency": r'\b(urgent|immediate|quickly|expires|limited time|act now)\b',
        "credential_request": r'\b(password|login|credential|verify account|confirm identity)\b',
        "threatening": r'\b(suspend|disable|terminate|restrict|limit access)\b',
        "poor_grammar": r'\b(kindly|please\s+(?:to|for)\s+(?:do|make))\b',
        "excessive_caps": r'[A-Z]{4,}',
        "misspelled_domain": r'paypa[l1]\.com|amaz[o0]n\.com|g[o0][o0]gle\.com|faceb[o0][o0]k\.com'
    }
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            analysis["suspicious_patterns"].append({
                "type": pattern_name,
                "matches": matches[:5]  # Limit to first 5 matches
            })
    
    return analysis

def tokenize(url, max_len=100, vocab_size=115):
    """Tokenize a URL string into a sequence of character indices.
    
    Args:
        url (str): The URL to tokenize
        max_len (int): Maximum length of the token sequence
        vocab_size (int): Size of the vocabulary (max index + 1)
    
    Returns:
        list: A list of character indices padded to max_len
    """
    url = url.lower()
    # Convert characters to indices and clip to vocab_size-1
    encoded = [min(ord(c) % vocab_size, vocab_size - 1) for c in url][:max_len]
    # Pad sequence to max_len
    padded = encoded + [0] * (max_len - len(encoded))
    return padded

def extract_links(body: str):
    # Regular expression to match both plain URLs and URLs within HTML tags
    # This pattern will find:
    # 1. URLs within href attributes
    # 2. Plain http/https URLs
    
    # First extract URLs from href attributes
    href_links = re.findall(r'href=["\']((?:https?|htpps?)://[^\s"\'<>]+)["\']', body)
    
    # Then extract plain URLs
    plain_links = re.findall(r'(?<!href=["\'])((?:https?|htpps?)://[^\s"\'<>]+)', body)
    
    # Clean links that might have HTML tags or closing quotes
    all_links = href_links + plain_links
    cleaned_links = []
    
    for link in all_links:
        # Remove any trailing HTML tags or quotes
        link = re.sub(r'["\']>.*$|[<>"].*$', '', link)
        # Remove trailing punctuation that might be part of the text but not the URL
        link = re.sub(r'[.,;:!?)]$', '', link)
        cleaned_links.append(link)
    
    return cleaned_links

def analyze_links(body: str):
    links = extract_links(body)
    analyzed_links = []
    
    if not url_model:
        return [{"url": link, "phishing": False, "error": "Model not loaded"} for link in links]
    
    for link in links:
        link_analysis = {"url": link, "phishing": False, "error": None}
        try:
            # Clean the URL before prediction (remove http/https/www)
            cleaned_url = clean_url(link)
            
            # Process URL for model input
            tokens = tokenize(cleaned_url)
            url_tensor = torch.tensor([tokens], dtype=torch.long).to(device)
            
            # Make prediction
            with torch.no_grad():
                output = url_model(url_tensor)
                # Get the probability for the phishing class (index 1)
                probabilities = torch.softmax(output, dim=1)
                phishing_probability = probabilities[0, 1].item()
                
            # Check if the prediction indicates phishing (threshold 0.5)
            link_analysis["phishing"] = phishing_probability > 0.5
            link_analysis["probability"] = phishing_probability
            link_analysis["cleaned_url"] = cleaned_url
            
        except Exception as e:
            link_analysis["error"] = str(e)
            print(f"Error analyzing link {link}: {e}")
            
        analyzed_links.append(link_analysis)
    return analyzed_links

def analyze_email(email: EmailData):
    report = {}
    report["attachments"] = analyze_attachments(email["attachments"])
    report["links"] = analyze_links(email["body"])
    report["sender"] = analyze_sender(email["sender"])
    report["subject"] = analyze_subject(email["subject"])
    report["body"] = analyze_body_content(email["body"])
    report["original_body"] = email["body"]
    
    # Overall risk assessment
    risk_level = "low"
    if report["attachments"] and any(report["attachments"].values()):
        risk_level = "high"
    elif report["body"].get("suspicious_patterns", []) and len(report["body"]["suspicious_patterns"]) > 2:
        risk_level = "high"
    elif report["subject"].get("suspicious", False) and (report["body"].get("suspicious_patterns", []) or report["links"]):
        risk_level = "medium"
    elif report["sender"].get("suspicious", False):
        risk_level = "medium"
    elif report["links"]:
        for link in report["links"]:
            if link.get("phishing", False):
                risk_level = "high"
                break
        
    report["risk_level"] = risk_level
    
    return report


