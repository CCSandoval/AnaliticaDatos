USE coffee;

ALTER TABLE `countries`
    MODIFY COLUMN `id` INT AUTO_INCREMENT,
    ADD PRIMARY KEY (`id`);

ALTER TABLE `domestic_consumption`
    MODIFY COLUMN `id` INT AUTO_INCREMENT,
    ADD PRIMARY KEY (`id`),
    ADD INDEX `idx_domestic_country` (`country_id`);

ALTER TABLE `domestic_consumption`
    ADD CONSTRAINT `fk_domestic_country`
    FOREIGN KEY (`country_id`)
    REFERENCES `countries`(`id`);

ALTER TABLE `exports`
    MODIFY COLUMN `id` INT AUTO_INCREMENT,
    ADD PRIMARY KEY (`id`),
    ADD INDEX `idx_exports_country` (`country_id`);

ALTER TABLE `exports`
    ADD CONSTRAINT `fk_exports_country`
    FOREIGN KEY (`country_id`)
    REFERENCES `countries`(`id`);

ALTER TABLE `importer_consumption`
    MODIFY COLUMN `id` INT AUTO_INCREMENT,
    ADD PRIMARY KEY (`id`),
    ADD INDEX `idx_importer_country` (`country_id`);

ALTER TABLE `importer_consumption`
    ADD CONSTRAINT `fk_importer_country`
    FOREIGN KEY (`country_id`)
    REFERENCES `countries`(`id`);

ALTER TABLE `imports`
    MODIFY COLUMN `id` INT AUTO_INCREMENT,
    ADD PRIMARY KEY (`id`),
    ADD INDEX `idx_imports_country` (`country_id`);

ALTER TABLE `imports`
    ADD CONSTRAINT `fk_imports_country`
    FOREIGN KEY (`country_id`)
    REFERENCES `countries`(`id`);

ALTER TABLE `production`
    MODIFY COLUMN `id` INT AUTO_INCREMENT,
    ADD PRIMARY KEY (`id`),
    ADD INDEX `idx_production_country` (`country_id`);

ALTER TABLE `production`
    ADD CONSTRAINT `fk_production_country`
    FOREIGN KEY (`country_id`)
    REFERENCES `countries`(`id`);

ALTER TABLE `re_exports`
    MODIFY COLUMN `id` INT AUTO_INCREMENT,
    ADD PRIMARY KEY (`id`),
    ADD INDEX `idx_re_exports_country` (`country_id`);

ALTER TABLE `re_exports`
    ADD CONSTRAINT `fk_re_exports_country`
    FOREIGN KEY (`country_id`)
    REFERENCES `countries`(`id`);
