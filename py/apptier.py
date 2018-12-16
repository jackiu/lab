from troposphere import Join, Output, ImportValue, Sub, FindInMap, Export, Name
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select
from troposphere.constants import M5_LARGE, HTTPS_PORT
from troposphere.elasticloadbalancingv2 import LoadBalancer, Listener, ListenerCertificate, Certificate, Action, TargetGroup
from troposphere.policies import AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
from troposphere.ec2 import LaunchTemplate, LaunchTemplateData, IamInstanceProfile
from troposphere.iam import InstanceProfile, Role 
from troposphere.autoscaling import AutoScalingGroup, Metadata, LaunchTemplateSpecification, Tag
from base64 import b64encode


import userdata
import util 

t = Template()

TOMCAT_PORT = 8080

t.add_version('2010-09-09')

t.add_description("""\
App Tier  \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")


pubCertArn = Parameter("PubCertARN", Description="Public Cert ARN for Web Application Load Balancer", Type="String", 
                    Default="arn:aws:acm:us-east-2:350032182433:certificate/355f0f79-d86d-4b19-9e0a-a740d9914b83")


vpcParam = Parameter("VPC", Description="VPC ID", Type="AWS::EC2::VPC::Id", Default="")
vpc = Sub("${VPC}")

webPrivateSubnet1Param = Parameter("SubnetId3", Description="Web Private Subnet 1 ID", Type="AWS::EC2::Subnet::Id", Default="")
webPrivateSubnet1 = Sub("${SubnetId3}")

webPrivateSubnet2Param = Parameter("SubnetId4", Description="Web Private Subnet 2 ID", Type="AWS::EC2::Subnet::Id", Default="")
webPrivateSubnet2 = Sub("${SubnetId4}")

appPrivateSubnet1Param = Parameter("SubnetId5", Description="App Private Subnet 1 ID", Type="AWS::EC2::Subnet::Id", Default="")
appPrivateSubnet1 = Sub("${SubnetId5}")

appPrivateSubnet2Param = Parameter("SubnetId6", Description="App Private Subnet 2 ID", Type="AWS::EC2::Subnet::Id", Default="")
appPrivateSubnet2 = Sub("${SubnetId6}")

instanceProfileArnParam = Parameter("InstanceProfileArn", Description="Instance Profile Arn", Type="String", Default="arn:aws:iam::350032182433:instance-profile/EC2InstanceProfile")
instanceProfileArn = Sub("${InstanceProfileArn}")

appInstanceSGParam = Parameter("AppInstanceSG", Description="App Instance SG", Type="AWS::EC2::SecurityGroup::Id", Default="")
appInstanceSG = Sub("${AppInstanceSG}")

appALBSGParam = Parameter("AppALBSG", Description="App ALB SG", Type="AWS::EC2::SecurityGroup::Id", Default="")
appALBSG = Sub("${AppALBSG}")



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


launchTemplateData = LaunchTemplateData("AppInstanceTemplateData", 
                            SecurityGroupIds=[appInstanceSG], 
                            UserData=(b64encode(userdata.appUserData.encode())).decode("ascii"),
                            IamInstanceProfile=IamInstanceProfile(Arn=instanceProfileArn),
                            ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
                            KeyName="mb", 
                            InstanceType=M5_LARGE)

launchTemplate  = LaunchTemplate("AppInstanceTemplate", 
                        LaunchTemplateName="AppInstanceTemplate", 
                        LaunchTemplateData=launchTemplateData)


appLBTG = TargetGroup("AppLBTG" , Name="AppTierTargetGroup", VpcId=vpc, TargetType="instance", 
                    Protocol="HTTPS", Port=TOMCAT_PORT, HealthCheckPath="/")

appASG = AutoScalingGroup("AppASG", AutoScalingGroupName="AppASG", 
                            VPCZoneIdentifier=[appPrivateSubnet1, appPrivateSubnet2], 
                            DesiredCapacity="2",  
                            MaxSize="6",
                            MinSize="2",
                            Tags=[Tag("Name", "AppASGInstance", True)],
                            TargetGroupARNs=[Ref(appLBTG)],
                            LaunchTemplate=LaunchTemplateSpecification(LaunchTemplateId=Ref(launchTemplate), Version="1")
                        )

appLB = LoadBalancer("AppLB", Name="AppTierLoadBalancer", Scheme="internal", 
                    SecurityGroups=[appALBSG], Subnets=[webPrivateSubnet1, webPrivateSubnet2], 
                    Type="application") 

appLBListenerAction = Action(Type="forward", TargetGroupArn=Ref(appLBTG))

appLBlistener = Listener("AppLBListener" , Certificates=[Certificate(CertificateArn=Ref(pubCertArn))], 
                        DefaultActions=[appLBListenerAction], LoadBalancerArn=Ref(appLB), 
                        Port=HTTPS_PORT, Protocol="HTTPS", SslPolicy="ELBSecurityPolicy-FS-2018-06")



t.add_parameter(pubCertArn)
t.add_parameter(vpcParam)
t.add_parameter(webPrivateSubnet1Param)
t.add_parameter(webPrivateSubnet2Param)
t.add_parameter(appPrivateSubnet1Param)
t.add_parameter(appPrivateSubnet2Param)
t.add_parameter(instanceProfileArnParam)
t.add_parameter(appInstanceSGParam)
t.add_parameter(appALBSGParam)

t.add_resource(launchTemplate)
t.add_resource(appASG)
t.add_resource(appLBTG)
t.add_resource(appLB)
t.add_resource(appLBlistener)


t.add_resource( util.createSSMParameter("ALBEndpoint", "internal-alb-dnsname", "Internal Load Balancer DNS Name", "String", GetAtt(appLB,"DNSName")) )



t.add_output(Output("EndPointAddress",Value=GetAtt(appLB,"DNSName"), 
                Export=Export(Name(Join("-", [Ref("AWS::StackName"), "EndpointAddress"])))))


file = open('apptier.json','w')
file.write(t.to_json())


