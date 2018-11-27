from troposphere import ImportValue, Sub, Template, Parameter, Ref
from troposphere.secretsmanager import Secret


def createSSMParameter(cfname, name, desc, type, value):
    from troposphere.ssm import Parameter 
    return Parameter(cfname, Name=name, Description=desc, Type=type, 
                    Value=value)


iamStackName = Parameter("IAMStackName", Description="IAMStackName", Type="String", Default="IAM-Stack")
dbStackName = Parameter("DBStackName", Description="Database Stack Name", Type="String", Default="DB-Stack")

dbUsername = Parameter("DBUserName", Description="DBUsername", Type="String", Default="jack")
dbPassword = Parameter("DBPassword", Description="DBPassword", Type="String", Default="11223344")

dbEndpointURL = ImportValue(Sub("${DBStackName}-EndpointAddress"))
secretManagerKeyArn = ImportValue(Sub("${IAMStackName}-SecretManagerKeyArn"))


dbSecret = Secret("DBSecret", Description="Aurora Postgres Database passowrd", KmsKeyId=secretManagerKeyArn, SecretString=Ref(dbPassword), Name="DBCreds")


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

t.add_resource(createSSMParameter("APDBURL", "AuroraPostgresEndpointAddress", "Aurora Postgres Endpoint URL", "String", dbEndpointURL))
t.add_resource(createSSMParameter("APUserName", "AuroraPostgresUsername", "Aurora Postgres User Name", "String", Ref(dbUsername)))

t.add_resource(dbSecret)


file = open('parameterstore.json','w')
file.write(t.to_json())

