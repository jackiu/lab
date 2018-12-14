from troposphere import Join, Output, Parameter, Template, ImportValue, Sub, Tags, Ref
from troposphere import Name, Export, GetAtt
from troposphere.rds import DBCluster, DBSubnetGroup, DBClusterParameterGroup, DBInstance


import userdata

t = Template()

MYSQL_PORT = 3306

networkingStackName = Parameter("NetworkingStackName", Description="NetworkingStackName", Type="String", Default="Networking-Stack")
iamStackName = Parameter("IAMStackName", Description="IAMStackName", Type="String", Default="IAM-Stack")
firewallStackName = Parameter("FirewallStackName", Description="=FirewallStackName", Type="String", Default="Firewall-Stack")
dbName = Parameter("DatabaseName", Description="=DatabaseName", Type="String", Default="pocdb")
masterUsername = Parameter("MasterUsername", Description="=MasterUsername", Type="String", Default="jack")
masterUserPassword = Parameter("MasterUserPassword", Description="=MasterUserPassword", Type="String", Default="11223344")

vpc = ImportValue(Sub("${NetworkingStackName}-VPCId"))
privateSubnetDB1 = ImportValue(Sub("${NetworkingStackName}-SubnetId7"))
privateSubnetDB2 = ImportValue(Sub("${NetworkingStackName}-SubnetId8"))
dbKeyArn = ImportValue(Sub("${IAMStackName}-DBKeyArn"))
dbSG = ImportValue(Sub("${FirewallStackName}-DBSG"))


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

t.add_parameter(networkingStackName)
t.add_parameter(iamStackName)
t.add_parameter(firewallStackName)

t.add_parameter(dbName)
t.add_parameter(masterUsername)
t.add_parameter(masterUserPassword)

t.add_resource(mysqlCluster)
t.add_resource(mysqlInstance)
t.add_resource(dbSubnetGroup)

t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")



t.add_output(Output("EndPointAddress",Value=GetAtt(mysqlCluster,"Endpoint.Address"), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "EndpointAddress"])))))
t.add_output(Output("ReadEndPointAddress",Value=GetAtt(mysqlCluster,"ReadEndpoint.Address"), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "ReadEndpointAddress"])))))
t.add_output(Output("Port",Value=GetAtt(mysqlCluster,"Endpoint.Port"), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "Port"])))))

file = open('db.json','w')
file.write(t.to_json())

