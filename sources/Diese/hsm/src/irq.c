#include "uart.h"

__attribute__((interrupt("IRQ")))
void irq_handler(void) {
	uart_irq();
}

void irq_enable(void)
{
	unsigned int cpsr;
	__asm__ volatile ("MRS %0, CPSR" : "=r" (cpsr));
	cpsr &= ~0x80U;
	__asm__ volatile ("MSR CPSR_cxsf, %0" : : "r" (cpsr));

}

void irq_disable(void)
{
	unsigned int cpsr;
	__asm__ volatile ("MRS %0, CPSR" : "=r" (cpsr));
	cpsr |= 0x80U;
	__asm__ volatile ("MSR CPSR_cxsf, %0" : : "r" (cpsr));
}
