CREATE TABLE mail (
    target text,
    source text,
    msg text,
    private boolean -- actually an int, because sqlite, but whatever
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
