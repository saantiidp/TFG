# test_bike_oqs.py
import oqs

def roundtrip(kem_name: str):
    print(f"Testing {kem_name}")
    with oqs.KeyEncapsulation(kem_name) as alice:   # Desencapsuladora
        pk = alice.generate_keypair()
        with oqs.KeyEncapsulation(kem_name) as bob: # Encapsulador
            ct, ss_bob = bob.encap_secret(pk)
        ss_alice = alice.decap_secret(ct)
        assert ss_alice == ss_bob
        print("  OK -> shared secret length:", len(ss_alice))

for name in ("BIKE-L1", "BIKE-L3", "BIKE-L5"):
    roundtrip(name)
print("All good.")
