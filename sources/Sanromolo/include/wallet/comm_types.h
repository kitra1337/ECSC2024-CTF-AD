#ifndef WALLET_COMM_TYPES_H
#define WALLET_COMM_TYPES_H

#include <stddef.h>
#include <stdint.h>

#include "common/event.h"
#include "wallet/nfclib.h"
#include "wallet/wallet.h"

enum MessageType {
    Read         = 0x30,
    Write        = 0xA2,
    BuyUser      = 0x59,
    BuyVIP       = 0x95,
    NumCards     = 0x75,
    GetCard      = 0x39,
    CreateWallet = 0x99,
};

struct BuyUserCommand {
    uint8_t event_id[EVENT_ID_SIZE];
    uint8_t user[NFCTAG_USER_SIZE];
};

struct BuyVIPCommand {
    uint8_t event_id[EVENT_ID_SIZE];
    uint8_t user[NFCTAG_USER_SIZE];
    uint8_t vip_code[EVENT_VIP_INV_CODE_SIZE];
};

struct WriteCommand {
    uint8_t ticket_id[NFCTAG_SERIAL_FULL_SIZE];
    uint8_t page;
    uint8_t page_data[NFCTAG_PAGE_SIZE];
};

struct ReadCommand {
    uint8_t ticket_id[NFCTAG_SERIAL_FULL_SIZE];
    uint8_t page;
};

struct GetCardCommand {
    uint8_t offset;
};

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

_Static_assert(sizeof_field(struct Command, length) == 1);
_Static_assert(offsetof(struct Command, data) == 18);

enum CommandLengths {
    // 19 = 1 type + 16 wallet_id + 2 crc
    CreateWalletCommandSize = 19, // zero-length, no associated struct
    NumCardsCommandSize     = 19, // zero-length, no associated struct
    BuyUserCommandSize      = sizeof(struct BuyUserCommand) + 19,
    BuyVipCommandSize       = sizeof(struct BuyVIPCommand)  + 19,
    WriteCommandSize        = sizeof(struct WriteCommand)   + 19,
    ReadCommandSize         = sizeof(struct ReadCommand)    + 19,
    GetCardCommandSize      = sizeof(struct GetCardCommand) + 19,
};

enum ResponseCode {
    ACK     = 0xA,
    InvArg  = 0x0,
    CRCErr  = 0x1,
    Unknown = 0x9,
};

struct BuyResponse {
    uint8_t ticket_id[NFCTAG_SERIAL_FULL_SIZE];
};

struct ReadResponse {
    uint8_t data[NFCTAG_PAGE_SIZE];
};

struct NumCardsResponse {
    uint8_t cards;
};

struct GetCardResponse {
    uint8_t ticket_id[NFCTAG_SERIAL_FULL_SIZE];
};

struct CreateWalletResponse {
    uint8_t wallet_id[WALLET_ID_SIZE];
};

enum ResponseLengths {
    // + 1 for code, + 2 for CRC
    ErrorResponseSize        = 3, // zero-length, no associated struct
    WriteResponseSize        = 3, // zero-length, no associated struct
    BuyResponseSize          = sizeof(struct BuyResponse)          + 3,
    ReadResponseSize         = sizeof(struct ReadResponse)         + 3,
    NumCardsResponseSize     = sizeof(struct NumCardsResponse)     + 3,
    GetCardResponseSize      = sizeof(struct GetCardResponse)      + 3,
    CreateWalletResponseSize = sizeof(struct CreateWalletResponse) + 3,
};

_Static_assert(ErrorResponseSize        == 0                       + 3);
_Static_assert(WriteResponseSize        == 0                       + 3);
_Static_assert(BuyResponseSize          == NFCTAG_SERIAL_FULL_SIZE + 3);
_Static_assert(ReadResponseSize         == NFCTAG_PAGE_SIZE        + 3);
_Static_assert(NumCardsResponseSize     == 1                       + 3);
_Static_assert(GetCardResponseSize      == NFCTAG_SERIAL_FULL_SIZE + 3);
_Static_assert(CreateWalletResponseSize == WALLET_ID_SIZE          + 3);

struct Response {
    union {
        struct {
            uint8_t length;
            uint8_t code;
            union {
                struct BuyResponse buy;
                struct ReadResponse read;
                struct NumCardsResponse num_cards;
                struct GetCardResponse get_card;
                struct CreateWalletResponse create_wallet;
            } data;
        };
        uint8_t raw[0x100];
    };
};

#endif
