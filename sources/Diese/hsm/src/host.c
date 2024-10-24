#include "heap.h"
#include "host.h"
#include "msg.h"
#include "stdint.h"
#include "string.h"

void host_ks_put(uint32_t key_id, const void *key, size_t size)
{
	struct msg *msg = msg_alloc(MSG_KS_PUT, 4 + size);
	*(uint32_t *)msg->data = key_id;
	memcpy(msg->data + 4, key, size);
	msg_send(msg);
	msg_free(msg);
}

void *host_ks_get(uint32_t key_id, size_t *size)
{
	struct msg *msg = msg_alloc(MSG_KS_GET, 4);
	*(uint32_t *)msg->data = key_id;
	msg_send(msg);
	msg_free(msg);

	msg = msg_recv();
	*size = msg->size;
	void *key = heap_alloc(*size);
	memcpy(key, msg->data, *size);
	msg_free(msg);

	return key;
}

void host_cs_put(uint32_t item_id, uint32_t key_id, const void *data,
                 size_t size)
{
	struct msg *msg = msg_alloc(MSG_CS_PUT, 8 + size);
	*(uint32_t *)msg->data = item_id;
	*(uint32_t *)(msg->data + 4) = key_id;
	memcpy(msg->data + 8, data, size);
	msg_send(msg);
	msg_free(msg);
}

void *host_cs_get(uint32_t item_id, uint32_t *key_id, size_t *size)
{
	struct msg *msg = msg_alloc(MSG_CS_GET, 4);
	*(uint32_t *)msg->data = item_id;
	msg_send(msg);
	msg_free(msg);

	msg = msg_recv();

	if (msg->size >= 4) {
		*key_id = *(uint32_t *)msg->data;
		*size = msg->size - 4;
	} else {
		*key_id = -1U;
		*size = 0;
	}

	void *data = heap_alloc(*size);
	memcpy(data, msg->data + 4, *size);

	msg_free(msg);

	return data;
}
