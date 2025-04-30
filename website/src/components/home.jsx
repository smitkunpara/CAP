import { useState } from 'react';
import '../styles/home.css';
import { SuccessNotification, ErrorNotification } from './notification';
import googleLogo from '../assets/google.svg';

const Home = () => {
    const [showLoginModal, setShowLoginModal] = useState(false);

    const handleLoginClick = () => {
        setShowLoginModal(true);
    };

    const closeModal = () => {
        setShowLoginModal(false);
    };

    const handleGoogleLogin = () => {
        // Will be implemented in the backend later
        SuccessNotification("Login feature will be available soon!");
        closeModal();
    };

    const handleDownload = () => {
        // Download extension from the API
        window.location.href = 'http://localhost:3000/emailshild';
        SuccessNotification("Extension download started!");
    };

    return (
        <div className="home-container">
            {/* Navigation Bar */}
            <nav className="navbar">
                <div className="logo-container">
                    <img src="src\assets\logo.svg" alt="Inbox Shield Logo" className="logo" />
                    <h1>Inbox Shield</h1>
                </div>
                <div className="nav-links">
                    <button className="login-button" onClick={handleLoginClick}>Login / Sign up</button>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="hero">
                <div className="hero-content">
                    <h1>Protect Your Inbox with AI</h1>
                    <p>Inbox Shield uses artificial intelligence to analyze emails and links, protecting you from phishing attacks and malicious content.</p>
                    <button className="cta-button" onClick={handleDownload}>Download Extension</button>
                </div>
                <div className="hero-image">
                    <img src="src\assets\phising_mail.png" alt="Email Protection" />
                </div>
            </section>

            {/* Features Section */}
            <section className="features">
                <h2>How Inbox Shield Protects You</h2>
                <div className="feature-cards">
                    <div className="feature-card">
                        <img src="src\assets\email_analysis.jpg" alt="Email Analysis" />
                        <h3>Email Analysis</h3>
                        <p>Our AI examines email content to detect suspicious patterns and language commonly used in phishing attempts.</p>
                    </div>
                    <div className="feature-card">
                        <img src="src\assets\url scanning.jpeg" alt="URL Scanning" />
                        <h3>URL Scanning</h3>
                        <p>We automatically check all links in your emails against our database of known phishing URLs and analyze suspicious ones.</p>
                    </div>
                    <div className="feature-card">
                        <img src="https://img.freepik.com/free-vector/cyber-security-concept_23-2148532223.jpg" alt="Real-time Protection" />
                        <h3>Real-time Protection</h3>
                        <p>Get instant alerts about potentially dangerous emails before you open them or click any links.</p>
                    </div>
                </div>
            </section>

            {/* How to Use Section */}
            <section className="how-to-use">
                <h2>How to Install the Extension</h2>
                <div className="installation-steps">
                    <div className="step">
                        <div className="step-number">1</div>
                        <p>Download the Inbox Shield extension</p>
                    </div>
                    <div className="step">
                        <div className="step-number">2</div>
                        <p>Open Chrome and go to chrome://extensions</p>
                    </div>
                    <div className="step">
                        <div className="step-number">3</div>
                        <p>Enable Developer Mode in the top right corner</p>
                    </div>
                    <div className="step">
                        <div className="step-number">4</div>
                        <p>Click "Load unpacked" and select the downloaded extension folder</p>
                    </div>
                    <div className="step">
                        <div className="step-number">5</div>
                        <p>Inbox Shield is now protecting your emails!</p>
                    </div>
                </div>
                <button className="download-button" onClick={handleDownload}>Download Now</button>
            </section>

            {/* Footer */}
            <footer className="footer">
                <div className="footer-content">
                    <div className="footer-logo">
                        <img src="src\assets\logo.svg" alt="Inbox Shield Logo" className="logo-small" />
                        <p>Inbox Shield</p>
                    </div>
                    <div className="footer-links">
                        <a href="#">Privacy Policy</a>
                        <a href="#">Terms of Service</a>
                        <a href="#">Contact Us</a>
                    </div>
                    <div className="copyright">
                        <p>&copy; {new Date().getFullYear()} Inbox Shield. All rights reserved.</p>
                    </div>
                </div>
            </footer>

            {/* Login Modal */}
            {showLoginModal && (
                <div className="modal-overlay">
                    <div className="login-modal">
                        <button className="close-modal" onClick={closeModal}>&times;</button>
                        <h2>Login to Inbox Shield</h2>
                        <button className="google-login-button" onClick={handleGoogleLogin}>
                            <img src={googleLogo} alt="Google Logo" />
                            <span>Login with Google</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Home;