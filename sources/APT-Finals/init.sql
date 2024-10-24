create table users
(
    username varchar(256) primary key not null,
    password varchar(256)             not null,
    secret   varchar(256)             not null
);

create table matches
(
    id         bigserial primary key not null,
    owner      varchar(256)          not null,
    prize      varchar(256)          not null,
    secret_key varchar(256)          not null,
    difficulty integer               not null
);

create table matches_played
(
    id       bigserial primary key not null,
    match_id bigint                not null references matches (id) on delete cascade,
    username varchar(256)          not null references users (username) on delete cascade,
    winner   varchar(16) default null
);

create table friend_invites
(
    user_a varchar(256) not null references users (username) on delete cascade,
    user_b varchar(255) not null references users (username) on delete cascade,
    key    bytea        not null,
    unique (user_a, user_b)
);

create table friends
(
    user_a varchar(256) not null references users (username) on delete cascade,
    user_b varchar(256) not null references users (username) on delete cascade,
    unique (user_a, user_b)
);
