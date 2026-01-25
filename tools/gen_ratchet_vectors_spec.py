
import json
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

# Spec Primitives

def b64u_dec(s: str) -> bytes:
    """Decode unpadded base64url."""
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)

def b64u_enc(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def dh(priv: bytes, pub: bytes) -> bytes:
    priv_key = x25519.X25519PrivateKey.from_private_bytes(priv)
    pub_key = x25519.X25519PublicKey.from_public_bytes(pub)
    return priv_key.exchange(pub_key)

def hkdf_derive(input_key, info, length=32):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    ).derive(input_key)

def kdf_rk(rk, dh_out):
    combined = hkdf_derive(rk + dh_out, b"talos-double-ratchet-root", length=64)
    return combined[:32], combined[32:]

def kdf_ck(ck):
    mk = hkdf_derive(ck, b"talos-double-ratchet-message")
    next_ck = hkdf_derive(ck, b"talos-double-ratchet-chain")
    return mk, next_ck

def decrypt_aead(key, ciphertext, nonce, ad):
    cipher = ChaCha20Poly1305(key)
    return cipher.decrypt(nonce, ciphertext, ad)

class SpecSession:
    def __init__(self, name):
        self.name = name
        self.root_key = None
        self.ck_send = None
        self.ck_recv = None
        self.dh_priv = None 
        self.dh_pub = None
        self.dh_remote = None
        
        self.send_count = 0
        self.recv_count = 0
        self.prev_send_count = 0 
        
    def init_alice(self, alice_eph_priv, bob_spk_pub, bob_id_pub, bob_otk_pub=None):
        # dh_out = DH(ek_a, spk_b)
        dh1 = dh(alice_eph_priv, bob_spk_pub)
        # HKDF(dh1, "x3dh-init") => RK
        self.root_key = hkdf_derive(dh1, b"x3dh-init")
        
        # Initial sending chain (Alice)
        # dh_out = DH(ek_a, spk_b) -> Same because Alice reuses EK as first ratchet key
        dh2 = dh(alice_eph_priv, bob_spk_pub)
        self.root_key, self.ck_send = kdf_rk(self.root_key, dh2)
        
        # State
        self.dh_priv = alice_eph_priv
        # Alice knows Bob's ratchet key is SPK_B initially
        self.dh_remote = bob_spk_pub
        
    def init_bob(self, bob_spk_priv, alice_ek_pub, alice_id_pub):
        # dh_out = DH(spk_b, ek_a)
        dh1 = dh(bob_spk_priv, alice_ek_pub)
        self.root_key = hkdf_derive(dh1, b"x3dh-init")
        
        # Initial receiving chain (Bob)
        dh2 = dh(bob_spk_priv, alice_ek_pub) # Matches Alice's DH
        self.root_key, self.ck_recv = kdf_rk(self.root_key, dh2)
        
        self.dh_priv = bob_spk_priv
        self.dh_remote = alice_ek_pub
        
    def decrypt(self, header, ciphertext, nonce, ad):
        # Check Ratchet
        header_dh = b64u_dec(header["dh"])
        if header_dh != self.dh_remote:
            print(f"[{self.name}] Ratchet Step!")
            # DH Ratchet
            # 1. Update Recv Chain
            dh_recv = dh(self.dh_priv, header_dh)
            self.root_key, self.ck_recv = kdf_rk(self.root_key, dh_recv)
            self.dh_remote = header_dh
            self.recv_count = 0
            
            # NOTE: sending chain update happens when we SEND specific key, 
            # here we drift along with receive steps?
            # Standard Double Ratchet: Receiving a new key triggers update of Recv Chain.
            # It implies Bob's PREVIOUS DH key matches Alice's PREVIOUS remote.
            
            # Note: We are not implementing full skipped key logic here, just sequential valid.
            
        # Decrypt
        if self.ck_recv is None:
            raise Exception("No receiving chain key")
            
        mk, self.ck_recv = kdf_ck(self.ck_recv)
        self.recv_count += 1
        
        return decrypt_aead(mk, ciphertext, nonce, ad)

    def encrypt_step_update(self, new_ratchet_priv):
        # Manual ratchet update for sending if we are simulating Sender state
        # (Used when Validator simulates Bob sending Reply)
        
        # dh_send = DH(new_priv, remote_pub)
        dh_send = dh(new_ratchet_priv, self.dh_remote)
        self.root_key, self.ck_send = kdf_rk(self.root_key, dh_send)
        self.dh_priv = new_ratchet_priv
        self.send_count = 0
        

