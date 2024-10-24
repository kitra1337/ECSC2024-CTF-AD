SRCDIR := src
INCDIR := include
OUTDIR := dist
RELDIR := ../../services/Sanromolo

LIBCOMMON_SRCDIR := $(SRCDIR)/common
LIBCOMMON_A      := $(LIBCOMMON_SRCDIR)/libcommon.a
LIBCOMMON_SRCS   := $(wildcard $(LIBCOMMON_SRCDIR)/*.c)
LIBCOMMON_OBJS   := $(patsubst $(LIBCOMMON_SRCDIR)/%.c,$(LIBCOMMON_SRCDIR)/%.o,$(LIBCOMMON_SRCS))
LIBCOMMON_DEPS   := $(LIBCOMMON_OBJS:.o=.d)
# Simplify reversing a bit here with no fortify builtins
LIBCOMMON_CFLAGS := -D_FORTIFY_SOURCE=0

MGMT_SRCDIR   := $(SRCDIR)/event_management
MGMT_BINARY   := $(OUTDIR)/event-management
MGMT_SRCS     := $(wildcard $(MGMT_SRCDIR)/*.c)
MGMT_OBJS     := $(patsubst $(MGMT_SRCDIR)/%.c,$(MGMT_SRCDIR)/%.o,$(MGMT_SRCS))
MGMT_DEPS     := $(MGMT_OBJS:.o=.d)

WALLET_SRCDIR := $(SRCDIR)/wallet
WALLET_BINARY := $(OUTDIR)/wallet
WALLET_SRCS   := $(wildcard $(WALLET_SRCDIR)/*.c)
WALLET_OBJS   := $(patsubst $(WALLET_SRCDIR)/%.c,$(WALLET_SRCDIR)/%.o,$(WALLET_SRCS))
WALLET_DEPS   := $(WALLET_OBJS:.o=.d)

WALLET_CLIENT_SRCDIR := $(SRCDIR)/wallet_client
WALLET_CLIENT_BINARY := $(OUTDIR)/wallet-client
WALLET_CLIENT_SRCS   := $(wildcard $(WALLET_CLIENT_SRCDIR)/*.c)
WALLET_CLIENT_OBJS   := $(patsubst $(WALLET_CLIENT_SRCDIR)/%.c,$(WALLET_CLIENT_SRCDIR)/%.o,$(WALLET_CLIENT_SRCS))
WALLET_CLIENT_DEPS   := $(WALLET_CLIENT_OBJS:.o=.d)
WALLET_CLIENT_LDLIBS := $(shell pkg-config --libs ncurses)

BINARIES = $(MGMT_BINARY) $(WALLET_BINARY) $(WALLET_CLIENT_BINARY)

CC := gcc
LD := ld
CFLAGS := -O1 -std=gnu99 -MMD -Wall -Wextra \
	-ffunction-sections -fdata-sections \
	-fno-asynchronous-unwind-tables -fstack-protector-strong \
	-fno-builtin-memcpy \
	-Iinclude
LDFLAGS := -Wl,-z,relro,-z,now,--gc-sections

ifeq ($(DEBUG),1)
	CFLAGS += -g -DDEBUG
endif

ifneq ($(V),1)
	MAKEFLAGS += --silent
endif

.PHONY: all clean release clean-release
all: $(BINARIES)

-include $(LIBCOMMON_DEPS) $(MGMT_DEPS) $(WALLET_DEPS) $(WALLET_CLIENT_DEPS)

$(LIBCOMMON_A): $(LIBCOMMON_OBJS)
	echo 'LD      $@'
	$(LD) -r -o $@ $^

$(MGMT_BINARY): $(MGMT_OBJS) $(LIBCOMMON_A) | $(OUTDIR)
	echo 'CCLD    $@'
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^
ifneq ($(DEBUG),1)
	echo 'STRIP   $@'
	strip $@
endif

$(WALLET_BINARY): ./check_stack.py $(WALLET_OBJS) $(LIBCOMMON_A) | $(OUTDIR)
	echo 'CCLD    $@'
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(filter-out $<,$^)
	echo 'CHECK   $@'
	./$< $@
ifneq ($(DEBUG),1)
	echo 'STRIP   $@'
	strip $@
endif

$(WALLET_CLIENT_BINARY): $(WALLET_CLIENT_OBJS) $(LIBCOMMON_A) | $(OUTDIR)
	echo 'CCLD    $@'
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(WALLET_CLIENT_LDLIBS)
ifneq ($(DEBUG),1)
	echo 'STRIP   $@'
	strip $@
endif

$(LIBCOMMON_SRCDIR)/%.o: $(LIBCOMMON_SRCDIR)/%.c
	echo 'CC      $@'
	$(CC) $(CFLAGS) $(LIBCOMMON_CFLAGS) -c -o $@ $<

$(MGMT_SRCDIR)/%.o: $(MGMT_SRCDIR)/%.c
	echo 'CC      $@'
	$(CC) $(CFLAGS) -c -o $@ $<

$(WALLET_SRCDIR)/%.o: $(WALLET_SRCDIR)/%.c
	echo 'CC      $@'
	$(CC) $(CFLAGS) -c -o $@ $<

$(WALLET_CLIENT_SRCDIR)/%.o: $(WALLET_CLIENT_SRCDIR)/%.c
	echo 'CC      $@'
	$(CC) $(CFLAGS) -c -o $@ $<

$(OUTDIR):
	echo 'MKDIR   $@'
	mkdir -p $@

clean:
	echo 'CLEAN   $(OUTDIR)'
	rm -fr '$(OUTDIR)'/*
	echo 'CLEAN   $(LIBCOMMON_SRCDIR)'
	rm -f $(LIBCOMMON_A) $(LIBCOMMON_OBJS) $(LIBCOMMON_DEPS)
	echo 'CLEAN   $(MGMT_SRCDIR)'
	rm -f $(MGMT_OBJS) $(MGMT_DEPS)
	echo 'CLEAN   $(WALLET_SRCDIR)'
	rm -f $(WALLET_OBJS) $(WALLET_DEPS)
	echo 'CLEAN   $(WALLET_CLIENT_SRCDIR)'
	rm -f $(WALLET_CLIENT_OBJS) $(WALLET_CLIENT_DEPS)

# Lazy, I know
release: docker-compose.yml deploy.sh $(BINARIES) | $(RELDIR)
	echo 'RELEASE'
	cp docker-compose.yml deploy.sh $(RELDIR)
	cp -r $(OUTDIR) $(RELDIR)/

clean-release:
	echo 'CLEAN RELEASE'
	rm -rf $(RELDIR)/*
