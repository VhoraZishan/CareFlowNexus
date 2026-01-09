import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './NurseDashboard.css';

const NurseDashboard = () => {
    const navigate = useNavigate();
    const [patients, setPatients] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState(null);

    useEffect(() => {
        const loadDashboardData = async () => {
            try {
                const userStr = localStorage.getItem('user');
                if (!userStr) {
                    navigate('/');
                    return;
                }
                const userData = JSON.parse(userStr);
                setUser(userData);

                const [patientsData, tasksData] = await Promise.all([
                    api.getPatients(userData.user_id).catch(() => []),
                    api.getTasks(userData.user_id).catch(() => [])
                ]);

                setPatients(patientsData);
                setTasks(tasksData);
            } catch (err) {
                console.error("Dashboard data load error:", err);
            } finally {
                setLoading(false);
            }
        };

        loadDashboardData();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('user');
        navigate('/');
    };

    const handleAcceptTask = async (taskId) => {
        try {
            await api.acceptTask(taskId, user.user_id);
            const updatedTasks = await api.getTasks(user.user_id);
            setTasks(updatedTasks);
        } catch (err) {
            console.error("Accept task error:", err);
        }
    };

    // Filter tasks into Current and Upcoming (Mocked logic for UI demonstration)
    const currentTasks = tasks.filter(t => t.status === 'accepted').slice(0, 3);
    const upcomingTasks = tasks.filter(t => t.status === 'pending');

    return (
        <div className="nurse-app-container">
            {/* Sidebar */}
            <aside className="nurse-sidebar-premium">
                <div className="sidebar-top">
                    <div className="sidebar-logo">
                        <h1>CareFlow Nexus</h1>
                        <p>NURSING UNIT A</p>
                    </div>

                    <nav className="sidebar-nav-premium">
                        <button className="nav-btn active">
                            <span className="nav-icon">📊</span>
                            Task Dashboard
                        </button>
                        <button className="nav-btn">
                            <span className="nav-icon">👥</span>
                            My Patients
                        </button>
                        <button className="nav-btn" style={{ marginTop: 'auto' }}>
                            <span className="nav-icon">⚙️</span>
                            Settings
                        </button>
                        <button className="nav-btn logout-nav-item" onClick={handleLogout} style={{ color: '#ef4444' }}>
                            <span className="nav-icon">⏻</span> Logout
                        </button>
                    </nav>
                </div>

                <div className="sidebar-bottom">
                    <div className="user-profile-widget">
                        <div className="user-avatar-small">
                            <img src={`https://ui-avatars.com/api/?name=${user?.name || 'Nurse'}&background=10b981&color=fff`} alt="Avatar" />
                        </div>
                        <div className="user-meta-small">
                            <h4>{user?.name || 'Nurse Taylor'}</h4>
                            <p>Shift ends 07:00 PM</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Wrapper */}
            <div className="nurse-main-wrapper">
                {/* Header */}
                <header className="nurse-header-premium">
                    <div className="header-title-section">
                        <h2>Nurse Task Management <span className="shift-badge">ON SHIFT</span></h2>
                    </div>

                    <div className="header-actions-premium">
                        <div className="search-box-premium">
                            <span className="search-icon">🔍</span>
                            <input type="text" placeholder="Search patients or tasks..." />
                        </div>
                        <button className="icon-action-btn">🔔</button>
                        <button className="icon-action-btn">💬</button>
                    </div>
                </header>

                {/* Content Grid */}
                <div className="nurse-grid-layout">
                    {/* Left Column: Current Tasks */}
                    <div className="grid-col-tasks">
                        <div className="col-header">
                            <h3>Current Tasks</h3>
                            <span className="active-count-pill">{currentTasks.length} Active</span>
                        </div>

                        <div className="tasks-container-premium">
                            {currentTasks.length === 0 ? (
                                <div className="empty-state-card">
                                    <p>No active tasks. Accept an upcoming task to begin.</p>
                                </div>
                            ) : (
                                currentTasks.map((task, idx) => (
                                    <div className={`current-task-card ${idx === 0 ? 'urgent' : 'normal'}`} key={task.task_id || idx}>
                                        <div className="task-priority-label">
                                            {idx === 0 ? 'URGENT PRIORITY' : 'NORMAL PRIORITY'}
                                        </div>
                                        <div className="task-card-header">
                                            <h4>{task.patient_name || 'Patient'} | Room {task.room || 'N/A'}</h4>
                                            <div className="task-time-meta">
                                                <span>Due {task.time || 'TBD'}</span>
                                            </div>
                                        </div>

                                        <div className="task-inner-box">
                                            <div className="task-icon-box">🩺</div>
                                            <div className="task-info-main">
                                                <h5>{task.title || 'Ongoing Task'}</h5>
                                                <p>{task.description || 'No additional details provided.'}</p>
                                            </div>
                                            <div className="task-status-tag">
                                                <span className="dot"></span> IN PROGRESS
                                            </div>
                                        </div>

                                        <div className="task-card-footer">
                                            <button className="btn-delegate">Delegate</button>
                                            <button className="btn-mark-done">Mark as Done</button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Right Column: Upcoming Queue */}
                    <div className="grid-col-queue">
                        <div className="col-header">
                            <h3>Upcoming Queue</h3>
                            <button className="icon-filter-btn">≡</button>
                        </div>

                        <div className="queue-container-premium">
                            {upcomingTasks.length === 0 ? (
                                <p className="queue-empty">Queue is clear.</p>
                            ) : (
                                upcomingTasks.map((task, idx) => (
                                    <div className="queue-card-premium" key={task.task_id || idx}>
                                        <div className="queue-card-left">
                                            <span className={`priority-badge ${idx === 0 ? 'medium' : 'low'}`}>
                                                {idx === 0 ? 'MEDIUM' : 'LOW'}
                                            </span>
                                            <h4>{task.patient_name || 'Generic Patient'}</h4>
                                            <p>Room {task.room || 'N/A'} • {task.title || 'Task'}</p>
                                            <button className="btn-link">Review Notes</button>
                                        </div>
                                        <div className="queue-card-right">
                                            <div className="queue-time">
                                                <strong>{task.time || 'TBD'}</strong>
                                                <small>{idx === 0 ? 'PROCEED' : 'QUEUED'}</small>
                                            </div>
                                            <button className="btn-accept-task" onClick={() => handleAcceptTask(task.task_id)}>
                                                Accept Task
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NurseDashboard;
