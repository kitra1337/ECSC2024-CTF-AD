#include <arpa/inet.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <termcap.h>
#include <unistd.h>

#include "common/event.h"
#include "common/util.h"
#include "common/wallet_api.h"
#include "wallet/nfclib.h"
#include "wallet/wallet.h"
#include "wallet_client/screen.h"

// make clean && make DEBUG=1
#ifdef DEBUG

void pretty_print(struct NFCTag *tag) {
    fprintf(stderr, "Manufacturer: %02hhx\n", tag->manufacturer);
    fprintf(stderr, "Serial N.:    %02hhx %02hhx %02hhx %02hhx %02hhx %02hhx\n",
            tag->serial_part_1[0], tag->serial_part_1[1],
            tag->serial_part_2[0], tag->serial_part_2[1],
            tag->serial_part_2[2], tag->serial_part_2[3]);
    fprintf(stderr, "Check byte 1: %02hhx\n", tag->check_byte_1);
    fprintf(stderr, "Check byte 2: %02hhx\n", tag->check_byte_2);
    fprintf(stderr, "Internal:     %02hhx\n", tag->internal);
    fprintf(stderr, "Lock bytes:   %04hx\n", tag->lock_bytes);
    fprintf(stderr, "OTP:          %08x\n", tag->OTP);
    fprintf(stderr, "User Data:\n");
    for (int i = 0; i < 48; i += 4) {
        fprintf(stderr, "%02hhx %02hhx %02hhx %02hhx\n", tag->raw[i + 16],
                tag->raw[i + 1 + 16], tag->raw[i + 2 + 16], tag->raw[i + 3 + 16]);
    }
}

void raw_dump(struct NFCTag *tag) {
    for (int i = 0; i < 64; i += 4) {
        fprintf(stderr, "%02hhx %02hhx %02hhx %02hhx\n", tag->raw[i],
                tag->raw[i + 1], tag->raw[i + 2], tag->raw[i + 3]);
    }
}

void print_locks(struct NFCTag *tag) {

    fprintf(stderr, "Block lock 4-9: ");
    if (tag->lock_bytes >> 1 & 0x1) {
        fprintf(stderr, "[LOCKED]\n");
    } else {
        fprintf(stderr, "\n");
    }

    fprintf(stderr, "Block lock 10-15: ");
    if (tag->lock_bytes >> 2 & 0x1) {
        fprintf(stderr, "[LOCKED]\n");
    } else {
        fprintf(stderr, "\n");
    }

    fprintf(stderr, "OTP block lock: ");
    if (tag->lock_bytes & 0x1) {
        fprintf(stderr, "[LOCKED]\n");
    } else {
        fprintf(stderr, "\n");
    }

    fprintf(stderr, "OTP lock:     %08x  ", tag->OTP);
    if (tag->lock_bytes >> 3 & 0x1) {
        fprintf(stderr, "[LOCKED]\n");
    } else {
        fprintf(stderr, "\n");
    }

    fprintf(stderr, "User Data locks:\n");
    for (int i = 0; i < 48; i += 4) {
        fprintf(stderr, "%02hhx %02hhx %02hhx %02hhx\n", tag->raw[i + 16],
                tag->raw[i + 1 + 16], tag->raw[i + 2 + 16], tag->raw[i + 3 + 16]);
        if (tag->lock_bytes >> ((i / 4) + 4) & 0x1) {
            fprintf(stderr, "[LOCKED]\n");
        } else {
            fprintf(stderr, "\n");
        }
    }
}

#endif // DEBUG

void clear_screen() {
    char buf[1024];
    char *str;

    tgetent(buf, getenv("TERM"));
    str = tgetstr("cl", NULL);
    fputs(str, stdout);
}

void update_wallet_serials(int walletfd, screen_data *data) {
    int res = wallet_num_cards(walletfd, data->wallet_id, &data->wallet_tag_amount);

    if (print_wallet_error(res) != 0) {
        puts("Wallet listing failed!");
        exit(1);
    }

    for (unsigned i = 0; i < data->wallet_tag_amount; i++) {
        res = wallet_get_card(walletfd, data->wallet_id, i, data->wallet_tag_serials[i]);
        if (print_wallet_error(res) != 0) {
            puts("Wallet listing failed!");
            exit(1);
        }
    }
}

