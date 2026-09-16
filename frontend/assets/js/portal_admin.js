/**
 * PORTAL ACADÉMICO - LÓGICA INTEGRAL DEL ADMINISTRADOR (SPA)
 * Mismo modelo visual, acordeones (+ / -), navegación dinámica y componentes del Estudiante.
 */

let moduloActualAdmin = 'dashboard';
let estudiantesGlobal = [];
let cursosGlobal = [];
let matriculasGlobal = [];
let backupsGlobal = [];
let programacionesGlobal = [];

// Mapeo de sub-rutas a módulos padre acordeón
const moduloToParentMap = {
  'estudiantes-lista': 'estudiantes',
  'estudiantes-nuevo': 'estudiantes',
  'estudiantes-estado': 'estudiantes',
  'cursos-lista': 'cursos',
  'cursos-nuevo': 'cursos',
  'matriculas-lista': 'matriculas',
  'matriculas-nueva': 'matriculas',
  'backups-panel': 'backups',
  'backups-crear': 'backups',
  'backups-explorador': 'backups',
  'backups-guardados': 'backups',
  'backups-programacion': 'backups',
  'backups-historial': 'backups',
  'backups-restauraciones': 'backups'
};

const allAccordionModules = ['estudiantes', 'cursos', 'matriculas', 'backups'];

const allNavIds = [
  'nav-dashboard',
  'nav-estudiantes-lista', 'nav-estudiantes-nuevo', 'nav-estudiantes-estado',
  'nav-cursos-lista', 'nav-cursos-nuevo',
  'nav-matriculas-lista', 'nav-matriculas-nueva',
  'nav-backups-panel', 'nav-backups-crear', 'nav-backups-explorador', 'nav-backups-guardados',
  'nav-backups-programacion', 'nav-backups-historial', 'nav-backups-restauraciones'
];

document.addEventListener('DOMContentLoaded', async () => {
  // Toggle dropdown perfil superior
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userDropdown = document.getElementById('userDropdown');
  if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('hidden');
    });
    document.addEventListener('click', () => {
      userDropdown.classList.add('hidden');
    });
  }

  // Toggle sidebar en móviles
  const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('-translate-x-full');
    });
  }

  // Revisar si hay un parámetro 'modulo' en la URL
  const urlParams = new URLSearchParams(window.location.search);
  const modParam = urlParams.get('modulo') || 'dashboard';

  await cargarModuloAdmin(modParam);
});

// =========================================================================
// GESTIÓN DE ACORDEÓN (+ / -) Y RESALTADO DE SIDEBAR
// =========================================================================

function toggleAdminAccordion(modName, autoOpenOnly = false) {
  const targetSubmenu = document.getElementById(`submenu-${modName}`);
  const targetIcon = document.getElementById(`icon-${modName}`);
  const targetHeader = document.getElementById(`header-${modName}`);
  if (!targetSubmenu) return;

  const isCurrentlyOpen = targetSubmenu.classList.contains('open');

  if (isCurrentlyOpen && !autoOpenOnly) {
    // Si ya está abierto y el usuario hace clic, cerrarlo
    targetSubmenu.classList.remove('open');
    if (targetIcon) targetIcon.textContent = '+';
    if (targetHeader) {
      targetHeader.classList.remove('text-white', 'bg-[#1e293b]');
      targetHeader.classList.add('text-slate-300');
    }
  } else {
    // Cerrar TODOS los demás módulos acordeón
    allAccordionModules.forEach(m => {
      const sub = document.getElementById(`submenu-${m}`);
      const ico = document.getElementById(`icon-${m}`);
      const hdr = document.getElementById(`header-${m}`);
      if (sub) sub.classList.remove('open');
      if (ico) ico.textContent = '+';
      if (hdr) {
        hdr.classList.remove('text-white', 'bg-[#1e293b]');
        hdr.classList.add('text-slate-300');
      }
    });

    // Abrir el módulo objetivo
    targetSubmenu.classList.add('open');
    if (targetIcon) targetIcon.textContent = '-';
    if (targetHeader) {
      targetHeader.classList.remove('text-slate-300');
      targetHeader.classList.add('text-white', 'bg-[#1e293b]');
    }
  }
}

function actualizarResaltadoSidebar(modulo) {
  allNavIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('text-rose-500', 'font-semibold', 'bg-slate-900/40');
      if (id !== 'nav-dashboard') {
        el.classList.add('text-slate-400');
      }
    }
  });

  const parentMod = moduloToParentMap[modulo];
  if (parentMod) {
    toggleAdminAccordion(parentMod, true);
  } else if (modulo === 'dashboard') {
    allAccordionModules.forEach(m => {
      const sub = document.getElementById(`submenu-${m}`);
      const ico = document.getElementById(`icon-${m}`);
      const hdr = document.getElementById(`header-${m}`);
      if (sub) sub.classList.remove('open');
      if (ico) ico.textContent = '+';
      if (hdr) {
        hdr.classList.remove('text-white', 'bg-[#1e293b]');
        hdr.classList.add('text-slate-300');
      }
    });
  }

  const currentNav = document.getElementById(`nav-${modulo}`);
  if (currentNav) {
    currentNav.classList.remove('text-slate-400');
    currentNav.classList.add('text-rose-500', 'font-semibold', 'bg-slate-900/40');
  }
}

// =========================================================================
// ENRUTADOR PRINCIPAL (SPA)
// =========================================================================

async function cargarModuloAdmin(modulo) {
  if (modulo === 'backups-crear') {
    abrirModalCrearBackup();
    return;
  }

  moduloActualAdmin = modulo;
  actualizarResaltadoSidebar(modulo);

  const container = document.getElementById('dynamicContentContainer');
  if (!container) return;

  container.innerHTML = `
    <div class="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
      <i class="fa fa-spinner fa-spin text-3xl text-[#f4511e]"></i>
      <p class="text-xs font-medium">Cargando registros oficiales...</p>
    </div>
  `;

  try {
    switch (modulo) {
      case 'dashboard':
        await renderDashboardView(container);
        break;

      // Estudiantes
      case 'estudiantes':
      case 'estudiantes-lista':
        await renderEstudiantesListaView(container);
        break;
      case 'estudiantes-nuevo':
        await renderEstudiantesNuevoView(container);
        break;
      case 'estudiantes-estado':
        await renderEstudiantesEstadoView(container);
        break;

      // Cursos
      case 'cursos':
      case 'cursos-lista':
        await renderCursosListaView(container);
        break;
      case 'cursos-nuevo':
        await renderCursosNuevoView(container);
        break;

      // Matrículas
      case 'matriculas':
      case 'matriculas-lista':
        await renderMatriculasListaView(container);
        break;
      case 'matriculas-nueva':
        await renderMatriculasNuevaView(container);
        break;

      // Copias de Seguridad
      case 'backups':
      case 'backups-panel':
        await renderBackupsPanelView(container);
        break;
      case 'backups-explorador':
        await renderBackupsExploradorView(container);
        break;
      case 'backups-guardados':
        await renderBackupsGuardadosView(container);
        break;
      case 'backups-programacion':
        await renderBackupsProgramacionView(container);
        break;
      case 'backups-historial':
        await renderBackupsHistorialView(container);
        break;
      case 'backups-restauraciones':
        await renderBackupsRestauracionesView(container);
        break;

      default:
        await renderDashboardView(container);
        break;
    }
  } catch (err) {
    container.innerHTML = `
      <div class="bg-rose-50 border border-rose-200 rounded p-4 text-xs text-rose-700">
        <h4 class="font-bold mb-1">Error al cargar módulo</h4>
        <p>${esc(err.message)}</p>
      </div>
    `;
  }
}

// =========================================================================
// 1. VISTA: DASHBOARD ADMINISTRADOR
// =========================================================================

async function renderDashboardView(container) {
  const [stats, summary] = await Promise.all([
    api('/dashboard').catch(() => ({ estudiantes: 0, cursos: 0, matriculas: 0, activos: 0 })),
    api('/backups/summary').catch(() => ({ backup_count: 0, status: 'Correcto' }))
  ]);

  container.innerHTML = `
    <!-- Encabezado con badge y título -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-5 border-b border-slate-200">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-gauge text-slate-700"></i> Panel de Control Principal
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">Visión general del sistema académico y estado de la plataforma</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="inline-flex items-center px-2.5 py-1 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span> Sistema Operativo
        </span>
      </div>
    </div>

    <!-- 4 Cards Métricas -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Estudiantes</span>
          <span class="text-2xl font-bold text-slate-800 mt-1 block">${stats.estudiantes ?? 0}</span>
          <span class="text-[10px] text-emerald-600 font-medium">${stats.activos ?? 0} activos registrados</span>
        </div>
        <div class="w-11 h-11 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center text-lg">
          <i class="fa fa-user-graduate"></i>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Cursos</span>
          <span class="text-2xl font-bold text-slate-800 mt-1 block">${stats.cursos ?? 0}</span>
          <span class="text-[10px] text-slate-500 font-medium">Catálogo activo</span>
        </div>
        <div class="w-11 h-11 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg">
          <i class="fa fa-book"></i>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Matrículas</span>
          <span class="text-2xl font-bold text-slate-800 mt-1 block">${stats.matriculas ?? 0}</span>
          <span class="text-[10px] text-slate-500 font-medium">Periodo vigente</span>
        </div>
        <div class="w-11 h-11 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center text-lg">
          <i class="fa fa-clipboard-list"></i>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Backups Realizados</span>
          <span class="text-2xl font-bold text-slate-800 mt-1 block">${summary.backup_count ?? 0}</span>
          <span class="text-[10px] text-purple-600 font-medium">${summary.status || 'Operativo'}</span>
        </div>
        <div class="w-11 h-11 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center text-lg">
          <i class="fa fa-database"></i>
        </div>
      </div>
    </div>

    <!-- Accesos Rápidos -->
    <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs mb-6">
      <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa fa-bolt text-amber-500"></i> Accesos Rápidos
      </h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <button onclick="cargarModuloAdmin('estudiantes-lista')" class="bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md p-3 text-left transition-colors flex items-center gap-2.5">
          <i class="fa fa-graduation-cap text-sky-600"></i>
          <span class="font-semibold text-slate-700">Gestionar Estudiantes</span>
        </button>
        <button onclick="cargarModuloAdmin('cursos-lista')" class="bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md p-3 text-left transition-colors flex items-center gap-2.5">
          <i class="fa fa-book text-emerald-600"></i>
          <span class="font-semibold text-slate-700">Gestionar Cursos</span>
        </button>
        <button onclick="cargarModuloAdmin('matriculas-lista')" class="bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md p-3 text-left transition-colors flex items-center gap-2.5">
          <i class="fa fa-clipboard-list text-amber-600"></i>
          <span class="font-semibold text-slate-700">Ver Matrículas</span>
        </button>
        <button onclick="cargarModuloAdmin('backups-panel')" class="bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md p-3 text-left transition-colors flex items-center gap-2.5">
          <i class="fa fa-database text-purple-600"></i>
          <span class="font-semibold text-slate-700">Copias de Seguridad</span>
        </button>
      </div>
    </div>

    <!-- Información del Servidor y Plataforma -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
        <h4 class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-2">
          <i class="fa fa-server text-slate-600"></i> Estado del Entorno
        </h4>
        <div class="space-y-2 text-xs">
          <div class="flex justify-between py-1.5 border-b border-slate-100">
            <span class="text-slate-500">Backend API:</span>
            <span class="font-semibold text-slate-800">FastAPI (Python 3.13)</span>
          </div>
          <div class="flex justify-between py-1.5 border-b border-slate-100">
            <span class="text-slate-500">Base de Datos:</span>
            <span class="font-semibold text-slate-800">PostgreSQL 17.11</span>
          </div>
          <div class="flex justify-between py-1.5 border-b border-slate-100">
            <span class="text-slate-500">Frontend:</span>
            <span class="font-semibold text-slate-800">PHP 8.2 + Tailwind CSS</span>
          </div>
          <div class="flex justify-between py-1.5">
            <span class="text-slate-500">Copias de Seguridad:</span>
            <span class="font-semibold text-emerald-600">pg_dump + pg_restore operativos</span>
          </div>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
        <h4 class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-2">
          <i class="fa fa-clock-rotate-left text-slate-600"></i> Últimos Respaldos
        </h4>
        <div id="dashRecentBackups" class="text-xs">
          <div class="text-center text-slate-400 py-4"><i class="fa fa-spinner fa-spin"></i> Cargando...</div>
        </div>
      </div>
    </div>
  `;

  // Cargar lista rápida de backups en el card
  try {
    const list = await api('/backups');
    const containerEl = document.getElementById('dashRecentBackups');
    if (list.length === 0) {
      containerEl.innerHTML = '<p class="text-slate-400 text-center py-3">No hay respaldos recientes.</p>';
    } else {
      containerEl.innerHTML = `
        <div class="divide-y divide-slate-100">
          ${list.slice(0, 3).map(b => `
            <div class="py-2 flex items-center justify-between">
              <div>
                <div class="font-mono text-slate-800 font-semibold text-[11px]">${esc(b.filename)}</div>
                <div class="text-[10px] text-slate-400">${esc(b.created_at)} — ${esc(b.size_formatted)}</div>
              </div>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">${esc(b.status)}</span>
            </div>
          `).join('')}
        </div>
      `;
    }
  } catch (err) {}
}

// =========================================================================
// 2. VISTA: ESTUDIANTES (LISTA, NUEVO, ESTADO)
// =========================================================================

