<?php
session_start();
if (!isset($_SESSION['token'])) {
    header('Location: /login.php');
    exit;
}
if (($_SESSION['rol'] ?? '') === 'ESTUDIANTE') {
    header('Location: /notas.php');
    exit;
}
header('Location: /dashboard.php?modulo=estudiantes-lista');
exit;
