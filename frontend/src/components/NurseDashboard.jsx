import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './NurseDashboard.css';

const NurseDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [tasks, setTasks] = useState([
        { id: 1, patient: 'Robert Chen', room: '302', type: 'Check Vital Signs', details: 'Record BP, SpO2, and Heart Rate.', priority: 'urgent', due: '10:30 AM', current: '10:15 AM', status: 'IN PROGRESS' },
        { id: 2, patient: 'Elena Rodriguez', room: '308', type: 'Pain Medication Delivery', details: 'Administer prescribed IV analgesics.', priority: 'normal', due: '11:00 AM', status: 'READY' }
    ]);
    const [queue, setQueue] = useState([
        { id: 3, patient: 'Sarah Miller', room: '305', type: 'Medication', priority: 'medium', due: '11:15 AM', timeMeta: 'IN 1HR' },
        { id: 4, patient: 'James Wilson', room: '310', type: 'Wound Dressing', priority: 'low', due: '12:00 PM', timeMeta: 'LATER' },
        { id: 5, patient: 'Linda Gray', room: '312', type: 'Post-Op Check', priority: 'normal', due: '01:30 PM', timeMeta: 'AFTERNOON' }
    ]);

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (!userStr) { navigate('/'); return; }
        setUser(JSON.parse(userStr));
    }, [navigate]);

    return (
        <div className="nurse-layout-premium">
            <aside className="nurse-sidebar">
                <div className="sidebar-brand">
                    <h1>CareFlow Nexus</h1>
                    <p>NURSING UNIT A</p>
                </div>

                <nav className="nurse-nav">
                    <button className="n-nav-btn active">
                        <span className="icon">⊞</span> Task Dashboard
                    </button>
                    <button className="n-nav-btn">
                        <span className="icon">👥</span> My Patients
                    </button>
                </nav>

                <div className="sidebar-bottom-profile">
                    <div className="profile-card">
                        <div className="avatar">
                            <img src={`https://ui-avatars.com/api/?name=Nurse+Taylor&background=10b981&color=fff&bold=true`} alt="Nurse" />
                        </div>
                        <div className="meta">
                            <h4>Nurse Taylor</h4>
                            <p>Shift ends 07:00 PM</p>
                        </div>
                        <button className="logout-btn" onClick={() => { localStorage.removeItem('user'); navigate('/'); }}>
                            ➔
                        </button>
                    </div>
                </div>
            </aside>

            <main className="nurse-content">
                <header className="nurse-header">
                    <div className="header-left">
                        <h2>Nurse Task Management</h2>
                        <span className="shift-badge">ON SHIFT</span>
                    </div>
                    <div className="header-right">
                        <div className="search-pill">
                            <span>🔍</span>
                            <input type="text" placeholder="Search patients or tasks..." />
                        </div>
                        <button className="icon-btn">🔔</button>
                        <button className="icon-btn">💬</button>
                    </div>
                </header>

                <div className="dashboard-columns">
                    {/* Left Column: Current Tasks */}
                    <div className="col-current">
                        <div className="col-header">
                            <h3>Current Tasks</h3>
                            <span className="count-tag">3 Active</span>
                        </div>

                        <div className="task-stack-main">
                            {tasks.map(task => (
                                <div key={task.id} className={`task-card-large ${task.priority}`}>
                                    <div className="card-top-row">
                                        <div className="priority-text">
                                            {task.priority.toUpperCase()} PRIORITY
                                        </div>
                                        <div className="time-text">
                                            <strong>Due {task.due}</strong>
                                            {task.current && <span className="sub-time">Current: {task.current}</span>}
                                            {!task.current && <span className="sub-time">Scheduled</span>}
                                        </div>
                                    </div>

                                    <div className="patient-header">
                                        <h3>{task.patient} <span className="divider">|</span> Room {task.room}</h3>
                                    </div>

                                    <div className="task-detail-box">
                                        <div className="icon-box">
                                            {task.type.includes('Vital') ? '📈' : '💊'}
                                        </div>
                                        <div className="detail-text">
                                            <h5>{task.type}</h5>
                                            <p>{task.details}</p>
                                        </div>
                                        <div className="status-pill-right">
                                            {task.status === 'IN PROGRESS' ? '◉ IN PROGRESS' : '🕒 READY'}
                                        </div>
                                    </div>

                                    <div className="action-row">
                                        {task.status === 'IN PROGRESS' ? (
                                            <>
                                                <button className="btn-white">Delegate</button>
                                                <button className="btn-blue">Mark as Done</button>
                                            </>
                                        ) : (
                                            <button className="btn-blue full">Start Task</button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Right Column: Queue */}
                    <div className="col-queue">
                        <div className="col-header">
                            <h3>Upcoming Queue</h3>
                            <button className="filter-icon">≡</button>
                        </div>

                        <div className="queue-list">
                            {queue.map(q => (
                                <div key={q.id} className="queue-card">
                                    <div className="q-top">
                                        <span className={`q-tag ${q.priority}`}>{q.priority.toUpperCase()}</span>
                                        <div className="q-time">
                                            <strong>{q.due}</strong>
                                            <span>{q.timeMeta}</span>
                                        </div>
                                    </div>
                                    <div className="q-main">
                                        <h4>{q.patient}</h4>
                                        <p>Room {q.room} • {q.type}</p>
                                    </div>
                                    <div className="q-actions">
                                        <button className="link-text">Review Notes</button>
                                        <button className="outline-btn">Accept Task</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default NurseDashboard;
