.code 32

.section .text.startup

.global irq_handler

.global vectors_start
vectors_start:
/* Reset */
LDR PC, reset_handler_addr
/* Undef */
B .
/* SWI */
B .
/* Prefetch Abort */
B .
/* Data Abort */
B .
/* Reserved */
B .
/* IRQ */
LDR PC, irq_handler_addr
/* FIQ */
B .

/* BUG DEP: not too far from vectors, so that LSB of reset handler LDR can be
 * overwritten if a message is allocated at NULL. */
reset_handler_addr: .word reset_handler
irq_handler_addr: .word irq_handler

vectors_end:

reset_handler:
/* Setup supervisor stack. */
LDR SP, =stack_top
/* Copy vectors to 0x0. */
MOV R0, #0
LDR R1, =vectors_start
LDR R2, =vectors_end
vectors_copy_loop_head:
CMP R1, R2
BEQ vectors_copy_loop_end
LDR R3, [R1], #4
STR R3, [R0], #4
B vectors_copy_loop_head
vectors_copy_loop_end:
/* Backup current PSR. */
MRS R0, CPSR
/* Transition to IRQ mode. */
BIC R1, R0, #0x1f
ORR R1, R1, #0x12
MSR CPSR, R1
/* Setup IRQ stack. */
LDR SP, =irq_stack_top
/* Enable IRQs and return to supervisor mode. */
BIC R0, R0, #0x80
MSR CPSR, R0
/* Let's go. */
BLX main
B .
