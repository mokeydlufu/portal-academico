/**
 * PORTAL ACADÉMICO - LÓGICA INTEGRAL DEL ESTUDIANTE (SPA)
 * Módulos, navegación en acordeón, llamadas a FastAPI y renderizado dinámico.
 */

let estudianteGlobal = null;
let periodosGlobal = [];
let moduloActual = 'notas';
let cacheBienestar = null;

// Mapa de sub-ruta a módulo padre acordeón
const moduloToParentMap = {
  'personal-perfil': 'personal',
  'personal-datos': 'personal',
  'personal-password': 'personal',
  'matricula-actual': 'matricula',
  'matricula-cursos': 'matricula',
  'matricula-horario': 'matricula',
  'record': 'academica',
  'avance': 'academica',
  'rendimiento': 'academica',
  'encuestas': 'academica',
  'notas': 'academica',
  'asistencias': 'academica',
  'tramites-mis': 'tramites',
  'tramites-nuevo': 'tramites',
  'pagos': 'tramites',
  'bienestar-ficha': 'bienestar',
  'bienestar-actualizar': 'bienestar',
  'recuperacion-solicitar': 'recuperacion',
  'recuperacion-mis': 'recuperacion',
  'reprogramacion-solicitar': 'reprogramacion',
  'reprogramacion-mis': 'reprogramacion',
  'bolsa-ofertas': 'bolsa',
  'bolsa-postulaciones': 'bolsa'
};

const allAccordionModules = [
  'personal', 'matricula', 'academica', 'tramites',
  'bienestar', 'recuperacion', 'reprogramacion', 'bolsa'
];

const allNavIds = [
  'nav-inicio',
  'nav-personal-perfil', 'nav-personal-datos', 'nav-personal-password',
  'nav-matricula-actual', 'nav-matricula-cursos', 'nav-matricula-horario',
  'nav-record', 'nav-avance', 'nav-rendimiento', 'nav-encuestas', 'nav-notas', 'nav-asistencias',
  'nav-tramites-mis', 'nav-tramites-nuevo', 'nav-pagos',
  'nav-bienestar-ficha', 'nav-bienestar-actualizar',
  'nav-recuperacion-solicitar', 'nav-recuperacion-mis',
  'nav-reprogramacion-solicitar', 'nav-reprogramacion-mis',
  'nav-bolsa-ofertas', 'nav-bolsa-postulaciones'
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

  // Toggle sidebar en pantallas móviles
  const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('-translate-x-full');
    });
  }

  // Cargar datos base
  await cargarPerfilEstudiante();
  await cargarPeriodosData();

  // Cargar vista inicial predeterminada (Notas del Periodo)
  await cargarModulo('notas');
});

// =========================================================================
// GESTIÓN DE ACORDEÓN (+ / -) Y RESALTADO DE SIDEBAR
// =========================================================================

function toggleModuloAccordion(modName, autoOpenOnly = false) {
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
    // Comportamiento de acordeón estricto: cerrar TODOS los demás módulos
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
  // Limpiar estilos de todos los enlaces del menú
  allNavIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('text-rose-500', 'font-semibold', 'bg-slate-900/40');
      if (id !== 'nav-inicio') {
        el.classList.add('text-slate-400');
      }
    }
  });

  // Si pertenece a un módulo colapsable, abrir el acordeón correspondiente
  const parentMod = moduloToParentMap[modulo];
  if (parentMod) {
    toggleModuloAccordion(parentMod, true);
  } else if (modulo === 'inicio') {
    // Si es inicio, podemos contraer los módulos acordeón
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

  // Resaltar el elemento activo
  const currentNav = document.getElementById(`nav-${modulo}`);
  if (currentNav) {
    currentNav.classList.remove('text-slate-400');
    currentNav.classList.add('text-rose-500', 'font-semibold', 'bg-slate-900/40');
  }
}

// =========================================================================
// DATOS BASE DEL ESTUDIANTE Y PERIODOS
// =========================================================================

async function cargarPerfilEstudiante() {
  try {
    const est = await api('/estudiante/perfil');
    if (!est) return;
    estudianteGlobal = est;

    const topName = document.getElementById('topbarStudentName');
    const topCareer = document.getElementById('topbarStudentCareer');
    const dropName = document.getElementById('dropdownName');
    const dropCode = document.getElementById('dropdownCode');

    if (topName) topName.textContent = est.nombre_completo;
    if (topCareer) topCareer.textContent = `${est.carrera} - CICLO ${est.ciclo}`;
    if (dropName) dropName.textContent = est.nombre_completo;
    if (dropCode) dropCode.textContent = `Cód: ${est.codigo} | ${est.correo}`;

    // Actualizar modal de perfil
    const pNom = document.getElementById('profNombre');
    const pCod = document.getElementById('profCodigo');
    const pDni = document.getElementById('profDni');
    const pCic = document.getElementById('profCiclo');
    const pCar = document.getElementById('profCarrera');
    const pCor = document.getElementById('profCorreo');
    const pTel = document.getElementById('profTelefono');
    const pDir = document.getElementById('profDireccion');

    if (pNom) pNom.textContent = est.nombre_completo;
    if (pCod) pCod.textContent = `Código de Alumno: ${est.codigo}`;
    if (pDni) pDni.textContent = est.dni;
    if (pCic) pCic.textContent = `Ciclo ${est.ciclo}`;
    if (pCar) pCar.textContent = est.carrera;
    if (pCor) pCor.textContent = est.correo;
    if (pTel) pTel.textContent = est.telefono || '987654321';
    if (pDir) pDir.textContent = est.direccion || 'Av. Universitaria 1450, Lima';

    // Form modal
    const editTel = document.getElementById('editTelefono');
    const editDir = document.getElementById('editDireccion');
    if (editTel) editTel.value = est.telefono || '987654321';
    if (editDir) editDir.value = est.direccion || 'Av. Universitaria 1450, Lima';
  } catch (err) {
    console.error('Error cargando perfil:', err);
  }
}

async function cargarPeriodosData() {
  try {
    const periodos = await api('/periodos');
    periodosGlobal = periodos || [];
  } catch (err) {
    console.error('Error cargando periodos:', err);
  }
}

// =========================================================================
// ENRUTADOR DINÁMICO DE MÓDULOS (SPA)
// =========================================================================

async function cargarModulo(modulo) {
  moduloActual = modulo;
  actualizarResaltadoSidebar(modulo);
  const container = document.getElementById('dynamicContentContainer');
  if (!container) return;

  container.innerHTML = `
    <div class="py-16 text-center text-slate-400">
      <i class="fa fa-spinner fa-spin text-3xl mb-2 text-[#f4511e]"></i>
      <p class="text-xs font-medium">Consultando registros oficiales en el servidor...</p>
    </div>
  `;

  try {
    switch (modulo) {
      // 1. Inicio
      case 'inicio':
        await renderInicioView(container);
        break;

      // 2. Personal
      case 'personal':
      case 'personal-perfil':
        await renderPersonalPerfilView(container);
        break;
      case 'personal-datos':
        await renderPersonalDatosView(container);
        break;
      case 'personal-password':
        await renderPersonalPasswordView(container);
        break;

      // 3. Matrícula
      case 'matricula':
      case 'matricula-actual':
        await renderMatriculaActualView(container);
        break;
      case 'matricula-cursos':
        await renderMatriculaCursosView(container);
        break;
      case 'matricula-horario':
        await renderMatriculaHorarioView(container);
        break;

      // 4. Académica
      case 'record':
        await renderRecordView(container);
        break;
      case 'avance':
        await renderAvanceView(container);
        break;
      case 'rendimiento':
        await renderRendimientoView(container);
        break;
      case 'encuestas':
        await renderEncuestasView(container);
        break;
      case 'notas':
        await renderNotasView(container);
        break;
      case 'asistencias':
        await renderAsistenciasView(container);
        break;

      // 5. Trámites y Pagos
      case 'tramites':
      case 'tramites-mis':
        await renderTramitesMisView(container);
        break;
      case 'tramites-nuevo':
        await renderTramitesNuevoView(container);
        break;
      case 'pagos':
        await renderPagosView(container);
        break;

      // 6. Fichas Bienestar
      case 'bienestar':
      case 'bienestar-ficha':
        await renderBienestarFichaView(container);
        break;
      case 'bienestar-actualizar':
        await renderBienestarActualizarView(container);
        break;

      // 7. Examen Recuperación
      case 'recuperacion':
      case 'recuperacion-solicitar':
        await renderRecuperacionSolicitarView(container);
        break;
      case 'recuperacion-mis':
        await renderRecuperacionMisView(container);
        break;

      // 8. Examen Reprogramación
      case 'reprogramacion':
      case 'reprogramacion-solicitar':
        await renderReprogramacionSolicitarView(container);
        break;
      case 'reprogramacion-mis':
        await renderReprogramacionMisView(container);
        break;

      // 9. Bolsa Laboral
      case 'bolsa':
      case 'bolsa-ofertas':
        await renderBolsaOfertasView(container);
        break;
      case 'bolsa-postulaciones':
        await renderBolsaPostulacionesView(container);
        break;

      default:
        await renderNotasView(container);
    }
  } catch (err) {
    container.innerHTML = `
      <div class="bg-rose-50 border border-rose-200 rounded p-5 text-xs text-rose-700 shadow-xs">
        <h4 class="font-bold mb-1 flex items-center gap-1.5"><i class="fa fa-triangle-exclamation"></i> Error al consultar el módulo</h4>
        <p>${esc(err.message)}</p>
        <button onclick="cargarModulo('notas')" class="mt-3 bg-rose-600 hover:bg-rose-700 text-white px-3 py-1.5 rounded cursor-pointer">Volver a Notas del Periodo</button>
      </div>
    `;
  }
}

// =========================================================================
// 1. INICIO (DASHBOARD GENERAL DEL ESTUDIANTE)
// =========================================================================

