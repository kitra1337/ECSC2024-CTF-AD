#ifndef PM_H
#define PM_H

static inline void pm_wfi(void)
{
	unsigned int zero = 0;
	__asm__ volatile ("MCR p15, 0, %0, c7, c0, 4" : : "r" (zero));
}

#endif
