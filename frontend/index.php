<?php
session_start();
if (isset($_SESSION['token'])) {
    if (($_SESSION['rol'] ?? '') === 'ESTUDIANTE') {
        header('Location: /notas.php');
    } else {
        header('Location: /dashboard.php');
    }
} else {
    header('Location: /login.php');
}
exit;
