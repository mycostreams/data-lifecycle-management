-- Creation of timestep table

CREATE TABLE IF NOT EXISTS prince_timestep (
  id INT GENERATED ALWAYS AS IDENTITY,
  experiment_id varchar(128) NOT NULL,
  key varchar(128) NOT NULL,
  prince_position INT NOT NULL,
  img_count INT NOT NULL,
  imaging_timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL,
  PRIMARY KEY(id)
);