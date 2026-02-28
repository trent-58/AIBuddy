import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'

const TOKEN_KEY = 'accessToken'
const REFRESH_TOKEN_KEY = 'refreshToken'
const LOGOUT_ENDPOINT = '/api/auth/logout/'
const REGISTER_ENDPOINT =
  import.meta.env.VITE_REGISTER_ENDPOINT ?? '/api/auth/register/email'
const REGISTER_SESSION_KEY = 'registerSessionToken'
const REGISTER_EMAIL_KEY = 'registerEmail'

function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY)
}

function getAuthHeaders(includeJson = false) {
  const headers = {}
  if (includeJson) {
    headers['Content-Type'] = 'application/json'
  }

  const token = getAccessToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return headers
}

async function extractErrorMessage(response, fallbackMessage) {
  try {
    const data = await response.json()

    if (typeof data === 'string' && data.trim()) {
      return data
    }

    if (data?.detail && typeof data.detail === 'string') {
      return data.detail
    }

    if (data && typeof data === 'object') {
      const fieldMessages = Object.entries(data)
        .map(([field, value]) => {
          if (Array.isArray(value) && value.length > 0) {
            return `${field}: ${value.join(', ')}`
          }
          if (typeof value === 'string' && value.trim()) {
            return `${field}: ${value}`
          }
          return ''
        })
        .filter(Boolean)

      if (fieldMessages.length > 0) {
        return fieldMessages.join(' | ')
      }
    }
  } catch {
    try {
      const rawText = await response.text()
      if (rawText) {
        return rawText
      }
    } catch {
      return fallbackMessage
    }
  }

  return fallbackMessage
}

function LandingPage({ navigate }) {
  return (
    <main className="page">
      <section className="card">
        <h1>Welcome to AI Buddy</h1>
        <p>
          This is the public page for visitors who are not logged in. Learn about
          the platform, what it offers, and create your account to continue.
        </p>
        <div className="about">
          <h2>About Us</h2>
          <p>
            We are building a simple, user-focused web app powered by a Django
            backend and a React frontend.
          </p>
          <p>
            Right now this is the starter structure. Design and full API
            integration will be added in the next steps.
          </p>
        </div>
        <div className="actions">
          <button onClick={() => navigate('/login')}>Login</button>
          <button className="button-secondary" onClick={() => navigate('/register')}>
            Register
          </button>
        </div>
      </section>
    </main>
  )
}

function LoginPage({ navigate, onLoginSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    try {
      setIsSubmitting(true)
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username.trim(),
          password,
        }),
      })

      if (!response.ok) {
        const errorMessage = await extractErrorMessage(
          response,
          `Login failed (${response.status}).`,
        )
        throw new Error(errorMessage)
      }

      const data = await response.json()
      const accessToken = data?.access ?? data?.access_token ?? data?.token
      const refreshToken = data?.refresh ?? data?.refresh_token

      if (!accessToken) {
        throw new Error('Login response did not include an access token.')
      }

      localStorage.setItem(TOKEN_KEY, accessToken)
      if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
      }
      onLoginSuccess()
    } catch (error) {
      const isNetworkError = error instanceof TypeError
      setStatus({
        type: 'error',
        message: isNetworkError
          ? 'Could not reach server. Check Django is running and API URL/proxy is correct.'
          : error instanceof Error
            ? error.message
            : 'Could not log in.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Login</h1>
        <p>Enter your username and password to log in.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="login-username">Username</label>
          <input
            id="login-username"
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Username"
            required
          />
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            required
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in...' : 'Login'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/')}>Back</button>
          <button
            className="button-secondary"
            onClick={() => navigate('/forgot-password')}
          >
            Forgot Password
          </button>
          <button className="button-secondary" onClick={() => navigate('/register')}>
            Go to Register
          </button>
        </div>
      </section>
    </main>
  )
}

