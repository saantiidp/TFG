import time
from Dilithium.default_parameters import Dilithium2, Dilithium3, Dilithium5

def run_performance_tests(dilithium_instance, iterations):
    # Variables para acumular los tiempos
    total_keygen_time = 0
    total_sign_time_small = 0
    total_sign_time_large = 0
    total_verify_time_small = 0
    total_verify_time_large = 0

    small_message = b"Your message signed by Dilithium"  # Mensaje pequeño
    large_message = b"A" * 1000  # Mensaje grande de 1,000 bytes (aproximadamente 10 KB)

    for _ in range(iterations):
        # Medir el tiempo de generación de claves
        start_time = time.time()
        pk, sk = dilithium_instance.keygen()
        total_keygen_time += time.time() - start_time

        # Medir el tiempo de firma para el mensaje pequeño
        start_time = time.time()
        sig_small = dilithium_instance.sign(sk, small_message)
        total_sign_time_small += time.time() - start_time

        # Medir el tiempo de firma para el mensaje grande
        start_time = time.time()
        sig_large = dilithium_instance.sign(sk, large_message)
        total_sign_time_large += time.time() - start_time

        # Medir el tiempo de verificación para el mensaje pequeño
        start_time = time.time()
        dilithium_instance.verify(pk, small_message, sig_small)
        total_verify_time_small += time.time() - start_time

        # Medir el tiempo de verificación para el mensaje grande
        start_time = time.time()
        dilithium_instance.verify(pk, large_message, sig_large)
        total_verify_time_large += time.time() - start_time

    # Resultados promedio
    print(f"\nResultados para {dilithium_instance.__class__.__name__}:")
    print(f"Tiempo promedio de generación de claves: {(total_keygen_time *1000) / iterations:.6f} ms")
    print(f"Tiempo promedio de firma (mensaje pequeño, {len(small_message)} bytes): {(total_sign_time_small *1000) / iterations:.6f} ms")
    print(f"Tiempo promedio de verificación (mensaje pequeño, {len(small_message)} bytes): {(total_verify_time_small *1000) / iterations:.6f} ms")
    print(f"\nTiempo promedio de firma (mensaje grande, {len(large_message)} bytes): {(total_sign_time_large *1000)/ iterations:.6f} ms")
    print(f"Tiempo promedio de verificación (mensaje grande, {len(large_message)} bytes): {(total_verify_time_large*1000) / iterations:.6f} ms")

def main():
    iterations = 10  # Número de iteraciones para las pruebas de rendimiento

    # Solicitar al usuario que elija el conjunto de parámetros de Dilithium
    print("Selecciona la opción de Dilithium:")
    print("1. Dilithium2")
    print("2. Dilithium3")
    print("3. Dilithium5")
    
    choice = input("Ingrese opción (1/2/3): ")

    # Seleccionar la instancia de Dilithium basada en la elección
    if choice == '1':
        dilithium_instance = Dilithium2
        print("Hola ", dilithium_instance)
    elif choice == '2':
        dilithium_instance = Dilithium3
    elif choice == '3':
        dilithium_instance = Dilithium5
    else:
        print("Opción no válida. Saliendo.")
        return

    # Ejecutar las pruebas de rendimiento
    run_performance_tests(dilithium_instance, iterations)

if __name__ == "__main__":
    main()
