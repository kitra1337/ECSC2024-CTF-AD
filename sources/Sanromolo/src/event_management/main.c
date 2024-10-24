#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include "common/event.h"
#include "common/util.h"
#include "common/wallet_api.h"
#include "wallet/comm_types.h"
#include "wallet/nfclib.h"

#define WALLET_HOSTNAME "wallet"
#define WALLET_PORT     1337

int hostname_to_ip(char *hostname, char *ip) {
    struct hostent *he;
    struct in_addr **addr_list;
    unsigned i;

    if ((he = gethostbyname(hostname)) == NULL)
        return -1;

    addr_list = (struct in_addr **)he->h_addr_list;
    for (i = 0; addr_list[i] != NULL; i++) {
        // Return the first one;
        strcpy(ip, inet_ntoa(*addr_list[i]));
        return 0;
    }

    return -1;
}

void read_whole_ticket(int walletfd, const uint8_t *wallet_id,
                       const uint8_t *ticket_serial, struct NFCTag *ticket) {
    for (unsigned i = 0; i < NFCTAG_N_PAGES; i++) {
        if (print_wallet_error(wallet_read_page(walletfd, wallet_id,
                ticket_serial, i, ticket->raw + i * NFCTAG_PAGE_SIZE)) != 0) {
            puts("Error reading ticket.");
            exit(1);
        }
    }
}

void proceed_to_seat(int walletfd, uint8_t *wallet_id, uint8_t *ticket_serial,
                     uint8_t *event_id) {
    struct Event e;
    char seat_str[5];
    unsigned seat;

    puts("At which seat do you want to sit? It looks like no one is actually "
         "looking...");

    while (1) {
        printf("> ");

        get_string(seat_str, sizeof(seat_str));
        seat = strtoul(seat_str, NULL, 10);
        if (seat <= 999)
            break;

        puts("There doesn't seem to be a seat with that number!");
    }

    if (seat >= 100) {
        printf("You sit in seat %u. No one questions you.\n", seat);
    } else {
        struct NFCTag ticket;

        puts("As soon as you enter the VIP section security approaches you "
             "asking for your ticket.");

        read_whole_ticket(walletfd, wallet_id, ticket_serial, &ticket);

        unsigned actual_seat = strtoul(ticket.seat, NULL, 0);
        if (actual_seat >= 100) {
            puts("You are escorted out of the venue by security for trying to "
                 "enter the VIP area without a VIP ticket.");
            exit(1);
        } else {
            printf("~ I'm sorry for not recognising you mr *looks quickly at his "
                   "screen*... %.*s!\n", (int)sizeof(ticket.user), ticket.user);

            if (seat == actual_seat) {
                puts("~ Hope you like the show, have a good evening!");
            } else {
                puts("~ Please allow me to show you to your seat.");
                seat = actual_seat;
            }
        }
    }

    if (get_event_data(event_id, &e) != 0) {
        puts("Unable to load event data.");
        exit(1);
    }

    while (1) {
        unsigned choice;

        puts("What do you want to do?");
        puts("  1. Ask the star for an autograph");
        puts("  2. Leave");
        printf("> ");

        if (get_uint(&choice) != 0) {
            puts("Invalid option.");
            continue;
        }

        switch (choice) {
        case 1:
            if (seat >= 100) {
                puts("You wave and wave your hand, only for the star to pass "
                     "near the VIP section, completely ignoring you. ");
                puts("Security throws you out for interfering with the festival.");
                exit(1);
            } else {
                puts("The star actually notices you! After all you are seated "
                     "first row, you must be someone important...");
                printf("You manage to get the star's autograph: %s\n",
                       e.star_signature);
                puts("You fall to the ground in excitement and are removed by "
                     "security.");
                exit(0);
            }
            break;
        case 2:
            puts("Thanks for visiting! Have a great day!");
            exit(0);
            break;
        default:
            puts("Unknown option.");
            break;
        }
    }
}

