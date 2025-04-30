import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../styles/analysis.css';
import { ErrorNotification } from './notification';

const Analysis = () => {
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(true);
    const { emailId } = useParams();
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/');
            return;
        }

        fetchEmailAnalysis(token, emailId);
    }, [emailId, navigate]);

    const fetchEmailAnalysis = async (token, id) => {
        try {
            const response = await fetch(`http://localhost:8000/email/${id}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('token');
                    navigate('/');
                    return;
                }
                throw new Error('Failed to fetch email analysis');
            }

            const data = await response.json();
            setAnalysis(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching email analysis:', error);
            ErrorNotification('Failed to fetch email analysis');
            setLoading(false);
        }
    };

    const handleBackToEmails = () => {
        navigate('/emails');
    };

    const getRiskLevelColor = (riskLevel) => {
        switch (riskLevel) {
            case 'high':
                return '#e74c3c';
            case 'medium':
                return '#f39c12';
            case 'low':
                return '#2ecc71';
            default:
                return '#3498db';
        }
    };

    if (loading) {
        return (
            <div className="analysis-loading">
                <div className="loading-spinner"></div>
                <p>Loading analysis...</p>
            </div>
        );
    }

    if (!analysis) {
        return (
            <div className="analysis-error">
                <h2>Analysis not found</h2>
                <button className="back-button" onClick={handleBackToEmails}>
                    Back to emails
                </button>
            </div>
        );
    }

    const { email_analysis } = analysis;

    return (
        <div className="analysis-container">
            <header className="analysis-header">
                <div className="header-content">
                    <h1>Email Analysis</h1>
                    <button className="back-button" onClick={handleBackToEmails}>
                        Back to emails
                    </button>
                </div>
            </header>

            <main className="analysis-content">
                <div className="analysis-summary">
                    <div className="risk-indicator" style={{ backgroundColor: getRiskLevelColor(email_analysis.risk_level) }}>
                        <span className="risk-level">{email_analysis.risk_level.toUpperCase()} RISK</span>
                    </div>
                    <h2>{email_analysis.subject.subject || 'No Subject'}</h2>
                    <div className="sender-info">
                        <strong>From:</strong> {email_analysis.sender.address}
                        {email_analysis.sender.suspicious && (
                            <span className="warning-tag">Suspicious Sender</span>
                        )}
                    </div>
                </div>

                <div className="analysis-sections">
                    <section className="analysis-section">
                        <h3>Subject Analysis</h3>
                        <div className="section-content">
                            <p><strong>Subject:</strong> {email_analysis.subject.subject}</p>
                            <p><strong>Suspicious:</strong> {email_analysis.subject.suspicious ? 'Yes' : 'No'}</p>
                            <p><strong>Urgency Indicators:</strong> {email_analysis.subject.urgency_indicators ? 'Yes' : 'No'}</p>
                            <p><strong>Reward Indicators:</strong> {email_analysis.subject.reward_indicators ? 'Yes' : 'No'}</p>
                        </div>
                    </section>

                    <section className="analysis-section">
                        <h3>Sender Analysis</h3>
                        <div className="section-content">
                            <p><strong>Address:</strong> {email_analysis.sender.address}</p>
                            <p><strong>Suspicious:</strong> {email_analysis.sender.suspicious ? 'Yes' : 'No'}</p>
                            {email_analysis.sender.reason && (
                                <p><strong>Reason:</strong> {email_analysis.sender.reason}</p>
                            )}
                        </div>
                    </section>

                    <section className="analysis-section">
                        <h3>Body Analysis</h3>
                        <div className="section-content">
                            <p><strong>Contains HTML:</strong> {email_analysis.body.contains_html ? 'Yes' : 'No'}</p>
                            
                            {email_analysis.body.suspicious_patterns && email_analysis.body.suspicious_patterns.length > 0 && (
                                <div className="suspicious-patterns">
                                    <h4>Suspicious Patterns Detected:</h4>
                                    <ul>
                                        {email_analysis.body.suspicious_patterns.map((pattern, index) => (
                                            <li key={index}>
                                                <strong>{pattern.type}:</strong> {pattern.matches.join(', ')}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </section>

                    {email_analysis.links && email_analysis.links.length > 0 && (
                        <section className="analysis-section">
                            <h3>Links Analysis</h3>
                            <div className="section-content">
                                <ul className="links-list">
                                    {email_analysis.links.map((link, index) => (
                                        <li key={index} className={link.phishing ? 'phishing-link' : 'safe-link'}>
                                            <div className="link-status">
                                                {link.phishing ? '⚠️ Suspicious' : '✓ Safe'}
                                            </div>
                                            <div className="link-url">{link.url}</div>
                                            {link.probability && (
                                                <div className="link-probability">
                                                    Phishing Probability: {(link.probability * 100).toFixed(1)}%
                                                </div>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </section>
                    )}

                    {Object.keys(email_analysis.attachments).length > 0 && (
                        <section className="analysis-section">
                            <h3>Attachments Analysis</h3>
                            <div className="section-content">
                                <ul className="attachments-list">
                                    {Object.entries(email_analysis.attachments).map(([name, suspicious]) => (
                                        <li key={name} className={suspicious ? 'suspicious-attachment' : 'safe-attachment'}>
                                            <span className="attachment-icon">{suspicious ? '⚠️' : '📄'}</span>
                                            <span className="attachment-name">{name}</span>
                                            <span className="attachment-status">
                                                {suspicious ? 'Potentially harmful' : 'Appears safe'}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </section>
                    )}

                    <section className="analysis-section original-email">
                        <h3>Original Email</h3>
                        <div className="email-content" dangerouslySetInnerHTML={{ __html: email_analysis.original_body }}></div>
                    </section>
                </div>
            </main>
        </div>
    );
};

export default Analysis;