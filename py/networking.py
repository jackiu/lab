from troposphere import Join, Output
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select
from troposphere.ec2 import VPC
from troposphere.ec2 import Subnet, InternetGateway, VPCGatewayAttachment, NatGateway
from troposphere.ec2 import EIP, RouteTable, Route, SubnetRouteTableAssociation
from troposphere.ec2 import SecurityGroupIngress, SecurityGroupEgress, SecurityGroup


##################### Define variable #######################
cidrPrefix = "192.168."
vpcCIDR = cidrPrefix + "0.0/16"
everywhereCIDR = "0.0.0.0/0"

subnetCIDR = []
for i in range(1, 9):
    subnetCIDR.append( cidrPrefix + str(i) + ".0/24" )

subnetNames = ["DMZ Tier Subnet 1", "DMZ Tier Subnet 2", "Web Tier Subnet 1", "Web Tier Subnet 2",
               "App Tier Subnet 1", "App Tier Subnet 2", "DB Tier Subnet 1", "DB Tier Subnet 2"]

subnets = []

t = Template()


vpc = VPC("VPC" , CidrBlock=vpcCIDR)

for i in range(1, 9):
    subnets.append( Subnet("Subnet" + str(i),
                    VpcId=Ref(vpc), 
                    CidrBlock = subnetCIDR[i-1],
                    Tags = Tags(Application=Ref("AWS::StackName"), Name=subnetNames[i-1]),
                    AvailabilityZone = Select( ((i+1)%2) , GetAZs("")) ) )

igw = InternetGateway("IGW")

igwAttachment = VPCGatewayAttachment("IGWAttachement", InternetGatewayId=Ref(igw), VpcId=Ref(vpc))

natEIP1 = EIP("NatEIP1", Domain="vpc")
natEIP2 = EIP("NatEIP2", Domain="vpc")

ngw1 = NatGateway("NGW1", AllocationId=GetAtt(natEIP1, "AllocationId"), SubnetId=Ref(subnets[0]), Tags = Tags(Application=Ref("AWS::StackName")))
ngw2 = NatGateway("NGW2", AllocationId=GetAtt(natEIP2, "AllocationId"), SubnetId=Ref(subnets[1]), Tags = Tags(Application=Ref("AWS::StackName")))

publicRouteTable = RouteTable("PublicRouteTable", VpcId=Ref(vpc), Tags = Tags(Application=Ref("AWS::StackName")))
privateRouteTable = RouteTable("PrivateRouteTable", VpcId=Ref(vpc), Tags = Tags(Application=Ref("AWS::StackName")))

publicRoute = Route("PublicRoute", DestinationCidrBlock=everywhereCIDR, GatewayId=Ref(igw), RouteTableId=Ref(publicRouteTable))
privateRoute1 = Route("PrivateRoute1", DestinationCidrBlock=everywhereCIDR, GatewayId=Ref(ngw1), RouteTableId=Ref(privateRouteTable))
privateRoute2 = Route("PrivateRoute2", DestinationCidrBlock=everywhereCIDR, GatewayId=Ref(ngw2), RouteTableId=Ref(privateRouteTable))

srtas = []
srtas.append(SubnetRouteTableAssociation("PubRouteTableAsso1", RouteTableId=Ref(publicRouteTable), SubnetId=Ref(subnets[0])))
srtas.append(SubnetRouteTableAssociation("PubRouteTableAsso2", RouteTableId=Ref(publicRouteTable), SubnetId=Ref(subnets[1])))

for i in range(2, 8):
    route = None
    if (i % 2) == 0:
        route = privateRoute1
    else:
        route = privateRoute2
        
    srtas.append(SubnetRouteTableAssociation("PubRouteTableAsso" + str(i+1) , RouteTableId=Ref(route), SubnetId=Ref(subnets[i])))




t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

t.add_parameter(Parameter("RandomString", Description="RandomString", Type="String"))

t.add_resource(vpc)

for s in subnets:
    t.add_resource(s)
t.add_resource(igw)
t.add_resource(igwAttachment)
t.add_resource(natEIP1)
t.add_resource(natEIP2)
t.add_resource(ngw1)
t.add_resource(ngw2)
t.add_resource(publicRouteTable)
t.add_resource(privateRouteTable)
t.add_resource(privateRoute1)
t.add_resource(privateRoute2)
for s in srtas:
    t.add_resource(s)

t.add_output(Output("VPC",Value=Ref(vpc)))
file = open('networking.json','w')
file.write(t.to_json())


