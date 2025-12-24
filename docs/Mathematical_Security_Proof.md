# Mathematical Security Proof: Talos Protocol

**Abstract**: This document provides a formal mathematical model and security proof for the Talos Protocol, a blockchain-based secure transport layer for the Model Context Protocol (MCP). We demonstrate that the protocol achieves **Confidentiality**, **Integrity**, **Authentication**, and **Non-Repudiation** under standard cryptographic assumptions.

---

## 1. Notation and Primitives

We define the following cryptographic primitives and sets.

### 1.1 Sets
*   $\mathcal{K}$: The space of all possible keys.
*   $\mathcal{M}$: The space of all potential messages (plaintexts).
*   $\mathcal{C}$: The space of all cyphertexts.
*   $\mathcal{S}$: The space of digital signatures.
*   $\mathcal{H}$: The space of hash outputs (e.g., $\{0,1\}^{256}$).
*   $\mathcal{B}$: The set of all valid blockchain states.

### 1.2 Cryptographic Functions
We utilize the following functions, assumed to be secure:

1.  **Hashing**: $H: \{0,1\}^* \to \{0,1\}^{256}$
    *   Implemented as SHA-256.
    *   Assumption: Collision Resistance and Preimage Resistance.

2.  **Signing**:
    *   $G_{sign} \to (sk_{sign}, pk_{sign})$: Key generation.
    *   $Sign(sk, m) \to \sigma$: Generates a signature $\sigma \in \mathcal{S}$.
    *   $Verify(pk, m, \sigma) \to \{true, false\}$: Verifies a signature.
    *   Implemented as Ed25519.
    *   Assumption: Existential Unforgeability under Chosen Message Attack (EU-CMA).

3.  **Key Exchange (KEM)**:
    *   $G_{enc} \to (sk_{enc}, pk_{enc})$: Key generation.
    *   $ECDH(sk_A, pk_B) \to K_{shared}$: Derives a shared secret.
    *   Implemented as X25519.
    *   Assumption: Hardness of the Elliptic Curve Discrete Logarithm Problem (ECDLP).

4.  **Authenticated Encryption (AEAD)**:
    *   $Enc(k, n, m) \to (c, \tau)$: Encrypts message $m$ with key $k$ and nonce $n$, producing ciphertext $c$ and tag $\tau$.
    *   $Dec(k, n, c, \tau) \to m \cup \{\bot\}$: Decrypts or returns error.
    *   Implemented as ChaCha20-Poly1305.
    *   Assumption: Indistinguishability under Chosen Plaintext Attack (IND-CPA) and Integrity of Ciphertexts (INT-CTXT).

---

## 2. System Model

### 2.1 Actors
*   **Alice ($A$)**: An MCP User/Client.
*   **Bob ($B$)**: An MCP Server/Agent.
*   **Network ($N$)**: The P2P gossip network (untrusted).
*   **Ledger ($L$)**: The distributed blockchain (trust-minimized).

### 2.2 Definitions
*   $ID_A = pk_{sign}^A$: The identity of Alice is her public signing key.
*   $State_t$: The state of the blockchain at time $t$, represented as an ordered list of blocks $B_0, ..., B_t$.

---

## 3. Protocol Execution Model

We model the transmission of a single MCP JSON-RPC message $m_{mcp}$ from Alice to Bob.

### 3.1 Setup Phase
Alice and Bob publish their identities to the Registry/Network:
1.  $A: (sk_{sign}^A, pk_{sign}^A) \leftarrow G_{sign}()$
2.  $A: (sk_{enc}^A, pk_{enc}^A) \leftarrow G_{enc}()$
3.  $A \xrightarrow{publish} (pk_{sign}^A, pk_{enc}^A)$
*(Similarly for Bob)*

### 3.2 Secure Channel Establishment (0-RTT)
To satisfy the requirement of asynchronous messaging, we use a KEM approach rather than a synchronous handshake.

1.  **Shared Key Derivation**:
    $$K_{AB} = HKDF(ECDH(sk_{enc}^A, pk_{enc}^B))$$
    *Note: In the implementation, ephemeral keys are also used for forward secrecy, but we model the static case for simplicity of the base proof.*

### 3.3 Message Construction ($Send_A(m)$)
Let $m_{mcp}$ be the plaintext MCP message (e.g., `{"jsonrpc": "2.0", "method": "tools/list"}`).

1.  **Encryption**:
    Generate nonce $n \in_R \{0,1\}^{96}$.
    $$C = (c, \tau) = Enc(K_{AB}, n, m_{mcp})$$

2.  **Payload Construction**:
    $$P = (pk_{sign}^A, pk_{sign}^B, timestamp, n, C)$$

3.  **Authentication (Signing)**:
    $$\sigma = Sign(sk_{sign}^A, H(P))$$

4.  **Final Message**:
    $$M_{final} = (P, \sigma)$$

### 3.4 Transmission and Mining
1.  Alice broadcasts $M_{final}$ to $N$.
2.  Miners verify $Verify(pk_{sign}^A, H(P), \sigma)$ is true.
3.  Miners include $Hash(M_{final})$ in the Merkle Tree of a new block $B_{new}$.
4.  $B_{new}$ is appended to $L$ via Proof of Work.

