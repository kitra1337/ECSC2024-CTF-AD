#ifndef CRYPTO_H
#define CRYPTO_H

#include <unistd.h>
#include <stdbool.h>
#include <gmp.h>

#define MAX_JSON_TOKEN_LEN 256

unsigned char* encrypt(char* json_token, char* username, char* password, size_t *enc_json_token_len);
void round_function(mpz_t result, mpz_t data, mpz_t tweak, mpz_t mod);

#endif