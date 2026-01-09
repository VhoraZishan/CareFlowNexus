import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './DoctorDashboard.css';

const DoctorDashboard = () => {
    const navigate = useNavigate();
    const [patients, setPatients] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPatients = async () => {
            try {
                const userStr = localStorage.getItem('user');
                if (!userStr) {
                    navigate('/');
                    return;
                }
                const user = JSON.parse(userStr);
                const data = await api.getPatients(user.user_id);
                // Filter for "undercare" status as requested
                setPatients(data.filter(p => p.status?.toLowerCase() === 'undercare'));
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

    // Helper to extract display data
    const getDiagnosis = (p) => {
        if (p.admission && p.admission.diagnosis) return p.admission.diagnosis;
        if (p.medical_history && p.medical_history.length > 0) return p.medical_history[0];
        return "Under Observation";
    };

    const getWard = (p) => {
        if (p.admission && p.admission.room) return `Ward ${p.admission.room}`;
        return "Unassigned";
    };

    return (
        <div className="doctor-layout">
            <aside className="doc-sidebar">
                <div className="doc-logo">CareFlow Nexus</div>
                <nav className="doc-nav">
                    <button className="doc-nav-item active">
                        <span className="icon">👥</span> My Patients
                    </button>
                </nav>
                <div className="doc-sidebar-footer">
                    <button className="doc-nav-item">
                        <span className="icon">⚙️</span> Settings
                    </button>
                    <button className="doc-nav-item" onClick={handleLogout} style={{ color: '#ef4444' }}>
                        <span className="icon">🚪</span> Logout
                    </button>
                </div>
            </aside>

            <main className="doc-main">
                <header className="doc-header">
                    <div className="doc-profile">
                        <div className="doc-avatar-circle"></div>
                        <div className="doc-info">
                            <h4 className="doc-name">Dr. Julian Smith</h4>
                            <div className="doc-status">
                                <span className="status-dot"></span> Shift Status: Active
                            </div>
                        </div>
                    </div>

                    <div className="doc-search">
                        <span className="search-icon">🔍</span>
                        <input type="text" placeholder="Search patients, wards..." />
                    </div>

                    <div className="doc-actions">
                        <button className="btn-admit" onClick={() => navigate('/patients/doctor-admit')}>
                            <span className="icon-plus">➕</span> Admit Patient
                        </button>
                        <button className="btn-bell">🔔</button>
                    </div>
                </header>

                <div className="doc-content">
                    <div className="content-header">
                        <h1>My Admitted Patients</h1>
                        <p>{patients.length} Admitted Patients under your care</p>
                    </div>

                    <div className="patient-cards-grid">
                        {loading ? <p>Loading patients...</p> : patients.length === 0 ? <p>No patients currently under care.</p> : patients.map(patient => (
                            <div className="patient-card" key={patient.patient_id}>
                                <div className="card-top">
                                    <span className="active-badge">ACTIVE ADMISSION</span>
                                    <span className="status-tag stable">UNDER CARE</span>
                                </div>

                                <div className="card-header">
                                    <h3>{patient.name}</h3>
                                    <span className="demographics">{patient.age}, {patient.gender}</span>
                                </div>

                                <div className="card-row ward-info">
                                    <span className="icon">🛏️</span>
                                    <span>{getWard(patient)}</span>
                                </div>

                                <div className="card-row diagnosis-section">
                                    <div className="icon-box">🏥</div>
                                    <div className="diagnosis-info">
                                        <span className="label">REASON FOR ADMISSION</span>
                                        <span className="value">{getDiagnosis(patient)}</span>
                                    </div>
                                </div>

                                <div className="time-row">
                                    <div className="time-block">
                                        <span className="icon-arrow-in">Login</span>
                                        <div className="time-details">
                                            <span className="label">ADMITTED</span>
                                            <span className="value">
                                                {patient.created_at ? new Date(patient.created_at).toLocaleDateString() : 'Today'}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="time-block right">
                                        <span className="icon-arrow-out">Logout</span>
                                        <div className="time-details">
                                            <span className="label">DISCHARGE</span>
                                            <span className="value">--</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="card-actions">
                                    <button className="btn-view-details">
                                        View Details
                                    </button>
                                    <button className="btn-request-discharge">
                                        Request Discharge
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DoctorDashboard;