void create_event(void) {
    char path[sizeof(EVENT_DIRECTORY) + 128];
    struct Event e;

    if (get_rand_bytes(&e.id, sizeof(e.id)) != sizeof(e.id))
        exit(1);

    if (get_rand_bytes(&e.vip_invitation_code, sizeof(e.vip_invitation_code))
            != sizeof(e.vip_invitation_code))
        exit(1);

    e.name = calloc(1, EVENT_NAME_LEN + 1);
    e.star_signature = calloc(1, EVENT_STAR_SIGNATURE_LEN + 1);

    puts("Welcome to the event creation system!");
    puts("Please provide the name of your event:");
    printf("> ");

    get_string(e.name, EVENT_NAME_LEN + 1);

    puts("Please have your star sign this document to confirm partecipation:");
    printf("> ");

    get_string(e.star_signature, EVENT_STAR_SIGNATURE_LEN + 1);

    strcpy(path, EVENT_DIRECTORY);
    bytes_to_hex(path + sizeof(EVENT_DIRECTORY) - 1, e.id, sizeof(e.id));

    int eventfd = open(path, O_CREAT | O_RDWR, 0664);
    if (eventfd < 0) {
        puts("Unexpected error creating the event");
        exit(1);
    }

    write_exactly(eventfd, e.id, sizeof(e.id));
    write_exactly(eventfd, e.vip_invitation_code, sizeof(e.vip_invitation_code));
    write_exactly(eventfd, e.name, EVENT_NAME_LEN);
    write_exactly(eventfd, e.star_signature, EVENT_STAR_SIGNATURE_LEN);
    close(eventfd);

    printf("Event \"%s\" successfully created!\n", e.name);
    printf("Your event id is: ");
    for (size_t i = 0; i < sizeof(e.id); i++)
        printf("%02hhx", e.id[i]);

    printf("\nYour VIP invitation code is: ");
    for (size_t i = 0; i < sizeof(e.vip_invitation_code); i++)
        printf("%02hhx", e.vip_invitation_code[i]);
    puts("\n");

    free(e.star_signature);
    free(e.name);
    return;
}

void join_event(void) {
    struct sockaddr_in sa = {};
    char remote[128] = {0};
    char user_name[sizeof_field(struct NFCTag, user) + 1];
    char event_id_hex[33];
    char wallet_id_hex[33];
    char ticket_serial_hex[13];
    uint8_t event_id[16];
    uint8_t wallet_id[16];
    uint8_t ticket_serial[6];
    struct NFCTag ticket, check_ticket;
    struct Event e;
    uint8_t num_tickets;
    unsigned seed, rand_seat;
    int walletfd;

    get_rand_bytes(&seed, sizeof(seed));
    srand(seed);

    puts("Please provide the 16-byte id of the event you want to join.");
    printf("> ");

    get_string(event_id_hex, sizeof(event_id_hex));
    hex_to_bytes(event_id_hex, event_id, sizeof(event_id));

    if (get_event_data(event_id, &e) != 0) {
        puts("There is no event with the id you specified.");
        exit(1);
    }

    // Not needed here
    free(e.star_signature);

    printf("You are joining the event \"%s\". Please provide the 16-byte "
           "address of your wallet.\n", e.name);
    printf("> ");

    get_string(wallet_id_hex, sizeof(wallet_id_hex));
    hex_to_bytes(wallet_id_hex, wallet_id, sizeof(wallet_id));

    puts("Please provide the 6-byte serial of your ticket.");
    printf("> ");

    get_string(ticket_serial_hex, sizeof(ticket_serial_hex));
    hex_to_bytes(ticket_serial_hex, ticket_serial, sizeof(ticket_serial));

    puts("Please wait while we connect to your wallet and validate your ticket...");

    walletfd = socket(AF_INET, SOCK_STREAM, 0);
    if (walletfd == -1) {
        printf("Socket creation failed...\n");
        exit(1);
    }

    if (hostname_to_ip(WALLET_HOSTNAME, remote) != 0) {
        printf("Could not resolve wallet hostname...\n");
        exit(1);
    }

    sa.sin_family = AF_INET;
    sa.sin_port = htons(WALLET_PORT);
    sa.sin_addr.s_addr = inet_addr(remote);

    if (connect(walletfd, (struct sockaddr *)&sa, sizeof(sa)) != 0) {
        puts("Connection with the wallet failed...");
        exit(1);
    }

    puts("Connected to the wallet.");

    if (wallet_num_cards(walletfd, wallet_id, &num_tickets) != ACK) {
        puts("Sorry, your wallet doesn't seem to exist or is not readable.");
        exit(1);
    }

    if (num_tickets == 0) {
        puts("Sorry, you don't seem to have any ticket in your wallet.");
        exit(1);
    }

    read_whole_ticket(walletfd, wallet_id, ticket_serial, &ticket);
    if (memcmp(ticket.event_id, event_id, sizeof(event_id)) != 0) {
        puts("Sorry, this ticket seems to be for a different event.");
        exit(1);
    }

    if (ticket.OTP & 0x00000001) {
        puts("Sorry, it appears this ticket has already been used.");
        exit(1);
    }

    // Seats [0,99] for VIP, seats [100,999] otherwise.
    if ((ticket.OTP & 0x01000000) == 0)
        rand_seat = rand() % (99 - 0 + 1) + 0;
    else
        rand_seat = rand() % (999 - 100 + 1) + 100;

    snprintf(ticket.seat, sizeof(ticket.seat), "%u", rand_seat);
    if (wallet_write_page(walletfd, wallet_id, ticket_serial, NFCTAG_SEAT_PAGE, &ticket.seat) != ACK) {
        puts("Failed to write seat to ticket");
        exit(1);
    }

    ticket.OTP |= 0x00000001;
    if (wallet_write_page(walletfd, wallet_id, ticket_serial, NFCTAG_OTP_PAGE, &ticket.OTP) != ACK) {
        puts("Failed to write used field to ticket");
        exit(1);
    }

    ticket.lock_bytes = 0xfff0;
    // Heh, let's just hardcode these
    _Static_assert(offsetof(struct NFCTag, lock_bytes) == 8 + 2);
    if (wallet_write_page(walletfd, wallet_id, ticket_serial, 2, ticket.raw + 8) != ACK) {
        puts("Failed to lock ticket");
        exit(1);
    }

    memcpy(user_name, ticket.user, sizeof(ticket.user));
    read_whole_ticket(walletfd, wallet_id, ticket_serial, &check_ticket);

    // BUG: only data after the header is chceked and the header itself is not,
    // so its content may be different than expected. In particular, the lock
    // bytes can lock themselves and therefore prevent their modification. Since
    // wallet_write_page() does not report on write failure due to locking,
    // wirte success must be checked by re-reading the data back (which is what
    // is done here).
    if (memcmp(ticket.raw + 12, check_ticket.raw + 12, sizeof(ticket.raw) - 12)) {
        puts("Sorry, it seems like your ticket is broken!");
        exit(1);
    }

    puts("Your ticket has been validated!");
    printf("Welcome to the venue for %s Mr. %s!\n", e.name, user_name);
    printf("Your assigned seat is %.*s.\n", (int)sizeof(ticket.seat),
        ticket.seat);
    free(e.name);

    while (1) {
        unsigned choice;

        puts("What do you want to do?");
        puts("  1. Proceed to seat");
        puts("  2. Leave");
        printf("> ");

        if (get_uint(&choice) != 0) {
            puts("Invalid option.");
            continue;
        }

        switch (choice) {
        case 1:
            proceed_to_seat(walletfd, wallet_id, ticket_serial, event_id);
            break;
        case 2:
            puts("Thanks for visiting! Have a great day!");
            exit(0);
            break;
        default:
            puts("Unknown option.");
            break;
        }
    }
}

