<?php
session_start();
require __DIR__ . '/config.php';

if (isset($_SESSION['token'])) {
    if (($_SESSION['rol'] ?? '') === 'ESTUDIANTE') {
        header('Location: /notas.php');
    } else {
        header('Location: /dashboard.php');
    }
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $correo = trim($_POST['correo'] ?? '');
    $password = trim($_POST['password'] ?? '');
    $payload = json_encode(['correo' => $correo, 'password' => $password]);
    $loginApi = defined('INTERNAL_API_URL') ? INTERNAL_API_URL : 'http://127.0.0.1:8000/api';
    $ch = curl_init($loginApi . '/auth/login');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_TIMEOUT => 15
    ]);
    $out = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlErr = curl_error($ch);
    curl_close($ch);

    if ($code === 200) {
        $d = json_decode($out, true);
        $_SESSION['token'] = $d['access_token'];
        $_SESSION['nombre'] = $d['nombre'];
        $_SESSION['rol'] = $d['rol'];
        if ($d['rol'] === 'ESTUDIANTE') {
            header('Location: /notas.php');
        } else {
            header('Location: /dashboard.php');
        }
        exit;
    } else {
        $d = json_decode($out, true);
        if ($curlErr) {
            $error = 'Error de comunicación interna: ' . $curlErr;
        } elseif (!empty($d['detail'])) {
            $error = is_string($d['detail']) ? $d['detail'] : 'Credenciales incorrectas';
        } else {
            $error = 'Correo o contraseña incorrectos';
        }
    }
}
?>
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Iniciar sesión - Portal Académico</title>
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
  <link rel="stylesheet" href="/assets/css/app.css">
</head>
<body class="login-wrap">
  <div class="login-card">
    <div class="login-logo"><i class="fa fa-graduation-cap"></i></div>
    <h3>Portal Académico</h3>
    <p class="text-muted text-center" style="font-size: 12px; margin-bottom: 15px;">Acceso para Estudiantes y Docentes</p>
    <?php if ($error): ?>
      <div class="alert alert-danger" style="font-size: 12px; padding: 8px 12px;"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>
    <form method="post">
      <div class="form-group">
        <label>Correo Electrónico</label>
        <input class="form-control" name="correo" type="email" value="carlos@portal.edu.pe" required autocomplete="username">
      </div>
      <div class="form-group">
        <label>Contraseña</label>
        <input class="form-control" name="password" type="password" value="Estudiante123*" required autocomplete="current-password">
      </div>
      <button class="btn btn-primary btn-block" style="background-color: #0f172a; border-color: #0f172a;">
        <i class="fa fa-sign-in-alt"></i> Ingresar al Portal
      </button>
      <div style="margin-top: 15px; font-size: 11px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 10px;">
        Demo Estudiante: <code>carlos@portal.edu.pe</code> / <code>Estudiante123*</code><br>
        Demo Administrador: <code>admin@portal.edu.pe</code> / <code>Admin123*</code>
      </div>
    </form>
  </div>
</body>
</html>
