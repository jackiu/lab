from troposphere import Join, Output, Export, Name, ImportValue, Sub, FindInMap
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select

from troposphere.ec2 import SecurityGroupIngress, SecurityGroupEgress, SecurityGroup
from troposphere.constants import SSH_PORT, HTTPS_PORT, POSTGRESQL_PORT

everywhereCIDR = "0.0.0.0/0"
localCIDR = "127.0.0.1/32"
blockedEgress = [{
    "CidrIp": localCIDR,
    "IpProtocol": "-1"
}]


t = Template()

t.add_mapping('RegionMap', {
    "us-east-1": {"PRE": "pl-63a5400a"},
    "us-east-2": {"PRE": "pl-7ba54012"},
    "us-west-1": {"PRE": "pl-6ba54002"},
    "us-west-2": {"PRE": "pl-68a54001"},
    "eu-west-1": {"PRE": "pl-6da54004"},
    "sa-east-1": {"PRE": "pl-6aa54003"},
    "ap-southeast-1": {"PRE": "pl-6fa54006"},
    "ap-northeast-1": {"PRE": "pl-61a54008"}
})

networkingStackName = Parameter("NetworkingStackName", Description="NetworkingStackName", Type="String", Default="Networking-Stack")

vpc = ImportValue(Sub("${NetworkingStackName}-VPCId"))

dbSG = SecurityGroup( "DBSG", GroupName="DB SG", 
                    GroupDescription="Database Security Group", 
                    SecurityGroupEgress=blockedEgress,
                    VpcId=vpc )

appInstanceSG = SecurityGroup( "AppInstanceSG", GroupName="App Instance SG", 
                    GroupDescription="Application Instance Security Group", 
                    VpcId=vpc )

appALBSG = SecurityGroup( "AppALBSG", GroupName="App ALB SG", 
                    GroupDescription="Application Load Balancer Security Group", 
                    VpcId=vpc )


webInstanceSG = SecurityGroup( "WebInstanceSG", GroupName="Web Instance SG", 
                    GroupDescription="Web Instance Security Group", 
                    VpcId=vpc )

webALBSG = SecurityGroup( "WebALBSG", GroupName="ALB SG", 
                    GroupDescription="ALB Security Group", 
                    VpcId=vpc )

bastionHostSG = SecurityGroup( "BastionHostSG", GroupName="Bastion Host SG", 
                    GroupDescription="Bastion Host Security Group", 
                    VpcId=vpc )

dbIngress = SecurityGroupIngress("DBIngress", SourceSecurityGroupId=Ref(appInstanceSG), Description="db Ingress from app instance", 
                                    IpProtocol="TCP", FromPort=POSTGRESQL_PORT, ToPort=POSTGRESQL_PORT, GroupId=Ref(dbSG))

appIngress1 = SecurityGroupIngress("AppIngress1", SourceSecurityGroupId=Ref(appALBSG), Description="App Server Ingress from Internal Application Load Balancer", 
                                    IpProtocol="TCP", FromPort=8443, ToPort=8443, GroupId=Ref(appInstanceSG))
appIngress2 = SecurityGroupIngress("AppIngress2", SourceSecurityGroupId=Ref(bastionHostSG), Description="App Server Ingress from Bastion Host", 
                                    IpProtocol="TCP", FromPort=SSH_PORT, ToPort=SSH_PORT, GroupId=Ref(appInstanceSG))
appEngress1 = SecurityGroupEgress("AppEngress1", DestinationSecurityGroupId=Ref(dbSG), Description="App Server Egress to DB", 
                                    IpProtocol="TCP", FromPort=POSTGRESQL_PORT, ToPort=POSTGRESQL_PORT, GroupId=Ref(appInstanceSG))
appEngress2 = SecurityGroupEgress("AppEngress2", DestinationPrefixListId=FindInMap("RegionMap", Ref("AWS::Region"), "PRE"), Description="App Server Egress to S3 Endpoint", 
                                    IpProtocol="TCP", FromPort=HTTPS_PORT, ToPort=HTTPS_PORT, GroupId=Ref(appInstanceSG))

appALBIngress = SecurityGroupIngress("AppALBIngress", SourceSecurityGroupId=Ref(webInstanceSG), Description="App ALB Ingress from App Instance", 
                                    IpProtocol="TCP", ToPort=HTTPS_PORT, FromPort=HTTPS_PORT, GroupId=Ref(appALBSG))
appALBEngress = SecurityGroupEgress("AppALBEngress", DestinationSecurityGroupId=Ref(dbSG), Description="App ALB Egress to App Instance", 
                                    IpProtocol="TCP", FromPort=8443, ToPort=8443, GroupId=Ref(appALBSG))


