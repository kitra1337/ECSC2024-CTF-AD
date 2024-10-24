# Diese

| Service     | Diese                                                                                                       |
| :---------- | :---------------------------------------------------------------------------------------------------------- |
| Authors     | Andrea Biondo <@abiondo>, Riccardo Bonafede <@bonaff>                                                       |
| Stores      | 2                                                                                                           |
| Categories  | pwn, web                                                                                                    |
| Port        | HTTP 80                                                                                                     |
| FlagIds     | store1: [username, post_id], store2: [key_id, item_id]                                                      |
| Checkers    | [store1](/checkers/Diese-1), [store2](/checkers/Diese-2)                                                    |

## Description

A note sharing service with one plain store and one end-to-end encrypted store.

## Vulnerabilities

### Store 1 (web):
A simple document document manager. Users can upload documents, and share with other users. Flags are stored in such documents.

### Vuln 1: Hash Length Extension Attack

When sharing a document, the application creates a token containing some basic information, such as the document_id, that are used to perform access control. The token is secured by an "hmac", in the form of `sha1($secret . $data)`. This kind of hmac is vulnerable to a [hash length extension attack](https://en.wikipedia.org/wiki/Length_extension_attack).

To exploit the vulnerability, one can simply create a document, share it with another user, then use a tool like hashpumpy (hashpump seems to be broken(?)), and then inject the from_user and document_id parameters with the flags id. 

The best way to patch this vulnerability is to change the `sha1` function with the secure `hash_hmac`.


### Vuln 2: parse_str Parameter Pollution

The templates allow users to auto-share their documents to other users. To do this, in the process of creating a document, the application checks if the template contains the `{auto_share}` tag. This tag is in the form of:
```
{auto_share=[to_user=ID&message=Some message]}
```

The vulnerability arises in the parsing of this tag. Infact, to parse the to_user and the message parameters, the application uses a simple regex. The regex will build a dictionary containing every key from the tag, not only the to_user and the message. This dictionary is then updated to contain the from_user and the document_id and then transformed into a sharing token. Because PHP's parse_str will transform some characters such as `.` to `_`, it is possible to inject a parameter that will pollute the `from_user` and `document_id` of the share token. An example of a payload which exploits such behavior is the following one:

```
{auto_share=[to_user=*username*&from_user=*username1*&from.user=*flag_username*&doc_id=x&doc.id=*document id**&message=foobar}
```

The quickest way to patch this vulnerability is to implement an allowlist of parameters that are allowed to be stored inside the share token.

## Store 2 (pwn)

(NOTE: whenever encryption is mentioned, it refers to the Chacha20 stream cipher)

This store implements a secret end-to-end encrypted item storage in a bare metal ARM firmware (the HSM) emulated using QEMU.
Users can share secret items with each other through share tokens, which authorize an user to access another user's item.
Tokens are transitive: if a user has access to an item, they can generate a token to share it with another user.

Each flag is stored as an item.
The flag ID provided to players includes the item ID and key ID (i.e., user ID).
Players do not have a token to access the item, so they have to exploit the service to read flags.

The web frontend communicates via TCP with `hsm.py`, which in turn communicates with the HSM firmware via a virtual serial port.
The `hsm.py` middleware translates the TCP text-based protocol to the serial binary protocol, and also handles storage requests from the HSM, so that keys and items can be stored in a persistent SQLite database.

After an user registers, they can import their key via `settings.php`.
This sends a `IMPORT_KEY` message to the HSM, which will send a `KS_PUT` message to the middleware to store the user's key.
The key ID is the user ID.

When a user wants to import a secret item, they use the `write_secret.php` API.
They pass the item encrypted with Chacha20 using their previously imported key and `'I'*12` nonce.
This sends a `IMPORT_ITEM` message to the HSM.
The HSM will fetch the key (`KS_GET`), decrypt the item, and store it (`CS_PUT`) along with the key ID of the user, which is the item's owner key ID.

Finally, secrets can be read via the `read_secret.php` API.
To read a secret, a user needs the item ID and a token.
This action sends a `GET_ITEM` message to the HSM and, if the token is valid, the HSM will return the item encrypted with the requesting user's key, so that they can decrypt it and read it.

The token is encrypted with the requesting user's key and an variable-length nonce.
The token begins with a single byte that specifies the length of the nonce, followed by the nonce itself encrypted using the requesting user's key and nonce `'T'*12`.
This is followed by the actual body of the token, encrypted with the requesting user's key and the provided nonce.

The structure of tokens is recursive.
We start from a root token, which a user uses to see their own items.
Such a token is `owner key ID || item ID || optional ignored data` (IDs are 32-bit), followed by an HMAC-SHA256 using the owner's key.
Given a token that allows access to user A, a token for user B can be generated by prepending B's key ID and appending an HMAC-SHA256 using A's key.
Token verification recursively unwraps the token and checks the HMACs backwards.

### Vuln 1: stream cipher OOB XOR

The `chacha20_xor` function looks like this:

```c
void chacha20_xor(struct chacha20_context *ctx, uint8_t *bytes, size_t n_bytes)
{
	for (size_t i = 0; i < n_bytes; i += 4)
	{
		if (ctx->position >= 64)
		{
			chacha20_block_next(ctx);
			ctx->position = 0;
		}
		*(uint32_t *)(bytes + i) ^= ctx->keystream32[ctx->position / 4];
		ctx->position += 4;
	}
}
```

If `n_bytes` is not a multiple of 4, it will XOR up to 3 bytes out-of-bounds.

Most uses of `chacha20_xor` happen on heap buffers, whose size is 4-byte aligned by the heap allocator, making the bug harmless.
However, there is one interesting usage in `token_check`.

`token_check` tries to construct a 12-byte Chacha20 nonce by prepending zeroes to the user-provided nonce.
To do this, it clears a 12-byte buffer on the stack, copies the used nonce at end of if, and then decrypts the user nonce in-place.
Therefore, if the user-provided nonce length is not a multiple of 4, a stack OOB will happen.

The stack layout looks like:

```c
uint8_t nonce[12];
uint32_t owner_key_id;
```

So this vulnerability can be used to overwrite 1 to 3 of the LSBs of `owner_key_id`.
The `owner_key_id` variable is used to check that the root token comes from the actual owner.
By overwriting it with our own key ID, we can pass a root token MACed by us and bypass the token check.

The OOB XOR is with the keystream, which we don't control directly, but we control the key that generates it.
Therefore, we can perform an offline bruteforce to find a key such that the XOR will turn the original owner key ID into our key ID.

Three bytes are always enough: for the 4th byte (MSB) to be used, we'd need to have more than 16M keys, which is not compatible with this A/D game and tick duration.
Bruteforcing the key for 3 bytes can be slow, but it can be done quickly (<15s single core) with a C helper.
However, 2 bytes can be bruteforced extremely quickly and are sufficient for basically all flags: it is unlikely that (on average) more than 32K keys will be imported during the validity time of a flag, as such, the third byte is mostly constant before flag expiration.

### Vuln 2: unchecked heap allocation

The HSM fimware implements a custom heap allocator (`heap_alloc` / `heap_free`).
The key points of the allocator are:

- 4-byte size alignment
- Inline metadata, 4-byte chunk header (size, free bit)
- First-fit allocation with chunk splitting
- When allocating, the heap is extended (up to a maximum size) with a new chunk if there are no suitably-sized free chunks
- When freeing, only forward consolidation is performed (no backwards)

When checking a token, `extract_token` will fetch the keys in the share chain.
Fetching a key via `host_ks_get` send a `KS_GET` message to the middleware.
The response message will be allocated on the heap by `msg_recv`.
`host_ks_get` will then copy to key to a new allocation and free the message.
Finally, `extract_token` will check the MAC and free the key.

Since this leads to an alloc-free-alloc-free-... pattern, it may appear that its heap usage is bounded by the largest key in the chain.
However, because the heap is always extended when needed and consolidation is only forward, picking key sizes so that the allocation sizes are increasing leads to excessive heap extension.
Eventually, the maximum heap size is reached and `heap_alloc` returns NULL.

Specifically, this happens when reading a `KS_GET` response message from UART.
Since `msg_alloc` (called from `msg_recv`) does not check for allocation failure, the message will be read to NULL, i.e., address 0.
This is a valid address: it contains the interrupt vector.

There are only two handlers used by the firmware: the reset handler, useless after startup, and the IRQ handler, used by UART, which will be our target.
This makes it a bit tricky: since `msg_recv` reads from UART and writes to the buffer, we're overwriting the handler for an interrupt which will be triggering repeatedly while we overwrite it.
This means that, in most cases, we will only be able to overwrite the LSB of the IRQ handler entry before it gets called due to incoming UART data.
One byte is enough, however, by also exploiting the fact that the message structure starts with the message type, which is a single 0x00 byte, followed by 3 bytes of untouched in-structure padding.

It is easier to explain by looking at how the exploit key that will be received at NULL is constructed:

```
# Message allocated at NULL, key starts at 0x8.
# 0x00: LDR PC, [PC, #0] ; 0x08
#       originally LDR PC, [PC, #24] corrupted by 0x00 message type
# 0x04: message length (garbage)
# --- KEY STARTS HERE ---
# 0x08: .word SHELLCODE_ADDR
null_key = struct.pack('<I', SHELLCODE_ADDR)
# 0x0c: padding
null_key += b'A'*12
# 0x18: LDR PC, [PC, #16] ; 0x30
#       originally LDR PC, [PC, #4]
#       this is the IRQ entry which is triggered by UART receive
#       usually we can corrupt just one byte before it gets called
#       we just change the LSB (0x04 -> 0x10)
#       word at 0x30 is zero, so jumps to 0x00 which jumps to shellcode
null_key += struct.pack('<I', 0xe51ff010)
```

All memory is executable, so shellcode can be placed for example on the heap.
The shellcode restores the vector, a clean state for heap and UART, returns from interrupt mode so that UART communication can work again, requests the flag item and sends it back to the attacker.


## Exploits

| Store | Exploit                                                                      |
| :---: | :--------------------------------------------------------------------------- |
|   1   | [1-length-extension.py](/exploits/Diese/1-length-extension.py)               |
|   1   | [1-template.py](/exploits/Diese/1-template.py)                               |
|   2   | [2-alloc-fail.py](/exploits/Diese/2-alloc-fail.py)                           |
|   2   | [2-xor-oob.py](/exploits/Diese/2-xor-oob.py)                                 |
