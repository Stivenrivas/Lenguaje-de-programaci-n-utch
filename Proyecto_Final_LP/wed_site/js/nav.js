document.addEventListener('DOMContentLoaded', async function () {
  let user;
  try {
    user = await LW.me();
  } catch (_) {
    window.location.href = '../Login/index.html';
    return;
  }

  const usernameEl = document.getElementById('navUsername');
  if (usernameEl) usernameEl.textContent = user.username;

  M.Dropdown.init(document.querySelectorAll('.dropdown-trigger'), { constrainWidth: false, coverTrigger: false });
  M.Sidenav.init(document.querySelectorAll('.sidenav'));
  M.Tabs.init(document.querySelectorAll('.tabs'));

  async function logout() {
    try { await LW.logout(); } catch (_) {}
    window.location.href = '../Login/index.html';
  }

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', function (e) { e.preventDefault(); logout(); });

  const mobileLogout = document.getElementById('mobileLogout');
  if (mobileLogout) mobileLogout.addEventListener('click', function (e) { e.preventDefault(); logout(); });
});
