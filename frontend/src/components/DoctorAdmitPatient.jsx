import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './NewPatient.css'; // Reusing styles for consistency
import './DoctorDashboard.css'; // For layout container if needed

const DoctorAdmitPatient = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        age: '',
        gender: '',
        diagnosis: '',
        notes: ''
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const userStr = localStorage.getItem('user');
            if (!userStr) throw new Error("No active session");
            const user = JSON.parse(userStr);

            // Doctors create patients differently - perhaps directly admitting them?
            // For now, aligning with the existing API structure but tailored for doctor input
            // The backend currently restricts creation to receptionists.
            // We might need to update backend permissions or use a different endpoint.
            // Assuming we reuse createPatient for now but with different UI intent.

            const patientData = {
                user_id: user.user_id,
                name: formData.name,
                age: parseInt(formData.age),
                gender: formData.gender,
                medical_history: [`Diagnosis: ${formData.diagnosis}`, `Notes: ${formData.notes}`],
                special_needs: []
            };

            await api.createPatient(patientData);
            navigate('/doctor-dashboard');
        } catch (error) {
            console.error(error);
            alert("Failed to admit patient. Ensure you have permissions.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="doctor-layout" style={{ justifyContent: 'center', alignItems: 'center', height: '100vh', overflowY: 'auto' }}>
            <div className="form-card" style={{ width: '100%', maxWidth: '600px', padding: '0' }}>
                <div className="form-section">
                    <div className="section-header">
                        <span className="section-icon user-icon">👨‍⚕️</span>
                        <h3>Doctor Admission Form</h3>
                    </div>

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Patient Name</label>
                            <input
                                className="form-input"
                                name="name"
                                placeholder="Patient Name"
                                required
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: '1rem' }}>
                            <div className="form-group" style={{ gridColumn: 'span 1' }}>
                                <label>Age</label>
                                <input
                                    className="form-input"
                                    name="age"
                                    type="number"
                                    placeholder="Age"
                                    required
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="form-group" style={{ gridColumn: 'span 1' }}>
                                <label>Gender</label>
                                <select className="form-select" name="gender" required onChange={handleChange} defaultValue="">
                                    <option value="" disabled>Select</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                </select>
                            </div>
                        </div>
                        <div className="form-group" style={{ marginTop: '1rem' }}>
                            <label>Primary Diagnosis</label>
                            <input
                                className="form-input"
                                name="diagnosis"
                                placeholder="Primary Diagnosis"
                                required
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group" style={{ marginTop: '1rem' }}>
                            <label>Clinical Notes</label>
                            <textarea
                                className="form-textarea"
                                name="notes"
                                placeholder="Initial observation notes..."
                                onChange={handleChange}
                            ></textarea>
                        </div>

                        <div className="form-footer" style={{ marginTop: '2rem', padding: '1rem 0 0 0', background: 'none', borderTop: 'none' }}>
                            <button type="button" className="btn-cancel" onClick={() => navigate('/doctor-dashboard')}>Cancel</button>
                            <button type="submit" className="btn-create" disabled={loading}>
                                {loading ? 'Admitting...' : 'Admit Patient'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default DoctorAdmitPatient;
