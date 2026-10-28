import socket
import threading
from datetime import datetime
import queue

# Crear socket UDP
servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Asociar IP y puerto
servidor_socket.bind(("0.0.0.0", 5000))
print("Servidor UDP esperando mensajes en el puerto 5000...")

# Diccionario para gestionar la cola de mensajes de cada cliente activo
# direccion -> queue.Queue()
clientes_activos = {}
lock_clientes = threading.Lock()
lock_print = threading.Lock()


def imprimir(texto=""):
    with lock_print:
        print(texto)


def manejar_cliente(direccion, cola_mensajes, servidor):
    hora_inicio = datetime.now()
    fmt = "%H:%M:%S"

    imprimir(f"\n[+] Nuevo cliente conectado desde {direccion}")
    imprimir(f"    Hora de inicio de conexión: {hora_inicio.strftime(fmt)}")

    # Lista de preguntas con sus respuestas válidas
    preguntas_respuestas = [
        ("¿Cuánto es 2 + 2?",                          ["4", "cuatro"]),
        ("¿De qué color es el cielo despejado de día?", ["azul"]),
        ("¿Cuál es la capital de Francia?",             ["paris", "parís"]),
        ("¿Cuánto es 10 / 2?",                          ["5", "cinco"]),
        ("¿En qué año estamos?",                        [str(datetime.now().year), "2026", "2025"]),
    ]

    fallo = False

    for i, (pregunta, respuestas_validas) in enumerate(preguntas_respuestas):

        # b) El servidor envía la pregunta al cliente
        servidor.sendto(f"PREGUNTA: {pregunta}".encode("utf-8"), direccion)
        imprimir(f"\n[{direccion}] Pregunta {i + 1}/5 enviada: {pregunta}")

        # c) Esperar la respuesta del cliente a través de su cola (hasta 60 s)
        try:
            respuesta_cliente = cola_mensajes.get(timeout=60)
        except queue.Empty:
            imprimir(f"[!] Cliente {direccion} no respondió a tiempo. Cerrando hilo.")
            fallo = True
            break

        imprimir(f"[{direccion}] Respuesta recibida: {respuesta_cliente}")

        # d) Validar la respuesta
        es_correcta = respuesta_cliente.strip().lower() in [r.lower() for r in respuestas_validas]

        if es_correcta:
            confirmacion = f"OK: '{respuesta_cliente}' es correcta. ✓"
            servidor.sendto(confirmacion.encode("utf-8"), direccion)
            imprimir(f"[{direccion}] Validación: CORRECTO")
        else:
            confirmacion = (
                f"FAIL: '{respuesta_cliente}' es incorrecta. "
                f"La respuesta correcta era: '{respuestas_validas[0]}'."
            )
            servidor.sendto(confirmacion.encode("utf-8"), direccion)
            imprimir(f"[{direccion}] Validación: INCORRECTO — fin del flujo.")
            fallo = True
            break

    # Mensaje final con hora de inicio y hora de fin (requerimiento 3)
    hora_fin = datetime.now()
    mensaje_fin = (
        f"FIN: Conexión iniciada a las {hora_inicio.strftime(fmt)} "
        f"y finalizada a las {hora_fin.strftime(fmt)}."
    )
    servidor.sendto(mensaje_fin.encode("utf-8"), direccion)

    imprimir("\n===================================")
    imprimir(f"--- Resumen Final Cliente {direccion} ---")
    imprimir(f"    Estado:             {'FALLÓ' if fallo else 'COMPLETÓ las 5 preguntas'}")
    imprimir(f"    Hora de inicio:     {hora_inicio.strftime(fmt)}")
    imprimir(f"    Hora de fin:        {hora_fin.strftime(fmt)}")
    imprimir("===================================\n")

    # Limpiar al cliente del diccionario de clientes activos
    with lock_clientes:
        if direccion in clientes_activos:
            del clientes_activos[direccion]


# ── Bucle principal del servidor ──────────────────────────────────────────────
while True:
    try:
        mensaje, direccion = servidor_socket.recvfrom(1024)
        mensaje_decodificado = mensaje.decode("utf-8", errors="ignore").strip()

        with lock_clientes:
            if direccion in clientes_activos:
                # Cliente ya activo: su respuesta va directo a la cola de su hilo
                clientes_activos[direccion].put(mensaje_decodificado)

            else:
                # Cliente nuevo: solo aceptar si envió "Begin"
                if mensaje_decodificado != "Begin":
                    continue  # ignorar cualquier otro mensaje de dirección desconocida

                imprimir(f"[Main] Mensaje 'Begin' recibido de {direccion} — creando hilo.")

                cola = queue.Queue()
                clientes_activos[direccion] = cola

                hilo = threading.Thread(
                    target=manejar_cliente,
                    args=(direccion, cola, servidor_socket),
                    daemon=True
                )
                hilo.start()

    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
        break
    except Exception as e:
        print(f"Error en el servidor: {e}")

servidor_socket.close()
