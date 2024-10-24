# Sanromolo

| Service    | Sanromolo                                                 |
| :--------- | :-------------------------------------------------------- |
| Authors    | Alberto Carboneri <@Alberto247>, Marco Bonelli <@mebeim>  |
| Stores     | 1                                                         |
| Categories | misc, pwn                                                 |
| Ports      | TCP 1337, 1338                                            |
| FlagIds    | store1: [event_id]                                        |
| Checker    | [store1](/checkers/Sanromolo/chceker/__main__.py)         |


## Description

This challenge consists of two services:

- A NFC tag reader/writer *"wallet"* service listening for connections on TCP
  port 1337 and running the [`wallet`](/services/Sanromolo/dist/wallet)
  binary to handle each conncetion. This *wallet* service implements a binary
  protocol where commands can be sent to create NFC tags and perform actions on
  them.

- An *"event management"* service listening for connections on TCP port 1338 and
  running the [`event-manager`](/services/Sanromolo/dist/wallet) binary to
  handle each connection. This *event manager* service implements a textual
  protocol and allows to create "events" and use NFC tickets to join the events.

In addition to those two, a third
[`wallet-client`](/services/Sanromolo/dist/wallet) binary is also available
to use as a client to interact with the *wallet* service.

All the binaries are Linux x86-64 ELFs, built with all protections except for
`wallet-client` which is compiled without `_FORTIFY_SOURCE` (for easier reverse
engineering).

### NFC Tags (Tickets)

Both services manipulate NFC tags that are used as "tickets" to access events. A
tag/ticket is composed of 16 pages of 4 bytes each, for a total of 64 bytes, and
looks like this:

```c
#define NFCTAG_PAGE_SIZE 4

struct NFCTag {
    union {
        struct {
            // Page 0
            uint8_t manufacturer;
            uint8_t serial_part_1[2];
            uint8_t check_byte_1;
            // Page 1
            uint8_t serial_part_2[NFCTAG_PAGE_SIZE];
            // Page 2
            uint8_t check_byte_2;
            uint8_t internal;
            uint16_t lock_bytes;
            // Page 3
            uint32_t OTP;
            // Pages 4..7
            uint8_t event_id[NFCTAG_PAGE_SIZE * 4];
            // Page 8
            char seat[NFCTAG_PAGE_SIZE];
            // Pages 9..15
            char user[NFCTAG_PAGE_SIZE * 7];
        };
        uint8_t raw[NFCTAG_PAGE_SIZE * NFCTAG_N_PAGES];
    };
};
```

A tag is composed of a 3-page "header", a OTP page and a 12-page body where
arbitrary data can be stored. Reading/writing to tags and part of the NFC tags'
embedded functionality is handled by the `wallet` service.

- All pages can be read.
- The 10-byte ticket header (up to and including the `internal` field) can never
  be written to.
- Only bytes in non-locked pages can be written to.
- All the bits in the `OTP` pages can only be set, but not unset.
- Page 2 holds an important bitmask (`lock_bytes`) used to lock other pages so
  that they cannot be written. In particular, the lowest 3 bits of `lock_bytes`
  control locking of the other 3 lock bytes and can only be set (not unset). The
  other 3 bytes control the locking of the pages from 3 to 15 and can also only
  be set (not unset).

The above core properties are checked by the `nfc_set_byte()` function
implemented in ([`src/wallet/nfclib.c`](src/wallet/nfclib.c)).

Since tags/tickets are used to access "events" (through the *event manager*
service), as can be seen above, the space after the `OTP` page is used to hold
information about the event they were "purchased" for (`event_id`), the owner's
name (`user`) and their assigned `seat`. Less obvious, a couple of important
bits of information are stored using the `OTP` value: one bit indicating whether
a ticket has been used or not, and another bit indicating whether a ticket
grants "VIP access" to an event or not.

### Wallet Service

As already said, tags/tickets can only be read or written through the *wallet*
service, which essentially mimicks a remote NFC tag reader/writer.

