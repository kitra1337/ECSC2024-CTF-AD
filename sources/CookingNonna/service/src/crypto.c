#include <gmp.h>
#include <openssl/sha.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "util.h"
#include "crypto.h"

#define ROUNDS 16

void round_function(mpz_t result, mpz_t data, mpz_t tweak, mpz_t mod) {
    mpz_t inv5;
    mpz_t x5, x3, t2;
    mpz_t tmp_res;

    mpz_init(tmp_res);
    mpz_init(inv5);
    mpz_init(x5);
    mpz_init(x3);
    mpz_init(t2);

    mpz_set_str(inv5, (const char *)"11068046444225730992\0", 10);
    mpz_powm_ui(x5, data, (unsigned long)5, mod);
    mpz_powm_ui(x3, data, (unsigned long)3, mod);
    mpz_powm_ui(t2, tweak, (unsigned long)2, mod);

    mpz_addmul(x5, tweak, x3);
    mpz_mul(t2, t2, inv5);
    mpz_addmul(x5, t2, data);

    mpz_mod(tmp_res, x5, mod);
    mpz_set(result, tmp_res);
}

unsigned char *encrypt(char *json_token, char *username, char *password, size_t *enc_json_token_len) {
    mpz_t mod;
    mpz_t k;
    unsigned char *ct;
    char padded_json[MAX_JSON_TOKEN_LEN + 1] = {0};
    char **blocks;
    char *padding;
    size_t num_blocks;
    unsigned char k_hash[SHA256_DIGEST_LENGTH] = {0};
    unsigned char *c[2 * ROUNDS] = {0};

    mpz_init(mod);
    mpz_init(k);
    
    mpz_set_str(mod, (const char *)"18446744073709551653\0", 10);
    
    size_t json_len = strlen(json_token);
    size_t padding_len = 32 - ((json_len + 32) % 32);
    padding = calloc(1, padding_len + 1);
    memset(padding, (unsigned char)padding_len, padding_len);
    strncpy(padded_json, json_token, sizeof(padded_json) - 1);
    strncat(padded_json, padding, sizeof(padded_json) - 1);
    padded_json[sizeof(padded_json) - 1] = '\0';
    num_blocks = strlen(padded_json) / 32;
    blocks = malloc(num_blocks * sizeof(char *));
    ct = calloc(1, num_blocks * 32 * sizeof(char) + 1);

    for (size_t i = 0; i < num_blocks; i++)
    {
        blocks[i] = calloc(1, 32 * sizeof(char) + 1);
        memcpy(blocks[i], &padded_json[32 * i], 32);
    }


    SHA256((unsigned char *)password, strlen(password), k_hash);
    mpz_import(k, 8, 1, sizeof(char), 0, 0, k_hash);

    c[0] = (unsigned char *)malloc(SHA256_DIGEST_LENGTH);
    SHA256((unsigned char *)username, strlen(username), c[0]);

    for (int i = 1; i < 2 * ROUNDS; i++)
    {
        c[i] = (unsigned char *)malloc(SHA256_DIGEST_LENGTH);
        SHA256(c[i - 1], SHA256_DIGEST_LENGTH, c[i]);
    }

    for (size_t i = 0; i < num_blocks; i++)
    {
        mpz_t state[4];
        mpz_t rf1, round_const1, round_tweak1, rf2, round_const2, round_tweak2;
        char tmp_char_state[33] = {0};

        for (int j = 0; j < 4; j++)
        {
            mpz_init(state[j]);
            mpz_import(state[j], 8, 1, sizeof(char), 0, 0, &blocks[i][8 * j]);
        }

        for (int r = 0; r < ROUNDS; r++)
        {
            mpz_t tmp;

            mpz_init(rf1);
            mpz_init(rf2);
            mpz_init(round_const1);
            mpz_init(round_const2);
            mpz_init(round_tweak1);
            mpz_init(round_tweak2);

            mpz_import(round_const1, SHA256_DIGEST_LENGTH, 1, sizeof(char), 0, 0, c[2 * r]);
            mpz_import(round_const2, SHA256_DIGEST_LENGTH, 1, sizeof(char), 0, 0, c[2 * r + 1]);
            mpz_set_ui(round_tweak1, 2 * (r + 1));
            mpz_set_ui(round_tweak2, 2 * (r + 1) + 1);

            mpz_set(rf1, state[0]);
            mpz_add(rf1, rf1, k);
            mpz_add(rf1, rf1, round_const1);
            round_function(rf1, rf1, round_tweak1, mod);

            mpz_add(state[1], state[1], rf1);
            mpz_mod(state[1], state[1], mod);

            mpz_set(rf2, state[2]);
            mpz_add(rf2, rf2, k);
            mpz_add(rf2, rf2, round_const2);
            round_function(rf2, rf2, round_tweak2, mod);
            mpz_add(state[3], state[3], rf2);
            mpz_mod(state[3], state[3], mod);

            mpz_init(tmp);
            mpz_set(tmp, state[0]);
            mpz_set(state[0], state[1]);
            mpz_set(state[1], state[2]);
            mpz_set(state[2], state[3]);
            mpz_set(state[3], tmp);

            mpz_clear(rf1);
            mpz_clear(rf2);
            mpz_clear(round_const1);
            mpz_clear(round_const2);
            mpz_clear(round_tweak1);
            mpz_clear(round_tweak2);
            mpz_clear(tmp);
        }

        for (int j = 0; j < 4; j++)
            mpz_export(&tmp_char_state[8 * j], NULL, 1, sizeof(unsigned long), 1, 0, state[j]);

        memcpy(&ct[32 * i], tmp_char_state, 32);
    }

    *enc_json_token_len = num_blocks * 32;

    mpz_clear(mod);
    mpz_clear(k);
    free(blocks);
    free(padding);
    return ct;
}