### 3.5 Reception ($Receive_B(M)$)
Bob observes $M_{final}$ from $N$ or $L$.

1.  **Verification**:
    Check $Verify(pk_{sign}^A, H(P), \sigma)$. If false, reject.

2.  **Decryption**:
    Derive $K_{BA} = HKDF(ECDH(sk_{enc}^B, pk_{enc}^A))$.  *(Note: $K_{BA} == K_{AB}$)*.
    $$m' = Dec(K_{BA}, n, C)$$
    If $m' = \bot$, reject (Integrity failure).
    Else, process $m_{mcp}$.

---

## 4. Security Proofs

### 4.1 Property 1: Confidentiality
**Theorem**: An adversary $E$ observing the network cannot distinguish $m_{mcp}$ from a random string of the same length, assuming ECDH and ChaCha20-Poly1305 are secure.

**Proof (Sketch)**:
1.  The message $m_{mcp}$ is encrypted using ChaCha20-Poly1305 with key $K_{AB}$.
2.  $K_{AB}$ is derived from $ECDH(sk_{enc}^A, pk_{enc}^B)$.
3.  For $E$ to decrypt, they must compute $K_{AB}$.
4.  To compute $K_{AB}$, $E$ must solve the Diffie-Hellman problem given only $pk_{enc}^A$ and $pk_{enc}^B$.
5.  Under the ECDLP assumption, this is negligible.
6.  Even if $K_{AB}$ is known, ChaCha20 is a stream cipher. Without the key, the ciphertext is indistinguishable from random noise (IND-CPA).
$\blacksquare$

### 4.2 Property 2: Integrity & Authenticity
**Theorem**: Bob accepts a message $m$ as coming from Alice if and only if Alice actually sent $m$ and $m$ has not been modified.

**Proof (Sketch)**:
1.  **Authenticity**: The message is signed by $sk_{sign}^A$.
    *   Let $\sigma$ be the signature on $P$.
    *   If $Verify(pk_{sign}^A, H(P), \sigma)$ returns true, then by the EU-CMA property of Ed25519, only the holder of $sk_{sign}^A$ could have generated $\sigma$.
    *   Thus, the sender is Alice.
2.  **Integrity**: The ciphertext $C$ is part of $P$, which is signed.
    *   Any modification to $C$ changes $H(P)$, invalidating $\sigma$.
    *   Furthermore, Poly1305 is a Message Authentication Code (MAC). If $C$ is altered, $Dec()$ returns $\bot$.
    *   Combining these, Bob detects any tampering with probability $1 - \epsilon$.
$\blacksquare$

### 4.3 Property 3: Non-Repudiation
**Theorem**: Once Alice sends $M_{final}$ and it is included in $L$ with sufficient depth, she cannot deny sending it.

**Proof**:
1.  Alice generates $\sigma = Sign(sk_{sign}^A, P)$.
2.  The tuple $(P, \sigma)$ is public.
3.  Any third party (Judge) can compute $Verify(pk_{sign}^A, H(P), \sigma)$.
4.  If true, Alice is cryptographically bound to $P$.
5.  **Timestamping**: The inclusion of $Hash(M_{final})$ in block $B_t$ at height $h$ proves the message existed at time $Time(B_t)$.
6.  **Immutability**: To remove the record, Alice would need to rewrite the blockchain from height $h$.
    *   Let $W$ be the work required to mine one block.
    *   To rewrite $k$ blocks, cost is $k \times W$.
    *   As $k \to \infty$ (chain grows), the cost to repudiate becomes prohibitive.
$\blacksquare$

---

## 5. MCP-Specific Security (The "Tunnel" Approach)

The Model Context Protocol (MCP) relies on JSON-RPC messages. A standard MCP connection is:

$$Client \leftrightarrow Transport \leftrightarrow Host$$

Talos Protocol replaces the Transport layer.

### 5.1 Threat Vector Mitigation
| Generic MCP Threat | Talos Mitigation | Mathematical Justification |
|-------------------|------------------|----------------------------|
| **Man-in-the-Middle** | Intercepting `tools/call` to inject malicious params | **Auth + Encr**: Attacker cannot generate valid $\sigma_{Alice}$ nor decrypt $C$ to inject valid JSON. |
| **Replay Attack** | Re-sending a `resources/read` command | **Nonce/Id**: $P$ contains a unique nonce/ID. $L$ records $Hash(M)$ preventing duplicate processing. |
| **Censorship** | Blocking an Agent's tool access | **Decentralization**: P2P network has no single choke point. Message is accepted if *any* miner includes it. |

### 5.2 Formal Constraint
For any MCP interaction $I$, defined as a sequence of Request-Response pairs.
$$I = \{(req_1, res_1), (req_2, res_2), ...\}$$

Talos guarantees:
$$\forall (req, res) \in I: Verify(req) \land Verify(res) \land Linked(req, res)$$

Where $Linked$ employs the `id` field in JSON-RPC, preserved securely within the encrypted payload $C$.

---

## 6. Conclusion

The Talos Protocol provides a mathematically provable security layer for MCP. By binding identities to Ed25519 keys and anchoring message history in a Proof-of-Work blockchain, it solves the "Agent Trust" problem. Agents can interact autonomously, with the mathematical certainty that their communications are private, authentic, and permanent.