async function renderEstudiantesListaView(container) {
  const data = await api('/estudiantes');
  estudiantesGlobal = data;

  container.innerHTML = `
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-graduation-cap text-[#f4511e]"></i> Lista de Estudiantes
        </h1>
        <p class="text-xs text-slate-500">Gestión de alumnos registrados y matrícula académica</p>
      </div>
      <div>
        <button onclick="cargarModuloAdmin('estudiantes-nuevo')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded shadow-xs flex items-center gap-1.5 cursor-pointer">
          <i class="fa fa-plus"></i> Registrar Estudiante
        </button>
      </div>
    </div>

    <!-- Buscador -->
    <div class="mb-4">
      <input type="text" id="buscEstudiante" oninput="filtrarEstudiantes()" placeholder="Buscar por código, apellidos, nombres o DNI..." class="w-full sm:w-80 bg-white border border-slate-300 rounded px-3 py-1.5 text-xs focus:outline-none focus:border-rose-500">
    </div>

    <!-- Tabla -->
    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px]">
            <tr>
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Nombre Completo</th>
              <th class="py-2.5 px-3">DNI</th>
              <th class="py-2.5 px-3">Carrera</th>
              <th class="py-2.5 px-3 text-center">Ciclo</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody id="tbodyEstudiantes" class="divide-y divide-slate-100">
            ${renderFilasEstudiantes(data)}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderFilasEstudiantes(lista) {
  if (lista.length === 0) {
    return '<tr><td colspan="7" class="text-center text-slate-400 py-6">No se encontraron estudiantes.</td></tr>';
  }
  return lista.map(e => `
    <tr class="hover:bg-slate-50 transition-colors">
      <td class="py-2.5 px-3 font-mono font-semibold text-slate-800">${esc(e.codigo)}</td>
      <td class="py-2.5 px-3 font-medium text-slate-900">${esc(e.apellidos)}, ${esc(e.nombres)}</td>
      <td class="py-2.5 px-3 text-slate-600">${esc(e.dni)}</td>
      <td class="py-2.5 px-3 text-slate-700">${esc(e.carrera)}</td>
      <td class="py-2.5 px-3 text-center font-bold text-slate-700">${e.ciclo}</td>
      <td class="py-2.5 px-3 text-center">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${e.estado === 'ACTIVO' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}">
          ${esc(e.estado)}
        </span>
      </td>
      <td class="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">
        <button onclick="verEstudianteModal(${e.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px]" title="Ver datos">
          <i class="fa fa-eye"></i>
        </button>
        <button onclick="editarEstudianteModal(${e.id})" class="bg-sky-50 hover:bg-sky-100 text-sky-700 px-2 py-1 rounded text-[11px]" title="Editar">
          <i class="fa fa-pen"></i>
        </button>
        <button onclick="toggleEstadoEstudiante(${e.id}, '${e.estado}')" class="bg-amber-50 hover:bg-amber-100 text-amber-700 px-2 py-1 rounded text-[11px]" title="${e.estado === 'ACTIVO' ? 'Desactivar' : 'Activar'}">
          <i class="fa ${e.estado === 'ACTIVO' ? 'fa-user-slash' : 'fa-user-check'}"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

function filtrarEstudiantes() {
  const q = document.getElementById('buscEstudiante').value.toLowerCase().trim();
  const filtrados = estudiantesGlobal.filter(e =>
    e.codigo.toLowerCase().includes(q) ||
    e.nombres.toLowerCase().includes(q) ||
    e.apellidos.toLowerCase().includes(q) ||
    e.dni.toLowerCase().includes(q)
  );
  document.getElementById('tbodyEstudiantes').innerHTML = renderFilasEstudiantes(filtrados);
}

async function renderEstudiantesNuevoView(container) {
  container.innerHTML = `
    <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
      <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
        <i class="fa fa-user-plus text-emerald-600"></i> Registrar Nuevo Estudiante
      </h1>
      <button onclick="cargarModuloAdmin('estudiantes-lista')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded">
        Volver a la lista
      </button>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs p-5 max-w-2xl">
      <form id="formNuevoEstudiante" onsubmit="guardarNuevoEstudiante(event)" class="space-y-4 text-xs">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Código de Alumno:</label>
            <input type="text" id="estCod" required placeholder="Ej. 2026003" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">DNI:</label>
            <input type="text" id="estDni" required placeholder="8 dígitos" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Nombres:</label>
            <input type="text" id="estNom" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Apellidos:</label>
            <input type="text" id="estApe" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Carrera:</label>
            <input type="text" id="estCar" required value="INGENIERÍA DE SISTEMAS DE INFORMACIÓN" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Ciclo:</label>
            <input type="number" id="estCic" min="1" max="10" value="1" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Correo Institucional:</label>
            <input type="email" id="estCor" required placeholder="alumno@portal.edu.pe" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Teléfono:</label>
            <input type="text" id="estTel" value="987654321" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
        </div>

        <div>
          <label class="block font-semibold text-slate-700 mb-1">Dirección:</label>
          <input type="text" id="estDir" value="Lima, Perú" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
        </div>

        <div class="pt-3 text-right">
          <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2 rounded">
            Guardar Estudiante
          </button>
        </div>
      </form>
    </div>
  `;
}

async function guardarNuevoEstudiante(e) {
  e.preventDefault();
  const payload = {
    codigo: document.getElementById('estCod').value.trim(),
    dni: document.getElementById('estDni').value.trim(),
    nombres: document.getElementById('estNom').value.trim(),
    apellidos: document.getElementById('estApe').value.trim(),
    carrera: document.getElementById('estCar').value.trim(),
    ciclo: parseInt(document.getElementById('estCic').value) || 1,
    correo: document.getElementById('estCor').value.trim(),
    telefono: document.getElementById('estTel').value.trim(),
    direccion: document.getElementById('estDir').value.trim(),
    fecha_ingreso: new Date().toISOString().split('T')[0],
    estado: 'ACTIVO'
  };

  try {
    await api('/estudiantes', { method: 'POST', body: JSON.stringify(payload) });
    if (typeof Swal !== 'undefined') {
      await Swal.fire({
        icon: 'success',
        title: '¡Estudiante Registrado!',
        text: 'El alumno fue registrado exitosamente y ya cuenta con acceso al portal.',
        confirmButtonColor: '#0f172a'
      });
    } else {
      alert('¡Estudiante registrado correctamente!');
    }
    cargarModuloAdmin('estudiantes-lista');
  } catch (err) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'Error al registrar estudiante',
        text: err.message,
        confirmButtonColor: '#0f172a'
      });
    } else {
      alert('Error al registrar estudiante: ' + err.message);
    }
  }
}

async function renderEstudiantesEstadoView(container) {
  const data = await api('/estudiantes');
  const activos = data.filter(e => e.estado === 'ACTIVO').length;
  const inactivos = data.filter(e => e.estado !== 'ACTIVO').length;

  container.innerHTML = `
    <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
      <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
        <i class="fa fa-chart-pie text-sky-600"></i> Estado Académico General
      </h1>
      <button onclick="cargarModuloAdmin('estudiantes-lista')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded">
        Ver lista
      </button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
        <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Total Matriculados</span>
        <span class="text-2xl font-bold text-slate-800 mt-1 block">${data.length}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
        <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Condición Activa</span>
        <span class="text-2xl font-bold text-emerald-600 mt-1 block">${activos}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs">
        <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Inactivos / Observados</span>
        <span class="text-2xl font-bold text-rose-600 mt-1 block">${inactivos}</span>
      </div>
    </div>
  `;
}

// Modales de Estudiante
async function verEstudianteModal(id) {
  const e = estudiantesGlobal.find(x => x.id === id);
  if (!e) return;
  if (typeof Swal !== 'undefined') {
    Swal.fire({
      title: `<span class="text-sm font-bold text-slate-800">${esc(e.apellidos)}, ${esc(e.nombres)}</span>`,
      html: `
        <div class="text-left text-xs space-y-2 p-3 bg-slate-50 border border-slate-200 rounded">
          <div><strong class="text-slate-700">Código de Alumno:</strong> <span class="font-mono font-bold text-slate-900">${esc(e.codigo)}</span></div>
          <div><strong class="text-slate-700">DNI:</strong> ${esc(e.dni)}</div>
          <div><strong class="text-slate-700">Carrera Profesional:</strong> ${esc(e.carrera)}</div>
          <div><strong class="text-slate-700">Ciclo Académico:</strong> Ciclo ${e.ciclo}</div>
          <div><strong class="text-slate-700">Correo Institucional:</strong> ${esc(e.correo)}</div>
          <div><strong class="text-slate-700">Teléfono de Contacto:</strong> ${esc(e.telefono || 'No registrado')}</div>
          <div><strong class="text-slate-700">Dirección Registrada:</strong> ${esc(e.direccion || 'No registrada')}</div>
          <div><strong class="text-slate-700">Condición Académica:</strong> <span class="px-2 py-0.5 rounded text-[10px] font-bold ${e.estado === 'ACTIVO' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}">${esc(e.estado)}</span></div>
        </div>
      `,
      confirmButtonText: 'Cerrar Ficha',
      confirmButtonColor: '#0f172a'
    });
  } else {
    alert(`Ficha de Estudiante:\n\nCódigo: ${e.codigo}\nNombre: ${e.apellidos}, ${e.nombres}\nDNI: ${e.dni}\nCarrera: ${e.carrera}\nCiclo: ${e.ciclo}\nCorreo: ${e.correo}\nEstado: ${e.estado}`);
  }
}

async function editarEstudianteModal(id) {
  const e = estudiantesGlobal.find(x => x.id === id);
  if (!e) return;

  if (typeof Swal !== 'undefined') {
    const { value: formValues } = await Swal.fire({
      title: 'Editar Datos de Estudiante',
      html: `
        <div class="text-left text-xs space-y-3 p-2">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Nombres:</label>
            <input id="swalEstNom" class="swal2-input !m-0 !w-full !text-xs !h-9" value="${esc(e.nombres)}">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Apellidos:</label>
            <input id="swalEstApe" class="swal2-input !m-0 !w-full !text-xs !h-9" value="${esc(e.apellidos)}">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Carrera:</label>
            <input id="swalEstCar" class="swal2-input !m-0 !w-full !text-xs !h-9" value="${esc(e.carrera)}">
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Ciclo:</label>
              <input id="swalEstCic" type="number" min="1" max="10" class="swal2-input !m-0 !w-full !text-xs !h-9" value="${e.ciclo}">
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Estado:</label>
              <select id="swalEstEst" class="swal2-select !m-0 !w-full !text-xs !h-9">
                <option value="ACTIVO" ${e.estado === 'ACTIVO' ? 'selected' : ''}>ACTIVO</option>
                <option value="INACTIVO" ${e.estado !== 'ACTIVO' ? 'selected' : ''}>INACTIVO</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Teléfono:</label>
            <input id="swalEstTel" class="swal2-input !m-0 !w-full !text-xs !h-9" value="${esc(e.telefono || '')}">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Dirección:</label>
            <input id="swalEstDir" class="swal2-input !m-0 !w-full !text-xs !h-9" value="${esc(e.direccion || '')}">
          </div>
        </div>
      `,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: 'Guardar Cambios',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#0f172a',
      preConfirm: () => {
        return {
          nombres: document.getElementById('swalEstNom').value.trim(),
          apellidos: document.getElementById('swalEstApe').value.trim(),
          carrera: document.getElementById('swalEstCar').value.trim(),
          ciclo: parseInt(document.getElementById('swalEstCic').value) || e.ciclo,
          estado: document.getElementById('swalEstEst').value,
          telefono: document.getElementById('swalEstTel').value.trim(),
          direccion: document.getElementById('swalEstDir').value.trim()
        };
      }
    });

    if (formValues) {
      try {
        await api(`/estudiantes/${id}`, {
          method: 'PUT',
          body: JSON.stringify(formValues)
        });
        await Swal.fire({
          icon: 'success',
          title: '¡Actualizado!',
          text: 'Datos del estudiante guardados con éxito.',
          timer: 1500,
          showConfirmButton: false
        });
        cargarModuloAdmin('estudiantes-lista');
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: 'Error al actualizar',
          text: err.message,
          confirmButtonColor: '#0f172a'
        });
      }
    }
  }
}