function ForgotPasswordEmailPage({ navigate }) {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    try {
      setIsSubmitting(true)
      const response = await fetch('/api/auth/password/forgot/email/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })

      if (!response.ok) {
        throw new Error(
          await extractErrorMessage(
            response,
            `Could not request password reset (${response.status}).`,
          ),
        )
      }

      setStatus({
        type: 'success',
        message: 'If the account exists, a reset code was sent to your email.',
      })
      navigate(`/forgot-password/verify?email=${encodeURIComponent(email.trim())}`)
    } catch (error) {
      setStatus({
        type: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not request password reset.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Forgot Password</h1>
        <p>Enter your email to receive a 6-digit verification code.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="forgot-email">Email</label>
          <input
            id="forgot-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="user@example.com"
            required
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sending...' : 'Send Code'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/login')}>Back to Login</button>
        </div>
      </section>
    </main>
  )
}

function ForgotPasswordVerifyPage({ navigate }) {
  const params = new URLSearchParams(window.location.search)
  const [email, setEmail] = useState(params.get('email') ?? '')
  const [code, setCode] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    try {
      setIsSubmitting(true)
      const response = await fetch('/api/auth/password/forgot/verify/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), code: code.trim() }),
      })

      if (!response.ok) {
        throw new Error(
          await extractErrorMessage(
            response,
            `Could not verify code (${response.status}).`,
          ),
        )
      }

      const data = await response.json()
      const sessionToken = data?.session_token
      if (!sessionToken) {
        throw new Error('Code verified but session_token was not returned.')
      }

      sessionStorage.setItem('forgotPasswordEmail', email.trim())
      sessionStorage.setItem('forgotPasswordSessionToken', sessionToken)
      navigate('/forgot-password/reset')
    } catch (error) {
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Could not verify code.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Verify Code</h1>
        <p>Enter the verification code sent to your email.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="forgot-verify-email">Email</label>
          <input
            id="forgot-verify-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="user@example.com"
            required
          />
          <label htmlFor="forgot-verify-code">Code</label>
          <input
            id="forgot-verify-code"
            type="text"
            value={code}
            onChange={(event) => setCode(event.target.value)}
            placeholder="123456"
            required
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Verifying...' : 'Verify Code'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/forgot-password')}>Back</button>
        </div>
      </section>
    </main>
  )
}

function ForgotPasswordResetPage({ navigate }) {
  const [email, setEmail] = useState(sessionStorage.getItem('forgotPasswordEmail') ?? '')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    const sessionToken = sessionStorage.getItem('forgotPasswordSessionToken')
    if (!sessionToken) {
      setStatus({
        type: 'error',
        message: 'Session token missing. Verify code again first.',
      })
      return
    }

    try {
      setIsSubmitting(true)
      const response = await fetch('/api/auth/password/forgot/reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          session_token: sessionToken,
          password,
        }),
      })

      if (!response.ok) {
        throw new Error(
          await extractErrorMessage(
            response,
            `Could not reset password (${response.status}).`,
          ),
        )
      }

      sessionStorage.removeItem('forgotPasswordEmail')
      sessionStorage.removeItem('forgotPasswordSessionToken')
      navigate('/login', true)
    } catch (error) {
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Could not reset password.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Set New Password</h1>
        <p>Choose your new password to finish reset.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="forgot-reset-email">Email</label>
          <input
            id="forgot-reset-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="user@example.com"
            required
          />
          <label htmlFor="forgot-reset-password">New Password</label>
          <input
            id="forgot-reset-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="newStrongPassword123"
            required
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/forgot-password/verify')}>Back</button>
          <button className="button-secondary" onClick={() => navigate('/login')}>
            Go to Login
          </button>
        </div>
      </section>
    </main>
  )
}

function RegisterPage({ navigate }) {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    try {
      setIsSubmitting(true)
      const response = await fetch(REGISTER_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.trim() }),
      })

      if (!response.ok) {
        const errorMessage = await extractErrorMessage(
          response,
          `Registration failed (${response.status}).`,
        )
        throw new Error(errorMessage)
      }

      setStatus({
        type: 'success',
        message: 'Verification code sent. Check your email for the 6-digit code.',
      })
      navigate(`/register/verify?email=${encodeURIComponent(email.trim())}`)
    } catch (error) {
      const isNetworkError = error instanceof TypeError
      setStatus({
        type: 'error',
        message: isNetworkError
          ? 'Could not reach server. Check Django is running and API URL/proxy is correct.'
          : error instanceof Error
            ? error.message
            : 'Could not start registration.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Register</h1>
        <p>Enter your email to start registration and receive a 6-digit code.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="user@example.com"
            required
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sending...' : 'Start Registration'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/')}>Back</button>
          <button className="button-secondary" onClick={() => navigate('/login')}>
            Go to Login
          </button>
        </div>
      </section>
    </main>
  )
}

function RegisterVerifyPage({ navigate }) {
  const params = new URLSearchParams(window.location.search)
  const [email, setEmail] = useState(params.get('email') ?? '')
  const [code, setCode] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    try {
      setIsSubmitting(true)
      const response = await fetch('/api/auth/register/verify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          code: code.trim(),
        }),
      })

      if (!response.ok) {
        const errorMessage = await extractErrorMessage(
          response,
          `Verification failed (${response.status}).`,
        )
        throw new Error(errorMessage)
      }

      const data = await response.json()
      const sessionToken = data?.session_token

      if (!sessionToken) {
        throw new Error('Verification succeeded but session_token was not returned.')
      }

      const normalizedEmail = email.trim()
      sessionStorage.setItem(REGISTER_SESSION_KEY, sessionToken)
      sessionStorage.setItem(REGISTER_EMAIL_KEY, normalizedEmail)

      setStatus({
        type: 'success',
        message: 'Code verified. Continue by setting your password.',
      })
      setCode('')
      navigate('/register/password')
    } catch (error) {
      const isNetworkError = error instanceof TypeError
      setStatus({
        type: 'error',
        message: isNetworkError
          ? 'Could not reach server. Check Django is running and API URL/proxy is correct.'
          : error instanceof Error
            ? error.message
            : 'Could not verify registration.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Verify Registration</h1>
        <p>Enter the 6-digit code received by email to complete registration.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="verify-email">Email</label>
          <input
            id="verify-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="user@example.com"
            required
          />
          <label htmlFor="verify-code">Verification Code</label>
          <input
            id="verify-code"
            type="text"
            value={code}
            onChange={(event) => setCode(event.target.value)}
            placeholder="099499"
            required
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Verifying...' : 'Verify Code'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/register')}>Back</button>
          <button className="button-secondary" onClick={() => navigate('/login')}>
            Go to Login
          </button>
        </div>
      </section>
    </main>
  )
}

