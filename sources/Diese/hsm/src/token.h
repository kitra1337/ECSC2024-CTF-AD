#ifndef TOKEN_H
#define TOKEN_H

#include "stddef.h"
#include "stdint.h"

const char *token_check(uint32_t item_id, uint32_t owner_key_id,
                        uint32_t target_key_id, const void *token, size_t size);

#endif
