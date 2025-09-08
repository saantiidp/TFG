#!/usr/bin/env python3
import time, csv, statistics
import oqs  # Open Quantum Safe (pyoqs)

# ===== Config =====
ITER = 1000
ALGS = ["HQC-128", "HQC-256"]           # añade "HQC-192" si lo usas
CSV_OUT = "hqc_rendimiento.csv"         # con columnas por operación

def ms(x): return x * 1000.0

def medir_alg(alg: str, n_iter: int):
    keygen, enc, dec, tot = [], [], [], []
    for _ in range(n_iter):
        with oqs.KeyEncapsulation(alg) as kem:
            # Keygen
            t0 = time.perf_counter(); pk = kem.generate_keypair(); t1 = time.perf_counter()
            t_key = ms(t1 - t0)
            # Encaps
            t0 = time.perf_counter(); ct, ss_b = kem.encap_secret(pk); t1 = time.perf_counter()
            t_enc = ms(t1 - t0)
            # Decaps
            t0 = time.perf_counter(); ss_a = kem.decap_secret(ct); t1 = time.perf_counter()
            t_dec = ms(t1 - t0)
            assert ss_a == ss_b
        keygen.append(t_key); enc.append(t_enc); dec.append(t_dec)
        tot.append(t_key + t_enc + t_dec)
    return keygen, enc, dec, tot

def resumen(xs):
    mu = sum(xs)/len(xs)
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return mu, sd

def main():
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Algoritmo","Iteracion",
                    "Tiempo_Generacion_Claves","Tiempo_Encapsulacion",
                    "Tiempo_Decapsulacion","Tiempo_Total"])
        for alg in ALGS:
            k,e,d,t = medir_alg(alg, ITER)
            mk,sk = resumen(k); me,se = resumen(e); md,sd = resumen(d); mt,st = resumen(t)
            print(f"\n{alg}  n={ITER}")
            print(f"  Keygen: {mk:.3f} ± {sk:.3f} ms")
            print(f"  Encaps: {me:.3f} ± {se:.3f} ms")
            print(f"  Decaps: {md:.3f} ± {sd:.3f} ms")
            print(f"  Total : {mt:.3f} ± {st:.3f} ms")
            for i in range(ITER):
                w.writerow([alg, i+1, f"{k[i]:.6f}", f"{e[i]:.6f}", f"{d[i]:.6f}", f"{t[i]:.6f}"])
    print(f"\n[OK] CSV guardado: {CSV_OUT}")

if __name__ == "__main__":
    main()