async function toggleEstadoEstudiante(id, estadoActual) {
  const nuevo = estadoActual === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';
  let confirmar = false;
  if (typeof Swal !== 'undefined') {
    const res = await Swal.fire({
      title: '¿Cambiar estado?',
      text: `¿Desea cambiar el estado del estudiante a ${nuevo}?`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Sí, cambiar',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#0f172a'
    });
    confirmar = res.isConfirmed;
  } else {
    confirmar = confirm(`¿Desea cambiar el estado del estudiante a ${nuevo}?`);
  }

  if (confirmar) {
    try {
      await api(`/estudiantes/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ estado: nuevo })
      });
      if (typeof Swal !== 'undefined') {
        await Swal.fire({
          icon: 'success',
          title: 'Estado Actualizado',
          text: `El estudiante ahora se encuentra en estado ${nuevo}.`,
          timer: 1500,
          showConfirmButton: false
        });
      }
      cargarModuloAdmin('estudiantes-lista');
    } catch (err) {
      if (typeof Swal !== 'undefined') {
        Swal.fire({ icon: 'error', title: 'Error', text: err.message, confirmButtonColor: '#0f172a' });
      } else {
        alert('Error: ' + err.message);
      }
    }
  }
}

// =========================================================================
// 3. VISTA: CURSOS (LISTA Y NUEVO)
// =========================================================================

async function renderCursosListaView(container) {
  const cursos = await api('/cursos');
  cursosGlobal = cursos;

  container.innerHTML = `
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-book text-emerald-600"></i> Catálogo de Cursos
        </h1>
        <p class="text-xs text-slate-500">Malla y asignaturas impartidas en el portal</p>
      </div>
      <div>
        <button onclick="cargarModuloAdmin('cursos-nuevo')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded shadow-xs flex items-center gap-1.5 cursor-pointer">
          <i class="fa fa-plus"></i> Nuevo Curso
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px]">
            <tr>
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3">Docente Responsable</th>
              <th class="py-2.5 px-3 text-center">Créditos</th>
              <th class="py-2.5 px-3 text-center">Ciclo</th>
              <th class="py-2.5 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${cursos.map(c => `
              <tr class="hover:bg-slate-50 transition-colors">
                <td class="py-2.5 px-3 font-mono font-semibold text-slate-800">${esc(c.codigo)}</td>
                <td class="py-2.5 px-3 font-bold text-slate-900">${esc(c.nombre)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(c.docente)}</td>
                <td class="py-2.5 px-3 text-center font-bold text-slate-700">${c.creditos}</td>
                <td class="py-2.5 px-3 text-center text-slate-600">${c.ciclo}</td>
                <td class="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">
                  <button onclick="alert('Curso: ${esc(c.nombre)} (${esc(c.codigo)})\\nDocente: ${esc(c.docente)}\\nCréditos: ${c.creditos}\\nCiclo: ${c.ciclo}')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px]">
                    <i class="fa fa-eye"></i>
                  </button>
                  <button onclick="eliminarCursoConfirm(${c.id}, '${esc(c.nombre)}')" class="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2 py-1 rounded text-[11px]">
                    <i class="fa fa-trash"></i>
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderCursosNuevoView(container) {
  container.innerHTML = `
    <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
      <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
        <i class="fa fa-plus-circle text-emerald-600"></i> Agregar Nuevo Curso
      </h1>
      <button onclick="cargarModuloAdmin('cursos-lista')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded">
        Volver a la lista
      </button>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs p-5 max-w-lg">
      <form onsubmit="guardarNuevoCurso(event)" class="space-y-4 text-xs">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Código del Curso:</label>
          <input type="text" id="curCod" required placeholder="Ej. EIS-050" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Nombre de la Asignatura:</label>
          <input type="text" id="curNom" required placeholder="Ej. Cloud Native DevOps" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Docente Responsable:</label>
          <input type="text" id="curDoc" required placeholder="Ej. Ing. Carlos Benítez" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Créditos:</label>
            <input type="number" id="curCred" min="1" max="10" value="4" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Ciclo:</label>
            <input type="number" id="curCic" min="1" max="10" value="7" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
          </div>
        </div>
        <div class="pt-3 text-right">
          <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2 rounded">
            Guardar Curso
          </button>
        </div>
      </form>
    </div>
  `;
}

async function guardarNuevoCurso(e) {
  e.preventDefault();
  const payload = {
    codigo: document.getElementById('curCod').value.trim(),
    nombre: document.getElementById('curNom').value.trim(),
    docente: document.getElementById('curDoc').value.trim(),
    creditos: parseInt(document.getElementById('curCred').value),
    ciclo: parseInt(document.getElementById('curCic').value)
  };
  try {
    await api('/cursos', { method: 'POST', body: JSON.stringify(payload) });
    if (typeof Swal !== 'undefined') {
      await Swal.fire({
        icon: 'success',
        title: '¡Curso Registrado!',
        text: 'La asignatura fue agregada exitosamente.',
        timer: 1500,
        showConfirmButton: false
      });
    } else {
      alert('¡Curso registrado con éxito!');
    }
    cargarModuloAdmin('cursos-lista');
  } catch (err) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({ icon: 'error', title: 'Error al registrar curso', text: err.message, confirmButtonColor: '#0f172a' });
    } else {
      alert('Error al guardar curso: ' + err.message);
    }
  }
}

async function eliminarCursoConfirm(id, nombre) {
  let confirmar = false;
  if (typeof Swal !== 'undefined') {
    const res = await Swal.fire({
      title: '¿Eliminar asignatura?',
      text: `¿Está seguro de eliminar el curso "${nombre}"? Esta acción no se puede deshacer.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#e11d48'
    });
    confirmar = res.isConfirmed;
  } else {
    confirmar = confirm(`¿Desea eliminar la asignatura "${nombre}"?`);
  }

  if (confirmar) {
    try {
      await api(`/cursos/${id}`, { method: 'DELETE' });
      if (typeof Swal !== 'undefined') {
        await Swal.fire({
          icon: 'success',
          title: 'Asignatura eliminada',
          timer: 1500,
          showConfirmButton: false
        });
      }
      cargarModuloAdmin('cursos-lista');
    } catch (err) {
      if (typeof Swal !== 'undefined') {
        Swal.fire({ icon: 'error', title: 'Error al eliminar', text: err.message, confirmButtonColor: '#0f172a' });
      } else {
        alert('Error: ' + err.message);
      }
    }
  }
}

// =========================================================================
// 4. VISTA: MATRÍCULAS (LISTA Y NUEVA)
// =========================================================================

async function renderMatriculasListaView(container) {
  const matriculas = await api('/matriculas');
  matriculasGlobal = matriculas;

  container.innerHTML = `
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-clipboard-list text-amber-600"></i> Registro de Matrículas
        </h1>
        <p class="text-xs text-slate-500">Asignaciones académicas vigentes</p>
      </div>
      <div>
        <button onclick="cargarModuloAdmin('matriculas-nueva')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded shadow-xs flex items-center gap-1.5 cursor-pointer">
          <i class="fa fa-plus"></i> Nueva Matrícula
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px]">
            <tr>
              <th class="py-2.5 px-3">Estudiante</th>
              <th class="py-2.5 px-3">Periodo</th>
              <th class="py-2.5 px-3">Curso</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${matriculas.map(m => `
              <tr class="hover:bg-slate-50 transition-colors">
                <td class="py-2.5 px-3 font-semibold text-slate-900">${esc(m.estudiante)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(m.periodo)}</td>
                <td class="py-2.5 px-3 text-slate-800 font-medium">${esc(m.curso)}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">${esc(m.estado || 'M')}</span>
                </td>
                <td class="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">
                  <button onclick="alert('Matrícula ID: ${m.id}\\nEstudiante: ${esc(m.estudiante)}\\nCurso: ${esc(m.curso)}\\nPeriodo: ${esc(m.periodo)}')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px]">
                    <i class="fa fa-eye"></i>
                  </button>
                  <button onclick="eliminarMatriculaConfirm(${m.id})" class="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2 py-1 rounded text-[11px]">
                    <i class="fa fa-trash"></i>
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderMatriculasNuevaView(container) {
  const [estudiantes, cursos] = await Promise.all([
    api('/estudiantes'),
    api('/cursos')
  ]);

  container.innerHTML = `
    <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
      <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
        <i class="fa fa-plus-circle text-amber-600"></i> Registrar Nueva Matrícula
      </h1>
      <button onclick="cargarModuloAdmin('matriculas-lista')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded">
        Volver a la lista
      </button>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs p-5 max-w-lg">
      <form onsubmit="guardarNuevaMatricula(event)" class="space-y-4 text-xs">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Seleccionar Estudiante:</label>
          <select id="matEstId" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
            ${estudiantes.map(e => `<option value="${e.id}">${esc(e.codigo)} - ${esc(e.apellidos)}, ${esc(e.nombres)}</option>`).join('')}
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Seleccionar Curso:</label>
          <select id="matCurId" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
            ${cursos.map(c => `<option value="${c.id}">${esc(c.codigo)} - ${esc(c.nombre)}</option>`).join('')}
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Periodo Académico:</label>
          <input type="text" id="matPer" value="2026 II-B" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:border-rose-500">
        </div>
        <div class="pt-3 text-right">
          <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2 rounded">
            Confirmar Matrícula
          </button>
        </div>
      </form>
    </div>
  `;
}

async function guardarNuevaMatricula(e) {
  e.preventDefault();
  const payload = {
    estudiante_id: parseInt(document.getElementById('matEstId').value),
    curso_id: parseInt(document.getElementById('matCurId').value),
    periodo: document.getElementById('matPer').value.trim(),
    estado: 'MATRICULADO'
  };
  try {
    await api('/matriculas', { method: 'POST', body: JSON.stringify(payload) });
    if (typeof Swal !== 'undefined') {
      await Swal.fire({
        icon: 'success',
        title: '¡Matrícula Confirmada!',
        text: 'El alumno fue matriculado correctamente en la asignatura.',
        timer: 1500,
        showConfirmButton: false
      });
    } else {
      alert('¡Matrícula registrada correctamente!');
    }
    cargarModuloAdmin('matriculas-lista');
  } catch (err) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({ icon: 'error', title: 'Error en matrícula', text: err.message, confirmButtonColor: '#0f172a' });
    } else {
      alert('Error al registrar matrícula: ' + err.message);
    }
  }
}

async function eliminarMatriculaConfirm(id) {
  let confirmar = false;
  if (typeof Swal !== 'undefined') {
    const res = await Swal.fire({
      title: '¿Dar de baja matrícula?',
      text: '¿Desea eliminar este registro de matrícula?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, dar de baja',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#e11d48'
    });
    confirmar = res.isConfirmed;
  } else {
    confirmar = confirm('¿Desea dar de baja esta matrícula?');
  }

  if (confirmar) {
    try {
      await api(`/matriculas/${id}`, { method: 'DELETE' });
      if (typeof Swal !== 'undefined') {
        await Swal.fire({
          icon: 'success',
          title: 'Matrícula eliminada',
          timer: 1500,
          showConfirmButton: false
        });
      }
      cargarModuloAdmin('matriculas-lista');
    } catch (err) {
      if (typeof Swal !== 'undefined') {
        Swal.fire({ icon: 'error', title: 'Error', text: err.message, confirmButtonColor: '#0f172a' });
      } else {
        alert('Error: ' + err.message);
      }
    }
  }
}

// =========================================================================
// 5. VISTAS: COPIAS DE SEGURIDAD (PANEL, GUARDADOS, PROGRAMACIÓN, HISTORIAL, RESTAURACIONES)
// =========================================================================

/**
 * Convierte un nombre técnico de archivo de backup como:
 * portal_academico_20260915_175509.backup
 * en un texto visible limpio y profesional:
 * Backup 15/09/2026 - 17:55:09
 */
function formatNombreBackupVisible(filename, description) {
  if (description && String(description).trim()) {
    return String(description).trim();
  }
  if (!filename) return '--';
  const str = String(filename);
  if (str.toLowerCase().includes('restore') || str.toLowerCase().includes('restaurad')) {
    return formatNombreRestauracionVisible(filename);
  }
  const m = str.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
  if (m) {
    const [_, yyyy, mm, dd, hh, min, ss] = m;
    return `Backup ${dd}/${mm}/${yyyy} - ${hh}:${min}:${ss}`;
  }
  return str;
}

/**
 * Convierte un nombre técnico de base restaurada como:
 * portal_academico_restore_20260915_175509 o portal_academico_restaurado_20260915_175509
 * en un texto visible profesional o muestra el nombre descriptivo si fue provisto:
 * Restauración 15/09/2026 - 17:55:09
 */
function formatNombreRestauracionVisible(nombre, description) {
  if (description && String(description).trim()) {
    return String(description).trim();
  }
  if (!nombre) return '--';
  const str = String(nombre);
  const m = str.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
  if (m) {
    const [_, yyyy, mm, dd, hh, min, ss] = m;
    return `Restauración ${dd}/${mm}/${yyyy} - ${hh}:${min}:${ss}`;
  }
  if (str === 'portal_academico_restaurado_prueba' || str.includes('restaurado_prueba') || str.includes('restore_prueba')) {
    return 'Base restaurada de prueba';
  }
  return str;
}

/**
 * Convierte el disparador o tipo a texto visible en español:
 * MANUAL -> Manual
 * PROGRAMADO / SCHEDULED / AUTOMATICO -> Automático
 */
function formatTipoBackupVisible(tipo) {
  if (!tipo) return '--';
  const t = String(tipo).trim().toUpperCase();
  if (t === 'MANUAL') return 'Manual';
  if (t === 'PROGRAMADO' || t === 'SCHEDULED' || t === 'AUTOMATICO') return 'Automático';
  return tipo;
}

async function renderBackupsPanelView(container) {
  const [summary, backups] = await Promise.all([
    api('/backups/summary'),
    api('/backups')
  ]);

  const h = summary.health;
  const lastBackupVisible = formatNombreBackupVisible(summary.last_backup_file, summary.last_backup_description);

  container.innerHTML = `
    <!-- Encabezado -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-database text-purple-600"></i> Panel de Copias de Seguridad
        </h1>
        <p class="text-xs text-slate-500">Gestión de respaldos automatizados, políticas de retención y pruebas en PostgreSQL</p>
      </div>
      <div>
        <button onclick="abrirModalCrearBackup()" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded shadow-xs flex items-center gap-1.5 cursor-pointer">
          <i class="fa fa-plus-circle"></i> Crear Backup Ahora
        </button>
      </div>
    </div>

    <!-- Health Check Banner -->
    <div class="mb-4">
      ${h.is_operational ? `
        <div class="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg p-3 text-xs flex items-center justify-between">
          <span class="flex items-center gap-2">
            <i class="fa fa-circle-check text-emerald-600 text-sm"></i>
            <span><strong>Sistema de Backups: Operativo</strong> — <code>pg_dump</code> y <code>pg_restore</code> PostgreSQL 17.11 activos. Almacenamiento seguro en <code>${esc(h.backup_dir_path)}</code>.</span>
          </span>
          <span class="bg-emerald-200 text-emerald-900 px-2 py-0.5 rounded text-[10px] font-bold">100% LISTO</span>
        </div>
      ` : `
        <div class="bg-amber-50 border border-amber-200 text-amber-800 rounded-lg p-3 text-xs">
          <i class="fa fa-triangle-exclamation text-amber-600 mr-1"></i> ${esc(h.message)}
        </div>
      `}
    </div>

    <!-- 4 Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Última copia de seguridad</span>
          <span class="text-base font-bold text-slate-800 mt-1 block">${summary.last_backup_date ? summary.last_backup_date.split(' ')[0] : 'Sin fecha'}</span>
          <span class="text-[10px] text-slate-500 truncate block max-w-[150px]" title="${esc(lastBackupVisible)}">${esc(lastBackupVisible || 'Sin respaldos')}</span>
        </div>
        <div class="w-10 h-10 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center text-base">
          <i class="fa fa-clock-rotate-left"></i>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Próxima copia programada</span>
          <span class="text-base font-bold text-slate-800 mt-1 block">${summary.next_backup_date || 'No programado'}</span>
          <span class="text-[10px] text-slate-500 truncate block max-w-[150px]">${summary.next_backup_schedule || 'Sin política'}</span>
        </div>
        <div class="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center text-base">
          <i class="fa fa-calendar-check"></i>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Copias guardadas</span>
          <span class="text-2xl font-bold text-slate-800 mt-1 block">${summary.backup_count}</span>
          <span class="text-[10px] text-emerald-600 font-medium">Archivos íntegros</span>
        </div>
        <div class="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-base">
          <i class="fa fa-box-archive"></i>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center justify-between">
        <div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Estado</span>
          <span class="text-lg font-bold ${summary.status === 'Correcto' ? 'text-emerald-600' : 'text-rose-600'} mt-1 block">${summary.status}</span>
          <span class="text-[10px] text-slate-500">PostgreSQL</span>
        </div>
        <div class="w-10 h-10 rounded-lg ${summary.status === 'Correcto' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'} flex items-center justify-center text-base">
          <i class="fa ${summary.status === 'Correcto' ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i>
        </div>
      </div>
    </div>

    <!-- Tabla Últimos Respaldos -->
    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">Últimos Respaldos Realizados</h3>
        <button onclick="cargarModuloAdmin('backups-guardados')" class="text-xs text-rose-600 font-semibold hover:underline">Ver todos &rarr;</button>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Fecha</th>
              <th class="py-2.5 px-3">Nombre de la Copia</th>
              <th class="py-2.5 px-3">Tipo</th>
              <th class="py-2.5 px-3">Tamaño</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${backups.slice(0, 5).map(b => renderFilaBackupAdmin(b)).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderFilaBackupAdmin(b) {
  return `
    <tr class="hover:bg-slate-50 transition-colors">
      <td class="py-2.5 px-3 font-semibold text-slate-800">${esc(b.created_at)}</td>
      <td class="py-2.5 px-3 font-semibold text-slate-900">${esc(formatNombreBackupVisible(b.filename, b.description))}</td>
      <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600">${esc(formatTipoBackupVisible(b.backup_type))}</span></td>
      <td class="py-2.5 px-3 font-medium text-slate-700">${esc(b.size_formatted)}</td>
      <td class="py-2.5 px-3 text-center">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${b.status === 'CORRECTO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
          ${esc(b.status)}
        </span>
      </td>
      <td class="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">
        ${b.status === 'CORRECTO' ? `
          <button onclick="descargarBackupAdmin(${b.id}, '${esc(b.filename)}')" class="bg-sky-50 hover:bg-sky-100 text-sky-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Descargar copia de seguridad">
            <i class="fa fa-download"></i>
          </button>
          <button onclick="verDetalleBackupAdmin(${b.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Ver detalle completo">
            <i class="fa fa-eye"></i>
          </button>
          <button onclick="restaurarBackupAdmin(${b.id}, '${esc(b.filename)}', '${esc(b.description || '')}')" class="bg-amber-50 hover:bg-amber-100 text-amber-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Restaurar en base de prueba">
            <i class="fa fa-rotate-left"></i>
          </button>
          <button onclick="eliminarBackupAdmin(${b.id}, '${esc(b.filename)}', '${esc(b.description || '')}')" class="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Eliminar copia de seguridad">
            <i class="fa fa-trash"></i>
          </button>
        ` : `
          <button onclick="verDetalleBackupAdmin(${b.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Ver detalle">
            <i class="fa fa-eye"></i>
          </button>
          <button onclick="eliminarBackupAdmin(${b.id}, '${esc(b.filename)}', '${esc(b.description || '')}')" class="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Eliminar registro">
            <i class="fa fa-trash"></i>
          </button>
        `}
      </td>
    </tr>
  `;
}

async function renderBackupsGuardadosView(container) {
  const backups = await api('/backups');
  backupsGlobal = backups;

  container.innerHTML = `
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-box-archive text-purple-600"></i> Copias Guardadas en Disco
        </h1>
        <p class="text-xs text-slate-500">Archivos protegidos físicamente en el servidor</p>
      </div>
      <div>
        <button onclick="abrirModalCrearBackup()" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded shadow-xs flex items-center gap-1.5 cursor-pointer">
          <i class="fa fa-plus-circle"></i> Crear Backup Ahora
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Fecha Creación</th>
              <th class="py-2.5 px-3">Nombre de la Copia</th>
              <th class="py-2.5 px-3">Tipo</th>
              <th class="py-2.5 px-3">Tamaño</th>
              <th class="py-2.5 px-3">Generado Por</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${backups.length === 0 ? '<tr><td colspan="7" class="text-center text-slate-400 py-6">No hay respaldos guardados.</td></tr>' : backups.map(b => renderFilaBackupAdmin(b)).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// =========================================================================
// EXPLORADOR DE ARCHIVOS REALES EN DISCO (BACKUP_DIR)
// =========================================================================

async function renderBackupsExploradorView(container) {
  let archivos;
  try {
    archivos = await api('/backups/files');
  } catch (err) {
    container.innerHTML = `
      <div class="bg-rose-50 border border-rose-200 rounded-lg p-4 text-xs text-rose-700">
        <div class="flex items-center gap-2 font-bold mb-1"><i class="fa fa-triangle-exclamation"></i> Error al cargar el Explorador</div>
        <p>${esc(err.message)}</p>
      </div>
    `;
    return;
  }

  const total = archivos.length;
  const huerfanos = archivos.filter(f => f.is_orphan).length;
  const registrados = total - huerfanos;
  const tamTotal = archivos.reduce((acc, f) => acc + f.size_bytes, 0);

  function formatBytes(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b / 1024).toFixed(2) + ' KB';
    if (b < 1073741824) return (b / 1048576).toFixed(2) + ' MB';
    return (b / 1073741824).toFixed(2) + ' GB';
  }

  container.innerHTML = `
    <!-- Cabecera -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-folder-open text-purple-600"></i> Explorador de Backups en Disco
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">Archivos <code class="bg-slate-100 px-1 rounded font-mono">.backup</code> reales encontrados en <code class="bg-slate-100 px-1 rounded font-mono text-purple-700">BACKUP_DIR</code></p>
      </div>
      <div class="flex items-center gap-2">
        <button id="btnRefrescarExplorador" onclick="cargarModuloAdmin('backups-explorador')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded cursor-pointer flex items-center gap-1.5 transition-colors">
          <i class="fa fa-rotate"></i> Refrescar
        </button>
        <button onclick="explorarCrearBackup()" class="bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded shadow-xs flex items-center gap-1.5 cursor-pointer transition-colors">
          <i class="fa fa-plus-circle"></i> Crear Backup
        </button>
      </div>
    </div>

    <!-- Tarjetas de resumen -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
      <div class="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
        <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Archivos en disco</div>
        <div class="text-2xl font-bold text-slate-800 mt-1">${total}</div>
        <div class="text-[10px] text-purple-600 font-medium mt-0.5">archivos .backup</div>
      </div>
      <div class="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
        <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Registrados en BD</div>
        <div class="text-2xl font-bold text-emerald-700 mt-1">${registrados}</div>
        <div class="text-[10px] text-emerald-600 font-medium mt-0.5">con historial</div>
      </div>
      <div class="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
        <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Huérfanos</div>
        <div class="text-2xl font-bold ${huerfanos > 0 ? 'text-amber-600' : 'text-slate-400'} mt-1">${huerfanos}</div>
        <div class="text-[10px] text-slate-400 font-medium mt-0.5">sin registro en BD</div>
      </div>
      <div class="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
        <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Espacio total</div>
        <div class="text-2xl font-bold text-slate-800 mt-1">${formatBytes(tamTotal)}</div>
        <div class="text-[10px] text-slate-500 font-medium mt-0.5">en BACKUP_DIR</div>
      </div>
    </div>

    ${ huerfanos > 0 ? `
    <div class="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 text-xs text-amber-800 mb-4 flex items-start gap-2">
      <i class="fa fa-triangle-exclamation text-amber-500 mt-0.5"></i>
      <span><strong>${huerfanos} archivo${huerfanos > 1 ? 's' : ''} huérfano${huerfanos > 1 ? 's' : ''}:</strong>
      existen en disco pero no tienen registro en la base de datos. Puede que hayan sido generados manualmente fuera del sistema.</span>
    </div>` : '' }

    <!-- Tabla principal -->
    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse" id="tablaExploradorBackups">
          <thead class="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Nombre de la Copia</th>
              <th class="py-2.5 px-3">Fecha en Disco</th>
              <th class="py-2.5 px-3">Tamaño</th>
              <th class="py-2.5 px-3">Tipo</th>
              <th class="py-2.5 px-3 text-center">Estado BD</th>
              <th class="py-2.5 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${ total === 0
              ? '<tr><td colspan="6" class="text-center text-slate-400 py-10"><i class="fa fa-folder-open text-slate-300 text-2xl block mb-2"></i>No hay archivos .backup en el directorio de almacenamiento.</td></tr>'
              : archivos.map(f => renderFilaExploradorBackup(f)).join('') }
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderFilaExploradorBackup(f) {
  // Badge de estado
  let estadoBadge;
  if (f.is_orphan) {
    estadoBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800"><i class="fa fa-ghost text-[9px] mr-0.5"></i>Huérfano</span>';
  } else if (f.db_status === 'CORRECTO') {
    estadoBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">CORRECTO</span>';
  } else if (f.db_status === 'ELIMINADO_RETENCION') {
    estadoBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500">RETENCION</span>';
  } else if (f.db_status === 'EN_PROCESO') {
    estadoBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-700">EN PROCESO</span>';
  } else if (f.db_status) {
    estadoBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-700">${esc(f.db_status)}</span>`;
  } else {
    estadoBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-400">—</span>';
  }

  // Badge de tipo
  let tipoBadge;
  const tipoTxt = formatTipoBackupVisible(f.db_type);
  if (f.db_type === 'MANUAL') {
    tipoBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800">${esc(tipoTxt)}</span>`;
  } else if (f.db_type) {
    tipoBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800">${esc(tipoTxt)}</span>`;
  } else {
    tipoBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-600 border border-amber-200">Externo</span>';
  }

  // Botones de acción
  const puedeDescargar = !f.is_orphan && f.db_status === 'CORRECTO' && f.db_id;
  const puedeRestaurar = !f.is_orphan && f.db_status === 'CORRECTO' && f.db_id;
  const puedeEliminar  = !f.is_orphan && f.db_id;

  const btnDescargar = puedeDescargar
    ? `<button onclick="descargarBackupAdmin(${f.db_id}, '${esc(f.filename)}')"
         class="bg-sky-50 hover:bg-sky-100 text-sky-700 px-2 py-1 rounded text-[11px] cursor-pointer transition-colors" title="Descargar">
         <i class="fa fa-download"></i>
       </button>`
    : `<button disabled class="bg-slate-50 text-slate-300 px-2 py-1 rounded text-[11px] cursor-not-allowed" title="No disponible para descarga"><i class="fa fa-download"></i></button>`;

  const btnVer = !f.is_orphan && f.db_id
    ? `<button onclick="verDetalleBackupAdmin(${f.db_id})"
         class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] cursor-pointer transition-colors" title="Ver detalle en BD">
         <i class="fa fa-eye"></i>
       </button>`
    : `<button onclick="explorarVerInfoHuerfano('${esc(f.filename)}', '${esc(f.size_formatted)}', '${esc(f.modified_at)}')"
         class="bg-amber-50 hover:bg-amber-100 text-amber-700 px-2 py-1 rounded text-[11px] cursor-pointer transition-colors" title="Info del archivo">
         <i class="fa fa-circle-info"></i>
       </button>`;

  const btnRestaurar = (puedeRestaurar && f.db_id)
    ? `<button onclick="restaurarBackupAdmin(${f.db_id}, '${esc(f.filename)}', '${esc(f.db_description || '')}')"
         class="bg-amber-50 hover:bg-amber-100 text-amber-700 px-2 py-1 rounded text-[11px] cursor-pointer transition-colors" title="Restaurar en base de prueba">
         <i class="fa fa-rotate-left"></i>
       </button>`
    : '';

  const btnEliminar = (puedeEliminar && f.db_id)
    ? `<button onclick="eliminarBackupAdmin(${f.db_id}, '${esc(f.filename)}', '${esc(f.db_description || '')}')"
         class="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2 py-1 rounded text-[11px] cursor-pointer transition-colors" title="Eliminar">
         <i class="fa fa-trash"></i>
       </button>`
    : '';

  const rowClass = f.is_orphan
    ? 'hover:bg-amber-50/40 transition-colors bg-amber-50/20'
    : 'hover:bg-slate-50 transition-colors';

  const creatorInfo = f.db_created_by
    ? `<div class="text-[10px] text-slate-400 mt-0.5"><i class="fa fa-user text-[8px] mr-0.5"></i>${esc(f.db_created_by)}</div>`
    : `<div class="text-[10px] text-amber-500 mt-0.5 font-medium"><i class="fa fa-ghost text-[9px] mr-0.5"></i>Archivo huérfano</div>`;

  return `
    <tr class="${rowClass}">
      <td class="py-2.5 px-3">
        <div class="font-semibold text-slate-900 text-xs">${esc(formatNombreBackupVisible(f.filename, f.db_description))}</div>
        ${creatorInfo}
      </td>
      <td class="py-2.5 px-3 font-mono text-[11px] text-slate-700">${esc(f.modified_at)}</td>
      <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(f.size_formatted)}</td>
      <td class="py-2.5 px-3">${tipoBadge}</td>
      <td class="py-2.5 px-3 text-center">${estadoBadge}</td>
      <td class="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">
        ${btnDescargar}
        ${btnVer}
        ${btnRestaurar}
        ${btnEliminar}
      </td>
    </tr>
  `;
}

function explorarCrearBackup() {
  // Usa el modal existente de crear backup y vuelve al explorador al terminar
  const originalModulo = moduloActualAdmin;
  moduloActualAdmin = 'backups-explorador';
  abrirModalCrearBackup();
}

function explorarVerInfoHuerfano(filename, size, fecha) {
  if (typeof Swal !== 'undefined') {
    Swal.fire({
      title: '<span class="text-base font-bold text-slate-900 flex items-center justify-center gap-2"><i class="fa fa-ghost text-amber-500"></i> Archivo Huérfano</span>',
      html: `
        <div class="text-left text-xs text-slate-700 mt-2 space-y-3">
          <div class="bg-amber-50 border border-amber-200 rounded p-3 text-amber-800 text-[11px] leading-relaxed">
            <i class="fa fa-circle-info text-amber-500 mr-1"></i>
            Este archivo <strong>.backup</strong> existe físicamente en el <code>BACKUP_DIR</code> del servidor
            pero <strong>no tiene registro en la base de datos</strong>. Puede que haya sido copiado manualmente,
            generado por una herramienta externa o que su registro fue eliminado.
          </div>
          <table class="w-full border-collapse border border-slate-200 rounded overflow-hidden">
            <tbody>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2 px-3 font-semibold text-slate-600 w-1/3">Copia de seguridad</td>
                <td class="py-2 px-3 font-semibold text-slate-900 break-all">${esc(formatNombreBackupVisible(filename))}</td>
              </tr>
              <tr class="border-b border-slate-200">
                <td class="py-2 px-3 font-semibold text-slate-600">Fecha en disco</td>
                <td class="py-2 px-3 font-mono text-slate-700">${esc(fecha)}</td>
              </tr>
              <tr>
                <td class="py-2 px-3 font-semibold text-slate-600">Tamaño</td>
                <td class="py-2 px-3 font-semibold text-slate-800">${esc(size)}</td>
              </tr>
            </tbody>
          </table>
          <p class="text-[11px] text-slate-500">Para operar sobre este archivo (descargar, restaurar, eliminar), primero debe registrarlo manualmente en la base de datos desde la consola de FastAPI o Swagger.</p>
        </div>
      `,
      showCloseButton: true,
      showConfirmButton: true,
      confirmButtonText: 'Cerrar',
      confirmButtonColor: '#0f172a'
    });
  }
}

async function renderBackupsProgramacionView(container) {
  const schedules = await api('/backups/schedules');
  programacionesGlobal = schedules;

  container.innerHTML = `
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-clock text-amber-600"></i> Programación Automática de Respaldos
        </h1>
        <p class="text-xs text-slate-500">Ejecución desatendida con retención automática</p>
      </div>
      <div class="flex items-center gap-2">
        <button onclick="cargarModuloAdmin('backups-programacion')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded cursor-pointer flex items-center gap-1">
          <i class="fa fa-rotate"></i> Refrescar
        </button>
        <button onclick="abrirModalProgramacionAdmin()" class="bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded shadow-xs flex items-center gap-1.5 cursor-pointer">
          <i class="fa fa-plus-circle"></i> Nueva Programación
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Tarea Programada</th>
              <th class="py-2.5 px-3">Frecuencia / Intervalo</th>
              <th class="py-2.5 px-3">Próxima Ejecución (Lima)</th>
              <th class="py-2.5 px-3">Última Ejecución</th>
              <th class="py-2.5 px-3 text-center">Retención</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${schedules.length === 0 ? '<tr><td colspan="7" class="text-center text-slate-400 py-6">No hay tareas programadas. Haga clic en "Nueva Programación" para crear una.</td></tr>' : schedules.map(s => `
              <tr class="hover:bg-slate-50 transition-colors">
                <td class="py-2.5 px-3">
                  <div class="font-bold text-slate-900">${esc(s.name)}</div>
                  <div class="text-[10px] text-slate-400 font-mono">ID #${s.id}</div>
                </td>
                <td class="py-2.5 px-3">
                  ${formatFrecuenciaBadge(s)}
                </td>
                <td class="py-2.5 px-3">
                  <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono font-bold text-[11px] bg-purple-50 text-purple-700 border border-purple-200">
                    <i class="fa fa-clock text-[9px]"></i> ${esc(s.next_run_at || '--')}
                  </span>
                </td>
                <td class="py-2.5 px-3 font-mono text-[11px] text-slate-600">
                  ${esc(s.last_run_at || 'Aún no ejecutado')}
                </td>
                <td class="py-2.5 px-3 text-center font-semibold text-slate-700">
                  ${s.retention_days === 0 ? '<span class="text-purple-700 bg-purple-50 px-2 py-0.5 rounded text-[10px] font-bold border border-purple-200">Indefinida</span>' : `${s.retention_days} d`}
                </td>
                <td class="py-2.5 px-3 text-center">
                  <button onclick="toggleEstadoProgramacionAdmin(${s.id}, ${s.enabled}, '${esc(s.name)}')" class="cursor-pointer px-2 py-0.5 rounded text-[10px] font-bold transition-all ${s.enabled ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}" title="Haga clic para ${s.enabled ? 'pausar' : 'activar'}">
                    <i class="fa ${s.enabled ? 'fa-check-circle' : 'fa-pause-circle'} mr-0.5"></i> ${s.enabled ? 'Activa' : 'Pausada'}
                  </button>
                </td>
                <td class="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">
                  <button onclick="probarProgramacionAdmin(${s.id}, '${esc(s.name)}')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1 rounded text-[11px] font-bold shadow-xs inline-flex items-center gap-1 cursor-pointer transition-colors" title="Ejecutar ahora inmediatamente">
                    <i class="fa fa-play text-[9px]"></i> Ejecutar ahora
                  </button>
                  <button onclick="verDetalleProgramacionAdmin(${s.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Ver detalle">
                    <i class="fa fa-eye"></i>
                  </button>
                  <button onclick="abrirModalProgramacionAdmin(${s.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Editar">
                    <i class="fa fa-pen"></i>
                  </button>
                  <button onclick="eliminarProgramacionAdmin(${s.id}, '${esc(s.name)}')" class="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2 py-1 rounded text-[11px] cursor-pointer" title="Eliminar">
                    <i class="fa fa-trash"></i>
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function formatFrecuenciaBadge(s) {
  const freq = (s.frequency || '').toUpperCase();
  if (freq === 'DIARIA' || freq === 'DIARIO') {
    return `<div><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800">Diaria</span> <span class="font-mono text-[11px] text-slate-800 font-semibold ml-1">${esc(s.run_time)}</span></div>`;
  } else if (freq === 'SEMANAL') {
    return `<div><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800">Semanal</span> <span class="text-[11px] text-slate-700 font-medium ml-1">${esc(s.day_of_week || 'Lunes')} ${esc(s.run_time)}</span></div>`;
  } else if (freq === 'INTERVALO_HORAS' || freq === 'CADA_HORAS' || freq === 'HORAS') {
    return `<div><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800">Cada ${s.interval_value || 1} h</span> <span class="text-[10px] text-slate-500">recurrente</span></div>`;
  } else if (freq === 'INTERVALO_MINUTOS' || freq === 'CADA_MINUTOS' || freq === 'MINUTOS') {
    return `<div><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-teal-800">Cada ${s.interval_value || 1} min</span> <span class="text-[10px] text-slate-500">recurrente</span></div>`;
  } else if (freq === 'INTERVALO_SEGUNDOS' || freq === 'CADA_SEGUNDOS' || freq === 'SEGUNDOS') {
    return `<div><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">Cada ${s.interval_value || 10} seg</span> <span class="text-[9px] text-amber-700 font-bold ml-1">PRUEBAS</span></div>`;
  }
  return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">${esc(s.frequency)}</span>`;
}

let historialGlobal = [];
let restauracionesGlobal = [];

async function renderBackupsHistorialView(container) {
  const rows = await api('/backups/history');
  historialGlobal = rows;

  container.innerHTML = `
    <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-list-check text-slate-700"></i> Historial de Ejecuciones
        </h1>
        <p class="text-xs text-slate-500">Bitácora completa de operaciones manuales y programadas</p>
      </div>
      <button onclick="cargarModuloAdmin('backups-historial')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded cursor-pointer">
        <i class="fa fa-rotate"></i> Actualizar
      </button>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Inicio</th>
              <th class="py-2.5 px-3">Fin</th>
              <th class="py-2.5 px-3">Duración</th>
              <th class="py-2.5 px-3">Tipo</th>
              <th class="py-2.5 px-3">Nombre de la Copia</th>
              <th class="py-2.5 px-3">Usuario / Disparador</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Detalle</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${rows.length === 0 ? '<tr><td colspan="8" class="text-center text-slate-400 py-6">No hay registros en el historial aún.</td></tr>' : rows.map(h => `
              <tr class="hover:bg-slate-50 transition-colors">
                <td class="py-2.5 px-3 font-semibold text-slate-800">${esc(h.started_at)}</td>
                <td class="py-2.5 px-3 font-mono text-slate-600">${esc(h.finished_at || '--')}</td>
                <td class="py-2.5 px-3 text-slate-600 font-medium">${esc(h.duration_str || '--')}</td>
                <td class="py-2.5 px-3">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${h.trigger === 'MANUAL' ? 'bg-purple-100 text-purple-800' : 'bg-sky-100 text-sky-800'}">
                    ${esc(formatTipoBackupVisible(h.trigger))}
                  </span>
                </td>
                <td class="py-2.5 px-3 font-semibold text-slate-900">${esc(formatNombreBackupVisible(h.filename, h.description))}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(h.user_name || 'Sistema')}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${h.status === 'CORRECTO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    ${esc(h.status)}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-right">
                  <button onclick="verHistorialDetalleAdmin(${h.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] cursor-pointer inline-flex items-center gap-1 font-semibold" title="Ver detalle de operación">
                    <i class="fa fa-eye"></i> Ver
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderBackupsRestauracionesView(container) {
  const rows = await api('/backups/restores');
  restauracionesGlobal = rows;

  container.innerHTML = `
    <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
      <div>
        <h1 class="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <i class="fa fa-rotate-left text-amber-600"></i> Historial de Restauraciones de Prueba
        </h1>
        <p class="text-xs text-slate-500">Bitácora de pruebas de restauración aisladas en PostgreSQL</p>
      </div>
      <button onclick="cargarModuloAdmin('backups-restauraciones')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded cursor-pointer">
        <i class="fa fa-rotate"></i> Actualizar
      </button>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead class="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Fecha Inicio</th>
              <th class="py-2.5 px-3">Duración</th>
              <th class="py-2.5 px-3">Nombre de la Restauración</th>
              <th class="py-2.5 px-3">Copia Utilizada</th>
              <th class="py-2.5 px-3">Base de Prueba</th>
              <th class="py-2.5 px-3">Usuario</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Resultado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${rows.length === 0 ? '<tr><td colspan="8" class="text-center text-slate-400 py-6">No hay restauraciones registradas aún.</td></tr>' : rows.map(r => `
              <tr class="hover:bg-slate-50 transition-colors">
                <td class="py-2.5 px-3 font-semibold text-slate-800">${esc(r.started_at)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(r.duration_str || '--')}</td>
                <td class="py-2.5 px-3 font-semibold text-slate-900">${esc(r.description || formatNombreRestauracionVisible(r.target_database))}</td>
                <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(formatNombreBackupVisible(r.filename, r.backup_description))}</td>
                <td class="py-2.5 px-3 font-semibold text-amber-800">${esc(formatNombreRestauracionVisible(r.target_database))}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(r.user_name || 'Sistema')}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.status === 'CORRECTO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    ${esc(r.status)}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-right">
                  <button onclick="verRestauracionDetalleAdmin(${r.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] cursor-pointer inline-flex items-center gap-1 font-semibold" title="Ver detalle de restauración">
                    <i class="fa fa-eye"></i> Ver
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// =========================================================================
// ACCIONES Y MODALES DE BACKUPS
// =========================================================================

function abrirModalCrearBackup() {
  const descInput = document.getElementById('crearBackupNombre');
  if (descInput) descInput.value = '';
  document.getElementById('crearBackupLoader').classList.add('hidden');
  document.getElementById('crearBackupAlert').classList.add('hidden');
  document.getElementById('btnConfirmarCrear').disabled = false;
  document.getElementById('btnCancelarCrear').disabled = false;
  document.getElementById('modalCrearBackup').classList.remove('hidden');
}

function cerrarModalCrearBackup() {
  document.getElementById('modalCrearBackup').classList.add('hidden');
}

async function ejecutarCrearBackupAdmin() {
  const descInput = document.getElementById('crearBackupNombre');
  const description = descInput ? descInput.value.trim() : '';

  if (!description) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'warning',
        title: 'Campo obligatorio',
        text: 'Debe ingresar el Nombre de la copia.',
        confirmButtonColor: '#d97706'
      });
    } else {
      alert('Debe ingresar el Nombre de la copia.');
    }
    if (descInput) descInput.focus();
    return;
  }

  const btn = document.getElementById('btnConfirmarCrear');
  const btnCancel = document.getElementById('btnCancelarCrear');
  const loader = document.getElementById('crearBackupLoader');
  const alertEl = document.getElementById('crearBackupAlert');

  btn.disabled = true;
  btnCancel.disabled = true;
  loader.classList.remove('hidden');
  alertEl.classList.add('hidden');

  try {
    const res = await api('/backups', {
      method: 'POST',
      body: JSON.stringify({ description: description || null })
    });
    cerrarModalCrearBackup();

    if (typeof Swal !== 'undefined') {
      const nombreVisible = formatNombreBackupVisible(res.filename, res.description);
      await Swal.fire({
        icon: 'success',
        title: '¡Backup Creado Correctamente!',
        html: `
          <div class="text-left text-xs space-y-1.5 mt-2">
            <p class="text-slate-600">La copia de seguridad binaria fue generada con éxito:</p>
            <div class="p-2.5 bg-slate-50 border border-slate-200 rounded text-slate-800 text-xs space-y-1">
              <div><strong>Nombre:</strong> <span class="font-semibold text-purple-700">${esc(nombreVisible)}</span></div>
              <div><strong>Tamaño:</strong> ${esc(res.size_formatted)}</div>
              <div><strong>Tipo:</strong> <span class="font-semibold text-purple-700">${esc(formatTipoBackupVisible(res.backup_type))}</span></div>
            </div>
          </div>
        `,
        confirmButtonColor: '#059669',
        timer: 3500
      });
    }

    cargarModuloAdmin(moduloActualAdmin);
  } catch (err) {
    loader.classList.add('hidden');
    btn.disabled = false;
    btnCancel.disabled = false;
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'No se pudo crear el backup',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    } else {
      alertEl.className = 'bg-rose-50 border border-rose-200 text-rose-800 rounded p-3 text-xs mb-3';
      alertEl.innerHTML = `<i class="fa fa-triangle-exclamation"></i> <strong>Error al crear el backup:</strong> ${esc(err.message)}`;
      alertEl.classList.remove('hidden');
    }
  }
}

async function descargarBackupAdmin(id, filename) {
  try {
    if (typeof Swal !== 'undefined') {
      const toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 2500,
        timerProgressBar: true
      });
      toast.fire({
        icon: 'info',
        title: 'Iniciando descarga segura...'
      });
    }

    const res = await fetch(window.API_URL + '/backups/' + id + '/download', {
      headers: {
        'Authorization': 'Bearer ' + window.API_TOKEN
      }
    });
    if (!res.ok) {
      let errText = '';
      try {
        const errJson = await res.json();
        errText = errJson.detail || errJson.message || JSON.stringify(errJson);
      } catch {
        errText = await res.text();
      }
      throw new Error(errText || 'Error al descargar el archivo de respaldo');
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename || ('backup_' + id + '.backup');
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(blobUrl);
    document.body.removeChild(a);

    if (typeof Swal !== 'undefined') {
      Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'success',
        title: 'Descarga iniciada exitosamente',
        showConfirmButton: false,
        timer: 2000
      });
    }
  } catch (err) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'Error de descarga',
        text: err.message || 'No se pudo descargar el archivo de respaldo.',
        confirmButtonColor: '#e11d48'
      });
    } else {
      window.open(window.API_URL + '/backups/' + id + '/download?token=' + encodeURIComponent(window.API_TOKEN), '_blank');
    }
  }
}

