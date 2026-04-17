const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const btnText = document.getElementById('btnText');
const spinner = document.getElementById('spinner');
const alertContainer = document.getElementById('alertContainer');

// Forgot Password Logic
const forgotModal = document.getElementById('forgotModal');
const stepEmail = document.getElementById('stepEmail');
const stepReset = document.getElementById('stepReset');
const modalAlert = document.getElementById('modalAlert');

function openForgotModal() {
    forgotModal.classList.remove('hidden');
    stepEmail.classList.remove('hidden');
    stepReset.classList.add('hidden');
    modalAlert.classList.add('hidden');
}

function closeForgotModal() {
    forgotModal.classList.add('hidden');
}

function showModalAlert(message, isError = true) {
    modalAlert.textContent = message;
    modalAlert.className = `mt-4 px-4 py-2 rounded text-sm ${isError ? 'bg-red-100 text-red-700 border border-red-400' : 'bg-green-100 text-green-700 border border-green-400'}`;
    modalAlert.classList.remove('hidden');
}

async function sendForgotOtp() {
    const email = document.getElementById('forgotEmail').value.trim();
    if (!email) {
        showModalAlert('Please enter your email.');
        return;
    }

    const btn = document.getElementById('sendOtpBtn');
    const spinner = document.getElementById('otpBtnSpinner');
    
    btn.disabled = true;
    spinner.classList.remove('hidden');
    modalAlert.classList.add('hidden');

    try {
        const response = await fetch(LOGIN_URLS.initiateReset, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email })
        });
        const data = await response.json();
        if (data.success) {
            showModalAlert(data.message, false);
            stepEmail.classList.add('hidden');
            stepReset.classList.remove('hidden');
        } else {
            showModalAlert(data.message);
        }
    } catch (e) {
        showModalAlert('Failed to send OTP.');
    } finally {
        btn.disabled = false;
        spinner.classList.add('hidden');
    }
}

async function resetPassword() {
    const email = document.getElementById('forgotEmail').value.trim();
    const otp = document.getElementById('forgotOtp').value.trim();
    const newPass = document.getElementById('newPass').value;
    const confirmPass = document.getElementById('confirmPass').value;

    if (!otp || !newPass || !confirmPass) {
        showModalAlert('Please fill all fields.');
        return;
    }

    if (newPass !== confirmPass) {
        showModalAlert('Passwords do not match.');
        return;
    }

    const btn = document.getElementById('resetBtn');
    const spinner = document.getElementById('resetBtnSpinner');
    
    btn.disabled = true;
    spinner.classList.remove('hidden');

    try {
        const response = await fetch(LOGIN_URLS.verifyReset, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                otp: otp,
                new_password: newPass
            })
        });
        const data = await response.json();
        if (data.success) {
            showModalAlert(data.message, false);
            setTimeout(() => {
                closeForgotModal();
                showAlert('Password reset successful! You can now login.', 'success');
            }, 2000);
        } else {
            showModalAlert(data.message);
        }
    } catch (e) {
        showModalAlert('Failed to reset password.');
    } finally {
        btn.disabled = false;
        spinner.classList.add('hidden');
    }
}

// Show alert message
function showAlert(message, type = 'error') {
    alertContainer.className = `px-4 py-3 rounded-lg ${
        type === 'success' ? 'bg-green-100 border border-green-400 text-green-700' : 'bg-red-100 border border-red-400 text-red-700'
    }`;
    alertContainer.innerHTML = message;
    alertContainer.classList.remove('hidden');
    alertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Hide alert message
function hideAlert() {
    alertContainer.classList.add('hidden');
}

// Handle form submission
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();

        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('remember').checked;

        // Validation
        if (!email || !password) {
            showAlert('Please fill in all fields.');
            return;
        }

        if (!email.includes('@')) {
            showAlert('Please enter a valid email address.');
            return;
        }

        // Show loading state
        loginBtn.disabled = true;
        btnText.classList.add('hidden');
        spinner.classList.remove('hidden');

        try {
            // Make API request
            const response = await fetch(LOGIN_URLS.login, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                }),
            });

            const data = await response.json();

            if (data.success) {
                // Save tokens to localStorage
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);
                localStorage.setItem('user_data', JSON.stringify(data.user));

                if (rememberMe) {
                    localStorage.setItem('remember_email', email);
                }

                showAlert('Login successful! Redirecting...', 'success');

                setTimeout(() => {
                    window.location.href = LOGIN_URLS.home;
                }, 1000);
            } else {
                showAlert(data.message || 'Login failed. Please try again.');
                loginBtn.disabled = false;
                btnText.classList.remove('hidden');
                spinner.classList.add('hidden');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('An error occurred. Please try again later.');
            loginBtn.disabled = false;
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    });
}

// Load remembered email on page load
window.addEventListener('load', () => {
    const rememberedEmail = localStorage.getItem('remember_email');
    if (rememberedEmail) {
        const emailInput = document.getElementById('email');
        if (emailInput) emailInput.value = rememberedEmail;
        const rememberCheck = document.getElementById('remember');
        if (rememberCheck) rememberCheck.checked = true;
    }
});

// Utility function to get token from localStorage
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Utility function to check if user is logged in
function isLoggedIn() {
    return Boolean(localStorage.getItem('access_token'));
}
