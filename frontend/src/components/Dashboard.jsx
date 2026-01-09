import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Layout from './Layout';
import './Dashboard.css';

const Dashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        patients: { value: '-', change: '...', isPositive: true },
        appointments: { value: '-', change: 'Today', isPositive: false },
        doctors: { value: '-', change: 'On Shift', isPositive: false },
        waitTime: { value: '-', change: 'Est.', isPositive: true }
    });
    const [activity, setActivity] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const userStr = localStorage.getItem('user');
                if (!userStr) return;
                const user = JSON.parse(userStr);

                const patients = await api.getPatients(user.user_id).catch(() => []);
                console.log('Patients:', patients);

                // Simple stats calculation based on list
                setStats({
                    patients: { value: patients.length.toString(), change: 'Total', isPositive: true },
                    appointments: { value: '0', change: 'Today', isPositive: false }, // Mocked for now
                    doctors: { value: '8', change: 'Active', isPositive: true },      // Mocked
                    waitTime: { value: '14m', change: 'Avg', isPositive: true }       // Mocked
                });

                // Process recent activity from real patients
                const sortedPatients = [...patients].sort((a, b) =>
                    new Date(b.created_at || 0) - new Date(a.created_at || 0)
                ).slice(0, 5);

                const recentActivities = sortedPatients.map((p, index) => ({
                    id: p.patient_id || index,
                    type: 'admission',
                    title: 'New Patient Registered',
                    desc: `${p.name} (Age: ${p.age})`,
                    time: p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Just now'
                }));

                setActivity(recentActivities.length > 0 ? recentActivities : []);

            } catch (error) {
                console.error('Loader error:', error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    return (
        <Layout
            title="Dashboard Overview"
            actions={
                <>
                    <button className="btn-primary" onClick={() => navigate('/patients/new')}>
                        <span className="btn-icon">➕</span> New Patient
                    </button>
                    <button className="btn-secondary">
                        <span className="btn-icon">🔔</span> Notifications
                    </button>
                </>
            }
        >
            <div className="stats-grid">
                <div className="stat-card" onClick={() => navigate('/patients')} style={{ cursor: 'pointer' }}>
                    <h3>Total Patients</h3>
                    <p className="stat-value">{stats.patients.value}</p>
                    <span className={`stat-change ${stats.patients.isPositive ? 'positive' : ''}`}>{stats.patients.change}</span>
                </div>
                <div className="stat-card">
                    <h3>Appointments</h3>
                    <p className="stat-value">{stats.appointments.value}</p>
                    <span className="stat-change">{stats.appointments.change}</span>
                </div>
                <div className="stat-card">
                    <h3>Active Doctors</h3>
                    <p className="stat-value">{stats.doctors.value}</p>
                    <span className="stat-change">{stats.doctors.change}</span>
                </div>
                <div className="stat-card">
                    <h3>Avg Wait Time</h3>
                    <p className="stat-value">{stats.waitTime.value}</p>
                    <span className="stat-change positive">{stats.waitTime.change}</span>
                </div>
            </div>

            <div className="recent-activity">
                <h2>Recent Activity</h2>
                <div className="activity-list">
                    {activity.map(item => (
                        <div className="activity-item" key={item.id}>
                            <span className="activity-icon">{item.type === 'admission' ? '🏥' : '📅'}</span>
                            <div className="activity-info">
                                <h4>{item.title}</h4>
                                <p>{item.desc}</p>
                            </div>
                            <span className="activity-time">{item.time}</span>
                        </div>
                    ))}
                </div>
            </div>
        </Layout>
    );
};

export default Dashboard;
