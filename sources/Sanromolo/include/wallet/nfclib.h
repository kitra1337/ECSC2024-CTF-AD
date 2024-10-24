#ifndef WALLET_NFCLIB_H
#define WALLET_NFCLIB_H

#include <assert.h>
#include <stdint.h>

/* Flattened ticket structure, for lock and page reference
    Page B0 B1 B2 B3
    0    00 00 00 00     manufacturer, serial, serial, check_byte 1
    1    00 00 00 00     serial
    2    00 00 00 00     check_byte 2, internal, lock
    3    00 00 00 00     OTP
    4    00 00 00 00     event_id
    5    00 00 00 00     event_id
    6    00 00 00 00     event_id
    7    00 00 00 00     event_id
    8    00 00 00 00     seat
    9    00 00 00 00     user
    10   00 00 00 00     user
    11   00 00 00 00     user
    12   00 00 00 00     user
    13   00 00 00 00     user
    14   00 00 00 00     user
    15   00 00 00 00     user
*/

#define NFCTAG_PAGE_SIZE   4
#define NFCTAG_N_PAGES     16
#define NFCTAG_PAGE_OFF(n) (NFCTAG_PAGE_SIZE * n)

struct NFCTag {
    union {
        struct {
            uint8_t manufacturer;
            uint8_t serial_part_1[2];
            uint8_t check_byte_1;
            uint8_t serial_part_2[4];
            uint8_t check_byte_2;
            uint8_t internal;
            uint16_t lock_bytes;
            uint32_t OTP;
            uint8_t event_id[NFCTAG_PAGE_SIZE * 4];
            char seat[NFCTAG_PAGE_SIZE];
            char user[NFCTAG_PAGE_SIZE * 7];
        };
        uint8_t raw[NFCTAG_PAGE_SIZE * NFCTAG_N_PAGES];
    };
};

#define NFCTAG_SERIAL_FULL_SIZE (sizeof_field(struct NFCTag, serial_part_1) \
                                 + sizeof_field(struct NFCTag, serial_part_2))
#define NFCTAG_EVENT_ID_SIZE    (sizeof_field(struct NFCTag, event_id))
#define NFCTAG_SEAT_SIZE        (sizeof_field(struct NFCTag, seat))
#define NFCTAG_USER_SIZE        (sizeof_field(struct NFCTag, user))

#define NFCTAG_OTP_OFF      (offsetof(struct NFCTag, OTP))
#define NFCTAG_EVENT_ID_OFF (offsetof(struct NFCTag, event_id))
#define NFCTAG_SEAT_OFF     (offsetof(struct NFCTag, seat))
#define NFCTAG_USER_OFF     (offsetof(struct NFCTag, user))

#define NFCTAG_OTP_PAGE      (NFCTAG_OTP_OFF      / NFCTAG_PAGE_SIZE)
#define NFCTAG_EVENT_ID_PAGE (NFCTAG_EVENT_ID_OFF / NFCTAG_PAGE_SIZE)
#define NFCTAG_SEAT_PAGE     (NFCTAG_SEAT_OFF     / NFCTAG_PAGE_SIZE)
#define NFCTAG_USER_PAGE     (NFCTAG_USER_OFF     / NFCTAG_PAGE_SIZE)

_Static_assert(sizeof(struct NFCTag) == 64);
_Static_assert(NFCTAG_PAGE_SIZE * NFCTAG_N_PAGES == 64);
_Static_assert(NFCTAG_SERIAL_FULL_SIZE == 6);
_Static_assert(NFCTAG_EVENT_ID_SIZE == 16);
_Static_assert(NFCTAG_SEAT_SIZE == 4);
_Static_assert(NFCTAG_USER_SIZE == 28);

_Static_assert(offsetof(struct NFCTag, manufacturer) == 0);
_Static_assert(offsetof(struct NFCTag, serial_part_1) == 1);
_Static_assert(offsetof(struct NFCTag, check_byte_1) == 3);
_Static_assert(offsetof(struct NFCTag, serial_part_2) == 4);
_Static_assert(offsetof(struct NFCTag, check_byte_2) == 8);
_Static_assert(offsetof(struct NFCTag, internal) == 9);
_Static_assert(offsetof(struct NFCTag, lock_bytes) == 10);
_Static_assert(NFCTAG_OTP_PAGE == 3);
_Static_assert(NFCTAG_EVENT_ID_PAGE == 4);
_Static_assert(NFCTAG_SEAT_PAGE == 8);
_Static_assert(NFCTAG_USER_PAGE == 9);

void nfc_reset_tag(struct NFCTag *tag);
int nfc_init_tag_header(struct NFCTag *tag);
int nfc_verify_tag(struct NFCTag *tag);
void nfc_set_byte(struct NFCTag *tag, uint8_t offset, uint8_t byte);

#endif
