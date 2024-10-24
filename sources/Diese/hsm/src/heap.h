#ifndef HEAP_H
#define HEAP_H

#include "stddef.h"

/* Guarantees 4-byte alignment of address and size. */
void *heap_alloc(size_t size);
void heap_free(void *ptr);

#endif
