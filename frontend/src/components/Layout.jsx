import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Layout.css';

const Layout = ({ children, title }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const [user, setUser] = useState(null);

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (userStr) setUser(JSON.parse(userStr));
    }, []);

    const isActive = (path) => location.pathname === path;

    return (
        <div className="admin-layout">
            <aside className="sidebar">
                <div className="sidebar-brand-top">
                    <h1>CareFlow Nexus</h1>
                    <p>Admin Portal</p>
                </div>

                <nav className="sidebar-nav">
                    <button onClick={() => navigate('/dashboard')} className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}>
                        Dashboard
                    </button>
                    <button onClick={() => navigate('/patients/new')} className={`nav-item ${isActive('/patients/new') ? 'active' : ''}`}>
                        New Patient
                    </button>
                    <button onClick={() => navigate('/patients')} className={`nav-item ${isActive('/patients') ? 'active' : ''}`}>
                        Patients List
                    </button>
                    <button className="nav-item">
                        Appointments
                    </button>
                    <button className="nav-item">
                        Settings
                    </button>
                    <button className="nav-item logout-nav-btn" onClick={() => { localStorage.removeItem('user'); navigate('/'); }}>
                        Log Out
                    </button>
                </nav>

                <div className="sidebar-footer">
                    <div className="help-desk-card">
                        <h4>HELP DESK</h4>
                        <p>Need assistance with automated assignment?</p>
                        <button className="contact-link">Contact Support →</button>
                    </div>

                    <div className="sidebar-user-profile">
                        <div className="user-avatar-premium">
                            <img src={`https://ui-avatars.com/api/?name=${user?.role || 'Admin'}&background=2563eb&color=fff&bold=true`} alt="Avatar" />
                        </div>
                        <div className="user-info-text">
                            <h4>{user?.name || user?.user_id || 'Administrator'}</h4>
                            <p>Active Session</p>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="main-content">
                <header className="admin-header">
                    <div className="header-session-info">
                        <span className="session-status">● Session Active</span>
                        <span className="session-time">1h 24m</span>
                    </div>

                    <div className="header-actions">
                        <div className="header-search">
                            <span>🔍</span>
                            <input type="text" placeholder="Search medical records..." />
                        </div>
                        <button className="icon-btn">🔔</button>
                    </div>
                </header>

                <div className="content-scroll-container">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