The service accepts commands using a binary communication protocol. It allows to
create "wallets", create tags (buy tickets) inside wallets and manipulate them.
Wallets are simply filesystem directories named after the hex-encoded walled ID
and tags are files within those directories.

Each command consists of a 1-byte length, followed by a 1-byte command type
identifier and a command body. The body itself is composed of a 16-byte walled
ID (always present) plus additional command data whose content varies for each
command. A 2-byte ISO 14443a CRC follows the body and is checked by the service.

```c
struct Command {
    union {
        struct {
            uint8_t length;
            uint8_t type;
            uint8_t wallet_id[WALLET_ID_SIZE];
            union {
                struct BuyUserCommand buy_user;
                struct BuyVIPCommand buy_vip;
                struct WriteCommand write;
                struct ReadCommand read;
                struct GetCardCommand get_card;
            } data;
        };
        uint8_t raw[0x100];
    };
};
```

The available commands acceped by the *wallet* service are:

- `CreateWallet` (`0x99`): create a new wallet and return its ID. This command
  does not have an associated data and is the only command that ignores the
  mandatory `wallet_id` field.
- `BuyUser` (`0x59`): buy a new ticket (tag), add it to a given (existing)
  wallet and return the ticket serial.
- `BuyVIP` (`0x95`): buy a new special "VIP" ticket (tag) given a valid VIP
  invitation code, add it to a given (existing) wallet and return the ticket
  serial.
- `Read` (`0x30`): read a page from a specific tag given a wallet ID and
  ticket ID.
- `Write` (`0xA2`): write a page to a specific tag given a wallet ID and
  ticket ID and return its content (4 bytes).
- `NumCards` (`0x75`): get the current number of tags in a given wallet.
  This command also does not have any associated data.
- `GetCard` (`0x39`): get the ID of the n-th tag inside a given wallet.

All commands that are accepted by the *wallet* service are answered with a
binary response that contains a 1-byte length followed by a response code,
variable-length response data (if any) and a 2-byte ISO 14443a CRC.

```c
enum ResponseCode {
    ACK     = 0xA,
    InvArg  = 0x0,
    CRCErr  = 0x1,
    Unknown = 0x9,
};
```

Commands can either succeed (`ACK`), fail because of invalid parameters
(`InvArg`), get rejected because of a bad CRC (`CRCErr`), or fail in a bad
"unknown" status if things go really wrong (system errors like failed syscalls).

**One important detail** to point out is that the `Write` commands will always
return an `ACK` response code even if no bytes (or only some bytes) were
successfully written to the tag. To be certain of a successful write, a second
`Read` command should be sent to read and then verity the new content of the
written page.

### Event Manager Service

The *event manager* offers a text-based protocol that can be used to create
events or join new events:

- To create an event, one must specify the event's name and provide the
  signature of the "star" performing the event (the flag). This information is
  stored in simple binary files (one per event named using the hex-encoded event
  ID). After creating an event, the *event manager* will return the randomly
  generated 16-byte event ID and a randomly generated 16-byte VIP invite code
  that can be used to purchase VIP tickets through the *wallet* service.

- To join an event, one must specify a wallet ID and ticket ID. The *wallet*
  service is then contacted internally to read the ticket. The *event manager*
  reads the user's access level (either VIP access or not), assigns a seat to
  the user based on its access level and grants access to the event.

When joining an event, tickets are "validated" by flipping one of the "one time"
use bits in the ticket's `OTP` page. A ticket that was already used cannot be
re-used to join an event again.

The interesting thing about VIP users is that they are granted first-row seats
to events and will be able to request the star's signature (autograph) through
the *event manager* service after joining the event and being seated.

Assigned seats are selected at event join time and written to the ticket's
`seat` page. This page is then locked by flipping the appropriate bit in the
`lock_bytes` bitmask in the ticket's header.


## Vulnerabilities

