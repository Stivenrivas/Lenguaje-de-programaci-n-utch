async function api(method, path, body) {
  const opts = {
    method,
    headers: {},
    credentials: 'include'
  };
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body instanceof FormData) {
    opts.body = body;
  }
  let res;
  try {
    res = await fetch('/api' + path + '?_=' + Date.now(), opts);
  } catch (e) {
    throw new Error('No se puede conectar con el servidor. ¿Estará encendido?');
  }
  let data;
  try {
    data = await res.json();
  } catch (e) {
    throw new Error('El servidor respondió con datos inválidos (código ' + res.status + '). Recarga la página.');
  }
  if (!res.ok) throw new Error(data.error || 'Error ' + res.status);
  return data;
}

const LW = {
  // Auth
  me: () => api('GET', '/me'),
  login: (email, password) => api('POST', '/login', { email, password }),
  logout: () => api('POST', '/logout'),
  registro: (data) => api('POST', '/registro', data),

  // Usuarios (admin)
  getUsuarios: () => api('GET', '/usuarios'),
  deleteUsuario: (email) => api('DELETE', `/usuarios/${email}`),

  // Empleos
  getEmpleos: () => api('GET', '/empleos'),
  misEmpleos: () => api('POST', '/empleos/mis'),
  crearEmpleo: (data) => api('POST', '/empleos', data),
  deleteEmpleo: (id) => api('DELETE', `/empleos/${id}`),

  // Servicios
  getServicios: () => api('GET', '/servicios'),
  misServicios: () => api('POST', '/servicios/mis'),
  crearServicio: (data) => api('POST', '/servicios', data),
  deleteServicio: (id) => api('DELETE', `/servicios/${id}`),

  // Upload
  upload: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return api('POST', '/upload', fd);
  },

  // Aplicaciones
  aplicar: (tipo, ref_id, mensaje) => api('POST', '/aplicaciones', { tipo, ref_id, mensaje }),
  aplicacionesRecibidas: () => api('GET', '/aplicaciones/recibidas'),
  aplicacionesEnviadas: () => api('GET', '/aplicaciones/enviadas'),
  cambiarEstadoAplicacion: (id, estado) => api('PATCH', `/aplicaciones/${id}/estado`, { estado }),

  // Contratos
  crearContrato: (data) => api('POST', '/contratos', data),
  misContratos: () => api('GET', '/contratos/mis'),
  finalizarContrato: (id) => api('PATCH', `/contratos/${id}`),

  // Finanzas
  crearFinanza: (data) => api('POST', '/finanzas', data),
  getFinanzas: (year, month) => {
    let q = '';
    if (year && month) q = `?year=${year}&month=${month}`;
    return api('GET', '/finanzas' + q);
  },
  resumenFinanzas: (year, month) => {
    let q = '';
    if (year && month) q = `?year=${year}&month=${month}`;
    return api('GET', '/finanzas/resumen' + q);
  },

  // Mensajes
  enviarMensaje: (data) => api('POST', '/mensajes', data),
  getMensajes: (tipo_ref, ref_id) => api('GET', `/mensajes/${tipo_ref}/${ref_id}`),
  mensajesNoLeidos: () => api('GET', '/mensajes/no-leidos'),
  marcarLeido: (id) => api('PATCH', `/mensajes/leer/${id}`),
  conversaciones: () => api('GET', '/mensajes/conversaciones'),

  // Recomendaciones (usuario)
  recomendaciones: () => api('GET', '/recomendaciones'),

  // Frecuentes (proveedor)
  frecuentes: () => api('GET', '/frecuentes'),

  // Dashboard
  dashboardStats: () => api('GET', '/dashboard/stats'),
};

const SWAL_BASE = {
  background: '#FFFFFF',
  color: '#1E293B',
  confirmButtonColor: '#2563EB',
  cancelButtonColor: '#94A3B8',
  buttonsStyling: true,
  padding: '24px',
};

function swalErr(err) {
  Swal.fire({
    ...SWAL_BASE,
    icon: 'error',
    iconColor: '#EF4444',
    title: 'Error',
    text: err.message || err,
    confirmButtonText: 'Aceptar',
  });
}

function swalOk(msg) {
  Swal.fire({
    ...SWAL_BASE,
    icon: 'success',
    iconColor: '#10B981',
    title: msg,
    timer: 1800,
    showConfirmButton: false,
  });
}

function swalConfirm(title, text) {
  return Swal.fire({
    ...SWAL_BASE,
    icon: 'question',
    iconColor: '#F59E0B',
    title,
    text,
    showCancelButton: true,
    confirmButtonText: 'Sí',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
  });
}
