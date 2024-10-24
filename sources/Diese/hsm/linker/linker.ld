ENTRY(vectors_start)

SECTIONS
{
	. = 0x10000;
	.text : {
		KEEP(*(.text.startup))
		*(.text .rodata)
	}
	.data : { *(.data) }
	.bss : { *(.bss) }

	/* Heap: 12KiB.
	 * BUG DEP: limited size allows exhaustion in extract_token. */
	. = ALIGN(0x1000);
	heap_start = .;
	. = . + 0x3000;
	heap_end = .;

	/* Main stack: 4KiB. */
	. = ALIGN(0x1000);
	. = . + 0x1000;
	stack_top = .;

	/* IRQ stack: 4KiB. */
	. = ALIGN(0x1000);
	. = . + 0x1000;
	irq_stack_top = .;
}
