from troposphere import ImportValue, Sub, Template, Parameter, Ref
from troposphere.secretsmanager import Secret


def createSSMParameter(cfname, name, desc, type, value):
    from troposphere.ssm import Parameter 
    return Parameter(cfname, Name=name, Description=desc, Type=type, 
                    Value=value)


iamStackName = Parameter("IAMStackName", Description="IAMStackName", Type="String", Default="IAM-Stack")
dbStackName = Parameter("DBStackName", Description="=Database Stack Name", Type="String", Default="DB-Stack")

dbUsername = Parameter("DBUsername", Description="=DBUsername", Type="String", Default="jack")
dbPassword = Parameter("DBPassword", Description="=DBPassword", Type="String", Default="11223344")

dbEndpointURL = ImportValue(Sub("${DBStackName}-EndpointAddress"))
secretManagerKeyArn = ImportValue(Sub("${IAMStackName}-SecretManagerKeyArn"))


dbSecret = Secret("DBSecret", Description="Aurora Postgres Database passowrd", KmsKeyId=secretManagerKeyArn, SecretString=Ref(dbPassword), Name="DBCreds")


t = Template()


t.add_parameter(dbStackName)


t.add_resource(createSSMParameter("DBURL", "DBURL", "Aurora Postgres URL", "String", dbEndpointURL))
t.add_resource(createSSMParameter("DBUsername", "DBUsername", "Aurora Postgres User Name", "String", Ref(dbUsername)))

t.add_resource(dbSecret)



file = open('parameterstore.json','w')
file.write(t.to_json())

