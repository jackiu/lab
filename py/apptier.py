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

t = Template()

networkingStackName = Parameter("NetworkingStackName", Description="NetworkingStackName", Type="String", Default="Networking-Stack")
iamStackName = Parameter("IAMStackName", Description="IAMStackName", Type="String", Default="IAM-Stack")
firewallStackName = Parameter("FirewallStackName", Description="=FirewallStackName", Type="String", Default="Firewall-Stack")
pubCertArn = Parameter("PubCertARN", Description="Public Cert ARN for Web Application Load Balancer", Type="String", 
                    Default="arn:aws:acm:us-east-2:350032182433:certificate/355f0f79-d86d-4b19-9e0a-a740d9914b83")

vpc = ImportValue(Sub("${NetworkingStackName}-VPCId"))

webPrivateSubnet1 = ImportValue(Sub("${NetworkingStackName}-SubnetId3"))
webPrivateSubnet2 = ImportValue(Sub("${NetworkingStackName}-SubnetId4"))
appPrivateSubnet1 = ImportValue(Sub("${NetworkingStackName}-SubnetId5"))
appPrivateSubnet2 = ImportValue(Sub("${NetworkingStackName}-SubnetId6"))
instanceProfileArn = ImportValue(Sub("${IAMStackName}-InstanceProfileArn"))
appInstanceSG = ImportValue(Sub("${FirewallStackName}-AppInstanceSG"))
appALBSG = ImportValue(Sub("${FirewallStackName}-AppALBSG"))


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
                    Protocol="HTTPS", Port=HTTPS_PORT, HealthCheckPath="/healthcheck")

appASG = AutoScalingGroup("AppASG", AutoScalingGroupName="AppASG", 
                            VPCZoneIdentifier=[appPrivateSubnet1, appPrivateSubnet2], 
                            DesiredCapacity="2",  
                            MaxSize="6",
                            MinSize="2",
                            Tags=[Tag("Name", "AppASGInstance", True)],
                            TargetGroupARNs=[Ref(appLBTG)],
                            LaunchTemplate=LaunchTemplateSpecification(LaunchTemplateId=Ref(launchTemplate), Version="1")
                        )

appLB = LoadBalancer("AppLB", Name="WebTierLoadBalancer", Scheme="internet-facing", 
                    SecurityGroups=[appALBSG], Subnets=[webPrivateSubnet1, webPrivateSubnet2], 
                    Type="application") 




appLBListenerAction = Action(Type="forward", TargetGroupArn=Ref(appLBTG))

appLBlistener = Listener("AppLBListener" , Certificates=[Certificate(CertificateArn=Ref(pubCertArn))], 
                        DefaultActions=[appLBListenerAction], LoadBalancerArn=Ref(appLB), 
                        Port=HTTPS_PORT, Protocol="HTTPS", SslPolicy="ELBSecurityPolicy-FS-2018-06")


t.add_parameter(networkingStackName)
t.add_parameter(iamStackName)
t.add_parameter(firewallStackName)
t.add_parameter(pubCertArn)

t.add_resource(launchTemplate)
t.add_resource(appASG)
t.add_resource(appLBTG)
t.add_resource(appLB)
t.add_resource(appLBlistener)

t.add_version('2010-09-09')

t.add_description("""\
AWS CloudFormation BLAH \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")


t.add_output(Output("EndPointAddress",Value=GetAtt(appLB,"Endpoint.Address"), 
                Export=Export(Name(Join("-", [Ref("AWS::StackName"), "EndpointAddress"])))))


file = open('apptier.json','w')
file.write(t.to_json())


