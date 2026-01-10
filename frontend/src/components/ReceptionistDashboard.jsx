import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './ReceptionistDashboard.css';

const ReceptionistDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [pendingPatients, setPendingPatients] = useState([]);
    const [allPatients, setAllPatients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [confirmingBed, setConfirmingBed] = useState(null);
    const [activeTab, setActiveTab] = useState('pending'); // 'pending' or 'all'

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const userStr = localStorage.getItem('user');
            if (!userStr) {
                navigate('/');
                return;
            }
            const parsedUser = JSON.parse(userStr);
            setUser(parsedUser);

            // Fetch pending confirmations
            const pending = await api.getPendingConfirmations(parsedUser.user_id);
            setPendingPatients(pending || []);

            // Fetch all patients
            const all = await api.getPatients(parsedUser.user_id);
            setAllPatients(all || []);

        } catch (err) {
            console.error("Failed to load data", err);
        } finally {
            setLoading(false);
        }
    };

    const handleConfirmBed = async (patient) => {
        if (!patient.admission?.recommended_bed_id) {
            alert('No bed recommendation available for this patient');
            return;
        }

        const confirmed = window.confirm(
            `Confirm bed assignment?\n\n` +
            `Patient: ${patient.name}\n` +
            `Recommended Bed: ${patient.admission.recommended_bed_id}\n` +
            `Reason: ${patient.admission.agent_message || 'AI recommended'}\n\n` +
            `This will assign a cleaner to prepare the bed.`
        );

        if (!confirmed) return;

        setConfirmingBed(patient.patient_id);

        try {
            await api.confirmBed(patient.patient_id, {
                user_id: user.user_id,
                bed_id: patient.admission.recommended_bed_id
            });

            alert('✅ Bed confirmed successfully!\n\nA cleaner has been assigned to prepare the bed.');

            // Refresh data
            await fetchData();
        } catch (error) {
            console.error('Failed to confirm bed', error);
            alert('❌ Error confirming bed: ' + error.message);
        } finally {
            setConfirmingBed(null);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('user');
        navigate('/');
    };

    const getStatusBadge = (status) => {
        const statusConfig = {
            'created': { label: 'Registered', color: 'blue' },
            'pending_confirmation': { label: 'Awaiting Confirmation', color: 'orange' },
            'bed_confirmed': { label: 'Bed Confirmed', color: 'green' },
            'admitted': { label: 'Admitted', color: 'green' },
            'discharged': { label: 'Discharged', color: 'gray' }
        };
        const config = statusConfig[status] || { label: status, color: 'gray' };
        return <span className={`status-badge ${config.color}`}>{config.label}</span>;
    };

    return (
        <div className="receptionist-layout">
            <aside className="receptionist-sidebar">
                <div className="sidebar-brand">
                    <h1>CareFlow Nexus</h1>
                    <p>RECEPTION DESK</p>
                </div>

                <nav className="receptionist-nav">
                    <button
                        className={`nav-btn ${activeTab === 'pending' ? 'active' : ''}`}
                        onClick={() => setActiveTab('pending')}
                    >
                        <span className="icon">⏳</span> Pending Confirmations
                        {pendingPatients.length > 0 && (
                            <span className="badge">{pendingPatients.length}</span>
                        )}
                    </button>
                    <button
                        className={`nav-btn ${activeTab === 'all' ? 'active' : ''}`}
                        onClick={() => setActiveTab('all')}
                    >
                        <span className="icon">📋</span> All Patients
                    </button>
                    <button className="nav-btn" onClick={() => navigate('/patients/new')}>
                        <span className="icon">➕</span> New Patient
                    </button>
                    <button className="nav-btn" onClick={handleLogout}>
                        <span className="icon">⏻</span> Logout
                    </button>
                </nav>

                <div className="sidebar-bottom-profile">
                    <div className="profile-card">
                        <div className="avatar">
                            <img
                                src={`https://ui-avatars.com/api/?name=${user?.user_id || 'Receptionist'}&background=6366f1&color=fff&bold=true`}
                                alt="Receptionist"
                            />
                        </div>
                        <div className="meta">
                            <h4>{user?.user_id || 'Receptionist'}</h4>
                            <p>Reception Desk</p>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="receptionist-content">
                <header className="receptionist-header">
                    <div className="header-left">
                        <h2>Reception Dashboard</h2>
                        <span className="shift-badge">ON DUTY</span>
                    </div>
                    <div className="header-right">
                        <button className="btn-primary" onClick={() => navigate('/patients/new')}>
                            ➕ Register New Patient
                        </button>
                        <div className="search-box">
                            <span>🔍</span>
                            <input type="text" placeholder="Search patients..." />
                        </div>
                    </div>
                </header>

                {activeTab === 'pending' && (
                    <div className="content-section">
                        <div className="section-header">
                            <div>
                                <h3>Pending Bed Confirmations</h3>
                                <p className="subtitle">
                                    {pendingPatients.length} patient{pendingPatients.length !== 1 ? 's' : ''} awaiting bed confirmation
                                </p>
                            </div>
                        </div>

                        {loading ? (
                            <div className="loading-state">Loading pending confirmations...</div>
                        ) : pendingPatients.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-icon">✅</div>
                                <h3>No Pending Confirmations</h3>
                                <p>All bed assignments have been confirmed!</p>
                            </div>
                        ) : (
                            <div className="patients-grid">
                                {pendingPatients.map((patient) => (
                                    <div key={patient.patient_id} className="patient-card pending">
                                        <div className="card-header">
                                            <div className="patient-info">
                                                <h3>{patient.name}</h3>
                                                <span className="patient-meta">
                                                    {patient.age} years, {patient.gender}
                                                </span>
                                            </div>
                                            {getStatusBadge(patient.status)}
                                        </div>

                                        <div className="card-body">
                                            <div className="info-row">
                                                <span className="label">Patient ID:</span>
                                                <span className="value">{patient.patient_id}</span>
                                            </div>
                                            <div className="info-row">
                                                <span className="label">Diagnosis:</span>
                                                <span className="value">{patient.admission?.diagnosis || 'N/A'}</span>
                                            </div>
                                            <div className="info-row highlight">
                                                <span className="label">🛏️ Recommended Bed:</span>
                                                <span className="value bed-id">
                                                    {patient.admission?.recommended_bed_id || 'None'}
                                                </span>
                                            </div>
                                            {patient.admission?.agent_message && (
                                                <div className="info-row">
                                                    <span className="label">AI Reasoning:</span>
                                                    <span className="value reason">
                                                        {patient.admission.agent_message}
                                                    </span>
                                                </div>
                                            )}
                                            <div className="info-row">
                                                <span className="label">Doctor:</span>
                                                <span className="value">{patient.admission?.doctor_id || 'N/A'}</span>
                                            </div>
                                        </div>

                                        <div className="card-footer">
                                            <button
                                                className="btn-confirm"
                                                onClick={() => handleConfirmBed(patient)}
                                                disabled={confirmingBed === patient.patient_id}
                                            >
                                                {confirmingBed === patient.patient_id ? (
                                                    <>
                                                        <span className="spinner"></span> Confirming...
                                                    </>
                                                ) : (
                                                    <>
                                                        ✓ Confirm Bed Assignment
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'all' && (
                    <div className="content-section">
                        <div className="section-header">
                            <div>
                                <h3>All Patients</h3>
                                <p className="subtitle">
                                    {allPatients.length} total patient{allPatients.length !== 1 ? 's' : ''}
                                </p>
                            </div>
                        </div>

                        {loading ? (
                            <div className="loading-state">Loading patients...</div>
                        ) : allPatients.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-icon">📋</div>
                                <h3>No Patients Yet</h3>
                                <p>Register your first patient to get started</p>
                                <button className="btn-primary" onClick={() => navigate('/patients/new')}>
                                    ➕ Register New Patient
                                </button>
                            </div>
                        ) : (
                            <div className="patients-table">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Patient Name</th>
                                            <th>Age/Gender</th>
                                            <th>Status</th>
                                            <th>Bed</th>
                                            <th>Created</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {allPatients.map((patient) => (
                                            <tr key={patient.patient_id}>
                                                <td>
                                                    <strong>{patient.name}</strong>
                                                    <br />
                                                    <small>{patient.patient_id}</small>
                                                </td>
                                                <td>{patient.age}, {patient.gender}</td>
                                                <td>{getStatusBadge(patient.status)}</td>
                                                <td>
                                                    {patient.admission?.confirmed_bed_id ||
                                                     patient.admission?.recommended_bed_id ||
                                                     '-'}
                                                </td>
                                                <td>
                                                    {patient.created_at
                                                        ? new Date(patient.created_at).toLocaleDateString()
                                                        : 'N/A'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default ReceptionistDashboard;