The flags for this challenge are the signatures (autographs) of the event stars.
Each event has its own star signature associated with it, and only VIP users
(that join an event using a VIP ticket) should be able to get an autograph. The
flag IDs are therefore event IDs, and the goal is to get the event manager to
let us join an event as VIP and sit in the front row unbothered, where we will
be able to get an autograph.

### Vuln 1 - Unchecked NFC tag lock bits

The [`event-management`](/services/Sanromolo/dist/event-management) binary
interacts with the [`wallet`](/services/Sanromolo/dist/wallet) throguh a
connection to retrieve the ticket the user presented.

After validation, the seat is then written to the ticket with a `Write` command,
and the correponding page is locked through the `lock_bytes` functionality.
Then, the content of the data pages is checked, validating the content to avoid
race conditions during the `Write` action.

Here is a snippet from `join_event()`:

```c
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
    _Static_assert(offsetof(struct NFCTag, lock_bytes) == 8 + 2);
    if (wallet_write_page(walletfd, wallet_id, ticket_serial, 2, ticket.raw + 8) != ACK) {
        puts("Failed to lock ticket");
        exit(1);
    }

    memcpy(user_name, ticket.user, sizeof(ticket.user));
    read_whole_ticket(walletfd, wallet_id, ticket_serial, &check_ticket);

    if (memcmp(ticket.raw + 12, check_ticket.raw + 12, sizeof(ticket.raw) - 12)) {
        puts("Sorry, it seems like your ticket is broken!");
        exit(1);
    }

    puts("Your ticket has been validated!");
```

While the code correctly checks the data written to the ticket, the content of
the `lock_bytes` field is not properly checked. An attacker is able to use the
`lock_bytes` functionality to lock the `lock_bytes` page itself. It is then
possible to edit the ticket after validation, changing the seat to one in
the rage [0,99], enabling VIP access and retrieving the flag.

#### Patching

The simplest patch for the vulnerability would be to patch the `memcmp()`
performed in `join_event()` to check the whole ticket and ensure that
`lock_bytes` was written successfully:

```diff
-    if (memcmp(ticket.raw + 12, check_ticket.raw + 12, sizeof(ticket.raw) - 12)) {
+    if (memcmp(ticket.raw, check_ticket.raw, sizeof(ticket.raw))) {
```

Since the source code was not provided, this needs to be done patching the
binary itself:

```diff
 00000000000029a4 <wallet_write_page>:
     ...
-    203d:       48 8d b4 24 9c 00 00    lea    rsi,[rsp+0x9c]
+    203d:       48 8d b4 24 90 00 00    lea    rsi,[rsp+0x90]
     2044:       00
-    2045:       48 8d 7c 24 5c          lea    rdi,[rsp+0x5c]
+    2045:       48 8d 7c 24 50          lea    rdi,[rsp+0x50]
-    204a:       ba 34 00 00 00          mov    edx,0x34
+    204a:       ba 40 00 00 00          mov    edx,0x40
     204f:       e8 bc f2 ff ff          call   1310 <memcmp@plt>
     ...
```


### Vuln 2 - Missing error check + uninitialized stack reuse

The [`wallet`](/services/Sanromolo/dist/wallet) implements the `Read` and
`Write` commands using helper functions that first read the entire ticket from
disk into a `struct NFCTag` that is on the stack of the command handler
functions. The functions are `read_page()` and `write_page()` in
[`src/wallet/comms.c`](src/wallet/comms.c).

Here's a snippet from `read_page()`:

```c
void read_page(struct Command *command, struct Response *response) {
    struct NFCTag ticket;
    //...

    if (check_wallet_exists(command) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    get_ticket_data(command->wallet_id, command->data.read.ticket_id, &ticket);

    if (nfc_verify_tag(&ticket) != 0) {
        prepare_error_response(response, InvArg);
        return;
    }

    // Send response back with page content...
}
```

