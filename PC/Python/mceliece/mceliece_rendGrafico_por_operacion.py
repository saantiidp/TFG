#!/usr/bin/env python3
import time, csv, statistics, sys
import oqs

# Iteraciones (o pásalo por CLI, p.ej. 100)
ITER = int(sys.argv[1]) if len(sys.argv) > 1 else 100
CSV_OUT = "mceliece_rendimiento.csv"

# Orden preferido (se filtrará por disponibilidad real)
PREFERRED_ALGS = [
    "Classic-McEliece-348864",  "Classic-McEliece-348864f",
    "Classic-McEliece-460896",  "Classic-McEliece-460896f",
    "Classic-McEliece-6688128", "Classic-McEliece-6688128f",
    "Classic-McEliece-6960119", "Classic-McEliece-6960119f",
    "Classic-McEliece-8192128", "Classic-McEliece-8192128f",
]

def _enabled_kems():
    # Tu build expone esta: get_enabled_kem_mechanisms
    if hasattr(oqs, "get_enabled_kem_mechanisms"):
        return list(oqs.get_enabled_kem_mechanisms())
    # Compatibilidad con otras builds
    if hasattr(oqs, "get_enabled_KEM_mechanisms"):
        return list(oqs.get_enabled_KEM_mechanisms())
    raise RuntimeError("No encuentro el listado de KEMs en 'oqs'.")

def ms(x): return x * 1000.0

def discover_mceliece_algs():
    enabled = set(_enabled_kems())
    prefer = [a for a in PREFERRED_ALGS if a in enabled]
    if prefer:
        return prefer
    others = sorted([a for a in enabled if "McEliece" in a])
    if not others:
        raise RuntimeError("No hay variantes Classic McEliece disponibles en tu liboqs.")
    return others

def medir_alg(alg: str, n_iter: int):
    keygen, enc, dec, tot = [], [], [], []
    for _ in range(n_iter):
        with oqs.KeyEncapsulation(alg) as kem:
            t0 = time.perf_counter(); pk = kem.generate_keypair(); t1 = time.perf_counter()
            t_key = ms(t1 - t0)

            t0 = time.perf_counter(); ct, ss_b = kem.encap_secret(pk); t1 = time.perf_counter()
            t_enc = ms(t1 - t0)

            t0 = time.perf_counter(); ss_a = kem.decap_secret(ct); t1 = time.perf_counter()
            t_dec = ms(t1 - t0)

            if ss_a != ss_b:
                raise ValueError(f"Shared secret mismatch en {alg}")

        keygen.append(t_key); enc.append(t_enc); dec.append(t_dec)
        tot.append(t_key + t_enc + t_dec)
    return keygen, enc, dec, tot

def resumen(xs):
    mu = sum(xs)/len(xs)
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return mu, sd

def main():
    algs = discover_mceliece_algs()
    print("[*] Variantes McEliece detectadas:", ", ".join(algs))

    with open(CSV_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Algoritmo","Iteracion",
                    "Tiempo_Generacion_Claves","Tiempo_Encapsulacion",
                    "Tiempo_Decapsulacion","Tiempo_Total"])
        for alg in algs:
            k,e,d,t = medir_alg(alg, ITER)
            mk,sk = resumen(k); me,se = resumen(e); md,sd = resumen(d); mt,st = resumen(t)
            print(f"\n{alg}  n={ITER}")
            print(f"  Keygen: {mk:.3f} ± {sk:.3f} ms")
            print(f"  Encaps: {me:.3f} ± {se:.3f} ms")
            print(f"  Decaps: {md:.3f} ± {sd:.3f} ms")
            print(f"  Total : {mt:.3f} ± {st:.3f} ms")
            for i in range(ITER):
                w.writerow([alg, i+1,
                            f"{k[i]:.6f}", f"{e[i]:.6f}",
                            f"{d[i]:.6f}", f"{t[i]:.6f}"])
    print(f"\n[OK] CSV guardado: {CSV_OUT}")

if __name__ == "__main__":
    main()
