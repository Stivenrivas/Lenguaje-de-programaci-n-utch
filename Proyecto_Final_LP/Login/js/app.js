function togglePW(id, btn) {
  const input = document.getElementById(id);
  const icon = btn.querySelector('i');
  input.type = input.type === 'password' ? 'text' : 'password';
  icon.textContent = input.type === 'password' ? 'visibility_off' : 'visibility';
}

// SWAL_BASE ya viene declarada en api.js (se carga antes que este archivo
// y ambos comparten el mismo scope global). No la vuelvas a declarar aquí:
// hacerlo con "const" duplicado rompe TODO este script con un SyntaxError,
// y por eso ningún listener de abajo llegaba a registrarse.

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('loginPassword').value = '';
  M.AutoInit();

  // Toggle login / register
  function showLogin() {
    document.getElementById('loginCard').style.display = 'block';
    document.getElementById('registerCard').style.display = 'none';
    document.getElementById('showLoginBtn').classList.add('active');
    document.getElementById('showRegisterBtn').classList.remove('active');
  }

  function showRegister() {
    document.getElementById('loginCard').style.display = 'none';
    document.getElementById('registerCard').style.display = 'block';
    document.getElementById('showRegisterBtn').classList.add('active');
    document.getElementById('showLoginBtn').classList.remove('active');
  }

  document.getElementById('showLoginBtn').addEventListener('click', showLogin);
  document.getElementById('showRegisterBtn').addEventListener('click', showRegister);

  // Login
  document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    document.getElementById('loginBtn').disabled = true;
    document.getElementById('loginBtn').innerHTML = '<i class="material-icons left">hourglass_empty</i>Ingresando...';
    try {
      const user = await LW.login(email, password);
      const routes = {
        usuario: '../wed_site/usuario.html',
        empleador: '../wed_site/empleador.html',
        proveedor: '../wed_site/provedor.html',
        admin: '../wed_site/dashboard.html',
      };
      window.location.href = routes[user.role] || '../wed_site/usuario.html';
    } catch (err) {
      Swal.fire({ ...SWAL_BASE, icon: 'error', iconColor: '#EF4444', title: 'Error al iniciar sesión', text: err.message, confirmButtonText: 'Aceptar' });
      document.getElementById('loginBtn').disabled = false;
      document.getElementById('loginBtn').innerHTML = 'Ingresar<i class="material-icons right">arrow_forward</i>';
    }
  });

  // Register
  document.getElementById('registerForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const data = {
      username: document.getElementById('regUsername').value.trim(),
      email: document.getElementById('regEmail').value.trim(),
      phone: document.getElementById('regPhone').value.trim(),
      password: document.getElementById('regPassword').value.trim(),
      role: document.getElementById('regRole').value,
    };
    document.getElementById('registerBtn').disabled = true;
    document.getElementById('registerBtn').innerHTML = '<i class="material-icons left">hourglass_empty</i>Creando...';
    try {
      await LW.registro(data);
      Swal.fire({ ...SWAL_BASE, icon: 'success', iconColor: '#10B981', title: 'Cuenta creada', text: 'Tu cuenta fue creada correctamente. Inicia sesión.', timer: 2500, showConfirmButton: false });
      document.getElementById('registerForm').reset();
      M.updateTextFields();
      M.FormSelect.init(document.getElementById('regRole'));
      showLogin();
    } catch (err) {
      Swal.fire({ ...SWAL_BASE, icon: 'error', iconColor: '#EF4444', title: 'Error al registrarse', text: err.message, confirmButtonText: 'Aceptar' });
    }
    document.getElementById('registerBtn').disabled = false;
    document.getElementById('registerBtn').innerHTML = 'Crear Cuenta<i class="material-icons right">person_add</i>';
  });

  M.updateTextFields();
});