async function verDetalleBackupAdmin(id) {
  try {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        title: 'Consultando datos...',
        text: 'Obteniendo información del respaldo desde FastAPI...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
      });
    }

    const b = await api('/backups/' + id);

    if (typeof Swal !== 'undefined') {
      Swal.fire({
        title: `<span class="text-base font-bold text-slate-900 flex items-center justify-center gap-2"><i class="fa fa-shield-halved text-purple-600"></i> Detalle de Copia de Seguridad</span>`,
        html: `
          <div class="text-left text-xs text-slate-700 mt-2">
            <table class="w-full border-collapse border border-slate-200 rounded overflow-hidden shadow-2xs">
              <tbody>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2.5 px-3 font-semibold text-slate-600 w-1/3">Nombre descriptivo</td>
                  <td class="py-2.5 px-3 font-bold text-purple-800">${esc(b.description || '--')}</td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2.5 px-3 font-semibold text-slate-600">Copia de seguridad</td>
                  <td class="py-2.5 px-3 font-semibold text-slate-900 break-all">${esc(formatNombreBackupVisible(b.filename, b.description))}</td>
                </tr>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-600">Fecha de Creación</td>
                  <td class="py-2 px-3">${esc(b.created_at || '--')}</td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2 px-3 font-semibold text-slate-600">Tipo</td>
                  <td class="py-2 px-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${b.backup_type === 'MANUAL' ? 'bg-purple-100 text-purple-800' : 'bg-sky-100 text-sky-800'}">
                      ${esc(formatTipoBackupVisible(b.backup_type))}
                    </span>
                  </td>
                </tr>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-600">Tamaño</td>
                  <td class="py-2 px-3 font-semibold">${esc(b.size_formatted)} <span class="text-slate-400 font-normal">(${Number(b.size_bytes || 0).toLocaleString()} bytes)</span></td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2 px-3 font-semibold text-slate-600">Estado</td>
                  <td class="py-2 px-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${b.status === 'CORRECTO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                      ${esc(b.status)}
                    </span>
                  </td>
                </tr>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-600">Inicio</td>
                  <td class="py-2 px-3 font-mono">${esc(b.started_at || b.created_at || '--')}</td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2 px-3 font-semibold text-slate-600">Fin</td>
                  <td class="py-2 px-3 font-mono">${esc(b.finished_at || '--')}</td>
                </tr>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-600">Duración</td>
                  <td class="py-2 px-3 font-semibold text-purple-700">${esc(b.duracion || '--')}</td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2 px-3 font-semibold text-slate-600">Mensaje</td>
                  <td class="py-2 px-3 text-slate-700">${esc(b.mensaje || 'Generado correctamente.')}</td>
                </tr>
                <tr>
                  <td class="py-2.5 px-3 font-semibold text-slate-600">Ruta / Ubicación Segura</td>
                  <td class="py-2.5 px-3 font-mono text-[11px] text-slate-500 break-all">${esc(b.path)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        `,
        showCloseButton: true,
        showConfirmButton: true,
        confirmButtonText: 'Cerrar',
        confirmButtonColor: '#0f172a'
      });
    } else {
      const descEl = document.getElementById('detDescripcion');
      if (descEl) descEl.innerText = b.description || '--';
      document.getElementById('detFilename').innerText = formatNombreBackupVisible(b.filename, b.description);
      document.getElementById('detPath').innerText = b.path;
      document.getElementById('detSize').innerText = `${b.size_formatted} (${b.size_bytes.toLocaleString()} bytes)`;
      document.getElementById('detType').innerText = formatTipoBackupVisible(b.backup_type);
      document.getElementById('detStatus').innerText = b.status;
      document.getElementById('detFecha').innerText = b.created_at;
      document.getElementById('detUsuario').innerText = b.usuario;
      document.getElementById('detDuracion').innerText = b.duracion;
      document.getElementById('detMensaje').innerText = b.mensaje;
      document.getElementById('modalDetalleBackup').classList.remove('hidden');
    }
  } catch (err) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'Error al consultar backup',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    } else {
      alert('Error: ' + err.message);
    }
  }
}

