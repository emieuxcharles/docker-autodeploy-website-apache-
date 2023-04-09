import argparse
import os
import socket

website=""
database=""
url=""
dbuser=""
dbpass=""
websitelocation="/Users/charlesemieux/Documents/automate-docker-python"

parser = argparse.ArgumentParser()
parser.add_argument("website_url", help="The URL of the website to be deployed")
parser.add_argument("zip_file", help="The zip file of the website to be deployed")
parser.add_argument("sql_file", help="The sql file of the website to be deployed")

args = parser.parse_args()

website_url = args.website_url
website_zip_file = args.zip_file
website_sql_file = args.sql_file

print("url : " + website_url)
print("zip : " + website_zip_file)
print("sql : " + website_sql_file)

sitename = website_url.replace("www.", "").replace("http://", "").replace("https://", "").replace(".fr", "").replace(".com", "").replace(".net", "").replace(".org", "")

siteurl = website_url.replace("www.", "").replace("http://", "").replace("https://", "")

print("siteurl : " + siteurl)

def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return "{}".format(port)

def create_website_dir():
    os.mkdir(websitelocation + "/" + sitename)
    os.mkdir(websitelocation + "/" + sitename + "/website")
    os.mkdir(websitelocation + "/" + sitename + "/mysql")
    os.mkdir(websitelocation + "/" + sitename + "/php-apache")

def copy_website_files():
    os.system("cp " + website_zip_file + " " + websitelocation + "/" + sitename + "/website")
    os.system("cp " + website_sql_file + " " + websitelocation + "/" + sitename + "/mysql")
    os.system("unzip -j " + websitelocation + "/" + sitename + "/website/" + website_zip_file + " -d " + websitelocation + "/" + sitename + "/website")
    os.system("rm " + websitelocation + "/" + sitename + "/website/" + website_zip_file)

def create_docker_compose():
    dockercompose = open(websitelocation + "/" + sitename + "/docker-compose.yml", "w")
    dockercompose.writelines([
        "version: '2'\n",
        "services:\n",
        "  web:\n",
        "    build: "+websitelocation+"/"+sitename+"/php-apache/\n",
        "    container_name: web_"+sitename+"\n",
        "    ports:\n",
        "      - '"+get_free_tcp_port()+":80'\n",
        "    volumes:\n",
        "      - "+websitelocation+"/"+sitename+"/website:/var/www/html\n",
        "      - "+websitelocation+"/"+sitename+"/php-apache/php.ini:/usr/local/etc/php/conf.d/custom.ini\n",
        "    links:\n",
        "      - db-"+sitename+"\n",
        "    labels:\n",
        "      - traefik.http.routers.web-"+sitename+"-http.entrypoints=insecure\n",
        "      - traefik.http.routers.web-"+sitename+"-http.rule=Host(`www."+siteurl+"`) || Host(`"+siteurl+"`)\n",
        "      - traefik.http.middlewares.https-redirect.redirectscheme.scheme=https\n",
        "      - traefik.http.middlewares.https-redirect.redirectscheme.permanent=true\n",
        "      - traefik.http.routers.web-"+sitename+"-http.middlewares=https-redirect@docker\n",
        "      - traefik.http.routers.web-"+sitename+"-https.entrypoints=secure\n",
        "      - traefik.http.routers.web-"+sitename+"-https.rule=Host(`www."+siteurl+"`) || Host(`"+siteurl+"`)\n",
        "      - traefik.http.routers.web-"+sitename+"-https.tls=true\n",
        "      - traefik.http.routers.web-"+sitename+"-https.tls.certresolver=letsencrypt\n",
        "    networks:\n",
        "      - traefik-33deg\n",
        "  db-"+sitename+":\n",
        "    image: 'mysql:5.7.35'\n",
        "    container_name: mysql_"+sitename+"\n",
        "    restart: always\n",
        "    environment:\n",
        "      MYSQL_ROOT_PASSWORD: root\n",
        "      MYSQL_DATABASE: "+sitename+"\n",
        "      MYSQL_USER: "+sitename+"\n",
        "      MYSQL_PASSWORD: xGjHHN6ZSpyc7T\n",
        "    volumes:\n",
        "      - "+websitelocation+"/"+sitename+"/mysql:/docker-entrypoint-initdb.d\n",
        "    ports:\n",
        "      - '"+get_free_tcp_port()+":3306'\n",
        "    networks:\n",
        "      - traefik-33deg\n",
        "networks:\n",
        "  traefik-33deg:\n",
        "    external:\n",
        "      name: traefik-33deg-"+sitename+"\n"
    ])
    dockercompose.close()

def create_apache_conf():
    apache = open(websitelocation + "/" + sitename + "/php-apache/apache.conf", "w")
    apache.writelines([
        "<VirtualHost *:80>\n",
        "        ServerAdmin webmaster@localhost\n",
        "        DocumentRoot /var/www/html/\n",
        "        <Directory /var/www/html/>\n",
        "                Options FollowSymLinks\n",
        "                AllowOverride all\n",
        "                Require all granted\n",
        "        </Directory>\n",
        "        ErrorLog ${APACHE_LOG_DIR}/error.log\n",
        "        CustomLog ${APACHE_LOG_DIR}/access.log combined\n",
        "</VirtualHost>\n"
    ])
    apache.close()

def create_php_ini():
    phpini = open(websitelocation + "/" + sitename + "/php-apache/php.ini", "w")
    phpini.writelines([
        "file_uploads = On\n",
        "memory_limit = 512M\n",
        "upload_max_filesize = 256M\n",
        "post_max_size = 256M\n",
        "max_execution_time = 600\n",
        "date.timezone = Europe/Paris\n"
    ])
    phpini.close()

def create_dockerfile():
    dockerfile = open(websitelocation + "/" + sitename + "/php-apache/Dockerfile", "w")
    dockerfile.write(
        '''
        FROM php:5-apache
        WORKDIR /var/www/html
        COPY ./apache.conf /etc/apache2/sites-available/000-default.conf
        RUN docker-php-ext-install pdo pdo_mysql mysql
        RUN apt-get update && \
        apt-get -y install curl git libicu-dev libpq-dev zlib1g-dev zip && \
        apt-get -y install libpng-dev && \
        apt-get -y install libmcrypt-dev  && \
        docker-php-ext-install intl mbstring pcntl pdo_mysql mysql pdo_pgsql zip && \
        usermod -u 1000 www-data && \
        usermod -a -G users www-data && \
        chown -R www-data:www-data /var/www && \
        curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer && \
        a2enmod rewrite
        RUN apt-get install -y \
            libwebp-dev \
            libjpeg62-turbo-dev \
            libpng-dev libxpm-dev \
            libfreetype6-dev
        RUN docker-php-ext-install mcrypt
        RUN docker-php-ext-configure gd \
            --with-gd \
            --with-webp-dir \
            --with-jpeg-dir \
            --with-png-dir \
            --with-zlib-dir \
            --with-xpm-dir \
            --with-freetype-dir \
            --enable-gd-native-ttf
        RUN docker-php-ext-install gd
        '''
    )
    dockerfile.close()

def run_docker():
    os.system("docker network create traefik-33deg-"+sitename)
    print("docker-compose -f " + websitelocation + "/" + sitename + "/docker-compose.yml up -d --build")
    os.system("docker-compose -f " + websitelocation + "/" + sitename + "/docker-compose.yml up -d --build")




create_website_dir()
copy_website_files()
create_php_ini()
create_docker_compose()
create_apache_conf()
create_dockerfile()
run_docker()