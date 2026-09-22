# ZonaShop Backend

## Pagos de prueba con Wompi

Copia `.env.example` como `.env` y completa las credenciales Sandbox de
Wompi. El checkout reserva existencias durante 30 minutos. Un pago aprobado
confirma el pedido; un pago rechazado o una reserva expirada repone las
existencias. Los secretos de integridad y eventos pertenecen exclusivamente
al backend y nunca deben copiarse al frontend.

El webhook es `/api/pedidos/wompi/webhook/`. Para recibir eventos durante el
desarrollo, el backend debe exponerse mediante una URL HTTPS y esa URL pública
debe registrarse en el panel Sandbox de Wompi.
