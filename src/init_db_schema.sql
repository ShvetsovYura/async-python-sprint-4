CREATE SCHEMA if not exists links;

CREATE TABLE if not exists links.links
(
    url_id character varying(10) NOT NULL,
    original_url text  NOT NULL,
    active integer NOT NULL DEFAULT 1,
    created timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT links_pkey PRIMARY KEY (url_id)
);


CREATE TABLE if not exists links.stats
(
    id SERIAL,
    info text COLLATE pg_catalog."default",
    happened timestamp with time zone NOT NULL DEFAULT now(),
    url_id character varying(10) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT stats_pkey PRIMARY KEY (id)
);


CREATE INDEX if not exists stats_url_id
    ON links.stats USING btree
    (url_id ASC NULLS LAST);