"""HTML templates for the AlertMate frontend."""

def get_login_signup_page() -> str:
    """Return the login/signup page HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AlertMate - Login & Signup</title>
    <style>
        :root {
            color-scheme: light dark;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
            color: #e2e8f0;
            min-height: 100vh;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 2rem;
        }
        
        .container {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 20px;
            padding: 2.5rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 25px 50px rgba(15, 23, 42, 0.5);
            width: 100%;
            max-width: 480px;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #3b82f6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }
        
        .logo p {
            color: #94a3b8;
            font-size: 1rem;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 2rem;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            padding: 4px;
        }
        
        .tab {
            flex: 1;
            padding: 0.75rem 1rem;
            text-align: center;
            background: none;
            border: none;
            color: #94a3b8;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s ease;
            font-weight: 500;
        }
        
        .tab.active {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: white;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        
        .form-container {
            position: relative;
            min-height: 500px;
        }
        
        .form {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            pointer-events: none;
        }
        
        .form.active {
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            font-size: 0.9rem;
            font-weight: 600;
            color: #cbd5e1;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        input, select {
            width: 100%;
            padding: 0.875rem 1rem;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.3);
            background: rgba(15, 23, 42, 0.7);
            color: #e2e8f0;
            font-size: 1rem;
            transition: all 0.2s ease;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
        }
        
        .location-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .submit-btn {
            width: 100%;
            padding: 1rem;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-top: 1rem;
        }
        
        .submit-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.4);
        }
        
        .submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .error {
            color: #ef4444;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(239, 68, 68, 0.2);
        }
        
        .success {
            color: #10b981;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: rgba(16, 185, 129, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .location-btn {
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #60a5fa;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }
        
        .location-btn:hover {
            background: rgba(59, 130, 246, 0.3);
            border-color: rgba(59, 130, 246, 0.6);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>🚨 AlertMate</h1>
            <p>Emergency Response System</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('login')">Login</button>
            <button class="tab" onclick="switchTab('signup')">Sign Up</button>
        </div>
        
        <div class="form-container">
            <!-- Login Form -->
            <form class="form active" id="login-form" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label for="login-email">Email</label>
                    <input type="email" id="login-email" name="email" required placeholder="your.email@example.com">
                </div>
                
                <div class="form-group">
                    <label for="login-password">Password</label>
                    <input type="password" id="login-password" name="password" required placeholder="Enter your password">
                </div>
                
                <button type="submit" class="submit-btn" id="login-btn">
                    <span class="btn-text">Log In</span>
                </button>
                
                <div id="login-message"></div>
            </form>
            
            <!-- Signup Form -->
            <form class="form" id="signup-form" onsubmit="handleSignup(event)">
                <div class="form-group">
                    <label for="signup-name">Full Name</label>
                    <input type="text" id="signup-name" name="name" required placeholder="John Doe">
                </div>
                
                <div class="form-group">
                    <label for="signup-email">Email</label>
                    <input type="email" id="signup-email" name="email" required placeholder="your.email@example.com">
                </div>
                
                <div class="form-group">
                    <label for="signup-password">Password</label>
                    <input type="password" id="signup-password" name="password" required placeholder="Min 8 characters">
                </div>
                
                <div class="form-group">
                    <label for="signup-phone">Phone Number</label>
                    <input type="tel" id="signup-phone" name="phone_number" required placeholder="+92 300 1234567">
                </div>
                
                <div class="form-group">
                    <label for="signup-cnic">CNIC</label>
                    <input type="text" id="signup-cnic" name="cnic" required placeholder="12345-6789012-3" pattern="[0-9]{5}-[0-9]{7}-[0-9]{1}">
                </div>
                
                <div class="form-group">
                    <label for="signup-blood-group">Blood Group</label>
                    <select id="signup-blood-group" name="blood_group" required>
                        <option value="">Select blood group</option>
                        <option value="A+">A+</option>
                        <option value="A-">A-</option>
                        <option value="B+">B+</option>
                        <option value="B-">B-</option>
                        <option value="AB+">AB+</option>
                        <option value="AB-">AB-</option>
                        <option value="O+">O+</option>
                        <option value="O-">O-</option>
                    </select>
                </div>
                
                <button type="button" class="location-btn" onclick="getCurrentLocation()">
                    📍 Get Current Location
                </button>
                
                <div class="location-group">
                    <div class="form-group">
                        <label for="signup-lat">Latitude</label>
                        <input type="number" id="signup-lat" name="lat" step="any" placeholder="24.8607" required>
                    </div>
                    <div class="form-group">
                        <label for="signup-lon">Longitude</label>
                        <input type="number" id="signup-lon" name="lon" step="any" placeholder="67.0011" required>
                    </div>
                </div>
                
                <button type="submit" class="submit-btn" id="signup-btn">
                    <span class="btn-text">Create Account</span>
                </button>
                
                <div id="signup-message"></div>
            </form>
        </div>
    </div>
    
    <script>
        function switchTab(tab) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`[onclick="switchTab('${tab}')"]`).classList.add('active');
            
            // Update forms
            document.querySelectorAll('.form').forEach(f => f.classList.remove('active'));
            document.getElementById(`${tab}-form`).classList.add('active');
            
            // Clear messages
            document.getElementById('login-message').innerHTML = '';
            document.getElementById('signup-message').innerHTML = '';
        }
        
        function showMessage(elementId, message, isError = false) {
            const element = document.getElementById(elementId);
            element.innerHTML = `<div class="${isError ? 'error' : 'success'}">${message}</div>`;
        }
        
        function setButtonLoading(buttonId, isLoading) {
            const button = document.getElementById(buttonId);
            const textSpan = button.querySelector('.btn-text');
            
            if (isLoading) {
                button.disabled = true;
                textSpan.innerHTML = '<span class="loading"></span> Processing...';
            } else {
                button.disabled = false;
                textSpan.innerHTML = buttonId === 'login-btn' ? 'Log In' : 'Create Account';
            }
        }
        
        async function handleLogin(event) {
            event.preventDefault();
            setButtonLoading('login-btn', true);
            
            const formData = new FormData(event.target);
            const data = {
                email: formData.get('email'),
                password: formData.get('password')
            };
            
            try {
                const response = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage('login-message', 'Login successful! Redirecting to chat...', false);
                    setTimeout(() => window.location.href = '/chat', 1500);
                } else {
                    console.error('Login failed:', response.status, result);
                    showMessage('login-message', result.detail || 'Login failed', true);
                }
            } catch (error) {
                showMessage('login-message', 'Network error. Please try again.', true);
            } finally {
                setButtonLoading('login-btn', false);
            }
        }
        
        async function handleSignup(event) {
            event.preventDefault();
            setButtonLoading('signup-btn', true);
            
            const formData = new FormData(event.target);
            const data = {
                name: formData.get('name'),
                email: formData.get('email'),
                password: formData.get('password'),
                phone_number: formData.get('phone_number'),
                cnic: formData.get('cnic'),
                blood_group: formData.get('blood_group'),
                lat: parseFloat(formData.get('lat')),
                lon: parseFloat(formData.get('lon'))
            };
            
            try {
                const response = await fetch('/api/v1/auth/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage('signup-message', 'Account created successfully! Redirecting to chat...', false);
                    setTimeout(() => window.location.href = '/chat', 1500);
                } else {
                    console.error('Signup failed:', response.status, result);
                    showMessage('signup-message', result.detail || 'Signup failed', true);
                }
            } catch (error) {
                showMessage('signup-message', 'Network error. Please try again.', true);
            } finally {
                setButtonLoading('signup-btn', false);
            }
        }
        
        function getCurrentLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        document.getElementById('signup-lat').value = position.coords.latitude.toFixed(6);
                        document.getElementById('signup-lon').value = position.coords.longitude.toFixed(6);
                        showMessage('signup-message', 'Location detected successfully!', false);
                    },
                    (error) => {
                        showMessage('signup-message', 'Could not get location. Please enter manually.', true);
                    }
                );
            } else {
                showMessage('signup-message', 'Geolocation not supported. Please enter manually.', true);
            }
        }
        
        // Format CNIC input
        document.getElementById('signup-cnic').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            if (value.length >= 5) {
                value = value.substring(0, 5) + '-' + value.substring(5);
            }
            if (value.length >= 13) {
                value = value.substring(0, 13) + '-' + value.substring(13, 14);
            }
            e.target.value = value;
        });
    </script>
</body>
</html>
"""


