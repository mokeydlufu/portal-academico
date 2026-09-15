<?php
session_start();
require __DIR__ . '/config.php';

// Verificación estricta de autenticación
if (!isset($_SESSION['token'])) {
    header('Location: /login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Intranet Académica - Portal del Estudiante</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
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
    .malla-curso {
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .malla-curso:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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

      <!-- Badge "UN" + Título ESTUDIANTE -->
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded bg-slate-900 flex items-center justify-center text-white text-xs font-black tracking-tighter">
          UN
        </div>
        <span class="text-[#f4511e] font-black text-base sm:text-lg tracking-wider uppercase select-none">
          ESTUDIANTE
        </span>
      </div>

      <!-- Iconos de Notificaciones con Badges -->
      <div class="flex items-center gap-2.5 ml-4">
        <!-- Campana Notificaciones -->
        <div onclick="cargarModulo('inicio')" class="relative cursor-pointer hover:opacity-80" title="Avisos Académicos">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
          </svg>
          <span id="badgeAvisos" class="absolute -top-1.5 -right-2 bg-sky-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center ring-1 ring-white">
            3
          </span>
        </div>

        <!-- Trámites / Mensajes -->
        <div onclick="cargarModulo('tramites')" class="relative cursor-pointer ml-1 hover:opacity-80" title="Mis Trámites">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-slate-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/>
          </svg>
          <span id="badgeTramites" class="absolute -top-1.5 -right-2 bg-amber-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center ring-1 ring-white">
            1
          </span>
        </div>
      </div>
    </div>

    <!-- Lado Derecho: Botón Ayuda (?) y Perfil del Alumno con Dropdown -->
    <div class="flex items-center gap-3">
      <button type="button" onclick="openAyudaModal()" class="w-7 h-7 rounded-full bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs flex items-center justify-center shadow-xs cursor-pointer" title="Ayuda e Información del Portal">
        ?
      </button>

      <!-- Perfil con menú desplegable -->
      <div class="relative pl-2 border-l border-slate-200">
        <button id="userMenuBtn" type="button" class="flex items-center gap-2 text-left focus:outline-none cursor-pointer">
          <div class="w-8 h-8 rounded bg-slate-800 overflow-hidden flex items-center justify-center text-white text-xs font-bold">
            <i class="fa fa-user-graduate"></i>
          </div>
          <div class="text-right hidden sm:block leading-tight">
            <div class="flex items-center gap-1 justify-end">
              <span id="topbarStudentName" class="text-[11px] font-bold text-slate-700 uppercase">Cargando...</span>
              <span class="text-[10px] text-slate-400">▼</span>
            </div>
            <div id="topbarStudentCareer" class="text-[9px] text-slate-400 font-semibold uppercase">
              CARGANDO...
            </div>
          </div>
        </button>

        <!-- Dropdown Menu -->
        <div id="userDropdown" class="hidden absolute right-0 mt-2 w-56 bg-white rounded-md shadow-xl border border-slate-200 py-1.5 z-50 text-xs">
          <div class="px-3 py-2 border-b border-slate-100 bg-slate-50">
            <div id="dropdownName" class="font-bold text-slate-800 text-[11px] uppercase truncate">...</div>
            <div id="dropdownCode" class="text-slate-500 text-[10px]">...</div>
          </div>
          <a href="javascript:void(0)" onclick="openProfileModal()" class="px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <i class="fa fa-id-card text-sky-500 w-4 text-center"></i> Mi Perfil Completo
          </a>
          <a href="javascript:void(0)" onclick="openEditProfileModal()" class="px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <i class="fa fa-user-edit text-emerald-500 w-4 text-center"></i> Actualizar Contacto
          </a>
          <a href="javascript:void(0)" onclick="openPasswordModal()" class="px-3 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <i class="fa fa-key text-amber-500 w-4 text-center"></i> Cambiar Contraseña
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

        <!-- 1. Inicio -->
        <div id="nav-inicio" onclick="cargarModulo('inicio')" class="px-3 py-2 rounded text-slate-300 hover:text-white flex items-center gap-2.5 cursor-pointer hover:bg-slate-800/40 transition-colors">
          <i class="fa fa-home w-4 text-center text-slate-400"></i>
          <span class="font-normal">Inicio</span>
        </div>

        <!-- 2. Personal (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-personal" onclick="toggleModuloAccordion('personal')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-user-circle w-4 text-center text-slate-400"></i>
              <span>Personal</span>
            </span>
            <span id="icon-personal" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-personal" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-personal-perfil" onclick="cargarModulo('personal-perfil')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Mi Perfil
            </div>
            <div id="nav-personal-datos" onclick="cargarModulo('personal-datos')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Datos Personales
            </div>
            <div id="nav-personal-password" onclick="cargarModulo('personal-password')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Cambiar Contraseña
            </div>
          </div>
        </div>

        <!-- 3. Matrícula (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-matricula" onclick="toggleModuloAccordion('matricula')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-id-card-clip w-4 text-center text-slate-400"></i>
              <span>Matrícula</span>
            </span>
            <span id="icon-matricula" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-matricula" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-matricula-actual" onclick="cargarModulo('matricula-actual')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Matrícula Actual
            </div>
            <div id="nav-matricula-cursos" onclick="cargarModulo('matricula-cursos')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Cursos Matriculados
            </div>
            <div id="nav-matricula-horario" onclick="cargarModulo('matricula-horario')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Horario
            </div>
          </div>
        </div>

        <!-- Categoría: GESTIÓN ACADÉMICA -->
        <div class="px-3 pt-3 pb-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          GESTIÓN ACADÉMICA
        </div>

        <!-- 4. Académica (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-academica" onclick="toggleModuloAccordion('academica')" class="accordion-header px-3 py-2 rounded text-white bg-[#1e293b] flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5 text-rose-400 font-medium">
              <i class="fa fa-graduation-cap text-rose-400 w-4 text-center"></i>
              <span>Académica</span>
            </span>
            <span id="icon-academica" class="text-slate-400 font-bold text-sm w-4 text-center select-none">-</span>
          </div>
          <div id="submenu-academica" class="accordion-submenu open space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-record" onclick="cargarModulo('record')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white flex items-center gap-2 cursor-pointer hover:bg-slate-800/40 transition-colors">
              <i class="fa fa-folder-open text-slate-400 text-[11px] w-4 text-center"></i>
              <span>Récord Académico</span>
            </div>
            <div id="nav-avance" onclick="cargarModulo('avance')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white flex items-center gap-2 cursor-pointer hover:bg-slate-800/40 transition-colors">
              <i class="fa fa-diagram-project text-slate-400 text-[11px] w-4 text-center"></i>
              <span>Avance Curricular</span>
            </div>
            <div id="nav-rendimiento" onclick="cargarModulo('rendimiento')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white flex items-center gap-2 cursor-pointer hover:bg-slate-800/40 transition-colors">
              <i class="fa fa-chart-line text-slate-400 text-[11px] w-4 text-center"></i>
              <span>Rendimiento por Ciclo</span>
            </div>
            <div id="nav-encuestas" onclick="cargarModulo('encuestas')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white flex items-center gap-2 cursor-pointer hover:bg-slate-800/40 transition-colors">
              <i class="fa fa-star-half-stroke text-slate-400 text-[11px] w-4 text-center"></i>
              <span>Encuestas</span>
            </div>
            <div id="nav-notas" onclick="cargarModulo('notas')" class="px-2.5 py-1.5 rounded text-rose-500 font-semibold flex items-center gap-2 cursor-pointer bg-slate-900/40 transition-colors">
              <i class="fa fa-clipboard-check text-rose-500 text-[11px] w-4 text-center"></i>
              <span>Notas del Periodo</span>
            </div>
            <div id="nav-asistencias" onclick="cargarModulo('asistencias')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white flex items-center gap-2 cursor-pointer hover:bg-slate-800/40 transition-colors">
              <i class="fa fa-calendar-check text-slate-400 text-[11px] w-4 text-center"></i>
              <span>Asistencias</span>
            </div>
          </div>
        </div>

        <!-- 5. Trámites y Pagos (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-tramites" onclick="toggleModuloAccordion('tramites')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-receipt w-4 text-center text-slate-400"></i>
              <span>Trámites y Pagos</span>
            </span>
            <span id="icon-tramites" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-tramites" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-tramites-mis" onclick="cargarModulo('tramites-mis')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Mis Trámites
            </div>
            <div id="nav-tramites-nuevo" onclick="cargarModulo('tramites-nuevo')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Nuevo Trámite
            </div>
            <div id="nav-pagos" onclick="cargarModulo('pagos')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Pagos
            </div>
          </div>
        </div>

        <!-- 6. Fichas Bienestar (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-bienestar" onclick="toggleModuloAccordion('bienestar')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-heart-pulse w-4 text-center text-slate-400"></i>
              <span>Fichas Bienestar</span>
            </span>
            <span id="icon-bienestar" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-bienestar" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-bienestar-ficha" onclick="cargarModulo('bienestar-ficha')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Mi Ficha
            </div>
            <div id="nav-bienestar-actualizar" onclick="cargarModulo('bienestar-actualizar')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Actualizar Datos
            </div>
          </div>
        </div>

        <!-- 7. Examen Recuperación (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-recuperacion" onclick="toggleModuloAccordion('recuperacion')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-pen-to-square w-4 text-center text-slate-400"></i>
              <span>Examen Recuperación</span>
            </span>
            <span id="icon-recuperacion" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-recuperacion" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-recuperacion-solicitar" onclick="cargarModulo('recuperacion-solicitar')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Solicitar
            </div>
            <div id="nav-recuperacion-mis" onclick="cargarModulo('recuperacion-mis')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Mis solicitudes
            </div>
          </div>
        </div>

        <!-- 8. Examen Reprogramación (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-reprogramacion" onclick="toggleModuloAccordion('reprogramacion')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-clock-rotate-left w-4 text-center text-slate-400"></i>
              <span>Examen Reprogramación</span>
            </span>
            <span id="icon-reprogramacion" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-reprogramacion" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-reprogramacion-solicitar" onclick="cargarModulo('reprogramacion-solicitar')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Solicitar
            </div>
            <div id="nav-reprogramacion-mis" onclick="cargarModulo('reprogramacion-mis')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Mis solicitudes
            </div>
          </div>
        </div>

        <!-- 9. Bolsa Laboral (Colapsable con Acordeón + / -) -->
        <div class="menu-item">
          <div id="header-bolsa" onclick="toggleModuloAccordion('bolsa')" class="accordion-header px-3 py-2 rounded text-slate-300 hover:text-white flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors">
            <span class="flex items-center gap-2.5">
              <i class="fa fa-briefcase w-4 text-center text-slate-400"></i>
              <span>Bolsa Laboral</span>
            </span>
            <span id="icon-bolsa" class="text-slate-500 font-bold text-sm w-4 text-center select-none">+</span>
          </div>
          <div id="submenu-bolsa" class="accordion-submenu space-y-0.5 mt-1 pl-6 text-[11px]">
            <div id="nav-bolsa-ofertas" onclick="cargarModulo('bolsa-ofertas')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Ofertas
            </div>
            <div id="nav-bolsa-postulaciones" onclick="cargarModulo('bolsa-postulaciones')" class="px-2.5 py-1.5 rounded text-slate-400 hover:text-white cursor-pointer hover:bg-slate-800/40 transition-colors">
              Mis Postulaciones
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-slate-800/60 mt-4">
          <a href="/logout.php" class="px-3 py-2 rounded text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 flex items-center gap-2.5 transition-colors">
            <i class="fa fa-arrow-right-from-bracket w-4 text-center"></i>
            <span>Cerrar Sesión</span>
          </a>
        </div>

      </div>
    </aside>

    <!-- ================= CONTENIDO PRINCIPAL DINÁMICO ================= -->
    <main class="ml-0 sm:ml-64 flex-1 bg-[#f8fafc] p-4 lg:p-6 min-h-[calc(100vh-3.5rem)]">
      <!-- CONTENEDOR DINÁMICO DE VISTAS (SPA que preserva la sesión) -->
      <div id="dynamicContentContainer">
        <!-- Renderizado dinámicamente -->
      </div>
    </main>
  </div>

  <!-- ================================================================ -->
  <!-- MODALES DE TODAS LAS ACCIONES DEL SISTEMA                        -->
  <!-- ================================================================ -->

  <!-- MODAL: DETALLE DE CALIFICACIONES (19. Ver Notas) -->
  <div id="notasModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa fa-clipboard-list text-rose-400 text-base"></i>
          <h3 class="text-sm font-bold tracking-wide uppercase">Detalle Oficial de Calificaciones</h3>
        </div>
        <button type="button" onclick="closeNotasModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer" title="Cerrar">&times;</button>
      </div>

      <div class="p-5 space-y-4 text-xs">
        <div class="bg-slate-50 border border-slate-200 rounded p-3 grid grid-cols-1 sm:grid-cols-2 gap-2 leading-relaxed">
          <div><span class="text-slate-500 font-medium">Curso:</span> <span id="modalCursoNombre" class="font-bold text-slate-800 ml-1">...</span></div>
          <div><span class="text-slate-500 font-medium">Código:</span> <span id="modalCursoCodigo" class="font-semibold text-slate-700 ml-1">...</span></div>
          <div><span class="text-slate-500 font-medium">Docente:</span> <span id="modalCursoDocente" class="font-semibold text-slate-700 ml-1">...</span></div>
          <div><span class="text-slate-500 font-medium">Periodo / Sección:</span> <span id="modalCursoPeriodoSeccion" class="font-semibold text-slate-700 ml-1">...</span></div>
        </div>

        <div class="border border-slate-200 rounded overflow-hidden">
          <table class="w-full text-left border-collapse text-xs">
            <thead class="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th class="py-2.5 px-3">Evaluación</th>
                <th class="py-2.5 px-3 text-center w-16">Tipo</th>
                <th class="py-2.5 px-3 text-center w-20">Peso</th>
                <th class="py-2.5 px-3 text-center w-20">Nota</th>
                <th class="py-2.5 px-3 text-center w-24">Estado</th>
              </tr>
            </thead>
            <tbody id="modalEvaluacionesBody" class="divide-y divide-slate-100"></tbody>
          </table>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-4">
            <div>
              <span class="text-slate-500 block text-[10px] uppercase font-semibold">Promedio Ponderado Actual</span>
              <span id="modalPromedioActual" class="text-base font-bold text-slate-800">--</span>
            </div>
            <div class="border-l border-slate-200 pl-4">
              <span class="text-slate-500 block text-[10px] uppercase font-semibold">Promedio Final Oficial</span>
              <span id="modalPromedioFinal" class="text-base font-bold text-slate-800">--</span>
            </div>
          </div>
          <div>
            <span class="text-slate-500 block text-[10px] uppercase font-semibold">Estado de la Asignatura</span>
            <span id="modalEstadoCurso" class="inline-block px-2.5 py-1 text-[11px] font-bold rounded mt-0.5 bg-slate-200 text-slate-700">--</span>
          </div>
        </div>
      </div>

      <div class="bg-slate-100 px-5 py-3 text-right border-t border-slate-200">
        <button type="button" onclick="closeNotasModal()" class="bg-slate-700 hover:bg-slate-800 text-white text-xs font-medium px-4 py-1.5 rounded cursor-pointer transition-colors">Cerrar</button>
      </div>
    </div>
  </div>

  <!-- MODAL: MI PERFIL DETALLADO -->
  <div id="profileModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa fa-id-card text-sky-400"></i>
          <h3 class="text-sm font-bold tracking-wide uppercase">Ficha Integral del Estudiante</h3>
        </div>
        <button type="button" onclick="closeProfileModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3">
        <div class="flex items-center gap-4 pb-3 border-b border-slate-100">
          <div class="w-14 h-14 rounded-full bg-slate-800 text-white flex items-center justify-center text-xl font-bold">
            <i class="fa fa-user-graduate"></i>
          </div>
          <div>
            <div id="profNombre" class="font-bold text-slate-800 text-sm uppercase">...</div>
            <div id="profCodigo" class="text-slate-500">...</div>
            <span class="inline-block mt-1 px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">ESTUDIANTE REGULAR ACTIVO</span>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-slate-600 leading-relaxed">
          <div><strong>DNI:</strong> <span id="profDni">...</span></div>
          <div><strong>Ciclo Académico:</strong> <span id="profCiclo">...</span></div>
          <div class="col-span-2"><strong>Carrera Profesional:</strong> <span id="profCarrera">...</span></div>
          <div class="col-span-2"><strong>Correo Electrónico:</strong> <span id="profCorreo">...</span></div>
          <div><strong>Teléfono / Celular:</strong> <span id="profTelefono">...</span></div>
          <div><strong>Fecha de Registro:</strong> <span>Semestre 2023-I</span></div>
          <div class="col-span-2"><strong>Dirección:</strong> <span id="profDireccion">...</span></div>
        </div>
      </div>
      <div class="bg-slate-100 px-5 py-2.5 flex justify-end gap-2 border-t border-slate-200">
        <button type="button" onclick="closeProfileModal(); openEditProfileModal();" class="bg-[#f4511e] hover:bg-[#e64a19] text-white text-xs font-medium px-3.5 py-1.5 rounded cursor-pointer">
          <i class="fa fa-pen mr-1"></i> Editar Contacto
        </button>
        <button type="button" onclick="closeProfileModal()" class="bg-slate-700 hover:bg-slate-800 text-white text-xs font-medium px-4 py-1.5 rounded cursor-pointer">Cerrar</button>
      </div>
    </div>
  </div>

  <!-- MODAL: EDITAR DATOS DE CONTACTO (PUT /api/estudiante/perfil) -->
  <div id="editProfileModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa fa-user-edit text-emerald-400"></i>
          <h3 class="text-sm font-bold tracking-wide uppercase">Actualizar Datos de Contacto</h3>
        </div>
        <button type="button" onclick="closeEditProfileModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="editProfileForm" onsubmit="handleProfileUpdate(event)" class="p-5 text-xs space-y-3">
        <div id="editProfileAlert" class="hidden p-2 rounded text-xs"></div>
        <div>
          <label class="block font-medium text-slate-700 mb-1">Teléfono Móvil:</label>
          <input id="editTelefono" type="tel" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block font-medium text-slate-700 mb-1">Dirección de Domicilio Actual:</label>
          <input id="editDireccion" type="text" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
        </div>
        <div class="pt-2 text-right">
          <button type="button" onclick="closeEditProfileModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded mr-2 cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded cursor-pointer font-medium">Guardar Cambios</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: CAMBIAR CONTRASEÑA -->
  <div id="passwordModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa fa-key text-amber-400"></i>
          <h3 class="text-sm font-bold tracking-wide uppercase">Cambiar Contraseña de Acceso</h3>
        </div>
        <button type="button" onclick="closePasswordModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="changePasswordForm" onsubmit="handlePasswordChange(event)" class="p-5 text-xs space-y-3">
        <div id="passwordAlert" class="hidden p-2 rounded text-xs"></div>
        <div>
          <label class="block font-medium text-slate-700 mb-1">Contraseña Actual:</label>
          <input id="pwdActual" type="password" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block font-medium text-slate-700 mb-1">Nueva Contraseña (mínimo 6 caracteres):</label>
          <input id="pwdNueva" type="password" minlength="6" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block font-medium text-slate-700 mb-1">Confirmar Nueva Contraseña:</label>
          <input id="pwdConfirmar" type="password" minlength="6" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
        </div>
        <div class="pt-2 text-right">
          <button type="button" onclick="closePasswordModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded mr-2 cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-[#f4511e] hover:bg-[#e64a19] text-white px-4 py-1.5 rounded cursor-pointer">Actualizar Contraseña</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: DETALLE DE CURSO DE MATRÍCULA -->
  <div id="cursoDetalleModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-book text-sky-400"></i> Detalle de Asignatura Matriculada
        </h3>
        <button type="button" onclick="closeCursoDetalleModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3" id="cursoDetalleBody"></div>
      <div class="bg-slate-100 px-5 py-2.5 text-right border-t border-slate-200">
        <button type="button" onclick="closeCursoDetalleModal()" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-4 py-1.5 rounded cursor-pointer">Cerrar</button>
      </div>
    </div>
  </div>

  <!-- MODAL: CURSO DE MALLA CURRICULAR -->
  <div id="mallaModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-sitemap text-amber-400"></i> Información de Malla Curricular
        </h3>
        <button type="button" onclick="closeMallaModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3" id="mallaModalBody"></div>
      <div class="bg-slate-100 px-5 py-2.5 text-right border-t border-slate-200">
        <button type="button" onclick="closeMallaModal()" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-4 py-1.5 rounded cursor-pointer">Cerrar</button>
      </div>
    </div>
  </div>

  <!-- MODAL: RESPONDER ENCUESTA DOCENTE -->
  <div id="encuestaModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-star text-amber-400"></i> Evaluación de Desempeño Docente
        </h3>
        <button type="button" onclick="closeEncuestaModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="encuestaForm" onsubmit="handleEncuestaSubmit(event)" class="p-5 text-xs space-y-4">
        <input type="hidden" id="encuestaSeccionId">
        <div class="bg-slate-50 border border-slate-200 rounded p-3">
          <div class="font-bold text-slate-800 text-sm" id="encuestaCursoNom">...</div>
          <div class="text-slate-600 mt-1">Docente: <strong id="encuestaDocenteNom">...</strong></div>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1.5">Calificación General (1 a 5 estrellas):</label>
          <div class="flex items-center gap-2">
            <select id="encuestaPuntaje" class="border border-slate-300 rounded px-3 py-2 text-sm font-bold focus:outline-none focus:border-rose-500">
              <option value="5">⭐⭐⭐⭐⭐ 5 - Excelente Desempeño</option>
              <option value="4">⭐⭐⭐⭐ 4 - Muy Bueno</option>
              <option value="3">⭐⭐⭐ 3 - Regular / Satisfactorio</option>
              <option value="2">⭐⭐ 2 - Requiere Mejora</option>
              <option value="1">⭐ 1 - Deficiente</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Comentarios u observaciones constructivas:</label>
          <textarea id="encuestaComentarios" rows="3" required placeholder="Escriba su apreciación sobre la metodología, puntualidad y dominio del docente..." class="w-full border border-slate-300 rounded p-2.5 focus:outline-none focus:border-rose-500"></textarea>
        </div>
        <div class="text-right pt-2">
          <button type="button" onclick="closeEncuestaModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded mr-2 cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-[#f4511e] hover:bg-[#e64a19] text-white px-4 py-1.5 rounded cursor-pointer font-bold">Enviar Evaluación</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: DETALLE DE TRÁMITE -->
  <div id="tramiteModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-file-invoice text-emerald-400"></i> Seguimiento de Solicitud de Trámite
        </h3>
        <button type="button" onclick="closeTramiteModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3" id="tramiteModalBody"></div>
      <div class="bg-slate-100 px-5 py-2.5 text-right border-t border-slate-200">
        <button type="button" onclick="closeTramiteModal()" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-4 py-1.5 rounded cursor-pointer">Cerrar</button>
      </div>
    </div>
  </div>

  <!-- MODAL: NUEVO TRÁMITE -->
  <div id="nuevoTramiteModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-plus-circle text-sky-400"></i> Registrar Nueva Solicitud de Trámite
        </h3>
        <button type="button" onclick="closeNuevoTramiteModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="nuevoTramiteForm" onsubmit="handleNuevoTramiteSubmit(event)" class="p-5 text-xs space-y-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Tipo de Trámite Solicitado:</label>
          <select id="trmTipo" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
            <option value="Constancia de Estudios">Constancia de Estudios Oficial</option>
            <option value="Certificado de Notas Oficial">Certificado de Notas Oficial</option>
            <option value="Carta de Presentación de Prácticas">Carta de Presentación de Prácticas Pre-Profesionales</option>
            <option value="Rectificación de Matrícula">Rectificación de Matrícula</option>
            <option value="Retiro de Asignatura">Retiro de Asignatura Extraordinario</option>
            <option value="Duplicado de Carné Universitario">Duplicado de Carné Universitario</option>
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Motivo / Asunto:</label>
          <input id="trmMotivo" type="text" required placeholder="Ej. Trámite para postulación laboral o seguro médico" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Descripción / Sustento del Trámite:</label>
          <textarea id="trmDescripcion" rows="3" required placeholder="Explique brevemente el motivo de su solicitud..." class="w-full border border-slate-300 rounded p-2.5 focus:outline-none focus:border-rose-500"></textarea>
        </div>
        <div class="pt-2 text-right">
          <button type="button" onclick="closeNuevoTramiteModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded mr-2 cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-[#f4511e] hover:bg-[#e64a19] text-white px-4 py-1.5 rounded cursor-pointer font-bold">Enviar Solicitud</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: ACTUALIZAR FICHA DE BIENESTAR -->
  <div id="bienestarModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-heart-pulse text-rose-400"></i> Actualizar Ficha de Bienestar Integral
        </h3>
        <button type="button" onclick="closeBienestarModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="bienestarForm" onsubmit="handleBienestarSubmit(event)" class="p-5 text-xs space-y-3">
        <div class="font-bold text-slate-700 uppercase text-[11px] border-b pb-1">Contacto de Emergencia</div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-slate-600 mb-1">Nombre Completo:</label>
            <input id="bienContacto" type="text" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
          <div>
            <label class="block text-slate-600 mb-1">Parentesco:</label>
            <input id="bienParentesco" type="text" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
          <div class="col-span-2">
            <label class="block text-slate-600 mb-1">Teléfono de Emergencia:</label>
            <input id="bienTelEmergencia" type="tel" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
        </div>

        <div class="font-bold text-slate-700 uppercase text-[11px] border-b pb-1 pt-2">Datos Socioeconómicos y Vivienda</div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-slate-600 mb-1">Condición Vivienda:</label>
            <select id="bienVivienda" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
              <option value="Propia">Propia</option>
              <option value="Alquilada">Alquilada</option>
              <option value="Familiar">Familiar / Compartida</option>
            </select>
          </div>
          <div>
            <label class="block text-slate-600 mb-1">Seguro Médico:</label>
            <select id="bienSeguro" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
              <option value="Seguro Estudiantil">Seguro Estudiantil Universitario</option>
              <option value="EsSalud">EsSalud</option>
              <option value="SIS">SIS (Seguro Integral de Salud)</option>
              <option value="Privado (EPS)">EPS / Privado</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-slate-600 mb-1">Alergias o Condiciones Médicas:</label>
            <input id="bienAlergias" type="text" placeholder="Ninguna o especificar" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
          </div>
        </div>

        <div class="pt-2 text-right">
          <button type="button" onclick="closeBienestarModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded mr-2 cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded cursor-pointer font-bold">Guardar Ficha</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: SOLICITAR EXAMEN DE RECUPERACIÓN -->
  <div id="recuperacionModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-pen-to-square text-amber-400"></i> Solicitud de Examen de Recuperación
        </h3>
        <button type="button" onclick="closeRecuperacionModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="recuperacionForm" onsubmit="handleRecuperacionSubmit(event)" class="p-5 text-xs space-y-3">
        <input type="hidden" id="recupMatriculaId">
        <div class="bg-slate-50 border border-slate-200 rounded p-3">
          <div class="text-slate-500 text-[10px] font-bold uppercase">Asignatura Seleccionada</div>
          <div class="font-bold text-slate-800 text-sm mt-0.5" id="recupCursoNom">...</div>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Motivo o Justificación:</label>
          <textarea id="recupMotivo" rows="3" required placeholder="Indique el motivo de la solicitud de evaluación de recuperación..." class="w-full border border-slate-300 rounded p-2.5 focus:outline-none focus:border-rose-500"></textarea>
        </div>
        <div class="text-right pt-2">
          <button type="button" onclick="closeRecuperacionModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded mr-2 cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-[#f4511e] hover:bg-[#e64a19] text-white px-4 py-1.5 rounded cursor-pointer font-bold">Confirmar Solicitud</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: SOLICITAR REPROGRAMACIÓN DE EVALUACIÓN -->
  <div id="reprogramacionModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#1e293b] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-clock-rotate-left text-sky-400"></i> Solicitud de Reprogramación de Evaluación
        </h3>
        <button type="button" onclick="closeReprogramacionModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <form id="reprogramacionForm" onsubmit="handleReprogramacionSubmit(event)" class="p-5 text-xs space-y-3">
        <input type="hidden" id="reprogEvaluacionId">
        <input type="hidden" id="reprogMatriculaId">
        <div class="bg-slate-50 border border-slate-200 rounded p-3">
          <div class="font-bold text-slate-800 text-sm" id="reprogCursoNom">...</div>
          <div class="text-slate-600 mt-0.5">Evaluación: <strong id="reprogEvalNom">...</strong></div>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Motivo Justificado:</label>
          <select id="reprogMotivo" class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
            <option value="Salud / Descanso Médico">Salud / Descanso Médico Certificado</option>
            <option value="Laboral / Comprobante de Trabajo">Laboral / Comprobante de Trabajo</option>
            <option value="Fuerza Mayor / Emergencia Familiar">Fuerza Mayor / Emergencia Familiar</option>
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Fecha Propuesta para Rendir Evaluación:</label>
          <input id="reprogFecha" type="date" required class="w-full border border-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-rose-500">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Detalle del Sustento Documentario:</label>
          <textarea id="reprogSustento" rows="3" required placeholder="Describa el certificado o documento probatorio que adjuntará..." class="w-full border border-slate-300 rounded p-2.5 focus:outline-none focus:border-rose-500"></textarea>
        </div>
        <div class="text-right pt-2">
          <button type="button" onclick="closeReprogramacionModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded mr-2 cursor-pointer">Cancelar</button>
          <button type="submit" class="bg-[#f4511e] hover:bg-[#e64a19] text-white px-4 py-1.5 rounded cursor-pointer font-bold">Enviar Solicitud</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: DETALLE DE EMPLEO / BOLSA LABORAL -->
  <div id="empleoModal" class="fixed inset-0 z-50 hidden overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-md shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
      <div class="bg-[#0f172a] text-white px-5 py-3.5 flex items-center justify-between">
        <h3 class="text-sm font-bold uppercase flex items-center gap-2">
          <i class="fa fa-briefcase text-emerald-400"></i> Detalle de Oportunidad Laboral
        </h3>
        <button type="button" onclick="closeEmpleoModal()" class="text-slate-400 hover:text-white text-lg font-bold p-1 cursor-pointer">&times;</button>
      </div>
      <div class="p-5 text-xs space-y-3" id="empleoModalBody"></div>
      <div class="bg-slate-100 px-5 py-2.5 flex justify-end gap-2 border-t border-slate-200">
        <button type="button" onclick="closeEmpleoModal()" class="bg-slate-700 hover:bg-slate-800 text-white text-xs px-4 py-1.5 rounded cursor-pointer">Cerrar</button>
      </div>
    </div>
  </div>

  <!-- CONFIGURACIÓN GLOBAL DE API -->
  <script>
    window.API_URL = '<?= API_URL ?>';
    window.API_TOKEN = '<?= $_SESSION['token'] ?>';
  </script>
  <script src="/assets/js/app.js"></script>

  <!-- LÓGICA INTEGRAL DEL PORTAL ACADÉMICO (SPA) -->
  <script src="/assets/js/portal_estudiante.js?v=<?= time() ?>"></script>
</body>
</html>
