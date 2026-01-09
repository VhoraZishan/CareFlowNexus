import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './DoctorDashboard.css';

const DoctorDashboard = () => {
    const navigate = useNavigate();
    const [patients, setPatients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState(null);

    useEffect(() => {
        const fetchPatients = async () => {
            try {
                const userStr = localStorage.getItem('user');
                if (!userStr) {
                    navigate('/');
                    return;
                }
                const parsedUser = JSON.parse(userStr);
                setUser(parsedUser);
                const data = await api.getPatients(parsedUser.user_id);
                // The backend returns 'created' or 'admitted' for doctors
                // Let's show all of them if they are returned
                setPatients(data);
            } catch (err) {
                console.error("Failed to load patients", err);
            } finally {
                setLoading(false);
            }
        };

        fetchPatients();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('user');
        navigate('/');
    };

    // Helper for priority demo 
    const getPriority = (status) => {
        if (status === 'critical') return 'high';
        if (status === 'admitted') return 'normal';
        return 'low';
    };

    return (
        <div className="doctor-layout">
            <aside className="doc-sidebar-premium">
                <div className="sidebar-logo">
                    <h1>CareFlow Nexus</h1>
                </div>

                <nav className="sidebar-nav-premium">
                    <button className="nav-btn active">
                        Dashboard
                    </button>
                    <button className="nav-btn" onClick={() => navigate('/patients/doctor-admit')}>
                        Add Patient
                    </button>
                    <button className="nav-btn" onClick={handleLogout}>
                        Logout
                    </button>
                </nav>

                <div className="sidebar-bottom">
                    <div className="user-profile-widget">
                        <div className="user-avatar-small">
                            <img src={`https://ui-avatars.com/api/?name=${user?.role || 'Doctor'}&background=3b82f6&color=fff&bold=true`} alt="Avatar" />
                        </div>
                        <div className="user-meta-small">
                            <h4>{user?.role === 'doctor' ? 'Clinical Lead' : 'Staff Member'}</h4>
                            <p>{user?.user_id}</p>
                        </div>
                        <button className="logout-icon-btn" onClick={handleLogout} title="Logout">
                            <span>⏻</span>
                        </button>
                    </div>
                </div>
            </aside>

            <main className="doc-main">
                <header className="doc-header">
                    <div className="header-left">
                        <h2>Dr. {user?.name || user?.user_id}</h2>
                        <span className="status-badge">ON SHIFT</span>
                    </div>

                    <div className="header-right">
                        <button className="add-patient-btn-header" onClick={() => navigate('/patients/doctor-admit')}>
                            + Add Patient
                        </button>
                        <div className="doc-search">
                            <span className="search-icon">🔍</span>
                            <input type="text" placeholder="Search patients..." />
                        </div>
                        <button className="notification-btn">🔔</button>
                    </div>
                </header>

                <div className="doc-grid-container">
                    <div className="content-header-row">
                        <div className="title-group">
                            <h2>My Admitted Patients</h2>
                            <p className="subtitle">{patients.length} Admitted Patients under your care today</p>
                        </div>
                    </div>

                    {loading ? (
                        <div className="loading-state">Syncing medical records...</div>
                    ) : patients.length === 0 ? (
                        <div className="empty-state">No active patient records found.</div>
                    ) : (
                        <div className="patient-card-grid">
                            {patients.map((patient) => (
                                <div className="patient-item-card" key={patient.patient_id}>
                                    <div className="card-header-v2">
                                        <span className="admission-tag">ACTIVE ADMISSION</span>
                                        <span className={`priority-tag-pill ${getPriority(patient.status)}`}>
                                            {patient.status.toUpperCase()}
                                        </span>
                                    </div>

                                    <div className="card-top-main">
                                        <div className="patient-basic">
                                            <h3>{patient.name}</h3>
                                            <span className="age-gender">{patient.age}, {patient.gender}</span>
                                        </div>
                                        <div className="ward-info">
                                            <span className="icon">🏥</span>
                                            Ward {patient.ward || 'A'} - Bed {patient.bed || '01'}
                                        </div>
                                    </div>

                                    <div className="card-detail-section">
                                        <div className="detail-item">
                                            <span className="icon">📝</span>
                                            <div className="detail-text">
                                                <label>REASON FOR ADMISSION</label>
                                                <p>{patient.medical_history?.[0] || 'General Admission'}</p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="card-timing-grid">
                                        <div className="time-block">
                                            <span className="arrow">➔</span>
                                            <div className="time-data">
                                                <label>ADMITTED</label>
                                                <p>08:30 AM</p>
                                            </div>
                                        </div>
                                        <div className="time-block">
                                            <span className="arrow logout">←</span>
                                            <div className="time-data">
                                                <label>DISCHARGE</label>
                                                <p>2:00 PM Tomorrow</p>
                                            </div>
                                        </div>
                                    </div>

                                    <button className="view-details-btn" onClick={() => navigate('/patients/details', { state: { patient } })}>
                                        View Details
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default DoctorDashboard;