def get_chat_page() -> str:
    """Return the authenticated chat page HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content=\"width=device-width, initial-scale=1\" />
    <title>AlertMate - Emergency Chat</title>
    <style>
        :root {
            color-scheme: light dark;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        .header {
            padding: 1.5rem 2rem;
            background: linear-gradient(135deg, #1d4ed8, #0ea5e9);
            color: #f8fafc;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.35);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logout-btn {
            background: rgba(248, 250, 252, 0.2);
            border: 1px solid rgba(248, 250, 252, 0.3);
            color: #f8fafc;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }
        
        .logout-btn:hover {
            background: rgba(248, 250, 252, 0.3);
            border-color: rgba(248, 250, 252, 0.5);
        }
        
        .main-container {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 2rem;
            padding: 2rem;
            max-height: calc(100vh - 120px);
        }
        
        @media (max-width: 1024px) {
            .main-container {
                grid-template-columns: 1fr;
                max-height: none;
            }
            
            .chat-info {
                order: -1;
            }
        }
        
        .chat-section, .chat-info {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.45);
        }
        
        .chat-messages {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 1.5rem;
            padding-right: 0.5rem;
        }
        
        .message {
            padding: 1rem;
            border-radius: 14px;
            line-height: 1.5;
            white-space: pre-wrap;
            border: 1px solid rgba(148, 163, 184, 0.2);
            position: relative;
        }
        
        .message.user {
            align-self: flex-end;
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.35);
            max-width: 80%;
        }
        
        .message.agent {
            background: rgba(30, 41, 59, 0.8);
            max-width: 90%;
        }
        
        .message.system {
            background: rgba(245, 158, 11, 0.2);
            border-color: rgba(245, 158, 11, 0.35);
            text-align: center;
            font-style: italic;
        }
        
        .message-time {
            font-size: 0.8rem;
            opacity: 0.6;
            margin-top: 0.5rem;
        }
        
        .input-section {
            display: flex;
            gap: 1rem;
            align-items: flex-end;
        }
        
        .input-group {
            flex: 1;
        }
        
        .emergency-input {
            width: 100%;
            min-height: 100px;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.6);
            color: inherit;
            resize: vertical;
            font-family: inherit;
            font-size: 1rem;
        }
        
        .emergency-input:focus {
            outline: none;
            border-color: #ef4444;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.25);
        }
        
        .send-btn {
            padding: 1rem 1.5rem;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        
        .send-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .emergency-notice {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
            color: #fca5a5;
        }
        
        .info-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .info-card h3 {
            color: #60a5fa;
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }
        
        .info-card p {
            font-size: 0.9rem;
            opacity: 0.8;
            line-height: 1.4;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .status-online {
            background: #10b981;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .quick-btn {
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #60a5fa;
            padding: 0.75rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .quick-btn:hover {
            background: rgba(59, 130, 246, 0.3);
            border-color: rgba(59, 130, 246, 0.6);
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>🚨 AlertMate</h1>
        <div class="user-info">
            <span id="user-name">Loading...</span>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
    </header>
    
    <div class="main-container">
        <section class="chat-section">
            <div class="emergency-notice">
                <strong>🚨 Emergency Chat Active</strong><br>
                Describe your emergency clearly. Help is on the way.
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message system">
                    <span class="status-indicator status-online"></span>
                    Connected to AlertMate Emergency Services
                    <div class="message-time" id="connect-time"></div>
                </div>
            </div>
            
            <div class="input-section">
                <div class="input-group">
                    <textarea 
                        class="emergency-input" 
                        id="emergency-input" 
                        placeholder="Describe your emergency situation in detail. Include location details if different from your registered address... (You can write in English, Urdu, or Roman Urdu)"
                        autofocus
                    ></textarea>
                </div>
                <button class="send-btn" id="send-btn" onclick="sendMessage()">
                    <span id="send-text">🚨 Send Alert</span>
                </button>
            </div>
        </section>
        
        <aside class="chat-info">
            <div class="info-card">
                <h3>📍 Your Location</h3>
                <p id="user-location">Loading location...</p>
            </div>
            
            <div class="info-card">
                <h3>📡 Network Status</h3>
                <p id="network-status">Detecting...</p>
            </div>
            
            <div class="info-card">
                <h3>🏥 Available Services</h3>
                <p>Medical emergencies, Police assistance, Fire & rescue, Natural disasters</p>
            </div>
            
            <div class="info-card">
                <h3>⚡ Quick Actions</h3>
                <div class="quick-actions">
                    <button class="quick-btn" onclick="quickMessage('Medical emergency / ایمرجنسی')">🏥 Medical</button>
                    <button class="quick-btn" onclick="quickMessage('Police needed / پولیس چاہیے')">🚔 Police</button>
                    <button class="quick-btn" onclick="quickMessage('Fire emergency / آگ لگ گئی')">🔥 Fire</button>
                    <button class="quick-btn" onclick="quickMessage('Natural disaster / قدرتی آفت')">🌪️ Disaster</button>
                </div>
            </div>
            
            <div class="info-card">
                <h3>📞 Emergency Hotlines</h3>
                <p>
                    Police: 15<br>
                    Fire: 16<br>
                    Medical: 1122<br>
                    Rescue: 1021
                </p>
            </div>
        </aside>
    </div>
    
    <script>
        let currentUser = null;
        let networkQuality = 'unknown';
        let connectionType = 'unknown';
        
        // Network quality detection
        function detectNetworkQuality() {
            if ('connection' in navigator) {
                const connection = navigator.connection;
                connectionType = connection.effectiveType || connection.type || 'unknown';
                
                // Map connection types to quality
                if (connectionType === 'slow-2g' || connectionType === '2g') {
                    networkQuality = 'slow';
                } else if (connectionType === '3g') {
                    networkQuality = 'medium';
                } else if (connectionType === '4g' || connectionType === 'wifi') {
                    networkQuality = 'fast';
                } else {
                    networkQuality = 'unknown';
                }
                
                // Adjust based on downlink speed if available
                if (connection.downlink) {
                    if (connection.downlink < 1) {
                        networkQuality = 'slow';
                    } else if (connection.downlink < 5) {
                        networkQuality = 'medium';
                    } else {
                        networkQuality = 'fast';
                    }
                }
            } else {
                // Fallback: estimate based on user agent or other factors
                networkQuality = 'unknown';
            }
            
            console.log('Network detected:', { connectionType, networkQuality });
            updateNetworkStatus();
        }
        
        function updateNetworkStatus() {
            const statusElement = document.getElementById('network-status');
            if (!statusElement) return;
            
            const qualityEmojis = {
                'slow': '🐌',
                'medium': '🚶',
                'fast': '🚀',
                'unknown': '❓'
            };
            
            const qualityTexts = {
                'slow': 'Slow (Minimal responses)',
                'medium': 'Medium (Optimized)',
                'fast': 'Fast (Full responses)',
                'unknown': 'Unknown (Minimal responses)'
            };
            
            const emoji = qualityEmojis[networkQuality] || '❓';
            const text = qualityTexts[networkQuality] || 'Unknown';
            
            statusElement.innerHTML = `${emoji} ${text}<br><small>${connectionType}</small>`;
        }
        
        // Monitor network changes
        if ('connection' in navigator) {
            navigator.connection.addEventListener('change', detectNetworkQuality);
        }
        
        async function loadUserInfo() {
            try {
                const response = await fetch('/api/v1/auth/me');
                if (response.ok) {
                    currentUser = await response.json();
                    document.getElementById('user-name').textContent = currentUser.name;
                    document.getElementById('user-location').textContent = 
                        `Lat: ${currentUser.lat?.toFixed(4) || 'N/A'}, Lon: ${currentUser.lon?.toFixed(4) || 'N/A'}`;
                } else {
                    window.location.href = '/';
                }
            } catch (error) {
                console.error('Failed to load user info:', error);
                window.location.href = '/';
            }
        }
        
        async function logout() {
            try {
                await fetch('/api/v1/auth/logout', { method: 'POST' });
            } catch (error) {
                console.error('Logout error:', error);
            }
            window.location.href = '/';
        }
        
        function addMessage(content, type = 'agent', timestamp = new Date()) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const timeString = timestamp.toLocaleTimeString();
            messageDiv.innerHTML = `
                ${content}
                <div class="message-time">${timeString}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function quickMessage(text) {
            document.getElementById('emergency-input').value = text;
            document.getElementById('emergency-input').focus();
        }
        
        async function sendMessage() {
            const input = document.getElementById('emergency-input');
            const sendBtn = document.getElementById('send-btn');
            const sendText = document.getElementById('send-text');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Set loading state
            sendBtn.disabled = true;
            sendText.innerHTML = '<span class="loading"></span> Processing...';
            
            try {
                // Assume good network quality for web users
                const networkQuality = 'fast';
                const connectionType = 'wifi';
                
                const response = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        userid: currentUser.user_id,
                        user_query: message,
                        user_location: `${currentUser.lat}, ${currentUser.lon}`,
                        lat: currentUser.lat,
                        lon: currentUser.lon,
                        lang: 'en',
                        network_quality: networkQuality,
                        connection_type: connectionType
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    addMessage(result.reply, 'agent');
                } else {
                    const error = await response.json();
                    addMessage(`Error: ${error.detail || 'Unable to process request'}`, 'system');
                }
            } catch (error) {
                addMessage('Network error. Please try again or call emergency hotlines.', 'system');
            } finally {
                sendBtn.disabled = false;
                sendText.innerHTML = '🚨 Send Alert';
                input.focus();
            }
        }
        
        // Handle Enter key to send message
        document.getElementById('emergency-input').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Initialize
        document.getElementById('connect-time').textContent = new Date().toLocaleTimeString();
        detectNetworkQuality(); // Detect initial network quality
        loadUserInfo();
    </script>
</body>
</html>
"""


