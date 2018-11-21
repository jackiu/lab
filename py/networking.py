from troposphere import Join, Output
from troposphere import Parameter, Ref, Tags, Template, GetAZs, Select
from troposphere.ec2 import VPC
from troposphere.ec2 import Subnet
from troposphere.ec2 import InternetGateway, VPCGatewayAttachment



##################### Define variable #######################
cidrPrefix = "192.168"
vpcCIDR = cidrPrefix + ".0.0/16"

subnetCIDR = []
for i in range(1, 9):
    subnetCIDR.append( cidrPrefix + str(i) + ".0/24" )

subnetNames = ["DMZ Tier Subnet 1", "DMZ Tier Subnet 2", "Web Tier Subnet 1", "Web Tier Subnet 2", "App Tier Subnet 1", "App Tier Subnet 2", "DB Tier Subnet 1", "DB Tier Subnet 2"]

subnet = []

vpc = VPC("VPC" , CidrBlock=vpcCIDR)

for i in range(1, 9):
    subnet.append( Subnet("Subnet" + str(i),
                    VpcId=Ref(vpc), 
                    CidrBlock = subnetCIDR[i-1],
                    Tags = [Tags(Application=Ref("AWS::StackName"),
                        Name=subnetNames[i-1])],
                    AvailabilityZone = Select(0, GetAZs("")) ) )


igw = InternetGateway("IGW", Tags = [Tags(Application=Ref("AWS::StackName"))])

igwAttachment = VPCGatewayAttachment("IGWAttachement", InternetGatewayId=Ref(igw), VpcId=Ref(vpc))



t = Template()

t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

t.add_resource(vpc)

for s in subnet:
    t.add_resource(s)
t.add_resource(igw)
t.add_resource(igwAttachment)

print(t.to_json())
