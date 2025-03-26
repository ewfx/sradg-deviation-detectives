-- Table: public.matched_records

-- DROP TABLE IF EXISTS public.matched_records;

CREATE TABLE IF NOT EXISTS public.matched_records
(
    id integer NOT NULL DEFAULT nextval('matched_records_id_seq'::regclass),
    "As of Date" date,
    "Company" text COLLATE pg_catalog."default",
    "Account" text COLLATE pg_catalog."default",
    "AU" text COLLATE pg_catalog."default",
    "Currency" text COLLATE pg_catalog."default",
    "Primary Account" text COLLATE pg_catalog."default",
    "Secondary Account" text COLLATE pg_catalog."default",
    "GL Balance" numeric,
    "iHub Balance" numeric,
    "Balance Difference" numeric,
    "Match Status" text COLLATE pg_catalog."default",
    "Comments" text COLLATE pg_catalog."default",
    "Anomaly" text COLLATE pg_catalog."default",
    CONSTRAINT matched_records_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.matched_records
    OWNER to postgres;

GRANT ALL ON TABLE public.matched_records TO myuser WITH GRANT OPTION;

GRANT ALL ON TABLE public.matched_records TO postgres;