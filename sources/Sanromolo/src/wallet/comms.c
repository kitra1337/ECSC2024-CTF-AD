#define _GNU_SOURCE

#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "common/event.h"
#include "common/util.h"
#include "wallet/comms.h"
#include "wallet/comm_types.h"
#include "wallet/nfclib.h"

#define WALLET_DIR      "/home/ubuntu/wallets/"
#define EVENT_DIRECTORY "/home/ubuntu/events/"

#define memcpy_buf_chk(dst, src) do {               \
        _Static_assert(sizeof(dst) == sizeof(src)); \
        memcpy(dst, src, sizeof(dst));              \
    } while (0)


void set_response_crc(struct Response *response) {
    iso14443a_crc(response->raw + 1, response->length - 2,
                  response->raw + 1 + response->length - 2);
}

void build_wallet_path(uint8_t *wallet_id, char *path) {
    strcpy(path, WALLET_DIR);
    bytes_to_hex(path + sizeof(WALLET_DIR) - 1, wallet_id, WALLET_ID_SIZE);
}

void build_ticket_path(uint8_t *wallet_id, uint8_t *serial, char *path) {
    strcpy(path, WALLET_DIR);
    bytes_to_hex(path + sizeof(WALLET_DIR) - 1, wallet_id, WALLET_ID_SIZE);
    path[strlen(path)] = '/';
    bytes_to_hex(path + strlen(path), serial, NFCTAG_SERIAL_FULL_SIZE);
}

int check_wallet_exists(struct Command *command) {
    char dirname[sizeof(WALLET_DIR) + 128] = {0};
    struct stat st = {0};

    strcpy(dirname, WALLET_DIR);
    bytes_to_hex(dirname + sizeof(WALLET_DIR) - 1, command->wallet_id,
                 sizeof(command->wallet_id));

    if (stat(dirname, &st) == 0 && S_ISDIR(st.st_mode))
        return 0;
    return -1;
}

int get_ticket_data(uint8_t *wallet_id, uint8_t *serial, struct NFCTag *ticket) {
    char path[sizeof(WALLET_DIR) + 128];
    struct stat st = {0};

    memset(path, 0, sizeof(path));
    build_ticket_path(wallet_id, serial, path);

    if (stat(path, &st) == 0 && S_ISREG(st.st_mode)) {
        int ticketfd = open(path, O_RDONLY);
        if (ticketfd < 0)
            return -1;

        read_exactly(ticketfd, ticket->raw, sizeof(struct NFCTag));
        close(ticketfd);
        return 0;
    }

    return -1;
}

int save_ticket_data(uint8_t *wallet_id, struct NFCTag *ticket) {
    char path[sizeof(WALLET_DIR) + 128];
    uint8_t serial[NFCTAG_SERIAL_FULL_SIZE] = {0};

    memcpy(serial, ticket->serial_part_1, sizeof(ticket->serial_part_1));
    memcpy(serial + 2, ticket->serial_part_2, sizeof(ticket->serial_part_2));

    memset(path, 0, sizeof(path));
    build_ticket_path(wallet_id, serial, path);

    int ticketfd = open(path, O_CREAT | O_RDWR, 0666);
    if (ticketfd < 0)
        return -1;

    write_exactly(ticketfd, ticket, sizeof(*ticket));
    close(ticketfd);
    return 0;
}

void prepare_error_response(struct Response *response, enum ResponseCode code) {
    response->length = ErrorResponseSize;
    response->code = (uint8_t)code;
    set_response_crc(response);
}

void create_wallet(struct Command *command, struct Response *response) {
    char path[sizeof(WALLET_DIR) + 128];
    uint8_t new_wallet_id[WALLET_ID_SIZE];
    struct stat st = {0};
    (void)command; // unused here

    if (get_rand_bytes(new_wallet_id, sizeof(new_wallet_id)) == -1) {
        prepare_error_response(response, Unknown);
        return;
    }

    memset(path, 0, sizeof(path));
    build_wallet_path(new_wallet_id, path);
    if (stat(path, &st) != -1) {
        prepare_error_response(response, Unknown);
        return;
    }

    if (mkdir(path, 0700) != 0) {
        prepare_error_response(response, Unknown);
        return;
    }

    response->length = CreateWalletResponseSize;
    response->code = ACK;
    memcpy_buf_chk(response->data.create_wallet.wallet_id, new_wallet_id);
    set_response_crc(response);
}