void buy_ticket(int walletfd, screen_data *data) {
    char user_name[NFCTAG_USER_SIZE + 1];
    char serial_hex[NFCTAG_SERIAL_FULL_SIZE * 2 + 1];
    char event_id_hex[NFCTAG_EVENT_ID_SIZE * 2 + 1];
    uint8_t event_id[NFCTAG_EVENT_ID_SIZE];

    puts("\nPlease provide the 16-bytes id of the event.");
    printf("> ");

    get_string(event_id_hex, sizeof(event_id_hex));
    hex_to_bytes(event_id_hex, event_id, sizeof(event_id));

    printf("\nPlease provide your name for the event (max length is %zu).\n",
        sizeof(user_name) - 1);
    puts("Don't worry, you can change this later.");
    printf("> ");

    get_string(user_name, sizeof(user_name));

    int res = wallet_buy_ticket(walletfd, data->wallet_id, event_id, user_name,
        data->wallet_tag_serials[data->wallet_tag_amount]);

    if (print_wallet_error(res) != 0) {
        puts("Ticket purchase failed.");
    } else {
        bytes_to_hex(serial_hex, data->wallet_tag_serials[data->wallet_tag_amount], 6);
        data->wallet_tag_amount++;
        printf("Your new ticket for the event %s, under the name of %s, has "
               "been stored in your wallet with serial No. %s",
               event_id_hex, user_name, serial_hex);
    }

    puts("\nPress ENTER to return to the main menu");
    getchar();
}

void buy_vip_ticket(int walletfd, screen_data *data) {
    char user_name[NFCTAG_USER_SIZE + 1];
    char vip_code_hex[EVENT_VIP_INV_CODE_SIZE * 2 + 1];
    char event_id_hex[NFCTAG_EVENT_ID_SIZE * 2 + 1];
    char serial_hex[NFCTAG_SERIAL_FULL_SIZE * 2 + 1];
    uint8_t event_id[NFCTAG_EVENT_ID_SIZE];
    uint8_t vip_code[EVENT_VIP_INV_CODE_SIZE];

    puts("\nPlease provide the 16-bytes id of the event.");
    printf("> ");

    get_string(event_id_hex, sizeof(event_id_hex));
    hex_to_bytes(event_id_hex, event_id, sizeof(event_id));

    puts("\nPlease provide the 16-bytes VIP invitation code for the event.");
    printf("> ");

    get_string(vip_code_hex, sizeof(vip_code_hex));
    hex_to_bytes(vip_code_hex, vip_code, sizeof(vip_code));

    printf("\nPlease provide your name for the event (max length is %zu).\n",
        sizeof(user_name) - 1);
    puts("Don't worry, you can change this later.");
    printf("> ");

    get_string(user_name, sizeof(user_name));

    int res = wallet_buy_vip_ticket(walletfd, data->wallet_id, event_id, user_name,
        vip_code, data->wallet_tag_serials[data->wallet_tag_amount]);
    if (print_wallet_error(res) != 0) {
        puts("Ticket purchase failed.");
    } else {
        bytes_to_hex(serial_hex, data->wallet_tag_serials[data->wallet_tag_amount], 6);
        data->wallet_tag_amount++;
        printf("Your new VIP ticket for the event %s, under the name of %s, "
               "has been stored in your wallet with serial No. %s",
               event_id_hex, user_name, serial_hex);
    }

    puts("\nPress ENTER to return to the main menu");
    getchar();
}

void list_tickets(const screen_data *data) {
    char serial_hex[NFCTAG_SERIAL_FULL_SIZE * 2 + 1] = {0};
    clear_screen();

    puts("\nTicket Serial");
    puts("-------------");

    for (unsigned i = 0; i < data->wallet_tag_amount; i++) {
        bytes_to_hex(serial_hex, data->wallet_tag_serials[i],
                     sizeof(data->wallet_tag_serials[i]));
        puts(serial_hex);
    }

    puts("\nPress ENTER to return to the main menu");
    getchar();
}

void ticket_detail(int walletfd, screen_data *data) {
    char ticket_serial_hex[NFCTAG_SERIAL_FULL_SIZE * 2 + 1];
    char event_id_hex[NFCTAG_EVENT_ID_SIZE * 2 + 1];
    uint8_t ticket_serial[NFCTAG_SERIAL_FULL_SIZE];
    struct NFCTag ticket;

    puts("\nPlease provide the 6-bytes serial of the ticket.");
    printf("> ");

    get_string(ticket_serial_hex, sizeof(ticket_serial_hex));
    hex_to_bytes(ticket_serial_hex, ticket_serial, sizeof(ticket_serial));

    for (unsigned i = 0; i < NFCTAG_N_PAGES; i++) {
        int res = wallet_read_page(walletfd, data->wallet_id, ticket_serial, i,
                                   ticket.raw + NFCTAG_PAGE_OFF(i));
        if (print_wallet_error(res) != 0) {
            puts("Error reading ticket!");
            goto back_to_main_menu;
        }
    }

    bytes_to_hex(event_id_hex, ticket.event_id, sizeof(ticket.event_id));
    printf("Loaded ticket with serial No. %s.\n", ticket_serial_hex);
    printf("This ticket is for the event with id %s.\n", event_id_hex);
    printf("It is under the name of %.*s.\n", (int)sizeof(ticket.user),
        ticket.user);

    if ((ticket.OTP & 0x01000000) == 0) {
        puts("Your ticket is a VIP ticket! Please proceed to the VIP "
             "entrance when reaching the venue.\n");
    }

    if (ticket.OTP & 0x00000001)
        puts("Your ticket has already been used!");

    if (*ticket.seat) {
        printf("Your ticket has seat %.*s assigned.\n",
            (int)sizeof(ticket.seat), ticket.seat);
    } else {
        puts("Your ticket doesn't have a seat assigned yet.");
    }

#ifdef DEBUG
    pretty_print(&ticket);
    puts("-----------------");
    raw_dump(&ticket);
    puts("-----------------");
    print_locks(&ticket);
#endif

back_to_main_menu:
    puts("\nPress ENTER to return to the main menu");
    getchar();
}

