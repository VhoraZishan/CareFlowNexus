import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import NewPatient from './components/NewPatient';
import PatientList from './components/PatientList';
import DoctorDashboard from './components/DoctorDashboard';
import DoctorAdmitPatient from './components/DoctorAdmitPatient';
import PatientDetails from './components/PatientDetails';
import NurseDashboard from './components/NurseDashboard';
import CleanerDashboard from './components/CleanerDashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/patients/new" element={<NewPatient />} />
        <Route path="/patients" element={<PatientList />} />
        <Route path="/doctor-dashboard" element={<DoctorDashboard />} />
        <Route path="/nurse-dashboard" element={<NurseDashboard />} />
        <Route path="/cleaner-dashboard" element={<CleanerDashboard />} />
        <Route path="/patients/doctor-admit" element={<DoctorAdmitPatient />} />
        <Route path="/patients/details" element={<PatientDetails />} />
        {/* Redirect unknown routes to login for now */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
