import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import Layout from './Layout';
import './PatientList.css';

const PatientList = () => {
    const [patients, setPatients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPatients = async () => {
            try {
                const userStr = localStorage.getItem('user');
                if (!userStr) throw new Error("No active session");
                const user = JSON.parse(userStr);

                const data = await api.getPatients(user.user_id);
                setPatients(data);
            } catch (err) {
                console.error("Error fetching patients:", err);
                setError("Failed to load patient list.");
            } finally {
                setLoading(false);
            }
        };

        fetchPatients();
    }, []);

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'admitted': return 'status-admitted';
            case 'discharged': return 'status-discharged';
            case 'created': return 'status-new';
            default: return '';
        }
    };

    return (
        <Layout title="Patient Registry">
            <div className="patient-list-container">
                <div className="list-header">
                    <div className="header-content">
                        <h2>All Patients</h2>
                        <p>Manage and monitor all registered patient records.</p>
                    </div>
                    <div className="search-filter">
                        <input type="text" placeholder="Search patients..." className="search-input" />
                    </div>
                </div>

                {error && <div className="error-message">{error}</div>}

                {loading ? (
                    <div className="loading-state">Loading records...</div>
                ) : (
                    <div className="table-responsive">
                        <table className="patient-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Age/Gender</th>
                                    <th>Status</th>
                                    <th>Date Added</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {patients.length > 0 ? (
                                    patients.map((patient) => (
                                        <tr key={patient.patient_id}>
                                            <td className="col-name">
                                                <div className="patient-avatar">
                                                    {patient.name.charAt(0).toUpperCase()}
                                                </div>
                                                <span className="name-text">{patient.name}</span>
                                            </td>
                                            <td>{patient.age} / {patient.gender}</td>
                                            <td>
                                                <span className={`status-badge ${getStatusColor(patient.status)}`}>
                                                    {patient.status || 'Unknown'}
                                                </span>
                                            </td>
                                            <td>
                                                {/* Fallback if created_at is missing or needs formatting */}
                                                {patient.created_at ? new Date(patient.created_at).toLocaleDateString() : 'N/A'}
                                            </td>
                                            <td>
                                                <button className="btn-view">View Details</button>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="5" className="empty-state">No patients found.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default PatientList;