async function renderInicioView(container) {
  const data = await api('/estudiante/dashboard');
  const est = data.estudiante;
  const res = data.resumen;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: INICIO - PANEL GENERAL DEL ESTUDIANTE
      </h2>
      <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-clipboard-check"></i> Ir a Notas del Periodo
      </button>
    </div>

    <!-- Tarjeta de Bienvenida -->
    <div class="bg-white border border-slate-200/70 rounded-sm p-5 mb-5 shadow-2xs">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-full bg-slate-900 text-white flex items-center justify-center text-xl font-bold flex-shrink-0">
            <i class="fa fa-user-graduate"></i>
          </div>
          <div>
            <span class="text-[11px] text-slate-400 uppercase font-bold block">Bienvenido a la Intranet Académica</span>
            <h3 class="text-base sm:text-lg font-bold text-slate-800 uppercase">${esc(est.nombre_completo)}</h3>
            <p class="text-xs text-slate-500">${esc(est.carrera)} - Ciclo ${est.ciclo} | Cód: <strong>${esc(est.codigo)}</strong></p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-3 py-1 rounded bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center gap-1">
            <i class="fa fa-circle text-[8px]"></i> ALUMNO REGULAR
          </span>
        </div>
      </div>

      <!-- 4 Métricas Clave -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div class="bg-slate-50 border border-slate-200 rounded p-3">
          <div class="text-[10px] text-slate-500 font-semibold uppercase">Cursos Matriculados</div>
          <div class="text-xl font-bold text-sky-600 mt-1">${res.cursos_matriculados}</div>
          <span class="text-[10px] text-slate-400">Periodo 2026 II-B</span>
        </div>
        <div class="bg-slate-50 border border-slate-200 rounded p-3">
          <div class="text-[10px] text-slate-500 font-semibold uppercase">Promedio del Ciclo</div>
          <div class="text-xl font-bold text-emerald-600 mt-1">${Number(res.promedio_ciclo || 0).toFixed(2)}</div>
          <span class="text-[10px] text-slate-400">Ponderado actual</span>
        </div>
        <div class="bg-slate-50 border border-slate-200 rounded p-3">
          <div class="text-[10px] text-slate-500 font-semibold uppercase">Asistencia Global</div>
          <div class="text-xl font-bold text-slate-800 mt-1">${res.porcentaje_asistencia}%</div>
          <span class="text-[10px] text-emerald-600 font-medium">Habilitado</span>
        </div>
        <div class="bg-slate-50 border border-slate-200 rounded p-3">
          <div class="text-[10px] text-slate-500 font-semibold uppercase">Trámites Pendientes</div>
          <div class="text-xl font-bold text-amber-600 mt-1">${res.tramites_pendientes || 0}</div>
          <span class="text-[10px] text-slate-400">En gestión</span>
        </div>
      </div>
    </div>

    <!-- 2 Tablas Dinámicas: Últimas Notas y Próximas Evaluaciones -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
      <!-- Columna 1: Últimas Notas Registradas -->
      <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
        <h4 class="text-xs font-bold text-slate-700 uppercase mb-3 flex items-center justify-between">
          <span class="flex items-center gap-1.5"><i class="fa fa-award text-rose-500"></i> Últimas Notas Registradas</span>
          <button onclick="cargarModulo('notas')" class="text-xs text-[#f4511e] hover:underline font-normal cursor-pointer">Ver todas</button>
        </h4>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-50 text-slate-500 border-b border-slate-200">
              <tr>
                <th class="py-2 px-2.5">Curso</th>
                <th class="py-2 px-2.5">Evaluación</th>
                <th class="py-2 px-2.5 text-center">Nota</th>
                <th class="py-2 px-2.5 text-center">Fecha</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${(data.ultimas_notas || []).map(n => `
                <tr class="hover:bg-slate-50">
                  <td class="py-2 px-2.5 font-medium text-slate-800">${esc(n.curso)}</td>
                  <td class="py-2 px-2.5 text-slate-600">${esc(n.evaluacion)}</td>
                  <td class="py-2 px-2.5 text-center font-bold ${n.nota >= 10.5 ? 'text-blue-600' : 'text-rose-600'}">${Number(n.nota).toFixed(2)}</td>
                  <td class="py-2 px-2.5 text-center text-slate-500">${esc(n.fecha)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Columna 2: Próximas Evaluaciones -->
      <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
        <h4 class="text-xs font-bold text-slate-700 uppercase mb-3 flex items-center justify-between">
          <span class="flex items-center gap-1.5"><i class="fa fa-clock text-amber-500"></i> Próximas Evaluaciones</span>
          <button onclick="cargarModulo('notas')" class="text-xs text-[#f4511e] hover:underline font-normal cursor-pointer">Calendario</button>
        </h4>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-50 text-slate-500 border-b border-slate-200">
              <tr>
                <th class="py-2 px-2.5">Curso</th>
                <th class="py-2 px-2.5">Evaluación</th>
                <th class="py-2 px-2.5 text-center">Fecha</th>
                <th class="py-2 px-2.5 text-center">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${(data.proximas_evaluaciones || []).map(ev => `
                <tr class="hover:bg-slate-50">
                  <td class="py-2 px-2.5 font-medium text-slate-800">${esc(ev.curso)}</td>
                  <td class="py-2 px-2.5 text-slate-600">${esc(ev.evaluacion)}</td>
                  <td class="py-2 px-2.5 text-center text-slate-500">${esc(ev.fecha || ev.fecha_estimada)}</td>
                  <td class="py-2 px-2.5 text-center">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">${esc(ev.estado)}</span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Cursos Actuales con Acceso a Notas -->
    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <h4 class="text-xs font-bold text-slate-700 uppercase mb-3 flex items-center justify-between">
        <span class="flex items-center gap-1.5"><i class="fa fa-book text-slate-400"></i> Asignaturas Matriculadas en el Semestre</span>
        <button onclick="cargarModulo('matricula-cursos')" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-[11px] px-3 py-1 rounded cursor-pointer">
          Ver Ficha de Matrícula
        </button>
      </h4>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        ${(data.cursos_actuales || []).map(c => `
          <div class="border border-slate-200 rounded p-3 hover:border-slate-300 hover:shadow-xs transition-all bg-white flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between text-[10px] font-bold text-slate-400 mb-1">
                <span>${esc(c.codigo)} - Sec: ${esc(c.seccion)}</span>
                <span class="text-slate-600">${c.creditos} Créd.</span>
              </div>
              <div class="font-bold text-slate-800 text-xs uppercase mb-1">${esc(c.curso)}</div>
              <div class="text-[11px] text-slate-500 mb-2 truncate"><i class="fa fa-user-tie mr-1 text-[10px]"></i>${esc(c.docente)}</div>
            </div>
            <div class="pt-2 border-t border-slate-100 flex items-center justify-between mt-2">
              <span class="text-[11px] font-semibold text-slate-600">Promedio: <strong class="text-blue-600">${c.promedio ? Number(c.promedio).toFixed(2) : '--'}</strong></span>
              <button onclick="verDetalleNotas(${c.matricula_id})" class="bg-[#5cb85c] hover:bg-[#4cae4c] text-white text-[11px] px-2.5 py-1 rounded cursor-pointer font-medium">
                Ver Notas
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// =========================================================================
// 2. PERSONAL: MI PERFIL, DATOS PERSONALES, CAMBIAR CONTRASEÑA
// =========================================================================

async function renderPersonalPerfilView(container) {
  const est = await api('/estudiante/perfil');
  estudianteGlobal = est;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: PERSONAL - MI PERFIL ESTUDIANTIL
      </h2>
      <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Notas
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-6 shadow-2xs max-w-3xl">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 mb-4">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-full bg-slate-900 text-white flex items-center justify-center text-2xl font-bold flex-shrink-0">
            <i class="fa fa-user-graduate"></i>
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-800 uppercase">${esc(est.nombre_completo)}</h3>
            <p class="text-xs text-slate-500">Código Universitario: <strong class="text-slate-800">${esc(est.codigo)}</strong></p>
            <span class="inline-block mt-1 px-2.5 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">ESTADO ACADÉMICO: REGULAR</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="cargarModulo('personal-datos')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-3.5 py-1.5 rounded cursor-pointer flex items-center gap-1.5 shadow-xs">
            <i class="fa fa-user-pen"></i> Actualizar Datos
          </button>
          <button onclick="cargarModulo('personal-password')" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-3.5 py-1.5 rounded cursor-pointer flex items-center gap-1.5 shadow-xs">
            <i class="fa fa-key"></i> Contraseña
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div class="border border-slate-100 rounded p-3 bg-slate-50/50">
          <span class="text-slate-400 block text-[10px] uppercase font-bold">Documento Nacional de Identidad (DNI)</span>
          <span class="font-bold text-slate-800 text-sm">${esc(est.dni)}</span>
        </div>
        <div class="border border-slate-100 rounded p-3 bg-slate-50/50">
          <span class="text-slate-400 block text-[10px] uppercase font-bold">Correo Institucional</span>
          <span class="font-bold text-slate-800 text-sm">${esc(est.correo)}</span>
        </div>
        <div class="border border-slate-100 rounded p-3 bg-slate-50/50">
          <span class="text-slate-400 block text-[10px] uppercase font-bold">Carrera Profesional</span>
          <span class="font-bold text-slate-800 text-sm">${esc(est.carrera)}</span>
        </div>
        <div class="border border-slate-100 rounded p-3 bg-slate-50/50">
          <span class="text-slate-400 block text-[10px] uppercase font-bold">Ciclo Actual</span>
          <span class="font-bold text-slate-800 text-sm">Ciclo ${est.ciclo}</span>
        </div>
        <div class="border border-slate-100 rounded p-3 bg-slate-50/50">
          <span class="text-slate-400 block text-[10px] uppercase font-bold">Teléfono de Contacto</span>
          <span class="font-bold text-slate-800 text-sm">${esc(est.telefono || '987654321')}</span>
        </div>
        <div class="border border-slate-100 rounded p-3 bg-slate-50/50">
          <span class="text-slate-400 block text-[10px] uppercase font-bold">Dirección Registrada</span>
          <span class="font-bold text-slate-800 text-sm">${esc(est.direccion || 'Av. Universitaria 1450, Lima')}</span>
        </div>
      </div>
    </div>
  `;
}

async function renderPersonalDatosView(container) {
  const est = await api('/estudiante/perfil');
  estudianteGlobal = est;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: PERSONAL - ACTUALIZACIÓN DE DATOS PERSONALES
      </h2>
      <button onclick="cargarModulo('personal-perfil')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Mi Perfil
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-6 shadow-2xs max-w-2xl">
      <div id="personalAlert" class="hidden mb-4 p-3 rounded text-xs"></div>

      <form id="formDatosPersonales" onsubmit="guardarDatosPersonales(event)" class="space-y-4 text-xs">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-slate-500 font-bold mb-1 uppercase text-[10px]">Nombres y Apellidos</label>
            <input type="text" value="${esc(est.nombre_completo)}" disabled class="w-full bg-slate-100 border border-slate-200 rounded px-3 py-2 text-slate-600 cursor-not-allowed">
          </div>
          <div>
            <label class="block text-slate-500 font-bold mb-1 uppercase text-[10px]">Código de Estudiante</label>
            <input type="text" value="${esc(est.codigo)}" disabled class="w-full bg-slate-100 border border-slate-200 rounded px-3 py-2 text-slate-600 cursor-not-allowed">
          </div>
          <div>
            <label class="block text-slate-500 font-bold mb-1 uppercase text-[10px]">DNI</label>
            <input type="text" value="${esc(est.dni)}" disabled class="w-full bg-slate-100 border border-slate-200 rounded px-3 py-2 text-slate-600 cursor-not-allowed">
          </div>
          <div>
            <label class="block text-slate-500 font-bold mb-1 uppercase text-[10px]">Correo Institucional</label>
            <input type="text" value="${esc(est.correo)}" disabled class="w-full bg-slate-100 border border-slate-200 rounded px-3 py-2 text-slate-600 cursor-not-allowed">
          </div>
        </div>

        <div class="border-t border-slate-100 pt-4 mt-2">
          <h4 class="font-bold text-slate-800 uppercase text-[11px] mb-3">Datos de Contacto Actualizables</h4>
          <div class="space-y-3">
            <div>
              <label class="block text-slate-700 font-semibold mb-1">Teléfono Móvil / Celular:</label>
              <input id="inputDatosTelefono" type="tel" required value="${esc(est.telefono || '987654321')}" class="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:border-rose-500">
            </div>
            <div>
              <label class="block text-slate-700 font-semibold mb-1">Dirección de Residencia Actual:</label>
              <input id="inputDatosDireccion" type="text" required value="${esc(est.direccion || 'Av. Universitaria 1450, Lima')}" class="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:border-rose-500">
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
          <button type="button" onclick="cargarModulo('personal-perfil')" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2 rounded cursor-pointer">
            Cancelar
          </button>
          <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-5 py-2 rounded cursor-pointer flex items-center gap-1.5">
            <i class="fa fa-save"></i> Guardar Cambios
          </button>
        </div>
      </form>
    </div>
  `;
}

async function guardarDatosPersonales(e) {
  e.preventDefault();
  const tel = document.getElementById('inputDatosTelefono').value;
  const dir = document.getElementById('inputDatosDireccion').value;
  const alertBox = document.getElementById('personalAlert');

  try {
    await api('/estudiante/perfil', {
      method: 'PUT',
      body: JSON.stringify({ telefono: tel, direccion: dir })
    });
    alertBox.className = 'block p-3 rounded bg-emerald-100 text-emerald-800 font-medium mb-4';
    alertBox.textContent = 'Datos de contacto actualizados exitosamente en la base de datos.';
    await cargarPerfilEstudiante();
  } catch (err) {
    alertBox.className = 'block p-3 rounded bg-rose-100 text-rose-800 font-medium mb-4';
    alertBox.textContent = 'Error al actualizar datos: ' + err.message;
  }
}

async function renderPersonalPasswordView(container) {
  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: PERSONAL - CAMBIAR CONTRASEÑA DE ACCESO
      </h2>
      <button onclick="cargarModulo('personal-perfil')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Mi Perfil
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-6 shadow-2xs max-w-md">
      <div id="passInPanelAlert" class="hidden mb-4 p-3 rounded text-xs"></div>

      <form onsubmit="handlePanelPasswordChange(event)" class="space-y-4 text-xs">
        <div>
          <label class="block text-slate-700 font-semibold mb-1">Contraseña Actual:</label>
          <input id="panelPwdActual" type="password" required class="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block text-slate-700 font-semibold mb-1">Nueva Contraseña:</label>
          <input id="panelPwdNueva" type="password" required minlength="6" class="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block text-slate-700 font-semibold mb-1">Confirmar Nueva Contraseña:</label>
          <input id="panelPwdConfirmar" type="password" required minlength="6" class="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:border-rose-500">
        </div>

        <div class="pt-2 text-right">
          <button type="submit" class="bg-[#f4511e] hover:bg-[#e64a19] text-white font-bold px-5 py-2 rounded cursor-pointer flex items-center gap-1.5 ml-auto">
            <i class="fa fa-key"></i> Actualizar Contraseña
          </button>
        </div>
      </form>
    </div>
  `;
}

async function handlePanelPasswordChange(e) {
  e.preventDefault();
  const pAct = document.getElementById('panelPwdActual').value;
  const pNew = document.getElementById('panelPwdNueva').value;
  const pConf = document.getElementById('panelPwdConfirmar').value;
  const alertBox = document.getElementById('passInPanelAlert');

  if (pNew !== pConf) {
    alertBox.className = 'block p-3 rounded bg-rose-100 text-rose-800 font-medium mb-4';
    alertBox.textContent = 'Las nuevas contraseñas no coinciden.';
    return;
  }

  try {
    await api('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ password_actual: pAct, password_nueva: pNew })
    });
    alertBox.className = 'block p-3 rounded bg-emerald-100 text-emerald-800 font-medium mb-4';
    alertBox.textContent = 'Contraseña actualizada correctamente en el sistema.';
    e.target.reset();
  } catch (err) {
    let msg = err.message;
    try { const j = JSON.parse(msg); if (j.detail) msg = j.detail; } catch(e){}
    alertBox.className = 'block p-3 rounded bg-rose-100 text-rose-800 font-medium mb-4';
    alertBox.textContent = msg;
  }
}

// =========================================================================
// 3. MATRÍCULA: ACTUAL, CURSOS MATRICULADOS, HORARIO
// =========================================================================

async function renderMatriculaActualView(container) {
  const data = await api('/estudiante/matricula/detalle');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: MATRÍCULA - FICHA OFICIAL DE MATRÍCULA ACTUAL (${esc(data.periodo)})
      </h2>
      <button onclick="descargarBoletaSimple()" class="bg-[#f4511e] hover:bg-[#e64a19] text-white px-3 py-1 rounded text-xs flex items-center gap-1.5 shadow-xs cursor-pointer">
        <i class="fa fa-file-pdf"></i> Constancia de Matrícula
      </button>
    </div>

    <!-- Resumen de Matrícula -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 text-center">
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Periodo Académico</span>
        <span class="text-base font-bold text-slate-800">${esc(data.periodo)}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Total Créditos</span>
        <span class="text-base font-bold text-sky-600">${data.creditos_matriculados}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Estado Matrícula</span>
        <span class="text-xs font-bold text-emerald-700 mt-1 block">${esc(data.estado_matricula)}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Fecha de Registro</span>
        <span class="text-xs font-bold text-slate-700 mt-1 block">${esc(data.fecha_matricula)}</span>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3 text-center w-10">N°</th>
              <th class="py-2.5 px-3 w-28">Código</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3 w-20 text-center">Sección</th>
              <th class="py-2.5 px-3 w-16 text-center">Créd.</th>
              <th class="py-2.5 px-3">Horario</th>
              <th class="py-2.5 px-3 text-center">Aula</th>
              <th class="py-2.5 px-3 text-right">Detalle</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.cursos.map((c, idx) => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 text-center text-slate-400">${idx + 1}</td>
                <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(c.codigo)}</td>
                <td class="py-2.5 px-3 uppercase font-medium text-slate-800">
                  <div>${esc(c.curso)}</div>
                  <div class="text-[10px] text-slate-400 font-normal"><i class="fa fa-user-tie mr-1 text-[9px]"></i>${esc(c.docente)}</div>
                </td>
                <td class="py-2.5 px-3 text-center text-slate-600">${esc(c.seccion)}</td>
                <td class="py-2.5 px-3 text-center font-bold">${c.creditos}</td>
                <td class="py-2.5 px-3 text-slate-600 font-medium">${esc(c.horario)}</td>
                <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 bg-slate-100 rounded text-slate-700 font-semibold">${esc(c.aula)}</span></td>
                <td class="py-2.5 px-3 text-right">
                  <button onclick="abrirCursoDetalle(${JSON.stringify(c).replace(/"/g, '&quot;')})" class="bg-sky-600 hover:bg-sky-700 text-white text-[11px] px-2.5 py-1 rounded cursor-pointer">
                    Ver Info
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

async function renderMatriculaCursosView(container) {
  const matriculas = await api('/estudiante/me/matriculas');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: MATRÍCULA - CURSOS MATRICULADOS DEL PERIODO
      </h2>
      <button onclick="cargarModulo('matricula-horario')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-calendar-days"></i> Ver Horario Semanal
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3 text-center w-10">N°</th>
              <th class="py-2.5 px-3 w-28">Código</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3 text-center w-24">Sección</th>
              <th class="py-2.5 px-3 text-center w-24">Estado</th>
              <th class="py-2.5 px-3 text-right w-48">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${matriculas.map((m, idx) => `
              <tr class="hover:bg-slate-50">
                <td class="py-3 px-3 text-center text-slate-400">${idx + 1}</td>
                <td class="py-3 px-3 font-semibold text-slate-700">${esc(m.codigo)}</td>
                <td class="py-3 px-3 uppercase font-medium text-slate-800">${esc(m.curso)}</td>
                <td class="py-3 px-3 text-center text-slate-600">${esc(m.seccion)}</td>
                <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">${esc(m.estado)}</span></td>
                <td class="py-3 px-3 text-right space-x-1.5">
                  <button onclick="verDetalleNotas(${m.matricula_id})" class="bg-[#5cb85c] hover:bg-[#4cae4c] text-white text-[11px] px-2.5 py-1 rounded cursor-pointer font-medium">
                    Ver Notas
                  </button>
                  <button onclick="verSilabo(${m.matricula_id})" class="bg-slate-600 hover:bg-slate-700 text-white text-[11px] px-2.5 py-1 rounded cursor-pointer">
                    Ver Sílabo
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

async function renderMatriculaHorarioView(container) {
  const data = await api('/estudiante/horario');
  const dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: MATRÍCULA - HORARIO SEMANAL DE CLASES (PERIODO ${esc(data.periodo)})
      </h2>
      <button onclick="window.print()" class="bg-slate-800 hover:bg-slate-900 text-white px-3 py-1 rounded text-xs flex items-center gap-1.5 shadow-xs cursor-pointer">
        <i class="fa fa-print"></i> Imprimir Horario
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      ${dias.map(dia => {
        const clasesDia = data.dias ? (data.dias[dia] || []) : [];
        return `
          <div class="bg-white border border-slate-200 rounded-sm p-3.5 shadow-2xs flex flex-col">
            <div class="font-bold text-slate-800 text-xs uppercase pb-2 mb-2 border-b border-slate-100 flex items-center justify-between">
              <span>${dia}</span>
              <span class="text-[10px] text-slate-400 font-normal">${clasesDia.length} sesión(es)</span>
            </div>
            <div class="space-y-2 flex-1">
              ${clasesDia.length === 0 ? `
                <div class="text-slate-400 text-center py-6 text-xs italic">Sin actividades lectivas programadas</div>
              ` : clasesDia.map(c => `
                <div class="border border-slate-100 bg-slate-50/70 rounded p-2.5 hover:bg-slate-100/70 transition-colors">
                  <div class="flex items-center justify-between text-[10px] text-[#f4511e] font-bold mb-1">
                    <span><i class="fa fa-clock mr-1"></i>${esc(c.hora_inicio)} - ${esc(c.hora_fin)}</span>
                    <span class="px-1.5 py-0.2 bg-slate-200 text-slate-700 rounded text-[9px]">${esc(c.modalidad)}</span>
                  </div>
                  <strong class="text-xs font-bold text-slate-800 block uppercase leading-snug">${esc(c.curso)}</strong>
                  <div class="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
                    <span>Aula: <strong>${esc(c.aula)}</strong></span>
                    <span class="text-slate-400">Sec: ${esc(c.seccion)}</span>
                  </div>
                  <div class="text-[10px] text-slate-400 mt-0.5 truncate"><i class="fa fa-user-tie mr-1"></i>${esc(c.docente)}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

// =========================================================================
// 4. ACADÉMICA: RÉCORD, AVANCE, RENDIMIENTO, ENCUESTAS, NOTAS, ASISTENCIAS
// =========================================================================

async function renderRecordView(container) {
  const data = await api('/estudiante/record-academico');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: ACADÉMICA - RÉCORD ACADÉMICO HISTÓRICO
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="descargarRecordPdf()" class="bg-[#f4511e] hover:bg-[#e64a19] text-white px-3 py-1 rounded text-xs flex items-center gap-1.5 shadow-xs cursor-pointer">
          <i class="fa fa-file-pdf"></i> Descargar Récord PDF
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 text-center">
      <div class="bg-white border border-slate-200 rounded p-3">
        <div class="text-[10px] text-slate-500 font-semibold uppercase">Promedio Acumulado</div>
        <div class="text-xl font-bold text-sky-600 mt-1">${Number(data.promedio_acumulado).toFixed(2)}</div>
        <span class="text-[10px] text-slate-400">Ponderado histórico</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <div class="text-[10px] text-slate-500 font-semibold uppercase">Créditos Aprobados</div>
        <div class="text-xl font-bold text-emerald-600 mt-1">${data.creditos_aprobados}</div>
        <span class="text-[10px] text-slate-400">De 210 para egreso</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <div class="text-[10px] text-slate-500 font-semibold uppercase">Cursos Aprobados</div>
        <div class="text-xl font-bold text-slate-800 mt-1">${data.cursos_aprobados || data.total_cursos}</div>
        <span class="text-[10px] text-slate-400">Asignaturas superadas</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <div class="text-[10px] text-slate-500 font-semibold uppercase">Cursos Desaprobados</div>
        <div class="text-xl font-bold text-rose-600 mt-1">${data.cursos_desaprobados || 0}</div>
        <span class="text-[10px] text-slate-400">En historial</span>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3 text-center">Periodo</th>
              <th class="py-2.5 px-3 text-center">Créd.</th>
              <th class="py-2.5 px-3 text-center">Promedio</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Detalle</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.cursos.map(c => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(c.codigo)}</td>
                <td class="py-2.5 px-3 uppercase font-medium text-slate-800">${esc(c.curso)}</td>
                <td class="py-2.5 px-3 text-center text-slate-600">${esc(c.periodo)}</td>
                <td class="py-2.5 px-3 text-center font-bold">${c.creditos}</td>
                <td class="py-2.5 px-3 text-center font-bold ${c.promedio >= 10.5 ? 'text-blue-600' : 'text-red-600'}">${Number(c.promedio || 0).toFixed(2)}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${c.estado === 'APROBADO' ? 'bg-emerald-100 text-emerald-800' : (c.estado === 'EN CURSO' ? 'bg-sky-100 text-sky-800' : 'bg-rose-100 text-rose-800')}">${esc(c.estado)}</span>
                </td>
                <td class="py-2.5 px-3 text-right">
                  <button onclick="abrirRecordCursoDetalle(${JSON.stringify(c).replace(/"/g, '&quot;')})" class="bg-slate-700 hover:bg-slate-800 text-white text-[11px] px-2.5 py-1 rounded cursor-pointer">
                    Ver Detalle
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

function abrirRecordCursoDetalle(c) {
  const b = document.getElementById('cursoDetalleBody');
  b.innerHTML = `
    <div class="space-y-2">
      <div><strong class="text-slate-500 block text-[10px] uppercase">Código y Asignatura:</strong> <span class="font-bold text-slate-800 text-sm">${esc(c.codigo)} - ${esc(c.curso)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Periodo Académico:</strong> <span class="font-semibold text-slate-800">${esc(c.periodo)}</span></div>
      <div class="grid grid-cols-2 gap-2">
        <div><strong class="text-slate-500 block text-[10px] uppercase">Créditos:</strong> <span class="font-bold text-slate-700">${c.creditos} CR</span></div>
        <div><strong class="text-slate-500 block text-[10px] uppercase">Calificación Final:</strong> <span class="font-bold ${c.promedio >= 10.5 ? 'text-blue-600' : 'text-red-600'} text-base">${Number(c.promedio || 0).toFixed(2)}</span></div>
      </div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Estado Oficial:</strong> <span class="px-2 py-0.5 rounded text-[10px] font-bold ${c.estado === 'APROBADO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">${esc(c.estado)}</span></div>
    </div>
  `;
  document.getElementById('cursoDetalleModal').classList.remove('hidden');
}

async function renderAvanceView(container) {
  const data = await api('/estudiante/avance-curricular');

  const ciclosGroup = {};
  for (let i = 1; i <= 10; i++) ciclosGroup[i] = [];
  data.malla.forEach(c => {
    if (!ciclosGroup[c.ciclo]) ciclosGroup[c.ciclo] = [];
    ciclosGroup[c.ciclo].push(c);
  });

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: ACADÉMICA - MALLA CURRICULAR Y AVANCE DE GRADO
      </h2>
      <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Notas del Periodo
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-5 mb-4 shadow-2xs">
      <div class="mb-4">
        <span class="text-[10px] text-slate-400 font-bold uppercase block">${esc(data.plan_estudios)}</span>
        <h3 class="text-base font-bold text-slate-800 uppercase">${esc(data.carrera)}</h3>
        <p class="text-xs text-slate-500 mt-0.5">Ubicación Curricular: <strong>Ciclo ${data.ciclo_actual} de ${data.total_ciclos}</strong></p>
      </div>

      <!-- Barra de Progreso Oficial -->
      <div class="mb-4">
        <div class="flex justify-between text-xs font-bold mb-1.5">
          <span>Porcentaje de Grado Cumplido</span>
          <span class="text-[#f4511e]">${data.porcentaje_avance}%</span>
        </div>
        <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
          <div class="bg-[#f4511e] h-3 rounded-full transition-all duration-500" style="width: ${data.porcentaje_avance}%"></div>
        </div>
      </div>

      <!-- 4 Métricas de Créditos -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs mt-4">
        <div class="border border-slate-200 rounded p-2.5 bg-slate-50">
          <span class="text-slate-400 block text-[10px] font-bold uppercase">Créditos de la Carrera</span>
          <span class="text-base font-bold text-slate-800">${data.creditos_totales}</span>
        </div>
        <div class="border border-slate-200 rounded p-2.5 bg-slate-50">
          <span class="text-slate-400 block text-[10px] font-bold uppercase">Créditos Aprobados</span>
          <span class="text-base font-bold text-emerald-600">${data.creditos_aprobados}</span>
        </div>
        <div class="border border-slate-200 rounded p-2.5 bg-slate-50">
          <span class="text-slate-400 block text-[10px] font-bold uppercase">Créditos en Curso</span>
          <span class="text-base font-bold text-sky-600">${data.creditos_cursando}</span>
        </div>
        <div class="border border-slate-200 rounded p-2.5 bg-slate-50">
          <span class="text-slate-400 block text-[10px] font-bold uppercase">Créditos Pendientes</span>
          <span class="text-base font-bold text-amber-600">${data.creditos_pendientes}</span>
        </div>
      </div>

      <!-- Leyenda de Colores -->
      <div class="flex items-center gap-4 flex-wrap mt-4 pt-3 border-t border-slate-100 text-xs">
        <span class="font-bold text-slate-600 text-[11px] uppercase">Leyenda de Estado:</span>
        <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-500 inline-block"></span> Aprobado</span>
        <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-amber-400 inline-block"></span> Cursando Actualmente</span>
        <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-slate-300 inline-block"></span> Pendiente</span>
      </div>
    </div>

    <!-- Malla de 10 Ciclos Curriculares -->
    <div class="space-y-4">
      ${Object.keys(ciclosGroup).map(cNum => `
        <div class="bg-white border border-slate-200/70 rounded-sm p-3.5 shadow-2xs">
          <div class="flex items-center justify-between pb-2 mb-2.5 border-b border-slate-100">
            <span class="font-bold text-slate-800 text-xs uppercase flex items-center gap-2">
              <span class="w-5 h-5 rounded-full bg-slate-800 text-white flex items-center justify-center text-[10px]">${cNum}</span>
              Ciclo Académico ${cNum} ${cNum == data.ciclo_actual ? '<span class="text-[#f4511e] text-[10px] font-black">(Ciclo Actual)</span>' : ''}
            </span>
            <span class="text-[10px] text-slate-400 font-semibold">${ciclosGroup[cNum].length} Asignaturas</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
            ${ciclosGroup[cNum].map(cur => {
              let badgeBg = 'bg-slate-100 text-slate-600 border-slate-200';
              let estadoText = 'PENDIENTE';
              if (cur.estado === 'VERDE') {
                badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-200';
                estadoText = 'APROBADO';
              } else if (cur.estado === 'AMARILLO') {
                badgeBg = 'bg-amber-50 text-amber-800 border-amber-300 ring-1 ring-amber-300';
                estadoText = 'CURSANDO';
              }
              return `
                <div onclick="abrirMallaCurso(${JSON.stringify(cur).replace(/"/g, '&quot;')})" class="malla-curso p-2.5 rounded border ${badgeBg} cursor-pointer flex flex-col justify-between">
                  <div>
                    <div class="flex items-center justify-between text-[10px] font-bold opacity-80 mb-1">
                      <span>${esc(cur.codigo)}</span>
                      <span>${cur.creditos} CR</span>
                    </div>
                    <div class="font-bold text-xs uppercase line-clamp-2 leading-tight">${esc(cur.nombre)}</div>
                  </div>
                  <div class="pt-2 mt-2 border-t border-current/10 flex items-center justify-between text-[10px] font-semibold">
                    <span>${estadoText}</span>
                    <span>${cur.nota !== '--' ? 'Nota: ' + cur.nota : ''}</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

async function renderRendimientoView(container) {
  const data = await api('/estudiante/rendimiento-historico');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: ACADÉMICA - RENDIMIENTO HISTÓRICO POR CICLO
      </h2>
      <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Notas del Periodo
      </button>
    </div>

    <!-- Gráfico Visual de Evolución de Promedios Ponderados -->
    <div class="bg-white border border-slate-200/70 rounded-sm p-5 mb-4 shadow-2xs">
      <div class="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
        <div>
          <h3 class="text-xs font-bold text-slate-800 uppercase">Evolución de Promedio Ponderado Semestral</h3>
          <span class="text-[10px] text-slate-400">Histórico de rendimiento académico en escala vigesimal (0 - 20)</span>
        </div>
        <div class="text-right">
          <span class="text-[10px] text-slate-400 uppercase font-bold block">Promedio Histórico</span>
          <span class="text-base font-bold text-blue-600">${Number(data.promedio_general).toFixed(2)}</span>
        </div>
      </div>

      <!-- Barras de Rendimiento -->
      <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3 pt-2">
        ${data.semestres.map(s => {
          const heightPct = Math.min(100, Math.round((s.promedio / 20) * 100));
          return `
            <div class="bg-slate-50 border border-slate-200 rounded p-3 text-center flex flex-col justify-between items-center h-40">
              <span class="text-xs font-bold text-blue-600">${Number(s.promedio).toFixed(2)}</span>
              <div class="w-8 bg-slate-200 rounded-t flex items-end h-20 overflow-hidden my-1">
                <div class="w-full bg-[#f4511e] rounded-t transition-all duration-500" style="height: ${heightPct}%"></div>
              </div>
              <div>
                <span class="font-bold text-slate-800 text-[11px] block">${esc(s.periodo)}</span>
                <span class="text-[10px] text-slate-400">Ciclo ${s.ciclo}</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>

    <!-- Tabla Semestral Oficial -->
    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Periodo Académico</th>
              <th class="py-2.5 px-3 text-center">Ciclo</th>
              <th class="py-2.5 px-3 text-center">Cursos</th>
              <th class="py-2.5 px-3 text-center">Créd. Matriculados</th>
              <th class="py-2.5 px-3 text-center">Promedio Ponderado</th>
              <th class="py-2.5 px-3 text-center">Estado del Semestre</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.semestres.map(h => `
              <tr class="hover:bg-slate-50">
                <td class="py-3 px-3 font-bold text-slate-800">${esc(h.periodo)}</td>
                <td class="py-3 px-3 text-center font-medium">${h.ciclo}</td>
                <td class="py-3 px-3 text-center font-semibold">${h.cursos}</td>
                <td class="py-3 px-3 text-center font-medium">${h.creditos}</td>
                <td class="py-3 px-3 text-center font-bold text-blue-600 text-sm">${Number(h.promedio).toFixed(2)}</td>
                <td class="py-3 px-3 text-center">
                  <span class="px-2.5 py-0.5 rounded text-[10px] font-bold ${h.estado === 'APROBADO' ? 'bg-emerald-100 text-emerald-800' : 'bg-sky-100 text-sky-800'}">${esc(h.estado)}</span>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderEncuestasView(container) {
  const data = await api('/estudiante/encuestas');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: ACADÉMICA - ENCUESTAS DE EVALUACIÓN DOCENTE
      </h2>
      <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Notas del Periodo
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 mb-4 shadow-2xs">
      <div class="flex items-center justify-between border-b border-slate-100 pb-3 mb-3 text-xs">
        <div>
          <span class="text-slate-400 block text-[10px] font-bold uppercase">Proceso de Evaluación Docente</span>
          <strong class="text-slate-800 text-sm">Periodo Activo ${esc(data.periodo)}</strong>
        </div>
        <span class="px-3 py-1 rounded bg-sky-100 text-sky-800 font-bold text-xs">
          <i class="fa fa-info-circle mr-1"></i> ENCUESTA OBLIGATORIA
        </span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3">Docente a Evaluar</th>
              <th class="py-2.5 px-3 text-center">Fecha Inicio</th>
              <th class="py-2.5 px-3 text-center">Fecha Fin</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-center">Calificación</th>
              <th class="py-2.5 px-3 text-right">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.encuestas.map(enc => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(enc.codigo)}</td>
                <td class="py-2.5 px-3 uppercase font-medium text-slate-800">${esc(enc.curso)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(enc.docente)}</td>
                <td class="py-2.5 px-3 text-center text-slate-500">${esc(enc.fecha_inicio || '2026-09-01')}</td>
                <td class="py-2.5 px-3 text-center text-slate-500">${esc(enc.fecha_fin || '2026-10-30')}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${enc.estado === 'Completada' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                    ${esc(enc.estado)}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-center font-bold text-slate-700">
                  ${enc.calificacion ? '⭐'.repeat(enc.calificacion) + ` (${enc.calificacion}/5)` : '--'}
                </td>
                <td class="py-2.5 px-3 text-right">
                  <button onclick="abrirEncuestaModal(${enc.seccion_id}, ${JSON.stringify(enc.curso)}, ${JSON.stringify(enc.docente)})" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-[11px] px-2.5 py-1 rounded cursor-pointer">
                    ${enc.estado === 'Completada' ? 'Modificar' : 'Responder'}
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

async function renderNotasView(container) {
  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: CURSOS MATRICULADOS EN EL PERIODO - MIS NOTAS
      </h2>
    </div>

    <!-- Barra de Filtros: Selector Periodo y Botones Naranjas -->
    <div class="bg-white border border-slate-200/60 rounded-sm px-4 py-3 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
      <div class="flex items-center gap-2 text-xs">
        <label for="periodoSelect" class="font-normal text-neutral-600">Periodo:</label>
        <div class="relative">
          <select id="periodoSelect" onchange="cargarMatriculas()" class="bg-white border border-slate-300 text-neutral-700 text-xs font-normal rounded px-3 py-1.5 pr-8 focus:outline-none focus:border-rose-400 cursor-pointer">
            <!-- Se puebla dinámicamente -->
          </select>
        </div>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <button type="button" onclick="descargarBoletaSimple()" class="inline-flex items-center gap-1.5 bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs font-normal px-3.5 py-1.5 rounded-sm shadow-2xs transition-colors cursor-pointer" title="Descargar Boleta de Notas Oficial en PDF">
          <i class="fa fa-print"></i>
          <span>Boleta de Notas</span>
        </button>

        <button type="button" onclick="descargarBoletaDetallada()" class="inline-flex items-center gap-1.5 bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs font-normal px-3.5 py-1.5 rounded-sm shadow-2xs transition-colors cursor-pointer" title="Descargar Boleta de Notas Detallada en PDF">
          <i class="fa fa-file-lines"></i>
          <span>Boleta de Notas Detallado</span>
        </button>
      </div>
    </div>

    <!-- Tabla de Cursos Matriculados -->
    <div class="bg-white rounded-sm border border-slate-200/70 shadow-2xs overflow-hidden mb-4">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-white border-b border-neutral-200 text-neutral-500 font-semibold text-xs">
              <th scope="col" class="py-3 px-3.5 w-10 text-center font-semibold">N°</th>
              <th scope="col" class="py-3 px-3.5 w-28 font-semibold">Código</th>
              <th scope="col" class="py-3 px-3.5 font-semibold">Curso</th>
              <th scope="col" class="py-3 px-3.5 w-32 font-semibold">Sección</th>
              <th scope="col" class="py-3 px-3.5 w-16 font-semibold">Estado</th>
              <th scope="col" class="py-3 px-3.5 w-56 text-right font-semibold">Acciones</th>
            </tr>
          </thead>
          <tbody id="cursosTableBody" class="text-neutral-600 font-normal">
            <tr>
              <td colspan="6" class="py-8 text-center text-slate-400">
                <i class="fa fa-spinner fa-spin mr-2"></i> Cargando cursos matriculados...
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Banner Inferior Informativo -->
    <div id="footer-banner" class="bg-[#F4ECF7] border border-[#e8d5ee] rounded-sm px-4 py-2.5 flex items-center justify-between shadow-2xs">
      <div class="text-left text-xs sm:text-[13px] text-[#8b1e2f] tracking-wide font-normal">
        <strong class="font-bold">IMPORTANTE!</strong> VERIFIQUE QUE TODAS SUS EVALUACIONES FIGUREN EN EL DETALLE DE NOTAS.
      </div>
      <button type="button" onclick="document.getElementById('footer-banner').style.display='none'" class="text-neutral-400 hover:text-neutral-700 text-xs font-bold px-1 cursor-pointer" title="Cerrar">
        &#10005;
      </button>
    </div>
  `;

  // Inicializar selector de periodos
  const select = document.getElementById('periodoSelect');
  if (select && periodosGlobal.length > 0) {
    select.innerHTML = '';
    periodosGlobal.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.codigo + (p.activo ? ' (Actual)' : '');
      if (p.activo) opt.selected = true;
      select.appendChild(opt);
    });
  }
  await cargarMatriculas();
}

async function cargarMatriculas() {
  const tbody = document.getElementById('cursosTableBody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" class="py-8 text-center text-slate-400 font-light">
        <i class="fa fa-spinner fa-spin mr-2"></i> Consultando asignaturas matriculadas...
      </td>
    </tr>
  `;

  const select = document.getElementById('periodoSelect');
  const periodoId = select ? select.value : '';
  try {
    const url = periodoId ? `/estudiante/me/matriculas?periodo_id=${periodoId}` : '/estudiante/me/matriculas';
    const matriculas = await api(url);

    if (!matriculas || matriculas.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="py-10 text-center text-neutral-500 font-light bg-neutral-50/40">
            No existen cursos matriculados para este periodo.
          </td>
        </tr>
      `;
      return;
    }

    let html = '';
    matriculas.forEach((m, index) => {
      const bgClass = (index % 2 === 1) ? 'bg-neutral-50/70' : 'bg-white';
      html += `
        <tr class="${bgClass} border-b border-neutral-100 hover:bg-neutral-100/50 transition-colors">
          <td class="py-3 px-3.5 text-center text-neutral-500 font-light">${index + 1}</td>
          <td class="py-3 px-3.5 font-light">${esc(m.codigo)}</td>
          <td class="py-3 px-3.5 font-normal tracking-tight uppercase">${esc(m.curso)}</td>
          <td class="py-3 px-3.5 font-light">${esc(m.seccion)}</td>
          <td class="py-3 px-3.5 font-normal">${esc(m.estado)}</td>
          <td class="py-3 px-3.5 text-right">
            <div class="inline-flex items-center gap-1.5">
              <button type="button" onclick="verDetalleNotas(${m.matricula_id})" class="inline-flex items-center gap-1 bg-[#5cb85c] hover:bg-[#4cae4c] text-white text-[11px] font-normal px-2.5 py-1 rounded-[3px] shadow-2xs transition-colors cursor-pointer" title="Ver detalle de calificaciones">
                <i class="fa fa-clipboard-list text-[10px]"></i>
                <span>Ver Notas</span>
              </button>

              <button type="button" onclick="verSilabo(${m.matricula_id})" class="inline-flex items-center gap-1 ${m.tiene_silabo ? 'bg-[#64748b] hover:bg-[#475569]' : 'bg-[#c8c8c8]'} text-white text-[11px] font-normal px-2.5 py-1 rounded-[3px] shadow-2xs transition-colors cursor-pointer" title="${m.tiene_silabo ? 'Visualizar Sílabo Oficial' : 'Sílabo no disponible'}">
                <i class="fa fa-file-lines text-[10px]"></i>
                <span>Ver Sílabo</span>
              </button>
            </div>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="py-6 text-center text-rose-500 font-normal">
          Error al consultar las asignaturas: ${esc(err.message)}
        </td>
      </tr>
    `;
  }
}

// VISTA EN PANEL DEL DETALLE DE NOTAS DE UN CURSO (SPA SIN RECARGAR)
async function verDetalleNotas(matriculaId) {
  const container = document.getElementById('dynamicContentContainer');
  if (!container) return;

  container.innerHTML = `
    <div class="py-16 text-center text-slate-400">
      <i class="fa fa-spinner fa-spin text-3xl mb-2 text-[#5cb85c]"></i>
      <p class="text-xs font-medium">Consultando detalle de calificaciones...</p>
    </div>
  `;

  try {
    const data = await api(`/matriculas/${matriculaId}/notas`);

    const promActStr = data.promedio_actual !== null ? Number(data.promedio_actual).toFixed(2) : '--';
    const promFinStr = data.promedio_final !== null ? Number(data.promedio_final).toFixed(2) : '--';

    let estadoBadgeClass = 'bg-sky-100 text-sky-800';
    if (data.estado_curso === 'APROBADO') estadoBadgeClass = 'bg-emerald-100 text-emerald-800';
    if (data.estado_curso === 'DESAPROBADO') estadoBadgeClass = 'bg-rose-100 text-rose-800';

    container.innerHTML = `
      <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
        <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
          .: DETALLE OFICIAL DE CALIFICACIONES - ${esc(data.curso)}
        </h2>
        <button onclick="cargarModulo('notas')" class="bg-[#8b1e2f] hover:bg-[#6b1422] text-white px-3 py-1 rounded text-xs flex items-center gap-1.5 shadow-xs cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Cursos
        </button>
      </div>

      <!-- Ficha Informativa del Curso -->
      <div class="bg-white border border-slate-200/70 rounded-sm p-4 mb-4 shadow-2xs">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div class="border border-slate-100 bg-slate-50 p-2.5 rounded">
            <span class="text-slate-400 block text-[10px] font-bold uppercase">Asignatura</span>
            <span class="font-bold text-slate-800 text-xs uppercase">${esc(data.curso)}</span>
          </div>
          <div class="border border-slate-100 bg-slate-50 p-2.5 rounded">
            <span class="text-slate-400 block text-[10px] font-bold uppercase">Código del Curso</span>
            <span class="font-bold text-slate-800 text-xs">${esc(data.codigo)}</span>
          </div>
          <div class="border border-slate-100 bg-slate-50 p-2.5 rounded">
            <span class="text-slate-400 block text-[10px] font-bold uppercase">Docente Titular</span>
            <span class="font-bold text-slate-800 text-xs">${esc(data.docente)}</span>
          </div>
          <div class="border border-slate-100 bg-slate-50 p-2.5 rounded">
            <span class="text-slate-400 block text-[10px] font-bold uppercase">Periodo / Sección</span>
            <span class="font-bold text-slate-800 text-xs">${esc(data.periodo)} - Sec: ${esc(data.seccion)}</span>
          </div>
        </div>
      </div>

      <!-- Tabla de Evaluaciones -->
      <div class="bg-white border border-slate-200/70 rounded-sm p-4 mb-4 shadow-2xs">
        <h4 class="text-xs font-bold text-slate-700 uppercase mb-3 flex items-center gap-1.5">
          <i class="fa fa-list-check text-rose-500"></i> Desglose de Evaluaciones y Ponderaciones
        </h4>
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse text-xs">
            <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th class="py-2.5 px-3">Evaluación</th>
                <th class="py-2.5 px-3 text-center w-20">Tipo</th>
                <th class="py-2.5 px-3 text-center w-24">Peso</th>
                <th class="py-2.5 px-3 text-center w-24">Nota</th>
                <th class="py-2.5 px-3 text-center w-28">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${(!data.evaluaciones || data.evaluaciones.length === 0) ? `
                <tr><td colspan="5" class="py-6 text-center text-slate-400">Sin evaluaciones registradas aún.</td></tr>
              ` : data.evaluaciones.map(ev => {
                const notaStr = (ev.nota !== null && ev.nota !== undefined) ? Number(ev.nota).toFixed(2) : '--';
                const notaColor = (ev.nota !== null && ev.nota >= 10.5) ? 'text-blue-600 font-bold' : (ev.nota !== null ? 'text-rose-600 font-bold' : 'text-slate-400');
                const badge = ev.estado === 'CALIFICADO'
                  ? '<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">Calificado</span>'
                  : '<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800">Pendiente</span>';
                return `
                  <tr class="hover:bg-slate-50">
                    <td class="py-2.5 px-3 font-medium text-slate-800">${esc(ev.evaluacion)}</td>
                    <td class="py-2.5 px-3 text-center text-slate-500">${esc(ev.tipo)}</td>
                    <td class="py-2.5 px-3 text-center text-slate-600 font-medium">${ev.peso}%</td>
                    <td class="py-2.5 px-3 text-center ${notaColor}">${notaStr}</td>
                    <td class="py-2.5 px-3 text-center">${badge}</td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Resumen Ponderado -->
      <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div class="flex items-center gap-6">
          <div>
            <span class="text-slate-400 block text-[10px] font-bold uppercase">Promedio Ponderado Actual</span>
            <span class="text-lg font-bold text-slate-800">${promActStr}</span>
          </div>
          <div class="border-l border-slate-200 pl-6">
            <span class="text-slate-400 block text-[10px] font-bold uppercase">Promedio Final Oficial</span>
            <span class="text-lg font-bold text-blue-600">${promFinStr}</span>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <div>
            <span class="text-slate-400 block text-[10px] font-bold uppercase">Estado de la Asignatura</span>
            <span class="px-3 py-1 rounded text-xs font-bold inline-block mt-0.5 ${estadoBadgeClass}">
              ${esc(data.estado_curso)}
            </span>
          </div>
          <button onclick="cargarModulo('notas')" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-4 py-2 rounded cursor-pointer font-medium">
            Volver a Cursos
          </button>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div class="bg-rose-50 border border-rose-200 rounded p-4 text-xs text-rose-700">
        <p>Error al cargar detalle de notas: ${esc(err.message)}</p>
        <button onclick="cargarModulo('notas')" class="mt-2 bg-rose-600 text-white px-3 py-1 rounded cursor-pointer">Volver</button>
      </div>
    `;
  }
}

// Alias para mantener compatibilidad con cualquier llamada verNotas
function verNotas(matriculaId) {
  verDetalleNotas(matriculaId);
}

// 20. VER SÍLABO (PDF STREAM O ALERTA)
async function verSilabo(matriculaId) {
  try {
    const res = await fetch(`${window.API_URL}/matriculas/${matriculaId}/silabo`, {
      headers: { 'Authorization': 'Bearer ' + window.API_TOKEN }
    });

    if (res.status === 404) {
      alert('Sílabo no disponible para este curso');
      return;
    }
    if (!res.ok) {
      const t = await res.text();
      throw new Error(t);
    }

    const blob = await res.blob();
    const fileUrl = URL.createObjectURL(blob);
    window.open(fileUrl, '_blank');
  } catch (err) {
    alert('Sílabo no disponible para este curso');
  }
}

async function renderAsistenciasView(container) {
  const data = await api('/estudiante/asistencias/detalle');
  const res = data.resumen;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: ACADÉMICA - REGISTRO DE ASISTENCIAS POR ASIGNATURA
      </h2>
      <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Notas del Periodo
      </button>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 text-center">
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">% Asistencia Global</span>
        <span class="text-xl font-bold text-emerald-600 mt-1 block">${res.porcentaje_asistencia}%</span>
        <span class="text-[10px] text-emerald-700 font-semibold">HABILITADO</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Sesiones Registradas</span>
        <span class="text-xl font-bold text-slate-800 mt-1 block">${res.total_sesiones}</span>
        <span class="text-[10px] text-slate-400">Total clases</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Asistidas / Justificadas</span>
        <span class="text-xl font-bold text-sky-600 mt-1 block">${res.presentes + res.justificados}</span>
        <span class="text-[10px] text-slate-400">Presentes</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Faltas / Tardanzas</span>
        <span class="text-xl font-bold ${res.faltas > 0 ? 'text-rose-600' : 'text-slate-800'} mt-1 block">${res.faltas} / ${res.tardanzas}</span>
        <span class="text-[10px] text-slate-400">Inasistencias</span>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-xs font-bold text-slate-700 uppercase">Bitácora Oficial de Asistencias del Semestre</h4>
        <span class="text-xs text-slate-400">Periodo 2026 II-B</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Fecha</th>
              <th class="py-2.5 px-3">Hora</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3">Observación</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.logs.map(l => {
              let badge = 'bg-emerald-100 text-emerald-800';
              if (l.estado === 'FALTA') badge = 'bg-rose-100 text-rose-800';
              if (l.estado === 'TARDANZA') badge = 'bg-amber-100 text-amber-800';
              if (l.estado === 'JUSTIFICADO') badge = 'bg-sky-100 text-sky-800';
              return `
                <tr class="hover:bg-slate-50">
                  <td class="py-2 px-3 font-semibold text-slate-700">${esc(l.fecha)}</td>
                  <td class="py-2 px-3 text-slate-500">${esc(l.hora)}</td>
                  <td class="py-2 px-3 uppercase font-medium text-slate-800">${esc(l.curso)}</td>
                  <td class="py-2 px-3 text-center"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${badge}">${esc(l.estado)}</span></td>
                  <td class="py-2 px-3 text-slate-500">${esc(l.observacion)}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// =========================================================================
// 5. TRÁMITES Y PAGOS: MIS TRÁMITES, NUEVO TRÁMITE, PAGOS
// =========================================================================

async function renderTramitesMisView(container) {
  const data = await api('/estudiante/tramites');
  const res = data.resumen;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: TRÁMITES - MIS SOLICITUDES Y GESTIÓN DOCUMENTARIA
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('tramites-nuevo')" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs px-3 py-1 rounded flex items-center gap-1 cursor-pointer font-bold">
          <i class="fa fa-plus"></i> Nuevo Trámite
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 text-center">
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">En Trámite / Pendientes</span>
        <span class="text-xl font-bold text-amber-600 mt-1 block">${res.pendientes}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">En Revisión</span>
        <span class="text-xl font-bold text-sky-600 mt-1 block">${res.en_revision}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Aprobados / Atendidos</span>
        <span class="text-xl font-bold text-emerald-600 mt-1 block">${res.aprobados}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Rechazados</span>
        <span class="text-xl font-bold text-slate-500 mt-1 block">${res.rechazados}</span>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Tipo de Trámite</th>
              <th class="py-2.5 px-3">Motivo / Asunto</th>
              <th class="py-2.5 px-3 text-center">Fecha Solicitud</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.tramites.map(t => {
              let badge = 'bg-amber-100 text-amber-800';
              if (t.estado === 'APROBADO') badge = 'bg-emerald-100 text-emerald-800';
              if (t.estado === 'RECHAZADO') badge = 'bg-rose-100 text-rose-800';
              if (t.estado === 'EN REVISION') badge = 'bg-sky-100 text-sky-800';
              return `
                <tr class="hover:bg-slate-50">
                  <td class="py-2.5 px-3 font-bold text-slate-800">${esc(t.codigo)}</td>
                  <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(t.tipo)}</td>
                  <td class="py-2.5 px-3 text-slate-600">${esc(t.motivo)}</td>
                  <td class="py-2.5 px-3 text-center text-slate-500">${esc(t.fecha_solicitud)}</td>
                  <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${badge}">${esc(t.estado)}</span></td>
                  <td class="py-2.5 px-3 text-right">
                    <button onclick="abrirTramiteDetalle(${JSON.stringify(t).replace(/"/g, '&quot;')})" class="bg-slate-700 hover:bg-slate-800 text-white text-[11px] px-2.5 py-1 rounded cursor-pointer">
                      Ver Detalle
                    </button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderTramitesNuevoView(container) {
  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: TRÁMITES - REGISTRAR NUEVO TRÁMITE O SOLICITUD
      </h2>
      <button onclick="cargarModulo('tramites-mis')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Mis Trámites
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-6 shadow-2xs max-w-2xl">
      <div id="nuevoTramiteAlert" class="hidden mb-4 p-3 rounded text-xs"></div>

      <form onsubmit="enviarNuevoTramitePanel(event)" class="space-y-4 text-xs">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Tipo de Trámite Solicitado:</label>
          <select id="panelTrmTipo" required class="w-full border border-slate-300 rounded p-2 focus:outline-none focus:border-rose-500">
            <option value="Constancia de Estudios">Constancia de Estudios Oficial</option>
            <option value="Certificado de Notas">Certificado Oficial de Notas</option>
            <option value="Carta de Presentación">Carta de Presentación para Prácticas Pre-Profesionales</option>
            <option value="Justificación de Inasistencia">Justificación Reglamentaria de Inasistencia</option>
            <option value="Rectificación de Matrícula">Rectificación / Modificación de Matrícula</option>
            <option value="Retiro de Asignatura">Retiro Extraordinario de Asignatura</option>
            <option value="Duplicado de Carné Universitario">Duplicado de Carné Universitario</option>
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Motivo o Asunto Breve:</label>
          <input id="panelTrmMotivo" type="text" required placeholder="Ej: Solicitud de constancia para trámite laboral o beca" class="w-full border border-slate-300 rounded p-2 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Descripción y Sustento:</label>
          <textarea id="panelTrmDescripcion" rows="4" required placeholder="Explique detalladamente el motivo de su solicitud..." class="w-full border border-slate-300 rounded p-2.5 focus:outline-none focus:border-rose-500"></textarea>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Documento Sustentatorio (Opcional - PDF o Imagen):</label>
          <input id="panelTrmArchivo" type="file" class="w-full border border-slate-300 rounded p-1.5 text-slate-600">
        </div>

        <div class="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
          <button type="button" onclick="cargarModulo('tramites-mis')" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2 rounded cursor-pointer">
            Cancelar
          </button>
          <button type="submit" class="bg-[#f4511e] hover:bg-[#e64a19] text-white font-bold px-5 py-2 rounded cursor-pointer flex items-center gap-1.5">
            <i class="fa fa-paper-plane"></i> Enviar Solicitud
          </button>
        </div>
      </form>
    </div>
  `;
}

async function enviarNuevoTramitePanel(e) {
  e.preventDefault();
  const tipo = document.getElementById('panelTrmTipo').value;
  const motivo = document.getElementById('panelTrmMotivo').value;
  const desc = document.getElementById('panelTrmDescripcion').value;
  const alertBox = document.getElementById('nuevoTramiteAlert');

  try {
    const res = await api('/estudiante/tramites', {
      method: 'POST',
      body: JSON.stringify({ tipo: tipo, motivo: motivo, descripcion: desc, archivo: null })
    });
    alertBox.className = 'block p-3 rounded bg-emerald-100 text-emerald-800 font-medium mb-4';
    alertBox.textContent = `Solicitud registrada exitosamente con código de trámite: ${res.codigo}. Redirigiendo a Mis Trámites...`;
    setTimeout(() => {
      cargarModulo('tramites-mis');
    }, 1500);
  } catch (err) {
    alertBox.className = 'block p-3 rounded bg-rose-100 text-rose-800 font-medium mb-4';
    alertBox.textContent = 'Error al registrar trámite: ' + err.message;
  }
}

async function renderPagosView(container) {
  const data = await api('/estudiante/pagos');
  const res = data.resumen;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: ESTADO DE CUENTA, PAGOS Y PENSIONES
      </h2>
      <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Notas del Periodo
      </button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4 text-center">
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Monto Total Facturado</span>
        <span class="text-xl font-bold text-slate-800 mt-1 block">S/ ${Number(res.deuda_total).toFixed(2)}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Total Cancelado</span>
        <span class="text-xl font-bold text-emerald-600 mt-1 block">S/ ${Number(res.pagado).toFixed(2)}</span>
      </div>
      <div class="bg-white border border-slate-200 rounded p-3">
        <span class="text-slate-400 block text-[10px] font-bold uppercase">Saldo Pendiente de Pago</span>
        <span class="text-xl font-bold ${res.pendiente > 0 ? 'text-rose-600' : 'text-slate-800'} mt-1 block">S/ ${Number(res.pendiente).toFixed(2)}</span>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-xs font-bold text-slate-700 uppercase">Cronograma Oficial de Cuotas y Pensiones</h4>
        <span class="text-xs text-slate-400">Ciclo 2026 II-B</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Concepto</th>
              <th class="py-2.5 px-3 text-center">Monto (S/)</th>
              <th class="py-2.5 px-3 text-center">Vencimiento</th>
              <th class="py-2.5 px-3 text-center">Fecha de Pago</th>
              <th class="py-2.5 px-3 text-center">N° Operación</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.pagos.map(p => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-800">${esc(p.concepto)}</td>
                <td class="py-2.5 px-3 text-center font-bold text-slate-700">S/ ${Number(p.monto).toFixed(2)}</td>
                <td class="py-2.5 px-3 text-center text-slate-500">${esc(p.fecha_vencimiento)}</td>
                <td class="py-2.5 px-3 text-center text-slate-600">${esc(p.fecha_pago)}</td>
                <td class="py-2.5 px-3 text-center font-mono text-slate-500">${esc(p.nro_operacion)}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${p.estado === 'CANCELADO' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    ${esc(p.estado)}
                  </span>
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
// 6. FICHAS BIENESTAR: MI FICHA, ACTUALIZAR DATOS
// =========================================================================

async function renderBienestarFichaView(container) {
  const data = await api('/estudiante/bienestar');
  cacheBienestar = data;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: BIENESTAR UNIVERSITARIO - FICHA INTEGRAL DEL ESTUDIANTE
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('bienestar-actualizar')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-3 py-1 rounded flex items-center gap-1 cursor-pointer font-bold">
          <i class="fa fa-pen"></i> Actualizar Ficha
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <!-- Tarjeta 1: Contacto de Emergencia -->
      <div class="bg-white border border-slate-200 rounded p-4 shadow-2xs">
        <span class="text-slate-400 block text-[10px] font-bold uppercase flex items-center gap-1">
          <i class="fa fa-phone-volume text-rose-500"></i> Contacto de Emergencia
        </span>
        <div class="font-bold text-slate-800 text-sm mt-1.5">${esc(data.contacto_emergencia)}</div>
        <p class="text-xs text-slate-600 mt-1">Parentesco: <strong>${esc(data.parentesco_contacto)}</strong></p>
        <p class="text-xs text-slate-600 mt-0.5">Teléfono: <strong class="text-emerald-700">${esc(data.telefono_emergencia)}</strong></p>
      </div>

      <!-- Tarjeta 2: Seguro y Salud -->
      <div class="bg-white border border-slate-200 rounded p-4 shadow-2xs">
        <span class="text-slate-400 block text-[10px] font-bold uppercase flex items-center gap-1">
          <i class="fa fa-shield-heart text-sky-500"></i> Seguro de Salud
        </span>
        <div class="font-bold text-slate-800 text-sm mt-1.5">${esc(data.seguro_salud)}</div>
        <p class="text-xs text-emerald-700 font-bold mt-1"><i class="fa fa-check-circle mr-1"></i> Cobertura Vigente 2026</p>
        <p class="text-[11px] text-slate-500 mt-0.5">Alergias: ${esc(data.alergias_condiciones)}</p>
      </div>

      <!-- Tarjeta 3: Socioeconómica y Vivienda -->
      <div class="bg-white border border-slate-200 rounded p-4 shadow-2xs">
        <span class="text-slate-400 block text-[10px] font-bold uppercase flex items-center gap-1">
          <i class="fa fa-house text-amber-500"></i> Ficha Socioeconómica
        </span>
        <div class="font-bold text-slate-800 text-sm mt-1.5">Vivienda: ${esc(data.condicion_vivienda)}</div>
        <p class="text-xs text-slate-600 mt-1">${esc(data.ocupacion_padres)}</p>
        <p class="text-[11px] text-slate-400 mt-0.5">${esc(data.direccion_actual)}</p>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <h4 class="text-xs font-bold text-slate-700 uppercase mb-3">Servicios Disponibles de Bienestar Universitario</h4>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div class="border border-slate-200 rounded p-3 bg-slate-50/50">
          <strong class="text-slate-800 text-xs block mb-1 flex items-center gap-1.5">
            <i class="fa fa-user-doctor text-sky-600"></i> Tópico de Atención Médica
          </strong>
          <div class="text-[11px] text-slate-600"><i class="fa fa-clock mr-1 text-slate-400"></i>Lunes a Viernes 08:00 - 18:00</div>
          <div class="text-[11px] text-slate-600 mt-1"><i class="fa fa-map-pin mr-1 text-slate-400"></i>Pabellón B - 1er Piso</div>
        </div>
        <div class="border border-slate-200 rounded p-3 bg-slate-50/50">
          <strong class="text-slate-800 text-xs block mb-1 flex items-center gap-1.5">
            <i class="fa fa-brain text-purple-600"></i> Orientación Psicológica
          </strong>
          <div class="text-[11px] text-slate-600"><i class="fa fa-clock mr-1 text-slate-400"></i>Lunes a Viernes 09:00 - 16:00</div>
          <div class="text-[11px] text-slate-600 mt-1"><i class="fa fa-map-pin mr-1 text-slate-400"></i>Edificio Central - Of. 204</div>
        </div>
        <div class="border border-slate-200 rounded p-3 bg-slate-50/50">
          <strong class="text-slate-800 text-xs block mb-1 flex items-center gap-1.5">
            <i class="fa fa-futbol text-emerald-600"></i> Talleres Deportivos y Culturales
          </strong>
          <div class="text-[11px] text-slate-600"><i class="fa fa-clock mr-1 text-slate-400"></i>Sábados 09:00 - 14:00</div>
          <div class="text-[11px] text-slate-600 mt-1"><i class="fa fa-map-pin mr-1 text-slate-400"></i>Polideportivo Universitario</div>
        </div>
      </div>
    </div>
  `;
}

async function renderBienestarActualizarView(container) {
  const data = await api('/estudiante/bienestar');
  cacheBienestar = data;

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: BIENESTAR UNIVERSITARIO - ACTUALIZAR FICHA INTEGRAL
      </h2>
      <button onclick="cargarModulo('bienestar-ficha')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
        <i class="fa fa-arrow-left"></i> Volver a Mi Ficha
      </button>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-6 shadow-2xs max-w-2xl">
      <div id="bienestarPanelAlert" class="hidden mb-4 p-3 rounded text-xs"></div>

      <form onsubmit="handleBienestarPanelSubmit(event)" class="space-y-4 text-xs">
        <div class="font-bold text-slate-700 uppercase text-[11px] border-b pb-1">Contacto de Emergencia</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-slate-600 mb-1">Nombre Completo:</label>
            <input id="panBienContacto" type="text" required value="${esc(data.contacto_emergencia)}" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
          <div>
            <label class="block text-slate-600 mb-1">Parentesco:</label>
            <input id="panBienParentesco" type="text" required value="${esc(data.parentesco_contacto)}" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
          <div class="sm:col-span-2">
            <label class="block text-slate-600 mb-1">Teléfono de Emergencia:</label>
            <input id="panBienTelEmergencia" type="tel" required value="${esc(data.telefono_emergencia)}" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
        </div>

        <div class="font-bold text-slate-700 uppercase text-[11px] border-b pb-1 pt-2">Datos Socioeconómicos y Salud</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-slate-600 mb-1">Condición Vivienda:</label>
            <select id="panBienVivienda" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
              <option value="Propia" ${data.condicion_vivienda === 'Propia' ? 'selected' : ''}>Propia</option>
              <option value="Alquilada" ${data.condicion_vivienda === 'Alquilada' ? 'selected' : ''}>Alquilada</option>
              <option value="Familiar" ${data.condicion_vivienda === 'Familiar' ? 'selected' : ''}>Familiar / Compartida</option>
            </select>
          </div>
          <div>
            <label class="block text-slate-600 mb-1">Seguro Médico:</label>
            <select id="panBienSeguro" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
              <option value="Seguro Estudiantil" ${data.seguro_salud === 'Seguro Estudiantil' ? 'selected' : ''}>Seguro Estudiantil Universitario</option>
              <option value="EsSalud" ${data.seguro_salud === 'EsSalud' ? 'selected' : ''}>EsSalud</option>
              <option value="SIS" ${data.seguro_salud === 'SIS' ? 'selected' : ''}>SIS (Seguro Integral de Salud)</option>
              <option value="Privado (EPS)" ${data.seguro_salud === 'Privado (EPS)' ? 'selected' : ''}>EPS / Privado</option>
            </select>
          </div>
          <div class="sm:col-span-2">
            <label class="block text-slate-600 mb-1">Alergias o Condiciones Médicas:</label>
            <input id="panBienAlergias" type="text" value="${esc(data.alergias_condiciones)}" placeholder="Ninguna o especificar..." class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
        </div>

        <div class="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
          <button type="button" onclick="cargarModulo('bienestar-ficha')" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2 rounded cursor-pointer">
            Cancelar
          </button>
          <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-5 py-2 rounded cursor-pointer flex items-center gap-1.5">
            <i class="fa fa-save"></i> Guardar Ficha
          </button>
        </div>
      </form>
    </div>
  `;
}

async function handleBienestarPanelSubmit(e) {
  e.preventDefault();
  const alertBox = document.getElementById('bienestarPanelAlert');
  const payload = {
    contacto_emergencia: document.getElementById('panBienContacto').value,
    parentesco_contacto: document.getElementById('panBienParentesco').value,
    telefono_emergencia: document.getElementById('panBienTelEmergencia').value,
    condicion_vivienda: document.getElementById('panBienVivienda').value,
    seguro_salud: document.getElementById('panBienSeguro').value,
    alergias_condiciones: document.getElementById('panBienAlergias').value
  };

  try {
    await api('/estudiante/bienestar', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    alertBox.className = 'block p-3 rounded bg-emerald-100 text-emerald-800 font-medium mb-4';
    alertBox.textContent = 'Ficha de bienestar actualizada correctamente en el sistema.';
    setTimeout(() => {
      cargarModulo('bienestar-ficha');
    }, 1200);
  } catch (err) {
    alertBox.className = 'block p-3 rounded bg-rose-100 text-rose-800 font-medium mb-4';
    alertBox.textContent = 'Error al actualizar ficha: ' + err.message;
  }
}

// =========================================================================
// 7. EXAMEN RECUPERACIÓN: SOLICITAR, MIS SOLICITUDES
// =========================================================================

async function renderRecuperacionSolicitarView(container) {
  const data = await api('/estudiante/recuperacion');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: EXAMEN RECUPERACIÓN - SOLICITAR EVALUACIÓN (PERIODO ${esc(data.periodo)})
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('recuperacion-mis')" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-3 py-1 rounded cursor-pointer">
          <i class="fa fa-list mr-1"></i> Mis Solicitudes
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 mb-4 shadow-2xs">
      <div class="border-b border-slate-100 pb-3 mb-3">
        <h4 class="text-xs font-bold text-slate-800 uppercase flex items-center gap-1.5 mb-1">
          <i class="fa fa-scale-balanced text-amber-500"></i> Normativa Académica de Exámenes de Recuperación
        </h4>
        <p class="text-xs text-slate-600 leading-relaxed">${esc(data.requisitos)}</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3 text-center">Nota Actual</th>
              <th class="py-2.5 px-3 text-center">Fecha Examen</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.cursos.map(c => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(c.codigo)}</td>
                <td class="py-2.5 px-3 uppercase font-medium text-slate-800">${esc(c.curso)}</td>
                <td class="py-2.5 px-3 text-center font-bold ${c.nota >= 10.5 ? 'text-blue-600' : 'text-red-600'}">
                  ${c.nota !== null ? Number(c.nota).toFixed(2) : '--'}
                </td>
                <td class="py-2.5 px-3 text-center text-slate-500">${esc(c.fecha)}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${c.estado === 'DISPONIBLE' ? 'bg-sky-100 text-sky-800' : 'bg-emerald-100 text-emerald-800'}">
                    ${esc(c.estado)}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-right">
                  ${c.puede_solicitar ? `
                    <button onclick="abrirRecuperacionModal(${c.matricula_id}, ${JSON.stringify(c.curso)})" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-[11px] px-2.5 py-1 rounded cursor-pointer font-medium">
                      Solicitar Examen
                    </button>
                  ` : `
                    <span class="text-[11px] text-emerald-700 font-bold"><i class="fa fa-check mr-1"></i>Registrado</span>
                  `}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderRecuperacionMisView(container) {
  const data = await api('/estudiante/recuperacion');
  const mis = data.mis_solicitudes || [];

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: EXAMEN RECUPERACIÓN - MIS SOLICITUDES REGISTRADAS
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('recuperacion-solicitar')" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs px-3 py-1 rounded cursor-pointer font-bold">
          <i class="fa fa-plus mr-1"></i> Nueva Solicitud
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3">Motivo / Sustento</th>
              <th class="py-2.5 px-3 text-center">Fecha Examen</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${mis.length === 0 ? `
              <tr><td colspan="5" class="py-8 text-center text-slate-400">No cuenta con solicitudes de examen de recuperación registradas.</td></tr>
            ` : mis.map(s => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-700">${esc(s.codigo)}</td>
                <td class="py-2.5 px-3 uppercase font-medium text-slate-800">${esc(s.curso)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(s.motivo)}</td>
                <td class="py-2.5 px-3 text-center text-slate-500">${esc(s.fecha)}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${s.estado === 'APROBADO' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                    ${esc(s.estado)}
                  </span>
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
// 8. EXAMEN REPROGRAMACIÓN: SOLICITAR, MIS SOLICITUDES
// =========================================================================

async function renderReprogramacionSolicitarView(container) {
  const data = await api('/estudiante/reprogramacion');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: EXAMEN REPROGRAMACIÓN - SOLICITAR REPROGRAMACIÓN DE EVALUACIONES
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('reprogramacion-mis')" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-3 py-1 rounded cursor-pointer">
          <i class="fa fa-list mr-1"></i> Mis Solicitudes
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 mb-4 shadow-2xs">
      <div class="border-b border-slate-100 pb-3 mb-3">
        <h4 class="text-xs font-bold text-slate-800 uppercase flex items-center gap-1.5 mb-1">
          <i class="fa fa-file-medical text-sky-500"></i> Normativa Oficial de Reprogramación de Evaluaciones
        </h4>
        <p class="text-xs text-slate-600 leading-relaxed">${esc(data.normativa)}</p>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3">Evaluación</th>
              <th class="py-2.5 px-3 text-center">Fecha Original</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
              <th class="py-2.5 px-3 text-right">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${data.evaluaciones.map(ev => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-semibold text-slate-800 uppercase">${esc(ev.curso)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(ev.evaluacion)}</td>
                <td class="py-2.5 px-3 text-center text-slate-500">${esc(ev.fecha_original)}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${ev.estado === 'HABILITADO' ? 'bg-sky-100 text-sky-800' : 'bg-amber-100 text-amber-800'}">
                    ${esc(ev.estado)}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-right">
                  ${ev.puede_solicitar ? `
                    <button onclick="abrirReprogramacionModal(${ev.evaluacion_id}, ${ev.matricula_id}, ${JSON.stringify(ev.curso)}, ${JSON.stringify(ev.evaluacion)})" class="bg-slate-700 hover:bg-slate-800 text-white text-[11px] px-2.5 py-1 rounded cursor-pointer font-medium">
                      Reprogramar
                    </button>
                  ` : `
                    <span class="text-[11px] text-amber-700 font-bold"><i class="fa fa-clock mr-1"></i>En Trámite</span>
                  `}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderReprogramacionMisView(container) {
  const data = await api('/estudiante/reprogramacion');
  const mis = data.mis_solicitudes || [];

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: EXAMEN REPROGRAMACIÓN - MIS SOLICITUDES REGISTRADAS
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('reprogramacion-solicitar')" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs px-3 py-1 rounded cursor-pointer font-bold">
          <i class="fa fa-plus mr-1"></i> Solicitar Reprogramación
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
            <tr>
              <th class="py-2.5 px-3">Asignatura</th>
              <th class="py-2.5 px-3">Evaluación</th>
              <th class="py-2.5 px-3 text-center">Fecha Solicitada</th>
              <th class="py-2.5 px-3">Motivo / Justificación</th>
              <th class="py-2.5 px-3 text-center">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            ${mis.length === 0 ? `
              <tr><td colspan="5" class="py-8 text-center text-slate-400">No registra solicitudes de reprogramación.</td></tr>
            ` : mis.map(s => `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 uppercase font-medium text-slate-800">${esc(s.curso)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(s.evaluacion)}</td>
                <td class="py-2.5 px-3 text-center text-slate-500">${esc(s.fecha)}</td>
                <td class="py-2.5 px-3 text-slate-600">${esc(s.motivo)}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${s.estado === 'APROBADO' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                    ${esc(s.estado)}
                  </span>
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
// 9. BOLSA LABORAL: OFERTAS, MIS POSTULACIONES
// =========================================================================

async function renderBolsaOfertasView(container) {
  const data = await api('/bolsa-laboral');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: BOLSA LABORAL - OFERTAS LABORALES Y PRÁCTICAS PRE-PROFESIONALES
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('bolsa-postulaciones')" class="bg-slate-800 hover:bg-slate-900 text-white text-xs px-3 py-1 rounded cursor-pointer font-medium">
          <i class="fa fa-user-check mr-1"></i> Mis Postulaciones
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="space-y-3">
      ${data.ofertas.map(o => `
        <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs hover:border-slate-300 transition-colors">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2.5 mb-2.5">
            <div>
              <h4 class="text-sm font-bold text-slate-800">${esc(o.puesto)}</h4>
              <div class="text-xs text-[#f4511e] font-semibold mt-0.5">
                <i class="fa fa-building mr-1"></i>${esc(o.empresa)} - <span class="text-slate-500 font-normal">${esc(o.ubicacion)}</span>
              </div>
            </div>
            <div class="text-left sm:text-right">
              <span class="text-xs font-bold text-emerald-700 block">${esc(o.remuneracion)}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">${esc(o.modalidad)}</span>
            </div>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed mb-3">${esc(o.descripcion)}</p>
          <div class="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
            <span class="text-slate-400 text-[11px]"><i class="fa fa-calendar-xmark mr-1"></i>Límite: ${esc(o.fecha_limite)}</span>
            <div class="flex items-center gap-2">
              <button onclick="abrirEmpleoModal(${JSON.stringify(o).replace(/"/g, '&quot;')})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded cursor-pointer font-medium">
                Ver Requisitos
              </button>
              ${o.ya_postulo ? `
                <span class="bg-emerald-100 text-emerald-800 font-bold px-3 py-1.5 rounded text-xs">
                  <i class="fa fa-check mr-1"></i> Ya Postulaste
                </span>
              ` : `
                <button onclick="postularEmpleo(${o.id}, ${JSON.stringify(o.puesto)})" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs px-3.5 py-1.5 rounded cursor-pointer font-medium">
                  Postular a esta vacante
                </button>
              `}
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

async function renderBolsaPostulacionesView(container) {
  const postulaciones = await api('/estudiante/postulaciones');

  container.innerHTML = `
    <div class="bg-[#f9e8e8] border border-rose-200/70 rounded-sm px-3.5 py-2 mb-4 flex items-center justify-between">
      <h2 class="text-xs sm:text-[13px] font-bold text-[#8b1e2f] tracking-wide uppercase">
        .: BOLSA LABORAL - MIS POSTULACIONES LABORALES REGISTRADAS
      </h2>
      <div class="flex items-center gap-2">
        <button onclick="cargarModulo('bolsa-ofertas')" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs px-3 py-1 rounded cursor-pointer font-bold">
          <i class="fa fa-briefcase mr-1"></i> Explorar Ofertas
        </button>
        <button onclick="cargarModulo('notas')" class="text-xs text-[#8b1e2f] hover:underline font-semibold flex items-center gap-1 cursor-pointer">
          <i class="fa fa-arrow-left"></i> Volver a Notas
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200/70 rounded-sm p-4 shadow-2xs">
      ${postulaciones.length === 0 ? `
        <p class="text-xs text-slate-400 py-8 text-center">Aún no has registrado postulaciones a convocatorias laborales.</p>
      ` : `
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse text-xs">
            <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th class="py-2.5 px-3">Puesto / Vacante</th>
                <th class="py-2.5 px-3">Empresa</th>
                <th class="py-2.5 px-3 text-center">Fecha de Postulación</th>
                <th class="py-2.5 px-3 text-center">Estado del Proceso</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${postulaciones.map(p => `
                <tr class="hover:bg-slate-50">
                  <td class="py-2.5 px-3 font-semibold text-slate-800">${esc(p.puesto)}</td>
                  <td class="py-2.5 px-3 text-slate-600">${esc(p.empresa)}</td>
                  <td class="py-2.5 px-3 text-center text-slate-500">${esc(p.fecha)}</td>
                  <td class="py-2.5 px-3 text-center">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                      ${esc(p.estado)}
                    </span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `}
    </div>
  `;
}

// =========================================================================
// PDF DOWNLOADS & MODALS HANDLERS
// =========================================================================

async function descargarBoletaSimple() {
  const select = document.getElementById('periodoSelect');
  const periodoId = select ? select.value : '';
  const url = `${window.API_URL}/estudiante/me/boleta${periodoId ? '?periodo_id=' + periodoId : ''}`;
  try {
    const res = await fetch(url, {
      headers: { 'Authorization': 'Bearer ' + window.API_TOKEN }
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const fileUrl = URL.createObjectURL(blob);
    window.open(fileUrl, '_blank');
  } catch (err) {
    alert('Error al generar la Boleta de Notas: ' + err.message);
  }
}

async function descargarBoletaDetallada() {
  const select = document.getElementById('periodoSelect');
  const periodoId = select ? select.value : '';
  const url = `${window.API_URL}/estudiante/me/boleta-detallada${periodoId ? '?periodo_id=' + periodoId : ''}`;
  try {
    const res = await fetch(url, {
      headers: { 'Authorization': 'Bearer ' + window.API_TOKEN }
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const fileUrl = URL.createObjectURL(blob);
    window.open(fileUrl, '_blank');
  } catch (err) {
    alert('Error al generar la Boleta Detallada: ' + err.message);
  }
}

async function descargarRecordPdf() {
  try {
    const res = await fetch(`${window.API_URL}/estudiante/record-academico/pdf`, {
      headers: { 'Authorization': 'Bearer ' + window.API_TOKEN }
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const fileUrl = URL.createObjectURL(blob);
    window.open(fileUrl, '_blank');
  } catch (err) {
    alert('Error al generar el Récord Académico: ' + err.message);
  }
}

// MODAL DE PERFIL
function openProfileModal() {
  const ud = document.getElementById('userDropdown');
  if (ud) ud.classList.add('hidden');
  const pm = document.getElementById('profileModal');
  if (pm) pm.classList.remove('hidden');
}
function closeProfileModal() {
  const pm = document.getElementById('profileModal');
  if (pm) pm.classList.add('hidden');
}

// MODAL DE EDITAR CONTACTO
function openEditProfileModal() {
  const ud = document.getElementById('userDropdown');
  if (ud) ud.classList.add('hidden');
  const al = document.getElementById('editProfileAlert');
  if (al) al.className = 'hidden';
  const em = document.getElementById('editProfileModal');
  if (em) em.classList.remove('hidden');
}
function closeEditProfileModal() {
  const em = document.getElementById('editProfileModal');
  if (em) em.classList.add('hidden');
}

async function handleProfileUpdate(e) {
  e.preventDefault();
  const tel = document.getElementById('editTelefono').value;
  const dir = document.getElementById('editDireccion').value;
  const alertBox = document.getElementById('editProfileAlert');

  try {
    await api('/estudiante/perfil', {
      method: 'PUT',
      body: JSON.stringify({ telefono: tel, direccion: dir })
    });
    alertBox.className = 'block p-2 rounded bg-emerald-100 text-emerald-700 font-medium';
    alertBox.textContent = 'Datos de contacto actualizados correctamente.';
    await cargarPerfilEstudiante();
    setTimeout(() => {
      closeEditProfileModal();
      if (moduloActual === 'personal' || moduloActual === 'personal-perfil') cargarModulo('personal-perfil');
    }, 1200);
  } catch (err) {
    alertBox.className = 'block p-2 rounded bg-rose-100 text-rose-700 font-medium';
    alertBox.textContent = err.message;
  }
}

// MODAL CAMBIAR CONTRASEÑA
function openPasswordModal() {
  const ud = document.getElementById('userDropdown');
  if (ud) ud.classList.add('hidden');
  const f = document.getElementById('changePasswordForm');
  if (f) f.reset();
  const al = document.getElementById('passwordAlert');
  if (al) al.className = 'hidden';
  const pm = document.getElementById('passwordModal');
  if (pm) pm.classList.remove('hidden');
}
function closePasswordModal() {
  const pm = document.getElementById('passwordModal');
  if (pm) pm.classList.add('hidden');
}

async function handlePasswordChange(e) {
  e.preventDefault();
  const pAct = document.getElementById('pwdActual').value;
  const pNew = document.getElementById('pwdNueva').value;
  const pConf = document.getElementById('pwdConfirmar').value;
  const alertBox = document.getElementById('passwordAlert');

  if (pNew !== pConf) {
    alertBox.className = 'block p-2 rounded bg-rose-100 text-rose-700 font-medium';
    alertBox.textContent = 'Las contraseñas no coinciden.';
    return;
  }

  try {
    await api('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ password_actual: pAct, password_nueva: pNew })
    });
    alertBox.className = 'block p-2 rounded bg-emerald-100 text-emerald-700 font-medium';
    alertBox.textContent = 'Contraseña actualizada correctamente.';
    setTimeout(() => closePasswordModal(), 1500);
  } catch (err) {
    let msg = err.message;
    try { const j = JSON.parse(msg); if (j.detail) msg = j.detail; } catch(e){}
    alertBox.className = 'block p-2 rounded bg-rose-100 text-rose-700 font-medium';
    alertBox.textContent = msg;
  }
}

// MODAL DETALLE DE CURSO DE MATRÍCULA
function abrirCursoDetalle(c) {
  const b = document.getElementById('cursoDetalleBody');
  b.innerHTML = `
    <div class="space-y-2">
      <div><strong class="text-slate-500 block text-[10px] uppercase">Código y Asignatura:</strong> <span class="font-bold text-slate-800 text-sm">${esc(c.codigo)} - ${esc(c.curso)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Docente a Cargo:</strong> <span class="font-semibold text-slate-800">${esc(c.docente)}</span></div>
      <div class="grid grid-cols-2 gap-2">
        <div><strong class="text-slate-500 block text-[10px] uppercase">Sección:</strong> <span class="font-bold text-slate-700">${esc(c.seccion)}</span></div>
        <div><strong class="text-slate-500 block text-[10px] uppercase">Créditos:</strong> <span class="font-bold text-slate-700">${c.creditos} CR</span></div>
      </div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Horario Semanal:</strong> <span class="font-semibold text-sky-700">${esc(c.horario)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Aula Asignada:</strong> <span class="font-bold text-slate-800">${esc(c.aula)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Modalidad:</strong> <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">${esc(c.modalidad)}</span></div>
    </div>
  `;
  document.getElementById('cursoDetalleModal').classList.remove('hidden');
}
function closeCursoDetalleModal() {
  document.getElementById('cursoDetalleModal').classList.add('hidden');
}

// MODAL MALLA CURRICULAR
function abrirMallaCurso(cur) {
  const b = document.getElementById('mallaModalBody');
  b.innerHTML = `
    <div class="space-y-2.5 leading-relaxed">
      <div><strong class="text-slate-500 block text-[10px] uppercase">Asignatura:</strong> <span class="font-bold text-slate-800 text-sm">${esc(cur.nombre)}</span></div>
      <div class="grid grid-cols-2 gap-2">
        <div><strong class="text-slate-500 block text-[10px] uppercase">Código:</strong> <span class="font-bold text-slate-700">${esc(cur.codigo)}</span></div>
        <div><strong class="text-slate-500 block text-[10px] uppercase">Ciclo Curricular:</strong> <span class="font-bold text-slate-700">Ciclo ${cur.ciclo}</span></div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div><strong class="text-slate-500 block text-[10px] uppercase">Créditos:</strong> <span class="font-bold text-slate-700">${cur.creditos} CR</span></div>
        <div><strong class="text-slate-500 block text-[10px] uppercase">Prerrequisito:</strong> <span class="font-semibold text-slate-700">${esc(cur.prereq)}</span></div>
      </div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Estado Actual:</strong> <span class="font-bold text-emerald-700">${esc(cur.estado === 'VERDE' ? 'APROBADO (Nota: ' + cur.nota + ')' : (cur.estado === 'AMARILLO' ? 'CURSANDO EN PERIODO ACTUAL' : 'PENDIENTE DE MATRÍCULA'))}</span></div>
    </div>
  `;
  document.getElementById('mallaModal').classList.remove('hidden');
}
function closeMallaModal() {
  document.getElementById('mallaModal').classList.add('hidden');
}

// MODAL ENCUESTAS
function abrirEncuestaModal(seccionId, curso, docente) {
  document.getElementById('encuestaSeccionId').value = seccionId;
  document.getElementById('encuestaCursoNom').textContent = curso;
  document.getElementById('encuestaDocenteNom').textContent = docente;
  document.getElementById('encuestaComentarios').value = '';
  document.getElementById('encuestaModal').classList.remove('hidden');
}
function closeEncuestaModal() {
  document.getElementById('encuestaModal').classList.add('hidden');
}

async function handleEncuestaSubmit(e) {
  e.preventDefault();
  const secId = document.getElementById('encuestaSeccionId').value;
  const puntaje = parseInt(document.getElementById('encuestaPuntaje').value);
  const com = document.getElementById('encuestaComentarios').value;

  try {
    await api(`/estudiante/encuestas/${secId}/responder`, {
      method: 'POST',
      body: JSON.stringify({ calificacion: puntaje, comentarios: com })
    });
    alert('Evaluación docente registrada con éxito. ¡Gracias por su participación!');
    closeEncuestaModal();
    await cargarModulo('encuestas');
  } catch (err) {
    alert('Error al enviar evaluación: ' + err.message);
  }
}

// MODALES TRÁMITES
function abrirTramiteDetalle(t) {
  const b = document.getElementById('tramiteModalBody');
  b.innerHTML = `
    <div class="space-y-2.5">
      <div class="flex items-center justify-between pb-2 border-b">
        <div>
          <span class="text-slate-400 block text-[10px] font-bold uppercase">Código de Seguimiento</span>
          <strong class="text-slate-800 text-sm">${esc(t.codigo)}</strong>
        </div>
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">${esc(t.estado)}</span>
      </div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Tipo de Trámite:</strong> <span class="font-bold text-slate-800">${esc(t.tipo)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Motivo / Asunto:</strong> <span class="font-semibold text-slate-700">${esc(t.motivo)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Descripción del Alumno:</strong> <p class="text-slate-600 bg-slate-50 p-2 rounded">${esc(t.descripcion)}</p></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Fecha de Solicitud:</strong> <span class="text-slate-700">${esc(t.fecha_solicitud)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Respuesta de Secretaría Académica:</strong> <p class="text-slate-700 font-medium bg-sky-50 p-2 rounded border border-sky-100">${esc(t.respuesta || 'Su trámite se encuentra en proceso de revisión reglamentaria.')}</p></div>
    </div>
  `;
  document.getElementById('tramiteModal').classList.remove('hidden');
}
function closeTramiteModal() {
  document.getElementById('tramiteModal').classList.add('hidden');
}

function openNuevoTramiteModal() {
  document.getElementById('nuevoTramiteForm').reset();
  document.getElementById('nuevoTramiteModal').classList.remove('hidden');
}
function closeNuevoTramiteModal() {
  document.getElementById('nuevoTramiteModal').classList.add('hidden');
}

async function handleNuevoTramiteSubmit(e) {
  e.preventDefault();
  const tipo = document.getElementById('trmTipo').value;
  const motivo = document.getElementById('trmMotivo').value;
  const desc = document.getElementById('trmDescripcion').value;

  try {
    const res = await api('/estudiante/tramites', {
      method: 'POST',
      body: JSON.stringify({ tipo: tipo, motivo: motivo, descripcion: desc })
    });
    alert(`Solicitud registrada exitosamente con código: ${res.codigo}`);
    closeNuevoTramiteModal();
    await cargarModulo('tramites-mis');
  } catch (err) {
    alert('Error al registrar trámite: ' + err.message);
  }
}

// MODALES RECUPERACIÓN Y REPROGRAMACIÓN
function abrirRecuperacionModal(matriculaId, cursoNom) {
  document.getElementById('recupMatriculaId').value = matriculaId;
  document.getElementById('recupCursoNom').textContent = cursoNom;
  document.getElementById('recupMotivo').value = '';
  document.getElementById('recuperacionModal').classList.remove('hidden');
}
function closeRecuperacionModal() {
  document.getElementById('recuperacionModal').classList.add('hidden');
}

async function handleRecuperacionSubmit(e) {
  e.preventDefault();
  const mId = parseInt(document.getElementById('recupMatriculaId').value);
  const mot = document.getElementById('recupMotivo').value;

  try {
    await api('/estudiante/recuperacion', {
      method: 'POST',
      body: JSON.stringify({ matricula_id: mId, motivo: mot })
    });
    alert('Solicitud de examen de recuperación registrada correctamente.');
    closeRecuperacionModal();
    await cargarModulo('recuperacion-mis');
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

function abrirReprogramacionModal(evalId, matId, cursoNom, evalNom) {
  document.getElementById('reprogEvaluacionId').value = evalId;
  document.getElementById('reprogMatriculaId').value = matId;
  document.getElementById('reprogCursoNom').textContent = cursoNom;
  document.getElementById('reprogEvalNom').textContent = evalNom;
  document.getElementById('reprogSustento').value = '';
  document.getElementById('reprogramacionModal').classList.remove('hidden');
}
function closeReprogramacionModal() {
  document.getElementById('reprogramacionModal').classList.add('hidden');
}

async function handleReprogramacionSubmit(e) {
  e.preventDefault();
  const payload = {
    evaluacion_id: parseInt(document.getElementById('reprogEvaluacionId').value),
    matricula_id: parseInt(document.getElementById('reprogMatriculaId').value),
    motivo: document.getElementById('reprogMotivo').value,
    fecha_solicitada: document.getElementById('reprogFecha').value,
    sustento: document.getElementById('reprogSustento').value
  };

  try {
    await api('/estudiante/reprogramacion', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    alert('Solicitud de reprogramación de examen enviada exitosamente.');
    closeReprogramacionModal();
    await cargarModulo('reprogramacion-mis');
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

// MODAL BOLSA LABORAL Y POSTULACIÓN
function abrirEmpleoModal(o) {
  const b = document.getElementById('empleoModalBody');
  b.innerHTML = `
    <div class="space-y-3">
      <div>
        <span class="text-xs text-[#f4511e] font-bold block">${esc(o.empresa)}</span>
        <h4 class="text-base font-bold text-slate-800 uppercase">${esc(o.puesto)}</h4>
        <div class="text-xs text-slate-500">${esc(o.ubicacion)} - <span class="font-semibold text-slate-700">${esc(o.modalidad)}</span></div>
      </div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Remuneración / Subvención:</strong> <span class="font-bold text-emerald-700 text-sm">${esc(o.remuneracion)}</span></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Descripción del Puesto:</strong> <p class="text-slate-600 leading-relaxed">${esc(o.descripcion)}</p></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Requisitos Solicitados:</strong> <p class="text-slate-600 bg-slate-50 p-2.5 rounded">${esc(o.requisitos)}</p></div>
      <div><strong class="text-slate-500 block text-[10px] uppercase">Funciones Principales:</strong> <p class="text-slate-600 leading-relaxed">${esc(o.funciones)}</p></div>
    </div>
  `;
  document.getElementById('empleoModal').classList.remove('hidden');
}
function closeEmpleoModal() {
  document.getElementById('empleoModal').classList.add('hidden');
}

async function postularEmpleo(empleoId, puesto) {
  if (!confirm(`¿Confirmas enviar tu postulación para la vacante: "${puesto}"?`)) return;

  try {
    const res = await api(`/bolsa-laboral/${empleoId}/postular`, {
      method: 'POST'
    });
    alert(res.message || 'Postulación enviada exitosamente.');
    await cargarModulo('bolsa-postulaciones');
  } catch (err) {
    let msg = err.message;
    try { const j = JSON.parse(msg); if (j.detail) msg = j.detail; } catch(e){}
    alert(msg);
  }
}

// MODAL DE AYUDA
function openAyudaModal() {
  alert("SISTEMA DE GESTIÓN ACADÉMICA UNIVERSITARIA\\n\\n• Horario de Soporte: Lunes a Viernes 08:00 - 18:00\\n• Correo Electrónico: soporte@portal.edu.pe\\n• Teléfono de Mesa de Ayuda: (01) 614-7800 Anexo 2100\\n\\nVersión del Sistema: 3.2 (Actualizada 2026)");
}
