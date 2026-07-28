const API = 'http://localhost:5000/api';
var currentUser = null;
var destinos = [];

async function checkSession() {
    try {
        var res = await fetch(API + '/session', { credentials: 'include' });
        if (res.ok) {
            var data = await res.json();
            currentUser = data.user;
            updateAuthUI();
            loadHomeDestinos();
            return;
        }
    } catch(e) {}
    window.location.href = '/login/';
}

function updateAuthUI() {
    var auth = document.getElementById('authLinks');
    var user = document.getElementById('userLinks');
    var name = document.getElementById('userName');
    var admin = document.getElementById('adminLink');
    if (currentUser) {
        if (auth) auth.style.display = 'none';
        if (user) user.style.display = 'flex';
        if (name) name.textContent = currentUser.nombre;
        var dashLink = document.getElementById('dashLink');
        if (admin) admin.style.display = currentUser.rol === 'admin' ? 'flex' : 'none';
        if (dashLink) dashLink.style.display = currentUser.rol === 'admin' ? 'flex' : 'none';
    } else {
        if (auth) auth.style.display = 'flex';
        if (user) user.style.display = 'none';
    }
}

function showView(id) {
    var views = document.querySelectorAll('.view');
    for (var i = 0; i < views.length; i++) views[i].classList.remove('active');
    var v = document.getElementById('view-' + id);
    if (v) v.classList.add('active');
    var links = document.querySelectorAll('.nav-link');
    for (var j = 0; j < links.length; j++) links[j].classList.remove('active');
    for (var k = 0; k < links.length; k++) {
        var onclick = links[k].getAttribute('onclick');
        if (onclick && onclick.indexOf("'" + id + "'") !== -1) links[k].classList.add('active');
    }
    document.getElementById('navMenu') && document.getElementById('navMenu').classList.remove('show');
    if (id === 'destinos') loadDestinos();
    if (id === 'admin') { loadAdminDestinos(); loadAdminUsuarios(); }
    if (id === 'dashboard') loadDashboard();
    if (id === 'home') loadHomeDestinos();
    if (id === 'perfil') showProfile();
}

function toggleMenu() {
    document.getElementById('navMenu').classList.toggle('show');
}

function showToast(msg, type) {
    if (!type) type = 'success';
    var t = document.getElementById('toast');
    t.className = 'toast ' + type + ' show';
    t.innerHTML = msg;
    setTimeout(function() { t.classList.remove('show'); }, 3000);
}

var confirmCb = null;
function showConfirm(msg, cb) {
    confirmCb = cb;
    document.getElementById('confirmMessage').textContent = msg;
    document.getElementById('confirmModal').classList.add('active');
    document.getElementById('confirmBtn').onclick = function() { closeConfirm(); if (confirmCb) confirmCb(); };
}
function closeConfirm() { document.getElementById('confirmModal').classList.remove('active'); }

async function logout() {
    await fetch(API + '/logout', { method: 'POST', credentials: 'include' });
    currentUser = null;
    updateAuthUI();
    showToast('Sesion cerrada');
    window.location.href = '/';
}

var carousels = [];

async function loadDestinos() {
    var g = document.getElementById('destinosList');
    g.innerHTML = '<p class="loading">Cargando...</p>';
    try {
        var res = await fetch(API + '/destinos', { credentials: 'include' });
        var data = await res.json();
        destinos = data;
        renderDestinos(destinos);
        loadFilterOpts();
    } catch(e) { g.innerHTML = '<p class="loading">Error al cargar destinos</p>'; }
}

async function loadHomeDestinos() {
    var g = document.getElementById('homeDestinos');
    if (!g) return;
    try {
        var res = await fetch(API + '/destinos', { credentials: 'include' });
        var data = await res.json();
        renderDestinosList(g, data);
    } catch(e) { g.innerHTML = '<p class="loading">Error al cargar</p>'; }
}

function renderDestinos(list) { renderDestinosList(document.getElementById('destinosList'), list); }

function getImgs(urlStr) {
    if (!urlStr) return [];
    return urlStr.split(',').map(function(s) { return s.trim(); }).filter(function(s) { return s; });
}

var carouselColors = ['#1a5a3a','#0d6b7a','#2d8a5e','#1a3a5a','#5a3a1a','#3a1a5a','#8a5e2d','#5e2d8a'];

