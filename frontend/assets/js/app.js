async function api(path, options={}) {
  options.headers = Object.assign({'Content-Type':'application/json','Authorization':'Bearer '+window.API_TOKEN}, options.headers||{});
  const res = await fetch(window.API_URL+path, options);
  if (res.status === 401) {
    if (typeof Swal !== 'undefined') {
      await Swal.fire({
        icon: 'warning',
        title: 'Sesión Expirada (401)',
        text: 'Su sesión ha caducado. Inicie sesión nuevamente.',
        confirmButtonColor: '#0f172a',
        timer: 2000
      });
    }
    location.href = '/logout.php';
    return;
  }
  if (!res.ok) {
    let errData = null;
    try {
      const errJson = await res.json();
      errData = errJson;
      if (typeof errJson.detail === 'string') {
        msg = errJson.detail;
      } else if (errJson.detail && typeof errJson.detail === 'object' && !Array.isArray(errJson.detail)) {
        msg = errJson.detail.message || errJson.detail.msg || JSON.stringify(errJson.detail);
      } else if (Array.isArray(errJson.detail)) {
        msg = errJson.detail.map(d => d.msg || d.message || JSON.stringify(d)).join(' | ');
      } else if (errJson.message) {
        msg = errJson.message;
      } else {
        msg = JSON.stringify(errJson);
      }
    } catch {
      msg = await res.text().catch(() => '');
    }
    const err = new Error(msg || `Error de servidor (HTTP ${res.status})`);
    err.status = res.status;
    err.data = errData;
    throw err;
  }
  return res.status === 204 ? null : res.json();
}
function esc(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
