#include "irq.h"
#include "pm.h"
#include "stddef.h"
#include "stdint.h"
#include "uart.h"

#define UART_RXFE 0x10U
#define UART_TXFF 0x20U

#define UART0_BASE 0x101f1000U
#define UART0_DR ((volatile unsigned int *)(UART0_BASE + 0x0))
#define UART0_FR ((volatile unsigned int *)(UART0_BASE + 0x18))
#define UART0_IMSC ((volatile unsigned int *)(UART0_BASE + 0x38))

#define VIC_BASE 0x10140000U
#define VIC_INTENABLE ((volatile unsigned int *)(VIC_BASE + 0x10))

static volatile uint8_t g_uart_rb[2048];
static volatile size_t g_uart_rb_rp = 0;
static volatile size_t g_uart_rb_wp = 0;

void uart_irq(void)
{
	size_t wp = g_uart_rb_wp;

	while (!(*UART0_FR & UART_RXFE)) {
		g_uart_rb[wp++] = *UART0_DR;
		if (wp == sizeof(g_uart_rb))
			wp = 0;
	}

	g_uart_rb_wp = wp;
}

void uart_init(void)
{
	/* Enable UART0 IRQ in the VIC. */
	*VIC_INTENABLE |= 1U << 12;
	/* Enable RXIM interrupt for UART0. */
	*UART0_IMSC = 1U << 4;
}

uint8_t uart_get_byte(void)
{
	size_t rp = g_uart_rb_rp;

	while (1) {
		irq_disable();
		if (rp != g_uart_rb_wp) {
			irq_enable();
			break;
		}
		pm_wfi();
		irq_enable();
	}

	uint8_t byte = g_uart_rb[rp];

	rp++;
	if (rp == sizeof(g_uart_rb))
		rp = 0;
	g_uart_rb_rp = rp;

	return byte;
}

void uart_put_byte(uint8_t byte)
{
	*UART0_DR = byte;
}

void uart_get_bytes(void *buf, size_t size)
{
	uint8_t *p = buf;
	while (size--)
		*p++ = uart_get_byte();
}

void uart_put_bytes(const void *buf, size_t size)
{
	const uint8_t *p = buf;
	while (size--)
		uart_put_byte(*p++);
}
