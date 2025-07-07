# Guía de compilación y ejecución del proyecto.

## 1\. Prerrequisitos

Antes de compilar, debes tener instalado lo siguiente en tu sistema:

### Prerrequisitos de cliente_sensor.cpp:

  * Un compilador de C++
  * La librería de desarrollo de OpenSSL. (En sistemas basados en Debian/Ubuntu puedes instalarla con `sudo apt install libssl-dev`. En MSYS2/MinGW, puedes usar `pacman -S mingw-w64-ucrt-x86_64-openssl`).
  * Se requiere el archivo de clave privada del cliente (`private.pem`) en el mismo directorio.
  * Para compilar: `g++ cliente_sensor.cpp -o cliente_sensor -lssl -lcrypto` (Agrega `-lws2_32` en Windows para la librería de sockets).

### Prerrequisitos de servidor_intermedio.py

  * Se utilizó Python 3.13
  * El módulo `cryptography`, `requests` y `pymodbus` deben estar instalados. (Puedes instalarlos con `pip install cryptography requests pymodbus`).
  * Se requiere el archivo de clave pública del cliente (`public.pem`) en el mismo directorio.
  * Se requiere el archivo de certificado SSL del servidor (`cert.pem`) en el mismo directorio.

### Prerrequisitos de servidor_final.py

  * Se utilizó Python 3.13
  * El módulo `flask` debe estar instalado. (Puedes instalarlo con `pip install flask`).
  * Se requiere tener los archivos de certificado SSL en el mismo directorio:
    * `cert.pem`: Certificado del servidor.
    * `key.pem`: Clave privada del servidor.
  
### Prerrequisitos de cliente_consulta.py

  * Se utilizó Python 3.13
  * El módulo `requests` debe estar instalado. (Puedes instalarlo con `pip install requests`).
  * Se requiere el archivo de certificado SSL del servidor (`cert.pem`) en el mismo directorio.

### Creación de claves

Si no tienes estos archivos, puedes generarlos con los siguientes comandos en tu terminal:
1. **Generar `private.pem`:**
   ```bash
   openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048
   ```

2. **Extraer `public.pem`:**
   ```bash
    openssl rsa -pubout -in private.pem -out public.pem
    ```
   
3. **Generar `cert.pem` y `key.pem`:**
    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -config san.cnf
    ```


## 2\. Ejecución del Proyecto

Para el correcto funcionamiento del proyecto, se debe seguir el siguiente orden de ejecución:

1. **Ejecuta servidor_final.py:**
   ```bash
   python servidor_final.py
   ```
2. **Ejecuta cliente_consulta.py:** 
   ```bash
    python cliente_consulta.py
    ```

3. **Ejecuta servidor_intermedio.py:**
   ```bash
    python servidor_intermedio.py
    ```

4. **Ejecuta cliente_sensor:**
   ```bash
   ./cliente_sensor
   ```
