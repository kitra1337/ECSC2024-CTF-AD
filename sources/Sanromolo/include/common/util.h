#ifndef COMMON_UTIL_H
#define COMMON_UTIL_H

#include <err.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

#define sizeof_field(type, field) (sizeof(((type *)0)->field))

ssize_t read_exactly(int fd, void *buf, size_t size);
ssize_t write_exactly(int fd, const void *buf, size_t size);
ssize_t get_rand_bytes(void *buf, size_t size);

void hex_to_bytes(const char *in_hex, uint8_t *out_bytes, size_t out_size);
void bytes_to_hex(char *out_hex, const uint8_t *in_bytes, size_t in_size);

void iso14443a_crc(const uint8_t *data, size_t size, uint8_t *out_crc);

void flush_stdin(void);
void get_string(char *out, size_t size);
int get_uint(unsigned *value);

#endif