function cerrarModalDetalleBackup() {
  document.getElementById('modalDetalleBackup').classList.add('hidden');
}

async function restaurarBackupAdmin(id, filename, backupDescription = '') {
  const nombreBackupVis = formatNombreBackupVisible(filename, backupDescription);

  if (typeof Swal !== 'undefined') {
    const { value: formValues } = await Swal.fire({
      title: '<span class="text-base font-bold text-slate-900 flex items-center justify-center gap-2"><i class="fa fa-rotate-left text-amber-500"></i> Confirmar Restauración</span>',
      html: `
        <div class="text-left text-xs text-slate-600 space-y-2 mt-2">
          <p>Se restaurará la copia <strong>${esc(nombreBackupVis)}</strong> ejecutando <code>pg_restore</code> en una base de datos de prueba aislada para verificar tablas e índices.</p>
          <div class="p-2.5 bg-amber-50 border border-amber-200 rounded text-amber-900 text-[11px] leading-relaxed">
            <i class="fa fa-shield-halved text-amber-600 mr-1"></i>
            <strong>Aislamiento de Seguridad:</strong> Está prohibido restaurar sobre la base de producción <code>portal_academico</code>.
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">
              Nombre de la restauración <span class="text-rose-500 font-bold">*</span>:
            </label>
            <input type="text" id="swal-restore-description" placeholder="Ej: Restauración de prueba de matrículas" class="w-full border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-amber-500">
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Base restaurada de prueba:</label>
            <input type="text" id="swal-restore-targetdb" value="portal_academico_restaurado_prueba" class="w-full border border-slate-300 rounded px-3 py-1.5 font-mono text-xs text-slate-800 focus:outline-none focus:border-amber-500">
          </div>
        </div>
      `,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: '<i class="fa fa-play mr-1"></i> Restaurar Base de Prueba',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#d97706',
      cancelButtonColor: '#64748b',
      reverseButtons: true,
      showLoaderOnConfirm: true,
      preConfirm: async () => {
        const descInput = document.getElementById('swal-restore-description');
        const dbInput = document.getElementById('swal-restore-targetdb');
        const descVal = descInput ? descInput.value.trim() : '';
        const dbName = dbInput ? dbInput.value.trim() : '';

        if (!descVal) {
          Swal.showValidationMessage('Debe ingresar el Nombre de la restauración');
          return false;
        }
        if (!dbName) {
          Swal.showValidationMessage('Debe ingresar un nombre para la base de datos de prueba');
          return false;
        }
        try {
          const res = await api(`/backups/${id}/restore`, {
            method: 'POST',
            body: JSON.stringify({
              target_database: dbName,
              description: descVal
            })
          });
          return res;
        } catch (err) {
          Swal.showValidationMessage(err.message || 'Error al restaurar');
          return false;
        }
      },
      allowOutsideClick: () => !Swal.isLoading()
    });

    if (formValues) {
      await Swal.fire({
        icon: 'success',
        title: '¡Restauración Completada!',
        text: formValues.message || 'La base de prueba fue creada y restaurada exitosamente.',
        confirmButtonColor: '#059669'
      });
      cargarModuloAdmin('backups-restauraciones');
    }
  } else {
    abrirModalRestaurarAdmin(id, filename, backupDescription);
  }
}

