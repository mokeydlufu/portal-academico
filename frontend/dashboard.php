<?php
session_start();
require __DIR__ . '/config.php';

// Verificación estricta de autenticación y rol de Administrador
if (!isset($_SESSION['token'])) {
    header('Location: /login.php');
    exit;
}

if (!in_array($_SESSION['rol'] ?? '', ['ADMIN', 'ADMINISTRADOR'])) {
    if (($_SESSION['rol'] ?? '') === 'ESTUDIANTE') {
        header('Location: /notas.php');
        exit;
    }
    header('Location: /login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Intranet Académica - Panel del Administrador</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- FontAwesome CDN -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
  <!-- SweetAlert2 CDN -->
  <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .custom-scrollbar::-webkit-scrollbar {
      width: 5px;
      height: 5px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background-color: #cbd5e1;
      border-radius: 4px;
    }
    .nav-item-active {
      color: #f43f5e !important;
      font-weight: 600 !important;
      background-color: rgba(15, 23, 42, 0.5) !important;
      border-left: 3px solid #f43f5e;
    }
    .accordion-submenu {
      max-height: 0;
      opacity: 0;
      overflow: hidden;
      transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease;
    }
    .accordion-submenu.open {
      max-height: 500px;
      opacity: 1;
    }
    .accordion-header {
      transition: background-color 0.2s ease, color 0.2s ease;
    }
  </style>
</head>
<body class="bg-[#f8fafc] text-neutral-800 antialiased min-h-screen flex flex-col">

  <!-- ================= BARRA SUPERIOR (HEADER) ================= -->
  <header class="bg-white border-b border-slate-200 h-14 fixed top-0 left-0 right-0 z-30 flex items-center justify-between px-4 shadow-xs">
    <!-- Lado Izquierdo: Hamburguesa, Identidad y Badges -->
    <div class="flex items-center gap-3">
      <button id="sidebarToggleBtn" type="button" class="text-slate-600 hover:text-slate-900 p-1 rounded hover:bg-slate-100 cursor-pointer" title="Alternar menú">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>

      <!-- Badge "UN" + Título ADMINISTRADOR -->
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded bg-slate-900 flex items-center justify-center text-white text-xs font-black tracking-tighter">
          UN
        </div>
        <span class="text-[#f4511e] font-black text-base sm:text-lg tracking-wider uppercase select-none">
          ADMINISTRADOR
        </span>
      </div>

      <!-- Iconos de Estado Rápido -->
      <div class="flex items-center gap-2.5 ml-4">
        <!-- Acceso directo a Backups -->
        <div onclick="cargarModuloAdmin('backups-panel')" class="relative cursor-pointer hover:opacity-80" title="Copias de Seguridad">
          <i class="fa fa-database text-purple-600 text-base"></i>
          <span class="absolute -top-1.5 -right-2 bg-purple-600 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center ring-1 ring-white">
            <i class="fa fa-shield-halved text-[8px]"></i>
          </span>
        </div>

        <!-- Estado de Base de Datos -->
        <div onclick="cargarModuloAdmin('dashboard')" class="relative cursor-pointer ml-1 hover:opacity-80" title="Servidor Activo">
          <i class="fa fa-server text-emerald-600 text-base"></i>
          <span class="absolute -top-1.5 -right-2 bg-emerald-500 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center ring-1 ring-white">
            ✓
          </span>
        </div>
      </div>
    </div>

    <!-- Lado Derecho: Botón Ayuda (?) y Perfil del Administrador con Dropdown -->
    <div class="flex items-center gap-3">
      <button type="button" onclick="alert('Portal Académico - Panel de Administración General.\nVersión con Copias de Seguridad Reales de PostgreSQL (pg_dump / pg_restore).')" class="w-7 h-7 rounded-full bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs flex items-center justify-center shadow-xs cursor-pointer" title="Ayuda e Información del Sistema">
        ?
      </button>

      <!-- Perfil con menú desplegable -->
      <div class="relative pl-2 border-l border-slate-200">
        <button id="userMenuBtn" type="button" class="flex items-center gap-2 text-left focus:outline-none cursor-pointer">
          <div class="w-8 h-8 rounded bg-slate-800 overflow-hidden flex items-center justify-center text-white text-xs font-bold">
            <i class="fa fa-user-shield"></i>
          </div>
          <div class="text-right hidden sm:block leading-tight">
            <div class="flex items-center gap-1 justify-end">
              <span class="text-[11px] font-bold text-slate-700 uppercase"><?= htmlspecialchars($_SESSION['nombre'] ?? 'Administrador') ?></span>
              <span class="text-[10px] text-slate-400">▼</span>
            </div>
            <div class="text-[9px] text-[#f4511e] font-semibold uppercase">
              ROL: <?= htmlspecialchars($_SESSION['rol'] ?? 'ADMIN') ?>
            </div>
          </div>
        </button>

        <!-- Dropdown Menu -->
        <div id="userDropdown" class="hidden absolute right-0 mt-2 w-56 bg-white rounded-md shadow-xl border border-slate-200 py-1.5 z-50 text-xs">
          <div class="px-3 py-2 border-b border-slate-100 bg-slate-50">
            <div class="font-bold text-slate-800 text-[11px] uppercase truncate"><?= htmlspecialchars($_SESSION['nombre'] ?? 'Administrador General') ?></div>
            <div class="text-slate-500 text-[10px]"><?= htmlspecialchars($_SESSION['rol'] ?? 'ADMIN') ?> - Acceso Total</div>
          </div>
          <a href="javascript:void(0)" onclick="cargarModuloAdmin('dashboard')" class="px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <i class="fa fa-gauge text-sky-500 w-4 text-center"></i> Panel General
          </a>
          <a href="javascript:void(0)" onclick="cargarModuloAdmin('backups-panel')" class="px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <i class="fa fa-database text-purple-500 w-4 text-center"></i> Copias de Seguridad
          </a>
          <div class="border-t border-slate-100 my-1"></div>
          <a href="/logout.php" class="px-3 py-2 text-rose-600 hover:bg-rose-50 flex items-center gap-2 font-medium">
            <i class="fa fa-sign-out-alt text-rose-500 w-4 text-center"></i> Cerrar Sesión
          </a>
        </div>
      </div>
    </div>
  </header>

  <!-- ================= LAYOUT PRINCIPAL (SIDEBAR + CONTENIDO) ================= -->
  <div class="flex pt-14 min-h-screen">

    <!-- SIDEBAR (MENÚ IZQUIERDO AZUL MARINO OSCURO: bg-[#0f172a]) -->
    <aside id="sidebar" class="w-64 bg-[#0f172a] text-slate-300 flex-shrink-0 fixed top-14 bottom-0 left-0 overflow-y-auto z-20 select-none text-xs custom-scrollbar transition-transform duration-200">
      <div class="p-3 space-y-1">

        <!-- Categoría: MENÚ PRINCIPAL -->
        <div class="px-3 pt-2 pb-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          MENÚ PRINCIPAL
        </div>

        <!-- 1. Inicio / Dashboard -->
        <div id="nav-dashboard" onclick="cargarModuloAdmin('dashboard')" class="px-3 py-2 rounded text-rose-500 font-semibold flex items-center gap-2.5 cursor-pointer bg-slate-900/40 transition-colors">
          <i class="fa fa-home w-4 text-center text-slate-400"></i>
          <span>Inicio</span>
        </div>

        <!-- 2. Estudiantes (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-estudiantes" onclick="toggleAdminAccordion('estudiantes')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-graduation-cap w-4 text-center text-slate-400"></i>
              <span>Estudiantes</span>
            </span>
            <span id="icon-estudiantes" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-estudiantes" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-estudiantes-lista" onclick="cargarModuloAdmin('estudiantes-lista')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Listado General
            </div>
            <div id="nav-estudiantes-nuevo" onclick="cargarModuloAdmin('estudiantes-nuevo')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Registrar Estudiante
            </div>
            <div id="nav-estudiantes-estado" onclick="cargarModuloAdmin('estudiantes-estado')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Estado Académico
            </div>
          </div>
        </div>

        <!-- Categoría: GESTIÓN ACADÉMICA -->
        <div class="px-3 pt-3 pb-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          GESTIÓN ACADÉMICA
        </div>

        <!-- 3. Cursos (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-cursos" onclick="toggleAdminAccordion('cursos')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-book w-4 text-center text-slate-400"></i>
              <span>Cursos</span>
            </span>
            <span id="icon-cursos" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-cursos" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-cursos-lista" onclick="cargarModuloAdmin('cursos-lista')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Catálogo de Cursos
            </div>
            <div id="nav-cursos-nuevo" onclick="cargarModuloAdmin('cursos-nuevo')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Registrar Curso
            </div>
          </div>
        </div>

        <!-- 4. Matrículas (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-matriculas" onclick="toggleAdminAccordion('matriculas')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-clipboard-list w-4 text-center text-slate-400"></i>
              <span>Matrículas</span>
            </span>
            <span id="icon-matriculas" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-matriculas" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-matriculas-lista" onclick="cargarModuloAdmin('matriculas-lista')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Matrículas Activas
            </div>
            <div id="nav-matriculas-nueva" onclick="cargarModuloAdmin('matriculas-nueva')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Registrar Matrícula
            </div>
          </div>
        </div>

        <!-- Categoría: ADMINISTRACIÓN DEL SISTEMA -->
        <div class="px-3 pt-3 pb-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          ADMINISTRACIÓN
        </div>

        <!-- 5. Copias de Seguridad (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-backups" onclick="toggleAdminAccordion('backups')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-database w-4 text-center text-purple-400"></i>
              <span>Copias de Seguridad</span>
            </span>
            <span id="icon-backups" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-backups" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-backups-panel" onclick="cargarModuloAdmin('backups-panel')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Panel de Control
            </div>
            <div id="nav-backups-explorador" onclick="cargarModuloAdmin('backups-explorador')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors flex items-center gap-1.5">
              <i class="fa fa-folder-open text-[9px] text-purple-400"></i> Explorador de Backups
            </div>
            <div id="nav-backups-guardados" onclick="cargarModuloAdmin('backups-guardados')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Copias guardadas
            </div>
            <div id="nav-backups-programacion" onclick="cargarModuloAdmin('backups-programacion')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Programación Automática
            </div>
            <div id="nav-backups-historial" onclick="cargarModuloAdmin('backups-historial')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Historial de Operaciones
            </div>
            <div id="nav-backups-restauraciones" onclick="cargarModuloAdmin('backups-restauraciones')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Restauraciones de Prueba
            </div>
          </div>
        </div>

      </div>
    </aside>

    <!-- ================= CONTENIDO PRINCIPAL DINÁMICO ================= -->
    <main class="ml-0 sm:ml-64 flex-1 bg-[#f8fafc] p-4 lg:p-6 min-h-[calc(100vh-3.5rem)]">
      <!-- CONTENEDOR DINÁMICO DE VISTAS (SPA que preserva la sesión) -->
      <div id="dynamicContentContainer">
        <!-- Renderizado dinámicamente por portal_admin.js -->
      </div>
    </main>
  </div>

  <!-- ================================================================ -->
  <!-- MODALES DEL SISTEMA DE ADMINISTRACIÓN Y BACKUPS                  -->
  <!-- ================================================================ -->

  <!-- MODAL 1: CREAR COPIA DE SEGURIDAD MANUAL -->
  <div id="modalCrearBackup" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-lg shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa fa-database text-purple-400"></i>
          <h3 class="text-sm font-bold uppercase tracking-wide">Nueva Copia de Seguridad</h3>
        </div>
        <button type="button" onclick="cerrarModalCrearBackup()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3">
        <div id="crearBackupAlert" class="hidden"></div>
        <p class="text-slate-600 leading-relaxed">
          Se generará una copia de seguridad oficial y completa de la base de datos PostgreSQL utilizando el formato binario comprimido de <code class="bg-slate-100 px-1 py-0.5 rounded text-purple-700 font-semibold">pg_dump (-F c)</code>.
        </p>
        <div class="bg-slate-50 border border-slate-200 rounded p-3 space-y-1.5 text-[11px]">
          <div class="flex justify-between">
            <span class="text-slate-500">Base de Datos Origen:</span>
            <span class="font-bold text-slate-800">portal_academico</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Tipo de Copia:</span>
            <span class="font-semibold text-purple-700">Manual</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Directorio de Almacenamiento:</span>
            <span class="font-mono text-slate-700 text-[10px]">storage/backups/</span>
          </div>
        </div>

        <div id="crearBackupLoader" class="hidden text-center py-3 text-purple-700 font-medium">
          <i class="fa fa-spinner fa-spin text-2xl mb-1"></i>
          <div>Ejecutando pg_dump y verificando integridad...</div>
        </div>
      </div>
      <div class="bg-slate-100 px-5 py-3 flex justify-end gap-2 border-t border-slate-200">
        <button id="btnCancelarCrear" type="button" onclick="cerrarModalCrearBackup()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs px-3.5 py-1.5 rounded cursor-pointer transition-colors">Cancelar</button>
        <button id="btnConfirmarCrear" type="button" onclick="ejecutarCrearBackupAdmin()" class="bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold px-4 py-1.5 rounded cursor-pointer transition-colors flex items-center gap-1.5 shadow-xs">
          <i class="fa fa-floppy-disk"></i> Generar Backup Ahora
        </button>
      </div>
    </div>
  </div>

  <!-- MODAL 2: DETALLE DE COPIA DE SEGURIDAD -->
  <div id="modalDetalleBackup" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-lg shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa fa-file-circle-info text-sky-400"></i>
          <h3 class="text-sm font-bold uppercase tracking-wide">Ficha Técnica de la Copia</h3>
        </div>
        <button type="button" onclick="cerrarModalDetalleBackup()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3">
        <div class="bg-slate-50 border border-slate-200 rounded p-3 space-y-2 text-[11px]">
          <div><span class="text-slate-500 font-medium">Copia de seguridad:</span> <span id="detFilename" class="font-bold text-slate-800 block text-xs">...</span></div>
          <div><span class="text-slate-500 font-medium">Ruta en Disco:</span> <span id="detPath" class="font-mono text-slate-600 block text-[10px] break-all">...</span></div>
          <div class="grid grid-cols-2 gap-2 pt-1 border-t border-slate-200">
            <div><span class="text-slate-500">Tamaño:</span> <span id="detSize" class="font-semibold text-slate-800 block">...</span></div>
            <div><span class="text-slate-500">Tipo:</span> <span id="detType" class="font-semibold text-purple-700 block">...</span></div>
            <div><span class="text-slate-500">Estado:</span> <span id="detStatus" class="font-bold text-emerald-700 block">...</span></div>
            <div><span class="text-slate-500">Fecha y Hora:</span> <span id="detFecha" class="font-semibold text-slate-800 block">...</span></div>
            <div><span class="text-slate-500">Generado Por:</span> <span id="detUsuario" class="font-semibold text-slate-800 block">...</span></div>
            <div><span class="text-slate-500">Duración pg_dump:</span> <span id="detDuracion" class="font-semibold text-slate-800 block">...</span></div>
          </div>
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-600 mb-1">Informe de Verificación / TOC:</label>
          <div id="detMensaje" class="bg-slate-900 text-slate-200 font-mono text-[10px] p-2.5 rounded h-28 overflow-y-auto custom-scrollbar">...</div>
        </div>
      </div>
      <div class="bg-slate-100 px-5 py-2.5 text-right border-t border-slate-200">
        <button type="button" onclick="cerrarModalDetalleBackup()" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-4 py-1.5 rounded cursor-pointer">Cerrar</button>
      </div>
    </div>
  </div>

  <!-- MODAL 3: RESTAURACIÓN AISLADA DE PRUEBA -->
  <div id="modalRestaurar" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-lg shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa fa-rotate-left text-amber-400"></i>
          <h3 class="text-sm font-bold uppercase tracking-wide">Restaurar Copia en Base de Prueba</h3>
        </div>
        <button type="button" onclick="cerrarModalRestaurarAdmin()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3">
        <div id="restaurarAlert" class="hidden"></div>
        <div class="bg-amber-50 border border-amber-200 rounded p-3 text-amber-800 text-[11px]">
          <i class="fa fa-shield-halved text-amber-600 font-bold"></i>
          <strong>Protección de Base de Producción:</strong>
          Por política estricta de seguridad, el sistema nunca sobrescribe la base productiva principal. La restauración se realiza de forma aislada en una base de datos de prueba para certificar que el dump contiene todas las tablas y datos íntegros.
        </div>

        <input type="hidden" id="restaurarBackupId">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Copia utilizada:</label>
          <input type="text" id="restaurarFilename" readonly class="w-full bg-slate-100 border border-slate-300 rounded px-3 py-1.5 font-mono text-[11px] text-slate-800">
        </div>

        <div>
          <label class="block font-semibold text-slate-700 mb-1">Base restaurada de prueba:</label>
          <input type="text" id="restaurarTargetDb" value="portal_academico_restaurado_prueba" class="w-full border border-slate-300 rounded px-3 py-1.5 font-mono text-xs focus:outline-none focus:border-amber-500">
          <span class="text-[10px] text-slate-500 mt-0.5 block">Solo letras minúsculas, números y guiones bajos (ej: portal_academico_restaurado_prueba).</span>
        </div>

        <div id="restaurarLoader" class="hidden text-center py-3 text-amber-700 font-medium">
          <i class="fa fa-spinner fa-spin text-2xl mb-1"></i>
          <div>Creando base de prueba y ejecutando pg_restore...</div>
        </div>
      </div>
      <div class="bg-slate-100 px-5 py-3 flex justify-end gap-2 border-t border-slate-200">
        <button id="btnCancelarRestaurar" type="button" onclick="cerrarModalRestaurarAdmin()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs px-3.5 py-1.5 rounded cursor-pointer transition-colors">Cancelar</button>
        <button id="btnConfirmarRestaurar" type="button" onclick="ejecutarRestaurarBackupAdmin()" class="bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold px-4 py-1.5 rounded cursor-pointer transition-colors flex items-center gap-1.5 shadow-xs">
          <i class="fa fa-play"></i> Ejecutar Restauración de Prueba
        </button>
      </div>
    </div>
  </div>

  <!-- MODAL 4: PROGRAMACIÓN AUTOMÁTICA DE BACKUP -->
  <div id="modalProgramacion" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-lg shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 id="modalProgTitulo" class="text-sm font-bold uppercase tracking-wide flex items-center gap-2">
          <i class="fa fa-clock text-amber-500"></i> Programar Copia Automática
        </h3>
        <button type="button" onclick="cerrarModalProgramacionAdmin()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="formProgramacion" onsubmit="guardarProgramacionAdmin(event)" class="p-5 text-xs space-y-3">
        <input type="hidden" id="progId">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Nombre Descriptivo de la Tarea:</label>
          <input type="text" id="progNombre" required placeholder="Ej: Copia Diaria Nocturna" class="w-full border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:border-purple-500">
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Frecuencia:</label>
            <select id="progFrecuencia" onchange="toggleFrecuenciaAdmin()" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-purple-500 font-medium">
              <option value="DIARIA">Diaria (Hora fija HH:MM:SS)</option>
              <option value="SEMANAL">Semanal (Día y hora fija)</option>
              <option value="INTERVALO_HORAS">Cada N horas</option>
              <option value="INTERVALO_MINUTOS">Cada N minutos</option>
              <option value="INTERVALO_SEGUNDOS">Cada N segundos (Pruebas)</option>
            </select>
          </div>
          <div id="groupHora">
            <label class="block font-semibold text-slate-700 mb-1">Hora (HH:MM:SS):</label>
            <input type="time" step="1" id="progHora" value="02:00:00" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-purple-500">
          </div>
          <div id="groupIntervalo" style="display: none;">
            <label id="lblIntervalo" class="block font-semibold text-slate-700 mb-1">Intervalo (N):</label>
            <input type="number" id="progIntervalo" min="10" value="10" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-purple-500">
            <span id="hintIntervalo" class="text-[10px] text-purple-700 mt-0.5 block font-medium">Mínimo 10 segundos para pruebas</span>
          </div>
        </div>

        <div id="groupDiaSemana" style="display: none;">
          <label class="block font-semibold text-slate-700 mb-1">Día de la Semana:</label>
          <select id="progDiaSemana" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-purple-500">
            <option value="Lunes">Lunes</option>
            <option value="Martes">Martes</option>
            <option value="Miércoles">Miércoles</option>
            <option value="Jueves">Jueves</option>
            <option value="Viernes">Viernes</option>
            <option value="Sábado">Sábado</option>
            <option value="Domingo">Domingo</option>
          </select>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Retención (Días):</label>
            <input type="number" id="progRetencion" min="0" max="365" value="7" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-purple-500">
            <span class="text-[10px] text-slate-400 mt-0.5 block">0 para indefinido (los respaldos nunca se eliminan)</span>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Estado de Tarea:</label>
            <select id="progHabilitado" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-purple-500">
              <option value="1">Activa / Habilitada</option>
              <option value="0">Pausada / Deshabilitada</option>
            </select>
          </div>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded p-2.5 text-[10px] text-slate-500">
          <i class="fa fa-info-circle text-sky-500"></i> La tarea se ejecutará de forma desatendida desde el backend con zona horaria <strong>America/Lima</strong> y protección anti-colisión exclusiva.
        </div>

        <div class="bg-slate-100 px-5 py-3 -mx-5 -mb-5 mt-4 flex justify-end gap-2 border-t border-slate-200">
          <button type="button" onclick="cerrarModalProgramacionAdmin()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs px-3.5 py-1.5 rounded cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold px-4 py-1.5 rounded cursor-pointer shadow-xs">Guardar Programación</button>
        </div>
      </form>
    </div>
  </div>

  <!-- CONFIGURACIÓN GLOBAL DE API -->
  <script>
    window.API_URL = '<?= API_URL ?>';
    window.API_TOKEN = '<?= $_SESSION['token'] ?>';
  </script>
  <script src="/assets/js/app.js"></script>

  <!-- LÓGICA INTEGRAL DEL PORTAL ADMINISTRADOR (SPA) -->
  <script src="/assets/js/portal_admin.js?v=<?= time() ?>"></script>
</body>
</html>
