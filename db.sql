CREATE TABLE mail (
    target text,
    source text,
    msg text,
    private boolean -- actually an int, because sqlite, but whatever
);
