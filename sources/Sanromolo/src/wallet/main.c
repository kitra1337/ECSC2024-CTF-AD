#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "common/util.h"
#include "wallet/comms.h"
#include "wallet/comm_types.h"
#include "wallet/nfclib.h"

void setbufs() {
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
    setbuf(stdin, NULL);
}

int main(void) {
    struct Command command;
    struct Response response;
    uint8_t crc[2];
    ssize_t n_read;

    setbufs();

    while (1) {
        memset(&command, 0, sizeof(command));
        memset(&response, 0, sizeof(response));

        n_read = read(STDIN_FILENO, &command.length, sizeof(command.length));
        if (n_read == -1)
            err(1, "read");
        if (n_read == 0)
            break;

        if (n_read > 0 && command.length < 3) {
            prepare_error_response(&response, Unknown);
            goto send_response_and_continue;
        }

        // Read whole command from its type onwards
        n_read = read_exactly(STDIN_FILENO, command.raw + 1, command.length);
        if (n_read == -1)
            err(1, "read");
        if (n_read == 0)
            errx(1, "read: EOF");

        // This should be impossible given read_exactly() implementation, but
        // check anyway and bail out
        if (n_read != command.length)
            errx(1, "read: internal error");

        // Verify CRC
        uint8_t *command_crc = command.raw + 1 + command.length - 2;
        iso14443a_crc(command.raw + 1, command.length - 2, crc);

        if (crc[0] != command_crc[0] || crc[1] != command_crc[1]) {
            prepare_error_response(&response, CRCErr);
            goto send_response_and_continue;
        }

        switch ((enum MessageType)command.type) {
        case Read:
            read_page(&command, &response);
            break;

        case Write:
            write_page(&command, &response);
            break;

        case BuyUser:
            buy_user_ticket(&command, &response);
            break;

        case BuyVIP:
            buy_vip_ticket(&command, &response);
            break;

        case NumCards:
            num_cards(&command, &response);
            break;

        case GetCard:
            get_card(&command, &response);
            break;

        case CreateWallet:
            create_wallet(&command, &response);
            break;

        default:
            prepare_error_response(&response, InvArg);
            break;
        }

send_response_and_continue:
        write_exactly(STDOUT_FILENO, &response.length, sizeof(response.length));
        write_exactly(STDOUT_FILENO, response.raw + 1, response.length);
    }

    return 0;
}