def get_admin_dashboard() -> str:
    """Return the admin dashboard HTML.""" 
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AlertMate - Admin Dashboard</title>
    <style>
        :root {
            color-scheme: light dark;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        .header {
            padding: 1.5rem 2rem;
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            color: #f8fafc;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.35);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .header-actions {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .refresh-btn, .logout-btn {
            background: rgba(248, 250, 252, 0.2);
            border: 1px solid rgba(248, 250, 252, 0.3);
            color: #f8fafc;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }
        
        .refresh-btn:hover, .logout-btn:hover {
            background: rgba(248, 250, 252, 0.3);
            border-color: rgba(248, 250, 252, 0.5);
        }
        
        .main-container {
            flex: 1;
            padding: 2rem;
            display: grid;
            gap: 2rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
        }
        
        .stat-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.45);
        }
        
        .stat-card h3 {
            font-size: 0.9rem;
            color: #94a3b8;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .stat-change {
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .stat-change.positive {
            color: #10b981;
        }
        
        .stat-change.negative {
            color: #ef4444;
        }
        
        .medical { color: #ef4444; }
        .police { color: #3b82f6; }
        .disaster { color: #f59e0b; }
        .users { color: #10b981; }
        
        .dashboard-sections {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 1024px) {
            .dashboard-sections {
                grid-template-columns: 1fr;
            }
        }
        
        .section-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.45);
        }
        
        .section-card h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #60a5fa;
        }
        
        .queue-item {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        
        .queue-item:last-child {
            margin-bottom: 0;
        }
        
        .queue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .queue-service {
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .queue-priority {
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .priority-1 { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
        .priority-2 { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .priority-3 { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        
        .queue-time {
            font-size: 0.8rem;
            opacity: 0.7;
        }
        
        .activity-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }
        
        .activity-content {
            flex: 1;
        }
        
        .activity-text {
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .activity-time {
            font-size: 0.8rem;
            opacity: 0.7;
        }
        
        .empty-state {
            text-align: center;
            padding: 2rem;
            opacity: 0.6;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .chart-container {
            height: 200px;
            display: flex;
            align-items: end;
            justify-content: space-around;
            gap: 1rem;
            padding: 1rem;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            margin-top: 1rem;
        }
        
        .chart-bar {
            flex: 1;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            border-radius: 4px;
            min-height: 20px;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .chart-bar:hover {
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
        }
        
        .chart-label {
            position: absolute;
            bottom: -2rem;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8rem;
            opacity: 0.7;
        }
        
        .chart-value {
            position: absolute;
            top: -1.5rem;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>📊 AlertMate Admin</h1>
        <div class="header-actions">
            <button class="refresh-btn" onclick="refreshDashboard()">
                <span id="refresh-text">🔄 Refresh</span>
            </button>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
    </header>
    
    <div class="main-container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Active Emergencies</h3>
                <div class="stat-value medical" id="active-emergencies">-</div>
                <div class="stat-change" id="emergencies-change">
                    <span>Loading...</span>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>Total Users</h3>
                <div class="stat-value users" id="total-users">-</div>
                <div class="stat-change" id="users-change">
                    <span>Loading...</span>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>Tasks Completed</h3>
                <div class="stat-value police" id="tasks-completed">-</div>
                <div class="stat-change" id="tasks-change">
                    <span>Loading...</span>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>Response Time</h3>
                <div class="stat-value disaster" id="response-time">-</div>
                <div class="stat-change" id="response-change">
                    <span>seconds avg</span>
                </div>
            </div>
        </div>
        
        <div class="dashboard-sections">
            <div class="section-card">
                <h2>🚨 Active Queue</h2>
                <div id="active-queue">
                    <div class="empty-state">
                        <span class="loading"></span> Loading queue data...
                    </div>
                </div>
            </div>
            
            <div class="section-card">
                <h2>📈 Recent Activity</h2>
                <div id="recent-activity">
                    <div class="empty-state">
                        <span class="loading"></span> Loading activity...
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section-card">
            <h2>📊 Service Distribution (Last 24h)</h2>
            <div class="chart-container" id="service-chart">
                <div class="chart-bar" style="height: 60%;">
                    <div class="chart-value">12</div>
                    <div class="chart-label">Medical</div>
                </div>
                <div class="chart-bar" style="height: 40%;">
                    <div class="chart-value">8</div>
                    <div class="chart-label">Police</div>
                </div>
                <div class="chart-bar" style="height: 20%;">
                    <div class="chart-value">4</div>
                    <div class="chart-label">Fire</div>
                </div>
                <div class="chart-bar" style="height: 15%;">
                    <div class="chart-value">3</div>
                    <div class="chart-label">Disaster</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        async function loadDashboardData() {
            try {
                // Simulate dashboard data loading
                // In a real implementation, these would be separate API calls
                
                // Load stats
                document.getElementById('active-emergencies').textContent = Math.floor(Math.random() * 20) + 5;
                document.getElementById('total-users').textContent = Math.floor(Math.random() * 1000) + 500;
                document.getElementById('tasks-completed').textContent = Math.floor(Math.random() * 100) + 250;
                document.getElementById('response-time').textContent = (Math.random() * 30 + 15).toFixed(1);
                
                // Load active queue
                await loadActiveQueue();
                
                // Load recent activity
                await loadRecentActivity();
                
            } catch (error) {
                console.error('Failed to load dashboard data:', error);
            }
        }
        
        async function loadActiveQueue() {
            try {
                const response = await fetch('/api/v1/admin/queue');
                let tasks = [];
                
                if (response.ok) {
                    tasks = await response.json();
                } else {
                    // Mock data for demo
                    tasks = [
                        {
                            id: 1,
                            service: 'medical',
                            priority: 3,
                            created_at: new Date(Date.now() - 5 * 60000).toISOString(),
                            user_location: 'Karachi, PK'
                        },
                        {
                            id: 2,
                            service: 'police',
                            priority: 2,
                            created_at: new Date(Date.now() - 12 * 60000).toISOString(),
                            user_location: 'Lahore, PK'
                        }
                    ];
                }
                
                const queueContainer = document.getElementById('active-queue');
                
                if (tasks.length === 0) {
                    queueContainer.innerHTML = '<div class="empty-state">No active tasks in queue</div>';
                    return;
                }
                
                queueContainer.innerHTML = tasks.map(task => {
                    const timeAgo = Math.floor((Date.now() - new Date(task.created_at)) / 60000);
                    return `
                        <div class="queue-item">
                            <div class="queue-header">
                                <span class="queue-service ${task.service}">${task.service.toUpperCase()}</span>
                                <span class="queue-priority priority-${task.priority}">P${task.priority}</span>
                            </div>
                            <div class="queue-time">${timeAgo} minutes ago • ${task.user_location}</div>
                        </div>
                    `;
                }).join('');
                
            } catch (error) {
                document.getElementById('active-queue').innerHTML = 
                    '<div class="empty-state">Failed to load queue data</div>';
            }
        }
        
        async function loadRecentActivity() {
            try {
                const response = await fetch('/api/v1/admin/activity');
                let activities = [];
                
                if (response.ok) {
                    activities = await response.json();
                } else {
                    // Mock data for demo
                    activities = [
                        {
                            type: 'medical',
                            message: 'Medical emergency resolved in Karachi',
                            timestamp: new Date(Date.now() - 3 * 60000).toISOString()
                        },
                        {
                            type: 'user',
                            message: 'New user registered: Ahmad Ali',
                            timestamp: new Date(Date.now() - 8 * 60000).toISOString()
                        },
                        {
                            type: 'police',
                            message: 'Police assistance dispatched to Lahore',
                            timestamp: new Date(Date.now() - 15 * 60000).toISOString()
                        }
                    ];
                }
                
                const activityContainer = document.getElementById('recent-activity');
                
                if (activities.length === 0) {
                    activityContainer.innerHTML = '<div class="empty-state">No recent activity</div>';
                    return;
                }
                
                const icons = {
                    medical: '🏥',
                    police: '🚔',
                    disaster: '🌪️',
                    user: '👤',
                    system: '⚙️'
                };
                
                activityContainer.innerHTML = activities.map(activity => {
                    const timeAgo = Math.floor((Date.now() - new Date(activity.timestamp)) / 60000);
                    return `
                        <div class="activity-item">
                            <div class="activity-icon ${activity.type}">
                                ${icons[activity.type] || '📋'}
                            </div>
                            <div class="activity-content">
                                <div class="activity-text">${activity.message}</div>
                                <div class="activity-time">${timeAgo} minutes ago</div>
                            </div>
                        </div>
                    `;
                }).join('');
                
            } catch (error) {
                document.getElementById('recent-activity').innerHTML = 
                    '<div class="empty-state">Failed to load activity data</div>';
            }
        }
        
        async function refreshDashboard() {
            const refreshBtn = document.getElementById('refresh-text');
            refreshBtn.innerHTML = '<span class="loading"></span> Refreshing...';
            
            try {
                await loadDashboardData();
                refreshBtn.textContent = '✅ Updated';
                setTimeout(() => {
                    refreshBtn.textContent = '🔄 Refresh';
                }, 2000);
            } catch (error) {
                refreshBtn.textContent = '❌ Failed';
                setTimeout(() => {
                    refreshBtn.textContent = '🔄 Refresh';
                }, 2000);
            }
        }
        
        async function logout() {
            try {
                await fetch('/api/v1/auth/logout', { method: 'POST' });
            } catch (error) {
                console.error('Logout error:', error);
            }
            window.location.href = '/';
        }
        
        // Initialize dashboard
        loadDashboardData();
        
        // Set up auto-refresh every 30 seconds
        refreshInterval = setInterval(loadDashboardData, 30000);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>
"""