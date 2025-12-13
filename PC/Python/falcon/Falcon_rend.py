# Falcon_rend.py — runner por operación (exporta CSV largo)
import falcon as falcon
import time
import csv
import statistics

# =========================
# Configuración
# =========================
REPETICIONES = 1000          # por cada versión y tipo de mensaje
VERSIONES = [256, 512, 1024] # tamaños n de Falcon
SMALL_LEN = 31               # bytes (mensaje corto)
LARGE_LEN = 1000             # bytes (mensaje largo)
OPS_CSV = "falcon_python_ops.csv"

def medir_rendimiento(tam_mensaje: int, n: int, repeticiones: int):
    """Devuelve (listas en ms) keygen, sign, verify y totales (ms), y verificación booleana."""
    keygen_ms, sign_ms, verify_ms, total_ms, verif_ok = [], [], [], [], []

    for _ in range(repeticiones):
        # Keygen (ms)
        t0 = time.perf_counter()
        sk = falcon.SecretKey(n)
        pk = falcon.PublicKey(sk)
        k_ms = (time.perf_counter() - t0) * 1000.0
        keygen_ms.append(k_ms)

        # Mensaje
        msg = bytes(tam_mensaje)

        # Sign (ms)
        t0 = time.perf_counter()
        sig = sk.sign(msg)
        s_ms = (time.perf_counter() - t0) * 1000.0
        sign_ms.append(s_ms)

        # Verify (ms)
        t0 = time.perf_counter()
        ok = pk.verify(msg, sig)
        v_ms = (time.perf_counter() - t0) * 1000.0
        verify_ms.append(v_ms)
        verif_ok.append(ok)

        total_ms.append(k_ms + s_ms + v_ms)

    return keygen_ms, sign_ms, verify_ms, total_ms, all(verif_ok)

def ms_mean_std(xs):
    mean = sum(xs)/len(xs)
    std  = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return mean, std

def main():
    # CSV largo por operación
    with open(OPS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Version", "Operation", "Message", "Iteration", "Time (ms)"])

        for n in VERSIONES:
            for label_msg, mlen in [("small", SMALL_LEN), ("large", LARGE_LEN)]:
                k, s, v, tot, ok = medir_rendimiento(mlen, n, REPETICIONES)

                mk, sk = ms_mean_std(k)
                ms_, ss_ = ms_mean_std(s)
                mv, sv = ms_mean_std(v)
                mt, st = ms_mean_std(tot)

                print(f"\nFalcon n={n} | msg={label_msg}")
                print(f"  Keygen : {mk:.3f} ± {sk:.3f} ms")
                print(f"  Sign   : {ms_:.3f} ± {ss_:.3f} ms")
                print(f"  Verify : {mv:.3f} ± {sv:.3f} ms")
                print(f"  Total  : {mt:.3f} ± {st:.3f} ms")
                print(f"  Verificación OK: {ok}")

                for i in range(REPETICIONES):
                    w.writerow([f"Falcon{n}", "Keygen", "-",      i+1, k[i]])
                    w.writerow([f"Falcon{n}", "Sign",   label_msg, i+1, s[i]])
                    w.writerow([f"Falcon{n}", "Verify", label_msg, i+1, v[i]])
                    w.writerow([f"Falcon{n}", "Total",  label_msg, i+1, tot[i]])

    print(f"\nGuardado CSV por operación: {OPS_CSV}")
    print("Ahora ejecuta: python plot_falcon_python_por_operacion.py")

if __name__ == "__main__":
    main()
