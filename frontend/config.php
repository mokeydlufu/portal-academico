<?php
// URL interna para llamadas cURL desde PHP
define('INTERNAL_API_URL', getenv('INTERNAL_API_URL') ?: 'http://127.0.0.1:8000/api');

// URL para el navegador (JavaScript fetch)
$envApiUrl = getenv('API_URL');
if ($envApiUrl) {
    define('API_URL', $envApiUrl);
} else {
    // Si corre en localhost con puertos separados (8080 y 8000)
    if (isset($_SERVER['HTTP_HOST']) && strpos($_SERVER['HTTP_HOST'], 'localhost:8080') !== false) {
        define('API_URL', 'http://127.0.0.1:8000/api');
    } else {
        // En producción unificada bajo un mismo link:
        define('API_URL', '/api');
    }
}
?>