void setbufs(void) {
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
    setbuf(stdin, NULL);
}

void print_banner() {
    puts(
        "  ____                                        _              \n"
        " / ___|  __ _ _ __  _ __ ___  _ __ ___   ___ | | ___         \n"
        " \\___ \\ / _` | '_ \\| '__/ _ \\| '_ ` _ \\ / _ \\| |/ _ \\        \n"
        "  ___) | (_| | | | | | | (_) | | | | | | (_) | | (_) |       \n"
        " |____/ \\__,_|_| |_|_|  \\___/|_| |_| |_|\\___/|_|\\___/        \n"
        "  _____         _   _            _   ____   ___ ____  _  _   \n"
        " |  ___|__  ___| |_(_)_   ____ _| | |___ \\ / _ \\___ \\| || |  \n"
        " | |_ / _ \\/ __| __| \\ \\ / / _` | |   __) | | | |__) | || |_ \n"
        " |  _|  __/\\__ \\ |_| |\\ V / (_| | |  / __/| |_| / __/|__   _|\n"
        " |_|  \\___||___/\\__|_| \\_/ \\__,_|_| |_____|\\___/_____|  |_|  \n"
        "  _____ ____ ____   ____   _____    _ _ _   _                \n"
        " | ____/ ___/ ___| / ___| | ____|__| (_) |_(_) ___  _ __     \n"
        " |  _|| |   \\___ \\| |     |  _| / _` | | __| |/ _ \\| '_ \\    \n"
        " | |__| |___ ___) | |___  | |__| (_| | | |_| | (_) | | | |   \n"
        " |_____\\____|____/ \\____| |_____\\__,_|_|\\__|_|\\___/|_| |_|   \n"
        "\n"
    );
}

int main() {
    setbufs();
    print_banner();

    while (1) {
        unsigned choice;

        puts("What do you want to do?");
        puts("  1. Join an event");
        puts("  2. Create an event");
        puts("  3. Leave");
        printf("> ");

        if (get_uint(&choice) != 0) {
            puts("Invalid option.");
            continue;
        }

        switch (choice) {
        case 1:
            join_event();
            break;
        case 2:
            create_event();
            break;
        case 3:
            puts("Thanks for visiting! Have a great day!");
            exit(0);
            break;
        default:
            puts("Unknown option.");
            break;
        }
    }

    return 0;
}
