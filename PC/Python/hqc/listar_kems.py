
import oqs

print("KEMs habilitados:")
for kem in oqs.get_enabled_kem_mechanisms():
    print("-", kem)
