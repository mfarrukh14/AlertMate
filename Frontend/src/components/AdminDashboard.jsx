import React, { useState, useEffect, useRef } from 'react';
import { adminService } from '../services/api';
import './AdminDashboard.css';

const AdminDashboard = () => {
    const [stats, setStats] = useState({});
    const [queueTasks, setQueueTasks] = useState([]);
    const [recentActivity, setRecentActivity] = useState([]);
    const [dispatchLocations, setDispatchLocations] = useState([]);
    const [serviceDistribution, setServiceDistribution] = useState({});
    const mapRef = useRef(null);
    const leafletMapRef = useRef(null);
    const markersRef = useRef([]);

    useEffect(() => {
        loadDashboardData();
        
        // Refresh data every 30 seconds
        const interval = setInterval(loadDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        // Initialize map even if no dispatch locations
        initializeMap();
    }, [dispatchLocations]);

    const loadDashboardData = async () => {
        try {
            console.log('Loading dashboard data...');
            const [
                statsResponse,
                queueResponse,
                activityResponse,
                locationsResponse,
                distributionResponse
            ] = await Promise.all([
                adminService.getStats(),
                adminService.getQueue(),
                adminService.getActivity(),
                adminService.getDispatchLocations(),
                adminService.getServiceDistribution()
            ]);

            console.log('API Responses:', {
                stats: statsResponse.data,
                queue: queueResponse.data,
                activity: activityResponse.data,
                locations: locationsResponse.data,
                distribution: distributionResponse.data
            });

            setStats(statsResponse.data);
            setQueueTasks(queueResponse.data);
            setRecentActivity(activityResponse.data);
            setDispatchLocations(locationsResponse.data);
            setServiceDistribution(distributionResponse.data);
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            if (error.response) {
                console.error('Error response:', error.response.status, error.response.data);
            }
        }
    };

    const initializeMap = () => {
        if (!window.L || !mapRef.current) return;

        // Clear existing map
        if (leafletMapRef.current) {
            leafletMapRef.current.remove();
        }

        // Clear existing markers
        markersRef.current = [];

        // Create new map centered on Pakistan
        leafletMapRef.current = window.L.map(mapRef.current).setView([30.3753, 69.3451], 6);

        // Add tile layer
        window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(leafletMapRef.current);

        // Static service locations to always show
        const staticLocations = [
            { name: "Karachi Medical Centers", lat: 24.8607, lon: 67.0011, service: "medical" },
            { name: "Lahore Police HQ", lat: 31.5204, lon: 74.3587, service: "police" },
            { name: "Islamabad Emergency Center", lat: 33.6844, lon: 73.0479, service: "disaster" },
            { name: "Faisalabad General Hospital", lat: 31.4504, lon: 73.1350, service: "medical" },
        ];

        const serviceColors = {
            medical: '#ef4444',
            police: '#f59e0b', 
            disaster: '#dc2626',
            general: '#6b7280'
        };

        // Add static service location markers (smaller, non-flashing)
        staticLocations.forEach(location => {
            const marker = window.L.marker([location.lat, location.lon])
                .addTo(leafletMapRef.current);

            const color = serviceColors[location.service] || '#6b7280';
            const icon = window.L.divIcon({
                className: 'service-marker',
                html: `<div class="marker-dot static" style="background-color: ${color}"></div>`,
                iconSize: [12, 12],
                iconAnchor: [6, 6]
            });

            marker.setIcon(icon);
            marker.bindPopup(`
                <div class="marker-popup">
                    <strong>${location.service.toUpperCase()} SERVICE</strong><br>
                    ${location.name}
                </div>
            `);

            markersRef.current.push(marker);
        });

        // Add dispatch markers (larger, flashing)
        dispatchLocations.forEach(location => {
            const marker = window.L.marker([location.latitude, location.longitude])
                .addTo(leafletMapRef.current);

            const color = serviceColors[location.service] || '#6b7280';
            const icon = window.L.divIcon({
                className: 'dispatch-marker',
                html: `<div class="marker-dot flashing" style="background-color: ${color}"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            marker.setIcon(icon);
            marker.bindPopup(`
                <div class="marker-popup">
                    <strong>ACTIVE ${location.service.toUpperCase()} DISPATCH</strong><br>
                    User: ${location.user_name}<br>
                    City: ${location.city}<br>
                    Time: ${new Date(location.created_at).toLocaleString()}
                </div>
            `);

            markersRef.current.push(marker);
        });
    };

    const formatTimeAgo = (timestamp) => {
        const minutes = Math.floor((Date.now() - new Date(timestamp)) / 60000);
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    };

    const activityIcons = {
        medical: '🏥',
        police: '🚔',
        disaster: '🌪️',
        user: '👤',
        system: '⚙️'
    };

    return (
        <div className="admin-dashboard">
            <div className="dashboard-header">
                <h1>Admin Dashboard</h1>
                <button onClick={loadDashboardData} className="refresh-btn">
                    Refresh Data
                </button>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-value">{stats.total_users || 0}</div>
                    <div className="stat-label">Total Users</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{stats.active_tasks || 0}</div>
                    <div className="stat-label">Active Tasks</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{stats.resolved_today || 0}</div>
                    <div className="stat-label">Resolved Today</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{stats.total_events || 0}</div>
                    <div className="stat-label">Total Events</div>
                </div>
            </div>

            <div className="dashboard-content">
                {/* Dispatch Map */}
                <div className="dashboard-section map-section">
                    <h2>Live Dispatch Map</h2>
                    <div ref={mapRef} className="dispatch-map"></div>
                </div>

                {/* Active Queue */}
                <div className="dashboard-section">
                    <h2>Active Queue ({queueTasks.length})</h2>
                    <div className="queue-container">
                        {queueTasks.length === 0 ? (
                            <div className="empty-state">No active tasks in queue</div>
                        ) : (
                            queueTasks.map(task => (
                                <div key={task.id} className="queue-item">
                                    <div className="queue-header">
                                        <span className={`queue-service ${task.service}`}>
                                            {task.service.toUpperCase()}
                                        </span>
                                        <span className={`queue-priority priority-${task.priority}`}>
                                            P{task.priority}
                                        </span>
                                    </div>
                                    <div className="queue-time">
                                        {formatTimeAgo(task.created_at)} • {task.user_location}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="dashboard-section">
                    <h2>Recent Activity</h2>
                    <div className="activity-container">
                        {recentActivity.length === 0 ? (
                            <div className="empty-state">No recent activity</div>
                        ) : (
                            recentActivity.slice(0, 10).map((activity, index) => (
                                <div key={index} className="activity-item">
                                    <div className={`activity-icon ${activity.type}`}>
                                        {activityIcons[activity.type] || '📋'}
                                    </div>
                                    <div className="activity-content">
                                        <div className="activity-text">{activity.message}</div>
                                        <div className="activity-time">
                                            {formatTimeAgo(activity.timestamp)}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Service Distribution Chart */}
                <div className="dashboard-section">
                    <h2>Service Distribution</h2>
                    <div className="service-chart">
                        {['medical', 'police', 'disaster', 'general'].map(service => {
                            const count = serviceDistribution[service] || 0;
                            const maxValue = Math.max(...Object.values(serviceDistribution), 1);
                            const height = (count / maxValue * 80) + 20;
                            
                            return (
                                <div key={service} className="chart-bar" style={{ height: `${height}%` }}>
                                    <div className="chart-value">{count}</div>
                                    <div className="chart-label">{service}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;