In case the provided wallet ID (`command->wallet_id`) does not exist, the
`get_ticket_data()` function fails to find the corresponding file on disk anr
returns an error without reading anything into the passed `&ticket`. This error
should be checked by the caller, but the check is missing. Therefore, if the
function fails the `struct NFCTag ticket` on the stack of the function will be
left uninitialized. If the `nfc_verify_tag()` check passes, 4 bytes of data from
the dirty stack frame will be returned in the response.

The handler for the `BuyVIP` command takes the following values as input:

- A wallet ID (like any other command)
- An event ID (exactly 16 bytes).
- A VIP invitation code (exactly 16 bytes).
- A user name (max 28 bytes).

It then first partially populates the `->user` field of a `struct NFCTag` on the
stack, then reads the event details into another `struct Event` that is also on
the stack, and then proceeds to verify if the provided VIP invitation code
matches the one of the event. This is implemented in the `buy_vip_ticket()`
function of [`src/wallet/comms.c`](src/wallet/comms.c):

```c
void buy_vip_ticket(struct Command *command, struct Response *response) {
    struct NFCTag ticket;
    struct Event event;
    // ...

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

    // Initialize rest of ticket and return its serial...
}
```

As it turns out, the stack frames of `buy_vip_ticket()` and `read_page()` align
almost perfectly: the end of the `ticket` in `buy_vip_ticket()` overlaps with
the header of the `ticket` in `read_page()`, and the `event` in
`buy_vip_ticket()` overlaps with the body of the `ticket` in `read_page()`.

If we try to buy a VIP ticket for a given event using a carefully crafted `user`
plus any invalid VIP invitation code, and then try to read a page from a
non-existing ticket, we can pass the `nfc_verify_tag()` check in `read_page()`
and get data from the `event` that was previusly in the stack frame of
`buy_vip_ticket()`. In particular, if we pass the check and try to read pages
from index 10 to 13 (inclusive) we will leak the VIP invitation code for the
event that was previously requested when trying to buy the VIP ticket. This
invitation code can then be used to buy a real VIP ticket, which in turns can be
provided to the *event manager* service to get the star autograph (i.e. the
flag).

See more details in
[`exploits/Sanromolo/README.md`](/exploits/Sanromolo/README.md) and the
full exploit code in
[`expl_stack_reuse.py`](/exploits/Sanromolo/expl_stack_reuse.py).

#### Patching

Patching this vulnerability to make it unexploitable can be done in different
ways. The simplest one is to just keep the missing error check as is, but make
the stack frame of `buy_vip_ticket()` larger to later avoid the collision with
the `ticket` in the stack frame of `read_page()`. This can be done by changing
the size subtracted from the stack pointer at function entry and added at
function exit:

```diff
 0000000000001abd <buy_vip_ticket>:
     1abd:       f3 0f 1e fa             endbr64
     1ac1:       55                      push   rbp
     1ac2:       53                      push   rbx
-    1ac3:       48 81 ec a8 00 00 00    sub    rsp,0xa8
+    1ac3:       48 81 ec 08 02 00 00    sub    rsp,0x208
     ...         ...                     ...
-    1bbb:       48 81 c4 a8 00 00 00    add    rsp,0xa8
+    1bbb:       48 81 c4 08 02 00 00    add    rsp,0x208
     1bc2:       5b                      pop    rbx
     1bc3:       5d                      pop    rbp
     1bc4:       c3                      ret
```

Another option is to correctly implement the check on the return value of
`get_ticket_data()`, but that would require inserting more code with a jump to a
stub to perform the check and a jump back into the function.

## Exploits

| Store | Vuln | Exploit                                                                |
|:-----:|:-----|:-----------------------------------------------------------------------|
|   1   | misc | [`expl_lock_byte_lock.py`](/exploits/Sanromolo/expl_lock_byte_lock.py) |
|   1   | pwn  | [`expl_stack_reuse.py`](/exploits/Sanromolo/expl_stack_reuse.py)       |
