#ifndef CRYPTO_H
#define CRYPTO_H

#include "stddef.h"
#include "stdint.h"

/* BUG WARN: operates on 4-byte blocks, OOB if size is not 4-byte aligned. */
void crypto_chacha20(void *buf, size_t size, const void *key, size_t key_size,
                     const uint8_t *nonce);

int crypto_memcmp(const void *s1, const void *s2, size_t size);

#endif
