from troposphere import Join, Output, Export, Name, ImportValue, Sub
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select

from troposphere.ec2 import SecurityGroupIngress, SecurityGroupEgress, SecurityGroup



everywhereCIDR = "0.0.0.0/0"
localCIDR = "127.0.0.1/32"
blockedEgress = [{
    "CidrIp": localCIDR,
    "IpProtocol": "-1"
}]

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

dbIngress = SecurityGroupIngress("DBIngress", SourceSecurityGroupId=Ref(appInstanceSG), Description="db Ingress from app instance", IpProtocol="TCP", FromPort=5432, ToPort=5432, GroupId=Ref(dbSG))

appIngress = SecurityGroupIngress("AppIngress", SourceSecurityGroupId=Ref(appALBSG), Description="App Server Ingress from Internal Application Load Balancer", IpProtocol="TCP", FromPort=8443, ToPort=8443, GroupId=Ref(appInstanceSG))
appEngress = SecurityGroupEgress("AppEngress", DestinationSecurityGroupId=Ref(dbSG), Description="App Server Egress to DB", IpProtocol="TCP", FromPort=5432, ToPort=5432, GroupId=Ref(appInstanceSG))

appALBIngress = SecurityGroupIngress("AppALBIngress", SourceSecurityGroupId=Ref(webInstanceSG), Description="App ALB Ingress from App Instance", IpProtocol="TCP", ToPort=443, FromPort=443, GroupId=Ref(appALBSG))
appALBEngress = SecurityGroupEgress("AppALBEngress", DestinationSecurityGroupId=Ref(dbSG), Description="App ALB Egress to App Instance", IpProtocol="TCP", FromPort=8443, ToPort=8443, GroupId=Ref(appALBSG))

webIngress = SecurityGroupIngress("WebIngress", SourceSecurityGroupId=Ref(webALBSG), Description="Web Server Ingress from Web Application Load Balancer", IpProtocol="TCP", ToPort=443, FromPort=443, GroupId=Ref(webInstanceSG))
webEngress = SecurityGroupEgress("WebEngress", DestinationSecurityGroupId=Ref(appALBSG), Description="Web Server Egress to Internal Application Load Balancer", IpProtocol="TCP", FromPort=443, ToPort=443, GroupId=Ref(webInstanceSG))

webALBIngress = SecurityGroupIngress("WebALBIngress", CidrIp=everywhereCIDR, Description="Opened Ingress", IpProtocol="TCP", ToPort=443, FromPort=443, GroupId=Ref(webALBSG))
webALBEngress = SecurityGroupEgress("WebALBEngress", DestinationSecurityGroupId=Ref(webInstanceSG), Description="Egress to Web Server", IpProtocol="TCP", FromPort=443, ToPort=443, GroupId=Ref(webALBSG))



t = Template()

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

t.add_resource(dbIngress)
t.add_resource(appIngress)
t.add_resource(appEngress)
t.add_resource(appALBIngress)
t.add_resource(appALBEngress)
t.add_resource(webIngress)
t.add_resource(webEngress)
t.add_resource(webALBEngress)
t.add_resource(webALBIngress)

t.add_output(Output("WebALBSG",Value=Ref(webALBSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "WebALBSG"])))))
t.add_output(Output("WebInstanceSG",Value=Ref(webInstanceSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "WebInstanceSG"])))))
t.add_output(Output("AppALBSG",Value=Ref(appALBSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "AppALBSG"])))))
t.add_output(Output("AppInstanceSG",Value=Ref(appInstanceSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "AppInstanceSG"])))))
t.add_output(Output("DBSG",Value=Ref(dbSG), Export=Export(Name(Join("-", [Ref("AWS::StackName"), "DBSG"])))))

file = open('firewall.json','w')
file.write(t.to_json())