function renderDestinosList(container, list) {
    carousels = [];
    if (!list || !list.length) { container.innerHTML = '<p class="loading">No hay destinos disponibles</p>'; return; }
    var html = '';
    for (var i = 0; i < list.length; i++) {
        var d = list[i];
        var imgs = getImgs(d.imagen_url);

        var slidesHtml = '';
        if (imgs.length === 0) {
            slidesHtml += '<div class="carousel-slide"><div class="carousel-slide-placeholder" style="background:' + carouselColors[i % carouselColors.length] + '"><i class="fas fa-mountain"></i> ' + escapeHtml(d.nombre) + '</div></div>';
        } else {
            for (var j = 0; j < imgs.length; j++) {
                if (imgs[j] && imgs[j].indexOf('/img/') === 0) {
                    slidesHtml += '<div class="carousel-slide"><img src="' + imgs[j] + '" alt="' + escapeHtml(d.nombre) + '" onerror="this.outerHTML=\'<div class=\\\\\\"carousel-slide-placeholder\\\\\\" style=\\\\\\"background:\' + carouselColors[(i+j) % carouselColors.length] + \'\\\\\\"><i class=\\\\\\"fas fa-image\\\\\\"></i> ' + escapeHtml(d.nombre) + '</div>\'"></div>';
                } else {
                    slidesHtml += '<div class="carousel-slide"><div class="carousel-slide-placeholder" style="background:' + carouselColors[(i+j) % carouselColors.length] + '"><i class="fas fa-image"></i> ' + escapeHtml(d.nombre) + '</div></div>';
                }
            }
        }

        var dotsHtml = '';
        for (var j = 0; j < imgs.length; j++) {
            dotsHtml += '<button class="carousel-dot' + (j === 0 ? ' active' : '') + '" onclick="goToSlide(' + i + ',' + j + ')"></button>';
        }

        var actHtml = '';
        if (d.actividades) {
            var acts = d.actividades.split(',').map(function(s) { return s.trim(); }).filter(function(s) { return s; });
            actHtml = '<div class="destino-section-actividades"><h4><i class="fas fa-tasks"></i> Actividades</h4><div class="actividades-list">';
            for (var a = 0; a < acts.length; a++) {
                actHtml += '<span class="actividad-tag"><i class="fas fa-check-circle"></i> ' + escapeHtml(acts[a]) + '</span>';
            }
            actHtml += '</div></div>';
        }

        html += '<div class="destino-section" id="destinoSec' + i + '">' +
            '<div class="destino-carousel" id="carousel' + i + '">' +
            '<div class="carousel-track" id="carouselTrack' + i + '">' + slidesHtml + '</div>' +
            (imgs.length > 1 ? '<button class="carousel-btn carousel-prev" onclick="prevSlide(' + i + ')"><i class="fas fa-chevron-left"></i></button>' : '') +
            (imgs.length > 1 ? '<button class="carousel-btn carousel-next" onclick="nextSlide(' + i + ')"><i class="fas fa-chevron-right"></i></button>' : '') +
            (imgs.length > 1 ? '<div class="carousel-dots" id="carouselDots' + i + '">' + dotsHtml + '</div>' : '') +
            '</div>' +
            '<div class="destino-section-body">' +
            '<h2>' + escapeHtml(d.nombre) + '</h2>' +
            '<div class="destino-section-tags">' +
            '<span><i class="fas fa-city"></i> ' + escapeHtml(d.municipio) + '</span>' +
            '<span class="badge">' + escapeHtml(d.categoria) + '</span>' +
            '</div>' +
            '<p class="destino-section-desc">' + escapeHtml(d.descripcion || 'Sin descripcion disponible.') + '</p>' +
            actHtml +
            (d.ubicacion ? '<div class="destino-section-extra"><p><i class="fas fa-map-pin"></i> ' + escapeHtml(d.ubicacion) + '</p></div>' : '') +
            '</div></div>';
    }
    container.innerHTML = html;

    for (var i = 0; i < list.length; i++) {
        var imgs = getImgs(list[i].imagen_url);
        carousels[i] = { current: 0, total: Math.max(imgs.length, 1), timer: null };
        startAutoplay(i);
    }
}

