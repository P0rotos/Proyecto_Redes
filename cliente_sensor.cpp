#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <thread>
#include <cstdint>
#include <cstdlib>
#include <ctime>

// --- Librerías de Red (Socket) ---
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#define SOCKET int
#define INVALID_SOCKET -1
#define SOCKET_ERROR -1
#define closesocket close
#endif

// --- Librerías de Criptografía (OpenSSL - API Moderna EVP) ---
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/err.h>

// ======================= CONFIGURACIÓN =======================
const char* SERVER_IP = "127.0.0.1";
const int SERVER_PORT = 12345;
const int SENSOR_ID = 101;
const char* PRIVATE_KEY_FILE = "private.pem";
// =============================================================

#pragma pack(push, 1)
struct SensorData {
    int16_t id;
    int64_t timestamp;
    float temperature;
    float pressure;
    float humidity;
};
#pragma pack(pop)

// Función para cargar la clave privada como una estructura genérica EVP_PKEY
EVP_PKEY* cargarClavePrivada(const std::string& filename) {
    FILE* fp = fopen(filename.c_str(), "rb");
    if (!fp) {
        std::cerr << "Error: No se pudo abrir el archivo de la clave privada." << std::endl;
        return nullptr;
    }
    EVP_PKEY* pkey = PEM_read_PrivateKey(fp, NULL, NULL, NULL);
    fclose(fp);
    if (!pkey) {
        std::cerr << "Error: No se pudo leer la clave privada del archivo." << std::endl;
    }
    return pkey;
}

// Función para firmar datos usando la API moderna EVP
bool firmarDatos(const SensorData& data, EVP_PKEY* pkey, std::vector<unsigned char>& signature) {
    EVP_MD_CTX* md_ctx = EVP_MD_CTX_new();
    if (!md_ctx) {
        return false;
    }

    // Inicializa la operación de firma con hash SHA256
    if (EVP_DigestSignInit(md_ctx, NULL, EVP_sha256(), NULL, pkey) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        return false;
    }

    // Proporciona los datos a ser firmados (la API se encarga del hashing)
    if (EVP_DigestSignUpdate(md_ctx, &data, sizeof(data)) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        return false;
    }

    // Finaliza la firma para obtener el tamaño de la firma
    size_t signature_len;
    if (EVP_DigestSignFinal(md_ctx, NULL, &signature_len) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        return false;
    }

    signature.resize(signature_len);

    // Finaliza la firma y obtiene la firma real
    if (EVP_DigestSignFinal(md_ctx, signature.data(), &signature_len) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        return false;
    }
    
    signature.resize(signature_len);
    EVP_MD_CTX_free(md_ctx);
    return true;
}


int main() {
    #ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "Fallo al inicializar Winsock" << std::endl;
        return 1;
    }
    #endif

    // Cargar la clave privada
    EVP_PKEY* pkey = cargarClavePrivada(PRIVATE_KEY_FILE);
    if (!pkey) {
        return 1;
    }
    std::cout << "Clave privada cargada correctamente." << std::endl;

    srand(time(0));

    while (true) {
        SensorData data_packet;
        data_packet.id = SENSOR_ID;
        data_packet.timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count();
        data_packet.temperature = 20.0f + (rand() % 100) / 20.0f;
        data_packet.pressure = 1010.0f + (rand() % 50) / 10.0f;
        data_packet.humidity = 40.0f + (rand() % 200) / 10.0f;

        std::vector<unsigned char> signature;
        if (!firmarDatos(data_packet, pkey, signature)) {
            std::cerr << "Error al firmar los datos." << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        std::vector<unsigned char> full_packet(sizeof(data_packet));
        memcpy(full_packet.data(), &data_packet, sizeof(data_packet));
        full_packet.insert(full_packet.end(), signature.begin(), signature.end());

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
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }

    // Liberar recursos de la clave
    EVP_PKEY_free(pkey);
    #ifdef _WIN32
    WSACleanup();
    #endif

    return 0;
}