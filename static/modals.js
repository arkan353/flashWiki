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
        api.notify('Вход выполнен', 'success');
        closeLoginModal();
        setTimeout(() => { location.reload(); }, 1000);
    } else {
        api.notify('Ошибка входа: ' + res.message, 'error');
    }
}

showRegisterModal = () => {
    const modal = document.getElementById('register-modal');
    if (!modal) return;
    modal.style.display = 'block';
}

closeRegisterModal = () => {
    const modal = document.getElementById('register-modal');
    if (!modal) return;
    modal.style.display = 'none';
}

registerModalOnSubmit = async (e) => {
    e.preventDefault();
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const res = await api.register(name, email, password);
    if (res.success) {
        api.notify('Регистрация прошла успешно. Теперь можно войти.', 'success');
        closeRegisterModal();

    } else {
        api.notify('Ошибка регистрации: ' + res.message, 'error');
    }
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    if (event.target == loginModal) {
        closeLoginModal();
    } else if (event.target == registerModal) {
        closeRegisterModal();
    }
}

