
INSERT INTO item (name, per_unit_weight, image_link) VALUES
('10g test mass', 1000, 'https://awsite.site/static/css/img/kilo.svg'),
('Pens', 100, 'https://awsite.site/static/css/img/pen.svg'),
('Binder Clips', 75, 'https://awsite.site/static/css/img/binder-clip.svg');


INSERT INTO shelf (name)
VALUES
('s1'),
('s2'),
('s3');

INSERT INTO shelf_item (shelf_id, item_name, count, restock_count, allowed)
SELECT s.id, '10g test mass', 0, 3, TRUE FROM shelf s WHERE s.name IN ('s1', 's2', 's3')
UNION ALL
SELECT s.id, 'Pens', 0, 3, FALSE FROM shelf s WHERE s.name IN ('s1', 's2', 's3')
UNION ALL
SELECT s.id, 'Binder Clips', 0, 3, FALSE FROM shelf s WHERE s.name IN ('s1', 's2', 's3');