webIngress1 = SecurityGroupIngress("WebIngress1", SourceSecurityGroupId=Ref(webALBSG), Description="Web Server Ingress from Web Application Load Balancer", 
                                    IpProtocol="TCP", ToPort=HTTPS_PORT, FromPort=HTTPS_PORT, GroupId=Ref(webInstanceSG))

webIngress2 = SecurityGroupIngress("WebIngress2", SourceSecurityGroupId=Ref(bastionHostSG), Description="Web Server Ingress from Bastion Host", 
                                    IpProtocol="TCP", ToPort=SSH_PORT, FromPort=SSH_PORT, GroupId=Ref(webInstanceSG))

webEngress1 = SecurityGroupEgress("WebEngress1", DestinationSecurityGroupId=Ref(appALBSG), Description="Web Server Egress to Internal Application Load Balancer", 
                                    IpProtocol="TCP", FromPort=HTTPS_PORT, ToPort=HTTPS_PORT, GroupId=Ref(webInstanceSG))

webEngress2 = SecurityGroupEgress("WebEngress2", DestinationPrefixListId=FindInMap("RegionMap", Ref("AWS::Region"), "PRE"), Description="Web Server Egress to S3 Endpoint", 
                                    IpProtocol="TCP", FromPort=HTTPS_PORT, ToPort=HTTPS_PORT, GroupId=Ref(webInstanceSG))


webALBIngress = SecurityGroupIngress("WebALBIngress", CidrIp=everywhereCIDR, Description="Opened Ingress", IpProtocol="TCP", ToPort=HTTPS_PORT, FromPort=HTTPS_PORT, GroupId=Ref(webALBSG))

webALBEngress = SecurityGroupEgress("WebALBEngress", DestinationSecurityGroupId=Ref(webInstanceSG), Description="Egress to Web Server", 
                                    IpProtocol="TCP", FromPort=HTTPS_PORT, ToPort=HTTPS_PORT, GroupId=Ref(webALBSG))


bastionHostIngress = SecurityGroupIngress("BastionHostIngress", CidrIp=everywhereCIDR, Description="Bastion Host Ingress", 
                                        IpProtocol="TCP", ToPort=SSH_PORT, FromPort=SSH_PORT, GroupId=Ref(bastionHostSG))
bastionHostEngress = SecurityGroupEgress("BastionHostEngressWeb", DestinationSecurityGroupId=Ref(webInstanceSG), Description="Bastion Host Egress to Web Instances", 
                                        IpProtocol="TCP", FromPort=SSH_PORT, ToPort=SSH_PORT, GroupId=Ref(bastionHostSG))
bastionHostEngress2 = SecurityGroupEgress("BastionHostEngressApp", DestinationSecurityGroupId=Ref(appInstanceSG), Description="Bastion Host Egress to Web Instances", 
                                        IpProtocol="TCP", FromPort=SSH_PORT, ToPort=SSH_PORT, GroupId=Ref(bastionHostSG))
bastionHostEngress3 = SecurityGroupEgress("BastionHostEngressS3", DestinationPrefixListId=FindInMap("RegionMap", Ref("AWS::Region"), "PRE"), Description="Bastion Host Egress to S3", 
                                        IpProtocol="TCP", FromPort=HTTPS_PORT, ToPort=HTTPS_PORT, GroupId=Ref(bastionHostSG))


t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")

t.add_parameter(networkingStackName)
# t.add_resource(closeEgress)
t.add_resource(dbSG)
t.add_resource(appInstanceSG)
t.add_resource(appALBSG)
t.add_resource(webInstanceSG)
t.add_resource(webALBSG)
t.add_resource(bastionHostSG)

t.add_resource(dbIngress)
t.add_resource(appIngress1)
t.add_resource(appIngress2)
t.add_resource(appEngress1)
t.add_resource(appEngress2)
t.add_resource(appALBIngress)
t.add_resource(appALBEngress)
t.add_resource(webIngress1)
t.add_resource(webIngress2)
t.add_resource(webEngress1)
t.add_resource(webEngress2)
t.add_resource(webALBEngress)
t.add_resource(webALBIngress)
t.add_resource(bastionHostIngress)
t.add_resource(bastionHostEngress)
t.add_resource(bastionHostEngress2)
t.add_resource(bastionHostEngress3)

t.add_output(Output("WebALBSG",Value=Ref(webALBSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "WebALBSG"])))))
t.add_output(Output("WebInstanceSG",Value=Ref(webInstanceSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "WebInstanceSG"])))))
t.add_output(Output("AppALBSG",Value=Ref(appALBSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "AppALBSG"])))))
t.add_output(Output("AppInstanceSG",Value=Ref(appInstanceSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "AppInstanceSG"])))))
t.add_output(Output("DBSG",Value=Ref(dbSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "DBSG"])))))
t.add_output(Output("BastionSG",Value=Ref(bastionHostSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "BastionSG"])))))

file = open('firewall.json','w')
file.write(t.to_json())