function prevSlide(idx) {
    var c = carousels[idx];
    if (!c) return;
    c.current = (c.current - 1 + c.total) % c.total;
    updateCarousel(idx);
    resetAutoplay(idx);
}

function nextSlide(idx) {
    var c = carousels[idx];
    if (!c) return;
    c.current = (c.current + 1) % c.total;
    updateCarousel(idx);
    resetAutoplay(idx);
}

function goToSlide(idx, slideIdx) {
    var c = carousels[idx];
    if (!c) return;
    c.current = slideIdx;
    updateCarousel(idx);
    resetAutoplay(idx);
}

function updateCarousel(idx) {
    var c = carousels[idx];
    var track = document.getElementById('carouselTrack' + idx);
    var dots = document.getElementById('carouselDots' + idx);
    if (track) {
        track.style.transform = 'translateX(-' + (c.current * 100) + '%)';
    }
    if (dots) {
        var dotEls = dots.querySelectorAll('.carousel-dot');
        for (var i = 0; i < dotEls.length; i++) {
            dotEls[i].classList.toggle('active', i === c.current);
        }
    }
}

function startAutoplay(idx) {
    var c = carousels[idx];
    if (!c || c.total <= 1) return;
    c.timer = setInterval(function() {
        nextSlide(idx);
    }, 5000);
}

