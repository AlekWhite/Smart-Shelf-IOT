
INSERT INTO item (name, per_unit_weight, image_link) VALUES
('Test Mass', 5200, 'https://awsite.site/static/css/img/kilo.svg'),
('Pens', 7400, 'https://awsite.site/static/css/img/pen.svg'),
('Cards', 13600, 'https://awsite.site/static/css/img/cards.svg'),
('Binder Clips', 11400, 'https://awsite.site/static/css/img/binder-clip.svg');


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