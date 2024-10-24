#ifndef COMMON_WALLET_API_H
#define COMMON_WALLET_API_H

#include <stdint.h>

int print_wallet_error(uint8_t code);

int wallet_create_wallet(int walletfd, uint8_t *outwallet_id);

int wallet_buy_ticket(int walletfd, uint8_t *wallet_id, uint8_t *event_id,
                      const char *name, uint8_t *outserial);
int wallet_buy_vip_ticket(int walletfd, uint8_t *wallet_id, uint8_t *event_id,
                          const char *name, uint8_t *vip_code,
                          uint8_t *outserial);

int wallet_read_page(int walletfd, const uint8_t *wallet_id,
                     const uint8_t *serial, uint8_t offset, void *outdata);
int wallet_write_page(int walletfd, const uint8_t *wallet_id,
                      const uint8_t *serial, uint8_t offset, const void *data);

int wallet_num_cards(int walletfd, uint8_t *wallet_id, uint8_t *out_num_cards);
int wallet_get_card(int walletfd, uint8_t *wallet_id, uint8_t offset,
                    uint8_t *outserial);

#endif
