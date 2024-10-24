FROM php:8.1-apache

RUN apt update && apt upgrade -y && apt-get install -y git && docker-php-ext-install pdo pdo_mysql

WORKDIR /var/www/html

