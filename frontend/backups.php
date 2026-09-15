<?php
session_start();
if (!isset($_SESSION['token'])) {
    header('Location: /login.php');
    exit;
}
if (!in_array($_SESSION['rol'] ?? '', ['ADMIN', 'ADMINISTRADOR'])) {
    header('Location: /notas.php');
    exit;
}
header('Location: /dashboard.php?modulo=backups-panel');
exit;
