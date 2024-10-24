#ifndef UART_H
#define UART_H

#include "stddef.h"
#include "stdint.h"

void uart_irq(void);

void uart_init(void);

uint8_t uart_get_byte(void);
void uart_put_byte(uint8_t byte);

void uart_get_bytes(void *buf, size_t size);
void uart_put_bytes(const void *buf, size_t size);

#endif
