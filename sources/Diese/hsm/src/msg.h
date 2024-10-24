#ifndef MSG_H
#define MSG_H

#include "stddef.h"
#include "stdint.h"

enum msg_type {
	/* Replies */
	/* BUG DEP: when a message is allocated at NULL, 0x00 type corrupts LSB of
	 * reset handler vectors entry: LDR PC, [PC, #24] -> LDR PC, [PC, #0] */
	MSG_OK = 0x00,
	MSG_ERROR = 0x01,
	/* Host -> HSM */
	MSG_IMPORT_KEY = 0x10,
	MSG_IMPORT_ITEM = 0x11,
	MSG_GET_ITEM = 0x12,
	/* HSM -> host */
	MSG_KS_PUT = 0x20,
	MSG_KS_GET = 0x21,
	MSG_CS_PUT = 0x22,
	MSG_CS_GET = 0x23,
};

struct msg {
	/* BUG DEP: properly enum msg_type, force it to a byte to corrupt just
	 * the LSB when a message is allocated at NULL. */
	uint8_t type;
	uint8_t pad[3];
	size_t size;
	uint8_t data[];
};

struct msg *msg_alloc(enum msg_type type, size_t size);
void msg_free(struct msg *msg);

struct msg *msg_recv(void);
void msg_send(const struct msg *msg);

#endif
