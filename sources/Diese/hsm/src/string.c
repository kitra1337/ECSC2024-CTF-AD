#include "stddef.h"
#include "string.h"

void *memcpy(void *dst, const void *src, size_t size)
{
	char *dstp = dst;
	const char *srcp = src;
	while (size--)
		*dstp++ = *srcp++;
	return dst;
}

void *memset(void *buf, int c, size_t size)
{
	char *bufp = buf;
	while (size--)
		*bufp++ = c;
	return buf;
}

size_t strlen(const char *s)
{
	size_t len = 0;
	while (*s++) len++;
	return len;
}