function resetAutoplay(idx) {
    var c = carousels[idx];
    if (!c) return;
    if (c.timer) clearInterval(c.timer);
    startAutoplay(idx);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

function showDetalle(idx) {
    var d = destinos[idx];
    if (!d) return;
    showView('detalle');
    var el = document.getElementById('destinoDetail');
    var imgHtml = '<div class="destino-detail-placeholder"><i class="fas fa-mountain"></i></div>';
    if (d.imagen_url) {
        imgHtml = '<img class="destino-detail-img" src="' + d.imagen_url + '" alt="' + d.nombre + '" onerror="this.style.display=\'none\';this.parentNode.innerHTML=\'<div class=\\\\\\"destino-detail-placeholder\\\\\\"><i class=\\\\\\"fas fa-mountain\\\\\\"></i></div>\'">';
    }
    var actHtml = '';
    if (d.actividades) {
        var acts = d.actividades.split(',').map(function(s) { return s.trim(); }).filter(function(s) { return s; });
        actHtml = '<div class="detalle-actividades"><h4><i class="fas fa-tasks"></i> Actividades</h4><div class="actividades-list">';
        for (var a = 0; a < acts.length; a++) {
            actHtml += '<span class="actividad-tag"><i class="fas fa-check-circle"></i> ' + escapeHtml(acts[a]) + '</span>';
        }
        actHtml += '</div></div>';
    }

    el.innerHTML = imgHtml +
        '<div class="destino-detail-body">' +
        '<h2>' + escapeHtml(d.nombre) + '</h2>' +
        '<div class="destino-detail-meta">' +
        '<span><i class="fas fa-city"></i> ' + escapeHtml(d.municipio) + '</span>' +
        '<span class="badge">' + escapeHtml(d.categoria) + '</span>' +
        (d.ubicacion ? '<span><i class="fas fa-map-pin"></i> ' + escapeHtml(d.ubicacion) + '</span>' : '') +
        '</div><p>' + escapeHtml(d.descripcion || 'Sin descripcion disponible.') + '</p>' + actHtml + '</div>';
}

function loadFilterOpts() {
    var munSet = {}, catSet = {};
    for (var i = 0; i < destinos.length; i++) {
        if (destinos[i].municipio) munSet[destinos[i].municipio] = 1;
        if (destinos[i].categoria) catSet[destinos[i].categoria] = 1;
    }
    var muns = Object.keys(munSet).sort();
    var cats = Object.keys(catSet);
    var ms = document.getElementById('filterMunicipio');
    var cs = document.getElementById('filterCategoria');
    if (!ms || !cs) return;
    var cv = ms.value, cv2 = cs.value;
    ms.innerHTML = '<option value="">Todos los municipios</option>';
    for (var j = 0; j < muns.length; j++) ms.innerHTML += '<option value="' + muns[j] + '">' + muns[j] + '</option>';
    cs.innerHTML = '<option value="">Todas las categorias</option>';
    for (var k = 0; k < cats.length; k++) cs.innerHTML += '<option value="' + cats[k] + '">' + cats[k] + '</option>';
    ms.value = cv; cs.value = cv2;
}

function filterDestinos() {
    var s = document.getElementById('searchInput').value.toLowerCase();
    var m = document.getElementById('filterMunicipio').value;
    var ct = document.getElementById('filterCategoria').value;
    var f = [];
    for (var i = 0; i < destinos.length; i++) {
        var d = destinos[i];
        if (s && d.nombre.toLowerCase().indexOf(s) === -1 && (d.descripcion || '').toLowerCase().indexOf(s) === -1) continue;
        if (m && d.municipio !== m) continue;
        if (ct && d.categoria !== ct) continue;
        f.push(d);
    }
    renderDestinos(f);
}

function switchAdminTab(tab, btn) {
    var btns = document.querySelectorAll('.tab-btn');
    for (var i = 0; i < btns.length; i++) btns[i].classList.remove('active');
    btn.classList.add('active');
    var tabs = document.querySelectorAll('.admin-tab');
    for (var j = 0; j < tabs.length; j++) tabs[j].classList.remove('active');
    document.getElementById('admin' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
}

async function loadAdminDestinos() {
    var tb = document.getElementById('adminDestinosTable');
    if (!tb) return;
    try {
        var res = await fetch(API + '/destinos', { credentials: 'include' });
        var data = await res.json();
        var html = '';
        for (var i = 0; i < data.length; i++) {
            var d = data[i];
            html += '<tr><td>' + d.id + '</td><td>' + escapeHtml(d.nombre) + '</td><td>' + escapeHtml(d.municipio) + '</td>' +
                '<td><span class="badge">' + escapeHtml(d.categoria) + '</span></td>' +
                '<td class="actions"><button class="btn btn-secondary btn-sm" onclick="editDestino(' + d.id + ')"><i class="fas fa-edit"></i></button> ' +
                '<button class="btn btn-danger btn-sm" onclick="deleteDestino(' + d.id + ')"><i class="fas fa-trash"></i></button></td></tr>';
        }
        tb.innerHTML = html;
    } catch(e) { tb.innerHTML = '<tr><td colspan="5">Error</td></tr>'; }
}

async function loadAdminUsuarios() {
    var tb = document.getElementById('adminUsuariosTable');
    if (!tb) return;
    try {
        var res = await fetch(API + '/usuarios', { credentials: 'include' });
        var data = await res.json();
        var html = '';
        for (var i = 0; i < data.length; i++) {
            var u = data[i];
            html += '<tr><td>' + u.id + '</td><td>' + escapeHtml(u.nombre) + '</td><td>' + escapeHtml(u.email) + '</td>' +
                '<td><span class="badge">' + (u.rol === 'admin' ? 'Admin' : 'Usuario') + '</span></td><td>';
            if (u.rol !== 'admin') html += '<button class="btn btn-danger btn-sm" onclick="deleteUsuario(' + u.id + ')"><i class="fas fa-user-minus"></i></button>';
            else html += '<span class="badge">---</span>';
            html += '</td></tr>';
        }
        tb.innerHTML = html;
    } catch(e) { tb.innerHTML = '<tr><td colspan="5">Error</td></tr>'; }
}

function openDestinoModal(d) {
    document.getElementById('destinoModal').classList.add('active');
    document.getElementById('destinoForm').reset();
    document.getElementById('destinoId').value = '';
    if (d) {
        document.getElementById('modalTitle').innerHTML = '<i class="fas fa-edit"></i> Editar Destino';
        document.getElementById('modalSubmitBtn').innerHTML = '<i class="fas fa-save"></i> Actualizar';
        document.getElementById('destinoId').value = d.id;
        document.getElementById('destinoNombre').value = d.nombre;
        document.getElementById('destinoDescripcion').value = d.descripcion || '';
        document.getElementById('destinoActividades').value = d.actividades || '';
        document.getElementById('destinoMunicipio').value = d.municipio || '';
        document.getElementById('destinoCategoria').value = d.categoria || '';
        document.getElementById('destinoUbicacion').value = d.ubicacion || '';
        document.getElementById('destinoImagen').value = d.imagen_url || '';
    } else {
        document.getElementById('modalTitle').innerHTML = '<i class="fas fa-map-marker-alt"></i> Nuevo Destino';
        document.getElementById('modalSubmitBtn').innerHTML = '<i class="fas fa-save"></i> Guardar';
    }
}

function closeDestinoModal() { document.getElementById('destinoModal').classList.remove('active'); }

async function handleDestinoSubmit(e) {
    e.preventDefault();
    var id = document.getElementById('destinoId').value;
    var data = {
        nombre: document.getElementById('destinoNombre').value,
        descripcion: document.getElementById('destinoDescripcion').value,
        actividades: document.getElementById('destinoActividades').value,
        municipio: document.getElementById('destinoMunicipio').value,
        categoria: document.getElementById('destinoCategoria').value,
        ubicacion: document.getElementById('destinoUbicacion').value,
        imagen_url: document.getElementById('destinoImagen').value
    };
    var url = id ? API + '/destinos/' + id : API + '/destinos';
    var method = id ? 'PUT' : 'POST';
    try {
        var res = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify(data) });
        if (res.ok) {
            showToast(id ? 'Destino actualizado' : 'Destino creado');
            closeDestinoModal();
            loadAdminDestinos();
            loadDestinos();
        } else {
            var err = await res.json();
            showToast(err.error || 'Error', 'error');
        }
    } catch(e) { showToast('Error de conexion', 'error'); }
}

