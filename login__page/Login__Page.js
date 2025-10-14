const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const showSignupLink = document.getElementById('show-signup');
const showLoginLink = document.getElementById('show-login');
const messageDiv = document.getElementById('message');

function toggleForms(showForm) {
  messageDiv.style.display = 'none';
  messageDiv.className = '';
  messageDiv.textContent = '';
  loginForm.reset();
  signupForm.reset();

  if (showForm === 'login') {
    loginForm.style.display = 'block';
    signupForm.style.display = 'none';
    document.querySelector('.container h2').textContent = 'Member Login';
  } else {
    loginForm.style.display = 'none';
    signupForm.style.display = 'block';
    document.querySelector('.container h2').textContent = 'Create Account';
  }
}

showSignupLink.addEventListener('click', (e) => {
  e.preventDefault();
  toggleForms('signup');
});

showLoginLink.addEventListener('click', (e) => {
  e.preventDefault();
  toggleForms('login');
});

loginForm.addEventListener('submit', function (event) {
  event.preventDefault();
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;

  const demoUser = 'testuser';
  const demoPass = '12345';

  if (username === demoUser && password === demoPass) {
    messageDiv.textContent = '✅ Success! Logged in.';
    messageDiv.className = 'success';
  } else {
    messageDiv.textContent = '❌ Login failed. Check your credentials.';
    messageDiv.className = 'error';
  }
  messageDiv.style.display = 'block';
});

signupForm.addEventListener('submit', function (event) {
  event.preventDefault();
  const email = document.getElementById('signup-email').value;
  const password = document.getElementById('signup-password').value;
  const confirmPassword = document.getElementById('signup-confirm-password').value;

  if (password !== confirmPassword) {
    messageDiv.textContent = '❌ Sign Up failed! Passwords do not match.';
    messageDiv.className = 'error';
    messageDiv.style.display = 'block';
    return;
  }

  messageDiv.textContent = `🎉 Success! Account created for ${email}. Please log in.`;
  messageDiv.className = 'success';
  messageDiv.style.display = 'block';

  setTimeout(() => {
    toggleForms('login');
  }, 3000);
});