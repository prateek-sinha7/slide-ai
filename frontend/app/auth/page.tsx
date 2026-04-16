'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import RegistrationForm from '@/components/RegistrationForm';
import LoginForm from '@/components/LoginForm';

export default function AuthPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');

  // Redirect authenticated users to main app (Requirement 3.2)
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  // Handle successful registration - navigate to main app
  const handleRegistrationSuccess = () => {
    router.push('/');
  };

  // Handle successful login - navigate to main app
  const handleLoginSuccess = () => {
    router.push('/');
  };

  return (
    <main style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>
        AI PowerPoint Generator
      </h1>

      {/* Tab Navigation */}
      <div className="tab-container">
        <button
          className={`tab-button ${activeTab === 'login' ? 'active' : ''}`}
          onClick={() => setActiveTab('login')}
        >
          Login
        </button>
        <button
          className={`tab-button ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => setActiveTab('register')}
        >
          Register
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'login' ? (
          <LoginForm onSuccess={handleLoginSuccess} />
        ) : (
          <RegistrationForm onSuccess={handleRegistrationSuccess} />
        )}
      </div>

      <style jsx global>{`
        .tab-container {
          display: flex;
          border-bottom: 2px solid #e0e0e0;
          margin-bottom: 2rem;
        }

        .tab-button {
          flex: 1;
          padding: 1rem;
          background: transparent;
          border: none;
          border-bottom: 3px solid transparent;
          font-size: 1rem;
          font-weight: 500;
          color: #666;
          cursor: pointer;
          transition: all 0.2s;
        }

        .tab-button:hover {
          color: #007bff;
          background: #f5f5f5;
        }

        .tab-button.active {
          color: #007bff;
          border-bottom-color: #007bff;
        }

        .tab-content {
          animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .registration-form,
        .login-form {
          border: 1px solid #ddd;
          padding: 2rem;
          border-radius: 8px;
          background-color: #f9f9f9;
        }

        .registration-form h2,
        .login-form h2 {
          margin-top: 0;
          margin-bottom: 1.5rem;
          color: #333;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
          color: #555;
        }

        .form-group input,
        .form-group select {
          width: 100%;
          padding: 0.5rem;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 1rem;
          box-sizing: border-box;
        }

        .form-group input:focus,
        .form-group select:focus {
          outline: none;
          border-color: #007bff;
          box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
        }

        .form-group input[aria-invalid="true"],
        .form-group select[aria-invalid="true"] {
          border-color: #dc3545;
        }

        .form-group input:disabled,
        .form-group select:disabled {
          background-color: #e9ecef;
          cursor: not-allowed;
        }

        .error-message {
          display: block;
          color: #dc3545;
          font-size: 0.875rem;
          margin-top: 0.25rem;
        }

        .general-error {
          padding: 0.75rem;
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 4px;
          margin-bottom: 1rem;
        }

        .success-message {
          padding: 0.75rem;
          background-color: #d4edda;
          border: 1px solid #c3e6cb;
          border-radius: 4px;
          color: #155724;
          margin-bottom: 1rem;
        }

        button[type="submit"] {
          width: 100%;
          padding: 0.75rem;
          background-color: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        button[type="submit"]:hover:not(:disabled) {
          background-color: #0056b3;
        }

        button[type="submit"]:disabled {
          background-color: #6c757d;
          cursor: not-allowed;
        }

        .required {
          color: #dc3545;
        }

        .prompt-form {
          border: 1px solid #ddd;
          padding: 2rem;
          border-radius: 8px;
          background-color: #f9f9f9;
          margin-bottom: 2rem;
        }

        .prompt-form h2 {
          margin-top: 0;
          margin-bottom: 1.5rem;
          color: #333;
        }

        @media (max-width: 768px) {
          main {
            padding: 1rem !important;
          }
        }
      `}</style>
    </main>
  );
}
