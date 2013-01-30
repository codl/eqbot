CREATE TABLE mail (
    dest text,
    source text,
    msg text,
    private boolean, -- actually an int, because sqlite, but whatever
    time integer
);
CREATE INDEX mail_idx ON mail(dest);

CREATE TABLE word_pairs (
    first text,
    second text
);

CREATE TABLE word_triplets (
    first text,
    second text,
    third text
);
CREATE INDEX triplet_idx ON word_triplets(first, second);
CREATE INDEX triplet_first_idx ON word_triplets(first);

CREATE TABLE variables (
    name text,
    value int
);
CREATE INDEX var_idx ON variables(name);

CREATE TABLE nick_host (
    nick text,
    host text,
    count int default 1
);

CREATE TABLE log (
    type int not null,
    source text,
    dest text,
    msg text,
    time integer
);
CREATE INDEX log_dest_idx ON log(dest);
CREATE INDEX log_type_msg_idx ON log(type,msg);


CREATE TABLE definitions (
    source text,
    thing text,
    definition text
);
CREATE INDEX def_idx ON definitions(thing);


