#ifndef WALLET_COMMS_H
#define WALLET_COMMS_H

#include <stddef.h>
#include <stdint.h>

#include "wallet/comm_types.h"

void prepare_error_response(struct Response *response, enum ResponseCode code);
void create_wallet(struct Command *command, struct Response *response);
void buy_user_ticket(struct Command *command, struct Response *response);
void buy_vip_ticket(struct Command *command, struct Response *response);
void read_page(struct Command *command, struct Response *response);
void write_page(struct Command *command, struct Response *response);
void num_cards(struct Command *command, struct Response *response);
void get_card(struct Command *command, struct Response *response);

#endif
