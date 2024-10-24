#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "common/util.h"
#include "wallet/comm_types.h"
#include "wallet/nfclib.h"

int nfc_verify_tag(struct NFCTag *tag) {
     // This is just a random hardcoded value
    if (tag->manufacturer != 0x73)
        return -1;

    uint8_t check_byte_calculated_value = tag->manufacturer
                                          ^ tag->serial_part_1[0]
                                          ^ tag->serial_part_1[1] ^ 0x99;
    if (check_byte_calculated_value != tag->check_byte_1)
        return -1;

    uint8_t check_byte_2_calculated_value = tag->serial_part_2[0]
        ^ tag->serial_part_2[1] ^ tag->serial_part_2[2] ^ tag->serial_part_2[3];

    if (check_byte_2_calculated_value != tag->check_byte_2)
        return -1;

    return 0;
}

inline static uint8_t is_lock_bit_locked(struct NFCTag *tag, uint8_t page_bit) {
    // Block lock for OTP is at offset 0
    uint8_t offset = 0;

    if (page_bit >= 4 && page_bit <= 9) {
        // Block lock for pages 4-9 is at offset 1
        offset = 1;
    } else if (page_bit >= 10 && page_bit <= 15) {
        // Block lock for pages 10-15 is at offset 2
        offset = 2;
    }

    return (tag->lock_bytes >> offset & 1);
}

inline static uint8_t is_page_locked(struct NFCTag *tag, uint8_t page) {
    return (tag->lock_bytes >> page) & 0x1;
}

void nfc_set_byte(struct NFCTag *tag, uint8_t offset, uint8_t byte) {
    if (offset >= 64) { // Out of bound
        return;
    } else if (offset < 10) { // Read only serial number + internal bytes
        return;
    } else if (offset < 12) { // Lock write
        uint8_t bit_offset = offset == 11 ? 8 : 0;
        for (uint8_t i = 0; i < 8; i++) {
            // The bit offset we are trying to write, with
            // respect to the 16-bit page lock
            uint8_t bit = i + bit_offset;
            // The bit we are trying to write
            uint8_t writing_bit = byte >> i & 0x1;
            // Block locks, just OR the bit
            if (bit < 3) {
                tag->lock_bytes |= writing_bit << bit;
            } else {
                if (!is_lock_bit_locked(tag, bit)) {
                    tag->lock_bytes |= writing_bit << bit;
                }
            }
        }
    } else if (offset < 16) { // OTP write (page 3)
        if (!is_page_locked(tag, 3)) {
            // OTP can only be set to 1, so emulate an OR operation on the bytes
            tag->raw[offset] |= byte;
        }
    } else { // User data write
        if (!is_page_locked(tag, offset / 4)) {
            tag->raw[offset] = byte;
        }
    }
}

void nfc_reset_tag(struct NFCTag *tag) {
    memset(tag, 0, sizeof(*tag));
}

int nfc_init_tag_header(struct NFCTag *tag) {
    uint8_t serial[6];

    if (get_rand_bytes(serial, 6) == -1)
        return -1;

    _Static_assert(sizeof(tag->serial_part_1) == 2);
    _Static_assert(sizeof(tag->serial_part_2) == 4);
    memcpy(tag->serial_part_1, serial, 2);
    memcpy(tag->serial_part_2, serial + 2, 4);

    tag->manufacturer = 0x73;
    tag->check_byte_1 = tag->manufacturer ^ tag->serial_part_1[0]
        ^ tag->serial_part_1[1] ^ 0x99;
    tag->check_byte_2 = tag->serial_part_2[0] ^ tag->serial_part_2[1]
        ^ tag->serial_part_2[2] ^ tag->serial_part_2[3];
    return 0;
}