def main():
    print("Running Spec Validator...")
    vector_path = "contracts/test_vectors/sdk/ratchet/roundtrip_basic.json"
    
    with open(vector_path) as f:
        vec = json.load(f)
    
    print(f"Loaded {vec['title']}")
    
    alice_eph_priv = b64u_dec(vec["alice"]["ephemeral_private"])
    bob_spk_priv = b64u_dec(vec["bob"]["bundle_secrets"]["signed_prekey_private"])
    bob_spk_pub = b64u_dec(vec["bob"]["prekey_bundle"]["signed_prekey"])
    
    alice_id_pub = b64u_dec(vec["alice"]["identity_public"])
    bob_id_pub = b64u_dec(vec["bob"]["identity_public"])
    
    # Header 1 DH is Alice's ephemeral public
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    alice_ek = x25519.X25519PrivateKey.from_private_bytes(alice_eph_priv).public_key().public_bytes(
        encoding=Encoding.Raw, format=PublicFormat.Raw
    )
    
    # Init Sessions
    alice = SpecSession("Alice")
    alice.init_alice(alice_eph_priv, bob_spk_pub, bob_id_pub)
    
    bob = SpecSession("Bob")
    bob.init_bob(bob_spk_priv, alice_ek, alice_id_pub)
    
    # Verify Initial Root Key Match
    if alice.root_key != bob.root_key:
        print("ERROR: Root Key Mismatch!")
        exit(1)
    if alice.ck_send != bob.ck_recv:
        print("ERROR: Alice CK_Send != Bob CK_Recv")
        print(f"Alice: {b64u_enc(alice.ck_send)}")
        print(f"Bob:   {b64u_enc(bob.ck_recv)}")
        exit(1)
        
    print("X3DH Agreement: OK")
    
    for step in vec["steps"]:
        print(f"Verifying step {step['step']} ({step['action']})...")
        
        if step["action"] == "encrypt":
            # Just verify we can decrypt it with the RECEIVER
            receiver = bob if step["actor"] == "alice" else alice
            
            # If actor is Bob, he might have ratcheted sending chain using new key
            if step["actor"] == "bob":
                 if "ratchet_priv" in step:
                     new_priv = b64u_dec(step["ratchet_priv"])
                     # Update Bob's sending state (simulate the ratchet he did)
                     # Note: Bob does this *before* encrypting
                     sender = bob # sender is bob
                     # Does bob need to update his sending state? 
                     # The Validator checks if the RECEIVER (Alice) can decrypt.
                     # Alice receives header.
                     # But we can also check if Sender logic produces the right key.
                     # Let's perform the update on Sender (Bob)
                     bob.encrypt_step_update(new_priv)
            
            ct = b64u_dec(step["ciphertext"])
            nonce = b64u_dec(step["nonce"])
            aad = b64u_dec(step["aad"])
            header = step["header"]
            
            try:
                pt = receiver.decrypt(header, ct, nonce, aad)
                expected = b64u_dec(step["plaintext"])
                if pt != expected:
                    print(f"Decryption Mismatch! {pt} != {expected}")
                    exit(1)
                else:
                    print("Decryption OK")
            except Exception as e:
                print(f"Decryption Failed: {e}")
                import traceback
                traceback.print_exc()
                exit(1)
                
    print("Validation COMPLETE: All steps passed.")

if __name__ == "__main__":
    main()
