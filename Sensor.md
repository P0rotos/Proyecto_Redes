
# Guía de Compilación y Ejecución del Cliente Sensor

Este documento contiene los pasos para compilar y ejecutar el cliente C++ (`cliente_sensor.cpp`) del proyecto.

## 1\. Prerrequisitos

Antes de compilar, asegúrate de tener instalado lo siguiente en tu sistema:

  * Un compilador de C++, como **g++**.
  * La librería de desarrollo de **OpenSSL**. En sistemas basados en Debian/Ubuntu puedes instalarla con `sudo apt install libssl-dev`. En MSYS2/MinGW, puedes usar `pacman -S mingw-w64-ucrt-x86_64-openssl`.

-----

## 2\. Generación de Claves RSA 🔑

El cliente necesita un archivo de clave privada (`private.pem`) para firmar los datos. [cite\_start]El servidor intermedio necesitará la clave pública (`public.pem`) correspondiente para verificar esa firma[cite: 41, 42].

Si no tienes estos archivos, puedes generarlos con los siguientes comandos en tu terminal:

1.  **Generar clave privada:**
    ```bash
    openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048
    ```
2.  **Extraer clave pública:**
    ```bash
    openssl rsa -pubout -in private.pem -out public.pem
    ```

Asegúrate de que el archivo **`private.pem`** esté en la misma carpeta donde compilarás y ejecutarás el cliente.

-----

## 3\. Compilación ⚙️

Abre una terminal en el directorio que contiene el archivo **`cliente_sensor.cpp`** y **`private.pem`**.

### En Linux o macOS

Usa el siguiente comando para compilar:

```bash
g++ cliente_sensor.cpp -o cliente_sensor -lssl -lcrypto
```

### En Windows (con MinGW/MSYS2)

Usa el siguiente comando para compilar:

```bash
g++ cliente_sensor.cpp -o cliente_sensor.exe -lws2_32 -lssl -lcrypto
```

  * **`-lws2_32`**: Es la librería de sockets de Windows, necesaria para la comunicación por red.

-----

## 4\. Ejecución ▶️

Para que el cliente funcione correctamente, el **servidor intermedio de Python (`servidor_intermedio.py`) debe estar en ejecución**, ya que el cliente intentará conectarse a él.

Una vez compilado, ejecuta el cliente con el siguiente comando:

### En Linux o macOS

```bash
./cliente_sensor
```

### En Windows

```bash
./cliente_sensor.exe
```

Verás mensajes en la consola indicando que la clave fue cargada y que los paquetes se están enviando al servidor cada 5 segundos.