void buy_user_ticket(struct Command *command, struct Response *response) {
    struct {
        struct NFCTag ticket;
        struct Event event;
        uint8_t serial[NFCTAG_SERIAL_FULL_SIZE];
        char path[sizeof(WALLET_DIR) + 128];
    } stack;

    nfc_reset_tag(&stack.ticket);
    memcpy_buf_chk(stack.ticket.user, command->data.buy_user.user);

    if (check_wallet_exists(command) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    if (get_event_data(command->data.buy_user.event_id, &stack.event) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    memcpy_buf_chk(stack.ticket.event_id, stack.event.id);

    if (nfc_init_tag_header(&stack.ticket) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    // Set the ticket as a user ticket. Last bit at 0 means VIP.
    // NOTE that this is inverted.
    stack.ticket.OTP = 0x01000000;
    // Lock event id page
    stack.ticket.lock_bytes = 0x00f0;

    memcpy(stack.serial, stack.ticket.serial_part_1, sizeof(stack.ticket.serial_part_1));
    memcpy(stack.serial + 2, stack.ticket.serial_part_2, sizeof(stack.ticket.serial_part_2));

    memset(stack.path, 0, sizeof(stack.path));
    build_ticket_path(command->wallet_id, stack.serial, stack.path);

    int ticket_file = open(stack.path, O_CREAT | O_RDWR, 0666);
    if (ticket_file < 0) {
        prepare_error_response(response, Unknown);
        return;
    }

    write_exactly(ticket_file, &stack.ticket, sizeof(stack.ticket));
    close(ticket_file);

    response->length = BuyResponseSize;
    response->code = ACK;
    memcpy_buf_chk(response->data.buy.ticket_id, stack.serial);
    set_response_crc(response);
}

void buy_vip_ticket(struct Command *command, struct Response *response) {
    struct {
        struct NFCTag ticket;
        struct Event event;
        char pad[0x20];
    } stack;

    // BUG AUX: stack alignment
    (void)stack.pad;

    nfc_reset_tag(&stack.ticket);
    memcpy_buf_chk(stack.ticket.user, command->data.buy_user.user);

    if (check_wallet_exists(command) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    if (get_event_data(command->data.buy_vip.event_id, &stack.event) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    if (memcmp(command->data.buy_vip.vip_code, stack.event.vip_invitation_code,
               EVENT_VIP_INV_CODE_SIZE) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    memcpy_buf_chk(stack.ticket.event_id, stack.event.id);

    if (nfc_init_tag_header(&stack.ticket) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    // Lock event id pages
    stack.ticket.lock_bytes = 0x00f0;

    if (save_ticket_data(command->wallet_id, &stack.ticket) != 0) {
        prepare_error_response(response, Unknown);
        return;
    }

    response->length = BuyResponseSize;
    response->code = ACK;

    memcpy(response->data.buy.ticket_id, stack.ticket.serial_part_1,
           sizeof(stack.ticket.serial_part_1));
    memcpy(response->data.buy.ticket_id + 2, stack.ticket.serial_part_2,
           sizeof(stack.ticket.serial_part_2));
    set_response_crc(response);
}

void read_page(struct Command *command, struct Response *response) {
    struct {
        char pad1[0x08];
        struct NFCTag ticket;
        char pad2[0x18];
    } stack;

    // BUG AUX: stack alignment. Also avoids collision of user controlled
    // fields of this ticket and the header of the ticket in write_page(), which
    // should not be the exploitation target.
    (void)stack.pad1;
    (void)stack.pad2;

    if (command->data.read.page >= 16) {
        prepare_error_response(response, InvArg);
        return;
    }

    if (check_wallet_exists(command) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    // BUG: no error check here means that requesting to read data from a ticket
    // that does not exist will leak data from the stack. The stack is aligned
    // in such a way that the ticket here collides with the ticket and the event
    // in buy_vip_ticket() above, so it's possible to craft the appropriate
    // input for buy_vip_ticket(), pass che nfc_verify_tag() check below and
    // then leak the old event->vip_invitation_code[] still on the stack.
    get_ticket_data(command->wallet_id, command->data.read.ticket_id, &stack.ticket);

    if (nfc_verify_tag(&stack.ticket) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    response->length = ReadResponseSize;
    response->code = ACK;
    memcpy(response->data.read.data,
           stack.ticket.raw + (command->data.read.page * NFCTAG_PAGE_SIZE),
           NFCTAG_PAGE_SIZE);
    set_response_crc(response);
}

void write_page(struct Command *command, struct Response *response) {
    struct NFCTag ticket;

    if (command->data.write.page >= NFCTAG_N_PAGES) {
        prepare_error_response(response, InvArg);
        return;
    }

    if (check_wallet_exists(command) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    // Make vuln in read_page() less obvious and also avoid the error check
    // here. It shouldn't be possible to pass nfc_verify_tag() if this fails
    // because user controlled data in other stack frames does not collide with
    // the necessary ticket header fields in this frame. Even if it was though,
    // it wouldn't be a big deal: it would just allow creating bogus tickets.
    get_ticket_data(command->wallet_id, command->data.read.ticket_id, &ticket);

    if (nfc_verify_tag(&ticket) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    for (size_t i = 0; i < NFCTAG_PAGE_SIZE; i++) {
        nfc_set_byte(&ticket, (command->data.write.page * NFCTAG_PAGE_SIZE) + i,
            command->data.write.page_data[i]);
    }

    if (save_ticket_data(command->wallet_id, &ticket) != 0) {
        prepare_error_response(response, Unknown);
        return;
    }

    response->length = WriteResponseSize;
    response->code = ACK;
    set_response_crc(response);
}

uint8_t countfiles(char *path) {
    DIR *dir_ptr = NULL;
    struct dirent *direntp;

    if (!path)
        return 0;
    if ((dir_ptr = opendir(path)) == NULL)
        return 0;

    uint8_t count = 0;
    while ((direntp = readdir(dir_ptr))) {
        switch (direntp->d_type) {
        case DT_REG:
            ++count;
            break;
        }
    }

    closedir(dir_ptr);
    return count;
}

uint8_t get_nth_file(char *path, uint8_t offset, char *filename) {
    DIR *dir_ptr = NULL;
    struct dirent *direntp;

    if (!path)
        return 0;
    if ((dir_ptr = opendir(path)) == NULL)
        return 0;

    uint8_t count = 0;
    while ((direntp = readdir(dir_ptr))) {
        switch (direntp->d_type) {
        case DT_REG:
            if (count == offset) {
                strncpy(filename, direntp->d_name, 12);
                return 0;
            }
            ++count;
            break;
        }
    }

    closedir(dir_ptr);
    return -1;
}

void num_cards(struct Command *command, struct Response *response) {
    char path[sizeof(WALLET_DIR) + 128] = {0};

    if (check_wallet_exists(command) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    build_wallet_path(command->wallet_id, path);

    response->length = NumCardsResponseSize;
    response->code = ACK;
    response->data.num_cards.cards = countfiles(path);
    set_response_crc(response);
}

void get_card(struct Command *command, struct Response *response) {
    char path[sizeof(WALLET_DIR) + 128] = {0};
    uint8_t serial[NFCTAG_SERIAL_FULL_SIZE] = {0};
    char serial_hex[NFCTAG_SERIAL_FULL_SIZE * 2] = {0};
    char *serial_ptr = serial_hex;

    if (check_wallet_exists(command) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    build_wallet_path(command->wallet_id, path);

    if (get_nth_file(path, command->data.get_card.offset, serial_hex) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    for (size_t i = 0; i < sizeof(serial); i++) {
        sscanf(serial_ptr, "%2hhx", serial + i);
        serial_ptr += 2;
    }

    response->length = GetCardResponseSize;
    response->code = ACK;
    memcpy_buf_chk(response->data.get_card.ticket_id, serial);
    set_response_crc(response);
}