function abrirModalRestaurarAdmin(id, filename, backupDescription = '') {
  document.getElementById('restaurarBackupId').value = id;
  document.getElementById('restaurarFilename').value = formatNombreBackupVisible(filename, backupDescription);
  const descEl = document.getElementById('restaurarDescripcion');
  if (descEl) descEl.value = '';
  document.getElementById('restaurarTargetDb').value = 'portal_academico_restaurado_prueba';
  document.getElementById('restaurarLoader').classList.add('hidden');
  document.getElementById('restaurarAlert').classList.add('hidden');
  document.getElementById('btnConfirmarRestaurar').disabled = false;
  document.getElementById('btnCancelarRestaurar').disabled = false;
  document.getElementById('modalRestaurar').classList.remove('hidden');
}

function cerrarModalRestaurarAdmin() {
  document.getElementById('modalRestaurar').classList.add('hidden');
}

async function ejecutarRestaurarBackupAdmin() {
  const id = document.getElementById('restaurarBackupId').value;
  const targetDb = document.getElementById('restaurarTargetDb').value.trim();
  const descEl = document.getElementById('restaurarDescripcion');
  const description = descEl ? descEl.value.trim() : '';

  if (!description) {
    alert('Debe ingresar el Nombre de la restauración.');
    if (descEl) descEl.focus();
    return;
  }
  if (!targetDb) {
    alert('Ingrese un nombre para la base restaurada de prueba.');
    return;
  }

  const btn = document.getElementById('btnConfirmarRestaurar');
  const btnCancel = document.getElementById('btnCancelarRestaurar');
  const loader = document.getElementById('restaurarLoader');
  const alertEl = document.getElementById('restaurarAlert');

  btn.disabled = true;
  btnCancel.disabled = true;
  loader.classList.remove('hidden');
  alertEl.classList.add('hidden');

  try {
    const res = await api(`/backups/${id}/restore`, {
      method: 'POST',
      body: JSON.stringify({
        target_database: targetDb,
        description: description
      })
    });

    loader.classList.add('hidden');
    alertEl.className = 'bg-emerald-50 border border-emerald-200 text-emerald-800 rounded p-3 text-xs mb-3';
    alertEl.innerHTML = `<i class="fa fa-check-circle"></i> <strong>¡Restauración completada!</strong> ${esc(res.message)}`;
    alertEl.classList.remove('hidden');

    setTimeout(() => {
      cerrarModalRestaurarAdmin();
      cargarModuloAdmin('backups-restauraciones');
    }, 1500);
  } catch (err) {
    loader.classList.add('hidden');
    btn.disabled = false;
    btnCancel.disabled = false;
    alertEl.className = 'bg-rose-50 border border-rose-200 text-rose-800 rounded p-3 text-xs mb-3';
    alertEl.innerHTML = `<i class="fa fa-triangle-exclamation"></i> <strong>Error al restaurar:</strong> ${esc(err.message)}`;
    alertEl.classList.remove('hidden');
  }
}

