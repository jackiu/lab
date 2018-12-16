from troposphere import Join, Output
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select,Export, Name, Sub
from troposphere.ec2 import VPC
from troposphere.ec2 import Subnet, InternetGateway, VPCGatewayAttachment, NatGateway, VPCEndpoint
from troposphere.ec2 import EIP, RouteTable, Route, SubnetRouteTableAssociation
from troposphere.ec2 import SecurityGroupIngress, SecurityGroupEgress, SecurityGroup
from troposphere.constants import QUAD_ZERO

##################### Define variable #######################
# cidrPrefix = "192.168."
# vpcCIDR = cidrPrefix + "0.0/16"


# subnetCIDR = []
# for i in range(1, 9):
#     subnetCIDR.append( cidrPrefix + str(i) + ".0/24" )

subnetNames = ["DMZ Tier Subnet 1", "DMZ Tier Subnet 2", "Web Tier Subnet 1", "Web Tier Subnet 2",
               "App Tier Subnet 1", "App Tier Subnet 2", "DB Tier Subnet 1", "DB Tier Subnet 2"]

subnets = []

cidrPrefixParam = Parameter("CIDRPrefix", Description="CIDR block prefix for VPC", Type="String", Default="192.168")

t = Template()

t.add_version('2010-09-09')

t.add_description("""\
Networking Stack  \
Creates VPC, Subnets, IGW, Nat Gatways, Route Table, VPC Endpoint for S3
""")

vpc = VPC("VPC" , CidrBlock=Sub("${CIDRPrefix}.0.0/16"), EnableDnsSupport=True, EnableDnsHostnames=True)

for i in range(1, 9):
    publicIP = False
    if i <= 2:
        publicIP = True
    subnets.append( Subnet("Subnet" + str(i),
                    VpcId=Ref(vpc), 
                    #CidrBlock = subnetCIDR[i-1],
                    CidrBlock = Join("", [Sub("${CIDRPrefix}."), str(i-1) , ".0/24"]),
                    Tags = Tags(Application=Ref("AWS::StackName"), Name=subnetNames[i-1]),
                    MapPublicIpOnLaunch=publicIP,
                    AvailabilityZone = Select( ((i+1)%2) , GetAZs("")) ) )

igw = InternetGateway("IGW")

igwAttachment = VPCGatewayAttachment("IGWAttachement", InternetGatewayId=Ref(igw), VpcId=Ref(vpc))

natEIP1 = EIP("NatEIP1", Domain="vpc")
natEIP2 = EIP("NatEIP2", Domain="vpc")

ngw1 = NatGateway("NGW1", AllocationId=GetAtt(natEIP1, "AllocationId"), SubnetId=Ref(subnets[0]), Tags = Tags(Application=Ref("AWS::StackName")))
ngw2 = NatGateway("NGW2", AllocationId=GetAtt(natEIP2, "AllocationId"), SubnetId=Ref(subnets[1]), Tags = Tags(Application=Ref("AWS::StackName")))

publicRouteTable = RouteTable("PublicRouteTable", VpcId=Ref(vpc), Tags = Tags(Application=Ref("AWS::StackName")))
privateRouteTable1 = RouteTable("PrivateRouteTable1", VpcId=Ref(vpc), Tags = Tags(Application=Ref("AWS::StackName")))
privateRouteTable2 = RouteTable("PrivateRouteTable2", VpcId=Ref(vpc), Tags = Tags(Application=Ref("AWS::StackName")))

publicRoute = Route("PublicRoute", DestinationCidrBlock=QUAD_ZERO, GatewayId=Ref(igw), RouteTableId=Ref(publicRouteTable))
privateRoute1 = Route("PrivateRoute1", DestinationCidrBlock=QUAD_ZERO, NatGatewayId=Ref(ngw1), RouteTableId=Ref(privateRouteTable1))
privateRoute2 = Route("PrivateRoute2", DestinationCidrBlock=QUAD_ZERO, NatGatewayId=Ref(ngw2), RouteTableId=Ref(privateRouteTable2))

srtas = []
srtas.append(SubnetRouteTableAssociation("PubRouteTableAsso1", RouteTableId=Ref(publicRouteTable), SubnetId=Ref(subnets[0])))
srtas.append(SubnetRouteTableAssociation("PubRouteTableAsso2", RouteTableId=Ref(publicRouteTable), SubnetId=Ref(subnets[1])))

for i in range(2, 8):
    route = None
    if (i % 2) == 0:
        routeTable = privateRouteTable1
    else:
        routeTable = privateRouteTable2
        
    srtas.append(SubnetRouteTableAssociation("PrivateRouteTableAsso" + str(i+1) , RouteTableId=Ref(routeTable), SubnetId=Ref(subnets[i])))


vpcEndPoint=VPCEndpoint("S3EndPoint", VpcId=Ref(vpc), RouteTableIds=[Ref(publicRouteTable), Ref(privateRouteTable1), Ref(privateRouteTable2)], 
                            ServiceName=Join("", ["com.amazonaws.", Ref("AWS::Region"), ".s3"]) )



t.add_parameter(cidrPrefixParam)

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
t.add_resource(privateRouteTable1)
t.add_resource(privateRouteTable2)
t.add_resource(publicRoute)
t.add_resource(privateRoute1)
t.add_resource(privateRoute2)
t.add_resource(vpcEndPoint)

for s in srtas:
    t.add_resource(s)


t.add_output(Output("VPC",Description="Reference to the VPC",Value=Ref(vpc)))
for idx, subnet in enumerate(subnets):
    t.add_output(Output("Subnet" + str(idx+1), Description="Reference to the Subnet",Value=Ref(subnet)))

file = open('networking.json','w')
file.write(t.to_json())


