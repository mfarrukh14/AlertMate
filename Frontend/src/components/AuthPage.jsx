import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const AuthPage = () => {
  const { isAuthenticated, login, signup } = useAuth();
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  const showMessage = (text, type = 'error') => {
    setMessage({ text, type });
  };

  const clearMessage = () => {
    setMessage({ text: '', type: '' });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    clearMessage();

    const formData = new FormData(e.target);
    const credentials = {
      email: formData.get('email'),
      password: formData.get('password'),
    };

    try {
      await login(credentials);
      showMessage('Login successful! Redirecting to chat...', 'success');
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Login failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    clearMessage();

    const formData = new FormData(e.target);
    const userData = {
      name: formData.get('name'),
      email: formData.get('email'),
      password: formData.get('password'),
      phone_number: formData.get('phone_number'),
      cnic: formData.get('cnic'),
      blood_group: formData.get('blood_group'),
      lat: parseFloat(formData.get('lat')),
      lon: parseFloat(formData.get('lon')),
    };

    try {
      await signup(userData);
      showMessage('Account created successfully! Redirecting to chat...', 'success');
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Signup failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          document.getElementById('signup-lat').value = position.coords.latitude.toFixed(6);
          document.getElementById('signup-lon').value = position.coords.longitude.toFixed(6);
          showMessage('Location detected successfully!', 'success');
        },
        (error) => {
          showMessage('Could not get location. Please enter manually.', 'error');
        }
      );
    } else {
      showMessage('Geolocation not supported. Please enter manually.', 'error');
    }
  };

  const formatCNIC = (e) => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length >= 5) {
      value = value.substring(0, 5) + '-' + value.substring(5);
    }
    if (value.length >= 13) {
      value = value.substring(0, 13) + '-' + value.substring(13, 14);
    }
    e.target.value = value;
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700">
      <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-10 w-full max-w-md shadow-2xl">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-2">
            🚨 AlertMate
          </h1>
          <p className="text-slate-400">Emergency Response System</p>
        </div>

        {/* Tabs */}
        <div className="flex mb-8 bg-slate-900/60 rounded-xl p-1">
          <button
            className={`flex-1 py-3 px-4 text-center rounded-lg font-medium transition-all ${
              activeTab === 'login'
                ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-300'
            }`}
            onClick={() => { setActiveTab('login'); clearMessage(); }}
          >
            Login
          </button>
          <button
            className={`flex-1 py-3 px-4 text-center rounded-lg font-medium transition-all ${
              activeTab === 'signup'
                ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-300'
            }`}
            onClick={() => { setActiveTab('signup'); clearMessage(); }}
          >
            Sign Up
          </button>
        </div>

        {/* Message Display */}
        {message.text && (
          <div className={`mb-4 p-3 rounded-lg border ${
            message.type === 'success' 
              ? 'bg-green-500/10 border-green-500/20 text-green-400' 
              : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}>
            {message.text}
          </div>
        )}

        {/* Login Form */}
        {activeTab === 'login' && (
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                Email
              </label>
              <input
                type="email"
                name="email"
                required
                placeholder="your.email@example.com"
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                name="password"
                required
                placeholder="Enter your password"
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-blue-600 focus:outline-none focus:ring-3 focus:ring-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white mr-2"></div>
                  Processing...
                </span>
              ) : (
                'Log In'
              )}
            </button>
          </form>
        )}

        {/* Signup Form */}
        {activeTab === 'signup' && (
          <form onSubmit={handleSignup} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                Full Name
              </label>
              <input
                type="text"
                name="name"
                required
                placeholder="John Doe"
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                Email
              </label>
              <input
                type="email"
                name="email"
                required
                placeholder="your.email@example.com"
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                name="password"
                required
                placeholder="Min 8 characters"
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                Phone Number
              </label>
              <input
                type="tel"
                name="phone_number"
                required
                placeholder="+92 300 1234567"
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                CNIC
              </label>
              <input
                type="text"
                name="cnic"
                required
                placeholder="12345-6789012-3"
                pattern="[0-9]{5}-[0-9]{7}-[0-9]{1}"
                onInput={formatCNIC}
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                Blood Group
              </label>
              <select
                name="blood_group"
                required
                className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
              >
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

            <button
              type="button"
              onClick={getCurrentLocation}
              className="w-full py-2 px-4 bg-blue-500/20 border border-blue-500/40 text-blue-400 rounded-lg hover:bg-blue-500/30 hover:border-blue-500/60 transition-all"
            >
              📍 Get Current Location
            </button>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                  Latitude
                </label>
                <input
                  type="number"
                  id="signup-lat"
                  name="lat"
                  step="any"
                  required
                  placeholder="24.8607"
                  className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wide">
                  Longitude
                </label>
                <input
                  type="number"
                  id="signup-lon"
                  name="lon"
                  step="any"
                  required
                  placeholder="67.0011"
                  className="w-full px-4 py-3 rounded-xl border border-slate-600/30 bg-slate-900/70 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-3 focus:ring-blue-500/25 focus:border-blue-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-blue-600 focus:outline-none focus:ring-3 focus:ring-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white mr-2"></div>
                  Processing...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default AuthPage;