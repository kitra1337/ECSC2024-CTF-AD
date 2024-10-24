# CookingNonna

| Service     | Name                                                 |
| :---------- | :----------------------------------------------------|
| Authors     | Giulia Martino <@Giulia>, Matteo Rossi <@mr96>       |
| Stores      | 1                                                    |
| Categories  | pwn, crypto                                          |
| Port        | TCP 2222                                             |
| FlagIds     | store1: [username, vault, recipe]                    |
| Checkers    | [store1](/checkers/CookingNonna/checker.py)          |

## Description
The program is a secret recipe manager that allows users to sign up, manage their vaults, and manage recipes inside their vaults. The program uses directory file descriptors to prevent common path traversal attacks, as well as making it easier to open relative files and folders.

The checker registers users and saves the flag inside recipes' descriptions. The attacker needs to find a way to read flag files.

## Vulnerabilities

#### Vuln 1/2 (pwn): leaked fd when login fails + null-byte overflow

*Bug 1*: when a user attempts to sign in, a "dfd" (directory file descriptor) for the user's directory (parent of vaults) is opened:

```c
// main.c: line 113
dfd = openat(data_fd, digest, O_DIRECTORY);
if (dfd < 0) {
    error("Error opening user directory");
    return;
}
```

This is also where the password of the user is stored:

```c
// main.c: line 119
fd = openat(dfd, "password", O_RDONLY);
if (!fd) {
    error("Error opening password file");
    goto err;
}
```

However, if the login fails, the "dfd" is not closed:

```c
// main.c: line 153
if (memcmp(response, hexnonce, sizeof(hexnonce))) {
    warn("Login failed");
    return;
}
```

This leads to a file descriptor leak (in the classic non-exploitation sense).

*Bug 2*: the `read_line` function which is used extensively throughout the program, has a null-byte overflow vulnerability, because it always appends a null-byte to the end of the buffer, even if the buffer is full.

```c
// util.c: line 108
ssize_t read_line(int fd, char *buf, size_t size) {
    if (size == 0) return -1;

    size_t count = 0;
    while (count < size) {
        ssize_t res = read(fd, buf + count, 1);
        if (res <= 0) {
            if (res == 0) break; // End of file
            return -1; // Error
        }
        if (buf[count] == '\n') break;
        count++;
    }
    buf[count] = '\0';
    return count;
}
```

Even though there are many potential null-byte overflow attack vectors, only one should be exploitable for something relevant. All open vaults are stored in a global "open_vaults" array:

```c
// vault.c: line 32
struct vault open_vaults[MAX_OPEN_VAULTS];
```

This array is a list of `struct vault`:

```c
// vault.h: line 11
struct vault {
    int fd;
    char id[ID_LEN];
    char name[MAX_VAULT_NAME];
};
```

The first member is the directory file descriptor of the vault. Inside this directory, all recipes should be stored as files. The last member of the struct is an inline buffer for the name of the vault.

As such, we have a null-byte overflow from one vault into another vault's fd. There are a few caveats. 

First, we know that we have a leak of another user's user directory fd, but this is a vault directory fd. However, a password and a recipe is stored in roughly the same format on disk, namely in len-data pairs. As such, if we could overwrite a vault's fd to be another user's user fd, we could list the recipes to leak the password, as only the first field inside a recipe is shown upon listing, which would be the password.

The second caveat is the ordering of the vaults. To make the overflow happen, we need to set the name, which can only be done on creation. As such, we need to open/create two vaults. Then we close the first one to free the first slot in the list. And then we create a new vault with a name that is exactly the size of a vault's name. This will overflow a single null-byte into the second vault.

Now, the last caveat is that we cannot get fd = 0, as this is stdin. However, if we make enough failed attempts, then eventually, the user's fd will be 0x100. As such, if the second vault's fd is 0x101, and we overflow a null-byte, it will become 0x100.

Finally, we simply open the second vault and list the recipes. This will interpreter the password as a recipe, and the name of the "recipe" will be the password.

Exploitation can be prevented by just fixing the overflow in `read_line`, and read one character less. It is not needed to patch the leaked fd bug in order to prevent exploitation.

