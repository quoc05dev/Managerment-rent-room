MERGE INTO roles (name) VALUES ('ROLE_ADMIN');
MERGE INTO roles (name) VALUES ('ROLE_RENTALER');
MERGE INTO roles (name) VALUES ('ROLE_USER');

MERGE INTO location(id, city_name) VALUES (1, 'Ha Noi');

MERGE INTO category(id, name) VALUES (1, 'Bat dong san');
MERGE INTO category(id, name) VALUES (2, 'Phong tro');
MERGE INTO category(id, name) VALUES (3, 'Chung cu mini');
