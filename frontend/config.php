<?php
$envApiUrl = getenv('API_URL') ?: (isset($_ENV['API_URL']) ? $_ENV['API_URL'] : null);
define('API_URL', $envApiUrl ?: 'http://127.0.0.1:8000/api');
?>
