import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './DoctorDashboard.css';

const DoctorDashboard = () => {
    const navigate = useNavigate();

    // Mock data based on the screenshot
    const patients = [
        {
            id: 1,
            name: "Robert Chen",
            age: 45,
            gender: "Male",
            ward: "Ward A - Bed 12",
            diagnosis: "Acute Appendicitis",
            status: "Critical",
            admitted: "08:30 AM",
            discharge: "2:00 PM Tomorrow",
            dischargeLabel: "Tomorrow"
        },
        {
            id: 2,
            name: "Sarah Miller",
            age: 62,
            gender: "Female",
            ward: "Ward B - Bed 04",
            diagnosis: "Pneumonia",
            status: "Stable",
            admitted: "11:15 AM",
            discharge: "09:00 AM Thursday",
            dischargeLabel: "Thursday"
        },
        {
            id: 3,
            name: "David Wilson",
            age: 38,
            gender: "Male",
            ward: "Ward C - Bed 21",
            diagnosis: "Post-Op Recovery (Knee)",
            status: "Observing",
            admitted: "Yesterday",
            discharge: "6:00 PM Tonight",
            dischargeLabel: "Tonight"
        }
    ];

    return (
        <div className="doctor-layout">
            {/* Sidebar */}
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
                </div>
            </aside>

            {/* Main Content */}
            <main className="doc-main">
                {/* Top Header */}
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
                        <button className="btn-admit" onClick={() => navigate('/patients/new')}>
                            <span className="icon-plus">➕</span> Admit Patient
                        </button>
                        <button className="btn-bell">🔔</button>
                    </div>
                </header>

                {/* Dashboard Content */}
                <div className="doc-content">
                    <div className="content-header">
                        <h1>My Admitted Patients</h1>
                        <p>3 Admitted Patients under your care today</p>
                    </div>

                    <div className="patient-cards-grid">
                        {patients.map(patient => (
                            <div className="patient-card" key={patient.id}>
                                <div className="card-top">
                                    <span className="active-badge">ACTIVE ADMISSION</span>
                                    <span className={`status-tag ${patient.status.toLowerCase()}`}>
                                        {patient.status.toUpperCase()}
                                    </span>
                                </div>

                                <div className="card-header">
                                    <h3>{patient.name}</h3>
                                    <span className="demographics">{patient.age}, {patient.gender}</span>
                                </div>

                                <div className="card-row ward-info">
                                    <span className="icon">🛏️</span>
                                    <span>{patient.ward}</span>
                                </div>

                                <div className="card-row diagnosis-section">
                                    <div className="icon-box">🏥</div>
                                    <div className="diagnosis-info">
                                        <span className="label">REASON FOR ADMISSION</span>
                                        <span className="value">{patient.diagnosis}</span>
                                    </div>
                                </div>

                                <div className="time-row">
                                    <div className="time-block">
                                        <span className="icon-arrow-in">Login</span>
                                        <div className="time-details">
                                            <span className="label">ADMITTED</span>
                                            <span className="value">{patient.admitted}</span>
                                        </div>
                                    </div>
                                    <div className="time-block right">
                                        <span className="icon-arrow-out">Logout</span>
                                        <div className="time-details">
                                            <span className="label">DISCHARGE</span>
                                            <span className="value">{patient.discharge}</span>
                                        </div>
                                    </div>
                                </div>

                                <button className="btn-view-details">
                                    View Details
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DoctorDashboard;
