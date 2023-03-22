FROM --platform=linux/amd64 drupal:10-apache

RUN apt-get update -y && \
apt-get upgrade -y && \
mkdir /var/www/files && \
ln -s /var/www/files /opt/drupal/web/sites/default/ && \
cp /opt/drupal/web/sites/default/default.settings.php /opt/drupal/web/sites/default/settings.php && \
echo " \
\
\$settings['hash_salt'] = 'SOelBL-o8b_k0BIJBRC7piYZxDFPFjnsRANJW7t9xJJEXidbTDKDBYzUxXsejPEEgJg_wSfXIQ'; \
\
\$settings['trusted_host_patterns'] = [ \
  '^.+\.elb\.amazonaws\.com\$', \
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
}" >> /opt/drupal/web/sites/default/settings.php && \
chown -R www-data:www-data /opt/drupal/web/sites/ && \
chown -R www-data:www-data /var/www/files

COPY themes /opt/drupal/web/themes
COPY modules /opt/drupal/web/modules