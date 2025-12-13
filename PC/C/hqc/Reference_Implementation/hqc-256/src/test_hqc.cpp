#include <iostream>
#include <chrono>
#include <fstream>
#include <vector>
#include "api.h"  // asegúrate de que sea compatible con C++, usa extern "C" si es C puro
#include "parameters.h"  // Asegúrate de que este archivo contenga las definiciones correctas

int main() {
    const int NTESTS = 1000;
    std::vector<double> keygen_times, enc_times, dec_times, total_times;

    for (int i = 0; i < NTESTS; ++i) {
        unsigned char pk[PUBLIC_KEY_BYTES];
        unsigned char sk[SECRET_KEY_BYTES];
        unsigned char ct[CIPHERTEXT_BYTES];
        unsigned char ss_enc[SHARED_SECRET_BYTES];
        unsigned char ss_dec[SHARED_SECRET_BYTES];

        auto start = std::chrono::high_resolution_clock::now();
        auto t1 = std::chrono::high_resolution_clock::now();
        crypto_kem_keypair(pk, sk);
        auto t2 = std::chrono::high_resolution_clock::now();
        crypto_kem_enc(ct, ss_enc, pk);
        auto t3 = std::chrono::high_resolution_clock::now();
        crypto_kem_dec(ss_dec, ct, sk);
        auto t4 = std::chrono::high_resolution_clock::now();

        keygen_times.push_back(std::chrono::duration<double, std::milli>(t2 - t1).count());
        enc_times.push_back(std::chrono::duration<double, std::milli>(t3 - t2).count());
        dec_times.push_back(std::chrono::duration<double, std::milli>(t4 - t3).count());
        total_times.push_back(std::chrono::duration<double, std::milli>(t4 - t1).count());
    }

    std::ofstream out("hqc_cpp_rendimiento.csv");
    out << "Iteration,Keygen Time (ms),Enc Time (ms),Dec Time (ms),Total Time (ms)\n";
    for (size_t i = 0; i < keygen_times.size(); ++i) {
        out << i << "," << keygen_times[i] << "," << enc_times[i] << "," << dec_times[i] << "," << total_times[i] << "\n";
    }
    out.close();

    std::cout << "Rendimiento exportado a hqc_cpp_rendimiento.csv (milisegundos)\n";
    return 0;
}
