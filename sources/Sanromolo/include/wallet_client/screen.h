#ifndef WALLET_CLIENT_SCREEN_H
#define WALLET_CLIENT_SCREEN_H

#include <stdint.h>

#include "wallet/nfclib.h"

typedef struct _screen_data {
    uint8_t wallet_id[16];
    uint8_t wallet_tag_amount;
    uint8_t selected_tag_serial[6];
    uint8_t wallet_tag_serials[0xff][6];
} screen_data;

#endif
