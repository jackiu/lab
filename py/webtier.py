from troposphere import Join, Output, ImportValue, Sub, FindInMap
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select
from troposphere.constants import M5_LARGE, HTTPS_PORT
from troposphere.elasticloadbalancingv2 import LoadBalancer, Listener, ListenerCertificate, Certificate, Action, TargetGroup
from troposphere.policies import AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
from troposphere.ec2 import LaunchTemplate, LaunchTemplateData, IamInstanceProfile
from troposphere.iam import InstanceProfile, Role 
from troposphere.autoscaling import AutoScalingGroup, Metadata, LaunchTemplateSpecification, Tag
from base64 import b64encode


import userdata

t = Template()

networkingStackName = Parameter("NetworkingStackName", Description="NetworkingStackName", Type="String", Default="Networking-Stack")
iamStackName = Parameter("IAMStackName", Description="IAMStackName", Type="String", Default="IAM-Stack")
firewallStackName = Parameter("FirewallStackName", Description="=FirewallStackName", Type="String", Default="Firewall-Stack")
pubCertArn = Parameter("PubCertARN", Description="Public Cert ARN for Web Application Load Balancer", Type="String", 
                    Default="arn:aws:acm:us-east-2:350032182433:certificate/355f0f79-d86d-4b19-9e0a-a740d9914b83")

vpc = ImportValue(Sub("${NetworkingStackName}-VPCId"))
pubSubnetId1 = ImportValue(Sub("${NetworkingStackName}-SubnetId1"))
pubSubnetId2 = ImportValue(Sub("${NetworkingStackName}-SubnetId2"))
privateSubnetId1 = ImportValue(Sub("${NetworkingStackName}-SubnetId3"))
privateSubnetId2 = ImportValue(Sub("${NetworkingStackName}-SubnetId4"))
instanceProfileArn = ImportValue(Sub("${IAMStackName}-InstanceProfileArn"))
webInstanceSG = ImportValue(Sub("${FirewallStackName}-WebInstanceSG"))
webALBSG = ImportValue(Sub("${FirewallStackName}-WebALBSG"))


t.add_mapping('RegionMap', {
    "us-east-1": {"AMI": "ami-009d6802948d06e52"},
    "us-east-2": {"AMI": "ami-02e680c4540db351e"},
    "us-west-1": {"AMI": "ami-011b6930a81cd6aaf"},
    "us-west-2": {"AMI": "ami-01bbe152bf19d0289"},
    "eu-west-1": {"AMI": "ami-09693313102a30b2c"},
    "sa-east-1": {"AMI": "ami-0112d42866980b373"},
    "ap-southeast-1": {"AMI": "ami-0b84d2c53ad5250c2"},
    "ap-northeast-1": {"AMI": "ami-0a2de1c3b415889d2"}
})


ltdata = LaunchTemplateData("WebInstanceTemplateData", 
                            SecurityGroupIds=[webInstanceSG], 
                            UserData=(b64encode(userdata.webUserData.encode())).decode("ascii"),
                            IamInstanceProfile=IamInstanceProfile(Arn=instanceProfileArn),
                            ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
                            KeyName="mb", 
                            InstanceType=M5_LARGE)

lt  = LaunchTemplate("WebInstanceTemplate", LaunchTemplateName="WebInstanceTemplate", LaunchTemplateData=ltdata)


webLBTG = TargetGroup("WebLBTG" , Name="WebTierTargetGroup", VpcId=vpc, TargetType="instance", 
                    Protocol="HTTPS", Port=HTTPS_PORT, HealthCheckPath="/hello.html")

webASG = AutoScalingGroup("WebASG", AutoScalingGroupName="WebASG", 
                            VPCZoneIdentifier=[privateSubnetId1, privateSubnetId2], 
                            DesiredCapacity="2",  
                            MaxSize="6",
                            MinSize="2",
                            Tags=[Tag("Name", "WebASGInstance", True)],
                            TargetGroupARNs=[Ref(webLBTG)],
                            LaunchTemplate=LaunchTemplateSpecification(LaunchTemplateId=Ref(lt), Version="1"))

webLB = LoadBalancer("WebLB", Name="WebTierLoadBalancer", Scheme="internet-facing", 
                    SecurityGroups=[webALBSG], Subnets=[pubSubnetId1, pubSubnetId2], 
                    Type="application") 




webLBListenerAction = Action(Type="forward", TargetGroupArn=Ref(webLBTG))

webLBlistener = Listener("WebLBListener" , Certificates=[Certificate(CertificateArn=Ref(pubCertArn))], 
                        DefaultActions=[webLBListenerAction], LoadBalancerArn=Ref(webLB), 
                        Port=HTTPS_PORT, Protocol="HTTPS", SslPolicy="ELBSecurityPolicy-FS-2018-06")


t.add_parameter(networkingStackName)
t.add_parameter(iamStackName)
t.add_parameter(firewallStackName)
t.add_parameter(pubCertArn)

t.add_resource(lt)
t.add_resource(webASG)
t.add_resource(webLBTG)
t.add_resource(webLB)
t.add_resource(webLBlistener)


t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")


file = open('webtier.json','w')
file.write(t.to_json())


