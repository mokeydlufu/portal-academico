<?php if (!isset($pageTitle)) $pageTitle = 'Portal Académico'; ?>
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars($pageTitle) ?></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    corePlugins: {
      preflight: false,
    },
    theme: {
      extend: {
        fontFamily: {
          sans: ['Inter', 'sans-serif'],
        }
      }
    }
  }
</script>
<link rel="stylesheet" href="/assets/css/app.css">
</head><body>
<nav class="navbar navbar-inverse navbar-fixed-top app-topbar"><div class="container-fluid"><div class="navbar-header"><a class="navbar-brand" href="/dashboard.php"><i class="fa fa-graduation-cap"></i> CampusSys</a></div><ul class="nav navbar-nav navbar-right"><li><a href="#"><i class="fa fa-user"></i> <?= htmlspecialchars($_SESSION['nombre'] ?? 'Usuario') ?></a></li><li><a href="/logout.php"><i class="fa fa-right-from-bracket"></i> Salir</a></li></ul></div></nav>
<div class="app-shell">
<aside class="sidebar">
<div class="profile-box"><div class="avatar"><i class="fa fa-user-graduate"></i></div><strong><?= htmlspecialchars($_SESSION['nombre'] ?? 'Administrador') ?></strong><small><?= htmlspecialchars($_SESSION['rol'] ?? 'ADMIN') ?></small></div>
<ul class="nav nav-pills nav-stacked">
<li><a href="/dashboard.php"><i class="fa fa-gauge"></i> Dashboard</a></li>
<li><a href="/estudiantes.php"><i class="fa fa-graduation-cap"></i> Mis Notas</a></li>
<li><a href="/cursos.php"><i class="fa fa-book"></i> Cursos</a></li>
<li><a href="/matriculas.php"><i class="fa fa-clipboard-list"></i> Matrículas</a></li>
<?php if (in_array($_SESSION['rol'] ?? '', ['ADMIN', 'ADMINISTRADOR'])): ?>
<li class="menu-item-backup-group">
  <a href="javascript:void(0)" onclick="toggleBackupAccordion()" id="btnToggleBackup" style="display:flex; justify-content:space-between; align-items:center;">
    <span><i class="fa fa-database"></i> Copias de Seguridad</span>
    <span id="backupIcon" style="font-weight:bold; font-size:14px;">+</span>
  </a>
  <ul id="backupSubmenu" class="nav nav-pills nav-stacked" style="display:none; padding-left:14px; font-size:12px; background:rgba(0,0,0,0.12); border-radius:4px; margin-top:2px;">
    <li><a href="/backups.php?tab=panel"><i class="fa fa-chart-pie" style="font-size:11px;"></i> Panel de Backups</a></li>
    <li><a href="javascript:void(0)" onclick="triggerCrearBackupModal()"><i class="fa fa-plus-circle text-success" style="font-size:11px;"></i> Crear Backup</a></li>
    <li><a href="/backups.php?tab=guardados"><i class="fa fa-box-archive" style="font-size:11px;"></i> Backups Guardados</a></li>
    <li><a href="/backups.php?tab=programacion"><i class="fa fa-clock text-warning" style="font-size:11px;"></i> Programación</a></li>
    <li><a href="/backups.php?tab=historial"><i class="fa fa-list-check" style="font-size:11px;"></i> Historial</a></li>
    <li><a href="/backups.php?tab=restauraciones"><i class="fa fa-rotate-left text-info" style="font-size:11px;"></i> Restauraciones</a></li>
  </ul>
</li>
<?php endif; ?>
</ul>
<script>
function toggleBackupAccordion(forceOpen = false) {
  const sm = document.getElementById('backupSubmenu');
  const ic = document.getElementById('backupIcon');
  if (!sm) return;
  const isOpen = sm.style.display !== 'none';
  if (isOpen && !forceOpen) {
    sm.style.display = 'none';
    if (ic) ic.innerText = '+';
  } else {
    sm.style.display = 'block';
    if (ic) ic.innerText = '-';
  }
}
function triggerCrearBackupModal() {
  if (window.location.pathname.includes('backups.php')) {
    if (typeof abrirModalCrearBackup === 'function') {
      abrirModalCrearBackup();
    }
  } else {
    window.location.href = '/backups.php?action=crear';
  }
}
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname.includes('backups.php')) {
    toggleBackupAccordion(true);
  }
});
</script>
</aside>
<main class="main-content"><div class="container-fluid">
