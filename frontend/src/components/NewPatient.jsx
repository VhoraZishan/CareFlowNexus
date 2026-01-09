import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Layout from './Layout';
import './NewPatient.css';

const NewPatient = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        age: '',
        gender: 'Select Gender',
        phone: '',
        reason: '',
        history: '',
        needs: ''
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

    const toggleDisease = (disease) => {
        setFormData(prev => {
            const currentReason = prev.reason;
            let updated;
            if (currentReason.includes(disease)) {
                updated = currentReason.split(', ').filter(d => d !== disease).join(', ');
            } else {
                updated = currentReason ? `${currentReason}, ${disease}` : disease;
            }
            return { ...prev, reason: updated };
        });
    };

    const getVisibleDiseases = () => {
        if (diseaseSearch) {
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
        return commonDiseases[activeCategory] || [];
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const userStr = localStorage.getItem('user');
            if (!userStr) throw new Error("No active session");
            const user = JSON.parse(userStr);

            // Map form data to API expectation
            const patientPayload = {
                user_id: user.user_id,
                name: formData.name,
                age: parseInt(formData.age, 10),
                gender: formData.gender.toLowerCase(),
                // 'reason' might be mapped to 'diagnosis' or just stored in history for now 
                // as the simple CREATE endpoint doesn't seem to have a dedicated 'reason' field
                // distinct from admission diagnosis. We'll append it to history.
                medical_history: [`${formData.history || ''} \n[Reason for Visit: ${formData.reason}]`],
                special_needs: [formData.needs],
            };

            await api.createPatient(patientPayload);
            navigate('/dashboard');

        } catch (error) {
            console.error('Failed to create patient', error);
            alert('Error creating patient: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout title="New Patient">
            <div className="new-patient-container">
                <div className="breadcrumbs">
                    <span>Patients</span> <span className="separator">/</span> <span className="current">Create New Profile</span>
                </div>

                <div className="page-header">
                    <h1>Create New Patient Profile</h1>
                    <p>Enter patient details to initiate automated resource and room assignment based on availability and medical needs.</p>
                </div>

                <div className="form-card">
                    <form onSubmit={handleSubmit}>
                        <section className="form-section">
                            <div className="section-header">
                                <span className="section-icon user-icon">👤</span>
                                <h3>Basic Information</h3>
                            </div>

                            <div className="form-grid">
                                <div className="form-group col-span-2">
                                    <label>PATIENT FULL NAME</label>
                                    <input
                                        type="text"
                                        name="name"
                                        value={formData.name}
                                        onChange={handleChange}
                                        placeholder="e.g. Jonathan Doe"
                                        className="form-input"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>AGE</label>
                                    <input
                                        type="number"
                                        name="age"
                                        value={formData.age}
                                        onChange={handleChange}
                                        placeholder="Years"
                                        className="form-input"
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>GENDER</label>
                                    <select
                                        name="gender"
                                        value={formData.gender}
                                        onChange={handleChange}
                                        className="form-select"
                                    >
                                        <option disabled>Select Gender</option>
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                <div className="form-group col-span-2-mobile">
                                    <label>PRIMARY PHONE</label>
                                    <input
                                        type="tel"
                                        name="phone"
                                        value={formData.phone}
                                        onChange={handleChange}
                                        placeholder="+1 (555) 000-0000"
                                        className="form-input"
                                    />
                                </div>
                            </div>
                        </section>

                        <div className="section-divider"></div>

                        <section className="form-section">
                            <div className="section-header">
                                <span className="section-icon notes-icon">📋</span>
                                <h3>Clinical Details</h3>
                            </div>

                            <div className="disease-selection-container-new">
                                <div className="selection-navbar-admin">
                                    <label className="input-label-small">QUICK SELECT ADMISSION REASON</label>
                                    <input
                                        type="text"
                                        placeholder="🔍 Search reason..."
                                        className="disease-mini-search-admin"
                                        value={diseaseSearch}
                                        onChange={(e) => setDiseaseSearch(e.target.value)}
                                        disabled={loading}
                                    />
                                </div>

                                {!diseaseSearch && (
                                    <div className="category-tabs-admin">
                                        {Object.keys(commonDiseases).map(cat => (
                                            <button
                                                key={cat}
                                                type="button"
                                                className={`cat-tab-admin ${activeCategory === cat ? 'active' : ''}`}
                                                onClick={() => setActiveCategory(cat)}
                                                disabled={loading}
                                            >
                                                {cat}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                <div className="disease-tag-cloud-admin animate-fade-in">
                                    {getVisibleDiseases().map(disease => (
                                        <button
                                            key={disease}
                                            type="button"
                                            className={`disease-select-tag ${formData.reason.includes(disease) ? 'active' : ''}`}
                                            onClick={() => toggleDisease(disease)}
                                            disabled={loading}
                                        >
                                            {disease}
                                        </button>
                                    ))}
                                    {getVisibleDiseases().length === 0 && (
                                        <p className="no-tags-admin">No matching reasons found.</p>
                                    )}
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group full-width">
                                    <label>FINAL ADMISSION REASON / CURRENT PROBLEM</label>
                                    <textarea
                                        name="reason"
                                        rows="1"
                                        value={formData.reason}
                                        onChange={handleChange}
                                        placeholder="Standardized reason will appear here..."
                                        className="form-textarea auto-height"
                                    ></textarea>
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group full-width">
                                    <label>MEDICAL HISTORY</label>
                                    <textarea
                                        name="history"
                                        rows="3"
                                        value={formData.history}
                                        onChange={handleChange}
                                        placeholder="Briefly describe previous conditions, surgeries, or chronic illnesses..."
                                        className="form-textarea"
                                    ></textarea>
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group full-width">
                                    <label>SPECIAL NEEDS / ALLERGIES</label>
                                    <textarea
                                        name="needs"
                                        rows="2"
                                        value={formData.needs}
                                        onChange={handleChange}
                                        placeholder="Mention any mobility requirements, diet restrictions, or medication allergies..."
                                        className="form-textarea"
                                    ></textarea>
                                </div>
                            </div>
                        </section>

                        <div className="form-footer">
                            <div className="footer-info">
                                <span className="info-icon">ℹ️</span>
                                <span className="info-text">System will auto-assign a room upon submission</span>
                            </div>
                            <div className="footer-buttons">
                                <button type="button" className="btn-cancel" onClick={() => navigate('/dashboard')}>Cancel</button>
                                <button type="submit" className="btn-create" disabled={loading}>
                                    {loading ? 'Creating...' : 'Create Patient & Assign Resources'}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </Layout>
    );
};

export default NewPatient;
