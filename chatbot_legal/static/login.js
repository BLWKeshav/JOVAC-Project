// Login form handling
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const passwordToggle = document.getElementById('passwordToggle');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // Password toggle functionality
    passwordToggle.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        const icon = passwordToggle.querySelector('i');
        if (type === 'password') {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        } else {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        }
    });

    // Form submission
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide previous errors
        errorMessage.style.display = 'none';
        
        // Get form values
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('rememberMe').checked;

        // Basic validation
        if (!username || !password) {
            showError('Please fill in all fields');
            return;
        }

        // Show loading state
        loginBtn.classList.add('loading');
        loginBtn.disabled = true;
        loginBtn.querySelector('.btn-text').textContent = 'Signing in...';
        loginBtn.querySelector('.btn-icon').classList.remove('fa-arrow-right');
        loginBtn.querySelector('.btn-icon').classList.add('fa-spinner', 'fa-spin');

        try {
            // Send login request
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    rememberMe: rememberMe
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Success - redirect to main page
                loginBtn.querySelector('.btn-text').textContent = 'Success!';
                loginBtn.querySelector('.btn-icon').classList.remove('fa-spinner', 'fa-spin');
                loginBtn.querySelector('.btn-icon').classList.add('fa-check');
                
                // Small delay for visual feedback
                setTimeout(() => {
                    window.location.href = '/';
                }, 500);
            } else {
                // Show error message
                showError(data.message || 'Invalid username or password. Please try again.');
                resetLoginButton();
            }
        } catch (error) {
            console.error('Login error:', error);
            showError('Network error. Please check your connection and try again.');
            resetLoginButton();
        }
    });

    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
        
        // Scroll to error message
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Shake animation
        errorMessage.style.animation = 'none';
        setTimeout(() => {
            errorMessage.style.animation = 'shake 0.5s ease';
        }, 10);
    }

    function resetLoginButton() {
        loginBtn.classList.remove('loading');
        loginBtn.disabled = false;
        loginBtn.querySelector('.btn-text').textContent = 'Sign In';
        loginBtn.querySelector('.btn-icon').classList.remove('fa-spinner', 'fa-spin', 'fa-check');
        loginBtn.querySelector('.btn-icon').classList.add('fa-arrow-right');
    }

    // Auto-focus username field
    document.getElementById('username').focus();

    // Enter key handling (already handled by form submit)
    // Add visual feedback on input focus
    const inputs = document.querySelectorAll('input[type="text"], input[type="password"]');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
});

