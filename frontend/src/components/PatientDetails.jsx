import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './PatientDetails.css';

const PatientDetails = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [patient, setPatient] = useState(null);

    useEffect(() => {
        if (location.state?.patient) {
            setPatient(location.state.patient);
        } else {
            // Ideally fetch here if ID is in URL params, but for now redirect
            navigate('/doctor-dashboard');
        }
    }, [location, navigate]);

    if (!patient) return null;

    return (
        <div className="patient-details-layout">
            <main className="details-main">
                <header className="details-header">
                    <div className="header-left">
                        <h2>Patient Medical Record</h2>
                        <span className="patient-status-badge status-admitted">
                            {patient.status || 'Admitted'}
                        </span>
                    </div>
                    <button className="back-btn" onClick={() => navigate('/doctor-dashboard')}>
                        ← Back to Dashboard
                    </button>
                </header>

                <div className="details-content">
                    {/* Hero Section */}
                    <div className="patient-hero-card">
                        <div className="hero-avatar">
                            {patient.name ? patient.name.charAt(0).toUpperCase() : 'P'}
                        </div>
                        <div className="hero-info">
                            <h1>{patient.name}</h1>
                            <div className="hero-meta">
                                <div className="meta-item">
                                    <span>🆔</span> {patient.patient_id}
                                </div>
                                <div className="meta-item">
                                    <span>🎂</span> {patient.age} Years Old
                                </div>
                                <div className="meta-item">
                                    <span>⚧</span> {patient.gender}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="details-grid">
                        {/* Admission Info */}
                        <div className="detail-card">
                            <div className="card-title">
                                <span>🏥</span> Current Admission
                            </div>
                            <div className="info-row">
                                <div className="info-label">Ward / Bed</div>
                                <div className="info-value">Ward {patient.ward || 'General'} - Bed {patient.bed || 'Unassigned'}</div>
                            </div>
                            <div className="info-row">
                                <div className="info-label">Admission Date</div>
                                <div className="info-value">{new Date().toLocaleDateString()}</div>
                            </div>
                            <div className="info-row">
                                <div className="info-label">Doctor in Charge</div>
                                <div className="info-value">Dr. {patient.doctor_name || 'Assigned Staff'}</div>
                            </div>
                        </div>

                        {/* Medical Details */}
                        <div className="detail-card full-width">
                            <div className="card-title">
                                <span>🩺</span> Clinical Information
                            </div>
                            <div className="info-row">
                                <div className="info-label">Primary Diagnosis</div>
                                <div className="diagnosis-box">
                                    {patient.medical_history?.[0] || 'Under Observation'}
                                </div>
                            </div>
                            <div className="info-row">
                                <div className="info-label">Medical History</div>
                                <div className="info-value">
                                    {patient.medical_history?.join(', ') || 'No history recorded'}
                                </div>
                            </div>
                            <div className="info-row">
                                <div className="info-label">Special Instructions</div>
                                <div className="info-value" style={{ fontStyle: 'italic', color: '#64748b' }}>
                                    {patient.notes || 'No special instructions provided.'}
                                </div>
                            </div>
                        </div>

                        {/* Vitals / Stats (Placeholder for now) */}
                        <div className="detail-card">
                            <div className="card-title">
                                <span>📊</span> Latest Vitals
                            </div>
                            <div className="info-row">
                                <div className="info-label">Blood Pressure</div>
                                <div className="info-value">120/80 mmHg</div>
                            </div>
                            <div className="info-row">
                                <div className="info-label">Heart Rate</div>
                                <div className="info-value">72 bpm</div>
                            </div>
                            <div className="info-row">
                                <div className="info-label">SpO2</div>
                                <div className="info-value">98%</div>
                            </div>
                        </div>

                        {/* Emergency Contact */}
                        <div className="detail-card">
                            <div className="card-title">
                                <span>📞</span> Emergency Contact
                            </div>
                            <div className="info-row">
                                <div className="info-label">Next of Kin</div>
                                <div className="info-value">{patient.emergency_contact_name || 'Not Provided'}</div>
                            </div>
                            <div className="info-row">
                                <div className="info-label">Contact Number</div>
                                <div className="info-value">{patient.emergency_contact_phone || '--'}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default PatientDetails;
