#include "heap.h"
#include "stddef.h"
#include "stdint.h"

extern char heap_start, heap_end;

static char *g_cur_heap_end = &heap_start;

void *heap_alloc(size_t size)
{
	size = 4 + ((size + 3) & ~3U);

	char *chunk = &heap_start;

	while (chunk < g_cur_heap_end) {
		size_t chunk_size = *(uint32_t *)chunk;
		char is_free = chunk_size & 1U;
		chunk_size &= ~1U;

		if (!is_free || chunk_size < size) {
			chunk += chunk_size;
			continue;
		}

		/* BUG DEP: aggressive splitting makes growing the heap easier. */
		if (chunk_size > size) {
			*(uint32_t *)chunk = size | 1U;
			*(uint32_t *)(chunk + size) = (chunk_size - size) | 1U;
		}

		*(uint32_t *)chunk &= ~1U;
		return chunk + 4;
	}

	char *new_heap_end = g_cur_heap_end + size;
	if (new_heap_end < g_cur_heap_end || new_heap_end > &heap_end)
		return 0;

	/* BUG DEP: we don't grow a free chunk at the end of the heap to
	 * make growing the heap easier. */

	chunk = g_cur_heap_end;
	*(uint32_t *)chunk = size;

	g_cur_heap_end = new_heap_end;

	return chunk + 4;
}

void heap_free(void *ptr)
{
	if (!ptr)
		return;

	char *chunk = (char *)ptr - 4;

	size_t chunk_size = *(uint32_t *)chunk;
	*(uint32_t *)chunk = chunk_size | 1U;

	/* BUG DEP: only forward consolidation without backward consolidation
	 * makes growing the heap easier. */
	char *next_chunk = chunk + chunk_size;
	if (next_chunk < g_cur_heap_end) {
		size_t next_chunk_size = *(uint32_t *)next_chunk;
		char next_is_free = next_chunk_size & 1U;
		next_chunk_size &= ~1U;
		if (next_is_free)
			*(uint32_t *)chunk += next_chunk_size;
	}
}
