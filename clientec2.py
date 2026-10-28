import socket
from datetime import datetime

# Crear socket UDP
socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Pedir IP del servidor (Enter para usar 127.0.0.1 en pruebas locales)
ip_input = input("Ingrese la IP del servidor [Enter para 127.0.0.1]: ").strip()
ip_servidor = ip_input if ip_input else "127.0.0.1"
direccion_servidor = (ip_servidor, 5000)

hora_inicio = datetime.now()
fmt = "%H:%M:%S"
print(f"\n--- Iniciando conexión con el servidor {direccion_servidor} a las {hora_inicio.strftime(fmt)} ---")

# a) El cliente envía "Begin" para iniciar el flujo
socket_cliente.sendto("Begin".encode("utf-8"), direccion_servidor)
print("[Cliente] Mensaje 'Begin' enviado al servidor.")

# Bucle de 5 preguntas
for i in range(5):

    # b) Recibe la pregunta del servidor
    data, _ = socket_cliente.recvfrom(1024)
    mensaje_servidor = data.decode("utf-8")
    print(f"\n[Servidor - PREGUNTA {i + 1}/5]: {mensaje_servidor}")

    # c) El cliente envía su respuesta
    mi_respuesta = input("Su respuesta: ").strip()
    socket_cliente.sendto(mi_respuesta.encode("utf-8"), direccion_servidor)

    # d) Recibe la validación del servidor (OK o FAIL)
    data_val, _ = socket_cliente.recvfrom(1024)
    validacion = data_val.decode("utf-8")
    print(f"[Servidor - Validación]: {validacion}")

    # Si la respuesta fue incorrecta el servidor termina el flujo
    if validacion.startswith("FAIL:"):
        break

# Al terminar (por 5 preguntas completadas o por FAIL), el servidor
# siempre envía un mensaje final con las horas de inicio y fin
data_fin, _ = socket_cliente.recvfrom(1024)
mensaje_fin = data_fin.decode("utf-8")

print("\n===================================")
print(f"[Servidor - MENSAJE FINAL]: {mensaje_fin}")
print("===================================")

socket_cliente.close()
