#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <thread>
#include <cstdint> // Para int16_t, int64_t
#include <cstdlib> // Para rand()
#include <ctime>   // Para srand()

// --- Librerías de Red (Socket) ---
// Para Windows
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
// Para Linux/macOS
#else
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#define SOCKET int
#define INVALID_SOCKET -1
#define SOCKET_ERROR -1
#define closesocket close
#endif

// --- Librerías de Criptografía (OpenSSL) ---
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/err.h>
#include <openssl/sha.h>

// ======================= CONFIGURACIÓN =======================
const char* SERVER_IP = "127.0.0.1"; // IP del servidor intermedio
const int SERVER_PORT = 12345;       // Puerto del servidor intermedio
const int SENSOR_ID = 101;           // ID de este sensor
const char* PRIVATE_KEY_FILE = "private.pem"; // Clave privada para firmar los datos
// =============================================================

// Estructura de datos que se enviará.
// #pragma pack(push, 1) asegura que no haya padding y que la estructura
// tenga el tamaño exacto de la suma de sus miembros (22 bytes),
// coincidiendo con el formato que espera el servidor Python.
#pragma pack(push, 1)
struct SensorData {
    int16_t id;         // 2 bytes
    int64_t timestamp;  // 8 bytes
    float temperature;  // 4 bytes
    float pressure;     // 4 bytes
    float humidity;     // 4 bytes
};
#pragma pack(pop)

// Función para cargar la clave privada RSA desde un archivo .pem
RSA* cargarClavePrivada(const std::string& filename) {
    FILE* fp = fopen(filename.c_str(), "rb");
    if (!fp) {
        std::cerr << "Error: No se pudo abrir el archivo de la clave privada." << std::endl;
        return nullptr;
    }
    RSA* rsa = PEM_read_RSAPrivateKey(fp, NULL, NULL, NULL);
    fclose(fp);
    if (!rsa) {
        std::cerr << "Error: No se pudo leer la clave privada del archivo." << std::endl;
    }
    return rsa;
}

// Función para firmar los datos usando RSA y SHA256
bool firmarDatos(const SensorData& data, RSA* rsa_private_key, std::vector<unsigned char>& signature) {
    // 1. Calcular el hash SHA256 de los datos del sensor
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, &data, sizeof(data));
    SHA256_Final(hash, &sha256);

    // 2. Firmar el hash con la clave privada
    signature.resize(RSA_size(rsa_private_key));
    unsigned int signature_len;
    if (!RSA_sign(NID_sha256, hash, SHA256_DIGEST_LENGTH, signature.data(), &signature_len, rsa_private_key)) {
        std::cerr << "Error: No se pudieron firmar los datos." << std::endl;
        ERR_print_errors_fp(stderr);
        return false;
    }
    signature.resize(signature_len);
    return true;
}

int main() {
    // --- Inicialización de Sockets (solo para Windows) ---
    #ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "Fallo al inicializar Winsock" << std::endl;
        return 1;
    }
    #endif

    // Cargar la clave privada
    RSA* rsa_key = cargarClavePrivada(PRIVATE_KEY_FILE);
    if (!rsa_key) {
        return 1;
    }
    std::cout << "Clave privada cargada correctamente." << std::endl;

    // Inicializar generador de números aleatorios
    srand(time(0));

    // Bucle principal para enviar datos cada 5 segundos
    while (true) {
        // 1. Crear el paquete de datos del sensor
        SensorData data_packet;
        data_packet.id = SENSOR_ID;
        data_packet.timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count();
        data_packet.temperature = 20.0f + (rand() % 100) / 20.0f; // Temp entre 20.0 y 25.0
        data_packet.pressure = 1010.0f + (rand() % 50) / 10.0f;  // Presión entre 1010.0 y 1015.0
        data_packet.humidity = 40.0f + (rand() % 200) / 10.0f;   // Humedad entre 40.0 y 60.0

        // 2. Firmar los datos
        std::vector<unsigned char> signature;
        if (!firmarDatos(data_packet, rsa_key, signature)) {
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        // 3. Unir los datos del sensor y la firma en un solo paquete
        std::vector<unsigned char> full_packet(sizeof(data_packet));
        memcpy(full_packet.data(), &data_packet, sizeof(data_packet));
        full_packet.insert(full_packet.end(), signature.begin(), signature.end());

        // 4. Conectar y enviar los datos
        SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock == INVALID_SOCKET) {
            std::cerr << "Error al crear el socket" << std::endl;
            continue;
        }

        sockaddr_in serv_addr;
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(SERVER_PORT);
        inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr);

        if (connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
            std::cerr << "Error: Conexión fallida con el servidor." << std::endl;
        } else {
            send(sock, (const char*)full_packet.data(), full_packet.size(), 0);
            std::cout << "Paquete enviado (" << full_packet.size() << " bytes) -> "
                      << "ID: " << data_packet.id << ", "
                      << "Temp: " << data_packet.temperature << std::endl;
        }

        closesocket(sock);

        // Esperar 5 segundos antes del próximo envío
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }

    // Liberar recursos
    RSA_free(rsa_key);
    #ifdef _WIN32
    WSACleanup();
    #endif

    return 0;
}