#### Vuln 3 (crypto): Login bypass
The login system works with a challenge-response mechanism. The user is asked to provide their username, then an encrypted token is returned by the server. The token is encrypted using (a derivation of) the user's password: by knowing it, the legitimate user can decrypt the token, read the nonce inside it and send it back. If the nonce given to the server is correct, the user is allowed to login.

How does the encryption work? It is a custom block cipher used in ECB mode, with blocks of 256 bits. The encrypted data is a JSON of the form `{"username": username, "nonce": nonce}`, with the nonce being 64 hex digits. It is padded to a multiple of 32 bytes using the standard PKCS#7 padding scheme.

The code (in python for better readability) of the block cipher is given below:
```python
p = 18446744073709551653
ROUNDS = 16

def F(x, t):
    return (pow(x, 5, p) + t*pow(x, 3, p) + 11068046444225730992*pow(t, 2, p)*x) % p

def encrypt(pt, username, password):
    ct = bytes.fromhex(pt)
    blocks = [ct[i:i+32] for i in range(0, len(ct), 32)]
    k = int(sha256(password).digest().hex()[:16], 16)
    c = [sha256(username).digest()]
    cts = []

    for _ in range(2*ROUNDS-1):
        c.append(sha256(c[-1]).digest())

    for x in blocks:
        state = [int.from_bytes(x[i:i+8], "big") for i in range(0,len(x),8)]
        for i in range(ROUNDS):
            state[1] += F(state[0] + k + int(c[2*i].hex(), 16), 2*(i+1))
            state[1] %= p
            state[3] += F(state[2] + k + int(c[2*i+1].hex(), 16), 2*(i+1)+1)
            state[3] %= p
            state = state[1:] + state[:1]
        cts.append(b"".join([int.to_bytes(s, 8, "big") for s in state]))
    return b"".join(cts)
```

The cipher is computing a polynomial with relatively low degree on the plaintext over `F_p`, with `p` being 64 bit long, and the full state of the cipher is composed by four 64-bit chunks in a Feistel-like structure.

The crucial observation is that `k` does not change between the rounds, that is, there is no key schedule.

Denoting with `E(k, p)` the encryption under the key `k` of the plaintext `p`, suppose to have two known plaintexts, `p1` and `p2`, with the corresponding ciphertexts `c1` and `c2`. If you compute the polynomials `E(x, p1) - c1` and `E(x, p2) - c2`, each of their components share (with high probability) `(x-k)` as a factor, where `k` is the used key. Computing the GCD of these two poynomials gives the key, that can be used to simulate a login.

In the challenge we do not have access of two full blocks of known plaintext, but the same technique works considering the 64-bit chunks of a single block. After the encryption, we can compute the GCD of a pair of the form `(E(x, p1)[i] - c1[i], E(x, p1)[j] - c1[j])` and retrieve the key.

This is theoretically doable, as we know (from flag_ids) a full block (256 bits) of plaintext. The problem is that the `E(x, p)` polynomial has degree `5 ** 16 = 152587890625`, and will probably lead you to some troubles in storing it and computing the GCD (roughly speaking, without clever optimization tricks, just storing the coefficients could require a couple of TB of RAM).

A possible strategy to reduce the memory needed is a Meet-In-The-Middle approach: instead of computing the full encryption polynomial, we compute it for half of the rounds. We then do the same starting from the ciphertext, simulating the decryption function. The difference of two chunks "in the middle" will have the same property as before (since it does not depend on the number of rounds): it will have `(x-k)` as root. Computing as before the GCD over two chunks does the job.

Notice that this is feasible because this time the degree of the polynomial is `5 ** 8 = 390625`, which means that a few MB are enough to store the polynomials.

The full exploit is available [here](/exploits/CookingNonna/crypto_exploit.sage).

In order to patch, you can play with the JSON (for example swapping the order of the elements), so that attackers do not have access to a full block of known plaintext anymore.

## Exploits

| Store | Exploit                                                |
| :---: | :----------------------------------------------------- |
|   1   | [pwn](/exploits/CookingNonna/pwn_exploit.py)                   |
|   1   | [crypto](/exploits/CookingNonna/crypto_exploit.sage)           |
