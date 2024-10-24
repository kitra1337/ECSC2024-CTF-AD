#include "crypto.h"
#include "heap.h"
#include "hmac_sha256.h"
#include "host.h"
#include "stddef.h"
#include "stdint.h"
#include "string.h"
#include "token.h"

static const char *extract_token(const uint8_t *token, size_t size,
                                 uint32_t owner_key_id, uint32_t *item_id,
                                 uint32_t *target_key_id)
{
	if (size < 4)
		return "invalid token (too small for target key ID)";

	*target_key_id = *(uint32_t *)token;

	uint32_t hmac_key_id;

	if (*target_key_id == owner_key_id) {
		if (size < 8 + 32)
			return "invalid token (too small for item ID + MAC)";
		*item_id = *(uint32_t *)(token + 4);
		hmac_key_id = owner_key_id;
	} else {
		if (size < 4 + 32)
			return "invalid token (too small for MAC)";
		/* BUG: recursion can be used to exhaust heap. This results in key data
		 * being read to NULL (0), where interrupt vectors are located. */
		const char *err = extract_token(token + 4, size - 4 - 32, owner_key_id,
			item_id, &hmac_key_id);
		if (err)
			return err;
	}

	size_t key_size;
	void *key = host_ks_get(hmac_key_id, &key_size);

	uint8_t hmac[32];
	hmac_sha256(key, key_size, token, size - 32, hmac, 32);

	heap_free(key);

	if (crypto_memcmp(hmac, token + size - 32, 32))
		return "invalid token (bad MAC)";

	return 0;
}

const char *token_check(uint32_t item_id, uint32_t owner_key_id,
                        uint32_t target_key_id, const void *token, size_t size)
{
	const uint8_t *tokenp = token;

	/* BUG DEP: force spilling of owner_key_id after nonce.
	 * 4-byte alignment to avoid suspicion from misaligned uint32_t. */
	struct {
		uint8_t nonce[12];
		uint8_t owner_key_id[4];
	} __attribute__((packed)) s __attribute__((aligned(4)));
	*(volatile uint32_t *)s.owner_key_id = owner_key_id;

	if (size < 1)
		return "invalid token (too small for nonce size)";

	uint8_t nonce_size = *tokenp;
	if (nonce_size > sizeof(s.nonce))
		return "invalid token (invalid nonce size)";

	if (size < 1U + nonce_size)
		return "invalid token (too small for nonce)";

	size_t key_size;
	void *key = host_ks_get(target_key_id, &key_size);

	uint8_t nonce_1[12];
	memset(nonce_1, 'T', sizeof(nonce_1));

	/* BUG DEP: OOB XOR of up to 3 bytes into s.owner_key_id. */
	uint8_t *nonce_enc = s.nonce + sizeof(s.nonce) - nonce_size;
	memset(s.nonce, 0, sizeof(s.nonce));
	memcpy(nonce_enc, tokenp + 1, nonce_size);
	crypto_chacha20(nonce_enc, nonce_size, key, key_size, nonce_1);

	const uint8_t *token_body = tokenp + 1 + nonce_size;
	size_t token_body_size = size - 1 - nonce_size;

	uint8_t *token_body_copy = heap_alloc(token_body_size);
	memcpy(token_body_copy, token_body, token_body_size);

	/* BUG WARN SAFE: heap allocation size is 4-byte aligned. */
	crypto_chacha20(token_body_copy, token_body_size, key, key_size, s.nonce);

	heap_free(key);

	uint32_t token_item_id, token_target_key_id;
	const char *err = extract_token(token_body_copy, token_body_size,
		*(volatile uint32_t *)s.owner_key_id, &token_item_id, &token_target_key_id);

	heap_free(token_body_copy);

	if (err)
		return err;

	if (token_item_id != item_id)
		return "invalid token (wrong item ID)";

	if (token_target_key_id != target_key_id)
		return "invalid token (wrong target key ID)";

	return 0;
}