async function editDestino(id) {
    try {
        var res = await fetch(API + '/destinos/' + id, { credentials: 'include' });
        var d = await res.json();
        openDestinoModal(d);
    } catch(e) { showToast('Error', 'error'); }
}

function deleteDestino(id) {
    showConfirm('Eliminar este destino?', async function() {
        var res = await fetch(API + '/destinos/' + id, { method: 'DELETE', credentials: 'include' });
        if (res.ok) { showToast('Destino eliminado'); loadAdminDestinos(); loadDestinos(); }
    });
}

function deleteUsuario(id) {
    showConfirm('Eliminar este usuario?', async function() {
        var res = await fetch(API + '/usuarios/' + id, { method: 'DELETE', credentials: 'include' });
        if (res.ok) { showToast('Usuario eliminado'); loadAdminUsuarios(); }
    });
}

function showProfile() {
    document.getElementById('profileName').textContent = currentUser ? currentUser.nombre : '';
    document.getElementById('profileEmail').textContent = currentUser ? currentUser.email : '';
    document.getElementById('profileRol').textContent = currentUser && currentUser.rol === 'admin' ? 'Administrador' : 'Usuario';
}

async function loadDashboard() {
    try {
        var res = await fetch(API + '/destinos', { credentials: 'include' });
        var dests = await res.json();
        var res2 = await fetch(API + '/usuarios', { credentials: 'include' });
        var users = [];
        if (res2.ok) { users = await res2.json(); }

        var munSet = {}, catSet = {};
        for (var i = 0; i < dests.length; i++) {
            if (dests[i].municipio) munSet[dests[i].municipio] = 1;
            if (dests[i].categoria) catSet[dests[i].categoria] = 1;
        }

        var de = document.getElementById('dashDestinos');
        var ue = document.getElementById('dashUsuarios');
        var me = document.getElementById('dashMunicipios');
        var ce = document.getElementById('dashCategorias');
        var re = document.getElementById('dashRecentDestinos');

        if (de) de.textContent = dests.length;
        if (ue) ue.textContent = users.length;
        if (me) me.textContent = Object.keys(munSet).length;
        if (ce) ce.textContent = Object.keys(catSet).length;

        if (re) {
            var recent = dests.slice(0, 5);
            var html = '';
            for (var j = 0; j < recent.length; j++) {
                html += '<div class="dash-list-item"><span class="name">' + escapeHtml(recent[j].nombre) + '</span><span class="meta"><span>' + escapeHtml(recent[j].municipio) + '</span><span class="badge">' + escapeHtml(recent[j].categoria) + '</span></span></div>';
            }
            re.innerHTML = html || '<p class="loading">No hay destinos</p>';
        }
    } catch(e) {
        var re = document.getElementById('dashRecentDestinos');
        if (re) re.innerHTML = '<p class="loading">Error al cargar dashboard</p>';
    }
}

checkSession();