function RegisterPasswordPage({ navigate }) {
  const params = new URLSearchParams(window.location.search)
  const [email, setEmail] = useState(
    params.get('email') ?? sessionStorage.getItem(REGISTER_EMAIL_KEY) ?? '',
  )
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    const sessionToken = sessionStorage.getItem(REGISTER_SESSION_KEY)
    if (!sessionToken) {
      setStatus({
        type: 'error',
        message:
          'Session token missing. Verify your email code again before setting password.',
      })
      return
    }

    try {
      setIsSubmitting(true)
      const response = await fetch('/api/auth/register/password/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          session_token: sessionToken,
          password,
        }),
      })

      if (!response.ok) {
        const errorMessage = await extractErrorMessage(
          response,
          `Password setup failed (${response.status}).`,
        )
        throw new Error(errorMessage)
      }

      setStatus({
        type: 'success',
        message: 'Password set successfully. Continue with your profile details.',
      })
      setPassword('')
      navigate('/register/complete')
    } catch (error) {
      const isNetworkError = error instanceof TypeError
      setStatus({
        type: 'error',
        message: isNetworkError
          ? 'Could not reach server. Check Django is running and API URL/proxy is correct.'
          : error instanceof Error
            ? error.message
            : 'Could not set password.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Set Password</h1>
        <p>Use the session token from verification to create your account password.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="password-email">Email</label>
          <input
            id="password-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="user@example.com"
            required
          />
          <label htmlFor="password-value">Password</label>
          <input
            id="password-value"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter password"
            required
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Set Password'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/register/verify')}>Back</button>
          <button className="button-secondary" onClick={() => navigate('/login')}>
            Go to Login
          </button>
        </div>
      </section>
    </main>
  )
}

function RegisterCompletePage({ navigate }) {
  const params = new URLSearchParams(window.location.search)
  const [email, setEmail] = useState(
    params.get('email') ?? sessionStorage.getItem(REGISTER_EMAIL_KEY) ?? '',
  )
  const [username, setUsername] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [bio, setBio] = useState('')
  const [interestsInput, setInterestsInput] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    const sessionToken = sessionStorage.getItem(REGISTER_SESSION_KEY)
    if (!sessionToken) {
      setStatus({
        type: 'error',
        message:
          'Session token missing. Restart verification before completing registration.',
      })
      return
    }

    const interests = interestsInput
      .split(',')
      .map((item) => Number.parseInt(item.trim(), 10))
      .filter((value) => Number.isInteger(value))

    try {
      setIsSubmitting(true)
      const response = await fetch('/api/auth/register/complete/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          session_token: sessionToken,
          username: username.trim(),
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          bio: bio.trim(),
          interests,
        }),
      })

      if (!response.ok) {
        const errorMessage = await extractErrorMessage(
          response,
          `Profile completion failed (${response.status}).`,
        )
        throw new Error(errorMessage)
      }

      sessionStorage.removeItem(REGISTER_SESSION_KEY)
      sessionStorage.removeItem(REGISTER_EMAIL_KEY)
      setStatus({
        type: 'success',
        message: 'Registration completed successfully. You can now log in.',
      })
      navigate('/login', true)
    } catch (error) {
      const isNetworkError = error instanceof TypeError
      setStatus({
        type: 'error',
        message: isNetworkError
          ? 'Could not reach server. Check Django is running and API URL/proxy is correct.'
          : error instanceof Error
            ? error.message
            : 'Could not complete registration.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Complete Registration</h1>
        <p>Add your profile details to finish account setup.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label htmlFor="complete-email">Email</label>
          <input
            id="complete-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="user@example.com"
            required
          />
          <label htmlFor="complete-username">Username</label>
          <input
            id="complete-username"
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Choose username"
            required
          />
          <label htmlFor="complete-first-name">First Name</label>
          <input
            id="complete-first-name"
            type="text"
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
            placeholder="First name"
            required
          />
          <label htmlFor="complete-last-name">Last Name</label>
          <input
            id="complete-last-name"
            type="text"
            value={lastName}
            onChange={(event) => setLastName(event.target.value)}
            placeholder="Last name"
            required
          />
          <label htmlFor="complete-bio">Bio</label>
          <input
            id="complete-bio"
            type="text"
            value={bio}
            onChange={(event) => setBio(event.target.value)}
            placeholder="Short bio"
          />
          <label htmlFor="complete-interests">Interests (IDs, comma separated)</label>
          <input
            id="complete-interests"
            type="text"
            value={interestsInput}
            onChange={(event) => setInterestsInput(event.target.value)}
            placeholder="1,2,3"
          />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Finishing...' : 'Complete Registration'}
          </button>
        </form>
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}
        <div className="actions">
          <button onClick={() => navigate('/register/password')}>Back</button>
          <button className="button-secondary" onClick={() => navigate('/login')}>
            Go to Login
          </button>
        </div>
      </section>
    </main>
  )
}

