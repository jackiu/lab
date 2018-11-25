


webUserData = r"""
#!/bin/bash

yum update -y
yum install -y httpd 

sudo yum install -y mod_ssl

aws s3 cp s3://jackiu-generic/ssl.conf /etc/httpd/conf.d/ssl.conf

systemctl start httpd
systemctl enable httpd
usermod -a -G apache ec2-user
chown -R ec2-user:apache /var/www
chmod 2775 /var/www
find /var/www -type d -exec chmod 2775 {} \;
find /var/www -type f -exec chmod 0664 {} \;


echo  "hello world" >  /var/www/html/hello.html
"""