async function eliminarBackupAdmin(id, filename, description = '') {
  const nombreVis = formatNombreBackupVisible(filename, description);
  if (typeof Swal !== 'undefined') {
    const result = await Swal.fire({
      title: '¿Eliminar esta copia de seguridad?',
      text: 'Esta acción eliminará el archivo de respaldo y no se podrá recuperar.',
      html: `
        <p class="text-xs text-slate-600 mb-3">Esta acción eliminará el archivo de respaldo y no se podrá recuperar.</p>
        <div class="p-2.5 bg-slate-100 rounded font-semibold text-xs text-slate-800 break-all text-left border border-slate-200">
          <i class="fa fa-file-shield text-slate-500 mr-1"></i> ${esc(nombreVis || `Copia #${id}`)}
        </div>
      `,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#e11d48',
      cancelButtonColor: '#64748b',
      reverseButtons: true,
      focusCancel: true
    });

    if (!result.isConfirmed) return;

    try {
      Swal.fire({
        title: 'Eliminando...',
        text: 'Eliminando archivo físico y depurando registros...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
      });

      const res = await api('/backups/' + id, { method: 'DELETE' });

      await Swal.fire({
        icon: 'success',
        title: 'Backup eliminado correctamente',
        text: res.message || 'El archivo físico y el registro fueron depurados.',
        confirmButtonColor: '#059669',
        timer: 2000
      });

      // Actualizar la tabla sin recargar toda la página
      cargarModuloAdmin(moduloActualAdmin);
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'No se pudo eliminar el backup',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    }
  } else {
    if (confirm('¿Eliminar copia de seguridad? Esta acción eliminará el archivo de respaldo y no se podrá recuperar.')) {
      try {
        await api('/backups/' + id, { method: 'DELETE' });
        cargarModuloAdmin(moduloActualAdmin);
      } catch (err) {
        alert('No se pudo eliminar el backup: ' + err.message);
      }
    }
  }
}

function abrirModalProgramacionAdmin(id = null) {
  document.getElementById('formProgramacion').reset();
  document.getElementById('progId').value = '';
  document.getElementById('modalProgTitulo').innerHTML = '<i class="fa fa-clock text-amber-500"></i> Nueva Programación';
  document.getElementById('progFrecuencia').value = 'DIARIA';
  document.getElementById('progHora').value = '02:00:00';
  document.getElementById('progIntervalo').value = '10';

  if (id) {
    const s = programacionesGlobal.find(x => x.id === id);
    if (s) {
      document.getElementById('progId').value = s.id;
      document.getElementById('progNombre').value = s.name;
      document.getElementById('progFrecuencia').value = s.frequency;
      document.getElementById('progHora').value = s.run_time || '02:00:00';
      document.getElementById('progIntervalo').value = s.interval_value || 10;
      document.getElementById('progDiaSemana').value = s.day_of_week || 'Lunes';
      document.getElementById('progRetencion').value = s.retention_days;
      document.getElementById('progHabilitado').value = s.enabled ? '1' : '0';
      document.getElementById('modalProgTitulo').innerHTML = '<i class="fa fa-pen text-amber-500"></i> Editar Programación';
    }
  }

  toggleFrecuenciaAdmin();
  document.getElementById('modalProgramacion').classList.remove('hidden');
}

function cerrarModalProgramacionAdmin() {
  document.getElementById('modalProgramacion').classList.add('hidden');
}

function toggleFrecuenciaAdmin() {
  const freq = document.getElementById('progFrecuencia').value;
  const groupDiaSemana = document.getElementById('groupDiaSemana');
  const groupHora = document.getElementById('groupHora');
  const groupIntervalo = document.getElementById('groupIntervalo');
  const lblIntervalo = document.getElementById('lblIntervalo');
  const hintIntervalo = document.getElementById('hintIntervalo');
  const inputIntervalo = document.getElementById('progIntervalo');

  if (freq === 'SEMANAL') {
    if (groupDiaSemana) groupDiaSemana.style.display = 'block';
    if (groupHora) groupHora.style.display = 'block';
    if (groupIntervalo) groupIntervalo.style.display = 'none';
  } else if (freq === 'DIARIA' || freq === 'DIARIO') {
    if (groupDiaSemana) groupDiaSemana.style.display = 'none';
    if (groupHora) groupHora.style.display = 'block';
    if (groupIntervalo) groupIntervalo.style.display = 'none';
  } else if (freq === 'INTERVALO_HORAS') {
    if (groupDiaSemana) groupDiaSemana.style.display = 'none';
    if (groupHora) groupHora.style.display = 'none';
    if (groupIntervalo) groupIntervalo.style.display = 'block';
    if (lblIntervalo) lblIntervalo.textContent = 'Cada cuántas horas:';
    if (hintIntervalo) hintIntervalo.textContent = 'Mínimo 1 hora (ej: 1, 4, 12, 24 horas)';
    if (inputIntervalo) { inputIntervalo.min = 1; if (!inputIntervalo.value || parseInt(inputIntervalo.value) < 1) inputIntervalo.value = 1; }
  } else if (freq === 'INTERVALO_MINUTOS') {
    if (groupDiaSemana) groupDiaSemana.style.display = 'none';
    if (groupHora) groupHora.style.display = 'none';
    if (groupIntervalo) groupIntervalo.style.display = 'block';
    if (lblIntervalo) lblIntervalo.textContent = 'Cada cuántos minutos:';
    if (hintIntervalo) hintIntervalo.textContent = 'Mínimo 1 minuto (ej: 5, 15, 30 minutos)';
    if (inputIntervalo) { inputIntervalo.min = 1; if (!inputIntervalo.value || parseInt(inputIntervalo.value) < 1) inputIntervalo.value = 5; }
  } else if (freq === 'INTERVALO_SEGUNDOS') {
    if (groupDiaSemana) groupDiaSemana.style.display = 'none';
    if (groupHora) groupHora.style.display = 'none';
    if (groupIntervalo) groupIntervalo.style.display = 'block';
    if (lblIntervalo) lblIntervalo.textContent = 'Cada cuántos segundos:';
    if (hintIntervalo) hintIntervalo.textContent = 'Modo de pruebas de laboratorio: Mínimo 10 segundos';
    if (inputIntervalo) { inputIntervalo.min = 10; if (!inputIntervalo.value || parseInt(inputIntervalo.value) < 10) inputIntervalo.value = 10; }
  }
}

// Alias de retrocompatibilidad si algún elemento HTML llamaba toggleDiaSemanaAdmin
function toggleDiaSemanaAdmin() {
  toggleFrecuenciaAdmin();
}

async function guardarProgramacionAdmin(e) {
  e.preventDefault();
  const id = document.getElementById('progId').value;
  const freq = document.getElementById('progFrecuencia').value;
  let runTimeVal = document.getElementById('progHora').value || '02:00:00';
  if (runTimeVal.split(':').length === 2) {
    runTimeVal += ':00';
  }

  let intervalVal = null;
  if (freq.startsWith('INTERVALO_')) {
    intervalVal = parseInt(document.getElementById('progIntervalo').value);
    if (freq === 'INTERVALO_SEGUNDOS' && (isNaN(intervalVal) || intervalVal < 10)) {
      if (typeof Swal !== 'undefined') {
        Swal.fire({
          icon: 'warning',
          title: 'Intervalo inválido',
          text: 'Para el modo de pruebas en segundos, el mínimo permitido es de 10 segundos.',
          confirmButtonColor: '#d97706'
        });
      } else {
        alert('Para el modo de pruebas en segundos, el mínimo permitido es de 10 segundos.');
      }
      return;
    }
    if ((freq === 'INTERVALO_MINUTOS' || freq === 'INTERVALO_HORAS') && (isNaN(intervalVal) || intervalVal < 1)) {
      if (typeof Swal !== 'undefined') {
        Swal.fire({
          icon: 'warning',
          title: 'Intervalo inválido',
          text: 'El intervalo debe ser al menos 1.',
          confirmButtonColor: '#d97706'
        });
      } else {
        alert('El intervalo debe ser al menos 1.');
      }
      return;
    }
  }

  const nombreInput = document.getElementById('progNombre');
  const nombreVal = nombreInput ? nombreInput.value.trim() : '';
  if (!nombreVal) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'warning',
        title: 'Campo obligatorio',
        text: 'Debe ingresar el Nombre de la programación.',
        confirmButtonColor: '#d97706'
      });
    } else {
      alert('Debe ingresar el Nombre de la programación.');
    }
    if (nombreInput) nombreInput.focus();
    return;
  }

  const payload = {
    name: nombreVal,
    frequency: freq,
    run_time: runTimeVal,
    interval_value: intervalVal,
    day_of_week: freq === 'SEMANAL' ? document.getElementById('progDiaSemana').value : null,
    retention_days: parseInt(document.getElementById('progRetencion').value),
    enabled: document.getElementById('progHabilitado').value === '1'
  };

  try {
    if (id) {
      await api('/backups/schedules/' + id, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await api('/backups/schedules', { method: 'POST', body: JSON.stringify(payload) });
    }
    cerrarModalProgramacionAdmin();

    if (typeof Swal !== 'undefined') {
      await Swal.fire({
        icon: 'success',
        title: id ? '¡Programación Actualizada!' : '¡Programación Creada!',
        text: id ? 'Los parámetros de la política automática fueron actualizados con éxito.' : 'La política automática de copias de seguridad fue registrada exitosamente.',
        confirmButtonColor: '#059669',
        timer: 2000
      });
    }

    cargarModuloAdmin('backups-programacion');
  } catch (err) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'Error al guardar programación',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    } else {
      alert('Error al guardar programación: ' + err.message);
    }
  }
}

async function eliminarProgramacionAdmin(id, name) {
  if (typeof Swal !== 'undefined') {
    const result = await Swal.fire({
      title: '¿Eliminar programación?',
      html: `Esta acción eliminará la política automática <strong>"${esc(name || `ID #${id}`)}"</strong> y no se volverá a ejecutar.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#e11d48',
      cancelButtonColor: '#64748b',
      reverseButtons: true,
      focusCancel: true
    });

    if (!result.isConfirmed) return;

    try {
      await api('/backups/schedules/' + id, { method: 'DELETE' });

      Swal.fire({
        icon: 'success',
        title: 'Programación eliminada',
        confirmButtonColor: '#059669',
        timer: 1800
      });

      cargarModuloAdmin('backups-programacion');
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'Error al eliminar programación',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    }
  } else {
    if (confirm('¿Eliminar esta política de programación?')) {
      try {
        await api('/backups/schedules/' + id, { method: 'DELETE' });
        cargarModuloAdmin('backups-programacion');
      } catch (err) {
        alert('Error: ' + err.message);
      }
    }
  }
}

async function probarProgramacionAdmin(id, name) {
  if (typeof Swal !== 'undefined') {
    const result = await Swal.fire({
      title: '¿Ejecutar programación ahora?',
      html: `Se forzará la creación inmediata de una copia de seguridad para la política <strong>"${esc(name || `ID #${id}`)}"</strong> bajo demanda (registrada como Manual).`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: '<i class="fa fa-play mr-1"></i> Ejecutar Ahora',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: '#059669',
      cancelButtonColor: '#64748b',
      reverseButtons: true
    });

    if (!result.isConfirmed) return;

    try {
      Swal.fire({
        title: 'Ejecutando copia de seguridad...',
        text: 'pg_dump está generando el archivo en segundo plano...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
      });

      const res = await api(`/backups/schedules/${id}/run-now`, { method: 'POST' });

      await Swal.fire({
        icon: 'success',
        title: '¡Copia generada con éxito!',
        text: res.message,
        confirmButtonColor: '#059669',
        timer: 2500
      });

      cargarModuloAdmin('backups-programacion');
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'Error al ejecutar programación',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    }
  } else {
    if (confirm('¿Ejecutar esta programación inmediatamente?')) {
      try {
        const res = await api(`/backups/schedules/${id}/run-now`, { method: 'POST' });
        alert(res.message);
        cargarModuloAdmin('backups-programacion');
      } catch (err) {
        alert('Error: ' + err.message);
      }
    }
  }
}

