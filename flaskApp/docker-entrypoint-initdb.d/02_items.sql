
INSERT INTO item (name, per_unit_weight, image_link) VALUES
('Test Mass', 5200, 'http://localhost:5100/static/css/img/kilo.svg'),
('Pens', 7230, 'http://localhost:5100/static/css/img/pen.svg'),
('Cards', 13380, 'http://localhost:5100/static/css/img/cards.svg'),
('Binder Clips', 11100, 'http://localhost:5100/static/css/img/binder-clip.svg');


INSERT INTO shelf (name)
VALUES
('s1'),
('s2'),
('s3');

INSERT INTO shelf_item (shelf_id, item_name, count, restock_count, allowed)
SELECT s.id, 'Test Mass', 0, 1, TRUE FROM shelf s WHERE s.name IN ('s1', 's2', 's3')
UNION ALL
SELECT s.id, 'Cards', 0, 2, TRUE FROM shelf s WHERE s.name IN ('s1', 's2', 's3')
UNION ALL
SELECT s.id, 'Pens', 0, 3, TRUE FROM shelf s WHERE s.name IN ('s1', 's2', 's3')
UNION ALL
SELECT s.id, 'Binder Clips', 0, 1, TRUE FROM shelf s WHERE s.name IN ('s1', 's2', 's3');