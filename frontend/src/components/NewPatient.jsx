import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import Layout from "./Layout";
import "./NewPatient.css";

const NewPatient = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    gender: "",
    phone: "",
    medical_history: "",
    reason: "",
    special_needs: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCancel = () => {
    const userStr = localStorage.getItem("user");
    if (!userStr) {
      navigate("/");
      return;
    }
    const user = JSON.parse(userStr);

    // Redirect based on user role
    if (user.role === "receptionist") {
      navigate("/receptionist-dashboard");
    } else if (user.role === "doctor") {
      navigate("/doctor-dashboard");
    } else {
      navigate("/patients");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) {
        alert("You must be logged in to create a patient.");
        navigate("/");
        return;
      }
      const user = JSON.parse(userStr);

      const payload = {
        ...formData,
        user_id: user.user_id,
        age: parseInt(formData.age),
        medical_history: formData.medical_history
          .split(",")
          .map((s) => s.trim()),
        special_needs: formData.special_needs.split(",").map((s) => s.trim()),
      };
      const response = await api.createPatient(payload);

      // Show success message
      alert(
        `✅ Patient Created Successfully!\n\n` +
          `Patient: ${formData.name}\n` +
          `Age: ${formData.age}\n` +
          `Gender: ${formData.gender}\n\n` +
          `Patient ID: ${response.patient_id || "Generated"}\n\n` +
          `The patient is now registered and ready for admission.`,
      );

      // Redirect based on user role
      if (user.role === "receptionist") {
        navigate("/receptionist-dashboard");
      } else if (user.role === "doctor") {
        navigate("/doctor-dashboard");
      } else {
        navigate("/patients");
      }
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="new-patient-flow">
        <nav className="breadcrumb">Patients / Create New Profile</nav>

        <header className="page-header-simple">
          <h1>Create New Patient Profile</h1>
          <p>
            Enter patient details to initiate automated resource and room
            assignment based on availability and medical needs.
          </p>
        </header>

        <div className="form-card-premium">
          <form onSubmit={handleSubmit}>
            <section className="form-section">
              <div className="section-title">
                <span className="icon">👤</span>
                <h3>Basic Information</h3>
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label>PATIENT FULL NAME</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="e.g. Jonathan Doe"
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
                    required
                  />
                </div>
                <div className="form-group">
                  <label>GENDER</label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>PRIMARY PHONE</label>
                  <input
                    type="text"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+1 (555) 000-0000"
                  />
                </div>
              </div>
            </section>

            <section className="form-section">
              <div className="section-title">
                <span className="icon">📂</span>
                <h3>Clinical Details</h3>
              </div>
              <div className="form-group full-width">
                <label>REASON FOR ADMISSION / CURRENT PROBLEM</label>
                <textarea
                  name="reason"
                  value={formData.reason}
                  onChange={handleChange}
                  placeholder="Describe the acute problem or reason for this admission..."
                ></textarea>
              </div>
              <div className="form-group full-width">
                <label>MEDICAL HISTORY</label>
                <textarea
                  name="medical_history"
                  value={formData.medical_history}
                  onChange={handleChange}
                  placeholder="Briefly describe previous conditions, surgeries, or chronic illnesses..."
                ></textarea>
              </div>
              <div className="form-group full-width">
                <label>SPECIAL NEEDS / ALLERGIES</label>
                <textarea
                  name="special_needs"
                  value={formData.special_needs}
                  onChange={handleChange}
                  placeholder="Mention any mobility requirements, diet restrictions, or medication allergies..."
                ></textarea>
              </div>
            </section>

            <div className="form-footer-action">
              <span className="notice"></span>
              <div className="buttons">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={handleCancel}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-submit-action"
                  disabled={loading}
                >
                  ⚡{" "}
                  {loading
                    ? "Creating..."
                    : "Create Patient & Assign Resources"}
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
