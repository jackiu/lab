from troposphere import Join, Output
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select
from troposphere.ec2 import VPC
from troposphere.ec2 import Subnet, InternetGateway, VPCGatewayAttachment, NatGateway
from troposphere.ec2 import EIP, RouteTable, Route, SubnetRouteTableAssociation
from troposphere.ec2 import SecurityGroupIngress, SecurityGroupEgress, SecurityGroup



everywhereCIDR = "0.0.0.0/0"
localCIDR = "127.0.0.1/32"
blockedEgress = [{
    "CidrIp": localCIDR,
    "IpProtocol": "-1"
}]

vpc = Parameter("VPC", Description="VPC", Type="AWS::EC2::VPC::Id")


dbSG = SecurityGroup( "DBSG", GroupName="DB SG", 
                    GroupDescription="Database Security Group", 
                    SecurityGroupEgress=blockedEgress,
                    VpcId=Ref(vpc) )

appInstanceSG = SecurityGroup( "AppInstanceSG", GroupName="App Instance SG", 
                    GroupDescription="Application Instance Security Group", 
                    VpcId=Ref(vpc) )

appALBSG = SecurityGroup( "AppALBSG", GroupName="App ALB SG", 
                    GroupDescription="Application Load Balancer Security Group", 
                    VpcId=Ref(vpc) )


webInstanceSG = SecurityGroup( "WebInstanceSG", GroupName="Web Instance SG", 
                    GroupDescription="Web Instance Security Group", 
                    VpcId=Ref(vpc) )

webALBSG = SecurityGroup( "WebALBSG", GroupName="ALB SG", 
                    GroupDescription="ALB Security Group", 
                    VpcId=Ref(vpc) )

dbIngress = SecurityGroupIngress("dbIngress", SourceSecurityGroupId=Ref(appInstanceSG), Description="db Ingress from app instance", IpProtocol="TCP", FromPort=5432, ToPort=5432, GroupId=Ref(dbSG))

appIngress = SecurityGroupIngress("appIngress", SourceSecurityGroupId=Ref(appALBSG), Description="App Server Ingress from Internal Application Load Balancer", IpProtocol="TCP", FromPort=8443, ToPort=8443, GroupId=Ref(appInstanceSG))
appEngress = SecurityGroupEgress("appEngress", DestinationSecurityGroupId=Ref(dbSG), Description="App Server Egress to DB", IpProtocol="TCP", FromPort=5432, ToPort=5432, GroupId=Ref(appInstanceSG))

appALBIngress = SecurityGroupIngress("appALBIngress", SourceSecurityGroupId=Ref(webInstanceSG), Description="App ALB Ingress from App Instance", IpProtocol="TCP", ToPort=443, FromPort=443, GroupId=Ref(appALBSG))
appALBEngress = SecurityGroupEgress("appALBEngress", DestinationSecurityGroupId=Ref(dbSG), Description="App ALB Egress to App Instance", IpProtocol="TCP", FromPort=8443, ToPort=8443, GroupId=Ref(appALBSG))

webIngress = SecurityGroupIngress("webIngress", SourceSecurityGroupId=Ref(webALBSG), Description="Web Server Ingress from Web Application Load Balancer", IpProtocol="TCP", ToPort=443, FromPort=443, GroupId=Ref(webInstanceSG))
webEngress = SecurityGroupEgress("webEngress", DestinationSecurityGroupId=Ref(appALBSG), Description="Web Server Egress to Internal Application Load Balancer", IpProtocol="TCP", FromPort=443, ToPort=443, GroupId=Ref(webInstanceSG))

webALBIngress = SecurityGroupIngress("webALBIngress", CidrIp=everywhereCIDR, Description="Opened Ingress", IpProtocol="TCP", ToPort=443, FromPort=443, GroupId=Ref(webALBSG))
webALBEngress = SecurityGroupEgress("webALBEngress", DestinationSecurityGroupId=Ref(webInstanceSG), Description="Egress to Web Server", IpProtocol="TCP", FromPort=443, ToPort=443, GroupId=Ref(webALBSG))



t = Template()

t.add_parameter(vpc)
# t.add_resource(closeEgress)
t.add_resource(dbSG)
t.add_resource(appInstanceSG)
t.add_resource(appALBSG)
t.add_resource(webInstanceSG)
t.add_resource(webALBSG)

t.add_resource(dbIngress)
t.add_resource(appIngress)
t.add_resource(appEngress)
t.add_resource(appALBIngress)
t.add_resource(appALBEngress)
t.add_resource(webIngress)
t.add_resource(webEngress)
t.add_resource(webALBEngress)
t.add_resource(webALBIngress)

file = open('firewall.json','w')
file.write(t.to_json())