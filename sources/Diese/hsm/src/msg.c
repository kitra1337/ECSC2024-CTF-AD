#include "heap.h"
#include "msg.h"
#include "stddef.h"
#include "stdint.h"
#include "uart.h"

struct msg *msg_alloc(enum msg_type type, size_t size)
{
	struct msg *msg = heap_alloc(sizeof(*msg) + size);
	msg->type = type;
	msg->size = size;
	return msg;
}

void msg_free(struct msg *msg)
{
	heap_free(msg);
}

struct msg *msg_recv(void)
{
	uint8_t type = uart_get_byte();

	uint32_t size;
	uart_get_bytes(&size, sizeof(size));

	struct msg *msg = msg_alloc(type, size);

	uart_get_bytes(msg->data, size);

	return msg;
}

void msg_send(const struct msg *msg)
{
	uart_put_byte(msg->type);

	uint32_t size = msg->size;
	uart_put_bytes(&size, sizeof(size));

	uart_put_bytes(msg->data, msg->size);
}
