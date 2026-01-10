import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import "./Login.css";

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    loginId: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Backend expects 'username', frontend form uses 'loginId'
      const response = await api.login(formData.loginId, formData.password);

      // Store user info
      localStorage.setItem("user", JSON.stringify(response)); // { user_id, role }

      // Redirect based on role
      if (response.role === "doctor") {
        navigate("/doctor-dashboard");
      } else if (response.role === "nurse") {
        navigate("/nurse-dashboard");
      } else if (response.role === "cleaner") {
        navigate("/cleaner-dashboard");
      } else if (response.role === "receptionist") {
        navigate("/receptionist-dashboard");
      } else {
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-split-wrapper">
        {/* Left Side - Visual & Branding */}
        <div className="login-visual-side">
          <div className="visual-overlay"></div>
          <div className="visual-content">
            <div className="brand-logo-large">
              <span className="logo-icon">✤</span>
              <span>CareFlow Nexus</span>
            </div>
            <div className="visual-text">
              <h2>
                Streamlined Healthcare <br /> Management
              </h2>
              <p>
                Experience the next generation of hospital administration and
                patient care coordination.
              </p>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="login-form-side">
          <div className="form-content-wrapper">
            <header className="login-header">
              <h3>Welcome Back</h3>
              <p>Please sign in to your account</p>
            </header>

            {error && <div className="error-message">{error}</div>}

            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="loginId">Login ID</label>
                <div className="input-wrapper">
                  <input
                    type="text"
                    id="loginId"
                    name="loginId"
                    value={formData.loginId}
                    onChange={handleChange}
                    placeholder="Enter Login ID"
                    required
                  />
                  <span className="input-focus-border"></span>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <div className="input-wrapper">
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Enter Password"
                    required
                  />
                  <span className="input-focus-border"></span>
                </div>
                <button
                  type="button"
                  className="forgot-password-link"
                  onClick={() =>
                    alert(
                      "Please contact the System Administrator to reset your password.",
                    )
                  }
                >
                  Forgot password?
                </button>
              </div>

              <button type="submit" className="sign-in-btn" disabled={loading}>
                {loading ? (
                  <span className="loading-spinner"></span>
                ) : (
                  <>
                    Sign In <span className="arrow-icon">→</span>
                  </>
                )}
              </button>
            </form>

            <footer className="login-footer">
              <p>
                Need support?{" "}
                <a
                  href="mailto:admin@careflownexus.com"
                  className="contact-link"
                >
                  Contact Admin
                </a>
              </p>
              <p className="copyright-text">
                Restricted Access • CareFlow Nexus System
              </p>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
