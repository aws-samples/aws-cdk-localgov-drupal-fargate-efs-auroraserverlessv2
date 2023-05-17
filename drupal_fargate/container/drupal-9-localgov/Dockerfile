FROM --platform=linux/amd64 localgovdrupal/apache-php:php8.1

RUN apt-get update -y && \
apt-get upgrade -y && \
mkdir /var/www/files && \
cd /var/www/html && \
composer create-project localgovdrupal/localgov-project . --no-install && \
composer require drupal/core:9.5.9 --update-with-all-dependencies && \
composer install && \
ln -s /var/www/files /var/www/html/web/sites/default/ && \
chown -R docker:docker /var/www/html/web/sites/ && \
chown -R docker:docker /var/www/files && \
echo " \
\
\$settings['trusted_host_patterns'] = [ \
  '^.+\.elb\.amazonaws\.com\$', \
  '^.+\.cloudfront\.net\$', \
  '^.aws\.dev\$', \
  '^localhost\$', \
]; \
\
\$db = getenv('DRUPAL_DB_NAME') ? getenv('DRUPAL_DB_NAME') : ''; \
\$un = getenv('DRUPAL_DB_USER') ? getenv('DRUPAL_DB_USER') : ''; \
\$pw = getenv('DRUPAL_DB_PASSWORD') ? getenv('DRUPAL_DB_PASSWORD') : ''; \
\$host = getenv('DRUPAL_DB_HOST') ? getenv('DRUPAL_DB_HOST') : ''; \
\$port = getenv('DRUPAL_DB_PORT') ? getenv('DRUPAL_DB_PORT') : ''; \
\
if(!empty(\$db)) { \
\$databases['default']['default'] = [   \
     'database' => \$db,  \
     'username' => \$un, \
     'password' => \$pw,  \
     'host' => \$host,  \
     'port' => \$port,  \
     'driver' => 'mysql', \ 
     'prefix' => '',  \
     'collation' => 'utf8mb4_general_ci',   \
     'init_commands' => [ \
        'isolation_level' => 'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED', \
      ], \
  ]; \
}" >> /var/www/html/web/sites/default/settings.php

COPY themes /var/www/html/web/themes
COPY modules /var/www/html/web/modules
