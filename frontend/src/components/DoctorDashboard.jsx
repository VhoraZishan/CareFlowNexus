import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import "./DoctorDashboard.css";

const DoctorDashboard = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("my-patients"); // 'my-patients' or 'all-patients'

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) {
        navigate("/");
        return;
      }
      const parsedUser = JSON.parse(userStr);
      setUser(parsedUser);
      const data = await api.getPatients(parsedUser.user_id);
      setPatients(data || []);
    } catch (err) {
      console.error("Failed to load patients", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/");
  };

  const getStatusInfo = (status) => {
    const statusConfig = {
      created: {
        label: "Not Admitted",
        color: "blue",
        icon: "📋",
        description: "Ready for admission",
      },
      pending_confirmation: {
        label: "Pending Bed Confirmation",
        color: "orange",
        icon: "⏳",
        description: "Awaiting receptionist confirmation",
      },
      bed_confirmed: {
        label: "Bed Confirmed",
        color: "purple",
        icon: "🛏️",
        description: "Preparing for admission",
      },
      admitted: {
        label: "Admitted",
        color: "green",
        icon: "✅",
        description: "Patient is admitted and under care",
      },
      discharged: {
        label: "Discharged",
        color: "gray",
        icon: "🏠",
        description: "Patient has been discharged",
      },
    };
    return (
      statusConfig[status] || {
        label: status,
        color: "gray",
        icon: "❓",
        description: "Unknown status",
      }
    );
  };

  const handleRequestDischarge = async (patientId) => {
    const confirmed = window.confirm(
      "Request discharge for this patient?\n\nThis will initiate the discharge process and create post-discharge cleaning tasks.",
    );

    if (!confirmed) return;

    try {
      await api.dischargePatient(patientId, user.user_id);
      alert("✅ Discharge request submitted successfully!");
      await fetchPatients();
    } catch (error) {
      console.error("Failed to request discharge", error);
      alert("❌ Error requesting discharge: " + error.message);
    }
  };

  // Filter patients based on active tab
  const myAdmittedPatients = patients.filter(
    (p) =>
      p.admission?.doctor_id === user?.user_id &&
      (p.status === "pending_confirmation" ||
        p.status === "bed_confirmed" ||
        p.status === "admitted"),
  );

  const allPatients = patients;

  const displayedPatients =
    activeTab === "my-patients" ? myAdmittedPatients : allPatients;

  return (
    <div className="doctor-layout">
      <aside className="doc-sidebar-premium">
        <div className="sidebar-logo">
          <h1>CareFlow Nexus</h1>
          <p className="sidebar-subtitle">MEDICAL STAFF</p>
        </div>

        <nav className="sidebar-nav-premium">
          <button
            className={`nav-btn ${activeTab === "my-patients" ? "active" : ""}`}
            onClick={() => setActiveTab("my-patients")}
          >
            <span className="nav-icon">👨‍⚕️</span> My Admitted Patients
            {myAdmittedPatients.length > 0 && (
              <span className="count-badge">{myAdmittedPatients.length}</span>
            )}
          </button>
          <button
            className={`nav-btn ${activeTab === "all-patients" ? "active" : ""}`}
            onClick={() => setActiveTab("all-patients")}
          >
            <span className="nav-icon">📋</span> All Patients
          </button>
          <button
            className="nav-btn"
            onClick={() => navigate("/patients/doctor-admit")}
          >
            <span className="nav-icon">➕</span> Admit Patient
          </button>
          <button className="nav-btn" onClick={handleLogout}>
            <span className="nav-icon">⏻</span> Logout
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="user-profile-widget">
            <div className="user-avatar-small">
              <img
                src={`https://ui-avatars.com/api/?name=${user?.user_id || "Doctor"}&background=3b82f6&color=fff&bold=true`}
                alt="Avatar"
              />
            </div>
            <div className="user-meta-small">
              <h4>{user?.user_id || "Doctor"}</h4>
              <p className="user-role">Medical Staff</p>
            </div>
          </div>
        </div>
      </aside>

      <main className="doc-main">
        <header className="doc-header">
          <div className="header-left">
            <h2>
              {activeTab === "my-patients"
                ? "My Admitted Patients"
                : "All Patients"}
            </h2>
            <span className="status-badge on-shift">ON SHIFT</span>
          </div>

          <div className="header-right">
            <button
              className="add-patient-btn-header"
              onClick={() => navigate("/patients/doctor-admit")}
            >
              ➕ Admit Patient
            </button>
            <div className="doc-search">
              <span className="search-icon">🔍</span>
              <input type="text" placeholder="Search patients..." />
            </div>
          </div>
        </header>

        <div className="doc-grid-container">
          <div className="content-header-row">
            <div className="title-group">
              <p className="subtitle">
                {displayedPatients.length} patient
                {displayedPatients.length !== 1 ? "s" : ""}
                {activeTab === "my-patients"
                  ? " under your care"
                  : " in the system"}
              </p>
            </div>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading patient records...</p>
            </div>
          ) : displayedPatients.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                {activeTab === "my-patients" ? "👨‍⚕️" : "📋"}
              </div>
              <h3>
                {activeTab === "my-patients"
                  ? "No Admitted Patients"
                  : "No Patients Found"}
              </h3>
              <p>
                {activeTab === "my-patients"
                  ? "You have no patients under your care at the moment."
                  : "No patients have been registered yet."}
              </p>
              <button
                className="btn-primary"
                onClick={() => navigate("/patients/doctor-admit")}
              >
                ➕ Admit New Patient
              </button>
            </div>
          ) : (
            <div className="patient-card-grid">
              {displayedPatients.map((patient) => {
                const statusInfo = getStatusInfo(patient.status);
                return (
                  <div className="patient-item-card" key={patient.patient_id}>
                    <div className="card-header-v2">
                      <span className={`status-pill ${statusInfo.color}`}>
                        {statusInfo.icon} {statusInfo.label}
                      </span>
                    </div>

                    <div className="card-top-main">
                      <div className="patient-basic">
                        <h3>{patient.name}</h3>
                        <span className="age-gender">
                          {patient.age} years, {patient.gender}
                        </span>
                      </div>
                    </div>

                    <div className="card-detail-section">
                      <div className="detail-item">
                        <span className="detail-icon">🆔</span>
                        <div className="detail-text">
                          <label>PATIENT ID</label>
                          <p className="patient-id">{patient.patient_id}</p>
                        </div>
                      </div>

                      {patient.admission?.diagnosis && (
                        <div className="detail-item">
                          <span className="detail-icon">🩺</span>
                          <div className="detail-text">
                            <label>DIAGNOSIS</label>
                            <p>{patient.admission.diagnosis}</p>
                          </div>
                        </div>
                      )}

                      {(patient.admission?.confirmed_bed_id ||
                        patient.admission?.recommended_bed_id) && (
                        <div className="detail-item">
                          <span className="detail-icon">🛏️</span>
                          <div className="detail-text">
                            <label>BED ASSIGNMENT</label>
                            <p>
                              {patient.admission?.confirmed_bed_id ||
                                patient.admission?.recommended_bed_id}
                            </p>
                          </div>
                        </div>
                      )}

                      {patient.medical_history &&
                        patient.medical_history.length > 0 && (
                          <div className="detail-item">
                            <span className="detail-icon">📋</span>
                            <div className="detail-text">
                              <label>MEDICAL HISTORY</label>
                              <p>{patient.medical_history.join(", ")}</p>
                            </div>
                          </div>
                        )}

                      <div className="detail-item status-description">
                        <span className="detail-icon">ℹ️</span>
                        <div className="detail-text">
                          <label>STATUS</label>
                          <p className="status-desc">
                            {statusInfo.description}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="card-actions">
                      {patient.status === "admitted" &&
                        patient.admission?.doctor_id === user?.user_id && (
                          <button
                            className="btn-discharge"
                            onClick={() =>
                              handleRequestDischarge(patient.patient_id)
                            }
                          >
                            📤 Request Discharge
                          </button>
                        )}
                      {patient.status === "created" && (
                        <button
                          className="btn-admit"
                          onClick={() =>
                            navigate("/patients/doctor-admit", {
                              state: { preSelectedPatient: patient },
                            })
                          }
                        >
                          ➕ Admit This Patient
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default DoctorDashboard;
