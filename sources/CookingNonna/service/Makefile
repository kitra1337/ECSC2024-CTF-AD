CC     := gcc
CFLAGS := -Wall -Wextra -pedantic -O0 # -gdwarf-4 -gstrict-dwarf
LDFLAGS := -Wl,-z,relro,-z,now
LIBS := -lcrypto -lgmp

TARGET := main
SRCDIR := src
OUTDIR := build
SRCS := $(wildcard $(SRCDIR)/*.c)
OBJS := $(patsubst $(SRCDIR)/%.c,$(OUTDIR)/%.o,$(SRCS))
BINARY := $(OUTDIR)/$(TARGET)

.PHONY: all clean dist

all: $(BINARY)

$(OUTDIR):
	echo 'MKDIR $@'
	mkdir -p $@

$(OUTDIR)/%.o: $(SRCDIR)/%.c | $(OUTDIR)
	echo 'CC $@'
	$(CC) $(CFLAGS) -c -o $@ $<

$(BINARY): $(OBJS) | $(OUTDIR)
	echo 'CCLD $@'
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(LIBS)

clean:
	echo 'CLEAN $(OUTDIR)'
	rm -rf $(OUTDIR)/*
