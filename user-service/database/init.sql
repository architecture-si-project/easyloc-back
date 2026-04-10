create table "users"
(
    userid   serial,
    name     varchar(50) not null,
    email    varchar(50) not null,
    password text        not null,
    constraint user_pk
        primary key (userid)
);