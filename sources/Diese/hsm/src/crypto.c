#include "chacha20.h"
#include "crypto.h"
#include "sha256.h"
#include "stdint.h"

void crypto_chacha20(void *buf, size_t size, const void *key, size_t key_size,
                     const uint8_t *nonce)
{
	uint8_t c20_key[32];
	sha256(key, key_size, c20_key, 32);

	struct chacha20_context ctx;
	chacha20_init_context(&ctx, c20_key, nonce, 0);

	chacha20_xor(&ctx, buf, size);
}

int crypto_memcmp(const void *s1, const void *s2, size_t size)
{
	uint8_t ret = 0;
	for (size_t i = 0; i < size; i++)
		ret |= ((const uint8_t *)s1)[i] ^ ((const uint8_t *)s2)[i];
	return ret;
}
