CREATE TABLE mail (
    dest text,
    source text,
    msg text,
    private boolean, -- actually an int, because sqlite, but whatever
    time integer
);
CREATE INDEX mail_idx ON mail(dest);

CREATE TABLE variables (
    name text,
    value int
);
CREATE INDEX var_idx ON variables(name);

CREATE TABLE definitions (
    source text,
    thing text,
    definition text
);
CREATE INDEX def_idx ON definitions(thing);