async function toggleEstadoProgramacionAdmin(id, estadoActual, name) {
  const nuevoEstado = !estadoActual;
  const accion = nuevoEstado ? 'activar' : 'pausar';

  if (typeof Swal !== 'undefined') {
    const result = await Swal.fire({
      title: `¿Desea ${accion} esta programación?`,
      html: `La política automática <strong>"${esc(name)}"</strong> pasará a estar <strong>${nuevoEstado ? 'Activa' : 'Pausada'}</strong>.`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: nuevoEstado ? 'Sí, activar' : 'Sí, pausar',
      cancelButtonText: 'Cancelar',
      confirmButtonColor: nuevoEstado ? '#059669' : '#eab308',
      cancelButtonColor: '#64748b',
      reverseButtons: true
    });

    if (!result.isConfirmed) return;

    try {
      await api(`/backups/schedules/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ enabled: nuevoEstado })
      });

      Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'success',
        title: `Programación ${nuevoEstado ? 'activada' : 'pausada'} correctamente`,
        showConfirmButton: false,
        timer: 2000
      });

      cargarModuloAdmin('backups-programacion');
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'Error al cambiar estado',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    }
  } else {
    try {
      await api(`/backups/schedules/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ enabled: nuevoEstado })
      });
      cargarModuloAdmin('backups-programacion');
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }
}

async function verDetalleProgramacionAdmin(id) {
  try {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        title: 'Consultando política...',
        text: 'Obteniendo datos de la programación desde FastAPI...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
      });
    }

    const s = await api('/backups/schedules/' + id);

    let freqDesc = s.frequency;
    if (s.frequency === 'DIARIA' || s.frequency === 'DIARIO') freqDesc = 'Diaria (Hora fija HH:MM:SS)';
    else if (s.frequency === 'SEMANAL') freqDesc = `Semanal (${s.day_of_week || 'Lunes'})`;
    else if (s.frequency === 'INTERVALO_HORAS') freqDesc = `Cada ${s.interval_value || 1} hora(s)`;
    else if (s.frequency === 'INTERVALO_MINUTOS') freqDesc = `Cada ${s.interval_value || 1} minuto(s)`;
    else if (s.frequency === 'INTERVALO_SEGUNDOS') freqDesc = `Cada ${s.interval_value || 10} segundo(s) (Modo Pruebas)`;

    if (typeof Swal !== 'undefined') {
      Swal.fire({
        title: '<span class="text-base font-bold text-slate-900 flex items-center justify-center gap-2"><i class="fa fa-clock text-amber-500"></i> Detalle de Programación</span>',
        html: `
          <div class="text-left text-xs text-slate-700 mt-2">
            <table class="w-full border-collapse border border-slate-200 rounded overflow-hidden shadow-2xs">
              <tbody>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2.5 px-3 font-semibold text-slate-600 w-1/3">Nombre</td>
                  <td class="py-2.5 px-3 font-bold text-slate-900">${esc(s.name)} <span class="text-[10px] text-slate-400 font-mono font-normal">(ID #${s.id})</span></td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2 px-3 font-semibold text-slate-600">Frecuencia</td>
                  <td class="py-2 px-3 font-medium">${esc(freqDesc)}</td>
                </tr>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-600">Hora / Intervalo</td>
                  <td class="py-2 px-3 font-mono font-bold text-purple-700">${esc(s.run_time || (s.interval_value ? s.interval_value + ' (seg/min/h)' : '--'))}</td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2 px-3 font-semibold text-slate-600">Retención</td>
                  <td class="py-2 px-3 font-semibold">${s.retention_days === 0 ? '<span class="text-purple-700 bg-purple-50 px-2 py-0.5 rounded text-[10px] font-bold border border-purple-200">Indefinida (nunca expira)</span>' : `${s.retention_days} días`}</td>
                </tr>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-600">Estado</td>
                  <td class="py-2 px-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${s.enabled ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}">
                      <i class="fa ${s.enabled ? 'fa-circle-check' : 'fa-circle-pause'} mr-0.5"></i> ${s.enabled ? 'Activa' : 'Pausada'}
                    </span>
                  </td>
                </tr>
                <tr class="border-b border-slate-200">
                  <td class="py-2 px-3 font-semibold text-slate-600">Próxima Ejecución</td>
                  <td class="py-2 px-3 font-mono text-purple-700 font-bold">${esc(s.next_run_at || '--')}</td>
                </tr>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-600">Última Ejecución</td>
                  <td class="py-2 px-3 font-mono text-slate-600">${esc(s.last_run_at || 'Aún no ejecutado')}</td>
                </tr>
                <tr>
                  <td class="py-2 px-3 font-semibold text-slate-600">Fecha de Creación</td>
                  <td class="py-2 px-3 text-slate-500 font-mono text-[11px]">${esc(s.created_at || '--')}</td>
                </tr>
              </tbody>
            </table>
          </div>
        `,
        showCloseButton: true,
        showConfirmButton: true,
        confirmButtonText: 'Cerrar',
        confirmButtonColor: '#0f172a'
      });
    } else {
      alert(`Programación #${s.id}\nNombre: ${s.name}\nFrecuencia: ${freqDesc}\nPróxima: ${s.next_run_at || '--'}`);
    }
  } catch (err) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'Error al consultar programación',
        text: err.message,
        confirmButtonColor: '#e11d48'
      });
    } else {
      alert('Error: ' + err.message);
    }
  }
}

function verHistorialDetalleAdmin(id) {
  const h = (historialGlobal || []).find(x => x.id === id);
  if (!h) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({ icon: 'warning', title: 'Registro no encontrado', confirmButtonColor: '#e11d48' });
    } else {
      alert('Registro no encontrado');
    }
    return;
  }

  if (typeof Swal !== 'undefined') {
    Swal.fire({
      title: '<span class="text-base font-bold text-slate-900 flex items-center justify-center gap-2"><i class="fa fa-list-check text-purple-600"></i> Detalle de Operación</span>',
      html: `
        <div class="text-left text-xs text-slate-700 mt-2">
          <table class="w-full border-collapse border border-slate-200 rounded overflow-hidden shadow-2xs">
            <tbody>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-600 w-1/3">Inicio</td>
                <td class="py-2.5 px-3 font-mono font-semibold text-slate-900">${esc(h.started_at || '--')}</td>
              </tr>
              <tr class="border-b border-slate-200">
                <td class="py-2 px-3 font-semibold text-slate-600">Fin</td>
                <td class="py-2 px-3 font-mono text-slate-700">${esc(h.finished_at || '--')}</td>
              </tr>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2 px-3 font-semibold text-slate-600">Duración</td>
                <td class="py-2 px-3 font-semibold text-purple-700">${esc(h.duration_str || '--')}</td>
              </tr>
              <tr class="border-b border-slate-200">
                <td class="py-2 px-3 font-semibold text-slate-600">Tipo</td>
                <td class="py-2 px-3">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${h.trigger === 'MANUAL' ? 'bg-purple-100 text-purple-800' : 'bg-sky-100 text-sky-800'}">
                    ${esc(formatTipoBackupVisible(h.trigger) || '--')}
                  </span>
                </td>
              </tr>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-600">Nombre descriptivo</td>
                <td class="py-2.5 px-3 font-bold text-purple-800">${esc(h.description || '--')}</td>
              </tr>
              <tr class="border-b border-slate-200">
                <td class="py-2.5 px-3 font-semibold text-slate-600">Copia de seguridad</td>
                <td class="py-2.5 px-3 font-semibold text-slate-900 break-all">${esc(formatNombreBackupVisible(h.filename, h.description) || 'N/A')}</td>
              </tr>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-600">Estado</td>
                <td class="py-2.5 px-3">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${h.status === 'CORRECTO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    ${esc(h.status)}
                  </span>
                </td>
              </tr>
              <tr>
                <td class="py-2.5 px-3 font-semibold text-slate-600">Mensaje</td>
                <td class="py-2.5 px-3 text-slate-700 break-words leading-relaxed">${esc(h.message || 'Operación ejecutada con éxito.')}</td>
              </tr>
            </tbody>
          </table>
        </div>
      `,
      showCloseButton: true,
      showConfirmButton: true,
      confirmButtonText: 'Cerrar',
      confirmButtonColor: '#0f172a'
    });
  } else {
    alert(`Operación #${h.id}\nNombre: ${h.description || '--'}\nInicio: ${h.started_at}\nFin: ${h.finished_at}\nDuración: ${h.duration_str}\nTipo: ${formatTipoBackupVisible(h.trigger)}\nCopia: ${formatNombreBackupVisible(h.filename, h.description)}\nEstado: ${h.status}\nMensaje: ${h.message}`);
  }
}

function verRestauracionDetalleAdmin(id) {
  const r = (restauracionesGlobal || []).find(x => x.id === id);
  if (!r) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({ icon: 'warning', title: 'Registro no encontrado', confirmButtonColor: '#e11d48' });
    } else {
      alert('Registro no encontrado');
    }
    return;
  }

  if (typeof Swal !== 'undefined') {
    Swal.fire({
      title: '<span class="text-base font-bold text-slate-900 flex items-center justify-center gap-2"><i class="fa fa-rotate-left text-amber-600"></i> Detalle de Restauración</span>',
      html: `
        <div class="text-left text-xs text-slate-700 mt-2">
          <table class="w-full border-collapse border border-slate-200 rounded overflow-hidden shadow-2xs">
            <tbody>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-600 w-1/3">Nombre descriptivo</td>
                <td class="py-2.5 px-3 font-bold text-amber-800">${esc(r.description || '--')}</td>
              </tr>
              <tr class="border-b border-slate-200">
                <td class="py-2.5 px-3 font-semibold text-slate-600">Copia utilizada</td>
                <td class="py-2.5 px-3 font-semibold text-slate-900 break-all">${esc(formatNombreBackupVisible(r.filename, r.backup_description) || 'N/A')}</td>
              </tr>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2 px-3 font-semibold text-slate-600">Base restaurada de prueba</td>
                <td class="py-2 px-3 font-semibold text-amber-800">${esc(formatNombreRestauracionVisible(r.target_database, r.description))}</td>
              </tr>
              <tr class="border-b border-slate-200">
                <td class="py-2 px-3 font-semibold text-slate-600">Fecha</td>
                <td class="py-2 px-3 font-mono text-slate-800">${esc(r.started_at || '--')}</td>
              </tr>
              <tr class="border-b border-slate-200 bg-slate-50">
                <td class="py-2 px-3 font-semibold text-slate-600">Duración</td>
                <td class="py-2 px-3 font-semibold text-purple-700">${esc(r.duration_str || '--')}</td>
              </tr>
              <tr class="border-b border-slate-200">
                <td class="py-2 px-3 font-semibold text-slate-600">Estado</td>
                <td class="py-2 px-3">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.status === 'CORRECTO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    ${esc(r.status)}
                  </span>
                </td>
              </tr>
              <tr>
                <td class="py-2.5 px-3 font-semibold text-slate-600">Mensaje</td>
                <td class="py-2.5 px-3 text-slate-700 break-words leading-relaxed">${esc(r.message || 'Sin observaciones.')}</td>
              </tr>
            </tbody>
          </table>
        </div>
      `,
      showCloseButton: true,
      showConfirmButton: true,
      confirmButtonText: 'Cerrar',
      confirmButtonColor: '#0f172a'
    });
  } else {
    alert(`Restauración #${r.id}\nCopia utilizada: ${formatNombreBackupVisible(r.filename)}\nBase restaurada de prueba: ${formatNombreRestauracionVisible(r.target_database)}\nFecha: ${r.started_at}\nDuración: ${r.duration_str}\nEstado: ${r.status}\nMensaje: ${r.message}`);
  }
}

function verLogHistorialAdmin(mensaje, startedAt, filename) {
  if (typeof Swal !== 'undefined') {
    Swal.fire({
      title: '<span class="text-base font-bold text-slate-900"><i class="fa fa-terminal text-slate-600 mr-1"></i> Log de Ejecución</span>',
      html: `
        <div class="text-left text-xs space-y-2 mt-2">
          <div class="text-slate-500 text-[11px]">${esc(startedAt)} | Copia: <strong>${esc(formatNombreBackupVisible(filename) || '--')}</strong></div>
          <pre class="bg-slate-900 text-emerald-400 p-3 rounded font-mono text-[11px] whitespace-pre-wrap overflow-x-auto max-h-60 border border-slate-800 text-left">${esc(mensaje || 'Operación ejecutada con éxito.')}</pre>
        </div>
      `,
      confirmButtonText: 'Cerrar',
      confirmButtonColor: '#0f172a'
    });
  } else {
    alert('Log del Historial:\n\n' + mensaje);
  }
}

function verResultadoRestauracionAdmin(mensaje, startedAt, targetDb) {
  if (typeof Swal !== 'undefined') {
    Swal.fire({
      title: '<span class="text-base font-bold text-slate-900"><i class="fa fa-database text-amber-500 mr-1"></i> Resultado de Restauración</span>',
      html: `
        <div class="text-left text-xs space-y-2 mt-2">
          <div class="text-slate-500 text-[11px]">Base: <strong>${esc(formatNombreRestauracionVisible(targetDb))}</strong> | Inicio: ${esc(startedAt)}</div>
          <div class="bg-slate-50 text-slate-800 p-3 rounded text-xs border border-slate-200 leading-relaxed text-left">${esc(mensaje || 'Sin detalles adicionales')}</div>
        </div>
      `,
      confirmButtonText: 'Cerrar',
      confirmButtonColor: '#0f172a'
    });
  } else {
    alert('Resultado:\n\n' + mensaje);
  }
}
