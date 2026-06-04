function showLoginModal() {
    const modal = document.getElementById('login-modal');
    if (!modal) return;
    modal.style.display = 'block';
}

closeLoginModal = () => {
    const modal = document.getElementById('login-modal');
    if (!modal) return;
    modal.style.display = 'none';
}

loginModalOnSubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const res = await api.login(email, password);
    if (res.success) {
        api.notify('Login successful!', 'success');
        closeLoginModal();
        setTimeout(() => { location.reload(); }, 1000);
    } else {
        api.notify('Login failed: ' + res.message, 'error');
    }
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('login-modal');
    if (event.target == modal) {
        closeLoginModal();
    }
}