const API = 'http://localhost:5000/api';

function togglePass(inputId, el) {
    const input = document.getElementById(inputId);
    const icon = el.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

function showAlert(msg, type) {
    const el = document.getElementById('floatAlert');
    el.innerHTML = '<i class="fas fa-' + (type === 'error' ? 'exclamation-circle' : 'check-circle') + '"></i> ' + msg;
    el.className = 'float-alert float-' + type;
    el.style.display = 'flex';
    setTimeout(function() {
        el.style.display = 'none';
    }, 4000);
}

function switchTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    if (tab === 'login') {
        document.querySelectorAll('.auth-tab')[0].classList.add('active');
        document.getElementById('loginForm').classList.add('active');
    } else {
        document.querySelectorAll('.auth-tab')[1].classList.add('active');
        document.getElementById('registerForm').classList.add('active');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    try {
        const res = await fetch(API + '/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (res.ok) {
            window.location.href = '/home';
        } else {
            showAlert(data.error, 'error');
        }
    } catch(e) {
        showAlert('Error de conexion con el servidor', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const nombre = document.getElementById('regNombre').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirm = document.getElementById('regConfirm').value;
    if (password !== confirm) {
        showAlert('Las contrasenas no coinciden', 'error');
        return;
    }
    if (password.length < 8) {
        showAlert('La contrasena debe tener al menos 8 caracteres', 'error');
        return;
    }
    try {
        const res = await fetch(API + '/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, email, password })
        });
        const data = await res.json();
        if (res.ok) {
            showAlert('Registro exitoso! Ahora puedes iniciar sesion.', 'success');
            document.querySelector('form').reset();
            setTimeout(() => switchTab('login'), 1500);
        } else {
            showAlert(data.error, 'error');
        }
    } catch(e) {
        showAlert('Error de conexion con el servidor', 'error');
    }
}