from troposphere import Join, Output, Parameter, Template, ImportValue, Sub, Tags, Ref
from troposphere import Name, Export, GetAtt
from troposphere.rds import DBCluster, DBSubnetGroup, DBClusterParameterGroup, DBInstance


import userdata

t = Template()

MYSQL_PORT = 3306

t.add_version('2010-09-09')

t.add_description("""\
Creates Aurora MySQL Database \
**WARNING** This template creates Amazon RDS instances. You will be billed \
for the AWS resources used if you create a stack from this template.""")


dbName = Parameter("DatabaseName", Description="=DatabaseName", Type="String", Default="poc")
masterUsername = Parameter("DBUser", Description="=MasterUsername", Type="String", Default="jack")
masterUserPassword = Parameter("DBPassword", Description="=MasterUserPassword", Type="String", Default="11223344")


vpcParam = Parameter("VPC", Description="VPC ID", Type="AWS::EC2::VPC::Id", Default="")
vpc = Sub("${VPC}")

privateSubnetDB1Param = Parameter("PrivateSubnetDB1", Description="Private Subnet 7 ID", Type="AWS::EC2::Subnet::Id", Default="")
privateSubnetDB1 = Sub("${PrivateSubnetDB1}")

privateSubnetDB2Param = Parameter("PrivateSubnetDB2", Description="Private Subnet 8 ID", Type="AWS::EC2::Subnet::Id", Default="")
privateSubnetDB2 = Sub("${PrivateSubnetDB2}")

dbKeyArnParam = Parameter("DBKeyArn", Description="Database KMS Key Arn", Type="String", Default="")
dbKeyArn = Sub("${DBKeyArn}")

dbSGParam = Parameter("DBSG", Description="Database Security Group", Type="AWS::EC2::SecurityGroup::Id", Default="")
dbSG = Sub("${DBSG}")



dbSubnetGroup = DBSubnetGroup("DBSubnetGroup", DBSubnetGroupDescription="Aurora MySQL Subnet Group", DBSubnetGroupName="aurora-mysql-subnet-group", 
                                SubnetIds=[privateSubnetDB1, privateSubnetDB2], Tags=Tags(Application=Ref("AWS::StackName")))

mysqlCluster = DBCluster("AuroraMySQLCluster", DBSubnetGroupName=Ref(dbSubnetGroup), DatabaseName=Ref(dbName),  
                                Engine="aurora-mysql", EngineMode="provisioned", EngineVersion="5.7.12", KmsKeyId=dbKeyArn, 
                                MasterUsername=Ref(masterUsername), MasterUserPassword=Ref(masterUserPassword), Port=MYSQL_PORT, 
                                StorageEncrypted=True, Tags=Tags(Application=Ref("AWS::StackName")), VpcSecurityGroupIds=[dbSG],
                                DBClusterParameterGroupName="default.aurora-mysql5.7"
                            )

mysqlInstance = DBInstance("AuroraMySQLInstance", DBSubnetGroupName=Ref(dbSubnetGroup),
                                DBClusterIdentifier=Ref(mysqlCluster),
                                DBInstanceClass="db.r4.large", DBInstanceIdentifier="pocdbinstance",
                                DBParameterGroupName="default.aurora-mysql5.7", 
                                EnablePerformanceInsights=False, CopyTagsToSnapshot=True,
                                Engine="aurora-mysql",
                                StorageEncrypted=True, Tags=Tags(Application=Ref("AWS::StackName"))
                            )

# t.add_parameter(networkingStackName)
# t.add_parameter(iamStackName)
# t.add_parameter(firewallStackName)

t.add_parameter(vpcParam)
t.add_parameter(privateSubnetDB1Param)
t.add_parameter(privateSubnetDB2Param)
t.add_parameter(dbKeyArnParam)
t.add_parameter(dbSGParam)

t.add_parameter(dbName)
t.add_parameter(masterUsername)
t.add_parameter(masterUserPassword)



t.add_resource(mysqlCluster)
t.add_resource(mysqlInstance)
t.add_resource(dbSubnetGroup)




t.add_output(Output("EndPointAddress",Value=GetAtt(mysqlCluster,"Endpoint.Address")))
t.add_output(Output("ReadEndPointAddress",Value=GetAtt(mysqlCluster,"ReadEndpoint.Address")))
t.add_output(Output("Port",Value=GetAtt(mysqlCluster,"Endpoint.Port")))

file = open('db.json','w')
file.write(t.to_json())

