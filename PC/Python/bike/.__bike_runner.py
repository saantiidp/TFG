import sys, time
try:
    import oqs
except Exception as e:
    print("IMPORT_ERROR", str(e))
    sys.exit(12)

if len(sys.argv) < 3:
    print("USAGE_ERROR")
    sys.exit(13)

level = sys.argv[1]   # L1, L3, L5
iters = int(sys.argv[2])

name_map = {"L1":"BIKE-L1", "L3":"BIKE-L3", "L5":"BIKE-L5"}
if level not in name_map:
    print("LEVEL_ERROR")
    sys.exit(14)

alg = name_map[level]

# Bucle de KEM
for _ in range(iters):
    with oqs.KeyEncapsulation(alg) as c:
        pk = c.generate_keypair()
        with oqs.KeyEncapsulation(alg) as s:
            ct, ss_s = s.encap_secret(pk)
        ss_c = c.decap_secret(ct)
        if ss_c != ss_s:
            print("MISMATCH")
            sys.exit(15)

print("OK")
