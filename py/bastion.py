from troposphere import Join, Output, ImportValue, Sub, FindInMap
from troposphere import Parameter, Ref, Tags, Template, GetAZs, GetAtt, Select
from troposphere.constants import M5_LARGE, HTTPS_PORT, T3_SMALL
from troposphere.elasticloadbalancingv2 import LoadBalancer, Listener, ListenerCertificate, Certificate, Action, TargetGroup
from troposphere.policies import AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
from troposphere.ec2 import LaunchTemplate, LaunchTemplateData, IamInstanceProfile
from troposphere.iam import InstanceProfile, Role 
from troposphere.autoscaling import AutoScalingGroup, Metadata, LaunchTemplateSpecification, Tag
from base64 import b64encode


import userdata

t = Template()


t.add_version('2010-09-09')

t.add_description("""\
Bastion Host \
**WARNING** This template creates an Amazon EC2 instance. You will be billed \
for the AWS resources used if you create a stack from this template.""")


vpcParam = Parameter("VPC", Description="VPC ID", Type="AWS::EC2::VPC::Id", Default="")
vpc = Sub("${VPC}")

pubSubnetId1Param = Parameter("PubSubnet1", Description="Public Subnet 1 ID", Type="AWS::EC2::Subnet::Id", Default="")
pubSubnetId1 = Sub("${PubSubnet1}")

pubSubnetId2Param = Parameter("PubSubnet2", Description="Public Subnet 2 ID", Type="AWS::EC2::Subnet::Id", Default="")
pubSubnetId2 = Sub("${PubSubnet2}")

instanceProfileArnParam = Parameter("InstanceProfileArn", Description="Instance Profile Arn", Type="String", Default="arn:aws:iam::350032182433:instance-profile/EC2InstanceProfile")
instanceProfileArn = Sub("${InstanceProfileArn}")

bastionSGParam = Parameter("BastionSG", Description="Bastion SG", Type="AWS::EC2::SecurityGroup::Id", Default="")
bastionSG = Sub("${BastionSG}")

# pubSubnetId1 = ImportValue(Sub("${NetworkingStackName}-SubnetId1"))
# pubSubnetId2 = ImportValue(Sub("${NetworkingStackName}-SubnetId2"))
# instanceProfileArn = ImportValue(Sub("${IAMStackName}-InstanceProfileArn"))
# bastionSG = ImportValue(Sub("${FirewallStackName}-BastionSG"))


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

bastionLaunchTemplateData = LaunchTemplateData("WebInstanceTemplateData", 
                            SecurityGroupIds=[bastionSG], 
                            IamInstanceProfile=IamInstanceProfile(Arn=instanceProfileArn),
                            ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
                            KeyName="mb", 
                            InstanceType=T3_SMALL)

bastionLaunchTemplate  = LaunchTemplate("BastionHostTemplate", LaunchTemplateName="BastionHostTemplate", LaunchTemplateData=bastionLaunchTemplateData)

bastionASG = AutoScalingGroup("BastionASG", AutoScalingGroupName="BastionASG", 
                            VPCZoneIdentifier=[pubSubnetId1, pubSubnetId2], 
                            DesiredCapacity="1",  
                            MaxSize="1",
                            MinSize="1",
                            Tags=[Tag("Name", "BastionHost", True)],
                            LaunchTemplate=LaunchTemplateSpecification(LaunchTemplateId=Ref(bastionLaunchTemplate), Version="1"))

t.add_parameter(vpcParam)
t.add_parameter(pubSubnetId1Param)
t.add_parameter(pubSubnetId2Param)
t.add_parameter(instanceProfileArnParam)
t.add_parameter(bastionSGParam)

t.add_resource(bastionLaunchTemplate)
t.add_resource(bastionASG)





file = open('bastion.json','w')
file.write(t.to_json())


