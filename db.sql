CREATE TABLE mail (
    dest text,
    source text,
    msg text,
    private boolean, -- actually an int, because sqlite, but whatever
    time integer
);

CREATE TABLE word_pairs (
    first text,
    second text
);

CREATE TABLE word_triplets (
    first text,
    second text,
    third text
);

CREATE TABLE variables (
    name text,
    value int
);

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

CREATE TABLE definitions (
    source text,
    thing text,
    definition text
);
