#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "common/util.h"
#include "common/wallet_api.h"
#include "wallet/comm_types.h"

#define memcpy_to_buf(buf, ptr)   memcpy((buf), ptr, sizeof(buf))
#define memcpy_from_buf(ptr, buf) memcpy(ptr, (buf), sizeof(buf))

int print_wallet_error(uint8_t code) {
    switch ((enum ResponseCode)code) {
    case ACK:
        return 0;
        break;
    case InvArg:
        puts("Invalid argument");
        break;
    case CRCErr:
        puts("Transmission error, please check for external disturbances...");
        break;
    case Unknown:
    default:
        puts("Unknown error.");
        break;
    }
    return 1;
}

static void set_command_crc(struct Command *command) {
    iso14443a_crc(command->raw + 1, command->length - 2,
                  command->raw + 1 + (command->length - 2));
}

static void send_command_and_get_response(int walletfd, struct Command *command,
                                   struct Response *response) {
    write_exactly(walletfd, command->raw, 1);
    write_exactly(walletfd, command->raw + 1, command->length);
    read_exactly(walletfd, response->raw, 1);
    read_exactly(walletfd, response->raw + 1, response->length);
}

int wallet_create_wallet(int walletfd, uint8_t *outwallet_id) {
    struct Response response;
    struct Command command;

    command.type = CreateWallet;
    command.length = CreateWalletCommandSize;
    set_command_crc(&command);

    send_command_and_get_response(walletfd, &command, &response);
    if (response.code == ACK)
        memcpy_from_buf(outwallet_id, response.data.create_wallet.wallet_id);

    return response.code;
}

int wallet_buy_ticket(int walletfd, uint8_t *wallet_id, uint8_t *event_id,
                      const char *name, uint8_t *outserial) {
    struct Response response;
    struct Command command;

    command.type = BuyUser;
    command.length = BuyUserCommandSize;
    memcpy_to_buf(command.wallet_id, wallet_id);
    memcpy_to_buf(command.data.buy_user.event_id, event_id);
    memcpy_to_buf(command.data.buy_user.user, name);
    set_command_crc(&command);

    send_command_and_get_response(walletfd, &command, &response);
    if (response.code == ACK)
        memcpy_from_buf(outserial, response.data.buy.ticket_id);

    return response.code;
}

int wallet_buy_vip_ticket(int walletfd, uint8_t *wallet_id, uint8_t *event_id,
                          const char *name, uint8_t *vip_code,
                          uint8_t *outserial) {
    struct Response response;
    struct Command command;

    command.type = BuyVIP;
    command.length = BuyVipCommandSize;
    memcpy_to_buf(command.wallet_id, wallet_id);
    memcpy_to_buf(command.data.buy_vip.event_id, event_id);
    memcpy_to_buf(command.data.buy_vip.user, name);
    memcpy_to_buf(command.data.buy_vip.vip_code, vip_code);
    set_command_crc(&command);

    send_command_and_get_response(walletfd, &command, &response);
    if (response.code == ACK)
        memcpy_from_buf(outserial, response.data.buy.ticket_id);

    return response.code;
}

int wallet_read_page(int walletfd, const uint8_t *wallet_id, const uint8_t *serial,
              uint8_t offset, void *outdata) {
    struct Response response;
    struct Command command;

    command.type = Read;
    command.length = ReadCommandSize;
    memcpy_to_buf(command.wallet_id, wallet_id);
    memcpy_to_buf(command.data.read.ticket_id, serial);
    command.data.read.page = offset;
    set_command_crc(&command);

    send_command_and_get_response(walletfd, &command, &response);
    if (response.code == ACK)
        memcpy_from_buf(outdata, response.data.read.data);

    return response.code;
}

int wallet_write_page(int walletfd, const uint8_t *wallet_id, const uint8_t *serial,
               uint8_t offset, const void *data) {
    struct Response response;
    struct Command command;

    command.type = Write;
    command.length = WriteCommandSize;
    memcpy_to_buf(command.wallet_id, wallet_id);
    memcpy_to_buf(command.data.write.ticket_id, serial);
    command.data.write.page = offset;
    memcpy_to_buf(command.data.write.page_data, data);
    set_command_crc(&command);

    send_command_and_get_response(walletfd, &command, &response);
    return response.code;
}

int wallet_num_cards(int walletfd, uint8_t *wallet_id, uint8_t *out_num_cards) {
    struct Response response;
    struct Command command;

    command.type = NumCards;
    command.length = NumCardsCommandSize;
    memcpy_to_buf(command.wallet_id, wallet_id);
    set_command_crc(&command);

    send_command_and_get_response(walletfd, &command, &response);
    if (response.code == ACK)
        *out_num_cards = response.data.num_cards.cards;

    return response.code;
}

int wallet_get_card(int walletfd, uint8_t *wallet_id, uint8_t offset,
             uint8_t *outserial) {
    struct Response response;
    struct Command command;

    command.type = GetCard;
    command.length = GetCardCommandSize;
    memcpy_to_buf(command.wallet_id, wallet_id);
    command.data.get_card.offset = offset;
    set_command_crc(&command);

    send_command_and_get_response(walletfd, &command, &response);
    if (response.code == ACK)
        memcpy_from_buf(outserial, response.data.get_card.ticket_id);

    return response.code;
}
