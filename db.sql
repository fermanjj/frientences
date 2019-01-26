################# CREATE USER ##############################

create user 'fs'@'%' identified with mysql_native_password by 'password';
grant all privileges on *.* to 'fs'@'%';
flush privileges;

#################### GAME SCHEMA AND TABLES ##########################

CREATE SCHEMA game;

USE game;

create table codes
(
  game_id bigint unsigned not null,
  code    varchar(255)    not null,
  primary key (game_id, code),
  constraint codes_code_uindex
  unique (code),
  constraint codes_game_id_uindex
  unique (game_id)
);

create table game
(
  id           bigint unsigned auto_increment,
  name         varchar(100)                       not null,
  creator_id   bigint unsigned                    null,
  sentences    int unsigned                       not null,
  words_shown  int unsigned                       not null,
  date_created datetime default CURRENT_TIMESTAMP not null,
  constraint game_id_uindex
  unique (id)
);

create index game_creator_id_index
  on game (creator_id);

create index game_date_created_index
  on game (date_created);

create index game_name_index
  on game (name);

alter table game
  add primary key (id);

create table `order`
(
  game_id bigint unsigned not null,
  user_id bigint unsigned not null,
  `order` int unsigned    not null,
  primary key (game_id, user_id)
);

create index order_game_id_index
  on `order` (game_id);

create index order_order_index
  on `order` (`order`);

create index order_user_id_index
  on `order` (user_id);

create table status
(
  game_id             bigint unsigned          not null,
  started             tinyint(1) default '0'   null,
  date_started        datetime                 null,
  finished            tinyint(1) default '0'   null,
  date_finished       datetime                 null,
  current_user_id     bigint unsigned          null,
  sentences_completed int unsigned default '0' null,
  constraint status_game_id_uindex
  unique (game_id)
);

create index status_date_finished_index
  on status (date_finished);

create index status_date_started_index
  on status (date_started);

create table users
(
  id         bigint unsigned auto_increment,
  name       varchar(100)                       not null,
  game_id    bigint unsigned                    not null,
  date_added datetime default CURRENT_TIMESTAMP not null,
  constraint users_id_uindex
  unique (id)
);

create index users_date_added_index
  on users (date_added);

create index users_game_id_index
  on users (game_id);

create index users_name_index
  on users (name);

alter table users
  add primary key (id);

create table words
(
  id         bigint unsigned auto_increment,
  game_id    bigint unsigned                    not null,
  user_id    bigint unsigned                    not null,
  word       varchar(255)                       not null,
  date_added datetime default CURRENT_TIMESTAMP not null,
  constraint words_id_uindex
  unique (id)
);

create index words_date_added_index
  on words (date_added);

create index words_game_id_index
  on words (game_id);

create index words_user_id_index
  on words (user_id);

create index words_word_index
  on words (word);

alter table words
  add primary key (id);

