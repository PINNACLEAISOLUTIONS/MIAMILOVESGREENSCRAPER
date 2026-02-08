import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Mail, Phone, Users, Globe, ArrowRight, Loader2, Database, ExternalLink, Calendar, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Types for Search Results
interface LeadData {
    company: {
        name: string;
        logo: string;
        domain: string;
        size?: string;
        industry?: string;
        location?: string;
        founded?: string;
        revenue?: string;
    };
    contacts: Array<{
        email: string;
        type?: string;
        confidence?: number;
    }>;
    phones: Array<{
        number: string;
        type?: string;
        carrier?: string;
    }>;
}

// Types for Extracted Leads
interface ExtractedLead {
    Job_Title: string;
    Source_URL: string;
    Agency: string;
    Closing_Date: string;
    Raw_Text: string;
    Score: number;
    Discovered_At?: string;
    Source_Platform?: string;
}

function App() {
    const [activeTab, setActiveTab] = useState<'search' | 'leads'>('search');

    // Search State
    const [domain, setDomain] = useState('');
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<LeadData | null>(null);

    // Leads State
    const [leads, setLeads] = useState<ExtractedLead[]>([]);
    const [leadsLoading, setLeadsLoading] = useState(false);

    const fetchIntel = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!domain) return;

        setLoading(true);
        try {
            const response = await axios.get(`/api/intel?domain=${domain}`);
            setData(response.data);
        } catch (error) {
            console.error('Error fetching data', error);
            alert('Failed to fetch data. Make sure search results are available for this domain.');
        } finally {
            setLoading(false);
        }
    };

    const fetchLeads = async () => {
        setLeadsLoading(true);
        try {
            const response = await axios.get('/api/leads');
            // Ensure response data is an array
            const leadsData = Array.isArray(response.data) ? response.data : [];
            setLeads(leadsData);
        } catch (error) {
            console.error('Error fetching leads', error);
            // alert('Failed to load extracted leads.');
        } finally {
            setLeadsLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'leads') {
            fetchLeads();
        }
    }, [activeTab]);

    return (
        <div className="app-container">
            <header className="app-header">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="header-content"
                >
                    <div className="brand">
                        <h1>LeadIntel</h1>
                        <span className="badge">BETA</span>
                    </div>
                    <nav className="nav-tabs">
                        <button
                            className={`nav-tab ${activeTab === 'search' ? 'active' : ''}`}
                            onClick={() => setActiveTab('search')}
                        >
                            <Search size={18} /> Domain Search
                        </button>
                        <button
                            className={`nav-tab ${activeTab === 'leads' ? 'active' : ''}`}
                            onClick={() => setActiveTab('leads')}
                        >
                            <Database size={18} /> Extracted Leads
                        </button>
                    </nav>
                </motion.div>
            </header>

            <main className="main-content">
                <AnimatePresence mode="wait">
                    {activeTab === 'search' ? (
                        <motion.div
                            key="search"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ duration: 0.3 }}
                            className="search-view"
                        >
                            <section className="search-section">
                                <div className="hero-text">
                                    <h2>Predictive Intelligence</h2>
                                    <p>Instant sales data enrichment for any domain.</p>
                                </div>

                                <form onSubmit={fetchIntel} className="search-bar">
                                    <input
                                        type="text"
                                        placeholder="Enter company domain (e.g. apple.com)"
                                        value={domain}
                                        onChange={(e) => setDomain(e.target.value)}
                                    />
                                    <button type="submit" disabled={loading}>
                                        {loading ? <Loader2 className="animate-spin" /> : 'Search'}
                                    </button>
                                </form>
                            </section>

                            {data && (
                                <motion.div
                                    className="results-grid"
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                >
                                    <div className="glass-card company-hero">
                                        <div className="logo-container">
                                            <img src={data.company.logo} alt={data.company.name} onError={(e) => {
                                                (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${data.company.name}&background=random`
                                            }} />
                                        </div>
                                        <div className="company-info">
                                            <div className="info-label">Organization</div>
                                            <h2>{data.company.name}</h2>
                                            <div className="metrics-row">
                                                <div className="metric">
                                                    <Globe size={16} /> {data.company.domain}
                                                </div>
                                                {data.company.size && (
                                                    <div className="metric">
                                                        <Users size={16} /> {data.company.size}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="glass-card">
                                        <div className="card-header">
                                            <Mail size={20} />
                                            <h3>Verified Contacts</h3>
                                        </div>
                                        <ul className="contact-list">
                                            {data.contacts.length > 0 ? (
                                                data.contacts.map((contact, i) => (
                                                    <li key={i} className="contact-item">
                                                        <div className="contact-main">{contact.email}</div>
                                                        <div className="contact-meta">
                                                            <span className="tag">{contact.type || 'Email'}</span>
                                                            <span className="confidence">{contact.confidence ? `${Math.round(contact.confidence)}%` : 'Verified'}</span>
                                                        </div>
                                                    </li>
                                                ))
                                            ) : (
                                                <li className="empty-state">No contacts found</li>
                                            )}
                                        </ul>
                                    </div>

                                    <div className="glass-card">
                                        <div className="card-header">
                                            <Phone size={20} />
                                            <h3>Phone Numbers</h3>
                                        </div>
                                        <ul className="contact-list">
                                            {data.phones.map((phone, i) => (
                                                <li key={i} className="contact-item">
                                                    <div className="contact-main">{phone.number}</div>
                                                    <div className="contact-meta">
                                                        <span className="tag">{phone.type}</span>
                                                        <span>{phone.carrier}</span>
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </motion.div>
                            )}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="leads"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.3 }}
                            className="leads-view"
                        >
                            <div className="leads-header">
                                <h2>Extracted Opportunities</h2>
                                <button className="refresh-btn" onClick={fetchLeads} disabled={leadsLoading}>
                                    {leadsLoading ? <Loader2 className="animate-spin" size={16} /> : 'Refresh Data'}
                                </button>
                            </div>

                            {leadsLoading && leads.length === 0 ? (
                                <div className="loading-state">
                                    <Loader2 className="animate-spin" size={48} />
                                    <p>Loading intelligence...</p>
                                </div>
                            ) : leads.length > 0 ? (
                                <div className="leads-grid">
                                    {leads.map((lead, index) => (
                                        <div key={index} className="glass-card lead-card">
                                            <div className="lead-header">
                                                <span className={`score-badge ${lead.Score >= 40 ? 'high' : 'med'}`}>
                                                    Score: {lead.Score}
                                                </span>
                                                <span className="platform-tag">
                                                    {lead.Source_Platform || 'Web'}
                                                </span>
                                            </div>
                                            <h3>{lead.Job_Title || 'Untitled Request'}</h3>
                                            <p className="lead-excerpt">{lead.Raw_Text?.substring(0, 150)}...</p>

                                            <div className="lead-meta">
                                                <div className="meta-item">
                                                    <User size={14} /> {lead.Agency}
                                                </div>
                                                <div className="meta-item">
                                                    <Calendar size={14} /> {lead.Closing_Date}
                                                </div>
                                            </div>

                                            <a href={lead.Source_URL} target="_blank" rel="noopener noreferrer" className="action-btn">
                                                View Source <ExternalLink size={14} />
                                            </a>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state-large">
                                    <Database size={48} />
                                    <h3>No Leads Found</h3>
                                    <p>Run the scraping pipeline to generate new leads.</p>
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>
        </div>
    );
}

export default App;
