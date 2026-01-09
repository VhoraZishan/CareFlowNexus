import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Layout.css';

const Layout = ({ children, title, actions }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const isActive = (path) => location.pathname === path;

    return (
        <div className="layout-container">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h2>CareFlow Nexus</h2>
                </div>
                <nav className="sidebar-nav">
                    <button onClick={() => navigate('/dashboard')} className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}>
                        Dashboard
                    </button>
                    <button onClick={() => navigate('/patients/new')} className={`nav-item ${isActive('/patients/new') ? 'active' : ''}`}>
                        New Patient
                    </button>
                    <button className="nav-item">Patients List</button>
                    <button className="nav-item">Appointments</button>
                    <button className="nav-item">Settings</button>
                </nav>

                <div className="help-desk-card">
                    <h4>HELP DESK</h4>
                    <p>Need assistance with automated assignment?</p>
                    <a href="#">Contact Support &rarr;</a>
                </div>

                <div className="sidebar-footer">
                    <div className="user-info">
                        <div className="avatar">AD</div>
                        <div className="user-details">
                            <span className="user-name">Sarah Jenkins</span>
                            <span className="user-role">Head Receptionist</span>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="main-content">
                <header className="top-bar">
                    <h1 className="page-title">{title}</h1>
                    <div className="header-right">
                        <div className="search-bar">
                            <input type="text" placeholder="Search medical records..." />
                        </div>
                        <div className="actions">
                            {actions}
                            <button className="icon-btn">🔔</button>
                        </div>
                    </div>
                </header>

                <div className="content-scrollable">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