function AppHeader({ navigate, onLogout }) {
  return (
    <header className="app-header">
      <button className="logo-button" onClick={() => navigate('/dashboard')}>
        AI Buddy
      </button>
      <button className="nav-button" onClick={() => navigate('/chats')}>
        Chats
      </button>
      <div className="header-actions">
        <button className="profile-button" onClick={() => navigate('/profile')}>
          Profile
        </button>
        <button className="logout-button" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  )
}

function DashboardPage({ navigate, onLogout }) {
  return (
    <main className="app-page">
      <AppHeader navigate={navigate} onLogout={onLogout} />
      <section className="app-content">
        <h1>Dashboard</h1>
        <button onClick={() => navigate('/matching')}>Start Chatting</button>
      </section>
    </main>
  )
}

function ProfilePage({ navigate, onLogout }) {
  const [profile, setProfile] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [isResettingPassword, setIsResettingPassword] = useState(false)
  const [passwordStatus, setPasswordStatus] = useState({ type: '', message: '' })
  const [isResetModalOpen, setIsResetModalOpen] = useState(false)

  const loadProfile = useCallback(async () => {
    try {
      setIsLoading(true)
      setErrorMessage('')
      const response = await fetch('/api/auth/profile/', {
        method: 'GET',
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        const message = await extractErrorMessage(
          response,
          `Failed to load profile (${response.status}).`,
        )
        throw new Error(message)
      }

      const data = await response.json()
      setProfile(data)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not load profile.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const handleResetPassword = async (event) => {
    event.preventDefault()
    setPasswordStatus({ type: '', message: '' })

    try {
      if (newPassword !== newPasswordConfirm) {
        throw new Error('New password and confirmation do not match.')
      }

      setIsResettingPassword(true)
      const response = await fetch('/api/auth/password/reset/', {
        method: 'POST',
        headers: getAuthHeaders(true),
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
          new_password_confirm: newPasswordConfirm,
        }),
      })

      if (!response.ok) {
        throw new Error(
          await extractErrorMessage(
            response,
            `Could not reset password (${response.status}).`,
          ),
        )
      }

      setOldPassword('')
      setNewPassword('')
      setNewPasswordConfirm('')
      setPasswordStatus({
        type: 'success',
        message: 'Password updated successfully.',
      })
    } catch (error) {
      setPasswordStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Could not reset password.',
      })
    } finally {
      setIsResettingPassword(false)
    }
  }

  const openResetModal = () => {
    setPasswordStatus({ type: '', message: '' })
    setIsResetModalOpen(true)
  }

  const closeResetModal = () => {
    setIsResetModalOpen(false)
    setOldPassword('')
    setNewPassword('')
    setNewPasswordConfirm('')
    setPasswordStatus({ type: '', message: '' })
  }

  return (
    <main className="app-page">
      <AppHeader navigate={navigate} onLogout={onLogout} />
      <section className="app-content">
        <h1>Profile</h1>
        <div className="toolbar">
          <button onClick={loadProfile}>Refresh Profile</button>
          <button className="button-secondary" onClick={openResetModal}>
            Reset Password
          </button>
        </div>

        {isLoading && <p>Loading profile...</p>}
        {!isLoading && errorMessage && <p className="status-error">{errorMessage}</p>}

        {!isLoading && !errorMessage && profile && (
          <div className="profile-layout">
            <article className="chat-item profile-card">
              <p>
                <strong>Email:</strong> {profile.email || '-'}
              </p>
              <p>
                <strong>Username:</strong> {profile.username || '-'}
              </p>
              <p>
                <strong>First Name:</strong> {profile.first_name || '-'}
              </p>
              <p>
                <strong>Last Name:</strong> {profile.last_name || '-'}
              </p>
              <p>
                <strong>Bio:</strong> {profile.bio || '-'}
              </p>
              <div className="profile-interests">
                <strong>Selected Interests:</strong>
                {Array.isArray(profile.selected_interests) &&
                profile.selected_interests.length > 0 ? (
                  <ul>
                    {profile.selected_interests.map((interest) => (
                      <li key={interest.option_id}>
                        {interest.name} (#{interest.option_id})
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No interests selected.</p>
                )}
              </div>
            </article>
          </div>
        )}

        {isResetModalOpen && (
          <div className="modal-overlay" onClick={closeResetModal}>
            <div className="modal-card" onClick={(event) => event.stopPropagation()}>
              <h2>Reset Password</h2>
              <form className="form" onSubmit={handleResetPassword}>
                <label htmlFor="profile-old-password">Current Password</label>
                <input
                  id="profile-old-password"
                  type="password"
                  value={oldPassword}
                  onChange={(event) => setOldPassword(event.target.value)}
                  placeholder="currentPassword"
                  required
                />
                <label htmlFor="profile-new-password">New Password</label>
                <input
                  id="profile-new-password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  placeholder="newPassword123"
                  required
                />
                <label htmlFor="profile-new-password-confirm">
                  Confirm New Password
                </label>
                <input
                  id="profile-new-password-confirm"
                  type="password"
                  value={newPasswordConfirm}
                  onChange={(event) => setNewPasswordConfirm(event.target.value)}
                  placeholder="newPassword123"
                  required
                />
                <button type="submit" disabled={isResettingPassword}>
                  {isResettingPassword ? 'Updating...' : 'Update Password'}
                </button>
              </form>
              {passwordStatus.message && (
                <p
                  className={
                    passwordStatus.type === 'success'
                      ? 'status-success'
                      : 'status-error'
                  }
                >
                  {passwordStatus.message}
                </p>
              )}
              <div className="actions">
                <button className="button-secondary" onClick={closeResetModal}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

function ChatsPage({ navigate, onLogout }) {
  const [chats, setChats] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  const loadChats = useCallback(async () => {
    try {
      setIsLoading(true)
      setErrorMessage('')

      const response = await fetch('/api/chats/', {
        method: 'GET',
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        const message = await extractErrorMessage(
          response,
          `Failed to load chats (${response.status}).`,
        )
        throw new Error(message)
      }

      const data = await response.json()
      setChats(Array.isArray(data) ? data : [])
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not load chats.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const startAiChat = async () => {
    setErrorMessage('')
    try {
      const response = await fetch('/api/chats/select/', {
        method: 'POST',
        headers: getAuthHeaders(true),
        body: JSON.stringify({ mode: 'ai' }),
      })

      if (!response.ok) {
        const message = await extractErrorMessage(
          response,
          `Failed to create AI chat (${response.status}).`,
        )
        throw new Error(message)
      }

      const chat = await response.json()
      if (chat?.id) {
        navigate(`/chats/${chat.id}`)
      } else {
        throw new Error('Chat created but id was missing in response.')
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not start AI chat.')
    }
  }

  useEffect(() => {
    loadChats()
  }, [loadChats])

  return (
    <main className="app-page">
      <AppHeader navigate={navigate} onLogout={onLogout} />
      <section className="app-content">
        <h1>Chats</h1>
        <div className="toolbar">
          <button onClick={loadChats}>Refresh Chats</button>
          <button className="button-secondary" onClick={startAiChat}>
            New AI Chat
          </button>
        </div>

        {isLoading && <p>Loading chats...</p>}
        {!isLoading && errorMessage && <p className="status-error">{errorMessage}</p>}
        {!isLoading && !errorMessage && chats.length === 0 && (
          <p>No chats found yet.</p>
        )}
        {!isLoading && !errorMessage && chats.length > 0 && (
          <div className="chat-list">
            {chats.map((chat) => (
              <article className="chat-item" key={chat.id}>
                <p>
                  <strong>{chat.peer_username || chat.peer_id || 'Unknown user'}</strong>
                </p>
                <p>Type: {chat.kind || '-'}</p>
                <p>Topic: {chat.current_topic || '-'}</p>
                <p>Task: {chat.current_task || '-'}</p>
                <button onClick={() => navigate(`/chats/${chat.id}`)}>Open Chat</button>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

function ChatDetailPage({ navigate, onLogout, chatId }) {
  const [chat, setChat] = useState(null)
  const [messageText, setMessageText] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)

  const loadChat = useCallback(async () => {
    try {
      setIsLoading(true)
      setStatus({ type: '', message: '' })

      const response = await fetch(`/api/chats/${chatId}/`, {
        method: 'GET',
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        const message = await extractErrorMessage(
          response,
          `Failed to load chat (${response.status}).`,
        )
        throw new Error(message)
      }

      const data = await response.json()
      setChat(data)
    } catch (error) {
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Could not load chat.',
      })
    } finally {
      setIsLoading(false)
    }
  }, [chatId])

  useEffect(() => {
    loadChat()
  }, [loadChat])

  const sendMessage = async (event) => {
    event.preventDefault()
    setStatus({ type: '', message: '' })

    try {
      setIsSending(true)
      const response = await fetch(`/api/chats/${chatId}/messages/`, {
        method: 'POST',
        headers: getAuthHeaders(true),
        body: JSON.stringify({ text: messageText.trim() }),
      })

      if (!response.ok) {
        const message = await extractErrorMessage(
          response,
          `Failed to send message (${response.status}).`,
        )
        throw new Error(message)
      }

      setMessageText('')
      await loadChat()
    } catch (error) {
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Could not send message.',
      })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <main className="app-page">
      <AppHeader navigate={navigate} onLogout={onLogout} />
      <section className="app-content">
        <h1>Chat #{chatId}</h1>
        <div className="toolbar">
          <button onClick={() => navigate('/chats')}>Back to Chats</button>
          <button className="button-secondary" onClick={loadChat}>
            Refresh
          </button>
        </div>

        {isLoading && <p>Loading chat...</p>}
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}

        {!isLoading && chat && (
          <>
            <div className="chat-item chat-detail-meta">
              <p>
                <strong>{chat.peer_username || chat.peer_id || 'AI Buddy'}</strong>
              </p>
              <p>Type: {chat.kind || '-'}</p>
              <p>Topic: {chat.current_topic || '-'}</p>
              <p>Task: {chat.current_task || '-'}</p>
            </div>

            <div className="messages-box">
              {Array.isArray(chat.messages) && chat.messages.length > 0 ? (
                chat.messages.map((message) => (
                  <article className="message-item" key={message.id}>
                    <p>
                      <strong>{message.sender_type || 'user'}</strong>
                    </p>
                    <p>{message.content || ''}</p>
                    {message.command && <p>Command: {message.command}</p>}
                  </article>
                ))
              ) : (
                <p>No messages yet.</p>
              )}
            </div>

            <form className="form message-form" onSubmit={sendMessage}>
              <label htmlFor="chat-message">Message</label>
              <input
                id="chat-message"
                type="text"
                value={messageText}
                onChange={(event) => setMessageText(event.target.value)}
                placeholder="Type your message"
                required
              />
              <button type="submit" disabled={isSending || !messageText.trim()}>
                {isSending ? 'Sending...' : 'Send'}
              </button>
            </form>
          </>
        )}
      </section>
    </main>
  )
}

function MatchingPage({ navigate, onLogout }) {
  const [candidates, setCandidates] = useState([])
  const [bestMatch, setBestMatch] = useState(null)
  const [incomingInvites, setIncomingInvites] = useState([])
  const [outgoingInvites, setOutgoingInvites] = useState([])
  const [status, setStatus] = useState({ type: '', message: '' })
  const [isLoading, setIsLoading] = useState(true)

  const loadMatchingData = useCallback(async () => {
    try {
      setIsLoading(true)
      setStatus({ type: '', message: '' })

      const [candidatesRes, matchRes, incomingRes, outgoingRes] = await Promise.all([
        fetch('/api/matching/candidates/', { method: 'GET', headers: getAuthHeaders() }),
        fetch('/api/matching/match/', { method: 'GET', headers: getAuthHeaders() }),
        fetch('/api/matching/invites/incoming/', {
          method: 'GET',
          headers: getAuthHeaders(),
        }),
        fetch('/api/matching/invites/outgoing/', {
          method: 'GET',
          headers: getAuthHeaders(),
        }),
      ])

      if (!candidatesRes.ok) {
        throw new Error(
          await extractErrorMessage(
            candidatesRes,
            `Failed to load candidates (${candidatesRes.status}).`,
          ),
        )
      }
      if (!matchRes.ok) {
        throw new Error(
          await extractErrorMessage(
            matchRes,
            `Failed to load best match (${matchRes.status}).`,
          ),
        )
      }
      if (!incomingRes.ok) {
        throw new Error(
          await extractErrorMessage(
            incomingRes,
            `Failed to load incoming invites (${incomingRes.status}).`,
          ),
        )
      }
      if (!outgoingRes.ok) {
        throw new Error(
          await extractErrorMessage(
            outgoingRes,
            `Failed to load outgoing invites (${outgoingRes.status}).`,
          ),
        )
      }

      const candidatesData = await candidatesRes.json()
      const matchData = await matchRes.json()
      const incomingData = await incomingRes.json()
      const outgoingData = await outgoingRes.json()

      setCandidates(Array.isArray(candidatesData) ? candidatesData : [])
      setBestMatch(matchData ?? null)
      setIncomingInvites(Array.isArray(incomingData) ? incomingData : [])
      setOutgoingInvites(Array.isArray(outgoingData) ? outgoingData : [])
    } catch (error) {
      setStatus({
        type: 'error',
        message:
          error instanceof Error ? error.message : 'Could not load matching data.',
      })
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMatchingData()
  }, [loadMatchingData])

  const sendInvite = async (toUserId) => {
    try {
      setStatus({ type: '', message: '' })
      const response = await fetch('/api/matching/invites/', {
        method: 'POST',
        headers: getAuthHeaders(true),
        body: JSON.stringify({ to_user_id: toUserId }),
      })

      if (!response.ok) {
        throw new Error(
          await extractErrorMessage(
            response,
            `Could not send invite (${response.status}).`,
          ),
        )
      }

      setStatus({ type: 'success', message: 'Invite sent.' })
      await loadMatchingData()
    } catch (error) {
      setStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Could not send invite.',
      })
    }
  }

  const actOnInvite = async (inviteId, action) => {
    try {
      setStatus({ type: '', message: '' })
      const response = await fetch(`/api/matching/invites/${inviteId}/${action}/`, {
        method: 'POST',
        headers: getAuthHeaders(true),
        body: JSON.stringify({ status: 'pending' }),
      })

      if (!response.ok) {
        throw new Error(
          await extractErrorMessage(response, `Could not ${action} invite.`),
        )
      }

      const data = await response.json().catch(() => null)
      if (action === 'accept' && data?.id) {
        navigate(`/chats/${data.id}`)
        return
      }

      setStatus({
        type: 'success',
        message: action === 'accept' ? 'Invite accepted.' : 'Invite rejected.',
      })
      await loadMatchingData()
    } catch (error) {
      setStatus({
        type: 'error',
        message:
          error instanceof Error ? error.message : `Could not ${action} invite.`,
      })
    }
  }

  const openDirectChat = async (peerId) => {
    try {
      setStatus({ type: '', message: '' })
      const response = await fetch('/api/chats/select/', {
        method: 'POST',
        headers: getAuthHeaders(true),
        body: JSON.stringify({ mode: 'person', peer_id: peerId }),
      })

      if (!response.ok) {
        throw new Error(
          await extractErrorMessage(
            response,
            `Could not open direct chat (${response.status}).`,
          ),
        )
      }

      const chat = await response.json()
      if (chat?.id) {
        navigate(`/chats/${chat.id}`)
      }
    } catch (error) {
      setStatus({
        type: 'error',
        message:
          error instanceof Error ? error.message : 'Could not open direct chat.',
      })
    }
  }

  return (
    <main className="app-page">
      <AppHeader navigate={navigate} onLogout={onLogout} />
      <section className="app-content">
        <h1>Matching</h1>
        <div className="toolbar">
          <button onClick={loadMatchingData}>Refresh</button>
          <button className="button-secondary" onClick={() => navigate('/chats')}>
            Go to Chats
          </button>
        </div>

        {isLoading && <p>Loading matching data...</p>}
        {status.message && (
          <p className={status.type === 'success' ? 'status-success' : 'status-error'}>
            {status.message}
          </p>
        )}

        {!isLoading && (
          <div className="matching-grid">
            <section className="chat-item">
              <h2>Best Match</h2>
              {bestMatch ? (
                <>
                  <p>User: {bestMatch.username || '-'}</p>
                  <p>Shared Interests: {bestMatch.shared_interests ?? 0}</p>
                  <p>
                    Interests:{' '}
                    {Array.isArray(bestMatch.interests)
                      ? bestMatch.interests.join(', ')
                      : '-'}
                  </p>
                  {!bestMatch.is_solo && bestMatch.matched_user_id ? (
                    <div className="actions">
                      <button onClick={() => sendInvite(bestMatch.matched_user_id)}>
                        Send Invite
                      </button>
                      <button
                        className="button-secondary"
                        onClick={() => openDirectChat(bestMatch.matched_user_id)}
                      >
                        Open Direct Chat
                      </button>
                    </div>
                  ) : (
                    <p>{bestMatch.detail || 'No direct match found yet.'}</p>
                  )}
                </>
              ) : (
                <p>No best-match data.</p>
              )}
            </section>

            <section className="chat-item">
              <h2>Candidates</h2>
              {candidates.length === 0 && <p>No candidates available.</p>}
              {candidates.map((candidate) => (
                <article className="list-row" key={candidate.user_id}>
                  <div>
                    <p>
                      <strong>{candidate.username}</strong>
                    </p>
                    <p>Shared: {candidate.shared_interests ?? 0}</p>
                  </div>
                  <div className="row-actions">
                    <button onClick={() => sendInvite(candidate.user_id)}>
                      Invite
                    </button>
                    <button
                      className="button-secondary"
                      onClick={() => openDirectChat(candidate.user_id)}
                    >
                      Chat
                    </button>
                  </div>
                </article>
              ))}
            </section>

            <section className="chat-item">
              <h2>Incoming Invites</h2>
              {incomingInvites.length === 0 && <p>No incoming invites.</p>}
              {incomingInvites.map((invite) => (
                <article className="list-row" key={invite.id}>
                  <div>
                    <p>
                      <strong>{invite.from_username}</strong>
                    </p>
                    <p>Status: {invite.status}</p>
                  </div>
                  <div className="row-actions">
                    <button onClick={() => actOnInvite(invite.id, 'accept')}>
                      Accept
                    </button>
                    <button
                      className="button-secondary"
                      onClick={() => actOnInvite(invite.id, 'reject')}
                    >
                      Reject
                    </button>
                  </div>
                </article>
              ))}
            </section>

            <section className="chat-item">
              <h2>Outgoing Invites</h2>
              {outgoingInvites.length === 0 && <p>No outgoing invites.</p>}
              {outgoingInvites.map((invite) => (
                <article className="list-row" key={invite.id}>
                  <div>
                    <p>
                      <strong>{invite.to_username}</strong>
                    </p>
                    <p>Status: {invite.status}</p>
                  </div>
                </article>
              ))}
            </section>
          </div>
        )}
      </section>
    </main>
  )
}

function App() {
  const [path, setPath] = useState(window.location.pathname)
  const [isAuthenticated, setIsAuthenticated] = useState(
    Boolean(localStorage.getItem(TOKEN_KEY)),
  )

  const navigate = useCallback((nextPath, replace = false) => {
    const url = new URL(nextPath, window.location.origin)

    if (
      url.pathname === window.location.pathname &&
      url.search === window.location.search
    ) {
      return
    }

    if (replace) {
      window.history.replaceState({}, '', `${url.pathname}${url.search}`)
    } else {
      window.history.pushState({}, '', `${url.pathname}${url.search}`)
    }
    setPath(url.pathname)
  }, [])

  useEffect(() => {
    const handleLocationChange = () => {
      setPath(window.location.pathname)
      setIsAuthenticated(Boolean(localStorage.getItem(TOKEN_KEY)))
    }

    window.addEventListener('popstate', handleLocationChange)
    return () => window.removeEventListener('popstate', handleLocationChange)
  }, [])

  const effectivePath = useMemo(() => {
    const authOnlyPaths = [
      '/dashboard',
      '/chats',
      '/matching',
      '/profile',
      '/register',
      '/register/verify',
      '/register/password',
      '/register/complete',
      '/forgot-password',
      '/forgot-password/verify',
      '/forgot-password/reset',
      '/login',
    ]

    if (!isAuthenticated) {
      if (
        path.startsWith('/chats/') ||
        ['/dashboard', '/chats', '/matching', '/profile'].includes(path)
      ) {
        return '/'
      }
      return path
    }

    if (isAuthenticated && authOnlyPaths.includes(path) && path.startsWith('/register')) {
      return '/dashboard'
    }

    if (isAuthenticated && path === '/login') {
      return '/dashboard'
    }

    return path
  }, [isAuthenticated, path])

  useEffect(() => {
    if (effectivePath !== path) {
      window.history.replaceState({}, '', effectivePath)
    }
  }, [effectivePath, path])

  const handleLogout = useCallback(async () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    const accessToken = localStorage.getItem(TOKEN_KEY)

    if (refreshToken) {
      try {
        const headers = {
          'Content-Type': 'application/json',
        }

        if (accessToken) {
          headers.Authorization = `Bearer ${accessToken}`
        }

        await fetch(LOGOUT_ENDPOINT, {
          method: 'POST',
          headers,
          body: JSON.stringify({ refresh: refreshToken }),
        })
      } catch {
        // Even if API logout fails, clear local session to log out on client side.
      }
    }

    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    setIsAuthenticated(false)
    navigate('/login', true)
  }, [navigate])

  const page = useMemo(() => {
    if (!isAuthenticated) {
      if (effectivePath === '/login') {
        return (
          <LoginPage
            navigate={navigate}
            onLoginSuccess={() => {
              setIsAuthenticated(true)
              navigate('/dashboard', true)
            }}
          />
        )
      }
      if (effectivePath === '/register') {
        return <RegisterPage navigate={navigate} />
      }
      if (effectivePath === '/register/verify') {
        return <RegisterVerifyPage navigate={navigate} />
      }
      if (effectivePath === '/register/password') {
        return <RegisterPasswordPage navigate={navigate} />
      }
      if (effectivePath === '/register/complete') {
        return <RegisterCompletePage navigate={navigate} />
      }
      if (effectivePath === '/forgot-password') {
        return <ForgotPasswordEmailPage navigate={navigate} />
      }
      if (effectivePath === '/forgot-password/verify') {
        return <ForgotPasswordVerifyPage navigate={navigate} />
      }
      if (effectivePath === '/forgot-password/reset') {
        return <ForgotPasswordResetPage navigate={navigate} />
      }
      return <LandingPage navigate={navigate} />
    }

    if (effectivePath === '/' || effectivePath === '/dashboard') {
      return <DashboardPage navigate={navigate} onLogout={handleLogout} />
    }

    if (effectivePath === '/chats') {
      return <ChatsPage navigate={navigate} onLogout={handleLogout} />
    }

    if (effectivePath.startsWith('/chats/')) {
      const chatId = Number.parseInt(effectivePath.replace('/chats/', ''), 10)
      if (Number.isInteger(chatId)) {
        return (
          <ChatDetailPage
            navigate={navigate}
            onLogout={handleLogout}
            chatId={chatId}
          />
        )
      }
      return <ChatsPage navigate={navigate} onLogout={handleLogout} />
    }

    if (effectivePath === '/matching') {
      return <MatchingPage navigate={navigate} onLogout={handleLogout} />
    }

    if (effectivePath === '/profile') {
      return <ProfilePage navigate={navigate} onLogout={handleLogout} />
    }

    return <DashboardPage navigate={navigate} onLogout={handleLogout} />
  }, [effectivePath, handleLogout, isAuthenticated, navigate])

  return page
}

export default App
