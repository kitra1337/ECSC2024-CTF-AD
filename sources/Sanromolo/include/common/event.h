#ifndef COMMON_EVENT_H
#define COMMON_EVENT_H

#include <assert.h>
#include <stdint.h>

#include "common/util.h"

#define EVENT_DIRECTORY          "/home/ubuntu/events/"
#define EVENT_NAME_LEN           64
#define EVENT_STAR_SIGNATURE_LEN 64

struct Event {
    char *name;
    uint8_t id[16];
    char *star_signature;
    uint8_t vip_invitation_code[16];
};

#define EVENT_ID_SIZE (sizeof_field(struct Event, id))
#define EVENT_VIP_INV_CODE_SIZE (sizeof_field(struct Event, vip_invitation_code))

_Static_assert(sizeof(struct Event) == 48);
_Static_assert(EVENT_ID_SIZE == 16);
_Static_assert(EVENT_VIP_INV_CODE_SIZE == 16);

int get_event_data(uint8_t *event_id, struct Event *event);

#endif
