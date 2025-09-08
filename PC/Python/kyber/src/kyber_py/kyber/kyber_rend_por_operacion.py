import time
import csv
import statistics
from default_parameters import Kyber512, Kyber768, Kyber1024

# ====================
# Configuración
# ====================
ITERATIONS = 1000
OPS_CSV = "kyber_python_ops.csv"

def run_performance_tests(impl_cls, iterations):
    """Devuelve listas de tiempos (ms) para keygen/enc/dec y total."""
    keygen, encaps, decaps, total = [], [], [], []

    for _ in range(iterations):
        # Keygen
        t0 = time.time()
        pk, sk = impl_cls.keygen()
        keygen.append((time.time() - t0) * 1000.0)

        # Encaps
        t0 = time.time()
        K, c = impl_cls.encaps(pk)
        encaps.append((time.time() - t0) * 1000.0)

        # Decaps
        t0 = time.time()
        _ = impl_cls.decaps(sk, c)
        decaps.append((time.time() - t0) * 1000.0)

        # Total
        total.append(keygen[-1] + encaps[-1] + decaps[-1])

    return keygen, encaps, decaps, total

def ms_mean_std(xs):
    mean = sum(xs)/len(xs)
    std  = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return mean, std

def main():
    versions = [
        (Kyber512, "Kyber512"),
        (Kyber768, "Kyber768"),
        (Kyber1024,"Kyber1024")
    ]

    with open(OPS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Version", "Operation", "Iteration", "Time (ms)"])

        for cls, vname in versions:
            print(f"\n>> Ejecutando {vname} con {ITERATIONS} iteraciones...")
            k, e, d, t = run_performance_tests(cls, ITERATIONS)

            mk, sk = ms_mean_std(k)
            me, se = ms_mean_std(e)
            md, sd = ms_mean_std(d)
            mt, st = ms_mean_std(t)

            print(f"   Keygen : {mk:.3f} ± {sk:.3f} ms")
            print(f"   Encaps : {me:.3f} ± {se:.3f} ms")
            print(f"   Decaps : {md:.3f} ± {sd:.3f} ms")
            print(f"   Total  : {mt:.3f} ± {st:.3f} ms")

            for i in range(ITERATIONS):
                w.writerow([vname, "Keygen", i+1, k[i]])
                w.writerow([vname, "Encaps", i+1, e[i]])
                w.writerow([vname, "Decaps", i+1, d[i]])
                w.writerow([vname, "Total",  i+1, t[i]])

    print(f"\nGuardado CSV por operación: {OPS_CSV}")
    print("Usa ahora plot_kyber_python_por_operacion.py para graficar.")

if __name__ == "__main__":
    main()
