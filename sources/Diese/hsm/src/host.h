#ifndef HOST_H
#define HOST_H

#include "stddef.h"
#include "stdint.h"

void host_ks_put(uint32_t key_id, const void *key, size_t size);
void *host_ks_get(uint32_t key_id, size_t *size);

void host_cs_put(uint32_t item_id, uint32_t key_id, const void *data,
                 size_t size);
void *host_cs_get(uint32_t item_id, uint32_t *key_id, size_t *size);

#endif
