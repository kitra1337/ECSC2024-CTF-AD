#include "crypto.h"
#include "heap.h"
#include "host.h"
#include "msg.h"
#include "stddef.h"
#include "stdint.h"
#include "string.h"
#include "token.h"
#include "uart.h"

static void handle_import_key(struct msg *msg)
{
	if (msg->size < 4) {
		struct msg *reply = msg_alloc(MSG_ERROR, 27);
		memcpy(reply->data, "bad import key message size", reply->size);
		msg_send(reply);
		msg_free(reply);
		return;
	}

	uint32_t key_id = *(uint32_t *)msg->data;

	host_ks_put(key_id, msg->data + 4, msg->size - 4);

	struct msg *reply = msg_alloc(MSG_OK, 0);
	msg_send(reply);
	msg_free(reply);
}

static void handle_import_item(struct msg *msg)
{
	if (msg->size < 8) {
		struct msg *reply = msg_alloc(MSG_ERROR, 28);
		memcpy(reply->data, "bad import item message size", reply->size);
		msg_send(reply);
		msg_free(reply);
		return;
	}

	uint32_t item_id = *(uint32_t *)msg->data;
	uint32_t key_id = *(uint32_t *)(msg->data + 4);

	void *item = msg->data + 8;
	size_t item_size = msg->size - 8;

	size_t key_size;
	void *key = host_ks_get(key_id, &key_size);

	uint8_t nonce[12];
	memset(nonce, 'I', sizeof(nonce));
	/* BUG WARN SAFE: heap allocation size is 4-byte aligned. */
	crypto_chacha20(item, item_size, key, key_size, nonce);

	heap_free(key);

	host_cs_put(item_id, key_id, item, item_size);

	struct msg *reply = msg_alloc(MSG_OK, 0);
	msg_send(reply);
	msg_free(reply);
}

static void handle_get_item(struct msg *msg)
{
	const char *err = 0;

	if (msg->size < 8) {
		struct msg *reply = msg_alloc(MSG_ERROR, 25);
		memcpy(reply->data, "bad get item message size", reply->size);
		msg_send(reply);
		msg_free(reply);
		return;
	}

	uint32_t item_id = *(uint32_t *)msg->data;
	uint32_t target_key_id = *(uint32_t *)(msg->data + 4);
	void *token = msg->data + 8;
	size_t token_size = msg->size - 8;

	uint32_t owner_key_id;
	size_t size;
	void *data = host_cs_get(item_id, &owner_key_id, &size);

	err = token_check(item_id, owner_key_id, target_key_id, token, token_size);

	if (!err) {
		size_t key_size;
		void *key = host_ks_get(target_key_id, &key_size);

		uint8_t nonce[12];
		memset(nonce, 'I', sizeof(nonce));
		/* BUG WARN SAFE: heap allocation size is 4-byte aligned. */
		crypto_chacha20(data, size, key, key_size, nonce);

		heap_free(key);
	}

	size_t reply_size = err ? strlen(err) : size;
	struct msg *reply = msg_alloc(err ? MSG_ERROR : MSG_OK, reply_size);
	memcpy(reply->data, err ? err : data, reply_size);
	msg_send(reply);
	msg_free(reply);

	heap_free(data);
}

static void handle_request(struct msg *msg)
{
	struct msg *reply;

	switch ((enum msg_type)msg->type) {
	case MSG_IMPORT_KEY:
		handle_import_key(msg);
		break;
	case MSG_IMPORT_ITEM:
		handle_import_item(msg);
		break;
	case MSG_GET_ITEM:
		handle_get_item(msg);
		break;
	default:
		reply = msg_alloc(MSG_ERROR, 23);
		memcpy(reply->data, "unknown request message", reply->size);
		msg_send(reply);
		msg_free(reply);
		break;
	}
}

void main()
{
	uart_init();

	while (1) {
		struct msg *msg = msg_recv();
		handle_request(msg);
		msg_free(msg);
	}
}
