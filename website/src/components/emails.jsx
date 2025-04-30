import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/emails.css';
import { ErrorNotification } from './notification';

const Emails = () => {
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        // Check if user is logged in
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/');
            return;
        }

        // Fetch emails
        fetchEmails(token);
    }, [navigate]);

    const fetchEmails = async (token) => {
        try {
            const response = await fetch('http://localhost:8000/emails', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired or invalid
                    localStorage.removeItem('token');
                    navigate('/');
                    return;
                }
                throw new Error('Failed to fetch emails');
            }

            const data = await response.json();
            setEmails(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching emails:', error);
            ErrorNotification('Failed to fetch email analysis');
            setLoading(false);
        }
    };

    const handleEmailClick = (emailId) => {
        navigate(`/email/${emailId}`);
    };

    const handleBackToHome = () => {
        navigate('/');
    };

    return (
        <div className="emails-container">
            <header className="emails-header">
                <div className="header-content">
                    <h1>Analyzed Emails</h1>
                    <button className="back-button" onClick={handleBackToHome}>Back to Home</button>
                </div>
            </header>

            <main className="emails-list-container">
                {loading ? (
                    <div className="loading">Loading your analyzed emails...</div>
                ) : emails.length === 0 ? (
                    <div className="no-emails">
                        <h2>No analyzed emails found</h2>
                        <p>When you analyze emails using the Inbox Shield extension, they will appear here.</p>
                    </div>
                ) : (
                    <ul className="emails-list">
                        {emails.map(email => (
                            <li key={email._id} className="email-item" onClick={() => handleEmailClick(email._id)}>
                                <div className="email-subject">{email.subject || 'No Subject'}</div>
                                <div className="email-arrow">→</div>
                            </li>
                        ))}
                    </ul>
                )}
            </main>
        </div>
    );
};

export default Emails;