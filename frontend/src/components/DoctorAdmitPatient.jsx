import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Layout from './Layout';
import './DoctorAdmitPatient.css';

const DoctorAdmitPatient = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [fetchingPatients, setFetchingPatients] = useState(true);
    const [patients, setPatients] = useState([]);
    const [selectedPatientId, setSelectedPatientId] = useState('');
    const [selectedPatient, setSelectedPatient] = useState(null);
    const [user, setUser] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const [admissionData, setAdmissionData] = useState({
        diagnosis: '',
        special_instructions: ''
    });

    const commonDiseases = {
        "Cardiac": ["Hypertension", "Heart Failure", "Myocardial Infarction", "Atrial Fibrillation", "Angina", "Arrhythmia"],
        "Respiratory": ["Pneumonia", "Asthma", "COPD", "COVID-19", "Pulmonary Embolism", "Bronchitis", "Tuberculosis"],
        "Neurology": ["Stroke", "Seizure", "Migraine", "Parkinson's", "Alzheimer's", "Encephalopathy", "Meningitis"],
        "Infectious": ["Sepsis", "Dengue", "Malaria", "Typhoid", "Gastroenteritis", "UTI", "Hepatitis", "Influenza"],
        "Metabolic/Endo": ["Diabetes Type 1", "Diabetes Type 2", "Hypothyroidism", "Dehydration", "Ketoacidosis"],
        "Gastro": ["Gastritis", "Appendicitis", "Pancreatitis", "Cholecystitis", "Cirrhosis", "Crohn's Disease"],
        "Orthopedic": ["Fracture", "Osteoarthritis", "Gout", "Rheumatoid Arthritis", "Disk Herniation"],
        "Nephrology": ["Acute Renal Failure", "Chronic Kidney Disease", "Kidney Stones", "Nephrotic Syndrome"],
        "Oncology": ["Leukemia", "Lymphoma", "Breast Cancer", "Lung Cancer", "Colon Cancer"],
        "Psychiatry": ["Depression", "Anxiety", "Schizophrenia", "Bipolar Disorder"],
        "General/Surgical": ["Post-Op Recovery", "Abscess", "Laceration", "Hernia", "Acute Pain"]
    };

    const [activeCategory, setActiveCategory] = useState("Cardiac");
    const [diseaseSearch, setDiseaseSearch] = useState("");

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (!userStr) {
            navigate('/');
            return;
        }
        const currentUser = JSON.parse(userStr);
        setUser(currentUser);

        const fetchPatients = async () => {
            try {
                const data = await api.getPatients(currentUser.user_id);
                // Only show patients who are registered ("created") but not yet admitted
                const availablePatients = data.filter(p => p.status === 'created');
                setPatients(availablePatients);
            } catch (err) {
                console.error("Failed to load patients", err);
            } finally {
                setFetchingPatients(false);
            }
        };

        fetchPatients();
    }, [navigate]);

    const toggleDisease = (disease) => {
        setAdmissionData(prev => {
            const currentDiagnosis = prev.diagnosis;
            if (currentDiagnosis.includes(disease)) {
                // Remove if already exists
                const updated = currentDiagnosis.split(', ').filter(d => d !== disease).join(', ');
                return { ...prev, diagnosis: updated };
            } else {
                // Add new
                const updated = currentDiagnosis ? `${currentDiagnosis}, ${disease}` : disease;
                return { ...prev, diagnosis: updated };
            }
        });
    };

    // Filter diseases based on search term
    const getVisibleDiseases = () => {
        if (diseaseSearch) {
            // If searching, search across all categories
            const allResults = [];
            Object.values(commonDiseases).forEach(list => {
                list.forEach(d => {
                    if (d.toLowerCase().includes(diseaseSearch.toLowerCase())) {
                        allResults.push(d);
                    }
                });
            });
            return allResults;
        }
        // Otherwise return active category
        return commonDiseases[activeCategory] || [];
    };

    const filteredPatients = patients.filter(p =>
        (p.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
        (p.patient_id?.toLowerCase() || '').includes(searchTerm.toLowerCase())
    );

    const handlePatientChange = (e) => {
        const patientId = e.target.value;
        setSelectedPatientId(patientId);
        const patient = patients.find(p => p.patient_id === patientId);
        setSelectedPatient(patient || null);
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setAdmissionData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedPatientId) {
            alert("Please select a patient first.");
            return;
        }
        setLoading(true);

        try {
            await api.admitPatient(selectedPatientId, {
                user_id: user.user_id,
                diagnosis: admissionData.diagnosis,
                special_instructions: admissionData.special_instructions
            });
            navigate('/doctor-dashboard');
        } catch (error) {
            console.error('Failed to admit patient', error);
            alert('Error admitting patient: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="doctor-layout">
            <aside className="doc-sidebar-premium">
                <div className="sidebar-logo">
                    <h1>CareFlow Nexus</h1>
                    <p>Doctor Portal</p>
                </div>

                <nav className="sidebar-nav-premium">
                    <button className="nav-btn" onClick={() => navigate('/doctor-dashboard')}>
                        Dashboard
                    </button>
                    <button className="nav-btn active" onClick={() => navigate('/patients/doctor-admit')}>
                        Add Patient
                    </button>
                    <button className="nav-btn" onClick={() => {
                        localStorage.removeItem('user');
                        navigate('/');
                    }}>
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
                        <button className="logout-icon-btn" onClick={() => {
                            localStorage.removeItem('user');
                            navigate('/');
                        }} title="Logout">
                            <span>⏻</span>
                        </button>
                    </div>
                </div>
            </aside>

            <main className="doc-main">
                <header className="doc-header">
                    <div className="header-left">
                        <h2>Dr. {user?.name || user?.user_id}</h2>
                        <span className="status-badge">ADMISSION MODE</span>
                    </div>

                    <div className="header-right">
                        <button className="notification-btn">🔔</button>
                    </div>
                </header>

                <div className="doc-content-scrollable">
                    <div className="admit-patient-container">
                        <div className="premium-card">
                            <div className="card-header">
                                <h2>Admit Registered Patient</h2>
                                <p>Search for an existing patient record to initiate the admission process.</p>
                            </div>

                            <form onSubmit={handleSubmit}>
                                <div className="search-section">
                                    <label className="input-label">SEARCH PATIENT BY NAME OR ID</label>
                                    <div className="search-wrapper-premium">
                                        <input
                                            type="text"
                                            placeholder="Type Name (e.g. Jonathan) or ID..."
                                            className="premium-input search-bar-enhanced"
                                            value={searchTerm}
                                            onChange={(e) => {
                                                setSearchTerm(e.target.value);
                                                // Reset selection if they keep typing
                                                if (selectedPatientId) {
                                                    setSelectedPatientId('');
                                                    setSelectedPatient(null);
                                                }
                                            }}
                                            disabled={loading || fetchingPatients}
                                        />

                                        {searchTerm && !selectedPatient && (
                                            <div className="recommendations-list animate-slide-down">
                                                {filteredPatients.length > 0 ? (
                                                    filteredPatients.map(p => (
                                                        <div
                                                            key={p.patient_id}
                                                            className="recommendation-item"
                                                            onClick={() => {
                                                                setSelectedPatientId(p.patient_id);
                                                                setSelectedPatient(p);
                                                                setSearchTerm(p.name);
                                                            }}
                                                        >
                                                            <div className="rec-info">
                                                                <span className="rec-name">{p.name}</span>
                                                                <span className="rec-id">ID: {p.patient_id.substring(0, 8)}</span>
                                                            </div>
                                                            <span className="rec-action">Select</span>
                                                        </div>
                                                    ))
                                                ) : (
                                                    <div className="recommendation-empty">
                                                        No patients found matching "{searchTerm}"
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        {fetchingPatients && <span className="loader-small"></span>}
                                    </div>
                                </div>

                                {selectedPatient && (
                                    <div className="patient-info-display animate-fade-in">
                                        <div className="selected-badge">✓ PATIENT SELECTED</div>
                                        <div className="info-grid">
                                            <div className="info-item full-width">
                                                <label>Patient ID (Auto-filled)</label>
                                                <input
                                                    type="text"
                                                    className="premium-input readonly-field"
                                                    value={selectedPatient.patient_id}
                                                    readOnly
                                                />
                                            </div>
                                            <div className="info-item">
                                                <label>Full Name</label>
                                                <p>{selectedPatient.name}</p>
                                            </div>
                                            <div className="info-item">
                                                <label>Age / Gender</label>
                                                <p>{selectedPatient.age} / {selectedPatient.gender}</p>
                                            </div>
                                            <div className="info-item full-width">
                                                <label>Medical History</label>
                                                <p>{selectedPatient.medical_history?.join(', ') || 'None reported'}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div className="admission-details-section">
                                    <div className="disease-selection-container">
                                        <div className="selection-navbar">
                                            <label className="input-label">QUICK SELECT DIAGNOSIS</label>
                                            <input
                                                type="text"
                                                placeholder="🔍 Fast Search Disease..."
                                                className="disease-mini-search"
                                                value={diseaseSearch}
                                                onChange={(e) => setDiseaseSearch(e.target.value)}
                                                disabled={!selectedPatient || loading}
                                            />
                                        </div>

                                        {!diseaseSearch && (
                                            <div className="category-tabs">
                                                {Object.keys(commonDiseases).map(cat => (
                                                    <button
                                                        key={cat}
                                                        type="button"
                                                        className={`cat-tab ${activeCategory === cat ? 'active' : ''}`}
                                                        onClick={() => setActiveCategory(cat)}
                                                        disabled={!selectedPatient || loading}
                                                    >
                                                        {cat}
                                                    </button>
                                                ))}
                                            </div>
                                        )}

                                        <div className="filtered-tags-area animate-fade-in">
                                            <div className="disease-tags">
                                                {getVisibleDiseases().map(disease => {
                                                    // Improved active check
                                                    const currentTerms = admissionData.diagnosis.split(',').map(t => t.trim());
                                                    const isActive = currentTerms.includes(disease);

                                                    return (
                                                        <button
                                                            key={disease}
                                                            type="button"
                                                            className={`disease-tag ${isActive ? 'active' : ''}`}
                                                            onClick={() => {
                                                                // Improved toggle logic
                                                                setAdmissionData(prev => {
                                                                    let terms = prev.diagnosis.split(',').map(t => t.trim()).filter(Boolean);
                                                                    if (terms.includes(disease)) {
                                                                        terms = terms.filter(t => t !== disease);
                                                                    } else {
                                                                        terms.push(disease);
                                                                    }
                                                                    return { ...prev, diagnosis: terms.join(', ') };
                                                                });
                                                            }}
                                                            disabled={!selectedPatient || loading}
                                                        >
                                                            {disease}
                                                        </button>
                                                    );
                                                })}
                                                {getVisibleDiseases().length === 0 && (
                                                    <p className="no-tags">No matching medical conditions found.</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">FINAL DIAGNOSIS & CLINICAL NOTES</label>
                                        <textarea
                                            name="diagnosis"
                                            value={admissionData.diagnosis}
                                            onChange={handleInputChange}
                                            placeholder="Standardized diagnosis will appear here..."
                                            rows="1"
                                            className="premium-textarea auto-height"
                                            required
                                            disabled={!selectedPatient || loading}
                                        ></textarea>
                                    </div>

                                    <div className="form-group">
                                        <label className="input-label">SPECIAL INSTRUCTIONS</label>
                                        <textarea
                                            name="special_instructions"
                                            value={admissionData.special_instructions}
                                            onChange={handleInputChange}
                                            placeholder="Any specific care instructions for nursing staff?"
                                            rows="2"
                                            className="premium-textarea"
                                            disabled={!selectedPatient || loading}
                                        ></textarea>
                                    </div>
                                </div>

                                <div className="action-footer">
                                    <button
                                        type="button"
                                        className="btn-secondary"
                                        onClick={() => navigate('/doctor-dashboard')}
                                        disabled={loading}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="btn-primary"
                                        disabled={!selectedPatient || loading}
                                    >
                                        {loading ? 'Processing Admission...' : 'Confirm Admission'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DoctorAdmitPatient;
