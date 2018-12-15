


webUserData = r"""
#!/bin/bash

yum update -y
yum install -y httpd 

yum install -y mod_ssl

export AWS_DEFAULT_REGION=$(curl -m5 -sS http://169.254.169.254/latest/meta-data/placement/availability-zone | sed 's/.$//')

aws s3 cp s3://jackiu-us-east-2/ssl.conf /etc/httpd/conf.d/ssl.conf

echo "ProxyPass / https://`aws ssm get-parameter --name internal-alb-dnsname --query "Parameter.Value" --output text`/" >> /etc/httpd/conf.d/ssl.conf
echo "ProxyPassReverse / https://`aws ssm get-parameter --name internal-alb-dnsname --query "Parameter.Value" --output text`/" >> /etc/httpd/conf.d/ssl.conf
echo "</VirtualHost>" >> /etc/httpd/conf.d/ssl.conf


systemctl start httpd
systemctl enable httpd
usermod -a -G apache ec2-user
chown -R ec2-user:apache /var/www
chmod 2775 /var/www
find /var/www -type d -exec chmod 2775 {} \;
find /var/www -type f -exec chmod 0664 {} \;

echo  "hello world" >  /var/www/html/hello.html
"""


appUserData = r"""
#!/bin/bash

yum -y install java-openjdk

aws s3 cp s3://jackiu-us-east-2/poc-0.0.1-SNAPSHOT.war .

aws s3 cp s3://jackiu-us-east-2/rds-ca-2015-root.pem .

chmod 755 poc-0.0.1-SNAPSHOT.war

openssl x509 -outform der -in rds-ca-2015-root.pem -out rds-combined-ca-bundle.der

keytool -noprompt -keystore /etc/pki/java/cacerts -alias rds_postgres -import -file rds-combined-ca-bundle.der -keypass changeit -storepass changeit

./poc-0.0.1-SNAPSHOT.war

"""