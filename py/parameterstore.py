from troposphere import ImportValue, Sub, Template, Parameter, Ref
from troposphere.secretsmanager import Secret

import util 

iamStackName = Parameter("IAMStackName", Description="IAMStackName", Type="String", Default="IAM-Stack")
dbStackName = Parameter("DBStackName", Description="Database Stack Name", Type="String", Default="DB-Stack")

dbUsername = Parameter("DBUserName", Description="DBUsername", Type="String", Default="jack")
dbPassword = Parameter("DBPassword", Description="DBPassword", Type="String", Default="11223344")

dbEndpointURL = ImportValue(Sub("${DBStackName}-EndpointAddress"))
secretManagerKeyArn = ImportValue(Sub("${IAMStackName}-SecretManagerKeyArn"))
ccEncryptionKeyArn = ImportValue(Sub("${IAMStackName}-CCEncryptionKeyArn"))

dbSecret = Secret("DBSecret", Description="Aurora MySQL Database passowrd", KmsKeyId=secretManagerKeyArn, SecretString=Ref(dbPassword), Name="prod/mysql/creds")


t = Template()

t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

t.add_parameter(iamStackName)
t.add_parameter(dbStackName)
t.add_parameter(dbUsername)
t.add_parameter(dbPassword)

t.add_resource(util.createSSMParameter("AMYSQLDBHOST", "db-host", "Aurora MySQL Endpoint URL", "String", dbEndpointURL))
t.add_resource(util.createSSMParameter("AMYSQLUserName", "db-username", "Aurora MySQL User Name", "String", Ref(dbUsername)))
t.add_resource(util.createSSMParameter("AMYSQLDBURL", "db-url", "Aurora MySQL User Name", "String", 
        "jdbc:mysql://%s:3306/poc?useUnicode=true&characterEncoding=utf8&useLegacyDatetimeCode=false&verifyServerCertificate=true&useSSL=true&requireSSL=true"))

t.add_resource(util.createSSMParameter("CCEncryptionKeyArn", "cc-encryption-keyarn", "Key Arn for Credit Card encryption", "String", ccEncryptionKeyArn))

t.add_resource(dbSecret)


file = open('parameterstore.json','w')
file.write(t.to_json())