void change_name(int walletfd, const screen_data *data) {
    char user_name[NFCTAG_USER_SIZE + 1];
    char ticket_serial_hex[NFCTAG_SERIAL_FULL_SIZE * 2 + 1];
    uint8_t ticket_serial[NFCTAG_SERIAL_FULL_SIZE];

    puts("\nPlease provide the 6-bytes serial of the ticket.");
    printf("> ");

    get_string(ticket_serial_hex, sizeof(ticket_serial_hex));
    hex_to_bytes(ticket_serial_hex, ticket_serial, sizeof(ticket_serial));

    printf("\nPlease provide your new name for the event (max length is %zu).",
        sizeof(user_name) - 1);
    printf("> ");

    get_string(user_name, sizeof(user_name));

    for (unsigned i = 0; i < NFCTAG_USER_SIZE / NFCTAG_PAGE_SIZE; i++) {
        // Write name in name field of ticket
        int res = wallet_write_page(walletfd, data->wallet_id, ticket_serial,
            NFCTAG_USER_PAGE + i, user_name + i * NFCTAG_PAGE_SIZE);
        if (print_wallet_error(res) != 0) {
            puts("Error writing ticket.");
            goto back_to_main_menu;
        }
    }

    printf("Updated name on ticket with serial No. %s.\n", ticket_serial_hex);

back_to_main_menu:
    puts("\nPress ENTER to return to the main menu");
    getchar();
}

int main(int argc, char **argv) {
    char wallet_id_hex[WALLET_ID_SIZE];
    struct sockaddr_in sa = {};
    screen_data data = {};
    int walletfd;

    if (argc != 3) {
        fprintf(stderr, "Usage: %s IP PORT\n", argv[0] ?: "wallet-client");
        return 1;
    }

    clear_screen();
    puts("Connecting to remote wallet...");

    if ((walletfd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        puts("Socket creation failed!");
        return 1;
    }

    sa.sin_family = AF_INET;
    sa.sin_port = htons(strtoul(argv[2], NULL, 10));
    sa.sin_addr.s_addr = inet_addr(argv[1]);

    if (sa.sin_addr.s_addr == INADDR_NONE) {
        puts("Invalid wallet address!");
        return 1;
    }

    if (connect(walletfd, (struct sockaddr *)&sa, sizeof(sa)) != 0) {
        clear_screen();
        puts("Connection with the remote wallet failed!");
        return 0;
    }

    clear_screen();
    puts("Connected to the remote wallet");

    char choice = 0;
    do {
        puts("\nDo you already have a wallet? (y/n)");
        printf("> ");

        choice = getchar();
        if (choice == EOF)
            exit(1);

        flush_stdin();
    } while (choice != 'y' && choice != 'n');

    if (choice == 'n') {
        clear_screen();

        puts("Please wait while we create a new wallet for you...");
        if (print_wallet_error(wallet_create_wallet(walletfd, data.wallet_id)) != 0) {
            puts("Wallet creation failed.");
            return 1;
        }

        bytes_to_hex(wallet_id_hex, data.wallet_id, 16);
    } else {
        puts("\nPlease insert your wallet ID to access its content");
        printf("> ");

        get_string(wallet_id_hex, sizeof(wallet_id_hex));
        hex_to_bytes(wallet_id_hex, data.wallet_id, sizeof(data.wallet_id));
    }

    puts("Downloading wallet content...");
    update_wallet_serials(walletfd, &data);

    while (1) {
        unsigned choice;
        clear_screen();

        printf("Current wallet id: %s\n", wallet_id_hex);
        printf("You have %hhu tickets in your wallet.\n", data.wallet_tag_amount);
        puts("Main menu:");
        puts("  1. Buy new ticket");
        puts("  2. Buy new VIP ticket");
        puts("  3. List your tickets");
        puts("  4. View ticket details");
        puts("  5. Change the name on a ticket");
        puts("  6. Leave");
        printf("> ");

        if (get_uint(&choice) != 0)
            continue;

        switch (choice) {
        case 1:
            buy_ticket(walletfd, &data);
            break;
        case 2:
            buy_vip_ticket(walletfd, &data);
            break;
        case 3:
            list_tickets(&data);
            break;
        case 4:
            ticket_detail(walletfd, &data);
            break;
        case 5:
            change_name(walletfd, &data);
            break;
        case 6:
            puts("Bye.");
            return 0;
        default:
            break;
        }
    }

    return 0;
}
